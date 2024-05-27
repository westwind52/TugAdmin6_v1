from flask import render_template, request, redirect, url_for, flash  # type: ignore
import random
import logging
from icecream import ic  # type: ignore
from datetime import datetime
from Folder import global_vars, db, app
from Folder.my_forms.forms import Glider_UpdateForm, Tug_Form, Tug_UpdateForm, Glider_Short_InsertForm
from Folder.myroutes import aircraft
from Folder.myroutes import operations
from Folder.models import Aircraft, Ops_days, Flight, Frame
import Folder.myroutes.my_utils as util
import Folder.myroutes.tows_support as tow_support
import Folder.myroutes.aircraft as a
import Folder.myroutes.pilots as p
import Folder.myroutes.analyse_support as asup
import Folder.myroutes.my_utils as utils
from Folder.myroutes.tows_support import TowPairs


@app.route('/all_tows_load', methods=['GET', 'POST'])
def all_tows_load() -> render_template:
    """
    Main editing and management page for flight data.
    Uses data previously uploaded from KTRAX via the KTRAX import functions triggered from Index page
    Data stored in the Flights database table. Main place for edit data and adding flights not
    captured in KTRAX.
    :return:  render index page
    """

    # make sure there is a ops_date  set
    if global_vars.ops_date_str is None:
        flash('Must set an Ops Date')

        return redirect(url_for('index'))
    _ops_date = global_vars.ops_date_str

    # load aircraft list
    aircraft.load_global_aircraft_list()

    # load all flights for selected day
    all_data = Flight.query.filter(Flight.to_date_str == _ops_date).order_by(Flight.flt_id).all()

    # tow_support.update_glider_ids_in_db(all_data)  # update  the database "Flight" records from Aircraft table leaving unknowns
    # all_data = Flight.query.filter(Flight.to_date_str == _ops_date) \
    #     .order_by(Flight.flt_id).all()  # get data again after update
    if _todays_tows := tow_support.create_tows(all_data):
        return render_template('tows.html', tows=_todays_tows)
    # -- there was no data -----
    flash(f" No data for this date: {_ops_date} /flights")
    return render_template('index.html')

# used from tows.html
@app.route('/glider_add/<int:tug_id>', methods=['GET', 'POST'])
def glider_add(tug_id: int):
    """
    Used to INSERT an (absent)  glider flight record in the main Flights datatable
    to pair with known tow.

    Can only execute if there is an actual tow without glider record.

    Args:
        tug_id: int

    Returns:
        object: New Flights record stored in Flights DATABASE table if successful data entry
    """
    my_tug_data = Flight.query.get(tug_id)  # load the tug flight for basic reference data
    if my_tug_data is None:
        flash('Tow record not found')
        return redirect(url_for('all_tows_load'))
    _to_date: datetime = my_tug_data.to_time_dt.date()
    _seq_num = my_tug_data.seq_num + 1
    flightForm: Glider_Short_InsertForm = Glider_Short_InsertForm()  # establish a blank for for data entry

    if request.method == 'POST':
        # web_data = request.form
        # my_flight = tow_support.process_glider_add_post(my_tug_data, flightForm)

        to_time: time  = flightForm.glider_take_off.data
        _to_time_dt : datetime = datetime.combine(_to_date, to_time)
        _int_flt_id: int = int(util.make_id_dt_dt(_to_date, to_time))
        if ld_time := flightForm.glider_land.data:
            _ld_time_dt = datetime.combine(_to_date, ld_time)
        else:
            _ld_time_dt = None

        _pilot_name = p.force_pilot_initials_upper(flightForm.pilot_name.data)
        # check to see if already present ( by date and take off time)
        my_glider_data = Flight.query.get(flt_id)
        if my_glider_data is not None and my_glider_data.flt_class != 'TUG':
            flash('Glider record already present')
            return redirect(url_for('all_tows_load'))

        my_flight = Flight(
            seq_num=_seq_num,
            flt_id=_int_flt_id,
            flt_class='GLIDER',
            to_date_str=_to_date_str,
            to_time_dt=_take_off_dt,
            ld_time_dt=_ld_time_dt,
            flt_time=0,
            aircraft=flightForm.glider.data,
            pilot_name=_pilot_name,
            pilot2_name=None,
            heavy=True,
            OGN_ht=0,  # OGN_ht,
            launch_ht=0,  # launch_ht,
            status='EDIT',  # status,
            sheet_number=999,
            cost=None,
            pair_id=tug_id,
            launch_id=None,
            pilot_id=None,
        )
        db.session.add(my_flight)
        db.session.commit()
        my_tug_data = Flight.query.get(my_flight.pair_id)
        my_tug_data.pair_id = my_flight.id
        db.session.add(my_tug_data)
        db.session.commit()
        flash('Glider inserted ')
        return redirect(url_for('all_tows_load'))

    # tug_seq_num = my_tug_data.seq_num

    flightForm.glider_take_off.data = my_tug_data.to_time_dt.time()  # set in form

    return render_template('glider_flight_add.html', form=flightForm)

