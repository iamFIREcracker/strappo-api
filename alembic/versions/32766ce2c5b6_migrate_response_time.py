"""migrate response_time

Revision ID: 32766ce2c5b6
Revises: 848c2db6d1f
Create Date: 2015-01-22 00:22:14.183895

"""

# revision identifiers, used by Alembic.
revision = '32766ce2c5b6'
down_revision = '848c2db6d1f'

from datetime import timedelta

import sqlalchemy as sa
from alembic import op
from strappon.models import DriveRequest
from weblib.db import create_session
from weblib.db import expunged


def offered_pickup_time(created, response_time):
    if response_time == 0:
        return None
    return created + timedelta(minutes=response_time)


def upgrade():
    orm = create_session()
    for d in DriveRequest.query:
        d = expunged(d, DriveRequest.session)
        d.offered_pickup_time = (d.offered_pickup_time
                                 if d.offered_pickup_time is not None
                                 else offered_pickup_time(d.created, d.response_time))
        orm.add(d)
    orm.commit()


def downgrade():
    pass
