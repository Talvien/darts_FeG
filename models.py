from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.associationproxy import association_proxy

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
})

db = SQLAlchemy(metadata=metadata)

class Player(db.Model):
    __tablename__ = 'players'

    player_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

class GroupStageFormat(db.Model):
    __tablename__ = 'group_stage_formats'
    format_id = db.Column(db.Integer, primary_key=True)
    format_name = db.Column(db.String(50), nullable=False)

class KnockOutStageFormat(db.Model):
    __tablename__ = 'knock_out_stage_formats'
    format_id = db.Column(db.Integer, primary_key=True)
    format_name = db.Column(db.String(50), nullable=False)


class Tournament(db.Model):
    __tablename__ = 'tournaments'

    tournament_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    date = db.Column(db.Date)
    group_stage_format_id = db.Column(db.Integer, db.ForeignKey('group_stage_formats.format_id'), nullable=True)
    knock_out_stage_format_id = db.Column(db.Integer, db.ForeignKey('knock_out_stage_formats.format_id'), nullable=True)
    advancing_players = db.Column(db.Integer, nullable=True)

    group_stage_format = db.relationship('GroupStageFormat', backref=db.backref('tournaments', lazy=True))
    knock_out_stage_format = db.relationship('KnockOutStageFormat', backref=db.backref('tournaments', lazy=True))
    rounds = db.relationship('Round', backref='tournament', cascade='all, delete-orphan')
    groups = db.relationship('Group', backref='tournament', cascade='all, delete-orphan')

class Group(db.Model):
    __tablename__ = 'groups'

    group_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.tournament_id'))
    group_number = db.Column(db.Integer, nullable=False, server_default = '1')
    group_name = db.Column(db.String(80), nullable=False)

    players = db.relationship('GroupPlayer', backref='group', cascade='all, delete-orphan')
    matches = db.relationship('Match', backref='group', cascade='all, delete-orphan') 

class GroupPlayer(db.Model):
    __tablename__ = 'group_players'

    group_player_id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'))
    player_id = db.Column(db.Integer, db.ForeignKey('players.player_id'))

    player = db.relationship('Player', backref='group_entries')

class Round(db.Model):
    __tablename__ = 'rounds'

    round_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.tournament_id'))
    round_number = db.Column(db.Integer, nullable=False)

    matches = db.relationship('Match', backref='round', cascade='all, delete-orphan')

class Match(db.Model):
    __tablename__ = 'matches'

    match_id = db.Column(db.Integer, primary_key=True)
    tournament_id = db.Column(db.Integer, db.ForeignKey('tournaments.tournament_id'))
    round_id = db.Column(db.Integer, db.ForeignKey('rounds.round_id'))
    group_id = db.Column(db.Integer, db.ForeignKey('groups.group_id'), nullable=True)  # Optional relationship with Group
    player1_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=False)
    player3_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=True)
    score_player1 = db.Column(db.Integer)
    score_player2 = db.Column(db.Integer)
    winner_id = db.Column(db.Integer, db.ForeignKey('players.player_id'))
    second_place_id = db.Column(db.Integer, db.ForeignKey('players.player_id'), nullable=True)

    tournament = db.relationship('Tournament', backref='matches')
    player1 = db.relationship('Player', foreign_keys=[player1_id], backref='matches_as_player1')
    player2 = db.relationship('Player', foreign_keys=[player2_id], backref='matches_as_player2')
    player3 = db.relationship('Player', foreign_keys=[player3_id], backref='matches_as_player3')

    winner = db.relationship('Player', foreign_keys=[winner_id])
    second_place = db.relationship('Player', foreign_keys=[second_place_id])
