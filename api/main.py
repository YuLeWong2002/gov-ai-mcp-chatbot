from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import os
from decimal import Decimal
from mangum import Mangum

# Pydantic models
class VehicleLicense(BaseModel):
    license_id: Optional[int] = None
    vehicle_id: str
    owner_name: str
    ic_number: str
    expiry_date: date
    renewal_fee: float

class VehicleSummons(BaseModel):
    summons_id: Optional[int] = None
    vehicle_id: str
    summons_type: str
    summons_date: date
    amount: float
    status: str = "Unpaid"

class VehicleLicenseResponse(BaseModel):
    license_id: int
    vehicle_id: str
    owner_name: str
    ic_number: str
    expiry_date: date
    renewal_fee: float

class VehicleSummonsResponse(BaseModel):
    summons_id: int
    vehicle_id: str
    summons_type: str
    summons_date: date
    amount: float
    status: str
    
# Database configuration for AWS RDS
DB_CONFIG = {
    'host': 'jpj-db.chww2e64ifml.ap-southeast-5.rds.amazonaws.com',
    'database': 'gov_ai_chatbot',
    'user': 'admin',  # Replace with your RDS username
    'password': 'teamwhite',  # Replace with your RDS password
    'port': 3306,
    'connect_timeout': 60,  # Add timeout for RDS connection
    'autocommit': True,  # Ensure auto-commit for RDS
    'ssl_disabled': False,  # Enable SSL for RDS (recommended)
    'use_unicode': True,
    'charset': 'utf8mb4'
}

app = FastAPI(title="Government Vehicle Management System", version="1.0.0", root_path="/jpj")

