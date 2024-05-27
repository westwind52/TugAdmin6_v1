from flask import render_template, request, redirect, url_for, flash    # type: ignore[import]
import Folder.global_vars
from Folder import app
from Folder.models import Ops_days, TowPairs, FltShort, Flight
import Folder.myroutes.launch_sheet as sh
import Folder.myroutes.analyse_support as asup
import Folder.myroutes.flight_support as fs
import logging

logging.basicConfig(encoding='utf-8', level=logging.DEBUG)              # type: ignore[call-arg]


@app.route('/sheet_log', methods=['GET', 'POST'])
def sheet_log():
    # my_data: list[FltShort] = []

    if request.method != 'GET':

        return
    get_date = Folder.global_vars.ops_date_str

    # -- get the sheet id for the chosen day from table 'ops_days'

    get_sheet = Ops_days.query.filter(Ops_days.flying_day == Folder.global_vars.ops_date_str).first()
    if not get_sheet:
        flash(' No sheet id')
        # -- Quit if no sheet entered for that day
        return redirect(url_for('flight_edit'))

    str_sheet = str(get_sheet.sheet_id)     # get sheet number and convert to str
    """ should be a valid sheet id by now..."""
    _sheet_id = 0
    all_flights = sh.Flight.query.filter(sh.Flight.sheet_number == _sheet_id).all()
    """get all flights for the chosen sheet number """

    if len(all_flights) == 0:
        return redirect(url_for('flight_edit'))         # no flights so exit

    """should be at least one flight in all_flights at this stage"""
    my_tows, unknown_tow = fs.find_tow_matchs(all_flights)
    """ get the list of tow pairs in 'my_tows' """
    data_frame = []
    no_height = []

    for tow in my_tows:
        this_tow = asup.load_one_launch_frame_supervisor(tow)
        if this_tow.billed_ht == 0:
            no_height.append(tow.tug_id)
        data_frame.append(this_tow)

    """ check to see if there are still unknowns"""
    if len(unknown_tow) > 0 or no_height:
        if unknown_tow:
            # print(f" STOP -- Unknown Tows: {unknown_tow}")
            flash(f" There are still unknown tows: {unknown_tow}")
        if no_height:
            # print(f" STOP -- Unknown Launch Height: {no_height}")
            flash(f" There are still unknown launch height: {no_height}")
        return redirect(url_for('flight_edits'))

    """ all good so process data_frame"""
    # result = asup.load_flightOps_days(data_frame)
    return render_template('flight_sheet.html', flt_data=data_frame, sheet=str_sheet, to_date_str=get_date)
