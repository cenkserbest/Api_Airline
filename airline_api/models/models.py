from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String, unique=True, index=True, nullable=False)
    date_from = Column(DateTime, nullable=False)
    date_to = Column(DateTime, nullable=False)
    airport_from = Column(String, nullable=False)
    airport_to = Column(String, nullable=False)
    duration = Column(String, nullable=False) # e.g. "2h 30m"
    capacity = Column(Integer, nullable=False)
    
    # Relationships
    tickets = relationship("Ticket", back_populates="flight")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    passenger_name = Column(String, nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    seat_assigned = Column(String, nullable=True) # Seat number like "1", "2A", etc.
    
    flight = relationship("Flight", back_populates="tickets")
