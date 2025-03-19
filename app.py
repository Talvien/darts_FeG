from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Player, Tournament, Match, Round, Group, GroupStageFormat, KnockOutStageFormat, GroupPlayer
from tournament import create_knockout_stage, create_next_round_matches, create_tiebreaker_matches
import tournament

app = Flask(__name__)
app.secret_key = b'***************************************'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Ilm1aGig#my@127.0.0.1:3306/database_darts'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
migrate = Migrate(app, db)
db.init_app(app)

@app.route('/api/group-stage-formats', methods=['GET'])
def get_group_stage_formats():
    formats = GroupStageFormat.query.all()
    formats_data = [{'format_id': fmt.format_id, 'format_name': fmt.format_name} for fmt in formats]
    return jsonify(formats_data)

@app.route('/api/knock-out-stage-formats', methods=['GET'])
def get_knock_out_stage_formats():
    formats = KnockOutStageFormat.query.all()
    formats_data = [{'format_id': fmt.format_id, 'format_name': fmt.format_name} for fmt in formats]
    return jsonify(formats_data)

@app.route('/api/create-tournament', methods=['POST'])
def create_tournament():
    try:
        data = request.json
        tournament_id = tournament.create_tournament(data)
        return jsonify({"message": "Tournament created", "tournament_id": tournament_id}), 201
    except Exception as e:
        # Print the error message to the server logs
        print(f"Error: {e}")
        # Return a response with the error message
        return jsonify({"error": str(e)}), 500

# Endpoint to fetch matches for the current round of a specific tournament
@app.route('/api/tournaments/<int:tournament_id>/matches', methods=['GET'])
def get_matches(tournament_id):
    round_number = request.args.get('round_number', type=int)
    
    if round_number is not None:
        current_round = Round.query.filter_by(tournament_id=tournament_id, round_number=round_number).first()
    else:
        current_round = Round.query.filter_by(tournament_id=tournament_id).order_by(Round.round_number.desc()).first()

    if not current_round:
        return jsonify({"error": "No matches found for the current round"}), 404

    matches = Match.query.filter_by(round_id=current_round.round_id).all()
    
    if not matches:
        return jsonify({"error": "No matches found for the current round"}), 404
    
    matches_data = [{
        "match_id": match.match_id,
        "group_number": match.group.group_number if match.group else None,
        "player1": {"player_id": match.player1.player_id, "name": match.player1.name},
        "player2": {"player_id": match.player2.player_id, "name": match.player2.name},
        "player3": {"player_id": match.player3.player_id, "name": match.player3.name} if match.player3 else None,
        "winner_id": match.winner_id
    } for match in matches]

    return jsonify(matches_data)


@app.route('/api/tournaments/<int:tournament_id>/rankings', methods=['GET'])
def get_player_rankings(tournament_id):
    try:
        # Step 1: Fetch the highest round number reached by each player
        highest_rounds = db.session.query(
            Player.player_id,
            Player.name,
            db.func.max(Round.round_number).label('highest_round')
        ).outerjoin(
            Match, db.or_(Match.player1_id == Player.player_id, Match.player2_id == Player.player_id)
        ).outerjoin(
            Round, Round.round_id == Match.round_id
        ).filter(
            Round.tournament_id == tournament_id
        ).group_by(Player.player_id).subquery()

        # Step 2: Fetch the number of matches won by each player
        matches_won = db.session.query(
            Player.player_id,
            db.func.count(Match.match_id).label('matches_won')
        ).outerjoin(
            Match, Match.winner_id == Player.player_id
        ).outerjoin(
            Round, Round.round_id == Match.round_id
        ).filter(
            Round.tournament_id == tournament_id
        ).group_by(Player.player_id).subquery()

        # Step 3: Fetch all players in the tournament
        all_players = db.session.query(
            Player.player_id,
            Player.name
        ).join(
            GroupPlayer, Player.player_id == GroupPlayer.player_id
        ).join(
            Group, Group.group_id == GroupPlayer.group_id
        ).filter(
            Group.tournament_id == tournament_id
        ).subquery()

        # Step 4: Combine the three queries
        rankings = db.session.query(
            all_players.c.player_id,
            all_players.c.name,
            db.func.coalesce(highest_rounds.c.highest_round, 0).label('highest_round'),
            db.func.coalesce(matches_won.c.matches_won, 0).label('matches_won')
        ).outerjoin(
            highest_rounds, all_players.c.player_id == highest_rounds.c.player_id
        ).outerjoin(
            matches_won, all_players.c.player_id == matches_won.c.player_id
        ).order_by(
            db.func.coalesce(highest_rounds.c.highest_round, 0).desc(),
            db.func.coalesce(matches_won.c.matches_won, 0).desc()
        ).all()

        # Step 5: Format the result
        players_data = [{
            "player_id": player.player_id,
            "name": player.name,
            "highest_round": player.highest_round,
            "matches_won": player.matches_won
        } for player in rankings]

        return jsonify(players_data), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500






