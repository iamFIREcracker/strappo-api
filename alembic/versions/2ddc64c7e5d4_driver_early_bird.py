"""driver early bird

Revision ID: 2ddc64c7e5d4
Revises: 34c4ca64f4a5
Create Date: 2014-10-29 21:57:49.563743

"""

# revision identifiers, used by Alembic.
revision = '2ddc64c7e5d4'
down_revision = '34c4ca64f4a5'

from alembic import op
import sqlalchemy as sa

from app.models import User
from app.repositories.perks import PerksRepository
from app.weblib.db import expunged
from app.weblib.db import create_session


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    ### end Alembic commands ###
    orm = create_session()
    driver_early_bird = PerksRepository.\
        add_driver_perk(name=PerksRepository.EARLY_BIRD_DRIVER_NAME,
                        eligible_for=7,
                        active_for=60,
                        fixed_rate=0.0,
                        multiplier=2.0)
    orm.add(driver_early_bird)
    for u in User.query:
        u = expunged(u, User.session)
        orm.add(PerksRepository.eligiblify_driver_perk(u, driver_early_bird))
        orm.add(u)
    orm.commit()


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    ### end Alembic commands ###
    pass