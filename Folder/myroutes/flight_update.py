from __future__ import annotations

from flask import render_template, request, redirect, url_for, flash  # type: ignore[import]
from Folder.models import Flight
from typing import Union
from Folder import db, app
import Folder.myroutes.my_utils as util
import Folder.myroutes.pilots as p
from Folder.my_forms.forms import Glider_UpdateForm, Tug_UpdateForm


@app.route('/tug_update/<int:_id>', methods=['GET', 'POST'])
def tug_update(_id: int):
    """
    Main workhorse page
    Pops as a modal on the Webflights page
    Used to edit / add / correct flight data - mostly set launch height.

    :return: Edited flight record stored in DATABASE

    Args:
        _id: int - record id for tug flight

    Returns:
        redirect: 'flight_edit' after data stored
        render_template: 'tug_update.html' to display data form
    """
    fltform = Tug_UpdateForm()
    my_data = Flight.query.get(_id)

    if request.method == 'GET':
        fltform.sheet_number.data = my_data.sheet_number
        # fltform.flt_class.data = my_data.flt_class
        fltform.tug.data = my_data.aircraft
        fltform.to_date_str.data = my_data.to_date_str
        to_time_str = my_data.to_time_dt.strftime("%H:%M") if my_data.to_time_dt is not None else ''

        fltform.to_time_str.data = to_time_str
        ld_time_str = my_data.ld_time_dt.strftime("%H:%M") if my_data.ld_time_dt is not None else ''

        fltform.ld_time_str.data = ld_time_str

        fltform.OGN_ht.data = my_data.OGN_ht
        fltform.launch_ht.data = my_data.launch_ht

    elif request.method == 'POST':
        _to_time_str = request.form['to_time_str']
        my_data.to_time_dt = util.combine_to_dt(my_data.to_date_str, _to_time_str)
        _ld_time_str = request.form['ld_time_str']
        if _ld_time_str is not None and _ld_time_str != '':
            my_data.ld_time_dt = util.combine_to_dt(my_data.to_date_str, _ld_time_str)
            flt_timedelta = my_data.ld_time_dt - my_data.to_time_dt
            my_data.flt_time = int(flt_timedelta.total_seconds() / 60)
        my_data.flt_id = util.make_id_str_str(my_data.to_date_str, _to_time_str)
        my_data.aircraft = request.form['tug']
        my_data.OGN_ht = request.form['OGN_ht']
        my_data.launch_ht = request.form['launch_ht']
        my_data.sheet_number = request.form['sheet_number']

        db.session.commit()
        flash("Towplane Flight Updated Successfully")
        return redirect(url_for('flight_edit'))

    return render_template('tug_update.html', form=fltform)


@app.route('/glider_update/<int:_id>', methods=['GET', 'POST'])
def glider_update(_id: int):
    """ Main workhorse page
    Pops as a modal on the Flights page
    Used to edit / add / correct flight data - mostly set launch height.

    Args:
        _id: the database id of the selected record

    Returns:
        object: HTML page object

    """
    form = Glider_UpdateForm()
    my_data: Flight = Flight.query.get(_id)

    if request.method == 'POST':

        _to_time_str = form.to_time_str.data
        my_data.to_time_dt = util.combine_to_dt(my_data.to_date_str, _to_time_str)
        ld_time_str = form.ld_time_str.data
        if ld_time_str in [None, '', '00:00']:
            my_data.ld_time_str = None
            my_data.flt_time = 0
            my_data.ld_time_dt = None
        else:
            my_data.ld_time_dt = util.combine_to_dt(my_data.to_date_str, ld_time_str)
            flt_timedelta = my_data.ld_time_dt - my_data.to_time_dt
            my_data.flt_time = int(flt_timedelta.total_seconds() / 60)

        my_data.flt_id = util.make_id_str_str(my_data.to_date_str, _to_time_str)
        my_data.aircraft = form.glider_rego.data
        my_data.pilot_id, my_data.pilot_name = p.check_and_update_pilot_name(form.pilot_name.data)
        my_data.heavy = form.heavy.data.upper() == "Y"
        my_data.sheet_number = form.sheet_number.data

        db.session.commit()
        flash("Glider Flight Updated Successfully")
        return redirect(url_for('flight_edit'))
    # ----  the initial form values load "GET" section
    form.sheet_number.data = my_data.sheet_number
    form.flt_class.data = 'GLIDER'
    form.to_date_str.data = my_data.to_date_str

    if my_data.to_time_dt is not None:
        form.to_time_str.data = my_data.to_time_dt.strftime("%H:%M")
    else:
        to_time_str = ''
        form.to_time_str.data = to_time_str

    if my_data.ld_time_dt is not None:
        form.ld_time_str.data = my_data.ld_time_dt.strftime("%H:%M")
    else:
        ld_time_str = ''
        form.ld_time_str.data = ld_time_str

    form.glider_rego.data = my_data.aircraft
    form.pilot_name.data = my_data.pilot_name
    form.heavy.data = 'Y' if my_data.heavy else 'N'

    return render_template('glider_update.html', form=form)


# def process_glider_update_post(form, my_data):
# # _to_time_str = form.to_time_str.data
# my_data.to_time_dt = util.combine_to_dt(my_data.to_date_str, _to_time_str)
# ld_time_str = form.ld_time_str.data
# if ld_time_str != None and ld_time_str != '':
#     my_data.ld_time_dt = util.combine_to_dt(my_data.to_date_str, ld_time_str)
#     flt_timedelta = my_data.ld_time_dt - my_data.to_time_dt
#     my_data.flt_time = int(flt_timedelta.total_seconds() / 60)
# my_data.flt_id = util.make_id(my_data.to_date_str, _to_time_str)
# my_data.aircraft = form.aircraft.data
# my_data.pilot_name = form.pilot_name.data
# if len(my_data.pilot_name) == 2:
#     this_initials = my_data.pilot_name.upper()
#     my_data.pilot_name = this_initials
#     record = util.get_pilot_object_from_initials(this_initials)
#     if record is not None:
#         my_data.pilot_id = record.id
#     else:
#         my_data.pilot_id = None
# elif len(my_data.pilot_name) > 2:
#     this_name = my_data.pilot_name.strip().title()
#     record = util.get_pilot_object_from_namestring(this_name)
#     if record is not None:
#         my_data.pilot_id = record.id
#         my_data.pilot_name = this_name
#     else:
#         my_data.pilot_id = None
#
# return_value = form.heavy.data
# my_data.heavy = True if return_value == "Y" else False
# my_data.sheet_number = form.sheet_number.data
#   pass
