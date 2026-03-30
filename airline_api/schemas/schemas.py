from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class FlightBase(BaseModel):
    flight_number: str
    date_from: datetime
    date_to: datetime
    airport_from: str
    airport_to: str
    duration: str
    capacity: int

class FlightCreate(FlightBase):
    pass

class AddFlightResponse(BaseModel):
    transaction_status: str
    flight_number: str

class FlightResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    flight_number: str
    duration: str
    
class TicketBuy(BaseModel):
    flight_number: str
    date: date
    passeger_names: List[str]

class TicketResponse(BaseModel):
    transaction_status: str
    ticket_numbers: List[str]

class CheckInRequest(BaseModel):
    ticket_number: str
    flight_number: str
    date: date
    passenger_name: str

class CheckInResponse(BaseModel):
    transaction_status: str
    seat_assigned: str

class PassengerInfo(BaseModel):
    passenger_name: str
    seat_assigned: Optional[str] = None

class PassengerListResponse(BaseModel):
    passengers: List[PassengerInfo]
