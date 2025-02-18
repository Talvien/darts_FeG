from flask import jsonify, make_response
from datetime import datetime
from pytz import timezone
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models import db, Player, Tournament, Group, GroupPlayer, Round, Match
import random

def create_tournament(data):
    name = data['name']
    format_id = data['format_id']
    num_groups = data.get('num_groups', 'Auto')
    selected_player_ids = data['players']
    

    try:
        # Convert player IDs to Player objects
        selected_players = Player.query.filter(Player.player_id.in_(selected_player_ids)).all()
        if not selected_players:
            raise ValueError("Selected players not found.")

        # Use the current timestamp in CET/CEST
        cet = timezone('Europe/Berlin')
        date = datetime.now(cet).date()

        # Create a new tournament
        tournament = Tournament(name=name, format_id=format_id, date=date)
        db.session.add(tournament)
        db.session.flush()  # Flush to get the tournament ID

        # Create the first round
        first_round = Round(tournament_id=tournament.tournament_id, round_number=1)
        db.session.add(first_round)
        db.session.flush()  # Flush to get the round ID

        # Apply specific logic based on the format
        if format_id == '3':
            if num_groups == 'Auto':
                create_groups_auto(tournament.tournament_id, selected_players, first_round.round_id)
            else:
                create_groups_manual(tournament.tournament_id, selected_players, num_groups, first_round.round_id)
        else:
            if num_groups == 'Auto':
                create_groups_auto(tournament.tournament_id, selected_players, first_round.round_id)
            else:
                create_groups_manual(tournament.tournament_id, selected_players, num_groups, first_round.round_id)

        db.session.commit()  # Commit transaction
        return tournament.tournament_id

    except (SQLAlchemyError, IntegrityError) as e:
        print(f"SQLAlchemyError: {e}")
        return jsonify({"error": "Database error occurred"}), 500

    except ValueError as e:
        print(f"ValueError: {e}")
        return jsonify({"error": str(e)}), 400

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

def create_groups_auto(tournament_id, players, round_id):
    num_players = len(players)
    if num_players <= 6:
        num_groups = 1
    elif num_players <= 12:
        num_groups = 2
    elif num_players <= 18:
        num_groups = 3
    else:
        num_groups = 4
    create_groups(tournament_id, players, num_groups, round_id)

def create_groups_manual(tournament_id, players, num_groups, round_id):
    create_groups(tournament_id, players, num_groups, round_id)

def create_groups(tournament_id, players, num_groups, round_id):
    groups = []
    for i in range(num_groups):
        group = Group(tournament_id=tournament_id, group_name=f"Gruppe {i+1}", group_number=i+1)
        groups.append(group)
        db.session.add(group)
    db.session.flush()

    random.shuffle(players)

    for i, player in enumerate(players):
        group = groups[i % num_groups]
        group_player = GroupPlayer(group_id=group.group_id, player_id=player.player_id)
        db.session.add(group_player)
    db.session.flush()

    for group in groups:
        create_group_matches(group, round_id)

def create_group_matches(group, round_id):
    players = group.players
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            match = Match(round_id=round_id, group_id=group.group_id, player1_id=players[i].player_id, player2_id=players[j].player_id)
            db.session.add(match)
    db.session.flush()



def determine_advancements(groups, tournament_id, round_number, ranks=2):
    advancing_players = []

    # Fetch the round instance using the round_number
    current_round = Round.query.filter_by(tournament_id=tournament_id, round_number=round_number).first()

    if current_round is not None:
        matches_in_round = Match.query.filter_by(round_id=current_round.round_id).all()
        print(f"Matches in round {current_round.round_number}: {matches_in_round}")
    else:
        matches_in_round = []

    for group in groups:
        group_players = []
        for gp in group.players:
            player = gp.player
            matches_won = sum(1 for match in matches_in_round if match.winner_id == player.player_id)
            print(f"Player ID: {player.player_id}, Matches won: {matches_won}")
            group_players.append({
                "player": player,
                "matches_won": matches_won
            })
        sorted_players = sorted(group_players, key=lambda p: p['matches_won'], reverse=True)
        advancing_players.extend([p['player'] for p in sorted_players[:ranks]])  # Top 2 players from each group
    print(f"Advancing Players: {advancing_players}")
    return advancing_players


def create_next_round_matches(advancing_players, round_number, tournament_id):
    next_round = Round(tournament_id=tournament_id, round_number=round_number)
    db.session.add(next_round)
    db.session.flush()  # Flush to get the round ID

    next_round_matches = []
    for i in range(0, len(advancing_players), 2):
        if i + 1 < len(advancing_players):
            match = Match(tournament_id=tournament_id, round_id=next_round.round_id, player1_id=advancing_players[i].player_id, player2_id=advancing_players[i+1].player_id)
            next_round_matches.append(match)
            db.session.add(match)
    db.session.commit()
    print(f"Created matches for round {round_number}: {next_round_matches}")
    return next_round_matches


