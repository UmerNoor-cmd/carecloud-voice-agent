import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, SessionLocal, Base
from app.models import Patient
from app.schemas import PatientCreate
from app import crud

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing_count = db.query(Patient).count()
    if existing_count > 0:
        print(f"Database already has {existing_count} patient(s). Skipping seed.")
        db.close()
        return

    seed_patients = [
        PatientCreate(
            first_name="Jane",
            last_name="Doe",
            date_of_birth="05/14/1990",
            sex="Female",
            phone_number="555-234-5678",
            email="jane.doe@example.com",
            address_line_1="123 Ocean Drive",
            address_line_2="Apt 4B",
            city="Miami",
            state="FL",
            zip_code="33139",
            insurance_provider="Blue Cross Blue Shield",
            insurance_member_id="BCBS-987654321",
            preferred_language="English",
            emergency_contact_name="John Doe",
            emergency_contact_phone="555-987-6543"
        ),
        PatientCreate(
            first_name="Carlos",
            last_name="Rodriguez",
            date_of_birth="11/23/1984",
            sex="Male",
            phone_number="555-876-5432",
            email="carlos.rodriguez@example.com",
            address_line_1="742 Evergreen Terrace",
            city="Orlando",
            state="FL",
            zip_code="32801",
            insurance_provider="Aetna",
            insurance_member_id="AET-44556677",
            preferred_language="Spanish",
            emergency_contact_name="Maria Rodriguez",
            emergency_contact_phone="555-345-6789"
        )
    ]

    for p in seed_patients:
        created = crud.create_patient(db, p)
        print(f"✓ Seeded patient: {created.first_name} {created.last_name} (ID: {created.patient_id}, Phone: {created.phone_number})")

    db.close()
    print("Database seeding completed.")

if __name__ == "__main__":
    seed()
