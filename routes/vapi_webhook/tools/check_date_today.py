from datetime import datetime
from zoneinfo import ZoneInfo

def check_date_today(params: dict) -> str:
    """
    Check todays date.
    
    Args:
        params: None
        
    Returns:
        A formatted string showing todays date including the day of the week
    """
    time_zone = params.get("time_zone") or "America/Phoenix"
    try:
        tz = ZoneInfo(time_zone)
    except Exception:
        # Default to America/Phoenix if timezone is invalid or unavailable
        tz = ZoneInfo("America/Phoenix")
    print("tz: ", tz)
    today = datetime.now(tz).strftime("%m/%d/%Y")
    return f"Today's date is {today}. The day of the week is {datetime.now(tz).strftime('%A')}."  


