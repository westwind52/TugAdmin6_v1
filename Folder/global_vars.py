from __future__ import annotations

from typing import List
from datetime import datetime

active_date = None
ops_date_str: str | None = None  # string yyyy-mm-dd
ops_date_dt: datetime | None = None
start = None
tow_base_rate: float = 25
height_fee_heavy_per100: float = 2.25
height_fee_light_per100: float = 2.25
STARTING: bool = True
sheet_number: int = 0
acft: dict[str, str] = {}
pilot_initials: set = set()
pilot_dict: dict[str, str] = {}
known_pilots: set[str] = set()
known_aircraft: set[str] = set()
tugs: List[str] = ['PXI', 'KKZ', 'TNE', 'ALD']
club: dict[str, float] = {'UIU': 0.9, 'GJH': 0.7}
bulk_bill: List[str] = ['GJ', 'BW', 'NJ', 'GN']
self_launch: List[str] = ['FFO', 'GXM', 'GDE', 'FFO', 'UOW']
last_invoice: dict = {"LAST_INVOICE": 999}
overwrite: bool = False
