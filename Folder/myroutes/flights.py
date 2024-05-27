from flask import render_template, request, redirect, url_for, flash  # type: ignore
import random
import logging
from icecream import ic  # type: ignore
from datetime import datetime
from Folder import global_vars, db, app
from Folder.my_forms.forms import Glider_UpdateForm, Tug_Form, Tug_UpdateForm
from Folder.myroutes import aircraft
from Folder.myroutes import operations
from Folder.myroutes import audit
from Folder.models import Aircraft, Ops_days, Flight
import Folder.myroutes.my_utils as util
from Folder.myroutes.flight_support import find_tow_matchs
import Folder.myroutes.aircraft as a
import Folder.myroutes.analyse_support as asup
import Folder.myroutes.my_utils as utils
import Folder.myroutes.flight_audit_log as sl
import Folder.myroutes.flight_db_support as fs_db
import Folder.myroutes.tows as t
from Folder.myroutes.flight_support import TowPairs


logging.basicConfig(encoding='utf-8', level=sl.logging.DEBUG)  # type: ignore[call-arg]


@app.route('/flight_edit', methods=['GET', 'POST'])
def flight_edit() -> render_template:
    """
    Main editing and management page for flight data.
    Uses data previously uploaded from KTRAX via the KTRAX import functions triggered from Index page
    Data stored in the Flights database table. Main place for edit data and adding flights not
    captured in KTRAX.
    :return:  render index page
    """
    VALID_DAY: bool = False

    # make sure there is a ops_date  set
    if global_vars.ops_date_str is None:
        flash('Must set an Ops Date')
        return redirect(url_for('index'))

    ops_days: list[int] = utils.get_ops_days_in_month(global_vars.ops_date_str)
    if request.method == 'POST':
        _ops_date_str = request.form.get('ops_date')
        print(f' ops date {_ops_date_str}')
        if _ops_date_str != '':
            _ops_date_dt = datetime.strptime(_ops_date_str, "%Y-%m-%d")
            today_day_in_month_str = _ops_date_str[8:]
            VALID_DAY = today_day_in_month_str in ops_days
            global_vars.ops_date_str = _ops_date_str
        else:
            flash('No operations this day  TRY one of...')
            flash(str(ops_days))
            return render_template('index.html')

    # get sheet id
    sheet_id: int = operations.get_sheet_id_for_date(global_vars.ops_date_str)

    # load aircraft list
    aircraft.load_global_aircraft_list()

    # load all flights for selected day
    all_data: list = Flight.query.filter(Flight.to_date_str == global_vars.ops_date_str).order_by(Flight.flt_id).all()

    fs_db.update_glider_ids_in_db(
        all_data)  # update  the database "Flight" records from Aircraft table leaving unknowns

    all_data: list = Flight.query.filter(Flight.to_date_str == global_vars.ops_date_str) \
        .order_by(Flight.flt_id).all()  # get data again after update

    data_frame: list = fs_db.load_flight_from_db(all_data, sheet_id)

    # --Check for unknown pilots, unallocated launch height and unverified data

    unknown_height = audit.audit_heights(data_frame)  # limited to the chosen sheet id

    clean_audit = audit.report_audit(all_data)

    # -- find the tow - glider pair matches and load the pair ids into the data base when found

    tows, tow_but_no_glider, glider_but_no_tow = find_tow_matchs(all_data)

    if len(tows) > 0:
        fs_db.add_tow_pair_data_to_db(tows)  # append flight ids to database records

    if len(tow_but_no_glider) != 0:
        outstr = str(tow_but_no_glider)
        flash(f" Unknown aircraft {outstr}/flights")
        logging.debug(f" Unknown aircraft {outstr}")

    # if there is flight data - go to web page

    if data_frame:
        return render_template('web_flights.html', ops_date=global_vars.ops_date_str, flights=data_frame)
    # -- there was no data -----
    flash(f" No data for this date: {global_vars.ops_date_str} /flights")
    return render_template('index.html')


@app.route('/flight_delete/<int:_id>', methods=['GET', 'POST'])
def flight_delete(_id: int) -> redirect:
    """
    Delete one record 'flt_id'.  'flt_id' is not primary key
    :param _id is primary key
    :return: redirect

    """
    Flight.query.filter_by(id=_id).delete()
    # db.session.delete(my_data)
    db.session.commit()
    flash('Flight deleted')

    return redirect(url_for('flight_edit'))


