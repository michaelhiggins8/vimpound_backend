from db import pool


def do_vehicle_check(org_id, vin_number, plate_number):
    """
    Do a vehicle check for the given org_id, vin_number, and plate_number.
    Queries the vehicles table to find a matching vehicle record.
    """
    try:
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        status,
                        make,
                        model,
                        year,
                        color,
                        vin_number,
                        plate_number,
                        owner_first_name,
                        owner_last_name,
                        location
                    FROM vehicles
                    WHERE org_id = %s
                    AND (vin_number = %s OR plate_number = %s)
                    LIMIT 1
                """, (org_id, vin_number, plate_number))

                row = cur.fetchone()
               
                if row:
                    print("row: ", row)
                    print("--------------------------------")
                    print("--------------------------------")
                    # Get column names from cursor description
                    column_names = [desc[0] for desc in cur.description]
                    # Create dictionary mapping column names to values
                    vehicle = dict(zip(column_names, row))
                    print("vehicle: ", vehicle)
                    print("--------------------------------")
                    print("--------------------------------")
                    return {
                        "status": "found",
                        "vehicle": vehicle
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": "No vehicle found matching the provided criteria"
                    }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Database error: {str(e)}"
        }


def check_vehicle(params: dict) -> str:
    """
    Check if a vehicle exists in the lot based on org_id, vin_number, and plate_number.
    
    Args:
        params: Dictionary containing 'org_id', 'vin_number', and 'plate_number' keys
        
    Returns:
        A formatted string indicating the vehicle status and details if found
    """
    org_id = params.get("org_id")
    vin_number = params.get("vin_number")
    plate_number = params.get("plate_number")
    print("org_id: ", org_id)
    print("vin_number: ", vin_number)
    print("plate_number: ", plate_number)
    print("--------------------------------")
    print("--------------------------------")

    tool_result = do_vehicle_check(org_id, vin_number, plate_number)
    print("tool_result: ", tool_result)
    print("--------------------------------")
    print("--------------------------------")

    status = tool_result.get("status")
    if status == "found":
        v = tool_result.get("vehicle", {})
        # Build a single, readable sentence for the LLM
        result_text = (
            "I found the vehicle in the lot. "
            f"It is a {v.get('color', 'unknown color')} "
            f"{v.get('year', 'unknown year')} "
            f"{v.get('make', 'unknown make')} "
            f"{v.get('model', 'unknown model')} "
            f"with plate {v.get('plate_number', 'unknown plate')}. "
            f"The VIN number is {v.get('vin_number', 'unknown VIN')}. "
            f"The status is {v.get('status', 'unknown')}, "
            f"and the recorded location is {v.get('location', 'unknown location')}."
        )
    elif status == "not_found":
        result_text = tool_result.get(
            "message",
            "No vehicle was found matching the provided information."
        )
    else:
        # error or unexpected
        result_text = tool_result.get(
            "message",
            "There was an error checking the vehicle."
        )
    
    return result_text

