from fastapi import FastAPI, HTTPException
import stripe
import os

app = FastAPI(title="Stripe Payment Gateway")

stripe.api_key = os.getenv("sk_test_51S9LBMBt12OZb6sY4oAUWpfT5bBZuc8dch1Vi3VUEM4VkJcKGE0RAGchhXsJrWnXGLefs5tE2MPUo0UmgzVMPzA400Hp9jlVXU")

@app.post("/summons/{summons_id}/payment-link")
def create_payment_link(summons_id: str):
    try:
        amount = 5000  # RM 50.00 in sen

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "myr",
                    "product_data": {
                        "name": f"JPJ Summons {summons_id}",
                    },
                    "unit_amount": amount,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="https://stripe.com/docs/payments/checkout/test-success",
            cancel_url="https://stripe.com/docs/payments/checkout/test-canceled",
        )

        return {"summons_id": summons_id, "payment_url": session.url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/success")
def success(session_id: str):
    return {"message": f"Payment successful! session_id={session_id}"}

@app.get("/cancel")
def cancel():
    return {"message": "Payment cancelled"}
