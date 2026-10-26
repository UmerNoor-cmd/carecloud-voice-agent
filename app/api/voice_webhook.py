import json
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import PatientCreate, PatientUpdate, AppointmentCreate, CallLogCreate, clean_phone
from .. import crud

logger = logging.getLogger("carecloud.voice")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

router = APIRouter(prefix="/vapi", tags=["Vapi Voice Webhook"])

def handle_tool_call(tool_name: str, args: Dict[str, Any], db: Session, call_info: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"Executing tool: {tool_name} with args: {args}")

    if tool_name == "check_existing_patient":
        phone = args.get("phone_number", "")
        if not phone and call_info.get("customer", {}).get("number"):
            phone = call_info["customer"]["number"]

        patient = crud.find_patient_by_phone(db, phone_number=phone)
        if patient:
            logger.info(f"Existing patient found: {patient.first_name} {patient.last_name} ({patient.patient_id})")
            return {
                "found": True,
                "patient_id": patient.patient_id,
                "first_name": patient.first_name,
                "last_name": patient.last_name,
                "date_of_birth": patient.date_of_birth,
                "phone_number": patient.phone_number,
                "address": f"{patient.address_line_1}, {patient.city}, {patient.state} {patient.zip_code}",
                "message": f"Existing record found for {patient.first_name} {patient.last_name}. Ask them if they would like to update their information instead."
            }
        else:
            return {
                "found": False,
                "message": "No existing record found for this phone number. Proceed with new patient registration."
            }

    elif tool_name == "register_patient":
        try:
            # Map parameters
            patient_in = PatientCreate(
                first_name=args.get("first_name", ""),
                last_name=args.get("last_name", ""),
                date_of_birth=args.get("date_of_birth", ""),
                sex=args.get("sex", ""),
                phone_number=args.get("phone_number", "") or call_info.get("customer", {}).get("number", ""),
                email=args.get("email"),
                address_line_1=args.get("address_line_1", ""),
                address_line_2=args.get("address_line_2"),
                city=args.get("city", ""),
                state=args.get("state", ""),
                zip_code=args.get("zip_code", ""),
                insurance_provider=args.get("insurance_provider"),
                insurance_member_id=args.get("insurance_member_id"),
                preferred_language=args.get("preferred_language", "English"),
                emergency_contact_name=args.get("emergency_contact_name"),
                emergency_contact_phone=args.get("emergency_contact_phone"),
            )

            new_patient = crud.create_patient(db, patient_in=patient_in)
            logger.info(f"Successfully registered patient {new_patient.first_name} {new_patient.last_name} with ID: {new_patient.patient_id}")
            print(f"\n[PATIENT REGISTRATION OBSERVED] Data Payload:\n{json.dumps(new_patient.to_dict(), indent=2)}\n")

            return {
                "success": True,
                "patient_id": new_patient.patient_id,
                "first_name": new_patient.first_name,
                "message": f"Patient record for {new_patient.first_name} {new_patient.last_name} has been successfully saved to CareCloud. Confirm to the caller: 'You're all set, {new_patient.first_name}!' and offer to schedule a first appointment."
            }
        except Exception as e:
            logger.error(f"Validation or DB error during register_patient: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "guidance": f"The patient data could not be saved due to validation issue: {str(e)}. Please politely ask the caller to clarify or correct that specific piece of information."
            }

    elif tool_name == "update_patient":
        patient_id = args.get("patient_id")
        if not patient_id:
            # Try to resolve by phone number
            phone = args.get("phone_number") or call_info.get("customer", {}).get("number", "")
            if phone:
                p = crud.find_patient_by_phone(db, phone)
                if p:
                    patient_id = p.patient_id

        if not patient_id:
            return {"success": False, "error": "Patient ID or matching phone number not found to update."}

        try:
            update_data = {k: v for k, v in args.items() if k not in ["patient_id"] and v is not None}
            patient_update = PatientUpdate(**update_data)
            updated = crud.update_patient(db, patient_id=patient_id, patient_update=patient_update)
            if updated:
                logger.info(f"Updated patient {updated.first_name} {updated.last_name} ({patient_id})")
                return {
                    "success": True,
                    "patient_id": updated.patient_id,
                    "message": f"Patient information for {updated.first_name} {updated.last_name} has been successfully updated."
                }
            return {"success": False, "error": "Patient not found."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    elif tool_name == "schedule_appointment":
        patient_id = args.get("patient_id")
        if not patient_id:
            phone = call_info.get("customer", {}).get("number", "")
            if phone:
                p = crud.find_patient_by_phone(db, phone)
                if p:
                    patient_id = p.patient_id

        if not patient_id:
            return {"success": False, "error": "Cannot schedule appointment without a registered patient."}

        try:
            appt_in = AppointmentCreate(
                patient_id=patient_id,
                department=args.get("department", "General Primary Care"),
                appointment_date=args.get("appointment_date", "Tomorrow"),
                appointment_time=args.get("appointment_time", "10:00 AM"),
                notes=args.get("notes", "Scheduled via Voice Intake")
            )
            created_appt = crud.create_appointment(db, appt_in=appt_in)
            logger.info(f"Appointment booked for patient {patient_id}: {created_appt.appointment_date} at {created_appt.appointment_time}")
            return {
                "success": True,
                "appointment_id": created_appt.appointment_id,
                "date": created_appt.appointment_date,
                "time": created_appt.appointment_time,
                "message": f"Appointment scheduled for {created_appt.appointment_date} at {created_appt.appointment_time} in {created_appt.department}."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"error": f"Unknown tool: {tool_name}"}

@router.post("/webhook")
async def vapi_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Main webhook for Vapi: handles tool-calling, function-calling, and end-of-call reports.
    """
    payload = await request.json()
    message = payload.get("message", payload)
    msg_type = message.get("type", "")

    logger.info(f"Received Vapi webhook message type: {msg_type}")

    # 1. Modern OpenAI-compatible tool-calls
    if msg_type == "tool-calls":
        tool_calls = message.get("toolCalls", [])
        call_info = message.get("call", {})
        results = []

        for call in tool_calls:
            t_id = call.get("id")
            func = call.get("function", {})
            name = func.get("name")
            arguments = func.get("arguments", {})
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except Exception:
                    arguments = {}

            res_data = handle_tool_call(name, arguments, db, call_info)
            results.append({
                "toolCallId": t_id,
                "result": json.dumps(res_data)
            })

        return JSONResponse(content={"results": results})

    # 2. Legacy function-call
    elif msg_type == "function-call":
        func_call = message.get("functionCall", {})
        name = func_call.get("name")
        params = func_call.get("parameters", {})
        call_info = message.get("call", {})

        res_data = handle_tool_call(name, params, db, call_info)
        return JSONResponse(content={"result": json.dumps(res_data)})

    # 3. End-of-call report (Bonus: call recording & transcript storage)
    elif msg_type == "end-of-call-report":
        call_obj = message.get("call", {})
        call_id = call_obj.get("id")
        customer_phone = call_obj.get("customer", {}).get("number")
        transcript = message.get("transcript") or call_obj.get("transcript")
        summary = message.get("summary") or call_obj.get("analysis", {}).get("summary")
        recording_url = message.get("recordingUrl") or call_obj.get("recordingUrl")
        duration = message.get("durationSeconds") or call_obj.get("durationSeconds", 0)

        # Match patient if possible
        matched_patient = None
        if customer_phone:
            matched_patient = crud.find_patient_by_phone(db, customer_phone)

        call_record = crud.create_or_update_call_log(
            db,
            call_in=CallLogCreate(
                patient_id=matched_patient.patient_id if matched_patient else None,
                vapi_call_id=call_id,
                caller_phone=customer_phone,
                status="completed",
                duration_seconds=int(duration or 0),
                transcript=transcript,
                summary=summary,
                recording_url=recording_url
            )
        )
        logger.info(f"Saved end-of-call report {call_record.id} for caller {customer_phone}. Duration: {duration}s")
        print(f"\n[VOICE AGENT CALL COMPLETED]\nCaller: {customer_phone}\nDuration: {duration}s\nSummary: {summary}\nTranscript preview: {str(transcript)[:200]}...\n")

        return JSONResponse(content={"status": "ok"})

    # 4. Status updates or assistant-request
    elif msg_type == "status-update":
        return JSONResponse(content={"status": "ok"})

    return JSONResponse(content={"status": "received"})
