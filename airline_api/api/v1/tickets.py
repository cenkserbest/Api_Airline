from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas import schemas
from services import ticket_service
from api.v1.auth import get_current_user
from models import models

router = APIRouter()

@router.post("/buy", response_model=schemas.TicketResponse)
def buy_ticket(
    ticket: schemas.TicketBuy, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Buy tickets for a flight.
    Authentication required.
    """
    return ticket_service.buy_ticket(db, ticket)

@router.post("/check-in", response_model=schemas.CheckInResponse)
def check_in(
    request: schemas.CheckInRequest,
    db: Session = Depends(get_db)
):
    """
    Check-in passenger to assign seat.
    Authentication NO.
    """
    return ticket_service.check_in(db, request)
