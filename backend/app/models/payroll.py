"""
Payroll Pydantic Models

Data models for Canadian payroll processing including:
- Employee management
- Payroll runs and records
- Tax calculation requests/results
- Tax table configuration
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, computed_field

# =============================================================================
# Enums
# =============================================================================

class Province(str, Enum):
    """Canadian provinces and territories (excluding Quebec)."""
    AB = "AB"  # Alberta
    BC = "BC"  # British Columbia
    MB = "MB"  # Manitoba
    NB = "NB"  # New Brunswick
    NL = "NL"  # Newfoundland and Labrador
    NS = "NS"  # Nova Scotia
    NT = "NT"  # Northwest Territories
    NU = "NU"  # Nunavut
    ON = "ON"  # Ontario
    PE = "PE"  # Prince Edward Island
    SK = "SK"  # Saskatchewan
    YT = "YT"  # Yukon


class PayFrequency(str, Enum):
    """Pay period frequencies with periods per year."""
    WEEKLY = "weekly"           # 52 periods
    BIWEEKLY = "bi_weekly"      # 26 periods
    SEMI_MONTHLY = "semi_monthly"  # 24 periods
    MONTHLY = "monthly"         # 12 periods

    @property
    def periods_per_year(self) -> int:
        """Get number of pay periods per year."""
        return {
            "weekly": 52,
            "bi_weekly": 26,
            "semi_monthly": 24,
            "monthly": 12
        }[self.value]


class PayrollRunStatus(str, Enum):
    """Payroll run status states."""
    DRAFT = "draft"
    CALCULATING = "calculating"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PAID = "paid"
    CANCELLED = "cancelled"


class EmploymentType(str, Enum):
    """Employment type classification."""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    SEASONAL = "seasonal"
    CONTRACT = "contract"
    CASUAL = "casual"


class CompensationType(str, Enum):
    """Compensation type classification."""
    SALARY = "salary"    # Annual salary
    HOURLY = "hourly"    # Hourly rate


class VacationPayoutMethod(str, Enum):
    """Vacation pay distribution method."""
    ACCRUAL = "accrual"           # Accrue and pay when taken
    PAY_AS_YOU_GO = "pay_as_you_go"  # Add to each paycheck
    LUMP_SUM = "lump_sum"         # Pay once per year


# =============================================================================
# Tax Configuration Models
# =============================================================================

class TaxBracket(BaseModel):
    """Tax bracket definition."""
    threshold: Decimal = Field(description="Income threshold for this bracket")
    rate: Decimal = Field(description="Tax rate for this bracket")
    constant: Decimal = Field(description="Tax constant (K value) for formula")
    description: str | None = None


class ProvinceTaxConfig(BaseModel):
    """Provincial/territorial tax configuration."""
    code: str
    name: str
    bpa: Decimal = Field(description="Basic Personal Amount")
    bpa_is_dynamic: bool = False
    brackets: list[TaxBracket]
    indexing_rate: Decimal | None = None
    has_surtax: bool = False
    has_health_premium: bool = False
    has_tax_reduction: bool = False


class FederalTaxConfig(BaseModel):
    """Federal tax configuration."""
    year: int
    bpaf: Decimal = Field(description="Basic Personal Amount Federal")
    cea: Decimal = Field(description="Canada Employment Amount")
    indexing_rate: Decimal
    brackets: list[TaxBracket]


class CppConfig(BaseModel):
    """CPP contribution configuration."""
    ympe: Decimal = Field(description="Year's Maximum Pensionable Earnings")
    yampe: Decimal = Field(description="Year's Additional Maximum Pensionable Earnings")
    basic_exemption: Decimal
    base_rate: Decimal
    additional_rate: Decimal
    max_base_contribution: Decimal
    max_additional_contribution: Decimal | None = None


class EiConfig(BaseModel):
    """EI premium configuration."""
    mie: Decimal = Field(description="Maximum Insurable Earnings")
    employee_rate: Decimal
    employer_rate_multiplier: Decimal
    max_employee_premium: Decimal


# =============================================================================
# Vacation Configuration
# =============================================================================

class VacationConfig(BaseModel):
    """
    Employee vacation pay configuration.

    The vacation rate follows provincial minimums based on years of service.
    - Most provinces: 4% (2 weeks) initially, 6% (3 weeks) after 5 years
    - Saskatchewan: 5.77% (3 weeks) initially, 7.69% (4 weeks) after 10 years
    - Quebec: 4% initially, 6% after only 3 years

    The frontend is responsible for showing the correct minimum options based on
    the employee's province, so vacation_rate always has a concrete value.
    Use "0" for Owner/Contractor with no vacation pay.
    """

    payout_method: VacationPayoutMethod = VacationPayoutMethod.ACCRUAL

    # Frontend sets this based on province; "0" for Owner/Contractor
    vacation_rate: Decimal = Field(
        default=Decimal("0.04"),
        description="Vacation rate as decimal (e.g., 0.04 = 4%, 0 = none)."
    )

    lump_sum_month: int | None = Field(
        default=None,
        ge=1,
        le=12,
        description="Month for lump sum payout (1-12)"
    )


# =============================================================================
# Employee Models
# =============================================================================

class EmployeeBase(BaseModel):
    """Base employee fields."""
    first_name: str
    last_name: str
    email: str | None = None
    province_of_employment: Province
    pay_frequency: PayFrequency
    employment_type: EmploymentType = EmploymentType.FULL_TIME

    # Address fields (for paystub)
    address_street: str | None = None
    address_city: str | None = None
    address_postal_code: str | None = None
    occupation: str | None = None

    # Compensation (at least one required)
    annual_salary: Decimal | None = None
    hourly_rate: Decimal | None = None

    # TD1 additional claims (beyond BPA, from TD1 form)
    # BPA is fetched dynamically from tax tables based on pay_date
    federal_additional_claims: Decimal = Decimal("0")
    provincial_additional_claims: Decimal = Decimal("0")

    # Exemptions
    is_cpp_exempt: bool = False
    is_ei_exempt: bool = False
    cpp2_exempt: bool = False  # CPT30 form exemption

    # Dates
    hire_date: date
    termination_date: date | None = None

    # Vacation
    vacation_config: VacationConfig = Field(default_factory=lambda: VacationConfig())

    # Initial YTD for transferred employees (CPP/EI only - tax handled by Cumulative Averaging)
    initial_ytd_cpp: Decimal = Field(default=Decimal("0"), ge=0)
    initial_ytd_cpp2: Decimal = Field(default=Decimal("0"), ge=0)
    initial_ytd_ei: Decimal = Field(default=Decimal("0"), ge=0)
    initial_ytd_year: int | None = Field(
        default=None,
        description="Tax year for which initial YTD values apply"
    )


class EmployeeCreate(EmployeeBase):
    """Employee creation request (API input)."""
    sin: str = Field(
        ...,
        min_length=9,
        max_length=9,
        description="Social Insurance Number (will be encrypted)"
    )


class EmployeeUpdate(BaseModel):
    """Employee update request (all fields optional)."""
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    province_of_employment: Province | None = None
    pay_frequency: PayFrequency | None = None
    employment_type: EmploymentType | None = None
    # Address fields
    address_street: str | None = None
    address_city: str | None = None
    address_postal_code: str | None = None
    occupation: str | None = None
    # Compensation
    annual_salary: Decimal | None = None
    hourly_rate: Decimal | None = None
    federal_additional_claims: Decimal | None = None
    provincial_additional_claims: Decimal | None = None
    is_cpp_exempt: bool | None = None
    is_ei_exempt: bool | None = None
    cpp2_exempt: bool | None = None
    termination_date: date | None = None
    vacation_config: VacationConfig | None = None
    # Initial YTD for transferred employees (with non-negative constraint)
    initial_ytd_cpp: Decimal | None = Field(default=None, ge=0)
    initial_ytd_cpp2: Decimal | None = Field(default=None, ge=0)
    initial_ytd_ei: Decimal | None = Field(default=None, ge=0)
    initial_ytd_year: int | None = None


class Employee(EmployeeBase):
    """Complete employee model (from database)."""
    id: UUID
    user_id: str
    company_id: str
    sin_encrypted: str = Field(exclude=True)  # Never expose in API
    vacation_balance: Decimal = Decimal("0")
    sick_balance: Decimal = Decimal("0")  # Paid sick days remaining
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_name(self) -> str:
        """Full name for display."""
        return f"{self.first_name} {self.last_name}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_active(self) -> bool:
        """Whether employee is currently active."""
        return self.termination_date is None

    model_config = {"from_attributes": True}


class EmployeeResponse(BaseModel):
    """Employee API response (with masked SIN)."""
    id: UUID
    first_name: str
    last_name: str
    full_name: str
    sin_masked: str = Field(description="Masked SIN: ***-***-XXX")
    email: str | None
    province_of_employment: Province
    pay_frequency: PayFrequency
    employment_type: EmploymentType
    # Address fields
    address_street: str | None
    address_city: str | None
    address_postal_code: str | None
    occupation: str | None
    # Compensation
    annual_salary: Decimal | None
    hourly_rate: Decimal | None
    federal_additional_claims: Decimal
    provincial_additional_claims: Decimal
    is_cpp_exempt: bool
    is_ei_exempt: bool
    cpp2_exempt: bool
    hire_date: date
    termination_date: date | None
    vacation_config: VacationConfig
    vacation_balance: Decimal
    is_active: bool
    # Initial YTD for transferred employees
    initial_ytd_cpp: Decimal
    initial_ytd_cpp2: Decimal
    initial_ytd_ei: Decimal
    initial_ytd_year: int | None
    created_at: datetime
    updated_at: datetime


# =============================================================================
# Employee Tax Claims Models (TD1 by year)
# =============================================================================

class EmployeeTaxClaimBase(BaseModel):
    """Base TD1 tax claim fields for a specific year."""
    tax_year: int = Field(ge=2020, le=2100)
    federal_bpa: Decimal = Field(ge=0, description="Federal Basic Personal Amount (from config)")
    federal_additional_claims: Decimal = Field(default=Decimal("0"), ge=0)
    provincial_bpa: Decimal = Field(ge=0, description="Provincial Basic Personal Amount (from config)")
    provincial_additional_claims: Decimal = Field(default=Decimal("0"), ge=0)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def federal_total_claim(self) -> Decimal:
        """Total federal TD1 claim amount."""
        return self.federal_bpa + self.federal_additional_claims

    @computed_field  # type: ignore[prop-decorator]
    @property
    def provincial_total_claim(self) -> Decimal:
        """Total provincial TD1 claim amount."""
        return self.provincial_bpa + self.provincial_additional_claims


class EmployeeTaxClaim(EmployeeTaxClaimBase):
    """Complete tax claim record (from database)."""
    id: UUID
    employee_id: UUID
    company_id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EmployeeTaxClaimCreate(BaseModel):
    """Input for creating a tax claim record.

    Note: BPA values are derived server-side from tax configuration based on
    employee's province and tax year. Client only provides additional claims.
    """
    tax_year: int = Field(ge=2020, le=2100)
    # BPA values removed - derived server-side from tax config
    federal_additional_claims: Decimal = Field(default=Decimal("0"), ge=0)
    provincial_additional_claims: Decimal = Field(default=Decimal("0"), ge=0)


class EmployeeTaxClaimUpdate(BaseModel):
    """Input for updating a tax claim record.

    By default, only additional claims are editable. Set recalculate_bpa=True
    to recalculate BPA values from tax config (e.g., when province changes).
    """
    federal_additional_claims: Decimal | None = Field(default=None, ge=0)
    provincial_additional_claims: Decimal | None = Field(default=None, ge=0)
    recalculate_bpa: bool = Field(
        default=False,
        description="If true, recalculate BPA values from tax config based on current province"
    )


# =============================================================================
# Payroll Run Models
# =============================================================================

class PayrollRunBase(BaseModel):
    """Base payroll run fields."""
    period_start: date
    period_end: date
    pay_date: date
    notes: str | None = None


class PayrollRunCreate(PayrollRunBase):
    """Payroll run creation request."""
    pass


class PayrollRun(PayrollRunBase):
    """Complete payroll run model."""
    id: UUID
    user_id: str
    company_id: str
    status: PayrollRunStatus = PayrollRunStatus.DRAFT

    # Summary totals
    total_employees: int = 0
    total_gross: Decimal = Decimal("0")
    total_cpp_employee: Decimal = Decimal("0")
    total_cpp_employer: Decimal = Decimal("0")
    total_ei_employee: Decimal = Decimal("0")
    total_ei_employer: Decimal = Decimal("0")
    total_federal_tax: Decimal = Decimal("0")
    total_provincial_tax: Decimal = Decimal("0")
    total_net_pay: Decimal = Decimal("0")
    total_employer_cost: Decimal = Decimal("0")

    # Beancount integration
    beancount_transaction_ids: list[str] = Field(default_factory=list)

    # Approval
    approved_by: str | None = None
    approved_at: datetime | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Payroll Record Models
# =============================================================================

class PayrollRecordBase(BaseModel):
    """Base payroll record fields (earnings)."""
    gross_regular: Decimal
    gross_overtime: Decimal = Decimal("0")
    bonus_earnings: Decimal = Decimal("0")  # Lump-sum payments (e.g., bonuses, commissions)
    holiday_pay: Decimal = Decimal("0")
    holiday_premium_pay: Decimal = Decimal("0")
    vacation_pay_paid: Decimal = Decimal("0")
    other_earnings: Decimal = Decimal("0")


class PayrollRecord(PayrollRecordBase):
    """Complete payroll record model."""
    id: UUID
    payroll_run_id: UUID
    employee_id: UUID
    user_id: str
    company_id: str

    # Employee deductions
    cpp_employee: Decimal = Decimal("0")
    cpp_additional: Decimal = Decimal("0")  # CPP2
    ei_employee: Decimal = Decimal("0")
    federal_tax: Decimal = Decimal("0")
    provincial_tax: Decimal = Decimal("0")
    rrsp: Decimal = Decimal("0")
    union_dues: Decimal = Decimal("0")
    garnishments: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")

    # Employer costs
    cpp_employer: Decimal = Decimal("0")
    ei_employer: Decimal = Decimal("0")

    # Computed totals (from database generated columns)
    total_gross: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    total_employer_cost: Decimal

    # YTD snapshot
    ytd_gross: Decimal = Decimal("0")
    ytd_cpp: Decimal = Decimal("0")
    ytd_ei: Decimal = Decimal("0")
    ytd_federal_tax: Decimal = Decimal("0")
    ytd_provincial_tax: Decimal = Decimal("0")

    # Vacation tracking
    vacation_accrued: Decimal = Decimal("0")
    vacation_hours_taken: Decimal = Decimal("0")

    # Calculation details (for audit/debugging)
    calculation_details: dict[str, Any] | None = None

    # Paystub
    paystub_storage_key: str | None = None
    paystub_generated_at: datetime | None = None

    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Calculation Request/Result Models
# =============================================================================

class PayrollCalculationRequest(BaseModel):
    """Request for payroll calculation."""
    employee_id: UUID
    province: Province
    pay_frequency: PayFrequency
    gross_pay: Decimal
    federal_claim_amount: Decimal
    provincial_claim_amount: Decimal

    # Optional earnings
    gross_overtime: Decimal = Decimal("0")
    holiday_pay: Decimal = Decimal("0")
    vacation_pay: Decimal = Decimal("0")

    # Optional deductions
    rrsp_deduction: Decimal = Decimal("0")
    union_dues: Decimal = Decimal("0")

    # YTD for accurate calculation
    ytd_gross: Decimal = Decimal("0")
    ytd_cpp: Decimal = Decimal("0")
    ytd_ei: Decimal = Decimal("0")

    # Exemptions
    is_cpp_exempt: bool = False
    is_ei_exempt: bool = False
    cpp2_exempt: bool = False


class PayrollCalculationResult(BaseModel):
    """Result of payroll calculation."""
    # Earnings
    gross_pay: Decimal
    gross_overtime: Decimal = Decimal("0")
    holiday_pay: Decimal = Decimal("0")
    vacation_pay: Decimal = Decimal("0")
    total_gross: Decimal

    # Employee deductions
    cpp_employee: Decimal
    cpp_additional: Decimal  # CPP2
    ei_employee: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    rrsp: Decimal
    union_dues: Decimal
    total_employee_deductions: Decimal

    # Employer costs
    cpp_employer: Decimal
    ei_employer: Decimal
    total_employer_costs: Decimal

    # Net pay
    net_pay: Decimal

    # Updated YTD
    new_ytd_gross: Decimal
    new_ytd_cpp: Decimal
    new_ytd_ei: Decimal

    # Calculation details (for debugging/audit)
    calculation_details: dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "json_schema_extra": {
            "example": {
                "gross_pay": "2307.69",
                "total_gross": "2307.69",
                "cpp_employee": "115.40",
                "cpp_additional": "0.00",
                "cpp_employer": "115.40",
                "ei_employee": "37.85",
                "ei_employer": "52.99",
                "federal_tax": "275.24",
                "provincial_tax": "145.80",
                "rrsp": "100.00",
                "union_dues": "0.00",
                "total_employee_deductions": "674.29",
                "total_employer_costs": "168.39",
                "net_pay": "1633.40"
            }
        }
    }


# =============================================================================
# List/Filter Models
# =============================================================================

class EmployeeListFilters(BaseModel):
    """Filters for employee list endpoint."""
    active_only: bool = True
    province: Province | None = None
    pay_frequency: PayFrequency | None = None
    employment_type: EmploymentType | None = None
    search: str | None = None


class PayrollRunListFilters(BaseModel):
    """Filters for payroll run list endpoint."""
    status: PayrollRunStatus | None = None
    year: int | None = None
    start_date: date | None = None
    end_date: date | None = None


# =============================================================================
# Company & Pay Group Enums
# =============================================================================

class RemitterType(str, Enum):
    """CRA remitter type classification based on AMWA."""
    QUARTERLY = "quarterly"         # < $3,000 AMWA
    REGULAR = "regular"             # $3,000 - $24,999 AMWA
    THRESHOLD_1 = "threshold_1"     # $25,000 - $99,999 AMWA
    THRESHOLD_2 = "threshold_2"     # >= $100,000 AMWA


class PeriodStartDay(str, Enum):
    """Period start day options for pay schedules."""
    # Weekly/Bi-weekly options
    SUNDAY = "sunday"
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    # Semi-monthly options
    FIRST_AND_SIXTEENTH = "1st_and_16th"
    FIFTEENTH_AND_LAST = "15th_and_last"
    # Monthly options
    FIRST_OF_MONTH = "1st_of_month"
    FIFTEENTH_OF_MONTH = "15th_of_month"
    LAST_DAY_OF_MONTH = "last_day_of_month"


class BankTimeRate(float, Enum):
    """Bank time accrual rate options."""
    STRAIGHT_TIME = 1.0
    TIME_AND_HALF = 1.5


class BankTimeExpiryMonths(int, Enum):
    """Bank time expiry options in months."""
    THREE_MONTHS = 3
    SIX_MONTHS = 6
    TWELVE_MONTHS = 12


class DeductionType(str, Enum):
    """Deduction type for custom deductions."""
    PRE_TAX = "pre_tax"
    POST_TAX = "post_tax"


class CalculationType(str, Enum):
    """Calculation type for deductions."""
    FIXED = "fixed"
    PERCENTAGE = "percentage"


# =============================================================================
# Company Models
# =============================================================================

class CompanyBase(BaseModel):
    """Base company fields."""
    company_name: str
    business_number: str = Field(
        ...,
        min_length=9,
        max_length=9,
        description="9-digit CRA Business Number"
    )
    payroll_account_number: str = Field(
        ...,
        min_length=15,
        max_length=15,
        description="15-character payroll account (e.g., 123456789RP0001)"
    )
    province: Province

    # Address fields (for paystub)
    address_street: str | None = None
    address_city: str | None = None
    address_postal_code: str | None = None

    # CRA Remittance
    remitter_type: RemitterType = RemitterType.REGULAR

    # Preferences
    auto_calculate_deductions: bool = True
    send_paystub_emails: bool = False

    # Bookkeeping Integration
    bookkeeping_ledger_id: str | None = None
    bookkeeping_ledger_name: str | None = None
    bookkeeping_connected_at: datetime | None = None

    # Company Logo
    logo_url: str | None = None


class CompanyCreate(CompanyBase):
    """Company creation request."""
    pass


class CompanyUpdate(BaseModel):
    """Company update request (all fields optional)."""
    company_name: str | None = None
    business_number: str | None = None
    payroll_account_number: str | None = None
    province: Province | None = None
    # Address fields
    address_street: str | None = None
    address_city: str | None = None
    address_postal_code: str | None = None
    # Other fields
    remitter_type: RemitterType | None = None
    auto_calculate_deductions: bool | None = None
    send_paystub_emails: bool | None = None
    bookkeeping_ledger_id: str | None = None
    bookkeeping_ledger_name: str | None = None
    bookkeeping_connected_at: datetime | None = None
    # Company Logo
    logo_url: str | None = None


class Company(CompanyBase):
    """Complete company model (from database)."""
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Pay Group Policy Models (embedded in PayGroup)
# =============================================================================

class OvertimePolicy(BaseModel):
    """Overtime and bank time policy configuration."""
    bank_time_enabled: bool = False
    bank_time_rate: float = 1.5
    bank_time_expiry_months: int = 3
    require_written_agreement: bool = True


class WcbConfig(BaseModel):
    """WCB/WSIB workers compensation configuration."""
    enabled: bool = False
    industry_class_code: str | None = None
    industry_name: str | None = None
    assessment_rate: Decimal = Decimal("0")
    max_assessable_earnings: Decimal | None = None


class BenefitConfig(BaseModel):
    """Individual benefit configuration."""
    enabled: bool = False
    employee_deduction: Decimal = Decimal("0")
    employer_contribution: Decimal = Decimal("0")
    is_taxable: bool = False


class LifeInsuranceConfig(BenefitConfig):
    """Life insurance configuration."""
    coverage_amount: Decimal = Decimal("0")
    coverage_multiplier: Decimal | None = None


class GroupBenefits(BaseModel):
    """Group benefits configuration."""
    enabled: bool = False
    health: BenefitConfig = Field(default_factory=BenefitConfig)
    dental: BenefitConfig = Field(default_factory=BenefitConfig)
    vision: BenefitConfig = Field(default_factory=BenefitConfig)
    life_insurance: LifeInsuranceConfig = Field(default_factory=LifeInsuranceConfig)
    disability: BenefitConfig = Field(default_factory=BenefitConfig)


class CustomDeduction(BaseModel):
    """Custom deduction item."""
    id: str
    name: str
    type: DeductionType = DeductionType.POST_TAX
    calculation_type: CalculationType = CalculationType.FIXED
    amount: Decimal
    is_employer_contribution: bool = False
    employer_amount: Decimal | None = None
    is_default_enabled: bool = False
    description: str | None = None


# =============================================================================
# Pay Group Models
# =============================================================================

class PayGroupBase(BaseModel):
    """Base pay group fields."""
    name: str
    description: str | None = None
    pay_frequency: PayFrequency
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    compensation_type: CompensationType = CompensationType.SALARY
    province: Province | None = None

    # Pay Schedule
    next_pay_date: date
    period_start_day: PeriodStartDay = PeriodStartDay.MONDAY

    # Leave Policy
    leave_enabled: bool = True

    # Policy Configurations
    overtime_policy: OvertimePolicy = Field(default_factory=OvertimePolicy)
    wcb_config: WcbConfig = Field(default_factory=WcbConfig)
    group_benefits: GroupBenefits = Field(default_factory=GroupBenefits)
    custom_deductions: list[CustomDeduction] = Field(default_factory=list)


class PayGroupCreate(PayGroupBase):
    """Pay group creation request."""
    company_id: UUID


class PayGroupUpdate(BaseModel):
    """Pay group update request (all fields optional)."""
    name: str | None = None
    description: str | None = None
    pay_frequency: PayFrequency | None = None
    employment_type: EmploymentType | None = None
    compensation_type: CompensationType | None = None
    province: Province | None = None
    next_pay_date: date | None = None
    period_start_day: PeriodStartDay | None = None
    leave_enabled: bool | None = None
    overtime_policy: OvertimePolicy | None = None
    wcb_config: WcbConfig | None = None
    group_benefits: GroupBenefits | None = None
    custom_deductions: list[CustomDeduction] | None = None


class PayGroup(PayGroupBase):
    """Complete pay group model (from database)."""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PayGroupWithEmployeeCount(PayGroup):
    """Pay group with employee count (from view)."""
    employee_count: int = 0
    company_name: str | None = None


# =============================================================================
# Company & Pay Group List/Filter Models
# =============================================================================

class CompanyListFilters(BaseModel):
    """Filters for company list endpoint."""
    province: Province | None = None
    search: str | None = None


class PayGroupListFilters(BaseModel):
    """Filters for pay group list endpoint."""
    company_id: UUID | None = None
    pay_frequency: PayFrequency | None = None
    employment_type: EmploymentType | None = None
    compensation_type: CompensationType | None = None
    province: Province | None = None
