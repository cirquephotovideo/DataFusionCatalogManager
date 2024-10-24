from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models.database import SessionLocal, engine
from models.subscription_models import Base, User, Subscription, Payment
from services.subscription_service import SubscriptionService
import stripe
from datetime import datetime
import os
from pathlib import Path

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(title="Data Fusion Catalog Manager Subscription")

# Mount static files
static_path = Path(__file__).parent / "static"
static_path.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize subscription service
stripe_key = os.getenv("STRIPE_SECRET_KEY")
subscription_service = SubscriptionService(stripe_key)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render home page with pricing plans"""
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "plans": subscription_service.plans
        }
    )

@app.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    """Render signup page"""
    return templates.TemplateResponse(
        "signup.html",
        {"request": request}
    )

@app.post("/signup")
async def signup(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user signup"""
    # Check if user exists
    existing_user = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create Stripe customer
    stripe_customer = subscription_service.create_customer(None, email)

    # Create user
    user = User(
        email=email,
        username=username,
        password_hash=password,  # TODO: Hash password
        stripe_customer_id=stripe_customer
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Start free trial
    trial_end = datetime.now() + timedelta(days=10)
    subscription = Subscription(
        user_id=user.id,
        plan_type="free_trial",
        status="trialing",
        current_period_start=datetime.now(),
        current_period_end=trial_end
    )
    db.add(subscription)
    db.commit()

    return RedirectResponse(url="/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user login"""
    user = db.query(User).filter(User.email == email).first()
    if not user or user.password_hash != password:  # TODO: Verify password hash
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Update last login
    user.last_login = datetime.now()
    db.commit()

    # TODO: Set session cookie
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    """Render user dashboard"""
    # TODO: Get user from session
    user_id = 1  # Placeholder
    
    subscription_status = subscription_service.check_subscription_access(user_id)
    user = db.query(User).filter(User.id == user_id).first()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "subscription": subscription_status
        }
    )

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Render admin dashboard"""
    # TODO: Check admin access
    metrics = subscription_service.get_subscription_metrics()
    
    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "metrics": metrics
        }
    )

@app.post("/create-checkout-session/{plan_type}")
async def create_checkout_session(
    plan_type: str,
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session"""
    # TODO: Get user from session
    user_id = 1  # Placeholder
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    plan = subscription_service.plans.get(plan_type)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    try:
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': plan['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.url_for('success'),
            cancel_url=request.url_for('cancel'),
        )
        return {"sessionId": checkout_session.id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/success")
async def success(request: Request):
    """Handle successful payment"""
    return templates.TemplateResponse(
        "success.html",
        {"request": request}
    )

@app.get("/cancel")
async def cancel(request: Request):
    """Handle cancelled payment"""
    return templates.TemplateResponse(
        "cancel.html",
        {"request": request}
    )

@app.post("/webhook")
async def webhook_received(request: Request):
    """Handle Stripe webhooks"""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    signature = request.headers.get("stripe-signature")
    
    try:
        subscription_service.handle_webhook(
            await request.body(),
            signature
        )
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
