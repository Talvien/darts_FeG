from flask import jsonify, make_response
from datetime import datetime
from pytz import timezone
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from models import db, Player, Tournament, Group, GroupPlayer, Round, Match
import random

def create_tournament(data):
    name = data['name']
    group_stage_format_id = data['group_stage_format_id']
    knock_out_stage_format_id = data['knock_out_stage_format_id']
    num_groups = data.get('num_groups', 'Auto')
    advancing_players = data.get('advancing_players', 2)
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
        tournament = Tournament(name=name, group_stage_format_id=group_stage_format_id, knock_out_stage_format_id=knock_out_stage_format_id, date=date, advancing_players=advancing_players)
        db.session.add(tournament)
        db.session.flush()  # Flush to get the tournament ID

        # Create the first round
        first_round = Round(tournament_id=tournament.tournament_id, round_number=1)
        db.session.add(first_round)
        db.session.flush()  # Flush to get the round ID

        # Apply specific logic based on the format
        if group_stage_format_id == '1':
            create_knockout_stage(tournament.tournament_id, selected_players, first_round.round_number)
        elif num_groups == 'Auto':
            create_groups_auto(tournament.tournament_id, selected_players, first_round.round_id, group_stage_format_id)
        else:
            create_groups(tournament.tournament_id, selected_players, num_groups, first_round.round_id, group_stage_format_id)

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
    
def create_knockout_stage(tournament_id, players, round_number, num_advancing_players):
    # Create matches for the knockout stage
    advancing_players = []
    current_round = Round.query.filter_by(tournament_id=tournament_id, round_number=round_number).first()
    print(f"Current Round: {current_round}")

    if num_advancing_players:
        print(f"Round Number: {round_number}")

        if current_round is not None:
            next_round_number = round_number + 1
            next_round = Round(tournament_id=tournament_id, round_number=next_round_number)
            db.session.add(next_round)
            db.session.flush()  # Flush to get the next_round.round_id

            print(f"Next Round: {next_round} - Number: {next_round_number}")

            matches_in_round = Match.query.filter_by(round_id=current_round.round_id).all()
            print(f"Matches in Current Round: {matches_in_round}")

            groups = Group.query.filter_by(tournament_id=tournament_id).all()
            group_players = []

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
                sorted_winners = sorted(group_winners, key=lambda p: p['matches_won'], reverse=True)
                group_players.append(sorted_winners[:num_advancing_players])  # Top players from each group
                print(f"Group Winners for Group {group.group_id}: {sorted_winners[:num_advancing_players]}")

            if len(groups) == 1:
                # Special case for single group
                single_group_players = group_players[0]
                for i in range(0, len(single_group_players), 2):
                    if i + 1 < len(single_group_players):
                        match = Match(tournament_id=tournament_id, round_id=next_round.round_id, player1_id=single_group_players[i]['player'].player_id, player2_id=single_group_players[i + 1]['player'].player_id)
                        print(f"Match: Player 1 : {single_group_players[i]['player'].player_id}, Player 2: {single_group_players[i + 1]['player'].player_id}")
                        db.session.add(match)
            else:
                # Ensure correct matching between groups
                first_seeds = [(group[0]['player'], group[0]['group_id']) for group in group_players if len(group) > 0]
                second_seeds = [(group[1]['player'], group[1]['group_id']) for group in group_players if len(group) > 1]

                print(f"First Seeds: {first_seeds}")
                print(f"Second Seeds: {second_seeds}")

                # Match second seed with first seed from another group
                for first_seed in first_seeds:
                    for second_seed in second_seeds:
                        if first_seed[1] != second_seed[1]:  # Ensure different groups
                            match = Match(tournament_id=tournament_id, round_id=next_round.round_id, player1_id=second_seed[0].player_id, player2_id=first_seed[0].player_id)
                            print(f"Match: Player 1 : {second_seed[0].player_id}, Player 2: {first_seed[0].player_id}")
                            db.session.add(match)
                            second_seeds.remove(second_seed)  # Remove matched second seed
                            break


    else:
        # Randomly match players if there's no group stage
        random.shuffle(players) 
        for i in range(0, len(players), 2):
            if i + 1 < len(players):
                match = Match(tournament_id=tournament_id, round_id=current_round.round_id, player1_id=players[i].player_id, player2_id=players[i + 1].player_id)
                db.session.add(match)
    db.session.commit()
    db.session.flush()




def create_groups_auto(tournament_id, players, round_id, format_id):
    num_players = len(players)
    if num_players <= 5:
        num_groups = 1
    elif num_players <= 13:
        num_groups = 2
    else:
        num_groups = 4
    create_groups(tournament_id, players, num_groups, round_id, format_id)

def create_groups(tournament_id, players, num_groups, round_id, format_id):
    print(f"Num Groups {num_groups}")
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
        create_group_matches(group, round_id, format_id), 

def create_group_matches(group, round_id, format_id):
    players = group.players
    if format_id != '1':
        for i in range(len(players)):
            for j in range(i + 1, len(players)):
                match = Match(round_id=round_id, group_id=group.group_id, player1_id=players[i].player_id, player2_id=players[j].player_id)
                db.session.add(match)
                if format_id == '3':  # Each player should play each other twice
                    reverse_match = Match(round_id=round_id, group_id=group.group_id, player1_id=players[j].player_id, player2_id=players[i].player_id)
                    db.session.add(reverse_match)
    db.session.flush()


