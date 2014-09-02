"""add response time

Revision ID: 2f6c56f0af54
Revises: 353e2e032af5
Create Date: 2014-07-07 16:55:48.707838

"""

# revision identifiers, used by Alembic.
revision = '2f6c56f0af54'
down_revision = '353e2e032af5'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drive_request', sa.Column('response_time', sa.Integer(), server_default='0', nullable=False))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('drive_request', 'response_time')
    ### end Alembic commands ###