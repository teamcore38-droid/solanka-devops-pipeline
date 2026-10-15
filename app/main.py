from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timezone
import os

app = FastAPI(
    title="Solanka Digital Tourism API",
    description=(
        "Core backend service for Solanka Digital Tourism (Pvt) Ltd. "
        "Adheres to ISO 9001 (QMS) and ISO/IEC 27001 (ISMS) standards."
    ),
    version="1.0.0"
)

# Simulated in-memory database for Solanka tours and bookings
DESTINATIONS_DB = [
    {
        "id": 1,
        "name": "Sigiriya Ancient Rock Fortress",
        "region": "Central Province",
        "category": "Cultural Heritage",
        "price_usd": 36.0,
        "availability": True
    },
    {
        "id": 2,
        "name": "Ella Nine Arches Bridge & Little Adam's Peak",
        "region": "Uva Province",
        "category": "Nature & Adventure",
        "price_usd": 25.0,
        "availability": True
    },
    {
        "id": 3,
        "name": "Galle Dutch Fort Walking Tour",
        "region": "Southern Province",
        "category": "Historical",
        "price_usd": 20.0,
        "availability": True
    },
    {
        "id": 4,
        "name": "Yala National Park Safari",
        "region": "Southern Province",
        "category": "Wildlife",
        "price_usd": 65.0,
        "availability": True
    },
    {
        "id": 5,
        "name": "Temple of the Sacred Tooth Relic - Kandy",
        "region": "Central Province",
        "category": "Religious & Cultural",
        "price_usd": 15.0,
        "availability": True
    }
]

BOOKINGS_DB = []


# Schemas
class BookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=2, max_length=100)
    customer_email: EmailStr
    destination_id: int
    num_passengers: int = Field(..., ge=1, le=20)
    travel_date: str = Field(..., description="Format: YYYY-MM-DD")


class BookingResponse(BaseModel):
    booking_id: str
    customer_name: str
    destination_name: str
    num_passengers: int
    total_cost_usd: float
    travel_date: str
    status: str
    created_at: str


@app.get("/", tags=["General"])
def read_root():
    """Service status and organizational metadata."""
    return {
        "service": "Solanka Digital Tourism Platform API",
        "organization": "Solanka Digital Tourism (Pvt) Ltd",
        "environment": os.getenv("APP_ENV", "production"),
        "version": "1.0.0",
        "compliance": ["ISO 9001:2015", "ISO/IEC 27001:2022", "ISO/IEC 20000-1:2018"],
        "status": "OPERATIONAL"
    }


@app.get("/health", tags=["Monitoring"])
def health_check():
    """Health check endpoint used by Jenkins, Docker, and Ansible for deployment validation."""
    return {
        "status": "UP",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "CONNECTED",
        "version": "1.0.0"
    }


@app.get("/api/v1/destinations", tags=["Destinations"])
def list_destinations():
    """Retrieve catalog of available Sri Lankan tourist packages."""
    return {
        "total": len(DESTINATIONS_DB),
        "destinations": DESTINATIONS_DB
    }


@app.get("/api/v1/destinations/{dest_id}", tags=["Destinations"])
def get_destination(dest_id: int):
    """Retrieve a single destination by ID."""
    for item in DESTINATIONS_DB:
        if item["id"] == dest_id:
            return item
    raise HTTPException(status_code=404, detail="Destination not found")


@app.post("/api/v1/bookings", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, tags=["Bookings"])
def create_booking(booking: BookingRequest):
    """Create a new booking for a traveler."""
    destination = next((d for d in DESTINATIONS_DB if d["id"] == booking.destination_id), None)
    if not destination:
        raise HTTPException(status_code=400, detail="Invalid destination ID")

    total_cost = destination["price_usd"] * booking.num_passengers
    booking_id = f"SLK-{len(BOOKINGS_DB) + 1001}"

    record = {
        "booking_id": booking_id,
        "customer_name": booking.customer_name,
        "customer_email": booking.customer_email,
        "destination_name": destination["name"],
        "num_passengers": booking.num_passengers,
        "total_cost_usd": total_cost,
        "travel_date": booking.travel_date,
        "status": "CONFIRMED",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    BOOKINGS_DB.append(record)
    return record


@app.get("/api/v1/bookings", tags=["Bookings"])
def list_bookings():
    """List all created bookings."""
    return {
        "total": len(BOOKINGS_DB),
        "bookings": BOOKINGS_DB
    }
