from fastapi import APIRouter, Depends, UploadFile, File, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from database import get_db
from schemas import schemas
from services import flight_service
from api.v1.auth import get_current_user
from models import models

router = APIRouter()

@router.post("/", response_model=schemas.AddFlightResponse)
def add_flight(
    flight: schemas.FlightCreate, 
    db: Session = Depends(get_db), 
    current_user: models.User = Depends(get_current_user)
):
    """
    Adds a flight to airline schedule.
    Authentication required.
    """
    return flight_service.add_flight(db, flight)

@router.post("/upload")
async def add_flight_by_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Adds flights by CSV file. 
    Authentication required.
    """
    return await flight_service.add_flights_from_csv(db, file)

@router.get("/", response_model=List[schemas.FlightResponse])
def query_flights(
    skip: int = Query(0, description="Pagination skip"),
    limit: int = Query(10, description="Pagination limit (max 10)"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    airport_from: Optional[str] = None,
    airport_to: Optional[str] = None,
    number_of_people: int = Query(1, description="Number of passengers"),
    is_round_trip: bool = Query(False, description="Is it a round trip"),
    db: Session = Depends(get_db)
):
    """
    Query available flights with pagination.
    Authentication NO. Rate Limit 3 per day is enforced by proxy.
    """
    if limit > 10:
        limit = 10
        
    if is_round_trip and (not date_from or not date_to):
        raise HTTPException(status_code=400, detail="Both date_from and date_to are required for Round Trip searches.")
        
    if not is_round_trip and date_to:
        raise HTTPException(status_code=400, detail="date_to (Return Date) cannot be provided for One-Way flight searches.")
        
    flights = flight_service.flight_repo.get_flights(
        db, skip=skip, limit=limit,
        date_from=date_from, date_to=date_to,
        airport_from=airport_from, airport_to=airport_to,
        number_of_people=number_of_people,
        is_round_trip=is_round_trip
    )
    return flights

@router.get("/{flight_number}/passengers", response_model=schemas.PassengerListResponse)
def query_flight_passenger_list(
    flight_number: str,
    date: datetime = Query(..., description="Flight date"),
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get passenger list for a specific flight.
    Authentication required. Pagination supported.
    """
    from services import ticket_service
    if limit > 10:
        limit = 10
    return ticket_service.get_passengers(db, flight_number, skip, limit, date=date)
