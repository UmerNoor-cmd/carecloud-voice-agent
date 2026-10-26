from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from .models import Patient, CallLog, Appointment
from .schemas import PatientCreate, PatientUpdate, AppointmentCreate, CallLogCreate, clean_phone, parse_and_validate_dob

def create_patient(db: Session, patient_in: PatientCreate) -> Patient:
    patient_data = patient_in.model_dump()
    db_patient = Patient(**patient_data)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

def get_patient(db: Session, patient_id: str, include_deleted: bool = False) -> Optional[Patient]:
    query = db.query(Patient).filter(Patient.patient_id == patient_id)
    if not include_deleted:
        query = query.filter(Patient.deleted_at == None)
    return query.first()

def find_patient_by_phone(db: Session, phone_number: str) -> Optional[Patient]:
    try:
        cleaned = clean_phone(phone_number)
    except Exception:
        cleaned = phone_number
    return db.query(Patient).filter(
        Patient.phone_number == cleaned,
        Patient.deleted_at == None
    ).order_by(Patient.created_at.desc()).first()

def list_patients(
    db: Session,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 100
) -> List[Patient]:
    query = db.query(Patient)
    if not include_deleted:
        query = query.filter(Patient.deleted_at == None)

    if last_name:
        query = query.filter(Patient.last_name.ilike(f"%{last_name.strip()}%"))
    if date_of_birth:
        try:
            formatted_dob = parse_and_validate_dob(date_of_birth)
            query = query.filter(Patient.date_of_birth == formatted_dob)
        except Exception:
            query = query.filter(Patient.date_of_birth.ilike(f"%{date_of_birth.strip()}%"))
    if phone_number:
        try:
            cleaned_phone = clean_phone(phone_number)
            query = query.filter(Patient.phone_number == cleaned_phone)
        except Exception:
            query = query.filter(Patient.phone_number.ilike(f"%{phone_number.strip()}%"))

    return query.order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()

def update_patient(db: Session, patient_id: str, patient_update: PatientUpdate) -> Optional[Patient]:
    db_patient = get_patient(db, patient_id, include_deleted=False)
    if not db_patient:
        return None

    update_data = patient_update.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(db_patient, field, val)

    db_patient.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_patient)
    return db_patient

def soft_delete_patient(db: Session, patient_id: str) -> Optional[Patient]:
    db_patient = get_patient(db, patient_id, include_deleted=False)
    if not db_patient:
        return None

    db_patient.deleted_at = datetime.utcnow()
    db.commit()
    db.refresh(db_patient)
    return db_patient

def restore_patient(db: Session, patient_id: str) -> Optional[Patient]:
    db_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not db_patient:
        return None
    db_patient.deleted_at = None
    db_patient.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_patient)
    return db_patient

# Appointment CRUD
def create_appointment(db: Session, appt_in: AppointmentCreate) -> Appointment:
    db_appt = Appointment(**appt_in.model_dump())
    db.add(db_appt)
    db.commit()
    db.refresh(db_appt)
    return db_appt

def list_appointments(db: Session, patient_id: Optional[str] = None) -> List[Appointment]:
    query = db.query(Appointment)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    return query.order_by(Appointment.created_at.desc()).all()

# Call Log CRUD
def create_or_update_call_log(db: Session, call_in: CallLogCreate) -> CallLog:
    if call_in.vapi_call_id:
        existing = db.query(CallLog).filter(CallLog.vapi_call_id == call_in.vapi_call_id).first()
        if existing:
            for field, val in call_in.model_dump(exclude_unset=True).items():
                if val is not None:
                    setattr(existing, field, val)
            db.commit()
            db.refresh(existing)
            return existing

    db_call = CallLog(**call_in.model_dump())
    db.add(db_call)
    db.commit()
    db.refresh(db_call)
    return db_call

def list_call_logs(db: Session, patient_id: Optional[str] = None) -> List[CallLog]:
    query = db.query(CallLog)
    if patient_id:
        query = query.filter(CallLog.patient_id == patient_id)
    return query.order_by(CallLog.created_at.desc()).all()
