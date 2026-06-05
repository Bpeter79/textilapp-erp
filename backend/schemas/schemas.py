from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
import re
import datetime

# ── Helpers ───────────────────────────────────────────────────────────────────

def calc_brutto(netto: int, afa_pct: int = 27) -> int:
    n = Decimal(str(netto))
    m = Decimal("1") + Decimal(str(afa_pct)) / Decimal("100")
    return int((n * m).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

def calc_osszeg(menny: float, ar: int) -> int:
    return int((Decimal(str(menny)) * Decimal(str(ar))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ── Auth ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ── Company (companies) ───────────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    company_name: str
    tax_number: Optional[str] = ""
    address: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    industry: Optional[str] = "divat"
    status: Optional[str] = "aktív"
    client_value: Optional[str] = "B"
    payment_terms: Optional[str] = "15 napos átutalás"
    payment_discipline: Optional[str] = "normál"
    note: Optional[str] = ""

    @field_validator("company_name")
    @classmethod
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError("A cégnév nem lehet üres")
        return v.strip()

class CompanyOut(CompanyCreate):
    id: str  # Supabase UUID stringként
    created_at: Optional[datetime.datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ── Contact (contacts) ────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    company_id: str  # UUID
    contact_name: str
    position: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    is_active: Optional[bool] = True

class ContactOut(ContactCreate):
    id: str  # UUID
    company_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ── Project (projects) ────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    company_id: str  # UUID
    contact_id: Optional[str] = None  # UUID
    project_number: str
    project_name: str
    type: Optional[str] = "szériázás"
    status: Optional[str] = "folyamatban"
    priority: Optional[str] = "normál"
    start_date: Optional[str] = None
    deadline_date: Optional[str] = None
    fee_net_huf: Optional[int] = 0
    optitex_folder: Optional[str] = ""
    note: Optional[str] = ""

    @field_validator("project_number")
    @classmethod
    def number_format(cls, v):
        if not re.match(r"^[A-Z]{2,8}-\d{4}-\d{3,6}$", v):
            raise ValueError("Formátum hibás. Elvárt formátum pl: PROJ-2026-001")
        return v

    @model_validator(mode="after")
    def default_start(self):
        if not self.start_date:
            self.start_date = datetime.date.today().isoformat()
        return self

class ProjectOut(ProjectCreate):
    id: str  # UUID
    company_name: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ── Pattern (patterns) ────────────────────────────────────────────────────────

class PatternCreate(BaseModel):
    company_id: str  # UUID
    project_id: Optional[str] = None  # UUID
    item_number: str
    model_name: str
    category: Optional[str] = "felsőruha"
    gender: Optional[str] = "női"
    season: Optional[str] = ""
    size_range: Optional[str] = "XS-XL"
    base_size: Optional[str] = "38"
    fabric_type: Optional[str] = ""
    optitex_file: Optional[str] = ""
    optitex_folder: Optional[str] = ""
    version: Optional[str] = "1.0"
    status: Optional[str] = "aktív"
    note: Optional[str] = ""

class PatternOut(PatternCreate):
    id: str  # UUID
    company_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


# ── Quote (quotes) ────────────────────────────────────────────────────────────

class QuoteCreate(BaseModel):
    company_id: str  # UUID
    project_id: Optional[str] = None  # UUID
    quote_number: str
    quote_name: Optional[str] = ""
    net_huf: int = 0
    vat_pct: int = 27
    status: Optional[str] = "készített"
    valid_until: Optional[str] = None
    note: Optional[str] = ""

    @field_validator("quote_number")
    @classmethod
    def number_format(cls, v):
        if not re.match(r"^[A-Z]{2,8}-\d{4}-\d{3,6}$", v):
            raise ValueError("Formátum hibás. Elvárt formátum pl: AJ-2026-001")
        return v

class QuoteOut(QuoteCreate):
    id: str  # UUID
    gross_huf: int = 0
    company_name: Optional[str] = None

    @model_validator(mode="after")
    def calculate_gross(self):
        self.gross_huf = calc_brutto(self.net_huf, self.vat_pct)
        return self
        
    model_config = ConfigDict(from_attributes=True)


# ── Settlement Item (settlement_items) ────────────────────────────────────────

class SettlementItemCreate(BaseModel):
    settlement_id: str  # UUID
    item_name: str
    project_id: Optional[str] = None  # Opcionális régi munkákhoz
    pattern_id: Optional[str] = None
    service_type: Optional[str] = "szériázás"
    work_done: Optional[str] = ""
    quantity: float = 1.0
    unit: Optional[str] = "db"
    unit_price_net_huf: int = 0

class SettlementItemOut(SettlementItemCreate):
    id: str  # UUID
    total_net_huf: int = 0

    @model_validator(mode="after")
    def calculate_item_total(self):
        self.total_net_huf = calc_osszeg(self.quantity, self.unit_price_net_huf)
        return self
        
    model_config = ConfigDict(from_attributes=True)


# ── Settlement (settlements) ──────────────────────────────────────────────────

class SettlementCreate(BaseModel):
    company_id: str  # UUID
    project_id: Optional[str] = None  # NULL maradhat múltbéli munkáknál
    quote_id: Optional[str] = None
    settlement_number: str
    settlement_name: Optional[str] = "Munka elszámolási jegyzék"
    period_from: Optional[str] = None
    period_to: Optional[str] = None
    net_huf: int = 0
    vat_pct: int = 27
    advance_deducted: int = 0
    invoice_number: Optional[str] = ""
    status: Optional[str] = "piszkozat"
    note: Optional[str] = ""

    @field_validator("settlement_number")
    @classmethod
    def number_format(cls, v):
        if not re.match(r"^[A-Z]{2,8}-\d{4}-\d{3,6}$", v):
            raise ValueError("Formátum hibás. Elvárt formátum pl: ELSZ-2026-001")
        return v

class SettlementOut(SettlementCreate):
    id: str  # UUID
    gross_huf: int = 0
    payable_huf: int = 0
    company_name: Optional[str] = None
    items: List[SettlementItemOut] = []

    @model_validator(mode="after")
    def calculate_settlement_totals(self):
        if self.items:
            self.net_huf = sum(item.total_net_huf for item in self.items)
            
        self.gross_huf = calc_brutto(self.net_huf, self.vat_pct)
        self.payable_huf = max(0, self.gross_huf - self.advance_deducted)
        return self
        
    model_config = ConfigDict(from_attributes=True)


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    companies: int
    projects: int
    quotes: int
    active_projects: int
    total_settled_gross: int
    unbilled_hours: float
    recent_projects: List[Dict[str, Any]] = []
    monthly_revenue: List[Dict[str, Any]] = []

SettlementOut.model_rebuild()