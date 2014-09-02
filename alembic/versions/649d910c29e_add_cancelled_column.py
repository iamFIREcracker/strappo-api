"""Add cancelled column to drive_request

Revision ID: 649d910c29e
Revises: 2699e1b1f892
Create Date: 2014-07-28 21:27:11.266265

"""

# revision identifiers, used by Alembic.
revision = '649d910c29e'
down_revision = '2699e1b1f892'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('drive_request', sa.Column('cancelled', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('drive_request', 'cancelled')
    ### end Alembic commands ###