# Endpoint to update the result of a specific match
@app.route('/api/matches/<int:match_id>', methods=['PUT'])
def update_match(match_id):
    data = request.json
    winner_id = data.get('winner_id')
    second_place_id = data.get('second_place_id')

    match = Match.query.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    match.winner_id = winner_id
    if second_place_id:
        match.second_place_id = second_place_id
    db.session.commit()

    return jsonify({"message": "Match result updated"}), 200

@app.route('/api/tournaments/<int:tournament_id>/rounds/<int:round_number>/matches', methods=['GET'])
def get_round_matches(tournament_id, round_number):
    try:
        round_instance = Round.query.filter_by(tournament_id=tournament_id, round_number=round_number).first()
        if not round_instance:
            return jsonify({"error": "No matches found for the specified round"}), 404

        matches = Match.query.filter_by(round_id=round_instance.round_id).all()
        matches_data = [{
            "match_id": match.match_id,
            "group_number": match.group.group_number if match.group else None,
            "player1": {"player_id": match.player1.player_id, "name": match.player1.name},
            "player2": {"player_id": match.player2.player_id, "name": match.player2.name},
            "player3": {"player_id": match.player3.player_id, "name": match.player3.name} if match.player3 else None,
            "winner_id": match.winner_id,
            "winner_name": match.winner.name if match.winner else None
        } for match in matches]

        return jsonify(matches_data), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# Endpoint to handle next round logic
