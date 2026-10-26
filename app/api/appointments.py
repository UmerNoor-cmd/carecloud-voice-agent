from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import AppointmentCreate, EnvelopeResponse
from .. import crud

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.get("", response_model=EnvelopeResponse, status_code=status.HTTP_200_OK)
def list_appointments_endpoint(
    patient_id: Optional[str] = Query(None, description="Filter by patient_id UUID"),
    db: Session = Depends(get_db)
):
    appts = crud.list_appointments(db, patient_id=patient_id)
    return {
        "data": [a.to_dict() for a in appts],
        "error": None
    }

@router.post("", response_model=EnvelopeResponse, status_code=status.HTTP_201_CREATED)
def create_appointment_endpoint(appt_in: AppointmentCreate, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = crud.get_patient(db, patient_id=appt_in.patient_id)
    if not patient:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "data": None,
                "error": {
                    "code": "PATIENT_NOT_FOUND",
                    "message": f"Patient with ID '{appt_in.patient_id}' does not exist."
                }
            }
        )
    created = crud.create_appointment(db, appt_in=appt_in)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "data": created.to_dict(),
            "error": None
        }
    )
