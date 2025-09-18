# mcp_server/server.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Example: Renew license API
class LicenseRenewRequest(BaseModel):
    license_number: str

@app.post("/renew-license")
def renew_license(req: LicenseRenewRequest):
    return {"status": "success", "message": f"License {req.license_number} renewed."}

# Example: Pay summons API
class SummonsPaymentRequest(BaseModel):
    summons_id: str
    amount: float

@app.post("/pay-summons")
def pay_summons(req: SummonsPaymentRequest):
    return {"status": "success", "message": f"Summons {req.summons_id} paid, amount {req.amount}."}