@app.route('/api/next-round/<int:tournament_id>', methods=['POST'])
def next_round(tournament_id):
    try:
        tournament = Tournament.query.get(tournament_id)
        if not tournament:
            return jsonify({"error": "Tournament not found"}), 404

        # Determine the current round number
        current_round = Round.query.filter_by(tournament_id=tournament_id).order_by(Round.round_number.desc()).first()
        if not current_round:
            return jsonify({"error": "No rounds found for the tournament"}), 404

        # Get the list of players in the current round
        matches_in_current_round = Match.query.filter_by(round_id=current_round.round_id).all()
        players_in_current_round = [match.player1 for match in matches_in_current_round] + [match.player2 for match in matches_in_current_round]

        # Check whether to call create_knockout_stage or create_next_round_matches
        if tournament.group_stage_format_id != '1' and current_round.round_number == 1:
            print(f"Knock Out Called, {tournament.advancing_players}")
            create_knockout_stage(tournament.tournament_id, players_in_current_round, current_round.round_number, tournament.advancing_players)            
        else:
            create_next_round_matches(current_round.round_id, tournament.tournament_id)
            print(f"Next Round called")
        return jsonify({"message": f"Next round created"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500




@app.route('/api/players', methods=['GET', 'POST'])
def manage_players():
    if request.method == 'GET':
        try:
            players = Player.query.all()
            return jsonify([{'player_id': player.player_id, 'name': player.name} for player in players])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        try:
            new_player_data = request.json
            new_player = Player(name=new_player_data['name'])
            db.session.add(new_player)
            db.session.commit()
            return jsonify({'player_id': new_player.player_id, 'name': new_player.name}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/players/<int:player_id>', methods=['GET', 'PUT', 'DELETE'])
def player_detail(player_id):
    player = Player.query.get(player_id)
    if not player:
        return jsonify({"error": "Player not found"}), 404

    if request.method == 'GET':
        return jsonify({'player_id': player.player_id, 'name': player.name})

    elif request.method == 'PUT':
        try:
            updated_data = request.json
            player.name = updated_data.get('name', player.name)
            db.session.commit()
            return jsonify({'player_id': player.player_id, 'name': player.name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(player)
            db.session.commit()
            return jsonify({"message": "Player deleted"}), 204
        except Exception as e:
            return jsonify({"error": str(e)}), 500
@app.route('/api/tournaments/<int:tournament_id>', methods=['GET', 'PUT', 'DELETE'])
def tournament_detail(tournament_id):
    tournament = Tournament.query.get(tournament_id)
    if not tournament:
        return jsonify({"error": "Tournament not found"}), 404

    if request.method == 'GET':
        return jsonify({
            'tournament_id': tournament.tournament_id, 
            'name': tournament.name, 
            'group_stage_format_id': tournament.group_stage_format_id, 
            'knock_out_stage_format_id': tournament.knock_out_stage_format_id,
            'date': tournament.date.isoformat(),
            'advancing_players': tournament.advancing_players
        })

    elif request.method == 'PUT':
        try:
            updated_data = request.json
            tournament.name = updated_data.get('name', tournament.name)
            tournament.group_stage_format_id = updated_data.get('group_stage_format_id', tournament.group_stage_format_id)
            tournament.knock_out_stage_format_id = updated_data.get('knock_out_stage_format_id', tournament.knock_out_stage_format_id)
            db.session.commit()
            return jsonify({
                'tournament_id': tournament.tournament_id, 
                'name': tournament.name, 
                'group_stage_format_id': tournament.group_stage_format_id, 
                'knock_out_stage_format_id': tournament.knock_out_stage_format_id,
                'date': tournament.date.isoformat()
                
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(tournament)
            db.session.commit()
            return jsonify({"message": "Tournament deleted"}), 204
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/tournaments/<int:tournament_id>/rounds/<int:round_number>', methods=['GET'])
def get_round_by_number(tournament_id, round_number):
    try:
        # Fetch the round instance using the tournament_id and round_number
        round_instance = Round.query.filter_by(tournament_id=tournament_id, round_number=round_number).first()
        
        if not round_instance:
            return jsonify({"error": "Round not found"}), 404
        
        # Fetch matches for the specified round
        matches = Match.query.filter_by(round_id=round_instance.round_id).all()
        
        if not matches:
            return jsonify({"error": "No matches found for this round"}), 404
        
        matches_data = []
        for match in matches:
            match_data = {
                "match_id": match.match_id,
                "group_number": match.group.group_number if match.group else None,
                "player1": {"player_id": match.player1.player_id, "name": match.player1.name},
                "player2": {"player_id": match.player2.player_id, "name": match.player2.name},
                "player3": {"player_id": match.player3.player_id, "name": match.player3.name} if match.player3 else None,
                "winner_id": match.winner_id,
                "second_place": match.second_place
            }
            matches_data.append(match_data)
        
        return jsonify({
            "round_id": round_instance.round_id,
            "round_number": round_instance.round_number,
            "matches": matches_data
        }), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/api/tournaments/<int:tournament_id>/tiebreakers', methods=['POST'])
def create_tiebreakers(tournament_id):
    try:
        current_round = Round.query.filter_by(tournament_id=tournament_id).order_by(Round.round_number.desc()).first()
        if not current_round:
            return jsonify({"error": "No current round found"}), 404

        # Determine the number of advancing players
        num_advancing_players = Tournament.query.filter_by(tournament_id=tournament_id).first().advancing_players  # You can adjust this value as needed

        tiebreaker_matches = create_tiebreaker_matches(tournament_id, current_round.round_id, num_advancing_players)
        
        tiebreaker_data = [{
            "match_id": match.match_id,
            "group_number": match.group.group_number if match.group else None,
            "player1": {"player_id": match.player1.player_id, "name": match.player1.name},
            "player2": {"player_id": match.player2.player_id, "name": match.player2.name},
            "player3": {"player_id": match.player3.player_id, "name": match.player3.name} if match.player3 else None,
        } for match in tiebreaker_matches]

        return jsonify({"tiebreakers": tiebreaker_data}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tournaments/<int:tournament_id>/tiebreakers/check', methods=['GET'])
def check_tiebreakers(tournament_id):
    try:
        current_round = Round.query.filter_by(tournament_id=tournament_id).order_by(Round.round_number.desc()).first()
        num_advancing_players = Tournament.query.filter_by(tournament_id=tournament_id).first().advancing_players
        if not current_round:
            return jsonify({"error": "No current round found"}), 404

        matches_in_round = Match.query.filter_by(round_id=current_round.round_id).all()
        tiebreakers = []

        groups = Group.query.filter_by(tournament_id=tournament_id).all()
        for group in groups:
            group_winners = []
            for gp in group.players:
                player = gp.player
                matches_won = sum(1 for match in matches_in_round if match.winner_id == player.player_id)
                matches_won += sum(0.5 for match in matches_in_round if match.second_place_id == player.player_id)
                group_winners.append({
                    "player": player,
                    "matches_won": matches_won,
                    "group_id": group.group_id
                })
                print(f"Sorted Winners {player}: {matches_won}")
            sorted_winners = sorted(group_winners, key=lambda p: p['matches_won'], reverse=True)

            # Check for enough players before accessing list indices
            if len(sorted_winners) <= num_advancing_players:
                continue

            # Identify the top win counts for advancing players
            top_win_counts = sorted(set(p['matches_won'] for p in sorted_winners), reverse=True)[:num_advancing_players]
            relevant_tied_players = []
            for win_count in top_win_counts:
                players_with_win_count = [p for p in sorted_winners if p['matches_won'] == win_count]
                if len(players_with_win_count) > 1:
                    relevant_tied_players.extend(players_with_win_count)
                if len(relevant_tied_players) >= num_advancing_players:
                    break
            print(f"Tied Player Relevant {relevant_tied_players}")

            if len(relevant_tied_players) > 1 and len(relevant_tied_players) > num_advancing_players:
                # Handle 3-player match for uneven number of ties first
                if len(relevant_tied_players) % 2 == 1:
                    tiebreakers.append({
                        "player1": {"player_id": relevant_tied_players[-3]['player'].player_id, "name": relevant_tied_players[-3]['player'].name},
                        "player2": {"player_id": relevant_tied_players[-2]['player'].player_id, "name": relevant_tied_players[-2]['player'].name},
                        "player3": {"player_id": relevant_tied_players[-1]['player'].player_id, "name": relevant_tied_players[-1]['player'].name}
                    })
                    relevant_tied_players = relevant_tied_players[:-3]  # Remove the last 3 players from the ties list

                # Handle 2-player matches
                tiebreakers.extend([{
                    "player1": {"player_id": relevant_tied_players[i]['player'].player_id, "name": relevant_tied_players[i]['player'].name},
                    "player2": {"player_id": relevant_tied_players[i + 1]['player'].player_id, "name": relevant_tied_players[i + 1]['player'].name}
                } for i in range(0, len(relevant_tied_players), 2) if i + 1 < len(relevant_tied_players)])

        return jsonify({"tiebreakers": tiebreakers}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)