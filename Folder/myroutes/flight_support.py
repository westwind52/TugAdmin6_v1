from __future__ import annotations
from flask import flash  # type: ignore[import]
from typing import Any
from datetime import datetime, timedelta
import random
import logging
from Folder import global_vars, db, app
from Folder.myroutes import operations
from Folder.my_forms.forms import Glider_UpdateForm, GliderFlight_AddForm
from Folder.models import Aircraft, Ops_days, Flight, TowPairs, FltShort
from Folder.myroutes import my_utils as util
from Folder.myroutes import flight_audit_log as sl
from Folder.myroutes import pilots as p
import Folder.myroutes.flight_db_support as fs_db

logging.basicConfig(encoding='utf-8', level=sl.logging.DEBUG)  # type: ignore[call-arg]


def load_flightform(my_tug_data: Flight) -> Flight:
    """
    Helper function for "flight insert" from "flights.py".
    Load the database items into the display dataframe (flightForm)
    Args:
        my_tug_data as Flight


    Returns:
        Flight: Flights record
    """
    seq_num = get_seq_num(my_tug_data.seq_num)
    to_date_str = global_vars.ops_date_str
    # to_time_str = my_form['to_time_str']
    # to_time_dt = util.combine_to_dt(to_date_str, to_time_str)
    to_time_dt: time = my_tug_data['glider_take_off']
    flt_id = int(util.make_id_str_dt(to_date_str, to_time_dt))
    if my_form['ld_time_str'] and my_form['ld_time_str'] != '00:00':
        ld_time_dt = get_ld_time_dt(to_date_str, my_form['ld_time_str'])
    else:
        ld_time_dt = None
    flt_time = 0
    _aircraft = my_form['aircraft'].upper()
    pilot_name = p.force_pilot_initials_upper(my_form['pilot_name'])
    return_value = my_form['heavy']
    heavy = return_value == "Y"
    if my_tug_data.sheet_number in [None, '', 999]:
        _sheet_number = operations.get_sheet_id_for_date(to_date_str)
    else:
        _sheet_number = my_tug_data.sheet_number
    cost = 0.0

    return Flight(
        seq_num=seq_num,
        flt_id=flt_id,
        flt_class='GLIDER',
        to_date_str=to_date_str,
        to_time_dt=to_time_dt,
        ld_time_dt=ld_time_dt,
        flt_time=flt_time,
        aircraft=_aircraft,
        pilot_name=pilot_name,
        pilot2_name=None,
        heavy=heavy,
        OGN_ht=0,  # OGN_ht,
        launch_ht=0,  # launch_ht,
        status='EDIT',  # status,
        sheet_number=my_tug_data.sheet_number,
        cost=cost,
        pair_id=my_tug_data.id,
        launch_id=0,
        pilot_id=0,
    )


def process_flight(my_flight: Flight) -> dict[str, Any]:
    """
    Process one flight data set into a data record "rec".

    Args:
        my_flight (Flight):

    Returns:
        rec: dict for data - one flight
    """
    if my_flight.launch_ht == '':
        my_flight.launch_ht = 0

    # get one flight record
    rec: dict = util.make_flight_dict_record(my_flight)

    # set time into string variable for web display
    if my_flight.to_time_dt is not None:
        rec['to_time_str'] = my_flight.to_time_dt.time().isoformat(timespec='minutes')
    else:
        rec['to_time_str'] = None

    # set date into string variable for web display
    if my_flight.ld_time_dt is not None and my_flight.ld_time_dt != '':
        rec['ld_time_str'] = my_flight.ld_time_dt.time().isoformat(timespec='minutes')
    else:
        rec['ld_time_str'] = None

    # see if there is a valid flight time
    if my_flight.to_time_dt is not None and my_flight.ld_time_dt is not None:
        flt_time_dt = my_flight.ld_time_dt - my_flight.to_time_dt
        flt_time_int = int(flt_time_dt.total_seconds() / 60)
        rec['flt_time'] = flt_time_int

        # update the database
        fs_db.update_flight_time_in_db(my_flight.id, 'flt_time', flt_time_int)

    else:
        rec['flt_time'] = None

    # use registration to classify aircraft
    this_rego = my_flight.aircraft
    if this_rego in global_vars.tugs:
        rec['flt_class'] = 'TUG'
        rec['pilot_initials'] = ''
        rec['heavy'] = ''

    elif this_rego in global_vars.club:
        rec['flt_class'] = 'CLUB'
        rec['launch_ht'] = None
    else:
        rec['flt_class'] = 'GLIDER'
        rec['launch_ht'] = None

    return rec


