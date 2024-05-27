from __future__ import annotations

from collections import namedtuple
from datetime import datetime, time, timedelta
import pickle
from typing import Any,Tuple
from Folder import db, global_vars
from Folder.models import Flight, Uploads, Aircraft, Pilots
from Folder.myroutes import my_utils as util


def make_flight_dict_record(flight: Flight) -> dict[str, Any]:
    """
    make a dictionary object from one flight data db object.

    :return:

    Args:
        flight: Flight drawn from one database record from  Flights

    Returns:
        dict[str, Any]: rec: dict with full data for one flight
    """
    rec: dict[str, Any] = {"id": flight.id,
                           "seq_num": flight.seq_num,
                           "flt_id": flight.flt_id,
                           "flt_class": flight.flt_class,
                           "to_date_str": flight.to_date_str,
                           "to_time_str": None,
                           "ld_time_str": None,
                           "flt_time": flight.flt_time,
                           "aircraft": flight.aircraft,
                           "pilot_name": flight.pilot_name,
                           "pilot2_name": '',
                           "heavy": flight.heavy,
                           "OGN_ht": flight.OGN_ht,
                           "launch_ht": flight.launch_ht,
                           "status": flight.status,
                           "sheet_number": flight.sheet_number,
                           "cost": flight.cost,
                           "pair_id": 0,
                           "launch_id": 0,
                           "pilot_id": 0
                           }

    if flight.to_time_dt is not None:
        rec['to_time_str'] = flight.to_time_dt.time().isoformat(timespec='minutes')

    if flight.ld_time_dt is not None:
        rec['ld_time_str'] = flight.ld_time_dt.time().isoformat(timespec='minutes')

    return rec


def make_flt_rec(rec: dict) -> tuple:
    """
    make named tuple data set for one flight record.

    Args:
        rec:  dict object holding one flight

    Returns:
        named tuple:
    """

    namedTupleConstructor = namedtuple('Flight_record', ' '.join(sorted(rec.keys())))
    return namedTupleConstructor(**rec)


def make_id_dt_dt(my_date: datetime, my_time: time) -> str:
    """
    Compose a 12 character string as YYYYMMDDHHMM.

    Args:
        my_date: date as string
        my_time: time as string

    Returns:
        str: 12 character string, no delimiters
    """
    assert my_date is not None
    assert my_time is not None

    dt = datetime.combine(my_date, my_time)
    return dt.strftime('%Y%m%d%H%M')


def make_id_str_dt(my_date_str: str, my_time: time) -> str:
    """
    Compose a 12 character string as YYYYMMDDHHMM.

    Args:
        my_date_str: date as string
        my_time: time as string

    Returns:
        str: 12 character string, no delimiters
    """
    assert my_date_str is not None
    assert my_time is not None
    d = datetime.fromisoformat(my_date_str)
    dt = datetime.combine(d, my_time)
    return dt.strftime('%Y%m%d%H%M')

def make_id_str_str(my_date: str, my_time: str) -> str:
    """
    Compose a 12 character string as YYYYMMDDHHMM.

    Args:
        my_date: date as string
        my_time: time as string

    Returns:
        str: 12 character string, no delimiters
    """
    assert my_date is not None
    assert my_time is not None
    d = datetime.fromisoformat(my_date)
    t = time.fromisoformat(my_time)
    dt = datetime.combine(d, t)
    return dt.strftime('%Y%m%d%H%M')


def get_ld_time_dt(to_date_str: str, _ld_time_str: str) -> datetime | None:
    """
    Get the DATETIME formatted landing time for the flight, if known.

    Args:
        _ld_time_str: landing time as string
        to_date_str: Actual take off date as string

    Returns:
        object: Landing time as datetime
    """
    if _ld_time_str is not None and _ld_time_str != '' and _ld_time_str != '00:00':
        return util.combine_to_dt(to_date_str, _ld_time_str)
    return None


def combine_to_dt(my_date: str | None, my_time: str | None) -> datetime | None:
    """
    Combine a Date and a Time str objects to a datetime object.

    :param my_date:
    :param my_time:
    :return: dt : datetime object
    """

    if my_date is not None and my_time is not None:
        d = datetime.fromisoformat(my_date)
        t = time.fromisoformat(my_time)
        return datetime.combine(d, t)
    else:
        return None


def make_datetime_start_end_for_one_day(target_date: str, _days: int) -> [datetime, datetime]:
    """
    Returns:
        start and end dates in datetime format
    """
    return make_datetime_start_end_for_day_range(target_date, 1)


