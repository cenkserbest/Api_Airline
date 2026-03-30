from sqlalchemy.orm import Session
from repositories import ticket_repo
from schemas import schemas

def buy_ticket(db: Session, ticket: schemas.TicketBuy):
    return ticket_repo.buy_ticket(db, ticket)

def check_in(db: Session, request: schemas.CheckInRequest):
    return ticket_repo.check_in(db, request)

def get_passengers(db: Session, flight_number: str, skip: int = 0, limit: int = 10, date=None):
    return ticket_repo.get_passengers(db, flight_number, skip, limit, date=date)
