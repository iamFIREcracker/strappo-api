"""Add token table

Revision ID: 31acdf80b348
Revises: 3744e5c447f3
Create Date: 2013-06-02 15:00:55.725010

"""

# revision identifiers, used by Alembic.
revision = '31acdf80b348'
down_revision = '3744e5c447f3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('token',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('token')
    ### end Alembic commands ###