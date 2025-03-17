"""Add second_place to matches and change matches_won to float

Revision ID: 4865d8f39f6f
Revises: 7ef95cc2ae4e
Create Date: 2025-02-24 15:01:21.775823

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4865d8f39f6f'
down_revision = '7ef95cc2ae4e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.add_column(sa.Column('second_place_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_matches_second_place_id_players'), 'players', ['second_place_id'], ['player_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('matches', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_matches_second_place_id_players'), type_='foreignkey')
        batch_op.drop_column('second_place_id')

    # ### end Alembic commands ###
