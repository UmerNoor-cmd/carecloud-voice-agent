import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# In-memory test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_patients.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_patient_success():
    payload = {
        "first_name": "Eleanor",
        "last_name": "Vance",
        "date_of_birth": "03/15/1988",
        "sex": "Female",
        "phone_number": "555-321-7654",
        "email": "eleanor.vance@example.com",
        "address_line_1": "450 Hilltop Rd",
        "city": "Boston",
        "state": "MA",
        "zip_code": "02108",
        "insurance_provider": "Cigna",
        "insurance_member_id": "CIG-12345",
        "preferred_language": "English"
    }
    response = client.post("/patients", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["error"] is None
    data = body["data"]
    assert data["first_name"] == "Eleanor"
    assert data["last_name"] == "Vance"
    assert data["patient_id"] is not None
    assert data["phone_number"] == "555-321-7654"
    assert data["deleted_at"] is None

def test_create_patient_validation_errors():
    # 1. 3-digit phone number
    res1 = client.post("/patients", json={
        "first_name": "Bad", "last_name": "Phone", "date_of_birth": "01/01/1990",
        "sex": "Male", "phone_number": "123", "address_line_1": "123 St",
        "city": "Miami", "state": "FL", "zip_code": "33101"
    })
    assert res1.status_code == 422
    assert res1.json()["error"]["code"] == "VALIDATION_ERROR"

    # 2. Future date of birth
    res2 = client.post("/patients", json={
        "first_name": "Time", "last_name": "Traveler", "date_of_birth": "01/01/2099",
        "sex": "Male", "phone_number": "555-123-4567", "address_line_1": "123 St",
        "city": "Miami", "state": "FL", "zip_code": "33101"
    })
    assert res2.status_code == 422

    # 3. Invalid state abbreviation
    res3 = client.post("/patients", json={
        "first_name": "John", "last_name": "Smith", "date_of_birth": "01/01/1990",
        "sex": "Male", "phone_number": "555-123-4567", "address_line_1": "123 St",
        "city": "Miami", "state": "ZZ", "zip_code": "33101"
    })
    assert res3.status_code == 422

    # 4. Invalid zip code
    res4 = client.post("/patients", json={
        "first_name": "John", "last_name": "Smith", "date_of_birth": "01/01/1990",
        "sex": "Male", "phone_number": "555-123-4567", "address_line_1": "123 St",
        "city": "Miami", "state": "FL", "zip_code": "abc"
    })
    assert res4.status_code == 422

def test_list_and_filter_patients():
    client.post("/patients", json={
        "first_name": "Alice", "last_name": "Wonderland", "date_of_birth": "04/10/1995",
        "sex": "Female", "phone_number": "555-111-2222", "address_line_1": "Rabbit Hole",
        "city": "Orlando", "state": "FL", "zip_code": "32801"
    })
    client.post("/patients", json={
        "first_name": "Bob", "last_name": "Builder", "date_of_birth": "07/20/1980",
        "sex": "Male", "phone_number": "555-333-4444", "address_line_1": "Construction Rd",
        "city": "Tampa", "state": "FL", "zip_code": "33602"
    })

    # Filter by last_name
    res_name = client.get("/patients?last_name=Wonderland")
    assert res_name.status_code == 200
    assert len(res_name.json()["data"]) == 1
    assert res_name.json()["data"][0]["first_name"] == "Alice"

    # Filter by phone_number
    res_phone = client.get("/patients?phone_number=555-333-4444")
    assert res_phone.status_code == 200
    assert len(res_phone.json()["data"]) == 1
    assert res_phone.json()["data"][0]["first_name"] == "Bob"

def test_get_and_put_patient():
    create_res = client.post("/patients", json={
        "first_name": "Gregory", "last_name": "House", "date_of_birth": "06/11/1959",
        "sex": "Male", "phone_number": "555-999-8888", "address_line_1": "1 Diagnostic Way",
        "city": "Princeton", "state": "NJ", "zip_code": "08540"
    })
    p_id = create_res.json()["data"]["patient_id"]

    # GET /patients/:id
    get_res = client.get(f"/patients/{p_id}")
    assert get_res.status_code == 200
    assert get_res.json()["data"]["first_name"] == "Gregory"

    # PUT /patients/:id (Partial update)
    put_res = client.put(f"/patients/{p_id}", json={
        "phone_number": "555-777-6666",
        "insurance_provider": "Princeton Plainsboro Health"
    })
    assert put_res.status_code == 200
    assert put_res.json()["data"]["phone_number"] == "555-777-6666"
    assert put_res.json()["data"]["insurance_provider"] == "Princeton Plainsboro Health"

def test_soft_delete_and_restore():
    create_res = client.post("/patients", json={
        "first_name": "Arthur", "last_name": "Dent", "date_of_birth": "03/11/1978",
        "sex": "Male", "phone_number": "555-424-2424", "address_line_1": "Cottington Rd",
        "city": "Austin", "state": "TX", "zip_code": "78701"
    })
    p_id = create_res.json()["data"]["patient_id"]

    # Soft delete
    del_res = client.delete(f"/patients/{p_id}")
    assert del_res.status_code == 200
    assert del_res.json()["data"]["status"] == "soft_deleted"

    # GET /patients/:id should now return 404
    get_res = client.get(f"/patients/{p_id}")
    assert get_res.status_code == 404

    # Default list excludes soft-deleted
    list_res = client.get("/patients")
    assert not any(p["patient_id"] == p_id for p in list_res.json()["data"])

    # List with include_deleted=true includes it
    list_inc = client.get("/patients?include_deleted=true")
    assert any(p["patient_id"] == p_id for p in list_inc.json()["data"])

    # Restore
    rest_res = client.post(f"/patients/{p_id}/restore")
    assert rest_res.status_code == 200
    assert rest_res.json()["data"]["deleted_at"] is None

def test_vapi_duplicate_detection_tool():
    # Register Jane
    client.post("/patients", json={
        "first_name": "Jane", "last_name": "Doe", "date_of_birth": "05/14/1990",
        "sex": "Female", "phone_number": "555-234-5678", "address_line_1": "123 Ocean Dr",
        "city": "Miami", "state": "FL", "zip_code": "33139"
    })

    # Call tool webhook
    res = client.post("/vapi/webhook", json={
        "message": {
            "type": "tool-calls",
            "toolCalls": [{
                "id": "tool_call_dup",
                "type": "function",
                "function": {
                    "name": "check_existing_patient",
                    "arguments": { "phone_number": "555-234-5678" }
                }
            }]
        }
    })
    assert res.status_code == 200
    res_data = res.json()["results"][0]
    import json
    parsed = json.loads(res_data["result"])
    assert parsed["found"] is True
    assert parsed["first_name"] == "Jane"
    assert "Existing record found" in parsed["message"]
