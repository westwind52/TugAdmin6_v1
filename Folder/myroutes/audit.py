from icecream import ic  # type: ignore
from sqlalchemy import and_
# from dataclasses import dataclass
from datetime import datetime
from flask import render_template, request, flash, redirect, url_for  # type: ignore[import]
from Folder import db, app, global_vars
from Folder.models import Flight, Launches, Pilots, TowPairs, Frame
import Folder.myroutes.my_utils as utils
import Folder.myroutes.flight_db_support as fdb


@app.route('/main_audit', methods=['GET', 'POST'])
def main_audit() -> render_template:
    """
    Main editing and management page for
    """
    print('Main Audit')
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        sheet_id = request.form['sheet_id']
        print(f'found post {start_date} {end_date} {sheet_id}')

        all_data = Flight.query.filter(Flight.to_date_str == start_date).order_by(Flight.flt_id).all()

        print(all_data)

    check_sheet_id_present_for_month(global_vars.ops_date_str)
    fdb.update_sheet_id_for_month(global_vars.ops_date_str)

    return render_template('audit.html', start_date="2021-02-04")


@app.route('/audit_period')
def audit_period() -> render_template:
    print('Audit period')
    return redirect(url_for('index'))


def check_launch_coverage_month(_target_date: str) -> list[str]:
    missing_days: list[str] = []
    target_date_dt, target_end_dt, month_name, year_str = utils.make_datetime_one_calander_month(_target_date)
    launch_frame: list[Launches] = Launches.query.filter(and_
                                                         (Launches.tow_date_dt >= target_date_dt,
                                                          Launches.tow_date_dt <= target_end_dt)) \
        .order_by(Launches.tow_date_dt).all()
    flight_frame = Flight.query.filter(and_
                                       (Flight.to_time_dt >= target_date_dt, Flight.to_time_dt <= target_end_dt)) \
        .order_by(Flight.to_time_dt).all()

    list_of_launches: set = {launch.sequence_num for launch in launch_frame}
    for flight in flight_frame:
        if flight.flt_id not in list_of_launches:
            missing_launch = f'Found {flight.to_date_str} {flight.to_time_dt}'
            print(missing_launch)
            missing_days.append(missing_launch)

    return missing_days


def check_sheet_id_present_for_month(_target_date: str) -> list[int]:
    """
    Check database records for period to see if sheet_id i set

    Returns:
        missing flight id's -- > list of int
    """
    target_date_dt, target_end_dt, month_name, year_str = utils.make_datetime_one_calander_month(_target_date)

    flight_frame = Flight.query.filter(and_(Flight.to_time_dt >= target_date_dt, Flight.to_time_dt <= target_end_dt)).order_by(Flight.to_time_dt).all()

    return [flight.id for flight in flight_frame if flight.sheet_number == 999]


def audit_completness(my_data) -> tuple[bool, list[str], list[str], list[int], list[int]]:
    """
    Audit the database returned set for aircraft type data to find:
        unknown height
        unknown pilot
        CLUB flight status

    Args:
         my_data:

    Returns:
         result: Bool  - True if no anomalies ,
                        lists for unknown pilots, unallocated heights and unverified flight classification
    """

    unknown_glider: list[str] = []
    unknown_pilots: list[str] = []
    no_height: list[int] = []
    unverified: list[int] = []

    for flight in my_data:
        if flight.aircraft not in global_vars.acft and flight.aircraft not in global_vars.tugs:
            unknown_glider = flight.aircraft

        if flight.flt_class in ['GLIDER', 'CLUB'] and flight.pilot_name not in global_vars.pilot_initials:
            unknown_pilots.append(flight.id)

        if flight.flt_class == 'TUG' and not flight.launch_ht:
            no_height.append(flight.id)

        if (
                flight.flt_class == 'CLUB'
                and flight.pilot_name not in global_vars.bulk_bill
                and flight.status != 'VERIFIED'
        ):
            unverified.append(flight.id)

    result = not unknown_pilots and not no_height and len(unknown_glider) == 0 and not unverified

    return result, unknown_glider, unknown_pilots, no_height, unverified


def audit_heights(_data_frame) -> list[int]:
    """
    audit the heights column to see all launch heights set

    Args:
        _data_frame:

    Returns:
        list[int]: record ids with no height set 0 list[int]
    """

    return [rec.id for rec in _data_frame if rec.launch_ht is None]


def report_audit(_data_frame) -> bool:
    """
    Report audit data.
    Args:
        _data_frame:

    Returns:
        bool Clean_Audit for clean audit

    """
    clean_audit, unknown_gliders, no_pilots, no_heights, unverified = audit_completness(_data_frame)

    if not clean_audit:
        if len(no_pilots) != 0:  # Still unknown pilots
            flash(f' Unknown - pilots not in initials database {no_pilots}  (audit)')

        if len(no_heights) != 0:  # Still unallocated launch height
            flash(f' Unknown heights {no_heights}   (audit)')

    if len(unknown_gliders) != 0:
        outstr = str(unknown_gliders)
        flash(f' Unknown - Gliders not in database {outstr}  (audit)')

    if len(unverified) != 0:
        outstr = str(unverified)
        flash(f' Unverified {outstr}  (audit)')

    return clean_audit
