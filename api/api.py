from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import enum

# --- Database setup ---
DATABASE_URL = "mysql+mysqlconnector://admin:teamwhite@jpj-db.chww2e64ifml.ap-southeast-5.rds.amazonaws.com:3306/gov_ai_chatbot"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# --- Models ---
class VehicleLicense(Base):
    __tablename__ = "vehicle_licenses"

    id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String(100))
    ic_number = Column(String(20), unique=True)
    vehicle_number = Column(String(20), unique=True)
    expiry_date = Column(Date)
    renewal_fee = Column(Float)

class SummonsStatus(str, enum.Enum):
    Paid = "Paid"
    Unpaid = "Unpaid"

class VehicleSummons(Base):
    __tablename__ = "vehicle_summons"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String(20))
    ic_number = Column(String(20))
    summons_type = Column(String(50))
    summons_date = Column(Date)
    amount = Column(Float)
    status = Column(Enum(SummonsStatus))

# --- Pydantic Schemas ---
class VehicleLicenseSchema(BaseModel):
    owner_name: str
    ic_number: str
    vehicle_number: str
    expiry_date: str
    renewal_fee: float

class VehicleSummonsSchema(BaseModel):
    vehicle_number: str
    ic_number: str
    summons_type: str
    summons_date: str
    amount: float
    status: SummonsStatus

# --- Create tables if they do not exist ---
Base.metadata.create_all(bind=engine)

# --- FastAPI app ---
app = FastAPI(title="JPJ Vehicle API")

# --- Helper function ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Vehicle License Endpoints ---
@app.get("/licenses/", response_model=List[VehicleLicenseSchema])
def get_all_licenses(skip: int = 0, limit: int = 100):
    with SessionLocal() as db:
        licenses = db.query(VehicleLicense).offset(skip).limit(limit).all()
        return licenses

@app.get("/licenses/{vehicle_number}", response_model=VehicleLicenseSchema)
def get_license(vehicle_number: str):
    with SessionLocal() as db:
        license = db.query(VehicleLicense).filter(VehicleLicense.vehicle_number == vehicle_number).first()
        if not license:
            raise HTTPException(status_code=404, detail="License not found")
        return license

@app.post("/licenses/", response_model=VehicleLicenseSchema)
def create_license(license: VehicleLicenseSchema):
    with SessionLocal() as db:
        db_license = VehicleLicense(**license.dict())
        db.add(db_license)
        db.commit()
        db.refresh(db_license)
        return db_license

@app.put("/licenses/{vehicle_number}", response_model=VehicleLicenseSchema)
def update_license(vehicle_number: str, license: VehicleLicenseSchema):
    with SessionLocal() as db:
        db_license = db.query(VehicleLicense).filter(VehicleLicense.vehicle_number == vehicle_number).first()
        if not db_license:
            raise HTTPException(status_code=404, detail="License not found")
        for key, value in license.dict().items():
            setattr(db_license, key, value)
        db.commit()
        db.refresh(db_license)
        return db_license

@app.delete("/licenses/{vehicle_number}")
def delete_license(vehicle_number: str):
    with SessionLocal() as db:
        db_license = db.query(VehicleLicense).filter(VehicleLicense.vehicle_number == vehicle_number).first()
        if not db_license:
            raise HTTPException(status_code=404, detail="License not found")
        db.delete(db_license)
        db.commit()
        return {"detail": "License deleted successfully"}

# --- Vehicle Summons Endpoints ---
@app.get("/summons/", response_model=List[VehicleSummonsSchema])
def get_all_summons(skip: int = 0, limit: int = 100):
    with SessionLocal() as db:
        summons = db.query(VehicleSummons).offset(skip).limit(limit).all()
        return summons

@app.get("/summons/{id}", response_model=VehicleSummonsSchema)
def get_summons(id: int):
    with SessionLocal() as db:
        s = db.query(VehicleSummons).filter(VehicleSummons.id == id).first()
        if not s:
            raise HTTPException(status_code=404, detail="Summons not found")
        return s

@app.post("/summons/", response_model=VehicleSummonsSchema)
def create_summons(summons: VehicleSummonsSchema):
    with SessionLocal() as db:
        db_summons = VehicleSummons(**summons.dict())
        db.add(db_summons)
        db.commit()
        db.refresh(db_summons)
        return db_summons

@app.put("/summons/{id}", response_model=VehicleSummonsSchema)
def update_summons(id: int, summons: VehicleSummonsSchema):
    with SessionLocal() as db:
        db_summons = db.query(VehicleSummons).filter(VehicleSummons.id == id).first()
        if not db_summons:
            raise HTTPException(status_code=404, detail="Summons not found")
        for key, value in summons.dict().items():
            setattr(db_summons, key, value)
        db.commit()
        db.refresh(db_summons)
        return db_summons

@app.delete("/summons/{id}")
def delete_summons(id: int):
    with SessionLocal() as db:
        db_summons = db.query(VehicleSummons).filter(VehicleSummons.id == id).first()
        if not db_summons:
            raise HTTPException(status_code=404, detail="Summons not found")
        db.delete(db_summons)
        db.commit()
        return {"detail": "Summons deleted successfully"}
