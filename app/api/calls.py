from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import EnvelopeResponse
from .. import crud

router = APIRouter(prefix="/calls", tags=["Calls & Transcripts"])

@router.get("", response_model=EnvelopeResponse, status_code=status.HTTP_200_OK)
def list_calls_endpoint(
    patient_id: Optional[str] = Query(None, description="Filter call logs by patient_id"),
    db: Session = Depends(get_db)
):
    calls = crud.list_call_logs(db, patient_id=patient_id)
    return {
        "data": [c.to_dict() for c in calls],
        "error": None
    }
