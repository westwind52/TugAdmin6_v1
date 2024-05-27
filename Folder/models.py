from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy  # type: ignore
from dataclasses import dataclass
from datetime import datetime

db = SQLAlchemy()


@dataclass
class Tow:
    id: int = 0
    pilot1_name: str = ''
    pilot2_name: str = ''
    tug: str = ''
    glider: str = ''
    OGN_ht: int = 0
    launch_ht: int = 0
    to_time_str: str = ''
    ld_time_str: str = ''


@dataclass
class FullTow:
    id: int = 0
    pilot1_name: str = ''
    pilot2_name: str = ''
    tug: str = ''
    glider: str = ''
    to_time_str: str = ''
    tug_ld_time_str: str = ''
    glider_ld_time_str: str = ''
    OGN_ht: int = 0
    launch_ht: int = 0
    tug_flt_time: int = 0
    gld_flt_time: int = 0
    tow_cost: float = 0.0
    glider_cost: float = 0.0


@dataclass
class TowPairs:
    tow_daily_sequence: int
    tug_id: int | None
    glider_id: int | None


@dataclass
class FltShort:
    """ host the flight summary data"""

    id: int
    to_time: datetime
    rego: str
    flt_class: str


@dataclass
class Frame:
    """ Class to hold flight data pair ("tow" + "glider")"""

    sequence_num: int
    sheet_number: int
    tow: int
    tow_date_dt: datetime
    payer: str
    pilot2: str
    tug_rego: str
    glider_rego: str
    tug_to_str: str
    tug_ld_str: str
    gld_ld_str: str
    billed_ht: int = 0
    t_flt_time: int = 0
    g_flt_time: int = 0
    heavy: bool = True
    tow_cost: float = 0.0
    glider_cost: float = 0.0
    status: str = 'blank'
    written: datetime | None = None
    billed_date: datetime | None = None
    tug_flt_id: int = 0
    gld_flt_id: int = 0


@dataclass
class UploadRecord:
    seq_num: int
    category: str
    payer: str
    invoice: int
    bill_date: datetime
    due_date: datetime
    item: str
    quantity: int
    price: float
    description: str
    uploaded: datetime | None
    take_off_dt: datetime
    sheet_id: int = 0


class Flight(db.Model):
    id: int = db.Column(db.Integer(), primary_key=True)
    seq_num: int = db.Column(db.Integer(), unique=True)
    flt_id: int = db.Column(db.Integer())
    flt_class: str = db.Column(db.String(12))
    to_date_str: str = db.Column(db.String(12))
    to_time_dt = db.Column(db.DateTime())
    ld_time_dt = db.Column(db.DATETIME())
    flt_time: int = db.Column(db.Integer())
    aircraft: str = db.Column(db.String(10))
    pilot_name: str = db.Column(db.String(50))
    pilot2_name: str = db.Column(db.String(50))
    heavy: bool = db.Column(db.Boolean(), default=True)
    OGN_ht: int = db.Column(db.Integer(), default=0)
    launch_ht: int = db.Column(db.Integer(), default=0)
    status: str = db.Column(db.String(20))
    sheet_number: int = db.Column(db.Integer())
    cost: float = db.Column(db.Float())
    pair_id: int = db.Column(db.Integer(), default=0)
    launch_id: int = db.Column(db.Integer(), default=0)
    pilot_id: int = db.Column(db.Integer(), db.ForeignKey('pilots.id'))

    def __init__(self, seq_num: int, flt_id, flt_class, to_date_str, to_time_dt, ld_time_dt, flt_time,
                 aircraft, pilot_name, pilot2_name, heavy, OGN_ht, launch_ht, status,
                 sheet_number, cost, pair_id, launch_id, pilot_id):
        self.seq_num = seq_num
        self.flt_id = flt_id
        self.flt_class = flt_class
        self.to_date_str = to_date_str
        self.to_time_dt = to_time_dt
        self.ld_time_dt = ld_time_dt
        self.flt_time = flt_time
        self.aircraft = aircraft
        self.pilot_name = pilot_name
        self.pilot2_name = pilot2_name
        self.heavy = heavy
        self.OGN_ht = OGN_ht
        self.launch_ht = launch_ht
        self.status = status
        self.sheet_number = sheet_number
        self.cost = cost
        self.pair_id = pair_id
        self.launch_id = launch_id
        self.pilot_id = pilot_id


