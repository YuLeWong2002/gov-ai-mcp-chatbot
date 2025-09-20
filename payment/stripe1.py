# main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import stripe

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Set your Stripe secret key (test mode)
stripe.api_key = "sk_test_51S9LBMBt12OZb6sY4oAUWpfT5bBZuc8dch1Vi3VUEM4VkJcKGE0RAGchhXsJrWnXGLefs5tE2MPUo0UmgzVMPzA400Hp9jlVXU"
# stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")  # e.g. "sk_test_..."

@app.post("/create-checkout-session")
async def create_checkout_session():
    try:
        # Create a Checkout Session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": "Hackathon Demo Item"},
                        "unit_amount": 500,  # $5.00 in cents
                    },
                    "quantity": 1,
                }
            ],
            success_url="http://localhost:8000/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url="http://localhost:8000/cancel",
        )
        # Redirect user to Stripe Checkout page
        return RedirectResponse(session.url, status_code=303)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/success")
async def success(session_id: str):
    return {"message": "Payment success!", "session_id": session_id}


@app.get("/cancel")
async def cancel():
    return {"message": "Payment cancelled"}