@app.route('/flight_verify/<int:_id>', methods=['GET'])
def flight_verify(_id: int) -> redirect:
    """ Change the "status" record to VERIFIED.

    Args:
        _id: integer id of the seleted record

    return: redirect to flight edit
    """

    my_data = Flight.query.filter_by(id=_id).first()
    my_data.status = 'VERIFIED'
    db.session.commit()
    flash('Flight verified')

    return redirect(url_for('flight_edit'))


@app.route('/flight_unverify/<int:_id>', methods=['GET'])
def flight_unverify(_id: int):
    """
    Change the "status" record to EDIT.

    Args:
        _id: integer id of the seleted record
    """

    my_data = Flight.query.filter_by(id=_id).first()
    my_data.status = 'EDIT'
    db.session.commit()
    flash('Flight removed from verification')

    return redirect(url_for('flight_edit'))

#
# @app.route('/flights_tug_add', methods=['GET', 'POST'])
# def flights_tug_add():
#     """
#     Add a (missing) Tug flight to the daily flight sheet records.
#
#     Uses a data entry form Tug_Form
#     Writes the user input data to the Tug database
#     """
#     form = Tug_Form()
#     tug_to_date_str = global_vars.ops_date_str
#     tug_to_date_dt = datetime.fromisoformat(tug_to_date_str)
#
#     if form.validate_on_submit():
#         registration = form.registration.data
#         _take_off_date = form.take_off_date.data
#         _take_off_time = form.take_off_time.data
#
#         take_off_dt = datetime.combine(_take_off_date, _take_off_time)
#         if registration in ['PXI', 'TNE', 'KKZ']:
#             _flt_class = 'TUG'
#         else:
#             flash('TUG Rego not in list')
#             return redirect(url_for('flight_edit'))
#
#         status = "EDIT"
#         _seq_num = random.randint(120000000000, 900000000000)
#         my_flt_id = util.make_id_dt_dt(_take_off_date, _take_off_time)
#         int_flt_id = int(my_flt_id) - 1
#
#         my_webdata = Flight(
#             seq_num=_seq_num,
#             flt_id=int_flt_id,
#             flt_class=_flt_class,
#             to_date_str=take_off_date_str,
#             to_time_dt=take_off_dt,
#             ld_time_dt=None,
#             flt_time=0,
#             aircraft=registration,
#             pilot_name=None,
#             pilot2_name=None,
#             heavy=False,
#             OGN_ht=0,  # OGN_ht,
#             launch_ht=0,  # launch_ht,
#             status=status,  # status,
#             sheet_number=0,
#             cost=None,
#             pair_id=None,
#             launch_id=None,
#             pilot_id=None,
#         )
#         db.session.add(my_webdata)
#         db.session.commit()
#
#         flash('Tug Add')
#         return redirect(url_for('flight_edit'))
#
#     return render_template('/tug_insert.html', form=form, to_date=tug_to_date_dt)
#
#
# @app.route('/flights_tug_update/<int:_id>', methods=['GET', 'POST'])
# def flights_tug_update(_id: int):
#     """
#     Main workhorse page
#     Pops as a modal on the Webflights page
#     Used to edit / add / correct flight data - mostly set launch height.
#
#     :return: Edited flight record stored in DATABASE
#
#     Args:
#         _id: int - record id for tug flight
#
#     Returns:
#         redirect: 'flight_edit' after data stored
#         render_template: 'tug_update.html' to display data form
#     """
#     fltform = Tug_UpdateForm()
#     my_data: Flight = Flight.query.get(_id)
#     to_date_dt = datetime.strptime(my_data.to_date_str, "%Y-%m-%d")
#
#     if request.method == 'GET':
#         fltform.sheet_number.data = my_data.sheet_number
#         # fltform.flt_class.data = my_data.flt_class
#         fltform.tug.data = my_data.to_date_dt
#         fltform.take_off_time.data = my_data.to_time_dt
#         fltform.landing_time.data = my_data.ld_time_dt
#
#         fltform.OGN_ht.data = my_data.OGN_ht
#         fltform.launch_ht.data = my_data.launch_ht
#
#     elif request.method == 'POST':
#         _to_time = form.take_off_time.data
#         my_data.to_time_dt = util.combine_to_dt(my_data.to_date_str, _to_time_str)
#         _landing_time = form.landing_time.data
#         my_data.ld_time_dt = datetime.combine(to_date_dt, _landing_time)
#         if _landing_time:
#             my_data.ld_time_dt = datetime.combine(to_date_dt, _landing_time)
#             flt_timedelta = my_data.ld_time_dt - my_data.to_time_dt
#             my_data.flt_time = int(flt_timedelta.total_seconds() / 60)
#         my_data.flt_id = util.make_id_dt_dt(to_date_dt, _to_time_str)
#         my_data.aircraft = form.tug.data
#         my_data.OGN_ht = form.OGN_ht.data
#         my_data.launch_ht = form.launch_ht.data
#         my_data.sheet_number = form.sheet_number.data
#
#         db.session.commit()
#         flash("Towplane Flight Updated Successfully")
#         return redirect(url_for('flight_edit'))
#
#     return render_template('tug_update.html', form=fltform)