# used from tows.html
@app.route('/tug_add', methods=['GET', 'POST'])
def tug_add():
    """
    Add a (missing) Tug flight to the daily flight sheet records.

    Uses a data entry form Tug_Form
    Writes the user input data to the Tug database
    """
    form = Tug_Form()
    _to_date_str = global_vars.ops_date_str
    _to_date_dt = datetime.fromisoformat(_to_date_str)

    if form.validate_on_submit():
        # --------------------
        _registration = form.registration.data
        _to_date = form.take_off_date.data
        _to_time = form.take_off_time.data
        # -------------------

        _take_off_dt = datetime.combine(_to_date, _to_time)
        _flt_class = 'TUG' if _registration in ['PXI', 'TNE', 'KKZ'] else "VISITOR"
        _status = "EDIT"
        _seq_num = random.randint(120000000000, 900000000000)
        _my_flt_id = util.make_id_dt_dt(_to_date, _to_time)
        _int_flt_id = int(_my_flt_id) - 1

        my_webdata = Flight(
            seq_num=_seq_num,
            flt_id=_int_flt_id,
            flt_class=_flt_class,
            to_date_str=_to_date_str,
            to_time_dt=_take_off_dt,
            ld_time_dt=None,
            flt_time=0,
            aircraft=_registration,
            pilot_name=None,
            pilot2_name=None,
            heavy=True,
            OGN_ht=0,  # OGN_ht,
            launch_ht=0,  # launch_ht,
            status=_status,  # status,
            sheet_number=0,
            cost=None,
            pair_id=None,
            launch_id=None,
            pilot_id=None,
        )
        db.session.add(my_webdata)
        db.session.commit()

        flash('Tug Add')
        return redirect(url_for('flight_edit'))

    tug_to_date = global_vars.ops_date_str

    return render_template('/tug_insert.html', form=form, to_date=tug_to_date)

# used from tows.html
@app.route('/tug_update/<int:_id>', methods=['GET'])
def tug_update_get(_id: int):
    """
    Main workhorse page
    Pops as a modal on the Webflights page
    Used to edit / add / correct flight data - mostly set launch height.

    :return: Rendered template 'tug_update.html' to display data form

    Args:
        _id: int - record id for tug flight
    """
    fltform = Tug_UpdateForm()
    my_data = Flight.query.get(_id)
    to_date_dt = datetime.strptime(my_data.to_date_str, "%Y-%m-%d")

    fltform.sheet_number.data = my_data.sheet_number
    fltform.tug.data = my_data.aircraft
    fltform.take_off_date.data = to_date_dt
    fltform.take_off_time.data = my_data.to_time_dt
    fltform.landing_time.data = my_data.ld_time_dt
    fltform.OGN_ht.data = my_data.OGN_ht
    fltform.launch_ht.data = my_data.launch_ht

    return render_template('tug_update.html', form=fltform)


@app.route('/tug_update/<int:_id>', methods=['POST'])
def tug_update_post(_id: int):
    """
    Main workhorse page
    Pops as a modal on the Webflights page
    Used to edit / add / correct flight data - mostly set launch height.

    :return: Redirect to 'all_tows_load' after data stored

    Args:
        _id: int - record id for tug flight
    """
    fltform = Tug_UpdateForm()
    my_data = Flight.query.get(_id)
    to_date_dt = datetime.strptime(my_data.to_date_str, "%Y-%m-%d")

    fltform.populate_obj(my_data)
    my_data.to_time_dt = datetime.combine(to_date_dt, fltform.take_off_time.data)
    my_data.ld_time_dt = datetime.combine(to_date_dt, fltform.landing_time.data)
    if my_data.ld_time_dt is not None:
        _flt_timedelta = my_data.ld_time_dt - my_data.to_time_dt
        my_data.flt_time = int(_flt_timedelta.total_seconds() / 60)
    my_data.flt_id = util.make_id_dt_dt(to_date_dt, fltform.take_off_time.data)

    db.session.commit()
    flash("Towplane Flight Updated Successfully")
    return redirect(url_for('all_tows_load'))

# used from tows.html
@app.route('/glider_update/<int:_id>', methods=['GET', 'POST'])
def glider_update(_id):
    """ Main workhorse page
    Pops as a modal on the Flights page
    Used to edit / add / correct flight data - mostly set launch height.

    Args:
        _id: the database id of the selected tow's tug record

    Returns:
        object: HTML page object

    """
    form = Glider_UpdateForm()
    my_data = Flight.query.filter_by(id=_id).first()  # get the id reference form tug part

    if my_data is None:
        flash("Glider Flight missing at pair id")
        return redirect(url_for('all_tows_load'))

    if form.validate_on_submit():
        # -------------------------
        _to_time = form.glider_take_off.data
        _ld_time = form.glider_land.data
        _aircraft = form.glider_rego.data
        _pilot_name = form.pilot_name.data
        _pilot2_name = form.pilot2_name.data
        # -------------------------

        _to_date = my_data.to_time_dt.date() if my_data.to_time_dt is not None else None

        if _ld_time is None:
            my_data.ld_time_str = None
            my_data.flt_time = 0
            my_data.ld_time_dt = None
        else:
            _ld_time = _ld_time.replace(tzinfo=timezone.utc)  # Convert to timezone-aware datetime
            my_data.ld_time_dt = _ld_time
            flt_timedelta = my_data.ld_time_dt - my_data.to_time_dt
            my_data.flt_time = int(flt_timedelta.total_seconds() / 60)

        my_data.flt_id = p.make_id_dt_dt(_to_date, _to_time)
        my_data.aircraft = _aircraft
        my_data.pilot_id, my_data.pilot_name = p.check_and_update_pilot_name(_pilot_name)
        pilot_id, my_data.pilot2_name = p.check_and_update_pilot_name(_pilot2_name)

        try:
            db.session.commit()
            flash("Glider Flight Updated Successfully")
        except Exception as e:
            flash(f"Error occurred while updating glider flight: {str(e)}")
            raise e
        finally:
            db.session.rollback()

        return redirect(url_for('all_tows_load'))
    # ----  the initial form values load "GET" section

    form = glider_load_form(my_data, form)

    return render_template('glider_update.html', form=form)

