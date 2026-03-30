import pandas as pd
from typing import List
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from repositories import flight_repo
from schemas import schemas

def add_flight(db: Session, flight: schemas.FlightCreate):
    existing_flight = flight_repo.get_flight_by_number(db, flight.flight_number)
    if existing_flight:
        raise HTTPException(status_code=400, detail=f"Flight '{flight.flight_number}' already exists in the system.")
    
    created_flight = flight_repo.create_flight(db, flight)
    return {"transaction_status": "Success", "flight_number": created_flight.flight_number}

async def add_flights_from_csv(db: Session, file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    try:
        # Load csv into a pandas dataframe
        df = pd.read_csv(file.file)
        
        flights_added = 0
        for index, row in df.iterrows():
            flight_number_str = str(row['Flight number'])
            
            # Check if flight already exists to provide a clean error message
            if flight_repo.get_flight_by_number(db, flight_number_str):
                raise HTTPException(status_code=400, detail=f"Flight '{flight_number_str}' in line {index + 1} already exists! Stopping CSV processing. Records added so far: {flights_added}")
                
            # Validate row content against schema
            flight_data = schemas.FlightCreate(
                flight_number=flight_number_str,
                date_from=pd.to_datetime(row['date-from']).to_pydatetime(),
                date_to=pd.to_datetime(row['date-to']).to_pydatetime(),
                airport_from=str(row['airport-from']),
                airport_to=str(row['airport-to']),
                duration=str(row['duration']),
                capacity=int(row['capacity'])
            )
            flight_repo.create_flight(db, flight_data)
            flights_added += 1
        return {"status": "File processed successfully", "records_added": flights_added}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")
