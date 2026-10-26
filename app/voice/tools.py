"""
Vapi Tool Definitions (Function Calling schemas) for CareCloud Patient Registration.
"""

VAPI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "check_existing_patient",
            "description": "Checks if a caller with this phone number is already registered in CareCloud. Must be invoked at the beginning of the call.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone_number": {
                        "type": "string",
                        "description": "The 10-digit U.S. phone number of the caller (e.g., '5551234567')."
                    }
                },
                "required": ["phone_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "register_patient",
            "description": "Persists a new patient record to the database after collecting all required fields and receiving explicit caller confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "first_name": {
                        "type": "string",
                        "description": "First name (1-50 chars, alphabetic, hyphens, apostrophes)."
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Last name (1-50 chars, alphabetic, hyphens, apostrophes)."
                    },
                    "date_of_birth": {
                        "type": "string",
                        "description": "Date of birth in MM/DD/YYYY format. Must not be in the future."
                    },
                    "sex": {
                        "type": "string",
                        "enum": ["Male", "Female", "Other", "Decline to Answer"],
                        "description": "Administrative sex of the patient."
                    },
                    "phone_number": {
                        "type": "string",
                        "description": "Valid 10-digit U.S. phone number."
                    },
                    "email": {
                        "type": "string",
                        "description": "Optional email address."
                    },
                    "address_line_1": {
                        "type": "string",
                        "description": "Street address line 1."
                    },
                    "address_line_2": {
                        "type": "string",
                        "description": "Optional apartment, suite, or unit number."
                    },
                    "city": {
                        "type": "string",
                        "description": "City name."
                    },
                    "state": {
                        "type": "string",
                        "description": "Valid 2-letter U.S. state abbreviation (e.g., 'CA', 'FL', 'NY')."
                    },
                    "zip_code": {
                        "type": "string",
                        "description": "5-digit zip code (e.g., '33101')."
                    },
                    "insurance_provider": {
                        "type": "string",
                        "description": "Optional health insurance company name."
                    },
                    "insurance_member_id": {
                        "type": "string",
                        "description": "Optional insurance member / subscriber ID."
                    },
                    "preferred_language": {
                        "type": "string",
                        "description": "Preferred spoken language (default: 'English')."
                    },
                    "emergency_contact_name": {
                        "type": "string",
                        "description": "Optional emergency contact full name."
                    },
                    "emergency_contact_phone": {
                        "type": "string",
                        "description": "Optional emergency contact 10-digit phone number."
                    }
                },
                "required": [
                    "first_name",
                    "last_name",
                    "date_of_birth",
                    "sex",
                    "phone_number",
                    "address_line_1",
                    "city",
                    "state",
                    "zip_code"
                ]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_patient",
            "description": "Updates demographic or contact fields for an existing patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "UUID of the patient to update."
                    },
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "date_of_birth": {"type": "string"},
                    "sex": {"type": "string"},
                    "phone_number": {"type": "string"},
                    "email": {"type": "string"},
                    "address_line_1": {"type": "string"},
                    "address_line_2": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "zip_code": {"type": "string"},
                    "insurance_provider": {"type": "string"},
                    "insurance_member_id": {"type": "string"},
                    "preferred_language": {"type": "string"},
                    "emergency_contact_name": {"type": "string"},
                    "emergency_contact_phone": {"type": "string"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "schedule_appointment",
            "description": "Schedules a primary care or specialist appointment for a registered patient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "string",
                        "description": "UUID of the registered patient."
                    },
                    "department": {
                        "type": "string",
                        "description": "Clinic department (e.g., 'General Primary Care', 'Cardiology', 'Pediatrics')."
                    },
                    "appointment_date": {
                        "type": "string",
                        "description": "Requested date for appointment (e.g., 'Tomorrow', 'Next Monday', '11/02/2026')."
                    },
                    "appointment_time": {
                        "type": "string",
                        "description": "Requested appointment time (e.g., '10:00 AM', '2:30 PM')."
                    },
                    "notes": {
                        "type": "string",
                        "description": "Any specific medical notes or intake reason."
                    }
                },
                "required": ["appointment_date", "appointment_time"]
            }
        }
    }
]
