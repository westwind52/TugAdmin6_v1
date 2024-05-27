from __future__ import annotations

from Folder.models import Flight
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request
from Folder import global_vars, db, app
from Folder.models import Aircraft, Ops_days, Flight, TowPairs, FltShort
from Folder.myroutes import my_utils as util
from Folder.myroutes import flight_support as fs
import Folder.myroutes.audit as audit
from Folder.myroutes import operations as ops
from Folder.myroutes import tows as t

def update_sheet_id(_id: int, new_sheet: int) -> None:
    """
    UPDATE the db for one Flight record using supplied "id".

    Args:
        _id: int database Id of existing sheet
        new_sheet: int sheet id to be changed to
    """
    my_data = Flight.query.get(_id)
    my_data.sheet_number = new_sheet
    db.session.commit()

    return


def add_launch_link_to_db(launch_id: int, flt_id: int) -> None:
    """
    add the cross link to the launch db record to the individual flight.

    UPDATE the Launches link for one Flight record
    Args:
        launch_id:  int - Launches db identifier
        flt_id:  target flight record id

    Returns:
        None
    """
    if my_data := Flight.query.get(flt_id):
        my_data.launch_id = launch_id
        db.session.commit()
    else:
        flash(f' FLight db error - record {launch_id}not found')

    return


def add_tow_pair_data_to_db(daily_tows: list[TowPairs]) -> None:
    """
    Uses an input list of tug-glider pairs to update the primary Flights database
        table with record references.
    Returns:
        None:
        """

    for one_tow in daily_tows:
        my_tow = Flight.query.filter_by(id=one_tow.tug_id).first()
        my_tow.pair_id = one_tow.glider_id
        db.session.commit()
        my_glider = Flight.query.filter_by(id=one_tow.glider_id).first()
        my_glider.pair_id = one_tow.tug_id
        db.session.commit()
    return


def load_flight_from_db(_all_data: list[Flight], sheet_id: int) -> list[tuple]:
    """ load the flight data records into the dataframe from the supplied _alldata record set.

    Args:
        _all_data: list of lights to be preocesed
        sheet_id: target sheet id

    Returns:
        list[tuple]: data_frame


    """
    data_frame: list[tuple] = []

    for flight in _all_data:
        # process the flight data into a flight "rec'  -record
        rec = fs.process_flight(flight)
        rec['sheet_number'] = sheet_id
        # make the flight record as a tuple for transition to web page
        my_rec = util.make_flt_rec(rec)
        data_frame.append(my_rec)

    return data_frame


def update_glider_ids_in_db(_all_data) -> None:
    """
    Use pilot information pre-stored in Global variable 'acft'.
    UPDATE the pilot and heavy class field in the Flights table if None

    Args:
        _all_data:

    Returns:
        None
  """
    idents = [flight.id for flight in _all_data]

    for this_id in idents:

        my_data = Flight.query.get(this_id)
        # check Null return
        if my_data is not None:
            this_rego = my_data.aircraft
            if this_rego not in global_vars.tugs:  # should be a glider
                if (
                        this_rego in global_vars.acft.keys()
                        and my_data.pilot_name is None
                ):  # update the pilot field if possible
                    my_data.pilot_name = global_vars.acft[this_rego][0]
                    db.session.commit()

                if (
                        my_data.heavy is None  # update the heavy characteristic if known
                        and this_rego in global_vars.acft.keys()
                ):
                    my_data.heavy = global_vars.acft[this_rego][1]
                    db.session.commit()

    return


def update_flight_time_in_db(this_id: int, flt_var: str, flt_val: int) -> None:
    """
    UPDATE the db for one Flight record.

    Currently set to update the flt_time in flight
    Args:
        this_id: int - flight record id
        flt_var:
        flt_val: Any - might be time in minutes or None

    Returns:
        object:

    """
    my_data = Flight.query.get(this_id)
    # print(my_data)
    my_data.flt_time = flt_val
    db.session.commit()

    return


def update_sheet_id_for_month(target_date: str) -> int | None:
    still_missing_list: list[int] = []
    missing_list = audit.check_sheet_id_present_for_month(target_date)

    target_sheet_id: int | None = None

    for flt in missing_list:
        if flt is not None:
            this_flt: [Flight] = Flight.query.get(flt)
            ops_date = this_flt.to_date_str
            target_sheet_id: int | None = ops.get_sheet_id_for_date(ops_date)
            if target_sheet_id:
                this_flt.sheet_number = target_sheet_id
                db.session.commit()
            else:
                flash(f' Sheet number missing {this_flt.id}')

        print(f'Target date and id {target_date} {target_sheet_id}')
    return len(still_missing_list)
