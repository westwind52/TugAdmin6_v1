from __future__ import annotations
from flask import flash  # type: ignore[import]
from typing import Any
from datetime import datetime, timedelta
import random
import logging
from Folder import global_vars, db, app
from Folder.myroutes import operations
from Folder.my_forms.forms import Glider_UpdateForm, Glider_Short_InsertForm
from Folder.models import Aircraft, Ops_days, Flight, TowPairs, FltShort, Tow
from Folder.myroutes import my_utils as util
from Folder.myroutes import pilots as p
from Folder.myroutes import flight_db_support as fs_db


def load_flightform(my_tug_data: Flight) -> Glider_Short_InsertForm:
    """
    Helper function for "flight insert" from "tows.py".
    Load the database items into the display dataframe (flightForm)
    Args:
        my_tug_data Flight:
    Returns: flightForm - form class from wtforms
    """

    flightForm: Glider_Short_InsertForm = Glider_Short_InsertForm()  # establish a blank for for data entry

    flightForm.glider_take_off.data = my_tug_data.to_time_dt.time() # set in form

    return flightForm


def process_glider_add_post(my_tug_data: Flight,
                            my_form) -> Flight:
    """
    Helper function to load "flight insert" from "tows.py".

    Load the new glider record using Flights model from SQLAlchemy

    Args:
        my_tug_data: Flight data record for the matching tug flights
        my_form: from webform -  record for the flight to be processed

    Returns:
        Flight: Flights record
    """
    seq_num = get_seq_num(my_tug_data.seq_num)
    to_date = datetime.fromisoformat(my_tug_data.to_date_str)
    to_time = my_form['glider_take_off']
    to_time_dt = datetime.combine(to_date, to_time)
    flt_id = int(util.make_id_dt_dt(to_date, to_time))
    if ld_time := my_form['glider_land']:
        ld_time_dt = datetime.combine(to_date, ld_time)
    else:
        ld_time_dt = None
    flt_time = 0
    _aircraft = my_form['aircraft'].upper()
    pilot_name = p.force_pilot_initials_upper(my_form['pilot_name'])
    pilot2_name = '' if my_form['pilot2_name'] is None else my_form['pilot2_name']
    heavy = True
    # if my_tug_data.sheet_number in [None, '', 999]:
    #     _sheet_number = operations.get_sheet_id_for_date(my_tug_data.to_date_str)
    # else:
    #     _sheet_number = my_tug_data.sheet_number
    _sheet_number = my_tug_data.sheet_number

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
        pilot2_name=pilot2_name,
        heavy=heavy,
        OGN_ht=0,  # OGN_ht,
        launch_ht=0,  # launch_ht,
        status='EDIT',  # status,
        sheet_number=_sheet_number,
        cost=0.0,
        pair_id=my_tug_data.id,
        launch_id=0,
        pilot_id=0,
    )


def get_seq_num(_seq_num: int) -> int:
    """
    Create a flight sequence number for the new glider flight.

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

def process_tow(my_flight: Flight) -> dict[str, Any]:
    """
    Process one flight data set into a data record "rec".

    Args:
        my_flight (Flight):

    Returns:
        rec: dict for data - one tow
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
        flt_time_dt: datetime = my_flight.ld_time_dt - my_flight.to_time_dt
        flt_time_int: int = int(flt_time_dt.total_seconds() / 60)
        rec['flt_time'] = flt_time_int

        # update the database
        fs_db.update_flight_time_in_db(my_flight.id, 'flt_time', flt_time_int)

    else:
        rec['flt_time'] = None

    # use registration to classify aircraft
    this_rego: str  = my_flight.aircraft
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


def get_daily_tow_summary(_all_flights: list[Flight]) -> list[FltShort]:
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


def create_tows(all_flights: list[Flight]) -> list[Tow]:
    """
    Load indiviual tow sequences into a frame

    Returns:
        tow_frame as a list[Tows]
    """
    # sourcery skip: inline-immediately-returned-variable
    tow_set = create_tow_set(all_flights)
    tow_frame = create_tow_frame(tow_set)

    return tow_frame


def create_tow_set(_all_flights: list[Flight]) -> list[TowPairs]:
    """
    find the set of tows for the date and update the my_tows and unknown tows lists.

    Returns:
        my_tows[] and unknown tows[]
    """
    todays_tows: list[TowPairs] = []
    processed_flights: set[int] = set()
    my_data = get_daily_tow_summary(_all_flights)

    tow_count: int = 0

    for flt in my_data:

        tug_flt_id: int | None = None
        glider_flt_id: int | None = None

        # if flt.rego in global_vars.known_aircraft:  # it's a glider event
        if flt.rego not in global_vars.tugs:
            glider_flt_id = flt.id
        else:  # its a tug event
            tug_flt_id = flt.id

        if tug_flt_id:  # its a tug event
            glider_flt_id = check_match(my_data, tug_flt_id, flt.to_time)

        elif glider_flt_id not in processed_flights:
            glider_flt_id = flt.id

        if tug_flt_id and glider_flt_id or tug_flt_id:
            this_tow = TowPairs(tow_count, tug_flt_id, glider_flt_id, )  # make the tow pair dataset
            todays_tows.append(this_tow)
            tow_count += 1
        elif glider_flt_id not in processed_flights:
            this_tow = TowPairs(tow_count, glider_flt_id, glider_flt_id, )  # make the tow pair dataset
            todays_tows.append(this_tow)
            tow_count += 1

        if glider_flt_id is not None:
            processed_flights.add(glider_flt_id)

    return todays_tows


