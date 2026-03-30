from sqlalchemy.orm import Session
from models import models
from schemas import schemas
from datetime import datetime, date

def create_flight(db: Session, flight: schemas.FlightCreate):
    db_flight = models.Flight(**flight.model_dump())
    db.add(db_flight)
    db.commit()
    db.refresh(db_flight)
    return db_flight

def get_flights(db: Session, skip: int = 0, limit: int = 10,
                date_from: datetime = None, date_to: datetime = None,
                airport_from: str = None, airport_to: str = None,
                number_of_people: int = 1, is_round_trip: bool = False):
                
    from sqlalchemy import cast, Date
    
    # Outbound flight query (Gidiş Uçuşları)
    outbound = db.query(models.Flight).filter(models.Flight.capacity >= number_of_people)
    if date_from:
        # Sadece o günkü uçuşları getir, gelecekteki tüm uçuşları değil!
        outbound = outbound.filter(cast(models.Flight.date_from, Date) == date_from.date())
    if airport_from:
        outbound = outbound.filter(models.Flight.airport_from == airport_from)
    if airport_to:
        outbound = outbound.filter(models.Flight.airport_to == airport_to)
        
    if not is_round_trip:
        return outbound.offset(skip).limit(limit).all()
        
    # Round Trip: Fetch both outbound and inbound
    outbound_results = outbound.all()
    inbound_results = []
    
    # Inbound flight cross-query (Dönüş Uçuşları)
    if is_round_trip and date_to:
        inbound = db.query(models.Flight).filter(models.Flight.capacity >= number_of_people)
        inbound = inbound.filter(cast(models.Flight.date_from, Date) == date_to.date())
        if airport_from:
            inbound = inbound.filter(models.Flight.airport_to == airport_from)  # Gidiş havalimanı artık varış
        if airport_to:
            inbound = inbound.filter(models.Flight.airport_from == airport_to)  # Varış havalimanı artık kalkış
        inbound_results = inbound.all()
        
    combined = outbound_results + inbound_results
    
    # Remove duplicates preserving order
    unique_combined = []
    seen = set()
    for flight in combined:
        if flight.id not in seen:
            unique_combined.append(flight)
            seen.add(flight.id)
            
    return unique_combined[skip : skip + limit]

def get_flight_by_number(db: Session, flight_number: str):
    return db.query(models.Flight).filter(models.Flight.flight_number == flight_number).first()