def get_db_connection():
    """Create database connection with RDS-specific settings"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            # Test the connection
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return connection
    except Error as e:
        print(f"Database connection error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database connection failed: {str(e)}. Please check your RDS configuration."
        )

def close_db_connection(connection):
    """Close database connection"""
    if connection.is_connected():
        connection.close()

# =============================================
# VEHICLE LICENSE ENDPOINTS
# =============================================

@app.get("/", summary="Root endpoint")
async def root():
    return {"message": "Government Vehicle Management System API", "version": "1.0.0"}

@app.get("/licenses/", response_model=List[VehicleLicenseResponse], summary="Get all vehicle licenses")
async def get_all_licenses():
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicle_licenses ORDER BY license_id")
        licenses = cursor.fetchall()
        return licenses
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.get("/licenses/{vehicle_id}", response_model=VehicleLicenseResponse, summary="Get license by vehicle ID")
async def get_license_by_vehicle_id(vehicle_id: str):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicle_licenses WHERE vehicle_id = %s", (vehicle_id,))
        license_data = cursor.fetchone()
        
        if not license_data:
            raise HTTPException(status_code=404, detail="Vehicle license not found")
        
        return license_data
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.get("/licenses/ic/{ic_number}", response_model=List[VehicleLicenseResponse], summary="Get licenses by IC number")
async def get_licenses_by_ic(ic_number: str):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicle_licenses WHERE ic_number = %s", (ic_number,))
        licenses = cursor.fetchall()
        return licenses
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.post("/licenses/", response_model=VehicleLicenseResponse, summary="Create new vehicle license")
async def create_license(license: VehicleLicense):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        
        # Check if vehicle_id already exists
        cursor.execute("SELECT license_id FROM vehicle_licenses WHERE vehicle_id = %s", (license.vehicle_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Vehicle ID already exists")
        
        query = """
        INSERT INTO vehicle_licenses (vehicle_id, owner_name, ic_number, expiry_date, renewal_fee)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (license.vehicle_id, license.owner_name, license.ic_number, 
                 license.expiry_date, license.renewal_fee)
        
        cursor.execute(query, values)
        connection.commit()
        
        license_id = cursor.lastrowid
        
        # Return the created license
        cursor.execute("SELECT * FROM vehicle_licenses WHERE license_id = %s", (license_id,))
        created_license = cursor.fetchone()
        
        return {
            "license_id": created_license[0],
            "vehicle_id": created_license[1],
            "owner_name": created_license[2],
            "ic_number": created_license[3],
            "expiry_date": created_license[4],
            "renewal_fee": float(created_license[5])
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.put("/licenses/{vehicle_id}", response_model=VehicleLicenseResponse, summary="Update vehicle license")
async def update_license(vehicle_id: str, license: VehicleLicense):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        
        # Check if license exists
        cursor.execute("SELECT license_id FROM vehicle_licenses WHERE vehicle_id = %s", (vehicle_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Vehicle license not found")
        
        query = """
        UPDATE vehicle_licenses 
        SET owner_name = %s, ic_number = %s, expiry_date = %s, renewal_fee = %s
        WHERE vehicle_id = %s
        """
        values = (license.owner_name, license.ic_number, license.expiry_date, 
                 license.renewal_fee, vehicle_id)
        
        cursor.execute(query, values)
        connection.commit()
        
        # Return updated license
        cursor.execute("SELECT * FROM vehicle_licenses WHERE vehicle_id = %s", (vehicle_id,))
        updated_license = cursor.fetchone()
        
        return {
            "license_id": updated_license[0],
            "vehicle_id": updated_license[1],
            "owner_name": updated_license[2],
            "ic_number": updated_license[3],
            "expiry_date": updated_license[4],
            "renewal_fee": float(updated_license[5])
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.delete("/licenses/{vehicle_id}", summary="Delete vehicle license")
async def delete_license(vehicle_id: str):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        
        # Check if license exists
        cursor.execute("SELECT license_id FROM vehicle_licenses WHERE vehicle_id = %s", (vehicle_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Vehicle license not found")
        
        # Delete related summons first
        cursor.execute("DELETE FROM vehicle_summons WHERE vehicle_id = %s", (vehicle_id,))
        
        # Delete license
        cursor.execute("DELETE FROM vehicle_licenses WHERE vehicle_id = %s", (vehicle_id,))
        connection.commit()
        
        return {"message": f"Vehicle license {vehicle_id} deleted successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

# =============================================
# VEHICLE SUMMONS ENDPOINTS
# =============================================

@app.get("/summons/", response_model=List[VehicleSummonsResponse], summary="Get all summons")
async def get_all_summons():
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicle_summons ORDER BY summons_date DESC")
        summons = cursor.fetchall()
        return summons
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.get("/summons/{vehicle_id}", response_model=List[VehicleSummonsResponse], summary="Get summons by vehicle ID")
async def get_summons_by_vehicle_id(vehicle_id: str):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicle_summons WHERE vehicle_id = %s ORDER BY summons_date DESC", (vehicle_id,))
        summons = cursor.fetchall()
        return summons
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.get("/summons/status/{status}", response_model=List[VehicleSummonsResponse], summary="Get summons by status")
async def get_summons_by_status(status: str):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM vehicle_summons WHERE status = %s ORDER BY summons_date DESC", (status,))
        summons = cursor.fetchall()
        return summons
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.post("/summons/", response_model=VehicleSummonsResponse, summary="Create new summons")
async def create_summons(summons: VehicleSummons):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        
        # Check if vehicle exists
        cursor.execute("SELECT license_id FROM vehicle_licenses WHERE vehicle_id = %s", (summons.vehicle_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Vehicle ID does not exist")
        
        query = """
        INSERT INTO vehicle_summons (vehicle_id, summons_type, summons_date, amount, status)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (summons.vehicle_id, summons.summons_type, summons.summons_date, 
                 summons.amount, summons.status)
        
        cursor.execute(query, values)
        connection.commit()
        
        summons_id = cursor.lastrowid
        
        # Return the created summons
        cursor.execute("SELECT * FROM vehicle_summons WHERE summons_id = %s", (summons_id,))
        created_summons = cursor.fetchone()
        
        return {
            "summons_id": created_summons[0],
            "vehicle_id": created_summons[1],
            "summons_type": created_summons[2],
            "summons_date": created_summons[3],
            "amount": float(created_summons[4]),
            "status": created_summons[5]
        }
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.put("/summons/{summons_id}/pay", summary="Pay summons")
async def pay_summons(summons_id: int):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        
        # Check if summons exists and is unpaid
        cursor.execute("SELECT status FROM vehicle_summons WHERE summons_id = %s", (summons_id,))
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Summons not found")
        
        if result[0] == "Paid":
            raise HTTPException(status_code=400, detail="Summons already paid")
        
        cursor.execute("UPDATE vehicle_summons SET status = 'Paid' WHERE summons_id = %s", (summons_id,))
        connection.commit()
        
        return {"message": f"Summons {summons_id} has been paid successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.delete("/summons/{summons_id}", summary="Delete summons")
async def delete_summons(summons_id: int):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        
        # Check if summons exists
        cursor.execute("SELECT summons_id FROM vehicle_summons WHERE summons_id = %s", (summons_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Summons not found")
        
        cursor.execute("DELETE FROM vehicle_summons WHERE summons_id = %s", (summons_id,))
        connection.commit()
        
        return {"message": f"Summons {summons_id} deleted successfully"}
    except Error as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

# =============================================
# ADDITIONAL UTILITY ENDPOINTS
# =============================================

@app.get("/licenses/expiring/{days}", response_model=List[VehicleLicenseResponse], summary="Get licenses expiring within N days")
async def get_expiring_licenses(days: int):
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
        SELECT * FROM vehicle_licenses 
        WHERE expiry_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL %s DAY)
        ORDER BY expiry_date
        """
        cursor.execute(query, (days,))
        licenses = cursor.fetchall()
        return licenses
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

@app.get("/stats/summary", summary="Get system statistics")
async def get_summary_stats():
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        
        # Total licenses
        cursor.execute("SELECT COUNT(*) FROM vehicle_licenses")
        total_licenses = cursor.fetchone()[0]
        
        # Total summons
        cursor.execute("SELECT COUNT(*) FROM vehicle_summons")
        total_summons = cursor.fetchone()[0]
        
        # Unpaid summons
        cursor.execute("SELECT COUNT(*) FROM vehicle_summons WHERE status = 'Unpaid'")
        unpaid_summons = cursor.fetchone()[0]
        
        # Total unpaid amount
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM vehicle_summons WHERE status = 'Unpaid'")
        unpaid_amount = float(cursor.fetchone()[0])
        
        # Expired licenses
        cursor.execute("SELECT COUNT(*) FROM vehicle_licenses WHERE expiry_date < CURDATE()")
        expired_licenses = cursor.fetchone()[0]
        
        return {
            "total_licenses": total_licenses,
            "total_summons": total_summons,
            "unpaid_summons": unpaid_summons,
            "unpaid_amount": unpaid_amount,
            "expired_licenses": expired_licenses
        }
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        close_db_connection(connection)

handler = Mangum(app)