def get_daily_launches(_all_flights: list[Flight]) -> list[FltShort]:
    """
    Load a subset of flight data into a list FltShort for easy use.
    Args:
        _all_flights:

    Returns:
        my_data as a list[FltShort]
    """
    my_data: list[FltShort] = []
    for row in _all_flights:
        short_data_row = FltShort(row.id, row.to_time_dt,
                                  row.aircraft, row.flt_class)
        my_data.append(short_data_row)

    return my_data


def find_tow_matchs(_all_flights: list[Flight]) -> [list[TowPairs], list[int]]:
    """
    find the set of tows for the date and update the my_tows and unknown tows lists.

    Args:
        _all_flights:

    Returns:
        my_tows[] and unknown tows[]
    """

    todays_tows: list[TowPairs] = []
    tows_but_no_glider: list[int] = []
    gliders_but_no_tow: list[str] = []
    glider_match = False

    my_data = get_daily_launches(_all_flights)

    tow_count: int = 1

    for flt in my_data:
        if glider_match:
            glider_match = False  # Skip over this record because already processed as match
        elif flt.rego in global_vars.tugs:  # its a tug event
            tow_id: int = flt.id  # tug flight id for pair
            if glider_id := check_match(my_data, tow_id, flt.to_time):
                this_tow = TowPairs(tow_count, tow_id, glider_id, )  # make the tow pair dataset
                todays_tows.append(this_tow)
                tow_count += 1
                glider_match = True
            else:
                tows_but_no_glider.append(tow_id)
        elif flt.rego in global_vars.known_aircraft:
            gliders_but_no_tow.append(flt.rego)

    if gliders_but_no_tow:
        flash(f' Solo glider with mo matching tow {gliders_but_no_tow}')
    return todays_tows, tows_but_no_glider, gliders_but_no_tow


def check_match(daily_flight_data: list[FltShort], check_id: int,
                tow_time: datetime) -> Optional[int]:
    """
    Locate matching glider takeoff from Ktrax set. Following
    flight must be within "tow_time" of tug take off
    :param daily_flight_data: list of flights
    :param check_id is id of tow flight to be checked against
    :param tow_time: upper time interval to determine match
    :return: the id key for the matching glider flight
    """

    five_minutes: timedelta = timedelta(seconds=300)
    return next((flt.id for flt in daily_flight_data if (
            tow_time <= flt.to_time <= tow_time + five_minutes
            and flt.id != check_id
    )), None)


def get_seq_num(_seq_num: int) -> int:
    """
    Create a flight sequence number for the new glider flight'.

    usually one more than related tug flight
    Args:
        _seq_num (int):
    Returns:
        int: sequence number
    """
    if _seq_num is None:
        return random.randint(120000000000, 900000000000)

    check_next_num = _seq_num + 1
    return ensure_seq_num_unique(check_next_num)


def ensure_seq_num_unique(_num: int) -> int:
    """
    Check the Flights database to ensure no duplication of "sequence numbers".
    Start with the knownTug sequence number and begin to increment by 1
    Return: the guaranteed unique sequence number

    Args:
        _num: int - the target inital sequence number

    Returns:
        int: _ the finally selected number ( new or old)
    """

    my_tug_data = Flight.query.filter_by(seq_num=_num).first()
    while my_tug_data is not None:
        _num += 1
        my_tug_data = Flight.query.filter_by(seq_num=_num).first()
    return _num


# def check_and_update_pilot_name(_name: str) -> tuple[int | None, str | None]:
#     """
#     Helper function for pilot initials and name.
#
#     Args:
#         _name: Target name for lookup
#
#     Returns:
#         object: tuple of pilot id and pilot name OR None
#
#     """
#
#     pilot_id: int | None = None
#     pilot_name: str | None = None
#
#     if len(_name) == 2:
#         this_initials = _name.upper()
#         pilot_name = this_initials  # set the name
#         record = p.get_pilot_object_from_initials(this_initials)  # Find the id
#         pilot_id = record.id if record is not None else None
#     elif len(_name) > 2:
#         record = p.get_pilot_object_from_namestring(_name.strip().title())
#         pilot_id = record.id if record is not None else None
#         pilot_name = _name
#
#     return pilot_id, pilot_name
