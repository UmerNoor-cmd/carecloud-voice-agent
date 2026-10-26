import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(String(10), nullable=False)  # MM/DD/YYYY
    sex = Column(String(25), nullable=False)  # Male, Female, Other, Decline to Answer
    phone_number = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state = Column(String(2), nullable=False)  # 2-letter uppercase
    zip_code = Column(String(10), nullable=False)
    insurance_provider = Column(String(100), nullable=True)
    insurance_member_id = Column(String(50), nullable=True)
    preferred_language = Column(String(50), default="English", nullable=True)
    emergency_contact_name = Column(String(100), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    calls = relationship("CallLog", back_populates="patient", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "patient_id": self.patient_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "date_of_birth": self.date_of_birth,
            "sex": self.sex,
            "phone_number": self.phone_number,
            "email": self.email,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "insurance_provider": self.insurance_provider,
            "insurance_member_id": self.insurance_member_id,
            "preferred_language": self.preferred_language or "English",
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }

class CallLog(Base):
    __tablename__ = "call_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="SET NULL"), nullable=True)
    vapi_call_id = Column(String(100), nullable=True, index=True)
    caller_phone = Column(String(20), nullable=True)
    status = Column(String(50), default="completed")
    duration_seconds = Column(Integer, default=0)
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    recording_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="calls")

    def to_dict(self):
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "vapi_call_id": self.vapi_call_id,
            "caller_phone": self.caller_phone,
            "status": self.status,
            "duration_seconds": self.duration_seconds,
            "transcript": self.transcript,
            "summary": self.summary,
            "recording_url": self.recording_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(String(36), primary_key=True, default=generate_uuid)
    patient_id = Column(String(36), ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    department = Column(String(100), default="General Primary Care")
    appointment_date = Column(String(20), nullable=False)  # MM/DD/YYYY or YYYY-MM-DD
    appointment_time = Column(String(20), nullable=False)  # e.g., "10:00 AM"
    status = Column(String(50), default="Scheduled")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    patient = relationship("Patient", back_populates="appointments")

    def to_dict(self):
        return {
            "appointment_id": self.appointment_id,
            "patient_id": self.patient_id,
            "department": self.department,
            "appointment_date": self.appointment_date,
            "appointment_time": self.appointment_time,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
