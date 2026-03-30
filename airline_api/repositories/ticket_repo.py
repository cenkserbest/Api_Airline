from sqlalchemy.orm import Session
from models import models
from schemas import schemas
import uuid
from datetime import datetime
from fastapi import HTTPException

def buy_ticket(db: Session, ticket: schemas.TicketBuy):
    flight = db.query(models.Flight).filter(models.Flight.flight_number == ticket.flight_number).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
        
    # Security Rule: Reject 0 passengers
    if len(ticket.passeger_names) == 0:
        raise HTTPException(status_code=400, detail="At least one passenger is required to buy tickets")
        
    # Security Rule: Verify flight is not in the past
    if flight.date_from < datetime.now():
        raise HTTPException(status_code=400, detail="Cannot purchase tickets for flights that have already departed")
        
    # Security Rule: Verify requested date matches actual flight departure date
    if flight.date_from.date() != ticket.date:
        raise HTTPException(status_code=400, detail="Flight date does not match the requested date")
        
    if flight.capacity < len(ticket.passeger_names):
        return {"transaction_status": "Sold out", "ticket_numbers": []}
        
    ticket_numbers = []
    
    for passenger in ticket.passeger_names:
        ticket_number = str(uuid.uuid4())[:8].upper()
        db_ticket = models.Ticket(
            ticket_number=ticket_number,
            passenger_name=passenger,
            flight_id=flight.id,
            seat_assigned=None
        )
        db.add(db_ticket)
        ticket_numbers.append(ticket_number)
        
    flight.capacity -= len(ticket.passeger_names)
    db.commit()
    
    return {"transaction_status": "Success", "ticket_numbers": ticket_numbers}

def check_in(db: Session, request: schemas.CheckInRequest):
    flight = db.query(models.Flight).filter(models.Flight.flight_number == request.flight_number).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
        
    # Security Rule: Verify requested date matches actual flight departure date
    if flight.date_from.date() != request.date:
        raise HTTPException(status_code=400, detail="Flight date does not match the requested date")
        
    ticket = db.query(models.Ticket).filter(
        models.Ticket.ticket_number == request.ticket_number,
        models.Ticket.flight_id == flight.id,
        models.Ticket.passenger_name == request.passenger_name
    ).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found for passenger")
        
    if ticket.seat_assigned:
        return {"transaction_status": "Already checked in", "seat_assigned": ticket.seat_assigned}
        
    # Fix: Count ONLY tickets that have already been assigned a seat for this flight, not all tickets sold.
    existing_seats = db.query(models.Ticket).filter(
        models.Ticket.flight_id == flight.id,
        models.Ticket.seat_assigned.is_not(None)
    ).count()
    
    row = (existing_seats // 6) + 1
    letters = ['A', 'B', 'C', 'D', 'E', 'F']
    letter = letters[existing_seats % 6]
    seat = f"{row}{letter}"
    
    ticket.seat_assigned = seat
    db.commit()
    
    return {"transaction_status": "Success", "seat_assigned": seat}

def get_passengers(db: Session, flight_number: str, skip: int = 0, limit: int = 10, date: datetime = None):
    flight = db.query(models.Flight).filter(models.Flight.flight_number == flight_number).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
        
    # Security Rule: If date is requested, verify it matches
    if date and flight.date_from.date() != date.date():
        raise HTTPException(status_code=400, detail="Flight date does not match the requested date")
        
    tickets = db.query(models.Ticket).filter(models.Ticket.flight_id == flight.id).offset(skip).limit(limit).all()
    
    passengers = []
    for t in tickets:
        passengers.append({
            "passenger_name": t.passenger_name,
            "seat_assigned": t.seat_assigned
        })
        
    return {"passengers": passengers}
