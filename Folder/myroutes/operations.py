from __future__ import annotations
from datetime import datetime
from collections import defaultdict
import logging

from flask import render_template, request, redirect, url_for, flash  # type: ignore[import]
from Folder import db, app
from icecream import ic  # type: ignore[import]
from Folder.models import Ops_days
from Folder.my_forms.forms import Ops_UpdateForm, Ops_Delete_DayForm

# used in header.html
@app.route('/operations', methods=['GET', 'POST'])
def operations():
    all_data = Ops_days.query.with_entities(Ops_days.sheet_id, Ops_days.flying_day).all()

    dataset = defaultdict(list)
    for row in all_data:
        dataset[row.sheet_id].append(row.flying_day)

    my_data: dict[str, str] = {sheet: ' '.join(day) for sheet, day in dataset.items()}

    return render_template('operations.html', ops_data=list(my_data.items()))

# used in operations.html
@app.route('/ops_day_insert', methods=['GET', 'POST'])
def ops_day_insert():
    """
    Insert a day.

    Returns:
        redirect

    """
    form = Ops_UpdateForm()

    if request.method == 'POST' and form.validate_on_submit():

        sheet_id : int  = form.sheet_id.data
        flying_day : date = form.flying_day.data

        print(sheet_id, flying_day)

        # Call the service layer to handle the business logic
        ops_service.insert_day(sheet_id, flying_day)

        return redirect(url_for('operations'))

    return render_template('ops_add_day.html', form=form)


# Service Layer
def insert_day(sheet_id: int, flying_day: date):
    """
    Insert a day.

    Args:
        sheet_id: The ID of the sheet.
        flying_day: The flying day.

    Returns:
        None
    """
    my_data = Ops_days(sheet_id, flying_day, 0, 0)
    if check := Ops_days.query.filter_by(flying_day=flying_day).first():
        flash(f'Day {flying_day} already present')
    else:
        with db.session.begin():
            db.session.add(my_data)
            flash(f'Day {flying_day} inserted')

# used in operations.html
@app.route('/ops_day_delete', methods=['GET', 'POST'])
def ops_day_delete():
    """
    Delete a day.
    Returns: redirect

    """
    form = Ops_Delete_DayForm()

    if form.validate_on_submit():

        flying_day = form.flying_day.data

        logging.info(f'Flying day: {flying_day}')
        if (check := Ops_days.query.filter_by(flying_day=flying_day).first()) is not None:
            try:
                db.session.delete(check)
                db.session.commit()
                flash(f'Error deleting day: {e}')
            except Exception as e:
                flash(f'Error deleting day: {e}')
        else:
            flash('The day does not exist in the database.')
        
        return redirect(url_for('operations'))
    
    return render_template('ops_day_delete.html', form=form)


class SheetIdNotFoundError(Exception):
    pass

def get_sheet_id_for_date(_date: str) -> int:
    """
    get the sheet id for the selected date.

    Args:
        _date: str

    Returns:
       sheet_id: int

    Raises:
        ValueError: If sheet ID is not found for the selected date.
    """
    try:
        date_obj = datetime.strptime(_date, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Incorrect date format. Date should be in the format 'YYYY-MM-DD'")

    sheet_data = Ops_days.query.get(date_obj)
    if sheet_data:
        ic(sheet_data)
        return sheet_data.sheet_id
    else:
        raise ValueError("Sheet ID not found for the selected date")
