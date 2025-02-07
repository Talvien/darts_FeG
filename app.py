from flask import Flask, jsonify, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from models import db, Player, Tournament, TournamentFormat, TournamentPlayerlist, Match
import datetime

app = Flask(__name__)
app.secret_key = b'***************************************'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database_darts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

CORS(app)
migrate = Migrate(app, db)
db.init_app(app)

# CRUD operations for Players
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

# CRUD operations for Tournaments
@app.route('/api/tournaments', methods=['GET', 'POST'])
def manage_tournaments():
    if request.method == 'GET':
        try:
            tournaments = Tournament.query.all()
            return jsonify([{'tournament_id': tournament.tournament_id, 'name': tournament.name, 'format_id': tournament.format_id} for tournament in tournaments])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        try:
            tournament_data = request.json
            new_tournament = Tournament(
                name=tournament_data['name'],
                format_id=tournament_data['format_id'],
                date=datetime.date.today()
            )
            db.session.add(new_tournament)
            db.session.flush()  # Flush to get the tournament_id

            players = tournament_data['players']
            num_players = len(players)
            groups = int(tournament_data['groups']) if tournament_data['groups'] != 'Auto' else (num_players // 8) + (1 if num_players % 8 != 0 else 0)
            players_per_group = (num_players // groups) + (1 if num_players % groups != 0 else 0)

            # Assign players to groups
            player_groups = []
            for i in range(groups):
                player_groups.append(players[i * players_per_group:(i + 1) * players_per_group])

            # Create player list entries with group assignment
            for group_id, group_players in enumerate(player_groups, 1):
                for player_id in group_players:
                    new_playerlist = TournamentPlayerlist(
                        tournament_id=new_tournament.tournament_id,
                        player_id=player_id,
                        group_id=group_id
                    )
                    db.session.add(new_playerlist)

            # Create matches for the round-robin format
            for group_id, group_players in enumerate(player_groups, 1):
                for i in range(len(group_players)):
                    for j in range(i + 1, len(group_players)):
                        new_match = Match(
                            tournament_id=new_tournament.tournament_id,
                            player1_id=group_players[i],
                            player2_id=group_players[j]
                        )
                        db.session.add(new_match)

            db.session.commit()
            return jsonify({'tournament_id': new_tournament.tournament_id, 'name': new_tournament.name}), 201
        except Exception as e:
            db.session.rollback()
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

# CRUD operations for Tournament Player List
@app.route('/api/tournament-playerlist', methods=['GET', 'POST'])
def manage_tournament_playerlist():
    if request.method == 'GET':
        try:
            playerlists = TournamentPlayerlist.query.all()
            return jsonify([{'playerlist_id': pl.playerlist_id, 'tournament_id': pl.tournament_id, 'player_id': pl.player_id} for pl in playerlists])
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'POST':
        try:
            new_playerlist_data = request.json
            new_playerlist = TournamentPlayerlist(tournament_id=new_playerlist_data['tournament_id'], player_id=new_playerlist_data['player_id'])
            db.session.add(new_playerlist)
            db.session.commit()
            return jsonify({'playerlist_id': new_playerlist.playerlist_id, 'tournament_id': new_playerlist.tournament_id, 'player_id': new_playerlist.player_id}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/tournament-playerlist/<int:playerlist_id>', methods=['GET', 'PUT', 'DELETE'])
def tournament_playerlist_detail(playerlist_id):
    playerlist = TournamentPlayerlist.query.get(playerlist_id)
    if not playerlist:
        return jsonify({"error": "Tournament player list entry not found"}), 404

    if request.method == 'GET':
        return jsonify({'playerlist_id': playerlist.playerlist_id, 'tournament_id': playerlist.tournament_id, 'player_id': playerlist.player_id})

    elif request.method == 'PUT':
        try:
            updated_data = request.json
            playerlist.tournament_id = updated_data.get('tournament_id', playerlist.tournament_id)
            playerlist.player_id = updated_data.get('player_id', playerlist.player_id)
            db.session.commit()
            return jsonify({'playerlist_id': playerlist.playerlist_id, 'tournament_id': playerlist.tournament_id})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    elif request.method == 'DELETE':
        try:
            db.session.delete(playerlist)
            db.session.commit()
            return jsonify({"message": "Tournament player list entry deleted"}), 204
        except Exception as e:
            return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)