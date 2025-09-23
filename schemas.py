from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# User schemas for authentication
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "user"

class UserCreate(UserBase):
    password: str

# Schema for admins creating a user (can set role)
class AdminUserCreate(UserCreate):
    role: str = "user"

# Schema for admins updating a user (can change anything)
class AdminUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None

class User(UserBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class UserInDB(User):
    hashed_password: str

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Email Request Schema (updated) ---
class EmailRequest(BaseModel):
    from_email: Optional[EmailStr] = None
    to_email: EmailStr
    subject: str
    body: str

# Template schemas
class TemplateBase(BaseModel):
    name: str
    subject: str
    body: str
    category: str

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    category: Optional[str] = None

class Template(TemplateBase):
    id: str  # Changed to str to match existing database
    # user_id: Optional[int]  # Temporarily removed to match database
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# Campaign schemas
class CampaignBase(BaseModel):
    name: str
    template_id: str
    sender_email: str

class CampaignCreate(CampaignBase):
    pass

class Campaign(CampaignBase):
    id: int
    user_id: int
    created_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True

# Email Log schemas
class EmailLogBase(BaseModel):
    recipient_email: str
    status: str = "sent"

class EmailLogCreate(EmailLogBase):
    pass

class EmailLog(EmailLogBase):
    id: int
    campaign_id: int
    sent_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

# Stats schemas
class EmailStats(BaseModel):
    today: int
    last_7_days: int
    last_30_days: int
    this_month: int

class DashboardStats(BaseModel):
    email_stats: EmailStats
    total_campaigns: int
    recent_campaigns: List[Campaign]

# Analytics schemas
class EmailStatusStats(BaseModel):
    sent: int
    failed: int
    bounced: int
    total: int

class DeliveryStats(BaseModel):
    delivery_rate: float  # Percentage
    bounce_rate: float    # Percentage
    success_rate: float   # Percentage

class TimeBasedStats(BaseModel):
    today: EmailStatusStats
    last_7_days: EmailStatusStats
    last_30_days: EmailStatusStats
    this_month: EmailStatusStats

class ComprehensiveAnalytics(BaseModel):
    total_emails: int
    status_breakdown: EmailStatusStats
    delivery_stats: DeliveryStats
    time_based: TimeBasedStats
    campaign_emails: int
    individual_emails: int

# Email validation
class EmailValidationRequest(BaseModel):
    emails: List[str]

class EmailValidationResult(BaseModel):
    email: str
    valid: bool
    reason: Optional[str] = None

class EmailValidationResponse(BaseModel):
    results: List[EmailValidationResult]

# AI Email Generation
class EmailGenerationRequest(BaseModel):
    prompt: str
    recipient_info: Optional[str] = None
    tone: Optional[str] = "professional"

class EmailGenerationResponse(BaseModel):
    subject: str
    body: str