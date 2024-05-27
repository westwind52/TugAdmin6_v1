from typing import Optional
import logging
from sqlalchemy.sql.expression import text
from marshmallow import Schema, fields, validate
from flask import render_template, request, redirect, url_for, flash  # type: ignore[import]
from csv import DictReader
from Folder import db, global_vars, app
from Folder.models import Aircraft
from Folder.my_forms.forms import Aircraft_Form
from Folder.myroutes.pilots import check_pilot_initials, get_name_from_initials


@app.route('/aircraft')
def aircraft():
    """
    Load aircraft data into the html page.

    Returns:
        render_template
    """
    all_acft = get_all_aircraft()
    return render_template('aircraft_display.html', aircraft=all_acft)


def get_all_aircraft():
    """
    Fetch all aircraft data from the database.

    Returns:
        list: All aircraft data
    """
    try:
        return Aircraft.query.order_by(Aircraft.registration).all()
    except Exception as e:
        flash('Error retrieving aircraft data')
        return redirect(url_for('aircraft'))


class AircraftSchema(Schema):
    registration = fields.Str(required=True, validate=validate.Regexp('[A-Z]{3}', message="Rego is three upper case alpha characters"))
    make = fields.Str()
    pilot_initials = fields.Str(validate=validate.Length(min=2, max=2))
    normal_pilot = fields.Str()
    acft_class = fields.Str()
    self_launch = fields.Bool()

@app.route('/aircraft_insert', methods=['GET', 'POST'])
def aircraft_insert():
    """
    Insert new aircraft data from Form.

    Returns:
            redirect to url_for(aircraft)
    """
    form = Aircraft_Form()
    if form.validate_on_submit():

        registration = form.registration.data.upper()
        if rego_check(registration):
            flash(f'This Rego already present {registration}')
            return redirect(url_for('aircraft'))
        make = form.make.data
        pilot_initials = form.pilot_initials.data.upper()
        if not check_pilot_initials(pilot_initials):
            flash(f'Pilot not in database {pilot_initials}')
            return redirect(url_for('aircraft_insert'))  # Redirect to form page with error message
        normal_pilot = form.normal_pilot.data
        acft_class = form.acft_class.data
        heavy = True
        self_launch = form.self_launch.data

        my_acft = Aircraft(registration, make, self_launch, pilot_initials,
                           normal_pilot, acft_class, heavy)

        try:
            db.session.add(my_acft)
            db.session.commit()
            flash('glider inserted ')
        except Exception as e:
            flash(f'Error inserting glider: {str(e)}')
            flash(f'Error inserting glider: {str(e)}')

        return redirect(url_for('aircraft'))

    flash('Form validation failed')
    return render_template('aircraft_insert.html', form=form)


@app.route('/aircraft_update/<_id>', methods=['GET', 'POST'])
def aircraft_update(_id: int):
    """
    Update the data in one Aircraft.

    Args:
        _id: Aircraft identity 'id'

    Returns:
        redirect
    """
    my_data = Aircraft.query.get(_id)
    form = Aircraft_Form()
    
    if request.is_get:
        form.registration.data = my_data.registration
        form.make.data = my_data.make
        form.self_launch.data = my_data.self_launch is True
        form.pilot_initials.data = my_data.pilot_initials.upper()
        form.normal_pilot.data = my_data.normal_pilot
        form.acft_class.data = my_data.acft_class
        form.heavy.data = my_data.heavy is True

    if not form.validate():
        flash('Form validation failed')
        return render_template('aircraft_update.html', form=form)

    rego = form.registration.data.upper()

    my_data.make = form.make.data
    my_data.pilot_initials = form.pilot_initials.data
    try:
        if not check_pilot_initials(my_data.pilot_initials):
            raise Exception(f'Pilot not in database {my_data.pilot_initials}')
        my_data.normal_pilot = form.normal_pilot.data
        stored_name = get_name_from_initials(my_data.pilot_initials)
        if my_data.normal_pilot != stored_name:
            raise Exception(f'Different pilot name {my_data.normal_pilot} - {stored_name}')
    except Exception as e:
        flash(str(e))

    my_data.acft_class = form.acft_class.data
    my_data.heavy = True
    my_data.self_launch = form.self_launch.data

    db.session.commit()

    flash('Glider Updated Successfully')
    return redirect(url_for('aircraft'))


