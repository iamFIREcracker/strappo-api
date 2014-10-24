"""add feedback table

Revision ID: 524100bb379e
Revises: 28d5a7cc2f71
Create Date: 2014-10-23 22:55:06.711893

"""

# revision identifiers, used by Alembic.
revision = '524100bb379e'
down_revision = '28d5a7cc2f71'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('feedback',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('feedback')
    ### end Alembic commands ###
