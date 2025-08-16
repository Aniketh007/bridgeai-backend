import os
from fastapi import APIRouter, Request
from utils.razorpay_client import razorpay_client

router = APIRouter()

@router.post("/create-subscription")
async def create_subscription(request: Request):
    data = await request.json()
    plan_id = data.get("plan_id")
    customer_email = data.get("email")

    customer = razorpay_client.customer.create({
        "name": "ARI User",
        "email": customer_email,
        "fail_existing": "0"
    })

    subscription = razorpay_client.subscription.create({
        "plan_id": plan_id,
        "customer_notify": 1,
        "total_count": 12,  # for 12 months
        "customer_id": customer["id"]
    })

    return {
        "subscription_id": subscription["id"],
        "razorpay_key": os.getenv("RAZORPAY_KEY_ID")
    }


@router.post("/razorpay/webhook")
async def handle_webhook(request: Request):
    payload = await request.body()
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")

    signature = request.headers.get('x-razorpay-signature')

    import hmac, hashlib
    expected_signature = hmac.new(
        webhook_secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    if signature != expected_signature:
        return {"error": "Invalid signature"}

    event = await request.json()
    if event["event"] == "subscription.activated":
        subscription_id = event["payload"]["subscription"]["entity"]["id"]
        # ✅ Activate user access in DB
        print("Subscription activated:", subscription_id)

    return {"status": "ok"}