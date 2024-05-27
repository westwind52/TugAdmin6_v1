from datetime import datetime
import logging
from sqlalchemy import and_
from typing import Optional
from flask import render_template, request, flash, redirect, url_for  # type: ignore[import]
from Folder import db, global_vars, app
from Folder.models import Flight, Ktrax, Ops_days
import Folder.myroutes.my_utils as utils
import Folder.myroutes.launch_sheet as sh

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)  # type: ignore[call-arg]


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Main page.
    :return: Active start
    """

    if request.method == 'POST':

        _ops_date = request.form['ops_date']  # returns a str
        if _ops_date != '':
            global_vars.ops_date_str = _ops_date
            global_vars.ops_date_dt = datetime.strptime(_ops_date, "%Y-%m-%d")


        elif global_vars.STARTING:  # first run through so no date yet - suppress message
            global_vars.STARTING = False
        else:
            flash(' Must enter a start date')
            return redirect(url_for('index'))


        result = Flight.query.filter_by(to_date_str=_ops_date).all()
        total, this_month, this_year = count_flights_per_month(global_vars.ops_date_str)

        if not result:
            flash(" No Flight data for this date - Try again", category="Warning")
        else:
            #tow = request.form.get('set_tows')
            tow=True
            if tow:
  #              return redirect(url_for('all_tows_load'))
                return redirect(url_for('flight_edit'))

        if request.form.get('ktrax'):
            print('Checkbox')
            import_Ktraxdb()


        return render_template('index.html', ops_date=global_vars.ops_date_str)

    if global_vars.ops_date_str == '' or global_vars.ops_date_str is None:
        flash("Must set and Ops Date", "Warning")
        global_vars.ops_date_dt = datetime.now()
        global_vars.ops_date_str = global_vars.ops_date_dt.strftime("%Y-%m-%d")

    total, this_month, this_year = count_flights_per_month(global_vars.ops_date_str)
    return render_template('index.html',
                           ops_date=global_vars.ops_date_str,
                           tows=total,
                           this_month=this_month,
                           this_year=this_year)


# ============== Support functions =============


def call_audit():
    main_audit()
    return

def import_Ktraxdb():
    """
    Import Ktrax data from a stored Ktrax database table
    and store in Flights database table.

    :return: Data transferred to a Flights database
    """
    all_ktrax = Ktrax.query.all()

    for row in all_ktrax:
        my_rego = rego3(row.glider_rego)
        duplicate_flight = check_duplicate_flights(row.seq_num)
        new_row = (row.to_time, row.ld_time, my_rego, '', '', '', row.height, '')
        print("new row", new_row)
        to_date_str = datetime.strftime(row.to_time, '%Y-%m-%d')
        if my_rego == 'PXI':
            flt_class = 'TUG'
        elif my_rego == 'UIU':
            flt_class = 'CLUB'
        else:
            flt_class = "VISITOR"

        if not duplicate_flight:

            status = "EDIT"
            my_data = {
                'seq_num': row.seq_num,
                'flt_id': row.flt_id,
                'flt_class': flt_class,
                'to_date_str': to_date_str,
                'to_time_dt': row.to_time,
                'ld_time_dt': row.ld_time,
                'flt_time': 0,
                'aircraft': my_rego,
                'pilot_name': None,
                'heavy': None,
                'OGN_ht': row.height,
                'launch_ht': 0,
                'status': status,
                'sheet_number': 999,
                'cost': 0.0,
                'pair_id': None,
                'launch_id': None,
                'pilot_id': None
            }
            myFlight = Flight(**my_data)

            db.session.add(myFlight)
            db.session.commit()
            print(f"Flight added {row.to_time}")
        else:
            print(f"Flight already present {row.to_time}")

    return True


def audit_sheet_id():
    print('Audit sheet')
    ops_dates = set()
    no_sheet_dates = set()
    all_dates = Flight.query.all()
    for item in all_dates:
        if item.sheet_number == 999:
            result = Ops_days.query.filter(Ops_days.flying_day == item.to_date_str).first()
            if result is not None:
                ops_dates.add(item.to_date_str)
                print(f' Flight present entry{item.to_date_str} Sheet {item.sheet_number}  {result.sheet_id}')

                utils.update_sheet_id(item.id, result.sheet_id)
            else:
                no_sheet_dates.add(item.to_date_str)
                print(f' Flight not present {item.to_date_str} Sheet {item.sheet_number}')

    # result = utils.update_sheet_id(global_vars.ops_date)
    return


# ============== Utility functions =============

def check_duplicate_flights(check_data: int) -> bool:
    """
    Check for pre existing record in the Flights table to prevent inserting a duplicate record.

    :param check_data:
    :return:

    Args:
        check_data: this is the "seq_num" data element to be checked

    Returns:
        Bool: true / False to indicate duplicate
    """
    my_count = Flight.query.filter_by(seq_num=check_data).count()
    result = my_count > 0
    print("Check duplicate", result)

    return result


def rego3(instr: str) -> Optional[str]:
    """
    Return a three letter registration set from possible VH- style.

    Args:
        instr: Input call sign - may be in VH- format

    Returns:
        object: Three character registration string
    """
    if len(instr) > 3:
        return instr[-3:]
    elif instr is None:
        return None
    else:
        return instr[:3]


def write_sheet_number_for_date(dataset, _sheet):
    print('in write sheet')

    for rec in dataset:
        print(f' sheet added to rec: {rec.id}')
        rec.sheet_number = _sheet
        db.session.commit()

    return

def count_flights_per_month(_ops_date:str)-> tuple[int, str, str]:
    """

    :type _ops_date: str
    """
    start, end , this_month, this_year = utils.make_datetime_one_calander_month(_ops_date)
    print(start, end)
    flight_frame: list[Flight] = Flight.query.filter(and_
                                                         (Flight.to_time_dt >= start,
                                                          Flight.to_time_dt <= end)).all()
    total = len(flight_frame)
    print(total, this_month, this_year)
    return total, this_month, this_year