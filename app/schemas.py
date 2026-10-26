import re
from datetime import datetime, date
from enum import Enum
from typing import Optional, Generic, TypeVar, Any, Dict, List
from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr

T = TypeVar("T")

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP"
}

class SexEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    DECLINE = "Decline to Answer"

def clean_phone(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    # Strip everything except digits
    digits = re.sub(r"\D", "", v)
    if digits.startswith("1") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Phone number must be a valid 10-digit U.S. number (e.g. 555-123-4567)")
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

def parse_and_validate_dob(v: str) -> str:
    if not v or not isinstance(v, str):
        raise ValueError("Date of birth is required")
    v = v.strip()
    
    parsed_date = None
    formats = ["%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y", "%B %d, %Y", "%b %d, %Y"]
    for fmt in formats:
        try:
            parsed_date = datetime.strptime(v, fmt).date()
            break
        except ValueError:
            pass

    if not parsed_date:
        # Try regex extraction for spoke dates like "05 14 1990"
        match = re.match(r"^(\d{1,2})[\s/-](\d{1,2})[\s/-](\d{4})$", v)
        if match:
            m, d, y = map(int, match.groups())
            try:
                parsed_date = date(y, m, d)
            except ValueError:
                pass

    if not parsed_date:
        raise ValueError("Date of birth must be a valid date in MM/DD/YYYY format")

    today = date.today()
    if parsed_date > today:
        raise ValueError("Date of birth cannot be in the future")
    if parsed_date.year < 1900:
        raise ValueError("Date of birth must be after year 1900")

    return parsed_date.strftime("%m/%d/%Y")

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, description="1-50 chars, alphabetic + hyphens/apostrophes")
    last_name: str = Field(..., min_length=1, max_length=50, description="1-50 chars, alphabetic + hyphens/apostrophes")
    date_of_birth: str = Field(..., description="Valid date, not in future, MM/DD/YYYY")
    sex: str = Field(..., description="Male, Female, Other, Decline to Answer")
    phone_number: str = Field(..., description="Valid U.S. 10-digit phone number")
    email: Optional[str] = Field(None, description="Valid email format")
    address_line_1: str = Field(..., min_length=1, max_length=255, description="Street address")
    address_line_2: Optional[str] = Field(None, max_length=255, description="Apt/Suite/Unit if applicable")
    city: str = Field(..., min_length=1, max_length=100, description="1-100 characters")
    state: str = Field(..., description="Valid 2-letter U.S. state abbreviation")
    zip_code: str = Field(..., description="5-digit or ZIP+4 U.S. format")
    insurance_provider: Optional[str] = Field(None, max_length=100)
    insurance_member_id: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[str] = Field("English", max_length=50)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None)

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[A-Za-z\s'-]{1,50}$", v):
            raise ValueError("Name must be 1-50 alphabetic characters, hyphens, or apostrophes")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: str) -> str:
        return parse_and_validate_dob(v)

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: str) -> str:
        v_clean = v.strip().title()
        valid = {
            "Male": "Male",
            "Female": "Female",
            "Other": "Other",
            "Decline To Answer": "Decline to Answer",
            "Decline": "Decline to Answer",
            "Declined": "Decline to Answer"
        }
        if v_clean not in valid:
            raise ValueError("Sex must be one of: Male, Female, Other, Decline to Answer")
        return valid[v_clean]

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        res = clean_phone(v)
        if not res:
            raise ValueError("Phone number is required")
        return res

    @field_validator("emergency_contact_phone")
    @classmethod
    def validate_emergency_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        return clean_phone(v)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if not v or not v.strip():
            return None
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if v_upper not in US_STATES:
            raise ValueError(f"State must be a valid 2-letter U.S. state abbreviation (e.g. CA, NY, FL)")
        return v_upper

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("Zip code must be 5 digits or ZIP+4 format (e.g. 12345 or 12345-6789)")
        return v

    @field_validator("insurance_member_id")
    @classmethod
    def validate_member_id(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]{1,50}$", v):
            raise ValueError("Insurance member ID must be alphanumeric")
        return v

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not re.match(r"^[A-Za-z\s'-]{1,50}$", v):
            raise ValueError("Name must be 1-50 alphabetic characters, hyphens, or apostrophes")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return parse_and_validate_dob(v)

    @field_validator("sex")
    @classmethod
    def validate_sex(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_clean = v.strip().title()
        valid = {
            "Male": "Male",
            "Female": "Female",
            "Other": "Other",
            "Decline To Answer": "Decline to Answer",
            "Decline": "Decline to Answer",
            "Declined": "Decline to Answer"
        }
        if v_clean not in valid:
            raise ValueError("Sex must be one of: Male, Female, Other, Decline to Answer")
        return valid[v_clean]

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        return clean_phone(v)

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None or not v.strip():
            return None
        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Invalid email format")
        return v

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v_upper = v.strip().upper()
        if v_upper not in US_STATES:
            raise ValueError("State must be a valid 2-letter U.S. state abbreviation")
        return v_upper

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("Zip code must be 5 digits or ZIP+4 format")
        return v

class PatientResponse(PatientBase):
    patient_id: str
    created_at: str
    updated_at: str
    deleted_at: Optional[str] = None

class EnvelopeResponse(BaseModel):
    data: Optional[Any] = None
    error: Optional[Any] = None

class AppointmentCreate(BaseModel):
    patient_id: str
    department: Optional[str] = "General Primary Care"
    appointment_date: str
    appointment_time: str
    notes: Optional[str] = None

class CallLogCreate(BaseModel):
    patient_id: Optional[str] = None
    vapi_call_id: Optional[str] = None
    caller_phone: Optional[str] = None
    status: Optional[str] = "completed"
    duration_seconds: Optional[int] = 0
    transcript: Optional[str] = None
    summary: Optional[str] = None
    recording_url: Optional[str] = None