@app.route('/aircraft/get_csv')
def get_csv():
    try:
        with open('d:/DATA/aircraft.csv', newline='') as csvfile:
            all_acft = DictReader(csvfile)
            logging.info('opened file')

            for row in all_acft:
                row['self_launch']: int = int(row['self_launch'])
                row['heavy'] = int(row['heavy'])
                my_data = Aircraft(row['registration'], row['make'], row['self_launch'],
                                   row['pilot_initials'], row['normal_pilot'],
                                   row['acft_class'], row['heavy'], )
                logging.debug(f'Mydata: {my_data}')
                db.session.add(my_data)

            db.session.commit()
    except Exception:
        flash('Error reading the CSV file')
        return redirect(url_for('aircraft'))

    return redirect(url_for('aircraft'))


@app.route('/rego_check')
def rego_check(rego) -> bool:
    """
    Check to see if registration present in database.

    Args:
        rego: str - Aircraft registration

    Returns:
        check: bool - True if success

    """
    if not isinstance(rego, str) or not rego:
        return False
    check = Aircraft.query.filter_by(registration=rego).one_or_none()
    return check is not None


@app.route('/aircraft_delete/<int:_id>', methods=['GET', 'POST'])
def aircraft_delete(_id: int) -> object:
    """
    Delete one record 'flt_id'.  'flt_id' is not primary key.

    Args:
        _id: int - Aircraft record id

    Returns:
        redirect
    """
    try:
        my_data = Aircraft.query.filter_by(id=_id).first()
        if my_data:
            db.session.delete(my_data)
            db.session.commit()
            logging.info(f"Aircraft with id {_id} deleted")
            flash('Flight deleted')
        else:
            flash('Flight does not exist')
    except Exception as e:
        flash('Error deleting aircraft')
        logging.error(str(e))

    return redirect(url_for('aircraft'))


def get_all_aircraft(filter_param=None):
    """
    Get all aircraft records from db table.

    Args:
        filter_param: A parameter to filter the results based on certain criteria.

    Returns: List[Dict[str, Any]]: A list of dictionaries representing each aircraft record.
    """
    try:
        if filter_param:
            all_aircraft = Aircraft.query.filter_by(**filter_param).all()
        else:
            all_aircraft = Aircraft.query.all()
        
        aircraft_list = []
        for aircraft in all_aircraft:
            aircraft_dict = {
                'id': aircraft.id,
                'registration': aircraft.registration,
                'make': aircraft.make,
                'self_launch': aircraft.self_launch,
                'pilot_initials': aircraft.pilot_initials,
                'normal_pilot': aircraft.normal_pilot,
                'acft_class': aircraft.acft_class,
                'heavy': aircraft.heavy
            }
            aircraft_list.append(aircraft_dict)
        
        return aircraft_list
    
    except Exception as e:
        # Handle the exception here, e.g. log the error or return a default value
        print(f"Error occurred during database query: {str(e)}")
        return []

def get_aircraft(rego: str) -> Optional[Aircraft]:
    """
    Get individual aircraft by registration str.

    Args:
        rego: str

    Returns:
         Optional[Aircraft]: db record object or None
    """

    aircraft = Aircraft.query.filter_by(registration=rego).first()
    if aircraft is None:
        raise ValueError("Aircraft not found")
    return aircraft


def load_global_aircraft_list(acft):
    """
    Load the aircraft table in the provided dictionary.
    @param acft: The dictionary to store the aircraft information.
    @return: The updated dictionary.
    """
    try:
        if not acft:
            ac_records = Aircraft.query.all()
            acft = {ac.registration: [ac.pilot_initials, ac.heavy] for ac in ac_records}
    except Exception as e:
        print(f"An error occurred while loading the global aircraft list: {str(e)}")

    return acft
