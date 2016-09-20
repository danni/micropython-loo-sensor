"""
Flask server for converting OpsGenie hooks into WebSockets for an Internet of
Things device.
"""

from __future__ import unicode_literals, absolute_import, print_function

import enum
import functools
from datetime import datetime

from flask import Flask, _request_ctx_stack
from ac_flask.hipchat import Addon, addon_client, events, tenant
from ac_flask.hipchat.glance import Glance
from ac_flask.hipchat.auth import require_tenant

# pylint:disable=invalid-name
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

addon = Addon(app=app,
              key='loo-status',
              name="Loo Status",
              description="Displays the occupation of the loo",
              vendor_name="Squareweave",
              allow_room=True,
              allow_global=True,
              scopes=['send_notification', 'view_room'])
# pylint:enable=invalid-name


@enum.unique
class Status(enum.Enum):
    """Possible statuses for the loo."""
    UNKNOWN = None
    OCCUPIED = True
    VACANT = False


class StatusStore(object):
    status = Status.UNKNOWN
    timestamp = datetime.now()


# Global to store the status in
STATUS = StatusStore()


def get_glance():
    """
    Returns the data for the glance.
    """

    status_map = {
        Status.UNKNOWN: 'default',
        Status.VACANT: 'success',
        Status.OCCUPIED: 'error',
    }

    return Glance()\
        .with_label("Loo")\
        .with_lozenge(STATUS.status.name, status_map[STATUS.status])\
        .data


@app.route('/update/<status>')
def notify(status):
    """
    HTTP request called by the sensor.
    """
    try:
        status = getattr(Status, status.upper())
    except AttributeError:
        status = Status.UNKNOWN
        # FIXME: raise a 400

    STATUS.status = status
    STATUS.timestamp = datetime.now()

    events.fire_event('loo', STATUS)

    if status is Status.UNKNOWN:
        return "Unknown status"
    else:
        return "Ok!"


@addon.glance(key='loo', name="Loo", target='', icon='')
def register_glance():
    """Register the glance and return its data."""

    print("Tenant", tenant)

    def update_glance(tenant, data):
        print("Updating glance", tenant)
        try:
            ctx = _request_ctx_stack.top
            ctx.push()

            ctx.tenant = tenant

            addon_client.update_room_glance('loo',
                                            get_glance(),
                                            tenant.room_id)

        finally:
            ctx.pop()

    events.register_event("loo", functools.partial(update_glance,
                                                   tenant._get_current_object()))

    return get_glance()


if __name__ == '__main__':
    print("Starting server")
    app.run(host='0.0.0.0', debug=True, use_reloader=True)
