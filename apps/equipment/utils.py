# apps/equipment/utils.py
from datetime import date as ddate, time as dtime

def norm_date_str(val):
    if not val:
        return None
    if isinstance(val, ddate):
        return val.isoformat()[:10]
    s = str(val)
    return s[:10]  # assume YYYY-MM-DD

def norm_time_str(val):
    if not val:
        return None
    if isinstance(val, dtime):
        return val.strftime("%H:%M:%S")
    s = str(val)
    if len(s) == 5:            # "HH:MM"
        return f"{s}:00"
    return s[:8]               # "HH:MM:SS"
