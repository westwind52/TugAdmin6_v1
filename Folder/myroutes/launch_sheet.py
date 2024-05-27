from __future__ import annotations

from Folder import global_vars
from dataclasses import dataclass
from flask import render_template, request, url_for, redirect, flash  # type: ignore[import]
from sqlalchemy import and_
import Folder.myroutes.my_utils as utils
import Folder.myroutes.operations as ops
from Folder import db, app
from datetime import datetime, timedelta
from Folder.models import Launches, Flight


@app.route('/launches', methods=["GET", 'POST'])
def launches():
    """
    Prepare an Operations Launches ( Launch Sheet) for display or print
    This will write the currently set sheet number
    """
    target_date: str = global_vars.ops_date_str
    chosen_sheet: int = ops.get_sheet_id_for_date(target_date)

    """ set up the Launches on current ops_day as default"""

    launch_frame = Launches.query.filter_by(sheet_id=chosen_sheet).order_by(
        Launches.tow_date_dt).all()  # then it's a full sheet

    check_dates = check_launch_coverage_month(target_date)

    if request.method == 'POST':

        chosen_sheet = int(request.form['sheet_id'])

        summary_flag: str | None = request.form.get('summary')

        if chosen_sheet != 0:
            global_vars.sheet_number = chosen_sheet
            launch_frame = Launches.query.filter_by(sheet_id=chosen_sheet).order_by(
                Launches.tow_date_dt).all()
            my_test = "FULL SHEET"

        if summary_flag == 'sum_on':
            print("Summary Set")
            target_date_dt, target_end_dt, month_name, year_str = utils.make_datetime_one_calander_month(target_date)
            launch_frame: list[Launches] = Launches.query.filter(and_
                                                                 (Launches.tow_date_dt >= target_date_dt,
                                                                  Launches.tow_date_dt <= target_end_dt)) \
                .order_by(Launches.tow_date_dt).all()

            print(f' Launch frame has {len(launch_frame)}')
            #            summary_frame = ls.get_summary_frame(launch_frame)
            #            ls.print_launch_summary_pdf(month_name, year_str, summary_frame)

            return render_template('launch_summary.html',
                                   month_name=month_name,
                                   summary=summary_frame,
                                   ops_date=target_date)
            # --   end the summary processing screen ---

    if len(launch_frame) > 0:
        print(f'Flight Sheet {launch_frame[0].sheet_id}')
    else:
        flash('No data for this date')
    overwrite = global_vars.overwrite

    print_block = ls.create_launches(launch_frame)
    ls.print_launch_sheet_pdf(chosen_sheet, print_block)

    return render_template('launch_sheet.html',
                           flt_data=launch_frame,
                           sheet=str(chosen_sheet),
                           ops_date=target_date,
                           overwrite=overwrite
                           )


def launch_summary_month():
    """
    Prepare an Operations Launches Sheet ( Launch Sheet) for display or print for the currently active target date
    This will write the currently set sheet number  unless sheet Id field is set
    """
    # chosen_sheet: int = 0
    _target_date: str = global_vars.ops_date_str
    month = utils.make_month(target_date)
    print(f' month: {month}')

    """ set up the Launches on current ops_day as default"""
    target_startdate_dt, target_enddate_dt = utils.make_datetime_start_end_for_day_range(_target_date, 1)
    launch_frame: list[Launches] = Launches.query.filter(and_
                                                         (Launches.tow_date_dt >= target_startdate_dt,
                                                          Launches.tow_date_dt <= target_enddate_dt)).all()

    if request.method == 'POST':
        """look at the chosen sheet field"""
        _target_date = request.form['ops_date']
        if _target_date != '':  # make sure date is set
            target_startdate_dt, target_enddate_dt = utils.make_datetime_start_end_for_day_range(_target_date, 1)

        month = utils.make_month(global_vars.ops_date_str)
        print(f' month: {target_date} {month}')

        if target_date != '':  # else single day
            launch_frame: list[Launches] = Launches.query.filter(and_
                                                                 (Launches.tow_date_dt >= target_startdate_dt,
                                                                  Launches.tow_date_dt <= target_enddate_dt)).all()
            my_test = "ONE DAY"

    overwrite = global_vars.overwrite

    # print_block = create_launches(launch_frame)
    # print_pdf(print_block)

    return render_template('launch_summary_month.html',
                           flt_data=summary_frame,
                           target_month=target_month,
                           overwrite=overwrite
                           )


# def get_launches_by_day(_target_date: str):
#     target_date_dt = datetime.strptime(_target_date, "%Y-%m-%d")
#     end_date = target_date_dt + timedelta(days=1)
#     return Launches.query.filter_by(tow_date_dt >= target_date_dt,
#                                     tow_date_dt < end_date).all()


@app.route('/delete_launch_sheet')
def delete_launch_sheet():
    """
    Delete all entrys for one Launches ( launchsheet)
    """

    my_sheet = global_vars.sheet_number
    if my_sheet is not None:
        num_records = Launches.query.filter_by(sheet_id=my_sheet).delete()

        db.session.commit()
        flash(f'{num_records} records deleted')

    return redirect(url_for('launches'))


@app.route('/launch_verify/<int:_id>', methods=['GET'])
def launch_verify(_id: int):
    """ Change the "status" record to VERIFIED"""

    my_data: Launches = Launches.query.filter_by(id=_id).first()
    my_data.status = 'VERIFIED'
    db.session.commit()
    flash('Launch verified')

    return redirect(url_for('flight_edit'))


@app.route('/launch_unverify/<int:_id>', methods=['GET'])
def launch_unverify(_id: int):
    """ Change the "status" record to EDIT"""

    my_data = Launches.query.filter_by(id=_id).first()
    my_data.status = 'EDIT'
    db.session.commit()
    flash('Launch removed from verification')

    return redirect(url_for('flight_edit'))
