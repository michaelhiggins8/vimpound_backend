import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_dir))


from db import pool
from datetime import datetime, date
from zoneinfo import ZoneInfo

def next_occurrence_mmdd_in_tz(mmdd: str, tz_name: str):
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        # Default to America/Phoenix if timezone is invalid or unavailable
        tz = ZoneInfo("America/Phoenix")
    print("tz: ", tz)
    now = datetime.now(tz)
    year = now.year

    month, day = map(int, mmdd.split("/"))
    candidate = date(year, month, day)

    if candidate < now.date():
        candidate = date(year + 1, month, day)

    weekday = candidate.strftime("%A")
    return weekday

def check_date_open(params: dict) -> str:
    """
    Check if a lot is open on a given date.
    
    Args:
        params: Dictionary containing 'date' key with date string
        
    Returns:
        A formatted string indicating if the lot is open or closed on the given date
    """
    date_str = params.get("date")
    org_id = params.get("org_id")
    time_zone = params.get("time_zone") or "America/Phoenix"

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT hours FROM exception_dates WHERE org_id = %s AND date = %s
            """, (org_id, date_str))
            row = cur.fetchone()
            if row:
                hours = row[0]
                return f"On {date_str}, the lot is lot hours are: {hours}."
            else:
                with pool.connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("""
                            SELECT default_hours_of_operation FROM orgs WHERE id = %s
                        """, (org_id,))
                        row = cur.fetchone()
                        if row:
                            default_hours_of_operation = row[0]
                            weekday = next_occurrence_mmdd_in_tz(date_str, time_zone)
                            
                            # Extract the time for the specific weekday from default_hours_of_operation
                            weekday_time = None
                            for line in default_hours_of_operation.split('\n'):
                                line = line.strip()
                                if line.startswith(f'* {weekday}:'):
                                    # Extract everything after the colon
                                    weekday_time = line.split(':', 1)[1].strip()
                                    break
                            
                            if weekday_time:
                                return f"On {date_str}, the lot is open from {weekday_time}."
                            else:
                                return f"On {date_str}, the Nothing was found for the lot hours."





