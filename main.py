import os
import json
import dns.resolver
import smtplib
import asyncio
from dotenv import load_dotenv
import uuid
import re

load_dotenv()

# Environment variables with validation
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
JWT_SECRET = os.getenv("JWT_SECRET")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")

# Validate critical environment variables
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable is required")
if not SENDGRID_API_KEY:
    raise ValueError("SENDGRID_API_KEY environment variable is required")

# Email validation regex pattern
EMAIL_VALIDATION_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import or_, select
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import sendgrid
from sendgrid.helpers.mail import Mail
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from starlette.config import Config
from starlette.responses import RedirectResponse
import uvicorn
import requests
import re

from database import SessionLocal, engine
from typing import List
from models import Base, User as DBUser, Template, Campaign, EmailLog
from schemas import (
    EmailRequest, User as UserSchema, UserUpdate, AdminUserCreate, AdminUserUpdate, UserPasswordUpdate,
    Template as TemplateSchema, TemplateCreate, TemplateUpdate,
    Campaign as CampaignSchema, CampaignCreate,
    EmailLog as EmailLogSchema, EmailLogCreate,
    DashboardStats, EmailStats, EmailValidationRequest, EmailValidationResponse, EmailValidationResult, EmailGenerationRequest, EmailGenerationResponse,
    ComprehensiveAnalytics, EmailStatusStats, DeliveryStats, TimeBasedStats
)

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=JWT_SECRET
)

Base.metadata.create_all(bind=engine)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth config for Google
config = Config('.env')
oauth = OAuth(config)

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile',
            'redirect_uri': 'http://localhost:8000/auth/google/callback'
        },
    )
else:
    print("Warning: Google OAuth not configured.")