class Uploads(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    seq_num: int = db.Column(db.Integer(), unique=True)
    category: str = db.Column(db.String(12))
    payer_name: str = db.Column(db.String(50))
    invoice: int = db.Column(db.Integer())
    bill_date: str = db.Column(db.String(12))
    due_date: str = db.Column(db.String(12))
    item: str = db.Column(db.String(50))
    quantity: int = db.Column(db.Integer())
    price: float = db.Column(db.Float())
    description: str = db.Column(db.String())
    uploaded: str = db.Column(db.DATETIME)
    take_off_dt = db.Column(db.DATETIME)
    sheet_id: int = db.Column(db.Integer, default=0)

    def __init__(self, seq_num, category, payer_name, invoice, bill_date,
                 due_date, item, quantity, price, description, uploaded, take_off_dt, sheet_id):
        self.seq_num = seq_num
        self.category = category
        self.payer_name = payer_name
        self.invoice = invoice
        self.bill_date = bill_date
        self.due_date = due_date
        self.item = item
        self.quantity = quantity
        self.price = price
        self.description = description
        self.uploaded = uploaded
        self.take_off_dt = take_off_dt
        self.sheet_id = sheet_id


class Pilots(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    pilot_initials: str = db.Column(db.String(3), unique=True)
    pilot_name: str = db.Column(db.String(30))
    email: str = db.Column(db.String(50))
    phone: str = db.Column(db.String(15))
    club_member: bool = db.Column(db.Boolean())
    contact: str = db.Column(db.String(50))
    flights = db.relationship('Flight', backref='pilot')

    def __init__(self, pilot_initials, pilot_name, email, phone, club_member, contact):
        self.pilot_initials = pilot_initials
        self.pilot_name = pilot_name
        self.email = email
        self.phone = phone
        self.club_member = club_member
        self.contact = contact


class Aircraft(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    registration: str = db.Column(db.String(3), unique=True)
    make: str = db.Column(db.String(20))
    self_launch: bool = db.Column(db.Boolean())
    pilot_initials: str = db.Column(db.String(3))
    normal_pilot: str = db.Column(db.String(20))
    acft_class: str = db.Column(db.String(10))
    heavy: bool = db.Column(db.Boolean)

    def __init__(self, registration, make, self_launch, pilot_initials, normal_pilot, second_pilot,
                 acft_class, heavy):
        self.registration = registration
        self.make = make
        self.self_launch = self_launch
        self.pilot_initials = pilot_initials
        self.normal_pilot = normal_pilot
        self.second_pilot = second_pilot
        self.acft_class = acft_class
        self.heavy = heavy


class Launches(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)
    sequence_num: int = db.Column(db.Integer())
    sheet_id: int = db.Column(db.Integer(), default=0)
    tow_date_dt = db.Column(db.DATETIME)
    tow: int = db.Column(db.Integer())
    payer: str = db.Column(db.String())
    tug_id: str = db.Column(db.String())
    glider_id: str = db.Column(db.String())
    tug_to_str: str = db.Column(db.String())
    tug_ld_str: str = db.Column(db.String())
    gld_ld_str: str = db.Column(db.String())
    billed_ht: int = db.Column(db.Integer())
    t_flt_time: int = db.Column(db.Integer())
    g_flt_time: int = db.Column(db.Integer())
    heavy: bool = db.Column(db.Boolean(), default=True)
    tow_cost: float = db.Column(db.Float())
    glider_cost: float = db.Column(db.Float())
    status: str = db.Column(db.String())
    written = db.Column(db.DATETIME)
    billed_date = db.Column(db.DATETIME)
    tug_flt_id: int = db.Column(db.Integer())
    gld_flt_id: int = db.Column(db.Integer())

    def __init__(self, sequence_num, sheet_id, tow_date_dt, tow, payer, tug_id, glider_id, tug_to_str,
                 tug_ld_str, gld_ld_str, billed_ht, t_flt_time, g_flt_time,
                 heavy, tow_cost, glider_cost, status, written, billed_date, tug_flt_id, gld_flt_id):
        self.sequence_num = sequence_num
        self.sheet_id = sheet_id
        self.tow_date_dt = tow_date_dt
        self.tow = tow
        self.payer = payer
        self.tug_id = tug_id
        self.glider_id = glider_id
        self.tug_to_str = tug_to_str
        self.tug_ld_str = tug_ld_str
        self.gld_ld_str = gld_ld_str
        self.billed_ht = billed_ht
        self.t_flt_time = t_flt_time
        self.g_flt_time = g_flt_time
        self.heavy = True
        self.tow_cost = tow_cost
        self.glider_cost = glider_cost
        self.status = status
        self.written = written
        self.billed_date = billed_date
        self.tug_flt_id = tug_flt_id
        self.gld_flt_id = gld_flt_id


class Ktrax(db.Model):
    __bind_key__ = 'db1'
    record_id: int = db.Column(db.Integer(), primary_key=True)
    seq_num: int = db.Column(db.Integer())
    flt_id = db.Column(db.String(10))
    fl_type: int = db.Column(db.Integer())
    glider: str = db.Column(db.String(10))
    pilot: str = db.Column(db.String(30))
    to_time = db.Column(db.DATETIME())
    ld_time = db.Column(db.DATETIME())
    height: str = db.Column(db.String(10))
    tow_ht: str = db.Column(db.String(10))

    def __init__(self, record_id, seq_num, flt_id, fl_type, glider,
                 pilot, to_time, ld_time, height, tow_ht):
        self.record_id = record_id
        self.seq_num = seq_num
        self.flt_id = flt_id
        self.fl_type = fl_type
        self.glider = glider
        self.pilot = pilot
        self.to_time = to_time
        self.ld_time = ld_time
        self.height = height
        self.tow_ht = tow_ht



class Ops_days(db.Model):

    id: int = db.Column(db.Integer(), primary_key=True)
    sheet_id: int = db.Column(db.Integer())
    flying_day: str = db.Column(db.String(12))
    tows: int = db.Column(db.Integer)
    all_flights: int = db.Column(db.Integer)

    def __init__(self, sheet_id, flying_day, tows, all_flights):
        self.sheet_id = sheet_id
        self.flying_day = flying_day
        self.tows = tows
        self.all_flights = all_flights