def create_next_round_matches(current_round_id, tournament_id):
    current_round = Round.query.filter_by(tournament_id=tournament_id, round_id=current_round_id).first()
    next_round_number = current_round.round_number + 1 if current_round else 1
    next_round = Round(tournament_id=tournament_id, round_number=next_round_number)
    db.session.add(next_round)
    db.session.commit()
    db.session.flush()  # Flush to get the round ID

    print(f"Current Round: {current_round}")
    print(f"Next Round Number: {next_round_number}")
    print(f"Next Round: {next_round}")

    next_round_matches = []

    # Determine if the tournament has a group phase
    tournament = Tournament.query.filter_by(tournament_id=tournament_id).first()
    has_group_phase = tournament.group_stage_format_id != '1'
    format_id = tournament.knock_out_stage_format_id

    print(f"Tournament: {tournament}")
    print(f"Format ID: {format_id}")

    # Determine advancing players from the current round
    matches_in_current_round = Match.query.filter_by(round_id=current_round_id).all()
    advancing_players = [
        match.winner_id for match in matches_in_current_round if match.winner_id is not None
    ]

    print(f"Matches in Current Round: {matches_in_current_round}")
    print(f"Advancing Players: {advancing_players}")

    if format_id == 2:  # Single elimination
        print(f"In Single Elimination jetzt: {format_id}")
        random.shuffle(advancing_players)
        for i in range(0, len(advancing_players), 2):
            if i + 1 < len(advancing_players):
                match = Match(tournament_id=tournament_id, round_id=next_round.round_id, player1_id=advancing_players[i], player2_id=advancing_players[i+1])
                next_round_matches.append(match)
                db.session.add(match)
        print(f"Single Elimination Matches: {next_round_matches}")
    elif format_id == 3:  # Double elimination
        winners = advancing_players
        random.shuffle(winners)
        for i in range(0, len(winners), 2):
            if i + 1 < len(winners):
                match = Match(tournament_id=tournament_id, round_id=next_round.round_id, player1_id=winners[i], player2_id=winners[i+1])
                next_round_matches.append(match)
                db.session.add(match)
        print(f"Double Elimination Matches (Winners): {next_round_matches}")

        # Handle losers' bracket
        if next_round_number > 1 or not has_group_phase:  # Consider only losses in knockout rounds if there was a group phase
            previous_round = Round.query.filter_by(tournament_id=tournament_id, round_number=next_round_number - 1).first()
            if previous_round:
                previous_matches = Match.query.filter_by(round_id=previous_round.round_id).all()
                print(f"Previous Round: {previous_round}")
                print(f"Previous Matches: {previous_matches}")

                # Track the number of losses for each player
                player_losses = {}
                for match in previous_matches:
                    if match.loser_id:
                        if match.loser_id not in player_losses:
                            player_losses[match.loser_id] = 1
                        else:
                            player_losses[match.loser_id] += 1
                print(f"Player Losses: {player_losses}")

                # Collect players with only one loss
                losers = [match.loser_id for match in previous_matches if match.loser_id and player_losses[match.loser_id] == 1]
                random.shuffle(losers)
                print(f"Losers: {losers}")

                for i in range(0, len(losers), 2):
                    if i + 1 < len(losers):
                        match = Match(tournament_id=tournament_id, round_id=next_round.round_id, player1_id=losers[i], player2_id=losers[i+1])
                        next_round_matches.append(match)
                        db.session.add(match)
        print(f"Double Elimination Matches (Losers): {next_round_matches}")

    db.session.commit()
    print(f"Created matches for round {next_round_number}: {next_round_matches}")
    return next_round_matches


def create_tiebreaker_matches(tournament_id, current_round_id, num_advancing_players):
    current_round = Round.query.filter_by(tournament_id=tournament_id, round_id=current_round_id).first()
    matches_in_round = Match.query.filter_by(round_id=current_round.round_id).all()

    groups = Group.query.filter_by(tournament_id=tournament_id).all()
    tiebreaker_matches = []

    for group in groups:
        group_winners = []
        for gp in group.players:
            player = gp.player
            matches_won = sum(1 for match in matches_in_round if match.winner_id == player.player_id)
            matches_won += sum(0.5 for match in matches_in_round if match.second_place_id == player.player_id)
            group_winners.append({
                "player": player,
                "matches_won": matches_won
            })
            print(f"Sorted Winners {player}: {matches_won}")
        sorted_winners = sorted(group_winners, key=lambda p: p['matches_won'], reverse=True)
        for winner in sorted_winners:
            print(f"{winner}")

        if len(sorted_winners) <= num_advancing_players:
            print(f"Abbruch getriggert, Sorted Winners <= Advancing players")
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

        # Special case: if only one group and advancing players is 2, no tiebreaker needed for ties between 1st and 2nd place
        if len(relevant_tied_players) == 2 and num_advancing_players == 2:
            continue

        if len(relevant_tied_players) > 1 and len(relevant_tied_players) > num_advancing_players:
            # Handle 3-player match for uneven number of ties first
            if len(relevant_tied_players) % 2 == 1:
                print(f"Three Player handle triggered in {group.group_number}")

                match = Match(
                    tournament_id=tournament_id,
                    round_id=current_round.round_id,
                    player1_id=relevant_tied_players[-3]['player'].player_id,
                    player2_id=relevant_tied_players[-2]['player'].player_id,
                    player3_id=relevant_tied_players[-1]['player'].player_id
                )
                tiebreaker_matches.append(match)
                db.session.add(match)

                relevant_tied_players = relevant_tied_players[:-3]  # Remove the last 3 players from the ties list

            # Handle 2-player matches
            for i in range(0, len(relevant_tied_players), 2):
                match = Match(tournament_id=tournament_id, round_id=current_round.round_id, player1_id=relevant_tied_players[i]['player'].player_id, player2_id=relevant_tied_players[i + 1]['player'].player_id)
                tiebreaker_matches.append(match)
                db.session.add(match)

    db.session.commit()
    print(f"Tiebreaker matches created: {tiebreaker_matches}")
    return tiebreaker_matches