# used from tows.html
@app.route('/glider_delete/<int:glider_id>')
def glider_delete(glider_id: int) -> redirect:
    """
    Delete one record 'flt_id'.  'flt_id' is not primary key
    :param glider_id is primary key
    :return: redirect

    """

    try:
        if glider_id <= 0:
            flash('Invalid glider ID')
            return redirect(url_for('all_tows_load'))

        my_data = Flight.query.get(glider_id)
        if my_data is not None:
            tug_id = my_data.pair_id
            my_data.pair_id = None
            db.session.commit()

            Flight.query.filter_by(id=glider_id).delete()
            db.session.commit()
            flash('Flight deleted')

            my_data = Flight.query.get(tug_id)
            if my_data is not None:
                my_data.pair_id = None
                db.session.commit()
    except Exception as e:
        flash(f'Error deleting flight: {str(e)}')
    return redirect(url_for('all_tows_load'))


def glider_load_form(my_data: Flight, form: Glider_UpdateForm) -> Glider_UpdateForm:
    """
    loads string data into form for html for from Flight dataclass
    Returns:
        form: Glider_UpdateForm - an instance of Glider_UpdateForm
    """
    try:
        form.glider_take_off.data = my_data.to_time_dt.time() if my_data.to_time_dt is not None else ''
        form.glider_land.data = '' if my_data.ld_time_dt is None else my_data.ld_time_dt.time()
        form.glider_rego.data = my_data.aircraft
        form.pilot_name.data = my_data.pilot_name
        form.pilot2_name.data = my_data.pilot2_name
    except Exception as e:
        flash(f"Error occurred while loading glider form: {str(e)}")
        raise e
    return form


#
# def process_glider_add_post(my_tug_data: Flight, my_form) -> Flight:
#     """
#     Load the new glider record using Flights model from SQLAlchemy
#
#     Args:
#         my_tug_data: Flight data record for the matching tug flights
#         my_form: from webform -  record for the glider to be inserted
#
#     Returns:
#         Flight: Flights record
#     """
#     seq_num = get_seq_num(my_tug_data.seq_num)
#     to_date_str = global_vars.ops_date
#     to_time_str = my_form['to_time_str']
#     to_time_dt = util.combine_to_dt(to_date_str, to_time_str)
#     flt_id = int(util.make_id(to_date_str, to_time_str))
#     if my_form['ld_time_str'] and my_form['ld_time_str'] and my_form['ld_time_str'] != '00:00':
#         ld_time_dt = get_ld_time_dt(to_date_str, my_form['ld_time_str'])
#     else:
#         ld_time_dt = None
#     _aircraft = my_form['aircraft'].upper()
#     pilot_name = p.force_pilot_initials_upper(my_form['pilot_name'])
#
#     return Flight(
#         seq_num=seq_num,
#         flt_id=flt_id,
#         flt_class='GLIDER',
#         to_date_str=to_date_str,
#         to_time_dt=to_time_dt,
#         ld_time_dt=ld_time_dt,
#         flt_time=0,
#         aircraft=_aircraft,
#         pilot_name=pilot_name,
#         heavy='Y',
#         OGN_ht=0,  # OGN_ht,
#         launch_ht=0,  # launch_ht,
#         status='EDIT',  # status,
#         sheet_number=my_tug_data.sheet_number,
#         cost=0.0,
#         pair_id=my_tug_data.id,
#         launch_id=0,
#         pilot_id=0,
#     )
#

def create_tow_sheet(_data: list[Frame]) -> list[list[str]]:
    all_rows: list[list[str]] = [ls.make_header_row()] + [
        [f'{row.tow_date_dt:%Y-%m-%d}',
         f'{row.tow}',
         row.payer,
         row.tug_rego,
         row.glider_rego,
         row.tug_to_str,
         f'{row.billed_ht}',
         f'{row.t_flt_time}',
         f'{row.g_flt_time}',
         f'{row.heavy}',
         f'{row.tow_cost:.2f}',
         f'{row.glider_cost:.2f}'
         ] for row in _data
    ]

    print([item[2:] for item in all_rows])

    return all_rows
