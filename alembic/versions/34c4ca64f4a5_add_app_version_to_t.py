"""add app_version to traces

Revision ID: 34c4ca64f4a5
Revises: 524100bb379e
Create Date: 2014-10-26 11:45:13.049581

"""

# revision identifiers, used by Alembic.
revision = '34c4ca64f4a5'
down_revision = '524100bb379e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('trace', sa.Column('app_version', sa.String(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('trace', 'app_version')
    ### end Alembic commands ###