def create_tow_frame(tow_set: list[TowPairs]) -> list[Tow]:
    """
     Load individual tow sequences into a frame
    Args:
        Tow_set as a list of short tow_pair data

    Returns:
       tow_frame - a list of[Tows]
    """
    gld_ld_time_str: str = ''
    tow_frame: list[Tow] = []
    # t: Flight = None
    # g: Flight = None

    for tow in tow_set:
        my_tow = Tow()
        if tow.tug_id == tow.glider_id:
            tow.tug_id = None
        if tow.tug_id:
            t: Flight = Flight.query.get(tow.tug_id)

        if tow.glider_id:
            if not my_tow:
                my_tow = Tow
            g: Flight = Flight.query.get(tow.glider_id)
            if g.ld_time_dt is not None:
                gld_ld_time_str = g.ld_time_dt.strftime("%H:%M")
            else:
                gld_ld_time_str = ''

        if tow.tug_id and tow.glider_id:
            my_tow = Tow(id=tow.tug_id, tug=t.aircraft, OGN_ht=t.OGN_ht, launch_ht=t.launch_ht,
                         to_time_str=t.to_time_dt.strftime("%H:%M"), glider=g.aircraft,
                         pilot1_name=g.pilot_name, pilot2_name=g.pilot2_name, ld_time_str=gld_ld_time_str)
        elif tow.tug_id:
            my_tow = Tow(id=tow.tug_id, tug=t.aircraft, OGN_ht=t.OGN_ht, launch_ht=t.launch_ht,
                         to_time_str=t.to_time_dt.strftime("%H:%M"))
        elif tow.glider_id:
            my_tow = Tow(id=tow.glider_id, tug=g.aircraft, to_time_str=g.to_time_dt.strftime("%H:%M"),
                         glider=g.aircraft, pilot1_name=g.pilot_name, ld_time_str=g.ld_time_dt.strftime("%H:%M"))

        if my_tow:
            tow_frame.append(my_tow)

    return tow_frame


def check_match(daily_flight_data: list[FltShort],
                check_id: int,
                tow_time: datetime) -> int | None:
    """
    Locate matching glider takeoff from Ktrax set. Following
    flight must be within "tow_time" of tug take off
    :param daily_flight_data: list of flights
    :param check_id is id of tow flight to be checked against
    :param tow_time: upper time interval to determine match
    :return: the id key for the matching glider flight
    """

    five_minutes = timedelta(seconds=300)
    return next((flt.id for flt in daily_flight_data if (
            tow_time <= flt.to_time <= tow_time + five_minutes
            and flt.id != check_id
    )), None)


# def add_tow_pair_data_to_db(daily_tows: list[TowPairs]) -> None:
#     """
#     Uses an input list of tug-glider pairs to update the primary Flights database
#         table with record references.
#
#     Args:
#         daily_tows: list of TowPairs
#
#     Returns:
#         None:
#         """
#
#     for one_tow in daily_tows:
#         my_tow = Flight.query.filter_by(id=one_tow.tug_id).first()
#         my_tow.pair_id = one_tow.glider_id
#         db.session.commit()
#         my_glider = Flight.query.filter_by(id=one_tow.glider_id).first()
#         my_glider.pair_id = one_tow.tug_id
#         db.session.commit()
#     return
#
#
# def load_flight_from_db(_all_data: list[Flight]) -> list[tuple]:
#     """ load the flight data records into the dataframe from the supplied _alldata record set.
#
#     Args:
#         _all_data: list of lights to be processed
#
#     Returns:
#         list[tuple]: data_frame
#
#
#     """
#     data_frame: list[tuple] = []
#
#     for flight in _all_data:
#         # process the flight data into a flight "rec"  -record
#         rec = process_tow(flight)
#         # make the flight record as a tuple for transition to web page
#         my_rec = util.make_flt_rec(rec)
#         data_frame.append(my_rec)
#
#     return data_frame


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


def add_launch_link_to_db(launch_id: int,
                          _id: int) -> None:
    """
    add the cross link to the launch db record to the individual flight.

    UPDATE the Launches link in Flight record
    Args:
        launch_id:  int - Launches db identifier
        _id:  target db record primary key 'id' in Flight

    Returns:
        None
    """
    if my_data := Flight.query.get(_id):
        my_data.launch_id = launch_id
        db.session.commit()
    else:
        flash(f' FLight db error - record {_id}not found')

    return

