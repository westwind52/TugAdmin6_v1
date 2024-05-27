from icecream import ic  # type: ignore
from typing import Union, Optional
from Folder import global_vars
from dataclasses import dataclass
from datetime import datetime
from Folder import db
import Folder.global_vars
from Folder.models import Flight, Launches, Pilots, TowPairs, Frame
import Folder.myroutes.my_utils as utils
import Folder.myroutes.tows_support as ts

global data_frame

def create_tow_frame():
    return tow_frame


def build_tow_pairs(today_tows: list[TowPairs]) -> list[Frame]:
    """
    Returns:
         [list[Frame]  Data frame for the built tow pairs in Frame dataclass

    """

    launch_frame: list[Frame] = []

    for tow_set in today_tows:
        this_tow = load_one_launch_frame_supervisor(tow_set)
        if this_tow is not None:
            launch_frame.append(this_tow)

    return launch_frame


def load_one_launch_frame_supervisor(tow_pair: TowPairs) -> Optional[Frame]:
    """
    Return one frame with relevant data for one tow using the tow/glider
    ident key pairs found in prior step.

    Args:
        tow_pair: a tuple with tow day sequence number, tug identity key , glider identity key

    Returns:
        object: a 'frame'  as one row of data with the tug / glider ids
    """

    t: Flight = Flight.query.get(tow_pair.tug_id)
    g: Flight = Flight.query.get(tow_pair.glider_id)

    # this_tow_pair_ids_date_str = t.to_date_str

    if g is not None:
        sequence: int = t.flt_id

        return build_one_launch_frame(g, t, sequence, tow_pair)
    return None


def build_one_launch_frame(g: Flight, t: Flight, sequence: int, tow_pair_ids: TowPairs) -> Frame:
    """
    Function created by Sourcery.
    Extracted main method from the build one launch frame function.
    Does the actual work of assembling the composite record from the tug and glider data frames

    """
    if g.aircraft in Folder.global_vars.club:  # check if its a club glider
        g.quantity = g.flt_time  # if so set the number of minutes
        db.session.commit()

    to_time_str = t.to_time_dt.time().isoformat(timespec='minutes')

    if t.ld_time_dt:
        tug_land_time_str = t.ld_time_dt.time().isoformat(timespec='minutes')
    else:
        tug_land_time_str = ''
    if g.ld_time_dt:
        glider_land_time_str = g.ld_time_dt.time().isoformat(timespec='minutes')
    else:
        glider_land_time_str = ''

    tow_cost, _glider_cost = flight_cost(t, g)
    update_costs(t.id, tow_cost)
    update_costs(g.id, _glider_cost)
    update_tow_payee(t.id, g.pilot_name)
    pilot_full_name = get_full_name(g.pilot_name)

    if t.status != "VERIFIED" or g.status != 'VERIFIED':
        my_status = "EDIT"
    else:
        my_status = 'VERIFIED'
    written = datetime.now()

    return Frame(sequence_num=sequence,
                 sheet_number=t.sheet_number,
                 tow=tow_pair_ids.tow_daily_sequence,
                 tow_date_dt=t.to_time_dt,
                 payer=pilot_full_name,
                 pilot2='',
                 tug_rego=t.aircraft,
                 glider_rego=g.aircraft,
                 tug_to_str=to_time_str,
                 tug_ld_str=tug_land_time_str,
                 gld_ld_str=glider_land_time_str,
                 billed_ht=t.launch_ht,
                 t_flt_time=t.flt_time,
                 g_flt_time=g.flt_time,
                 heavy=True,
                 tow_cost=tow_cost,
                 glider_cost=_glider_cost,
                 status=my_status,
                 written=written,
                 billed_date=None,
                 tug_flt_id=t.id,
                 gld_flt_id=g.id)


def store_launches(_data_frame: list[Frame], sheet_number: int) -> object:
    """
    Write a page (sheet) of 'Launches' rows   to DB.
    Args:
        sheet_number: the sheet number
        _data_frame: a page of launches in Launches format
    """

    for row in _data_frame:

        full_name: str = get_full_name(row.payer) if len(row.payer) == 2 else row.payer

        launch = Launches(
            row.sequence_num,
            sheet_number,
            row.tow_date_dt,
            row.tow,
            full_name,
            row.tug_rego,
            row.glider_rego,
            row.tug_to_str,
            row.tug_ld_str,
            row.gld_ld_str,
            row.billed_ht,
            row.t_flt_time,
            row.g_flt_time,
            row.heavy,
            row.tow_cost,
            row.glider_cost,
            row.status,
            row.written,
            row.billed_date,
            row.tug_flt_id,
            row.gld_flt_id)

        launch_check = Launches.query.filter_by(tow_date_dt=launch.tow_date_dt, tow=launch.tow).first()

        if launch_check is None:
            db.session.add(launch)
            db.session.commit()
        elif global_vars.overwrite:
            db.session.delete(launch_check)
            db.session.add(launch)
            db.session.commit()

            this_rec = Launches.query.filter_by(sequence_num=launch.sequence_num).first()
            ts.add_launch_link_to_db(this_rec.id, launch.tug_flt_id)
            ts.add_launch_link_to_db(this_rec.id, launch.gld_flt_id)
            db.session.commit()

    return


