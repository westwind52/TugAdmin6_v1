from flask import Flask  # type: ignore
from Folder import models, global_vars
from Folder import global_vars
from Folder.models import Aircraft, Pilots, Ops_days
from flask_sqlalchemy import SQLAlchemy  # type: ignore[import]
from flask_bootstrap import Bootstrap5  # type: ignore[import]
from Folder.models import db
from Folder.config import Config
from Folder.myroutes.my_utils import initialise_last_invoice


def create_app(_name):
    app = Flask(_name)
    app.config.from_object(Config)
    db.init_app(app)
    with app.app_context():
        db.create_all()

    return app


app = create_app(__name__)
Bootstrap5(app)


@app.route('/hello')
def hello():
    return '<h2>Hello World</h2>'


@app.before_first_request
def create_table():
    db.create_all()
    return


from Folder.myroutes import tows, index, pilots, aircraft, analyse, audit
from Folder.myroutes import launch_sheet, operations, flight_db_support, flights
from Folder.models import Aircraft, Pilots
from Folder.myroutes.tows_support import TowPairs


@app.before_first_request
def load_audit_tables():
    acft = Aircraft.query.all()
    for ac in acft:
        global_vars.known_aircraft.add(ac.registration)
    print(f" Aircraft: {global_vars.known_aircraft}")

    all_pilots = Pilots.query.all()
    for p in all_pilots:
        global_vars.known_pilots.add(p.pilot_name)
        global_vars.pilot_initials.add(p.pilot_initials)
        global_vars.pilot_dict[p.pilot_initials] = p.pilot_name
    print(f'Loaded pilot initials {len(global_vars.pilot_initials)} and pilot name dict {len(global_vars.pilot_dict)}')
    return


global_vars.STARTING = True  # help suppress date request on first input screen
initialise_last_invoice()
print(f'Last Invoice set to {global_vars.last_invoice["LAST_INVOICE"]}')