# DB dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password utils
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# User utils
def get_user(db: Session, username: str):
    return db.query(DBUser).filter(DBUser.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(DBUser).filter(DBUser.email == email).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return user

def get_current_admin_user(current_user: DBUser = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have administrative privileges"
        )
    return current_user

# --- Admin User Management Endpoints ---

@app.get("/admin/users", response_model=List[UserSchema])
def get_all_users(db: Session = Depends(get_db), admin: DBUser = Depends(get_current_admin_user)):
    return db.query(DBUser).all()

@app.post("/admin/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user(user_create: AdminUserCreate, db: Session = Depends(get_db), admin: DBUser = Depends(get_current_admin_user)):
    # Input validation
    if not user_create.username or len(user_create.username.strip()) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if not EMAIL_VALIDATION_PATTERN.match(user_create.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    if not user_create.password or len(user_create.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Check for conflicts
    if get_user(db, user_create.username.strip()):
        raise HTTPException(status_code=400, detail="Username already registered")
    if get_user_by_email(db, user_create.email.lower()):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    try:
        hashed_password = get_password_hash(user_create.password)
        new_user = DBUser(
            username=user_create.username.strip(),
            email=user_create.email.lower(),
            hashed_password=hashed_password,
            role=user_create.role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create user")

@app.put("/admin/users/{user_id}", response_model=UserSchema)
def update_user(user_id: int, user_update: AdminUserUpdate, db: Session = Depends(get_db), admin: DBUser = Depends(get_current_admin_user)):
    user_to_update = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user_to_update:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from demoting themselves
    if user_id == admin.id and user_update.role and user_update.role != "admin":
        raise HTTPException(status_code=400, detail="You cannot demote yourself from admin role")

    if user_update.username:
        user_to_update.username = user_update.username
    if user_update.email:
        user_to_update.email = user_update.email
    if user_update.role:
        user_to_update.role = user_update.role

    db.commit()
    db.refresh(user_to_update)
    return user_to_update

@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db), admin: DBUser = Depends(get_current_admin_user)):
    user_to_delete = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user_to_delete)
    db.commit()

# --- Dashboard and Analytics Endpoints ---

@app.get("/dashboard/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Email stats - include both campaign emails and individual emails
    # Get all campaign IDs for this user
    user_campaign_ids = [c.id for c in db.query(Campaign.id).filter(Campaign.user_id == current_user.id).all()]

    today_count = db.query(EmailLog).filter(
        EmailLog.sent_at >= today_start,
        EmailLog.status == "sent",  # Only count sent emails
        or_(
            EmailLog.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,  # Campaign emails
            EmailLog.user_id == current_user.id  # Individual emails
        )
    ).count()

    week_count = db.query(EmailLog).filter(
        EmailLog.sent_at >= week_ago,
        EmailLog.status == "sent",  # Only count sent emails
        or_(
            EmailLog.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,  # Campaign emails
            EmailLog.user_id == current_user.id  # Individual emails
        )
    ).count()

    month_count = db.query(EmailLog).filter(
        EmailLog.sent_at >= month_ago,
        EmailLog.status == "sent",  # Only count sent emails
        or_(
            EmailLog.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,  # Campaign emails
            EmailLog.user_id == current_user.id  # Individual emails
        )
    ).count()

    this_month_count = db.query(EmailLog).filter(
        EmailLog.sent_at >= month_start,
        EmailLog.status == "sent",  # Only count sent emails
        or_(
            EmailLog.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,  # Campaign emails
            EmailLog.user_id == current_user.id  # Individual emails
        )
    ).count()

    email_stats = EmailStats(
        today=today_count,
        last_7_days=week_count,
        last_30_days=month_count,
        this_month=this_month_count
    )

    # Total campaigns
    total_campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).count()

    # Recent campaigns
    recent_campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).order_by(Campaign.created_at.desc()).limit(5).all()

    return DashboardStats(
        email_stats=email_stats,
        total_campaigns=total_campaigns,
        recent_campaigns=recent_campaigns
    )

# --- Comprehensive Analytics Endpoint ---

@app.get("/analytics", response_model=ComprehensiveAnalytics)
def get_comprehensive_analytics(db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get all campaign IDs for this user
    user_campaign_ids = [c.id for c in db.query(Campaign.id).filter(Campaign.user_id == current_user.id).all()]

    # Helper function to get status counts for a time period
    def get_status_counts(start_date):
        base_query = db.query(EmailLog).filter(
            EmailLog.sent_at >= start_date,
            or_(
                EmailLog.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False,
                EmailLog.user_id == current_user.id
            )
        )

        sent = base_query.filter(EmailLog.status == "sent").count()
        failed = base_query.filter(EmailLog.status == "failed").count()
        bounced = base_query.filter(EmailLog.status == "bounced").count()
        total = sent + failed + bounced

        return EmailStatusStats(sent=sent, failed=failed, bounced=bounced, total=total)

    # Get overall statistics
    all_time = get_status_counts(datetime.min)  # All emails

    # Calculate delivery stats
    total_emails = all_time.total
    if total_emails > 0:
        delivery_rate = (all_time.sent / total_emails) * 100
        bounce_rate = (all_time.bounced / total_emails) * 100
        success_rate = ((all_time.sent + all_time.failed) / total_emails) * 100  # Excluding bounces
    else:
        delivery_rate = bounce_rate = success_rate = 0.0

    delivery_stats = DeliveryStats(
        delivery_rate=round(delivery_rate, 2),
        bounce_rate=round(bounce_rate, 2),
        success_rate=round(success_rate, 2)
    )

    # Time-based statistics
    time_based = TimeBasedStats(
        today=get_status_counts(today_start),
        last_7_days=get_status_counts(week_ago),
        last_30_days=get_status_counts(month_ago),
        this_month=get_status_counts(month_start)
    )

    # Campaign vs Individual emails
    campaign_emails = db.query(EmailLog).filter(
        EmailLog.campaign_id.in_(user_campaign_ids) if user_campaign_ids else False
    ).count()

    individual_emails = db.query(EmailLog).filter(
        EmailLog.user_id == current_user.id,
        EmailLog.campaign_id.is_(None)
    ).count()

    return ComprehensiveAnalytics(
        total_emails=total_emails,
        status_breakdown=all_time,
        delivery_stats=delivery_stats,
        time_based=time_based,
        campaign_emails=campaign_emails,
        individual_emails=individual_emails
    )

# --- Template Management Endpoints ---

@app.get("/templates", response_model=List[TemplateSchema])
def get_templates(db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    # Return all templates for now (since existing DB doesn't have user_id column)
    # In future, we can filter by user when user_id column is added
    return db.query(Template).all()

@app.post("/templates", response_model=TemplateSchema)
def create_template(template: TemplateCreate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    # Generate a unique string ID for the new template
    import uuid
    template_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID

    # For now, don't set user_id since the column doesn't exist in existing DB
    # In future, we can set user_id when the column is added
    db_template = Template(
        id=template_id,
        name=template.name,
        subject=template.subject,
        body=template.body,
        category=template.category
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template

@app.put("/templates/{template_id}", response_model=TemplateSchema)
def update_template(template_id: str, template_update: TemplateUpdate, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    # Input validation
    if not template_id or len(template_id.strip()) == 0:
        raise HTTPException(status_code=400, detail="Invalid template ID")
    
    template = db.query(Template).filter(Template.id == template_id.strip()).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        update_data = template_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            if isinstance(value, str):
                value = value.strip()
            setattr(template, key, value)
        db.commit()
        db.refresh(template)
        return template
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update template")

@app.delete("/templates/{template_id}")
def delete_template(template_id: str, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # For now, allow deleting all templates since user_id column doesn't exist
    # In future, we can add proper authorization when user_id column is added

    db.delete(template)
    db.commit()
    return {"message": "Template deleted"}

# --- Email Validation Endpoint ---

# Add this import at the top of main.py if it's not there
# import uuid

# ULTRA-FAST Email Validation with Caching and Parallel Processing
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import threading

# Global DNS cache with TTL
dns_cache = {}
dns_cache_lock = threading.Lock()
DNS_CACHE_TTL = 3600  # 1 hour

# Thread pool for DNS lookups
dns_executor = ThreadPoolExecutor(max_workers=20)

# Known valid domains - pre-validated to skip DNS lookups
KNOWN_VALID_DOMAINS = {
    # Major providers
    'gmail.com', 'googlemail.com',  # Google
    'outlook.com', 'hotmail.com', 'live.com', 'msn.com',  # Microsoft
    'yahoo.com', 'yahoo.co.uk', 'yahoo.ca', 'yahoo.au', 'ymail.com', 'rocketmail.com',  # Yahoo
    'aol.com', 'aim.com',  # AOL
    'icloud.com', 'me.com', 'mac.com',  # Apple
    'protonmail.com', 'proton.me',  # ProtonMail
    'zoho.com', 'zohomail.com',  # Zoho
    'yandex.com', 'yandex.ru',  # Yandex
    'mail.ru', 'inbox.ru', 'list.ru', 'bk.ru',  # Mail.ru
    'gmx.com', 'gmx.net', 'gmx.de',  # GMX
    'web.de', 't-online.de',  # Deutsche Telekom
    'comcast.net', 'verizon.net', 'att.net', 'bellsouth.net',  # US ISPs

    # Common business domains (pre-validated)
    'company.com', 'business.com', 'enterprise.com', 'corp.com', 'inc.com',
    'example.com', 'test.com', 'sample.com', 'demo.com', 'fake.com',
    'kalkiavatar.org', 'apple.com', 'microsoft.com', 'amazon.com', 'facebook.com', 'twitter.com',
}

# Disposable/temporary email domains
DISPOSABLE_DOMAINS = {
    '10minutemail.com', 'guerrillamail.com', 'mailinator.com', 'tempmail.org',
    'throwaway.email', 'yopmail.com', 'temp-mail.org', 'fakeinbox.com',
    'maildrop.cc', 'tempail.com', 'dispostable.com', '0-mail.com',
    'mytemp.email', 'temp-mail.io', 'mail-temp.com', 'tempinbox.com',
    'spamgourmet.com', 'mailnull.com', 'suremail.info', 'spamhole.com',
    'grr.la', 'pokemail.net', 'spam4.me', 'koszmail.pl', 'binkmail.com',
    'spambog.ru', 'safersignup.de', 'deadaddress.com', 'kurzepost.de',
    'lifebyfood.com', 'objectmail.com', 'obobbo.com', 'rcpt.at',
    'spamobox.com', 'upliftnow.com', 'uplipht.com', 'venompen.com',
    'walkmail.net', 'wetrainbayarea.com', 'zetmail.com'
}

# Role-based email prefixes that might indicate non-personal emails
ROLE_PREFIXES = {
    'admin', 'administrator', 'info', 'contact', 'support', 'help', 'sales',
    'marketing', 'billing', 'accounts', 'finance', 'hr', 'humanresources',
    'jobs', 'careers', 'recruitment', 'noreply', 'no-reply', 'donotreply',
    'do-not-reply', 'newsletter', 'news', 'updates', 'alerts', 'notifications',
    'webmaster', 'postmaster', 'hostmaster', 'root', 'sysadmin', 'abuse',
    'security', 'privacy', 'legal', 'compliance', 'feedback', 'survey'
}

# Known spam trap domains/patterns
SPAM_TRAP_DOMAINS = {
    'spamtrap.com', 'spamcop.net', 'abuse.net', 'uol.com.br',
    'blackhole.com', 'devnull.com', 'null.com', 'spamhole.com'
}

# Major providers that don't need SMTP verification
MAJOR_PROVIDERS = KNOWN_VALID_DOMAINS.copy()

async def cached_dns_lookup(domain):
    """Cached DNS MX lookup with TTL"""
    now = asyncio.get_event_loop().time()

    with dns_cache_lock:
        if domain in dns_cache:
            cached_result, timestamp = dns_cache[domain]
            if now - timestamp < DNS_CACHE_TTL:
                return cached_result
            else:
                del dns_cache[domain]

    try:
        # Use thread pool for DNS lookup
        mx_records = await asyncio.get_event_loop().run_in_executor(
            dns_executor, dns.resolver.resolve, domain, 'MX'
        )
        result = str(mx_records[0].exchange)

        with dns_cache_lock:
            dns_cache[domain] = (result, now)

        return result
    except Exception as e:
        # Cache negative results too
        with dns_cache_lock:
            dns_cache[domain] = (None, now)
        return None

async def validate_single_email(email):
    """Advanced email validation with comprehensive checks"""
    email = email.strip()

    # 1. Format Check (instant)
    if not EMAIL_VALIDATION_PATTERN.match(email):
        return EmailValidationResult(email=email, valid=False, deliverable=False, reason="Invalid Format")

    local_part, domain = email.split('@')
    domain = domain.lower()
    local_part = local_part.lower()

    # 2. Check disposable domains first
    if domain in DISPOSABLE_DOMAINS:
        return EmailValidationResult(email=email, valid=False, deliverable=False, reason="Disposable Email Domain")

    # 3. Check spam trap domains
    if domain in SPAM_TRAP_DOMAINS:
        return EmailValidationResult(email=email, valid=False, deliverable=False, reason="Spam Trap Domain")

    # 4. Check known valid domains (instant - no network calls)
    if domain in KNOWN_VALID_DOMAINS:
        if domain in MAJOR_PROVIDERS:
            return EmailValidationResult(email=email, valid=True, deliverable=True, reason="Valid Domain (Major Provider)")
        else:
            return EmailValidationResult(email=email, valid=True, deliverable=True, reason="Valid Domain")

    # 5. For unknown domains, check DNS first
    mail_server = await cached_dns_lookup(domain)
    if not mail_server:
        return EmailValidationResult(email=email, valid=False, deliverable=False, reason="Invalid Domain (No MX Record)")

    # 6. Domain has MX, so role-based emails are acceptable
    if local_part in ROLE_PREFIXES:
        return EmailValidationResult(email=email, valid=True, deliverable=True, reason="Role-based / non-personal")

    # 7. Advanced SMTP verification with catch-all detection
    try:
        smtp_result = await asyncio.to_thread(check_smtp_advanced, mail_server, email, domain)

        if smtp_result["status"] == "verified":
            return EmailValidationResult(email=email, valid=True, deliverable=True, reason="Mailbox Verified")
        elif smtp_result["status"] == "catch_all":
            return EmailValidationResult(email=email, valid=True, deliverable=True, reason="Domain Valid (Catch-all)")
        elif smtp_result["status"] == "not_verified":
            return EmailValidationResult(email=email, valid=False, deliverable=False, reason="Mailbox Not Found")
        elif smtp_result["status"] == "smtp_unreachable":
            return EmailValidationResult(email=email, valid=True, deliverable=False, reason="SMTP unreachable – possibly valid")
        else:  # server_error
            # If SMTP fails, still mark as valid since many servers block verification
            return EmailValidationResult(email=email, valid=True, deliverable=True, reason="Domain Valid (SMTP Blocked)")

    except Exception:
        # If advanced SMTP fails, mark as SMTP unreachable
        return EmailValidationResult(email=email, valid=True, deliverable=False, reason="SMTP unreachable – possibly valid")

@app.post("/email/validate", response_model=EmailValidationResponse)
async def validate_emails(request: EmailValidationRequest, current_user: DBUser = Depends(get_current_user)):
    # Input validation
    if not request.emails or len(request.emails) == 0:
        raise HTTPException(status_code=400, detail="No emails provided")
    if len(request.emails) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 emails allowed")

    # Process all emails in parallel with semaphore to prevent overwhelming
    semaphore = asyncio.Semaphore(50)  # Max 50 concurrent validations

    async def validate_with_semaphore(email):
        async with semaphore:
            return await validate_single_email(email)

    # Create validation tasks
    tasks = [validate_with_semaphore(email) for email in request.emails]

    # Execute all validations concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle any exceptions that occurred
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # If validation failed, return a safe result
            final_results.append(EmailValidationResult(
                email=request.emails[i],
                valid=False,
                deliverable=False,
                reason="Validation Error"
            ))
        else:
            final_results.append(result)

    return EmailValidationResponse(results=final_results)

# Ultra-fast SMTP checking with optimized timeout
def check_smtp_mailbox_fast(mail_server, email_address, domain):
    """Fast SMTP verification with shorter timeout"""
    try:
        with smtplib.SMTP(mail_server, timeout=5) as server:  # Reduced timeout
            server.set_debuglevel(0)
            server.helo('kalkiavatar.org')

            # Check the actual email address only (skip catch-all detection for speed)
            code_real, _ = server.rcpt(email_address)

            if code_real == 250:
                return "verified", "Mailbox exists"
            elif code_real in (550, 551, 552, 553, 554):
                return "not_verified", f"Mailbox rejected (code {code_real})"
            else:
                return "server_error", f"Unexpected response code {code_real}"

    except smtplib.SMTPException as e:
        return "server_error", f"SMTP error: {str(e)}"
    except (ConnectionError, OSError) as e:
        return "server_error", f"Connection error: {str(e)}"
    except Exception as e:
        return "server_error", f"Unexpected error: {str(e)}"

# Advanced SMTP checking with catch-all detection
def check_smtp_advanced(mail_server, email_address, domain):
    """Advanced SMTP verification with catch-all detection"""
    # Use a random, non-existent email to check for catch-all
    random_user = uuid.uuid4().hex[:16]
    fake_email_for_check = f"{random_user}@{domain}"

    try:
        with smtplib.SMTP(mail_server, timeout=8) as server:  # Slightly longer timeout for advanced check
            server.set_debuglevel(0)
            server.helo('kalkiavatar.org')
            server.mail('verify@kalkiavatar.org')

            # Check the actual email address
            code_real, _ = server.rcpt(email_address)

            if code_real != 250:
                # If the real email is rejected, we know it's not valid
                return {"status": "not_verified", "message": f"Mailbox rejected with code {code_real}"}

            # If the real email was accepted, check the fake one to detect a catch-all
            code_fake, _ = server.rcpt(fake_email_for_check)

            if code_fake == 250:
                # If the server also accepts a random fake email, it's a catch-all
                return {"status": "catch_all", "message": "Domain is a catch-all"}
            else:
                # If the server accepts the real one but rejects the fake one, it's truly verified
                return {"status": "verified", "message": "Mailbox exists"}

    except smtplib.SMTPException as e:
        return {"status": "smtp_unreachable", "message": f"SMTP unreachable: {str(e)}"}
    except (ConnectionError, OSError) as e:
        return {"status": "smtp_unreachable", "message": f"SMTP unreachable: {str(e)}"}
    except Exception as e:
        return {"status": "smtp_unreachable", "message": f"SMTP unreachable: {str(e)}"}
# --- AI Email Generation Endpoint ---

@app.post("/ai/generate-email", response_model=EmailGenerationResponse)
def generate_email(request: EmailGenerationRequest, current_user: DBUser = Depends(get_current_user)):
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=500, detail="Perplexity API key not configured")

    prompt = f"""
Generate a professional email based on the following request:
{request.prompt}

Recipient information: {request.recipient_info or 'General recipient'}
Tone: {request.tone}

Please provide:
1. A compelling subject line
2. A well-structured email body

Format your response as JSON with 'subject' and 'body' fields.
"""

    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000
            }
        )

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="AI service error")

        data = response.json()
        content = data['choices'][0]['message']['content']

        # Parse the response (assuming it returns JSON)
        try:
            parsed = json.loads(content)
            return EmailGenerationResponse(subject=parsed['subject'], body=parsed['body'])
        except:
            # Fallback: extract subject and body from text
            lines = content.split('\n')
            subject = ""
            body = ""
            for line in lines:
                if line.startswith('Subject:') or line.startswith('subject:'):
                    subject = line.split(':', 1)[1].strip()
                elif line.startswith('Body:') or line.startswith('body:'):
                    body = line.split(':', 1)[1].strip()
                else:
                    body += line + '\n'
            return EmailGenerationResponse(subject=subject or "Generated Email", body=body.strip())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")


# Endpoints
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/google")
async def google_login(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google Oauth not configured.")
    redirect_uri = "http://localhost:8000/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth not configured.")
    
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info_response = await oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo', token=token)
        user_info = user_info_response.json()
        
        if user_info and 'email' in user_info:
            email = user_info['email']
            db_user = get_user_by_email(db, email)

            if not db_user:
                return RedirectResponse(url="http://localhost:8000/?contact_admin=1", status_code=302)
            else:
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(data={"sub": db_user.username}, expires_delta=access_token_expires)
                return RedirectResponse(url=f"http://localhost:8000/?token={access_token}", status_code=302)
        else:
            raise HTTPException(status_code=400, detail="Google login failed: Could not retrieve email.")
            
    except Exception as e:
        # For security, log the actual error to the console but return a generic message to the user.
        print(f"An error occurred during Google authentication: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during Google authentication.")

@app.get("/users/me", response_model=UserSchema)
async def read_users_me(current_user: DBUser = Depends(get_current_user)):
    return current_user

@app.put("/users/me/update", response_model=UserSchema)
async def update_user_me(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    # Check for username conflicts
    if user_update.username and user_update.username != current_user.username:
        existing_user = get_user(db, user_update.username)
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        current_user.username = user_update.username

    # Check for email conflicts
    if user_update.email and user_update.email != current_user.email:
        existing_user = get_user_by_email(db, user_update.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        current_user.email = user_update.email
    
    db.commit()
    db.refresh(current_user)
    return current_user

@app.put("/users/me/change-password")
async def change_password(
    password_update: UserPasswordUpdate,
    db: Session = Depends(get_db),
    current_user: DBUser = Depends(get_current_user)
):
    # Verify the current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    # Hash the new password and update the user
    current_user.hashed_password = get_password_hash(password_update.new_password)
    db.commit()

    return {"message": "Password updated successfully"}

@app.post("/api/send-email")
async def send_email(email_request: EmailRequest, db: Session = Depends(get_db), current_user: DBUser = Depends(get_current_user)):
    if not SENDGRID_API_KEY:
        raise HTTPException(status_code=500, detail="SendGrid not configured")
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        message = Mail(
            from_email=email_request.from_email or SENDGRID_FROM_EMAIL,
            to_emails=email_request.to_email,
            subject=email_request.subject,
            plain_text_content=email_request.body
        )
        response = sg.send(message)

        # Log the email
        email_log = EmailLog(
            user_id=current_user.id,  # Associate with current user
            campaign_id=None,  # For now, no campaign
            recipient_email=email_request.to_email,
            status="sent"
        )
        db.add(email_log)
        db.commit()

        return {"status": "success", "message": "Email sent"}
    except Exception as e:
        # Log failed email
        try:
            email_log = EmailLog(
                user_id=current_user.id,  # Associate with current user
                campaign_id=None,
                recipient_email=email_request.to_email,
                status="failed",
                error_message=str(e)[:500]  # Limit error message length
            )
            db.add(email_log)
            db.commit()
        except Exception as db_error:
            # Don't let database errors mask the original SendGrid error
            print(f"Failed to log email error: {db_error}")

        # Provide more specific error messages for common SendGrid issues
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            error_msg = "SendGrid authentication failed. Please verify: 1) API key is valid, 2) API key has 'Mail Send' permissions, 3) Sender email is verified in SendGrid dashboard"
        elif "401" in error_msg or "Unauthorized" in error_msg:
            error_msg = "SendGrid API key is invalid or expired"
        elif "400" in error_msg:
            error_msg = "Invalid email format or SendGrid configuration issue"

        raise HTTPException(status_code=500, detail=error_msg)

# Serve frontend - mount static files with lower priority so API routes take precedence
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@app.get("/")
async def read_root():
    return FileResponse("index.html", media_type="text/html")

# Mount static files at a specific path to avoid conflicts with API routes
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)