def set_overwrite(_setflag: str) -> bool:
    """
    set the Overwrite flag (held in Global_vars) to
    control the ovewrite behaviour of the Flighsheet loader.
    @return

    Args:
        _setflag:

    Returns:
        bool: Logical flag on success T/F
    """

    if _setflag == 'checkon':
        global_vars.overwrite = True
        return True
    else:
        global_vars.overwrite = False
        return False


def flight_cost(tug: Flight, glider: Flight) -> tuple[float, float]:
    """
    Calculate flight cost for tow and glider if club aircraft

    Args:
        tug: class instance of Flight
        glider: class instance of Flight

    Returns:
        tuple[float, float]: cost pair for tug and glider
    """

    tug_fee: float = tug_cost(tug.launch_ht, glider.heavy)

    glider_fee: float = glider_cost(glider.aircraft, glider.flt_time, glider.pilot_name, )

    return tug_fee, glider_fee


def tug_cost(_height: int, _heavy: bool) -> float:
    """ calculate the fee for one tow

    Args:
        _height: billable height
        _heavy: glider class for tow fee

    Returns:
        object: cost for tow
    """

    tow_base_rate = Folder.global_vars.tow_base_rate
    height_fee_heavy = Folder.global_vars.height_fee_heavy_per100
    if _height == 0 or _height is None:
        return 0.0
    elif _heavy:
        test = tow_base_rate + (_height / 100) * height_fee_heavy
        print(test)
        return tow_base_rate + (_height / 100) * height_fee_heavy
    else:
        height_fee_light = Folder.global_vars.height_fee_light_per100

        return tow_base_rate + (_height / 100) * height_fee_light


def glider_cost(_glider: str, _flt_time: int, _pilot_name: str) -> float:
    """
    calculate the fee for one flight.

    Args:
        _glider: glider registration
        _flt_time: glider flight time (minutes)
        _pilot_name: pilot name for billing

    Returns:
        object: glider cost for one flight
    """

    if _glider in Folder.global_vars.club.keys():

        if _flt_time is not None and _pilot_name not in Folder.global_vars.bulk_bill:
            glider_fee = _flt_time * Folder.global_vars.club[_glider]
        else:
            glider_fee = 0.0
    else:
        glider_fee = 0.0
    print(glider_fee)
    return glider_fee


def update_costs(ident: int, cost: float):
    """Update the flight cost in chosen flight

    Args:
        ident: is the database key id
        cost: the cost value to be added

    Returns:
        object: True
    """
    rec = utils.Flight.query.get(ident)
    rec.cost = cost
    db.session.commit()

    return True


def update_tow_payee(ident: int, payee: str) -> bool:
    """
    Update the pilot_name in chosen flight.

    Args:
        ident: is the database key id
        payee: the pilot name for billing

    Returns:
        object:
    """
    rec = utils.Flight.query.get(ident)
    rec.pilot_name = payee
    utils.db.session.commit()

    return True


def update_status(ident: int, token: str) -> bool:
    """
    update the bill status with the assigned token value.

    Args:
        ident: is the database key id
        token: is the text string to be written in 'status' column

    Returns:
        object:

    """
    rec = Flight.query.get(ident)
    rec.status = token
    db.session.commit()

    return True


def get_full_name(pilot_name: str) -> str:
    """
    Lookup full name in database if initials supplied.

    Args:
        pilot_name: - may be initials

    Returns:
        str: full name as str
    """
    full_name = ''
    if pilot_name:  # check not None
        if len(pilot_name) > 2: full_name = pilot_name
        if len(pilot_name) == 2:  # must be initials
            if record := Pilots.query.filter_by(pilot_initials=pilot_name).first():
                full_name = record.pilot_name
                if len(full_name) <= 2:
                    full_name = pilot_name
            else:
                full_name = pilot_name
    return full_name
