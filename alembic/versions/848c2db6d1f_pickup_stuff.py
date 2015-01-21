"""pickup stuff

Revision ID: 848c2db6d1f
Revises: 1fd451906279
Create Date: 2015-01-21 21:36:51.010020

"""

# revision identifiers, used by Alembic.
revision = '848c2db6d1f'
down_revision = '1fd451906279'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drive_request', sa.Column('offered_pickup_time', sa.DateTime(), nullable=True))
    op.add_column('passenger', sa.Column('pickup_time_new', sa.DateTime(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('passenger', 'pickup_time_new')
    op.drop_column('drive_request', 'offered_pickup_time')
    ### end Alembic commands ###
