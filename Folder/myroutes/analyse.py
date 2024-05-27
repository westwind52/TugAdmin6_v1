from Folder import global_vars, app
# from run import app
from flask import render_template, redirect, url_for, flash, request  # type: ignore[import]
from Folder.models import Flight, Ops_days, TowPairs, Frame
import Folder.myroutes.analyse_support as asup
import Folder.myroutes.tows_support as ts

my_tows: list[TowPairs] = []
data_frame: list[Frame] = []
sheet_number: int = 0


@app.route('/analyse', methods=["GET", "POST"])
def analyse():  #
    """
    Control logic for the Launches  record html view.
    Uses scan logic to assemble tug-glider flight pairs from the flights database.

    Presumes that all flight detail editing will be done in the "flights" view.

    :return: data to template "daily_tow_display.html"
    """
    global my_tows
    global sheet_number
    global data_frame

    get_date: Union[str, None] = global_vars.ops_date_str

    # get all flights for the chosen day

    all_flights: list[Flight] = Flight.query.filter(Flight.to_date_str == get_date).order_by(Flight.flt_id).all()

    tow_set: list[TowPairs] = ts.create_tow_set(all_flights)

    data_frame = asup.build_tow_pairs(tow_set)

    if request.method == 'POST':
        # result = request.form.get('cbox')
        # chkflag = asup.set_overwrite(result)
        writeflag = request.form.get('writesheet')
        if writeflag:
            print("write flag")
            asup.store_launches(data_frame, sheet_number)
            return redirect(url_for('all_tows_load'))

        return render_template('daily_tow_display.html', flt_data=data_frame, sheet=str(sheet_number),
                               chkflag=chkflag, writeflag=writeflag, to_date_str=get_date)

    return render_template('daily_tow_display.html', flt_data=data_frame, sheet=str(sheet_number), to_date_str=get_date)


@app.route('/tow_glider_verify/<int:_id>', methods=['GET'])
def tow_glider_verify(_id: int) -> redirect:
    """
    sets the Status column in the flights database to VERIFIED.

    Args:
        _id: tug or glider id to be updated

    Returns:
        object: redirect to  main analysis webpage
    """

    global my_tows

    asup.update_status(my_tows[_id - 1].tug_id, 'VERIFIED')
    asup.update_status(my_tows[_id - 1].glider_id, 'VERIFIED')
    flash('Flight verified')

    return redirect(url_for('analyse'))


@app.route('/tow_glider_unverify/<int:_id>', methods=['GET'])
def tow_glider_unverify(_id: int):
    """
    sets the Status column in the flights database to UNVERIFIED.

        Return to the main analysis webpage

    Args:
        _id: tug r glider id to unverify
        """

    asup.update_status(my_tows[_id - 1].tug_id, 'EDIT')
    asup.update_status(my_tows[_id - 1].glider_id, 'EDIT')
    flash('Flight verified')

    return redirect(url_for('analyse'))


@app.route('/save_launches')
def save_launches():
    """
    initiate the DB write for selected launches.

    *** relies on global variables data_frame and sheet_number ***
    Return to the master /index page
    """
    global data_frame
    global sheet_number

    # if request.method == 'POST':
    print('found POST')
    asup.store_launches(data_frame, sheet_number)
    print(" SAV Launches")
    return redirect(url_for('index'))


@app.route('/sheet_audit')
def sheet_audit():
    print('In sheet audit')
    print(data_frame)
    print(my_tows)
    print(global_vars.ops_date_str)

    return redirect(url_for('analyse'))
