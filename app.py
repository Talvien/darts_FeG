from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Player, Tournament, TournamentFormat, Match, Round, Group, GroupPlayer
import tournament

app = Flask(__name__)
app.secret_key = b'***************************************'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database_darts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
migrate = Migrate(app, db)
db.init_app(app)

# CRUD operations for Players

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
    matches_data = [{
        "match_id": match.match_id,
        "group_number": match.group.group_number if match.group else None,
        "player1": {"player_id": match.player1.player_id, "name": match.player1.name},
        "player2": {"player_id": match.player2.player_id, "name": match.player2.name},
        "winner_id": match.winner_id
    } for match in matches]

    return jsonify(matches_data)


# Endpoint to update the result of a specific match
@app.route('/api/matches/<int:match_id>', methods=['PUT'])
def update_match(match_id):
    data = request.json
    winner_id = data.get('winner_id')

    match = Match.query.get(match_id)
    if not match:
        return jsonify({"error": "Match not found"}), 404

    match.winner_id = winner_id
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
        current_round = Round.query.filter_by(tournament_id=tournament_id).order_by(Round.round_number.desc()).first()
        current_round_number = current_round.round_number

        groups = Group.query.filter_by(tournament_id=tournament_id).all()
        advancing_players = tournament.determine_advancements(groups, tournament_id, current_round_number)
        next_round_number = current_round_number + 1

        next_round_matches = tournament.create_next_round_matches(advancing_players, next_round_number, tournament_id)

        return jsonify({
            "message": "Next round matches created",
            "matches": [match.match_id for match in next_round_matches]
        }), 201
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


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

# CRUD operations for Tournament Formats
@app.route('/api/tournament-formats', methods=['GET', 'POST'])
def manage_tournament_formats():
    if request.method == 'GET':
        try:
            formats = TournamentFormat.query.all()
            return jsonify([{'format_id': fmt.format_id, 'format_name': fmt.format_name, 'description': fmt.description} for fmt in formats])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        try:
            new_format_data = request.json
            new_format = TournamentFormat(format_name=new_format_data['format_name'], description=new_format_data['description'])
            db.session.add(new_format)
            db.session.commit()
            return jsonify({'format_id': new_format.format_id, 'format_name': new_format.format_name}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/tournament-formats/<int:format_id>', methods=['GET', 'PUT', 'DELETE'])
def tournament_format_detail(format_id):
    tournament_format = TournamentFormat.query.get(format_id)
    if not tournament_format:
        return jsonify({"error": "Tournament format not found"}), 404

    if request.method == 'GET':
        return jsonify({'format_id': tournament_format.format_id, 'format_name': tournament_format.format_name, 'description': tournament_format.description})

    elif request.method == 'PUT':
        try:
            updated_data = request.json
            tournament_format.format_name = updated_data.get('format_name', tournament_format.format_name)
            tournament_format.description = updated_data.get('description', tournament_format.description)
            db.session.commit()
            return jsonify({'format_id': tournament_format.format_id, 'format_name': tournament_format.format_name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(tournament_format)
            db.session.commit()
            return jsonify({"message": "Tournament format deleted"}), 204
        except Exception as e:
            return jsonify({"error": str(e)}), 500



@app.route('/api/tournaments/<int:tournament_id>', methods=['GET', 'PUT', 'DELETE'])
def tournament_detail(tournament_id):
    tournament = Tournament.query.get(tournament_id)
    if not tournament:
        return jsonify({"error": "Tournament not found"}), 404

    if request.method == 'GET':
        return jsonify({'tournament_id': tournament.tournament_id, 'name': tournament.name, 'format_id': tournament.format_id})

    elif request.method == 'PUT':
        try:
            updated_data = request.json
            tournament.name = updated_data.get('name', tournament.name)
            tournament.format_id = updated_data.get('format_id', tournament.format_id)
            db.session.commit()
            return jsonify({'tournament_id': tournament.tournament_id, 'name': tournament.name})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(tournament)
            db.session.commit()
            return jsonify({"message": "Tournament deleted"}), 204
        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True)