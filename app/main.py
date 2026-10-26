import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .database import engine, Base, SessionLocal
from .models import Patient
from .schemas import PatientCreate
from . import crud
from .api.patients import router as patients_router
from .api.appointments import router as appointments_router
from .api.calls import router as calls_router
from .api.voice_webhook import router as vapi_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("carecloud.main")

# Initialize database tables
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Seed database if empty
    db = SessionLocal()
    try:
        count = db.query(Patient).count()
        if count == 0:
            logger.info("Database is empty. Inserting seed demo patient records...")
            seed_data = [
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
            for p in seed_data:
                crud.create_patient(db, p)
            logger.info("Successfully seeded 2 demonstration patients.")
    finally:
        db.close()
    yield

app = FastAPI(
    title="CareCloud Voice AI Agent & Patient Intake API",
    description="A voice-driven patient registration system integrating Telephony (Vapi), LLMs, SQLite Persistence, and REST APIs.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Standardized Error Envelopes ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join([str(l) for l in err.get("loc", []) if l != "body"])
        errors.append({
            "field": loc,
            "message": err.get("msg", "Invalid value"),
            "type": err.get("type", "value_error")
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "data": None,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Input validation failed. Please check the provided patient fields.",
                "details": errors
            }
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "data": None,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail)
            }
        }
    )

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Server Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred."
            }
        }
    )

# Include API Routers
app.include_router(patients_router)
app.include_router(appointments_router)
app.include_router(calls_router)
app.include_router(vapi_router)
app.include_router(vapi_router, prefix="/api")

# Health Check Endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "CareCloud Voice AI Intake",
        "database": "connected"
    }

# Static files & Dashboard Root
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", tags=["Dashboard"])
def serve_dashboard():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "CareCloud Voice Agent API is running. Access /docs for Swagger."}
