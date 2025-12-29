from datetime import datetime
import asyncio
import os
import re
from autumn import Autumn
from dotenv import load_dotenv
from db import pool
load_dotenv()



client = Autumn(
    token=os.environ.get("AUTUMN_SECRET_KEY"), 
)
AUTUMN_FEATURE_ID = os.getenv("AUTUMN_FEATURE_ID")

def _parse_iso_timestamp(ts: str | None):
    """
    Helper to parse ISO 8601 timestamps from the Call object.
    Vapi uses strings like '2024-01-15T09:30:00Z'.
    """
    if not ts:
        return None
    try:
        # Handle trailing 'Z' (UTC)
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except Exception as e:
        #print("Failed to parse timestamp:", ts, "ERROR:", e)
        return None


async def handle_end_of_call_report(msg: dict) -> dict:
    """
    Handle end-of-call-report message type.
    Prints how long the call lasted (for billing).
    """
    call = msg.get("call", {}) or {}
   
    # Extract phone number from call object
    phone_number = None
    try:
        # Try to get from SIP headers (for inbound calls)
        sip_details = call.get("phoneCallProviderDetails", {}).get("sip", {})
        to_header = sip_details.get("headers", {}).get("to", "")
        if to_header:
            # Parse SIP URI format: <sip:+17605281256@...>
            match = re.search(r'<sip:([^@]+)', to_header)
            if match:
                phone_number = match.group(1)
    except Exception:
        pass
    
    # Fallback: try customer number if available
    if not phone_number:
        phone_number = call.get("customer", {}).get("number")



    # customer_id from phone number
    customer_id = None
    if phone_number:
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT profiles.id
                        FROM profiles
                        INNER JOIN orgs ON profiles.org_id = orgs.id
                        WHERE orgs.phone_number = %s
                        LIMIT 1
                    """, (phone_number,))
                    
                    row = cur.fetchone()
                    if row:
                        customer_id = str(row[0])
        except Exception as e:
            print(f"Error fetching customer_id from phone_number: {e}")

    # Call id (same as before)
    call_id = call.get("id") or call.get("callId")

    # ✅ Use top-level startedAt / endedAt from the message
    started_at_raw = msg.get("startedAt") or call.get("startedAt") or call.get("createdAt")
    ended_at_raw   = msg.get("endedAt")   or call.get("endedAt")   or call.get("updatedAt")

    started_at = _parse_iso_timestamp(started_at_raw)
    ended_at = _parse_iso_timestamp(ended_at_raw)

    #print("raw startedAt:", started_at_raw)
    #print("raw endedAt:", ended_at_raw)
    #print("parsed started_at:", started_at)
    #print("parsed ended_at:", ended_at)

    if started_at and ended_at:
        duration_minutes = (ended_at - started_at).total_seconds() / 60
        
        response = await client.track(
            customer_id=customer_id,
            feature_id = AUTUMN_FEATURE_ID,   
            value = duration_minutes

        )
        
    else:
        #print(
            "Could not compute call duration. "
            f"call_id={call_id}, startedAt={started_at_raw}, endedAt={ended_at_raw}"
        #)

    return {}

