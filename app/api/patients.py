from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import PatientCreate, PatientUpdate, EnvelopeResponse
from .. import crud

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("", response_model=EnvelopeResponse, status_code=status.HTTP_200_OK)
def list_patients_endpoint(
    last_name: Optional[str] = Query(None, description="Filter by last name (case-insensitive substring)"),
    date_of_birth: Optional[str] = Query(None, description="Filter by date of birth (MM/DD/YYYY)"),
    phone_number: Optional[str] = Query(None, description="Filter by phone number"),
    include_deleted: bool = Query(False, description="Include soft-deleted records"),
    db: Session = Depends(get_db)
):
    """
    List all patients with optional search filters.
    """
    try:
        patients = crud.list_patients(
            db=db,
            last_name=last_name,
            date_of_birth=date_of_birth,
            phone_number=phone_number,
            include_deleted=include_deleted
        )
        return {
            "data": [p.to_dict() for p in patients],
            "error": None
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving patients: {str(exc)}"
        )

@router.get("/{patient_id}", response_model=EnvelopeResponse, status_code=status.HTTP_200_OK)
def get_patient_endpoint(patient_id: str, db: Session = Depends(get_db)):
    """
    Retrieve a single patient by patient_id (UUID).
    """
    patient = crud.get_patient(db, patient_id=patient_id)
    if not patient:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "data": None,
                "error": {
                    "code": "PATIENT_NOT_FOUND",
                    "message": f"Patient with ID '{patient_id}' not found."
                }
            }
        )
    return {
        "data": patient.to_dict(),
        "error": None
    }

@router.post("", response_model=EnvelopeResponse, status_code=status.HTTP_201_CREATED)
def create_patient_endpoint(patient_in: PatientCreate, db: Session = Depends(get_db)):
    """
    Create a new patient record with full server-side validation.
    """
    try:
        new_patient = crud.create_patient(db, patient_in=patient_in)
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "data": new_patient.to_dict(),
                "error": None
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create patient: {str(exc)}"
        )

@router.put("/{patient_id}", response_model=EnvelopeResponse, status_code=status.HTTP_200_OK)
def update_patient_endpoint(patient_id: str, patient_update: PatientUpdate, db: Session = Depends(get_db)):
    """
    Update an existing patient record. Partial updates are allowed.
    """
    updated_patient = crud.update_patient(db, patient_id=patient_id, patient_update=patient_update)
    if not updated_patient:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "data": None,
                "error": {
                    "code": "PATIENT_NOT_FOUND",
                    "message": f"Patient with ID '{patient_id}' not found or has been deleted."
                }
            }
        )
    return {
        "data": updated_patient.to_dict(),
        "error": None
    }

@router.delete("/{patient_id}", response_model=EnvelopeResponse, status_code=status.HTTP_200_OK)
def soft_delete_patient_endpoint(patient_id: str, db: Session = Depends(get_db)):
    """
    Soft-delete a patient record (sets deleted_at timestamp; does not hard-delete).
    """
    deleted = crud.soft_delete_patient(db, patient_id=patient_id)
    if not deleted:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "data": None,
                "error": {
                    "code": "PATIENT_NOT_FOUND",
                    "message": f"Patient with ID '{patient_id}' not found or already deleted."
                }
            }
        )
    return {
        "data": {
            "patient_id": deleted.patient_id,
            "deleted_at": deleted.deleted_at.isoformat() if deleted.deleted_at else None,
            "status": "soft_deleted"
        },
        "error": None
    }

@router.post("/{patient_id}/restore", response_model=EnvelopeResponse, status_code=status.HTTP_200_OK)
def restore_patient_endpoint(patient_id: str, db: Session = Depends(get_db)):
    """
    Restore a soft-deleted patient record.
    """
    restored = crud.restore_patient(db, patient_id=patient_id)
    if not restored:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "data": None,
                "error": {
                    "code": "PATIENT_NOT_FOUND",
                    "message": f"Patient with ID '{patient_id}' not found."
                }
            }
        )
    return {
        "data": restored.to_dict(),
        "error": None
    }