def make_datetime_start_end_for_day_range(target_date: str, _days: int) -> [datetime, datetime]:
    """
    Provide a datetime range of one day ( midnight).

    Returns: target_date_dt: datetime
            target_end_dt: datetime

    """
    target_date_dt = datetime.strptime(target_date, "%Y-%m-%d")
    target_end_dt = target_date_dt + timedelta(days=_days)

    return target_date_dt, target_end_dt


def make_datetime_one_calander_month(target_date: str) -> Tuple[datetime, datetime, str, str]:
    """
    Provide a datetime range of one month given number of days ( midnight).

    Args:
        target_date: str - date in YYYY-mm-dd format

    Returns: target_date_dt: datetime
             target_end_dt: datetime

    """

    month_first_day, month, days_per_month, month_name = get_days_in_month(target_date)

    target_date_dt = datetime.strptime(month_first_day, "%Y-%m-%d")
    target_end_dt = target_date_dt + timedelta(days=days_per_month)
    year_name = target_date[:4]

    return target_date_dt, target_end_dt, month_name, year_name


def make_date_start_end_str_one_month(target_date: str) -> Tuple[str, str, str]:
    """
    Provide a datetime range of one month given number of days ( midnight).

    Args:
        target_date: str - date in YYYY-mm-dd format

    Returns: month_first_day: str
             end_day_str: str

    """

    month_first_day, month, days_per_month, month_name = get_days_in_month(target_date)

    start_date_dt = datetime.strptime(month_first_day, "%Y-%m-%d")
    target_end_dt = start_date_dt + timedelta(days=days_per_month)
    end_day_str = datetime.strftime(target_end_dt, '%Y-%m-%d')

    return month_first_day, end_day_str, month_name


def get_days_in_month(target_date: str) -> Tuple[str, int, int, str]:
    """
    Derive the first day of month, and number of days in the month
    Args: target date (str) in isoformat yyyy-mm-dd
    Returns the first day in str form, and month name and days in month as ints
    """
    month_names = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                   'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    year_str = target_date[:4]
    if year_str.isdigit() and int(year_str) % 4 == 0:
        days_per_month[1] = 29

    month_str = target_date[5:7]
    print(f' Month string : {month_str}')
    month = int(month_str) if month_str.isdigit() else 0
    month_first_day = f'{target_date[:7]}-01'

    return month_first_day, month, days_per_month[month - 1], month_names[month - 1]


def get_ops_days_in_month(target_date: str) -> list[int]:
    """
    Return the ordered list of ops days in a month
    :param target_date:
    :return: ordered list of days
    """

    _month_first_day, _month_end_day, _month_name = make_date_start_end_str_one_month(target_date)

    return get_ops_days_in_time_period(_month_first_day, _month_end_day)


def get_ops_days_in_time_period(_begin_date: str, _end_date: str) -> [int]:
    """
    Get a sorted list of dates( day number) in a time period.
    :param _begin_date: str first day
    :param _end_date: str last day
    :return: [int]
    """
    _ops_days_set: set = set()
    all_data = Flight.query.filter(Flight.to_date_str >= _begin_date).filter(Flight.to_date_str <= _end_date) \
        .order_by(Flight.to_date_str).all()

    if len(all_data) > 0:
        _ops_days_set = {item.to_date_str[8:] for item in all_data}

    return sorted(_ops_days_set)


def check_duplicate_uploads(check_data: int) -> bool:
    """
    Check for pre-existing record in the Uploads table to prevent inserting a duplicate record.

    Args:
        check_data: this is the "seq_num" data element to be checked

    Returns:
        Bool: true / False to indicate duplicate
    """
    my_count = Uploads.query.filter_by(seq_num=check_data).count()
    return my_count > 0


def write_invoice_pickle():
    """
    Write the pickle on the last invoice number.

    Returns:

    """
    with open('d:\\data\\base_data', 'wb') as dbfile:
        pickle.dump(global_vars.last_invoice, dbfile)

    return


def updated_invoice() -> int:
    """
    Update the stored last invoice number and writ to pickle.

    Returns:
        global_vars.last_invoice["LAST_INVOICE"] : int
    """
    global_vars.last_invoice["LAST_INVOICE"] += 1
    write_invoice_pickle()

    return global_vars.last_invoice["LAST_INVOICE"]


def initialise_last_invoice():
    """

    Returns:

    """
    with open('d:\\data\\base_data', 'rb') as dbfile:
        global_vars.last_invoice = pickle.load(dbfile)

    return
