from __future__ import annotations
from typing import Dict, Optional
import logging

from flask import render_template, request, redirect, url_for, flash    # type: ignore
from Folder import db, global_vars, app
from Folder.models import Pilots
import csv
from Folder.my_forms.forms import Pilot_Form
from icecream import ic  # type: ignore


@app.route('/pilots')
def pilots_index():
    """
    Display all pilots.

    Returns:
        render_template: pilots_display.html
    """
    all_pilots = Pilots.query.order_by(Pilots.pilot_initials).all()

    return render_template('pilots_display.html', pilots_data=all_pilots)


@app.route('/pilot_insert', methods=['GET', 'POST'])
def pilot_insert():
    """
    Insert a new pilot into database from web page data entry.

    Returns:
        render_template: pilot_insert.html if data inputs
        redirect: pilots_index if data POSTED and stored
    """

    form = Pilot_Form()

    if request.method == 'POST' and form.validate_on_submit():

        pilot_initials = form.pilot_initials.data
        pilot_name = form.pilot_name.data
        email = force_pilot_initials_upper(form.email.data)
        phone = form.phone.data
        club_member = form.club_member.data
        contact = form.contact.data
        print(pilot_initials, pilot_name, email, phone, club_member, contact)

        my_data = Pilots(pilot_initials, pilot_name, email, phone, club_member, contact)
        # check to see if pilot already entered

        check: bool = check_pilot_initials(pilot_initials)  # see if already present
        if not check:  # if not.....
            db.session.add(my_data)
            db.session.commit()
            flash('Pilot inserted ')
        else:
            flash('Pilot already present ')
        return redirect(url_for('pilots_index'))

    return render_template('pilot_insert.html', form=form, data=global_vars.pilot_initials)


@app.route('/pilot_update/<int:_id>/', methods=['GET', 'POST'])
def pilot_update(_id: int) -> redirect:
    """
    Update a record in Pilots table.

    Args:
        _id: int - database id of the selected pilot

    Returns:
        redirect: 'pilots_index'
    """

    my_data = Pilots.query.get(_id)
    if my_data is not None:
        form = Pilot_Form()
        if request.method == 'GET':
            """ Load the form data """
            form.pilot_initials.data = my_data.pilot_initials
            form.pilot_name.data = my_data.pilot_name
            form.email.data = my_data.email
            form.phone.data = my_data.phone
            form.club_member.data = my_data.club_member
            form.contact.data = my_data.contact

            return render_template('pilot_update.html', form=form)

        if form.validate_on_submit():
            print(" In update --- 2")
            my_data.pilot_initials = form.pilot_initials.data
            my_data.pilot_name = form.pilot_name.data
            my_data.pilot_email = form.email.data
            my_data.pilot_phone = form.phone.data
            my_data.contact = form.contact.data
            my_data.club_member = form.club_member.data

            db.session.commit()

            flash("pilot Updated Successfully")
            return redirect(url_for('pilots_index'))


@app.route('/pilot_delete/<int:_id>/', methods=['GET', 'POST'])
def pilot_delete(_id: int) -> redirect:
    """
    Delete one pilot record from Pilots database.

    Args:
        _id: integer id value of record to be deleted

    Returns:
        redirect: 'pilots_index'
    """

    my_data = Pilots.query.get(_id)
    db.session.delete(my_data)
    db.session.commit()
    flash('Pilot deleted')

    return redirect(url_for('pilots_index'))


@app.route('/pilots/get_csv')
def pilot_get_csv():
    """
    load pilot data from csv file ( used on rare database bulk  loads
    csv file is prespecified.

    Returns:
        redirect: 'pilots_index'
    """

    with open('d:/DATA/pilots.csv', newline='') as csvfile:
        ...
        all_pilots = csv.DictReader(csvfile)
        logging.info("opened file")

        for row in all_pilots:

            pilot = Pilots.query.filter(Pilots.initials == row['initials']).first()
            if pilot is None:
                logging.debug(" No existing pilot")
                row['club_member'] = row['club_member'] == 'TRUE'
                my_data = Pilots(row['initials'], row['pilot_name'], row['email'],
                                 row['phone'], row['club_member'], row['contact'])

                logging.debug(f"Mydata: {my_data}")
                db.session.add(my_data)
                db.session.commit()
            else:
                logging.debug('Existing pilot')

    return redirect(url_for('pilots_index'))


def get_pilot_object_from_initials(initials: str) -> Optional[Dict[str, str]]:
    """
    Get one pilot record based on initials.

    Args:
        initials: str - Pilot initials

    Returns:
        rec: dict | None - Pilot record as a dictionary or None if not found
    """
    if initials is not None and initials != "":
        try:
            rec = Pilots.query.filter_by(pilot_initials=initials).first()
            if rec is not None:
                print(f"PILOT Found:{rec.pilot_name}")
                return rec.to_dict()
            else:
                print(f"Pilot not found  {initials}")
        except Exception as e:
            print(f"Error occurred: {str(e)}")
    else:
        print("Invalid initials")

    return None


def check_pilot_initials(initials: str):
    """
    Check the Pilots data base for pilot with initials.

    return

    Args:
        initials: str - Pilot initials

    Returns:
        bool: None if no record else True
    """
    rec = Pilots.query.filter_by(pilot_initials=initials).first()

    return bool(rec)


def force_pilot_initials_upper(_name: str) -> str:
    """
    Helper function to force upper case on pilot initials.

    Args:
        _name: Pilot initials - possibly lower case

    Returns:
        name : str
    """
    if _name is None:
        return None
    if isinstance(_name, str):
        _name = _name.strip()
        return _name.upper() if len(_name) == 2 else _name
    else:
        return _name


def get_name_from_initials(initials: str) -> str:
    """Get the matching name text of supplied initials

    Args:
        initials: pilot initials

    Returns: pilot name
        object: pilot name
    """

    rec = Pilots.query.filter_by(pilot_initials=initials).first()

    return rec.pilot_name if rec else ''

def get_pilot_object_from_namestring(namestring: str) -> Pilots | None:
    """
    Get a pilot data object from database - search key in initial pair.

    Args:
        namestring: pilot name ( or initials?)

    :return: rec : database query from Pilot db
      """

    rec = Pilots.query.filter_by(pilot_name=namestring).first()
    if rec is not None:
        print(f"PiLOT Found:{rec.pilot_initials, rec.pilot_name}")
    else:
        print(f"Pilot not found  {namestring}")

    return rec

def check_and_update_pilot_name(_name: str) -> tuple[int | None, str | None]:
    """
    Helper function for pilot initials and name.

    Args:
        _name: Target name for lookup

    Returns:
        object: tuple of pilot id and pilot name OR None

    """

    pilot_id: int | None = None
    pilot_name: str | None = None

    if len(_name) == 2:
        this_initials = _name.upper()
        pilot_name = this_initials  # set the name
        record = p.get_pilot_object_from_initials(this_initials)  # Find the id
        pilot_id = record.id if record is not None else None
    elif len(_name) > 2:
        record = p.get_pilot_object_from_namestring(_name.strip().title())
        pilot_id = record.id if record is not None else None
        pilot_name = _name

    return pilot_id, pilot_name