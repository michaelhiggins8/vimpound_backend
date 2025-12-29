from fastapi import APIRouter, Request
import json
from db import pool
from dotenv import load_dotenv
import os
from .tools.check_date_open import check_date_open
from .tools.check_vehicle import check_vehicle
from .tools.check_date_today import check_date_today
from .end_of_call_report import handle_end_of_call_report

load_dotenv()

router = APIRouter()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")

def handle_assistant_request(msg: dict) -> dict:
    """
    Handle assistant-request message type.
    Returns assistant configuration with variable values.
    """
    call = msg.get("call", {})
    phone_number_id = call.get("phoneNumberId")
    #print("PHONE NUMBER ID:", phone_number_id)

    to_header = (
        call
        .get("phoneCallProviderDetails", {})
        .get("sip", {})
        .get("headers", {})
        .get("to")
    )

    lot_phone_number = None
    if to_header and "sip:" in to_header:
        lot_phone_number = to_header.split("sip:")[1].split("@")[0]
    print("+++++++++LOT PHONE NUMBER+++++++++++++++:", lot_phone_number)
    #print("LOT PHONE NUMBER:", lot_phone_number)    
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    id,
                    created_at,
                    default_hours_of_operation,
                    agent_name,
                    company_name,
                    documents_needed,
                    cost_to_release_short,
                    cost_to_release_long,
                    phone_number,
                    default_address,
                    time_zone
                FROM orgs 
                WHERE phone_number = %s 
                LIMIT 1
            """, (lot_phone_number,))
            
            row = cur.fetchone()
            if row:
                # Get column names from cursor description
                column_names = [desc[0] for desc in cur.description]
                # Create dictionary mapping column names to values
                lot = dict(zip(column_names, row))
            else:
                lot = None
            #print("LOT:", lot)





    # TODO later: look up real lot info from your DB using phone_number_id
    lot_name = "Sunrise Towing"
    hours = "8am-6pm"
    rules = "Bring ID and proof of ownership"

    return {
        "assistantId": ASSISTANT_ID,
        "assistantOverrides": {
            "variableValues": {
                "agent_name": lot["agent_name"],
                "company_name": lot["company_name"],
                "default_hours_of_operation": lot["default_hours_of_operation"],
                "documents_needed":lot["documents_needed"],
                "cost_to_release_short":lot["cost_to_release_short"],
                "org_id":lot["id"],
                "default_address":lot["default_address"],
                "time_zone":lot["time_zone"]
            }
        }
    }








def handle_tool_calls(msg: dict) -> dict:
    """
    Handle tool-calls message type.
    Expects msg["toolCallList"] with items:
      { "id": "...", "name": "...", "function": { "arguments": { ... } } }

    Must return:
      { "results": [ { "toolCallId", "result" }, ... ] }
    """

    print("msg: ", msg)
    print("--------------------------------")
    print("--------------------------------")
    tool_calls = msg.get("toolCallList", []) or []
    results: list[dict] = []

    for tool_call in tool_calls:
        fn = tool_call.get("function", {}) or {}

        tool_name = fn.get("name")
        tool_call_id = tool_call.get("id")

        # Arguments can be a dict or a JSON string
        params = fn.get("arguments", {}) or {}
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except Exception:
                params = {}

        # Default text result if something goes wrong
        result_text = "Tool ran but did not return any details."

        match tool_name:
            case "check_date_open":
                result_text = check_date_open(params)
            case "check_vehicle":
                result_text = check_vehicle(params)
            case "check_date_today":
                result_text = check_date_today(params)

            case _:
                result_text = f"Unknown tool: {tool_name}"

        # 🔴 IMPORTANT: append *inside* the loop and only what Vapi expects
        #result_text = "DEBUG_TEST: I found a grey 2013 Toyota Prius with plate VHAOW2."
        print("tool_call_id: ", tool_call_id)
        results.append(
            {
                "toolCallId": tool_call_id,
                "result": result_text,
            }
        )

    print("results: ", results)
    return {"results": results}



@router.post("/vapi")
async def vapi_handler(request: Request):
    # 1) Read raw body safely
    raw_body = await request.body()
    #print("RAW BODY:", raw_body)

    # 2) Try to parse JSON, but don't crash if it's bad
    try:
        body = json.loads(raw_body) if raw_body else {}
    except json.JSONDecodeError:
        #print("JSON DECODE FAILED")
        # return 200 with empty JSON so Vapi doesn't get a 500
        return {}

    # 3) Get the message and its type
    msg = body.get("message", {})
    msg_type = msg.get("type")
    #print("EVENT TYPE:", msg_type)

    # 4) Switch statement - route message type to appropriate handler
    match msg_type:

        
        case "assistant-request":
            return handle_assistant_request(msg)
        case "tool-calls":
            return handle_tool_calls(msg)
        case "end-of-call-report":
            return await handle_end_of_call_report(msg)



        # Add more cases here for other message types if needed
        # case "status-update":
        #     return handle_status_update(msg)
        case _:
            # Default case: For all other event types, return empty JSON
            return {}
