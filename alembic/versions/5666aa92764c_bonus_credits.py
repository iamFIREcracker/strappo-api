"""bonus credits

Revision ID: 5666aa92764c
Revises: 32766ce2c5b6
Create Date: 2015-02-01 16:16:42.174984

"""

# revision identifiers, used by Alembic.
revision = '5666aa92764c'
down_revision = '32766ce2c5b6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('payment', sa.Column('bonus_credits', sa.Integer(), nullable=True))
    op.add_column('payment', sa.Column('promo_id', sa.String(), nullable=True))
    #op.create_foreign_key(None, 'payment', 'promo', ['promo_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('payment', 'promo_code')
    op.drop_column('payment', 'bonus_credits')
    ### end Alembic commands ###