# @app.route('/flights_glider_add/<int:tug_id>', methods=['GET', 'POST'])
# def flights_glider_add(tug_id: int):
#     """
#     Used to INSERT an (absent)  glider flight record in the main Flights datatable
#     to pair with known tow.
#
#     Can only execute if there is an actual tow without glider record.
#
#     Args:
#         tug_id: int
#
#     Returns:
#         object: New Flights record stored in Flights DATABASE table if successful data entry
#     """
#     my_tug_data = Flight.query.get(tug_id)  # load the tug flight for basic reference data
#     if my_tug_data is None:
#         flash('Tow record not found')
#         return redirect(url_for('flight_edit'))
#
#     if request.method == 'POST':
#         web_data = request.form
#         my_flight = fs.process_glider_add_post(my_tug_dat, web_data )
#
#         db.session.add(my_flight)
#         db.session.commit()
#         flash('Flight inserted ')
#         return redirect(url_for('flight_edit'))
#
#     flightForm = fs.load_flightform(my_tug_data)
#
#     return render_template('glider_flight_add.html', form=flightForm)
#

# @app.route('/flights_glider_update/<int:_id>', methods=['GET', 'POST'])
# def flights_glider_update(_id):
#     """ Main workhorse page
#     Pops as a modal on the Flights page
#     Used to edit / add / correct flight data - mostly set launch height.
#
#     Args:
#         _id: the database id of the selected record
#
#     Returns:
#         object: HTML page object
#
#     """
#     form = Glider_UpdateForm()
#     my_data: Flight = Flight.query.get(_id)
#     to_date_dt = datetime.strptime(my_data.to_date_str, "%Y-%m-%d")
#
#     if request.method == 'POST' and form.validate_on_submit():
#
#         _to_time: time = form.glider_take_off.data
#         my_data.to_time_dt = datetime.combine(to_date_dt, _to_time)
#         _ld_time: time = form.glider_land.data
#
#         if _ld_time in [None, '', '00:00']:
#             my_data.ld_time = None
#             my_data.flt_time = 0
#             my_data.ld_time_dt = None
#         else:
#             my_data.ld_time_dt = datetime.combine(to_date_dt, _ld_time)
#             flt_timedelta = my_data.ld_time_dt - my_data.to_time_dt
#             my_data.flt_time = int(flt_timedelta.total_seconds() / 60)
#
#         my_data.flt_id = util.make_id_dt_dt(to_date_dt, _to_time)
#         my_data.aircraft = form.glider_rego.data
#         my_data.pilot_id, my_data.pilot_name = fs.check_and_update_pilot_name(form.pilot_name.data)
#         my_data.pilot2_name = form.pilot2_name.data
#         my_data.heavy = True
#         if my_data.sheet_number not in [None, '', 999]:
#             my_data.sheet_number = my_data.sheet_number
#         else:
#             my_data.sheet_number = operations.get_sheet_id_for_date(my_data.to_date_str)
#
#         db.session.commit()
#         flash("Glider Flight Updated Successfully")
#         return redirect(url_for('flight_edit'))
#
#     # ----  the initial form values load "GET" section
#
#     # if my_data.to_time_dt is not None:
#     #     form.to_time_str.data = my_data.to_time_dt.strftime("%H:%M")
#     # else:
#     #     to_time_str = ''
#     #     form.to_time_str.data = to_time_str
#     form.glider_take_off.data = my_data.to_time_dt
#     # if my_data.ld_time_dt is not None:
#     #     form.ld_time_str.data = my_data.ld_time_dt.strftime("%H:%M")
#     # else:
#     #     ld_time_str = ''
#     #     form.ld_time_str.data = ld_time_str
#     form.glider_land.data = my_data.ld_time_dt
#     form.glider_rego.data = my_data.aircraft
#     form.pilot_name.data = my_data.pilot_name
#     form.pilot2_name.data = my_data.pilot2_name
#
#     return render_template('glider_update.html', form=form)

