# Phase 8: Holidays & Vacation Pay

**Duration**: 2-3 weeks
**Complexity**: Medium
**Prerequisites**: Phase 1 (Data Layer), Phase 2 (Calculations), Phase 6 (Configuration)

---

## 🎯 Objectives

Implement comprehensive holiday and vacation pay functionality for Canadian payroll across 12 provinces/territories (excluding Quebec).

### Deliverables
1. ✅ Statutory holiday calendars for all provinces (2025-2027)
2. ✅ Holiday pay calculation by province-specific rules
3. ✅ Vacation pay accrual and tracking system
4. ✅ Configuration-driven holiday management
5. ✅ Integration with payroll calculator
6. ✅ UI enhancements for holiday indicators

---

## 📚 Background: Canadian Employment Standards

### Statutory Holidays Overview

**What are Statutory Holidays?**
- Paid public holidays mandated by provincial/territorial employment standards
- Employees entitled to holiday pay even if not working
- Eligibility typically requires 30 days of employment
- Different calculation methods by province

**National vs Provincial Holidays**
- **Federal (Common)**: New Year's Day, Good Friday, Canada Day, Labour Day, Christmas Day
- **Provincial Variations**: Family Day, Victoria Day, Thanksgiving, Remembrance Day
- **Unique Provincial**: Nunavut Day, Islander Day, Heritage Day, Memorial Day (NL)

### Vacation Pay Overview

**Standard Rates:**
- **4%**: Employees with less than 5 years of service
- **6%**: Employees with 5-10 years of service
- **8%**: Federal employees with 10+ years (varies by province)

**Calculation Base:**
- Applied to gross wages earned during vacation entitlement year
- Excludes vacation pay itself
- Includes regular wages, overtime, bonuses, commissions

**Payout Options:**
1. **Accrued**: Paid when vacation taken (most common)
2. **Per-Period**: Added to each paycheck (4%/6% of gross)

---

## 📅 Task 8.1: Statutory Holiday Calendars

### Provincial Statutory Holiday Matrix (2025)

| Holiday | AB | BC | MB | NB | NL | NS | NT | NU | ON | PE | SK | YT |
|---------|----|----|----|----|----|----|----|----|----|----|----|----|
| **New Year's Day** (Jan 1) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Family Day** (Feb 17) | ✅ | ✅ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ⚪ |
| **Louis Riel Day** (Feb 17) | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Islander Day** (Feb 17) | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ |
| **Heritage Day (NS)** (Feb 17) | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Good Friday** (Apr 18) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Easter Monday** (Apr 21) | 🟡 | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Victoria Day** (May 19) | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Canada Day** (Jul 1) | ✅ | ✅ | ✅ | ✅ | ✅* | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Nunavut Day** (Jul 9) | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Civic Holiday** (Aug 4) | 🟡 | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ✅ | ⚪ | ⚪ | ✅ | ⚪ |
| **BC Day** (Aug 4) | ⚪ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ |
| **Labour Day** (Sep 1) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Truth & Reconciliation** (Sep 30) | 🟡 | ✅ | ✅ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ⚪ | ✅ |
| **Thanksgiving** (Oct 13) | ✅ | ✅ | ✅ | ✅ | ⚪ | ⚪ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Remembrance Day** (Nov 11) | ✅ | ✅ | ⚪ | ⚪ | ✅ | ⚪ | ✅ | ✅ | ⚪ | ✅ | ✅ | ✅ |
| **Christmas Day** (Dec 25) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Boxing Day** (Dec 26) | 🟡 | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ⚪ | ✅ | ⚪ | ⚪ | ⚪ |
| **Total Statutory** | **9** | **11** | **9** | **7** | **6** | **6** | **10** | **12** | **9** | **8** | **10** | **9** |

**Legend:**
- ✅ = Statutory holiday (mandatory paid day off)
- 🟡 = Optional holiday (employer discretion)
- ⚪ = Not a holiday in this province
- \* = NL calls Canada Day "Memorial Day"

### Moveable Holidays

Some holidays change dates annually:

```python
# Moveable holidays calculation (Easter-based)
# Good Friday: Easter Sunday - 2 days
# Easter Monday: Easter Sunday + 1 day
# Victoria Day: Last Monday before May 25

# Family Day/Louis Riel Day/Islander Day/Heritage Day: 3rd Monday in February
# BC Day/Civic Holiday: 1st Monday in August
# Labour Day: 1st Monday in September
# Thanksgiving: 2nd Monday in October
```

**2025 Dates:**
- Good Friday: April 18
- Easter Monday: April 21
- Victoria Day: May 19
- Family Day (Feb): February 17
- BC Day/Civic Holiday: August 4
- Labour Day: September 1
- Thanksgiving: October 13

**2026 Dates:**
- Good Friday: April 3
- Easter Monday: April 6
- Victoria Day: May 18
- Family Day (Feb): February 16
- BC Day/Civic Holiday: August 3
- Labour Day: September 7
- Thanksgiving: October 12

---

## 💰 Task 8.2: Holiday Pay Calculation

### Provincial Holiday Pay Formulas

#### Ontario
**Formula:** `(Total regular wages in past 4 work weeks + vacation pay) ÷ 20`

**Example:**
```python
past_4_weeks_wages = Decimal("4000.00")  # Regular wages
past_4_weeks_vacation_pay = Decimal("160.00")  # 4% of wages
holiday_pay = (past_4_weeks_wages + past_4_weeks_vacation_pay) / 20
# holiday_pay = 4160.00 / 20 = 208.00
```

**Implementation:**
```python
def calculate_ontario_holiday_pay(
    wages_past_4_weeks: Decimal,
    vacation_pay_past_4_weeks: Decimal
) -> Decimal:
    """
    Calculate Ontario statutory holiday pay.

    Reference: Ontario Employment Standards Act, Section 24
    URL: https://www.ontario.ca/document/your-guide-employment-standards-act-0/public-holidays
    """
    return (wages_past_4_weeks + vacation_pay_past_4_weeks) / Decimal("20")
```

#### British Columbia
**Formula:** Average day's pay

**Calculation Methods:**
1. **Hourly Employees**: Average daily hours × hourly rate
2. **Salaried Employees**: Annual salary ÷ pay periods per year ÷ work days per period

**Example (Hourly):**
```python
# Employee works 8 hours/day at $25/hour
average_daily_hours = Decimal("8")
hourly_rate = Decimal("25.00")
holiday_pay = average_daily_hours * hourly_rate
# holiday_pay = 200.00
```

**Example (Salaried):**
```python
# Employee earns $60,000/year, bi-weekly pay (26 periods)
annual_salary = Decimal("60000.00")
pay_periods = 26
work_days_per_period = 10  # 2 weeks × 5 days
holiday_pay = annual_salary / pay_periods / work_days_per_period
# holiday_pay = 60000 / 26 / 10 = 230.77
```

**Implementation:**
```python
def calculate_bc_holiday_pay_hourly(
    average_daily_hours: Decimal,
    hourly_rate: Decimal
) -> Decimal:
    """
    Calculate BC holiday pay for hourly employees.

    Reference: BC Employment Standards Act, Section 45-48
    URL: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays
    """
    return average_daily_hours * hourly_rate

def calculate_bc_holiday_pay_salaried(
    annual_salary: Decimal,
    pay_periods_per_year: int
) -> Decimal:
    """Calculate BC holiday pay for salaried employees."""
    work_days_per_period = {
        52: 5,   # Weekly: 5 days
        26: 10,  # Bi-weekly: 10 days
        24: 10,  # Semi-monthly: ~10 days
        12: 21   # Monthly: ~21 days
    }
    days = Decimal(str(work_days_per_period[pay_periods_per_year]))
    return annual_salary / pay_periods_per_year / days
```

#### Alberta
**Formula:** Average daily wage over previous pay period

**Example:**
```python
# Bi-weekly pay period, worked 80 hours, earned $2000
hours_in_pay_period = Decimal("80")
earnings_in_pay_period = Decimal("2000.00")
days_in_pay_period = 10  # 2 weeks

average_daily_wage = earnings_in_pay_period / Decimal(str(days_in_pay_period))
# holiday_pay = 2000 / 10 = 200.00
```

**Implementation:**
```python
def calculate_alberta_holiday_pay(
    earnings_in_pay_period: Decimal,
    days_in_pay_period: int
) -> Decimal:
    """
    Calculate Alberta statutory holiday pay.

    Reference: Alberta Employment Standards Code, Section 24-28
    URL: https://www.alberta.ca/employment-standards-rules
    """
    return earnings_in_pay_period / Decimal(str(days_in_pay_period))
```

#### Other Provinces

**Most provinces use variations of:**
1. **Average day's pay** (similar to BC)
2. **1/20 of wages in 4-week period** (similar to Ontario)
3. **Regular rate × regular hours** (for hourly employees)

### Holiday Pay Eligibility Rules

**Common Requirements:**
- Employed for 30+ days before the holiday
- Worked last scheduled shift before holiday
- Worked first scheduled shift after holiday
- Not absent without permission on either shift

**Exceptions:**
- Medical leave
- Authorized vacation
- Employer-granted leave

**Implementation:**
```python
def is_eligible_for_holiday_pay(
    employee: Employee,
    holiday_date: date,
    last_shift_worked: bool,
    first_shift_after_worked: bool,
    has_authorized_absence: bool
) -> bool:
    """
    Determine if employee qualifies for holiday pay.

    Args:
        employee: Employee record
        holiday_date: Date of statutory holiday
        last_shift_worked: Did employee work last scheduled shift before holiday?
        first_shift_after_worked: Did employee work first scheduled shift after holiday?
        has_authorized_absence: Is absence authorized (medical/vacation)?

    Returns:
        True if eligible for holiday pay
    """
    # Must be employed 30+ days
    days_employed = (holiday_date - employee.hire_date).days
    if days_employed < 30:
        return False

    # Must have worked surrounding shifts OR have authorized absence
    if has_authorized_absence:
        return True

    return last_shift_worked and first_shift_after_worked
```

### Worked Holiday Premium Pay

**If employee works on statutory holiday:**
- **Regular holiday pay** + **Premium pay for hours worked**

**Premium rates:**
- **Ontario**: 1.5× hourly rate (time-and-a-half) + regular holiday pay
- **BC**: 1.5× regular wage for hours worked + average day's pay
- **Alberta**: 1.5× regular rate OR time off in lieu + regular wages

**Example (Ontario):**
```python
# Employee works 8 hours on Christmas (statutory holiday)
# Hourly rate: $25/hour
# Regular holiday pay (from formula): $200

hourly_rate = Decimal("25.00")
hours_worked = Decimal("8")
regular_holiday_pay = Decimal("200.00")  # From 1/20 formula

premium_pay = hours_worked * hourly_rate * Decimal("1.5")
# premium_pay = 8 × 25 × 1.5 = 300.00

total_pay = regular_holiday_pay + premium_pay
# total_pay = 200.00 + 300.00 = 500.00
```

---

## 🏖️ Task 8.3: Vacation Pay Calculation

### Vacation Entitlement by Years of Service

| Years of Service | Vacation Time | Vacation Pay Rate | Applicable To |
|------------------|---------------|-------------------|---------------|
| 0 - 4 years | 2 weeks | 4% | All provinces |
| 5 - 9 years | 3 weeks | 6% | All provinces |
| 10+ years | 4 weeks | 8% | Federal only |

**Provincial Notes:**
- Most provinces: 4% (0-5 years), 6% (5+ years)
- Federal: 4% (0-5), 6% (5-10), 8% (10+)
- Saskatchewan: 3 weeks after 10 years (still 6% pay)

### Vacation Pay Calculation Base

**Included in calculation:**
- Regular wages
- Overtime pay
- Bonuses
- Commissions
- Statutory holiday pay

**Excluded from calculation:**
- Vacation pay itself
- Gifts
- Expense reimbursements
- Severance pay

### Accrual Method

**Method 1: Per-Period Accrual (Recommended)**

Accrue vacation pay each pay period and track balance:

```python
def calculate_vacation_accrual(
    gross_earnings: Decimal,
    years_of_service: Decimal,
    is_federal: bool = False
) -> Decimal:
    """
    Calculate vacation pay accrual for current pay period.

    Args:
        gross_earnings: Gross earnings this period (excluding previous vacation pay)
        years_of_service: Employee's years of service
        is_federal: Is this a federally-regulated employer?

    Returns:
        Vacation pay amount to accrue
    """
    # Determine vacation pay rate
    if years_of_service < 5:
        rate = Decimal("0.04")  # 4%
    elif years_of_service < 10:
        rate = Decimal("0.06")  # 6%
    elif is_federal:
        rate = Decimal("0.08")  # 8% (federal only)
    else:
        rate = Decimal("0.06")  # Most provinces cap at 6%

    return gross_earnings * rate
```

**Example:**
```python
# Employee with 3 years of service earns $2000 this period
gross = Decimal("2000.00")
years = Decimal("3")
vacation_accrual = gross * Decimal("0.04")
# vacation_accrual = 80.00

# Employee's vacation balance increases by $80
```

**Method 2: Annual Calculation**

Calculate vacation pay once per year based on total annual earnings:

```python
def calculate_annual_vacation_pay(
    annual_gross_wages: Decimal,
    years_of_service: Decimal
) -> Decimal:
    """Calculate total annual vacation pay entitlement."""
    if years_of_service < 5:
        return annual_gross_wages * Decimal("0.04")
    else:
        return annual_gross_wages * Decimal("0.06")
```

### Vacation Payout Options

**Option A: Paid Each Period (4% on Paycheck)**

Vacation pay added to each paycheck (common in construction/seasonal):

```python
# Pay period record
gross_regular = Decimal("2000.00")
vacation_pay = gross_regular * Decimal("0.04")  # 80.00
total_gross = gross_regular + vacation_pay  # 2080.00

# Employee doesn't accrue vacation balance; it's paid immediately
```

**Option B: Accrued and Paid When Taken**

Vacation pay accrued but only paid when vacation taken:

```python
# Each pay period: accrue vacation
vacation_balance += gross_regular * Decimal("0.04")

# When employee takes 1 week vacation (bi-weekly employee):
vacation_hours_taken = Decimal("40")  # 1 week = 40 hours
hourly_rate = Decimal("25.00")
vacation_payout = vacation_hours_taken * hourly_rate  # 1000.00
vacation_balance -= vacation_payout
```

**Option C: Lump Sum at Year End**

Pay all accrued vacation as lump sum (less common):

```python
# At end of vacation year:
total_annual_wages = sum(all_pay_periods)
vacation_pay_owing = total_annual_wages * Decimal("0.06")
# Pay as single payment
```

### Vacation Balance Tracking

**Data Model:**

```python
class VacationBalance(BaseModel):
    """Track employee vacation accrual and usage."""
    employee_id: str
    ledger_id: str

    # Balance tracking
    vacation_hours_available: Decimal = Decimal("0")  # Hours accrued
    vacation_hours_used: Decimal = Decimal("0")       # Hours taken
    vacation_pay_balance: Decimal = Decimal("0")      # Dollar value accrued

    # Configuration
    vacation_pay_rate: Decimal  # 0.04 or 0.06 or 0.08
    years_of_service: Decimal

    # Entitlement year
    entitlement_year_start: date
    entitlement_year_end: date

    # History
    last_accrual_date: date
    last_updated: datetime

    @computed_field
    @property
    def vacation_hours_remaining(self) -> Decimal:
        """Hours available minus hours used."""
        return self.vacation_hours_available - self.vacation_hours_used

    @computed_field
    @property
    def vacation_pay_remaining(self) -> Decimal:
        """Vacation pay balance remaining."""
        return self.vacation_pay_balance
```

**Firestore Storage:**
```
/users/{uid}/ledgers/{lid}/employees/{eid}/vacation
└── balance: VacationBalance
└── history/
    ├── 2025-01-15: {accrued: 80.00, reason: "Payroll 2025-01-15"}
    ├── 2025-02-01: {used: -400.00, reason: "1 week vacation"}
    └── 2025-02-15: {accrued: 80.00, reason: "Payroll 2025-02-15"}
```

### Years of Service Calculation

**Standard Calculation:**

```python
from datetime import date
from decimal import Decimal

def calculate_years_of_service(
    hire_date: date,
    calculation_date: date
) -> Decimal:
    """
    Calculate years of service with decimal precision.

    Args:
        hire_date: Employee's hire date
        calculation_date: Date to calculate service years from

    Returns:
        Years of service (e.g., 4.5 years)
    """
    days_employed = (calculation_date - hire_date).days
    years = Decimal(str(days_employed)) / Decimal("365.25")  # Account for leap years
    return years.quantize(Decimal("0.01"))  # 2 decimal places
```

**Rate Transition at 5-Year Mark:**

```python
def get_vacation_pay_rate(
    hire_date: date,
    pay_period_date: date
) -> Decimal:
    """
    Get current vacation pay rate based on years of service.

    Note: Rate increases the moment employee reaches 5 years.
    """
    years = calculate_years_of_service(hire_date, pay_period_date)

    if years >= 5:
        return Decimal("0.06")  # 6%
    else:
        return Decimal("0.04")  # 4%
```

**Special Case: Mid-Year Rate Change**

If employee reaches 5 years mid-year, some provinces require 6% on ALL wages for that year:

```python
def calculate_vacation_pay_with_service_milestone(
    annual_wages: Decimal,
    hire_date: date,
    vacation_year_end: date
) -> Decimal:
    """
    Calculate vacation pay for year where employee reaches 5 years.

    Ontario Example: If employee reaches 5 years on June 1,
    they get 6% on wages for entire vacation year (not just after June 1).
    """
    years_at_year_end = calculate_years_of_service(hire_date, vacation_year_end)

    if years_at_year_end >= 5:
        # Apply 6% to all wages for the year
        return annual_wages * Decimal("0.06")
    else:
        return annual_wages * Decimal("0.04")
```

---

## 🔗 Task 8.3.1: Vacation Pay Integration with Regular Payroll

### Overview

This section clarifies how vacation pay integrates with the regular payroll calculation flow. There are **three common integration methods** used by Canadian employers.

### Integration Method 1: Accrual (Most Common)

**How it works:**
- Vacation pay is **accrued** each pay period but **not paid** immediately
- Employee builds up a vacation balance (in dollars)
- Vacation pay is **only paid when employee takes vacation time**

**Payroll Flow:**
```
1. Calculate gross earnings (regular + overtime)
2. Accrue vacation pay = gross × vacation_rate (4% or 6%)
3. Update vacation balance += vacation_accrued
4. Calculate deductions (CPP, EI, taxes) on gross earnings ONLY
5. Net pay = gross - deductions

Vacation balance grows, but not included in current paycheck
```

**Example:**
```python
# Pay period: Employee earns $2000 gross
gross_earnings = Decimal("2000.00")
vacation_rate = Decimal("0.04")  # 4%

# Accrue vacation
vacation_accrued = gross_earnings * vacation_rate  # $80
vacation_balance += vacation_accrued  # Balance increases by $80

# Deductions calculated on gross (not including vacation)
cpp = calculate_cpp(gross_earnings)
ei = calculate_ei(gross_earnings)
federal_tax = calculate_federal_tax(gross_earnings)
provincial_tax = calculate_provincial_tax(gross_earnings)

net_pay = gross_earnings - (cpp + ei + federal_tax + provincial_tax)
# Net pay does NOT include the $80 vacation accrual
```

**When employee takes vacation:**
```python
# Employee takes 1 week vacation (40 hours)
vacation_hours_taken = Decimal("40")
hourly_rate = Decimal("25.00")

# Pay out vacation from balance
vacation_payout = vacation_hours_taken * hourly_rate  # $1000
vacation_balance -= vacation_payout

# Vacation payout is INCLUDED in gross for this pay period
gross_with_vacation = Decimal("0") + vacation_payout  # No regular earnings
cpp = calculate_cpp(gross_with_vacation)
ei = calculate_ei(gross_with_vacation)
federal_tax = calculate_federal_tax(gross_with_vacation)
provincial_tax = calculate_provincial_tax(gross_with_vacation)

net_pay = gross_with_vacation - deductions
```

**Configuration:**
```python
class EmployeeVacationConfig(BaseModel):
    payout_method: Literal["accrual", "pay_as_you_go", "lump_sum"] = "accrual"
    vacation_rate: Decimal  # 0.04 or 0.06
```

---

### Integration Method 2: Pay-As-You-Go

**How it works:**
- Vacation pay is **added to every paycheck**
- Employee receives vacation pay immediately (4% or 6% added to gross)
- No vacation balance tracking needed
- Common in construction and seasonal industries

**Payroll Flow:**
```
1. Calculate gross earnings (regular + overtime)
2. Calculate vacation pay = gross × vacation_rate
3. Add vacation to gross: total_gross = gross + vacation_pay
4. Calculate deductions on total_gross
5. Net pay = total_gross - deductions

Employee gets vacation pay in every paycheck
```

**Example:**
```python
# Pay period: Employee earns $2000 gross
gross_earnings = Decimal("2000.00")
vacation_rate = Decimal("0.04")

# Add vacation to gross
vacation_pay = gross_earnings * vacation_rate  # $80
total_gross = gross_earnings + vacation_pay  # $2080

# Deductions calculated on TOTAL gross (including vacation)
cpp = calculate_cpp(total_gross)
ei = calculate_ei(total_gross)
federal_tax = calculate_federal_tax(total_gross)
provincial_tax = calculate_provincial_tax(total_gross)

net_pay = total_gross - deductions
# Net pay includes the $80 vacation pay
```

**Important:** When using pay-as-you-go, employee typically **does NOT accrue vacation balance**. The 4%/6% is paid immediately instead.

---

### Integration Method 3: Lump Sum (Less Common)

**How it works:**
- Vacation pay accrued throughout the year
- Paid once per year (e.g., on employee anniversary date or fiscal year-end)
- Balance tracked but not paid until lump sum date

**Payroll Flow:**
```
Regular pay periods (11 months):
1. Calculate gross earnings
2. Accrue vacation (update balance)
3. Calculate deductions on gross ONLY
4. Net pay = gross - deductions

Vacation payout period (1 month):
1. Calculate gross earnings
2. Add accumulated vacation balance to gross
3. Calculate deductions on total
4. Reset vacation balance to $0
5. Net pay = (gross + vacation) - deductions
```

---

### Comparison Table

| Aspect | Accrual | Pay-As-You-Go | Lump Sum |
|--------|---------|---------------|----------|
| **When paid** | When vacation taken | Every paycheck | Once per year |
| **Balance tracking** | ✅ Required | ❌ Not needed | ✅ Required |
| **Gross per period** | Excludes vacation | Includes vacation | Excludes (except payout month) |
| **CPP/EI/Tax** | On gross only | On gross + vacation | On gross (until payout) |
| **Common in** | Most industries | Construction, seasonal | Rare |
| **Employee control** | Can take vacation anytime | Fixed 4%/6% per check | Wait for annual payout |

---

### Holiday Pay Impact on Vacation Calculation

**Important Rule:** In most provinces (especially Ontario), **vacation pay must be included** when calculating holiday pay using the 4-week average formula.

**Ontario Example:**
```python
# Calculating holiday pay for December 25
# Employee's last 4 weeks of wages:
wages_past_4_weeks = Decimal("4000.00")      # Regular wages
vacation_past_4_weeks = Decimal("160.00")    # 4% vacation accrual

# Ontario formula: (wages + vacation) / 20
holiday_pay = (wages_past_4_weeks + vacation_past_4_weeks) / Decimal("20")
# holiday_pay = $4160 / 20 = $208.00
```

**Why this matters:**
- Vacation pay affects holiday pay calculation
- If using "pay-as-you-go" method, employee already received vacation pay in paycheck
- If using "accrual" method, vacation accrual amount is included in calculation base

---

### Implementation in PayrollCalculator

**File: `backend/app/services/payroll/payroll_calculator.py`**

```python
async def calculate_payroll_with_vacation(
    self,
    employee: Employee,
    gross_earnings: Decimal,
    vacation_hours_taken: Decimal = Decimal("0")
) -> PayrollCalculationResult:
    """
    Calculate payroll with vacation pay integration.

    Handles all three vacation payout methods based on employee configuration.
    """
    vacation_config = employee.vacation_config

    if vacation_config.payout_method == "pay_as_you_go":
        # Method 2: Add vacation to gross immediately
        vacation_pay = gross_earnings * vacation_config.vacation_rate
        total_gross = gross_earnings + vacation_pay
        vacation_accrued = Decimal("0")  # No balance tracking

    elif vacation_config.payout_method == "accrual":
        # Method 1: Accrue but don't pay unless vacation taken
        vacation_accrued = gross_earnings * vacation_config.vacation_rate

        if vacation_hours_taken > 0:
            # Employee taking vacation - pay from balance
            hourly_rate = self._get_hourly_rate(employee)
            vacation_payout = vacation_hours_taken * hourly_rate
            total_gross = gross_earnings + vacation_payout
        else:
            # No vacation taken - just accrue
            vacation_payout = Decimal("0")
            total_gross = gross_earnings

    elif vacation_config.payout_method == "lump_sum":
        # Method 3: Accrue and pay once per year
        vacation_accrued = gross_earnings * vacation_config.vacation_rate

        # Check if this is the lump sum payout period
        if self._is_vacation_payout_period(employee):
            vacation_payout = employee.vacation_balance  # Pay entire balance
            total_gross = gross_earnings + vacation_payout
        else:
            vacation_payout = Decimal("0")
            total_gross = gross_earnings

    # Calculate deductions on total gross
    cpp = self._calculate_cpp(total_gross)
    ei = self._calculate_ei(total_gross)
    federal_tax = self._calculate_federal_tax(total_gross)
    provincial_tax = self._calculate_provincial_tax(total_gross)

    net_pay = total_gross - (cpp + ei + federal_tax + provincial_tax)

    return PayrollCalculationResult(
        gross_regular=gross_earnings,
        vacation_accrued=vacation_accrued,
        vacation_paid=vacation_payout,
        total_gross=total_gross,
        cpp_employee=cpp,
        ei_employee=ei,
        federal_tax=federal_tax,
        provincial_tax=provincial_tax,
        net_pay=net_pay
    )
```

---

### Data Model Enhancement

**File: `backend/app/models/employee.py`**

```python
class EmployeeVacationConfig(BaseModel):
    """
    Employee vacation pay configuration
    """
    # Payout method
    payout_method: Literal["accrual", "pay_as_you_go", "lump_sum"] = Field(
        default="accrual",
        description="How vacation pay is distributed to employee"
    )

    # Vacation rate (determined by years of service)
    vacation_rate: Decimal = Field(
        default=Decimal("0.04"),
        description="Vacation pay rate (4%, 6%, or 8%)"
    )

    # Lump sum configuration (if payout_method = "lump_sum")
    lump_sum_month: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Month to pay lump sum (1=Jan, 12=Dec)"
    )

    # For tracking (accrual and lump_sum methods only)
    vacation_balance: Decimal = Field(
        default=Decimal("0"),
        decimal_places=2,
        description="Current vacation pay balance"
    )
```

---

### Testing Integration Methods

**File: `backend/tests/test_vacation_integration.py`**

```python
import pytest
from decimal import Decimal

@pytest.mark.asyncio
async def test_accrual_method():
    """Test accrual method - vacation not included in gross"""
    employee = create_test_employee(payout_method="accrual")

    result = await payroll_calculator.calculate_payroll_with_vacation(
        employee=employee,
        gross_earnings=Decimal("2000.00"),
        vacation_hours_taken=Decimal("0")
    )

    # Vacation accrued but not paid
    assert result.vacation_accrued == Decimal("80.00")  # 4% of $2000
    assert result.vacation_paid == Decimal("0")
    assert result.total_gross == Decimal("2000.00")  # Gross unchanged

@pytest.mark.asyncio
async def test_pay_as_you_go_method():
    """Test pay-as-you-go - vacation added to gross"""
    employee = create_test_employee(payout_method="pay_as_you_go")

    result = await payroll_calculator.calculate_payroll_with_vacation(
        employee=employee,
        gross_earnings=Decimal("2000.00"),
        vacation_hours_taken=Decimal("0")
    )

    # Vacation paid immediately
    assert result.vacation_accrued == Decimal("0")  # No balance tracking
    assert result.vacation_paid == Decimal("80.00")  # 4% of $2000
    assert result.total_gross == Decimal("2080.00")  # Includes vacation
```

---

## 🗓️ Task 8.3.2: Vacation & Sick Leave Year-End Handling

### Overview

Year-end handling rules for vacation and sick leave in Canadian payroll. Unlike some jurisdictions, Canada has **no mandatory year-end payout** for vacation - employers choose their policy.

### Vacation Pay Year-End Rules

#### Federal & Provincial Overview

**Key Point**: No mandatory payout at year-end. Employers choose one of three policies:

| Policy | Description | Implementation |
|--------|-------------|----------------|
| **Carry-Over** | Balance rolls to next year | Default, no action needed |
| **Use-It-Or-Lose-It** | Unused balance forfeited | Zero balance on Jan 1 |
| **Payout** | Cash out unused balance | Payout before year-end |

#### Provincial Deadlines (Vacation Must Be Taken By)

Different provinces have different deadlines for when vacation must be taken:

| Province | Deadline | Reference |
|----------|----------|-----------|
| Ontario | 10 months after entitlement year ends | ESA s.35 |
| British Columbia | 12 months after qualifying period | ESA s.58 |
| Federal | 10 months after completion of year | Canada Labour Code |
| Alberta | 12 months after earning period | ESC s.36 |
| Saskatchewan | 12 months after becoming entitled | ESA s.2-26 |

**Example (Ontario)**:
- Employee's vacation year: Jan 1 - Dec 31, 2025
- Vacation must be taken by: Oct 31, 2026 (10 months after Dec 31, 2025)

#### T4 Reporting

Vacation payouts are included in **Box 14 (Employment Income)** in the year paid:
- If paid out in December 2025 → Include in 2025 T4
- If carried over and paid in January 2026 → Include in 2026 T4
- Subject to all normal deductions (CPP, EI, Tax)

#### Vacation Balance Payout (Anytime)

Employees using the **accrual** method can request to cash out their vacation balance at any time (not just year-end). Payout reasons include:

| Reason | Code | Use Case |
|--------|------|----------|
| **Scheduled** | `scheduled` | Planned year-end or anniversary payout |
| **Cashout Request** | `cashout_request` | Employee requests partial cashout mid-year |
| **Termination** | `termination` | Full balance on employment end |

**Note**: Only employees using the `accrual` payout method have a vacation balance. Employees using `pay_as_you_go` receive vacation pay with each paycheck and have no balance to cash out.

### Sick Leave Year-End Rules

#### Provincial Statutory Sick Leave (2025)

**Critical Point**: Provincial statutory sick leave does **NOT** accumulate year-over-year and does **NOT** require payout on termination.

| Province | Paid Days/Year | Accumulation | Payout Required | Notes |
|----------|----------------|--------------|-----------------|-------|
| BC | 5 days | No | No | Resets each year after 90 days employment |
| Ontario | 0 paid (3 unpaid) | No | No | ESA only provides unpaid (IDEL) days |
| Alberta | 0 days | N/A | N/A | No statutory sick leave |
| Federal | 10 days | Max 10 carry | No | Max 10 days at any time, no payout on exit |
| Saskatchewan | 0 days | N/A | N/A | No statutory sick leave |

#### Employer-Provided Sick Leave

If employer offers sick leave beyond statutory minimums:
- **Accumulation**: At employer's discretion
- **Payout**: At employer's discretion (most employers do NOT pay out unused sick leave)
- **Carryover**: At employer's discretion

**Recommendation**: Do NOT implement sick leave payout functionality. Standard practice is that unused sick leave has no cash value.

### Data Model Enhancement

Add `year_end_policy` to VacationConfig:

```python
class VacationConfig(BaseModel):
    """Vacation pay configuration for employee"""
    payout_method: Literal["accrual", "pay_as_you_go", "lump_sum"] = "accrual"
    vacation_rate: Decimal = Decimal("0.04")  # 4%, 6%, or 8%

    # Year-end handling (only relevant for accrual method)
    year_end_policy: Literal["carry_over", "use_it_or_lose_it", "payout"] = "carry_over"
    max_carryover_hours: Optional[Decimal] = None  # None = unlimited carryover
```

### References

- Ontario ESA: https://www.ontario.ca/document/your-guide-employment-standards-act-0/vacation
- BC Employment Standards: https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/time-off/vacation
- Canada Labour Code: https://laws-lois.justice.gc.ca/eng/acts/L-2/
- CRA T4 Guide: https://www.canada.ca/en/revenue-agency/services/forms-publications/publications/rc4120.html

---

## 📁 Task 8.4: Configuration Architecture

### Directory Structure

```
backend/config/holidays/
├── 2025/
│   ├── AB_holidays_2025.json
│   ├── BC_holidays_2025.json
│   ├── MB_holidays_2025.json
│   ├── NB_holidays_2025.json
│   ├── NL_holidays_2025.json
│   ├── NS_holidays_2025.json
│   ├── NT_holidays_2025.json
│   ├── NU_holidays_2025.json
│   ├── ON_holidays_2025.json
│   ├── PE_holidays_2025.json
│   ├── SK_holidays_2025.json
│   └── YT_holidays_2025.json
├── 2026/
│   └── [same 12 files]
└── 2027/
    └── [same 12 files]
```

### JSON Schema

**File: `backend/config/holidays/2025/ON_holidays_2025.json`**

```json
{
  "metadata": {
    "province_code": "ON",
    "province_name": "Ontario",
    "year": 2025,
    "source": "Ontario Employment Standards Act",
    "last_updated": "2025-01-01"
  },

  "statutory_holidays": [
    {
      "date": "2025-01-01",
      "name": "New Year's Day",
      "name_fr": "Jour de l'An",
      "is_moveable": false,
      "is_mandatory": true
    },
    {
      "date": "2025-02-17",
      "name": "Family Day",
      "name_fr": "Jour de la famille",
      "is_moveable": true,
      "calculation_rule": "3rd Monday in February",
      "is_mandatory": true
    },
    {
      "date": "2025-04-18",
      "name": "Good Friday",
      "name_fr": "Vendredi saint",
      "is_moveable": true,
      "calculation_rule": "Easter Sunday - 2 days",
      "is_mandatory": true
    },
    {
      "date": "2025-05-19",
      "name": "Victoria Day",
      "name_fr": "Fête de la Reine",
      "is_moveable": true,
      "calculation_rule": "Last Monday before May 25",
      "is_mandatory": true
    },
    {
      "date": "2025-07-01",
      "name": "Canada Day",
      "name_fr": "Fête du Canada",
      "is_moveable": false,
      "is_mandatory": true
    },
    {
      "date": "2025-09-01",
      "name": "Labour Day",
      "name_fr": "Fête du Travail",
      "is_moveable": true,
      "calculation_rule": "1st Monday in September",
      "is_mandatory": true
    },
    {
      "date": "2025-10-13",
      "name": "Thanksgiving",
      "name_fr": "Action de grâce",
      "is_moveable": true,
      "calculation_rule": "2nd Monday in October",
      "is_mandatory": true
    },
    {
      "date": "2025-12-25",
      "name": "Christmas Day",
      "name_fr": "Noël",
      "is_moveable": false,
      "is_mandatory": true
    },
    {
      "date": "2025-12-26",
      "name": "Boxing Day",
      "name_fr": "Lendemain de Noël",
      "is_moveable": false,
      "is_mandatory": true
    }
  ],

  "optional_holidays": [
    {
      "date": "2025-04-21",
      "name": "Easter Monday",
      "name_fr": "Lundi de Pâques",
      "is_moveable": true,
      "calculation_rule": "Easter Sunday + 1 day",
      "is_mandatory": false,
      "note": "Common in some industries but not statutory"
    }
  ],

  "holiday_pay_rules": {
    "calculation_method": "ontario_four_week_formula",
    "formula": "(wages_past_4_weeks + vacation_pay_past_4_weeks) / 20",
    "eligibility_days": 30,
    "requires_surrounding_shifts": true,
    "premium_rate_if_worked": "1.5",
    "reference_url": "https://www.ontario.ca/document/your-guide-employment-standards-act-0/public-holidays"
  },

  "vacation_pay_rules": {
    "rates": [
      {
        "min_years": 0,
        "max_years": 5,
        "rate": "0.04",
        "vacation_weeks": 2
      },
      {
        "min_years": 5,
        "max_years": null,
        "rate": "0.06",
        "vacation_weeks": 3
      }
    ],
    "rate_change_applies_to_full_year": true,
    "reference_url": "https://www.ontario.ca/document/your-guide-employment-standards-act-0/vacation"
  }
}
```

**File: `backend/config/holidays/2025/BC_holidays_2025.json`**

```json
{
  "metadata": {
    "province_code": "BC",
    "province_name": "British Columbia",
    "year": 2025,
    "source": "BC Employment Standards Act",
    "last_updated": "2025-01-01"
  },

  "statutory_holidays": [
    {
      "date": "2025-01-01",
      "name": "New Year's Day",
      "is_moveable": false,
      "is_mandatory": true
    },
    {
      "date": "2025-02-17",
      "name": "Family Day",
      "is_moveable": true,
      "calculation_rule": "3rd Monday in February",
      "is_mandatory": true
    },
    {
      "date": "2025-04-18",
      "name": "Good Friday",
      "is_moveable": true,
      "calculation_rule": "Easter Sunday - 2 days",
      "is_mandatory": true
    },
    {
      "date": "2025-05-19",
      "name": "Victoria Day",
      "is_moveable": true,
      "calculation_rule": "Last Monday before May 25",
      "is_mandatory": true
    },
    {
      "date": "2025-07-01",
      "name": "Canada Day",
      "is_moveable": false,
      "is_mandatory": true
    },
    {
      "date": "2025-08-04",
      "name": "British Columbia Day",
      "is_moveable": true,
      "calculation_rule": "1st Monday in August",
      "is_mandatory": true
    },
    {
      "date": "2025-09-01",
      "name": "Labour Day",
      "is_moveable": true,
      "calculation_rule": "1st Monday in September",
      "is_mandatory": true
    },
    {
      "date": "2025-09-30",
      "name": "National Day for Truth and Reconciliation",
      "is_moveable": false,
      "is_mandatory": true,
      "note": "Added as BC statutory holiday in 2023"
    },
    {
      "date": "2025-10-13",
      "name": "Thanksgiving",
      "is_moveable": true,
      "calculation_rule": "2nd Monday in October",
      "is_mandatory": true
    },
    {
      "date": "2025-11-11",
      "name": "Remembrance Day",
      "is_moveable": false,
      "is_mandatory": true
    },
    {
      "date": "2025-12-25",
      "name": "Christmas Day",
      "is_moveable": false,
      "is_mandatory": true
    }
  ],

  "optional_holidays": [],

  "holiday_pay_rules": {
    "calculation_method": "average_day_pay",
    "formula_hourly": "average_daily_hours * hourly_rate",
    "formula_salaried": "annual_salary / pay_periods / work_days_per_period",
    "eligibility_days": 30,
    "requires_surrounding_shifts": true,
    "premium_rate_if_worked": "1.5",
    "reference_url": "https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/statutory-holidays"
  },

  "vacation_pay_rules": {
    "rates": [
      {
        "min_years": 0,
        "max_years": 5,
        "rate": "0.04",
        "vacation_weeks": 2
      },
      {
        "min_years": 5,
        "max_years": null,
        "rate": "0.06",
        "vacation_weeks": 3
      }
    ],
    "rate_change_applies_to_full_year": false,
    "reference_url": "https://www2.gov.bc.ca/gov/content/employment-business/employment-standards-advice/employment-standards/forms-resources/igm/esa-part-7-section-58"
  }
}
```

### Python Configuration Loader

**File: `backend/app/services/payroll/holiday_config_loader.py`**

```python
from decimal import Decimal
from pathlib import Path
from datetime import date
from typing import Dict, List, Optional, Any
import json
from pydantic import BaseModel


class HolidayDefinition(BaseModel):
    """Statutory holiday definition."""
    date: date
    name: str
    name_fr: Optional[str] = None
    is_moveable: bool
    calculation_rule: Optional[str] = None
    is_mandatory: bool
    note: Optional[str] = None


class HolidayPayRules(BaseModel):
    """Holiday pay calculation rules."""
    calculation_method: str
    formula: Optional[str] = None
    formula_hourly: Optional[str] = None
    formula_salaried: Optional[str] = None
    eligibility_days: int
    requires_surrounding_shifts: bool
    premium_rate_if_worked: Decimal
    reference_url: str


class VacationPayRate(BaseModel):
    """Vacation pay rate definition."""
    min_years: int
    max_years: Optional[int]
    rate: Decimal
    vacation_weeks: int


class VacationPayRules(BaseModel):
    """Vacation pay rules."""
    rates: List[VacationPayRate]
    rate_change_applies_to_full_year: bool
    reference_url: str


class ProvinceHolidayConfig(BaseModel):
    """Complete holiday configuration for a province."""
    province_code: str
    province_name: str
    year: int
    source: str
    last_updated: date

    statutory_holidays: List[HolidayDefinition]
    optional_holidays: List[HolidayDefinition]
    holiday_pay_rules: HolidayPayRules
    vacation_pay_rules: VacationPayRules

    def get_holidays_in_date_range(
        self,
        start_date: date,
        end_date: date,
        include_optional: bool = False
    ) -> List[HolidayDefinition]:
        """Get all holidays within date range."""
        holidays = self.statutory_holidays[:]
        if include_optional:
            holidays.extend(self.optional_holidays)

        return [
            h for h in holidays
            if start_date <= h.date <= end_date
        ]

    def is_statutory_holiday(self, check_date: date) -> bool:
        """Check if date is a statutory holiday."""
        return any(h.date == check_date for h in self.statutory_holidays)

    def get_holiday_by_date(self, check_date: date) -> Optional[HolidayDefinition]:
        """Get holiday definition for specific date."""
        for h in self.statutory_holidays:
            if h.date == check_date:
                return h
        for h in self.optional_holidays:
            if h.date == check_date:
                return h
        return None


class HolidayConfigLoader:
    """Load and manage holiday configurations."""

    CONFIG_DIR = Path(__file__).parent.parent.parent.parent / "config" / "holidays"

    # Cache loaded configurations
    _cache: Dict[str, ProvinceHolidayConfig] = {}

    @classmethod
    def load_province_config(
        cls,
        province_code: str,
        year: int
    ) -> ProvinceHolidayConfig:
        """
        Load holiday configuration for province and year.

        Args:
            province_code: Two-letter province code (e.g., "ON", "BC")
            year: Calendar year (e.g., 2025)

        Returns:
            ProvinceHolidayConfig object

        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        cache_key = f"{province_code}_{year}"

        # Check cache
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # Load from file
        config_file = cls.CONFIG_DIR / str(year) / f"{province_code}_holidays_{year}.json"

        if not config_file.exists():
            raise FileNotFoundError(
                f"Holiday configuration not found: {config_file}\n"
                f"Province: {province_code}, Year: {year}"
            )

        with open(config_file, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        # Parse configuration
        config = cls._parse_config(raw_data)

        # Cache and return
        cls._cache[cache_key] = config
        return config

    @classmethod
    def _parse_config(cls, raw_data: Dict[str, Any]) -> ProvinceHolidayConfig:
        """Parse JSON data into ProvinceHolidayConfig."""
        metadata = raw_data["metadata"]

        # Convert Decimal strings
        holiday_pay_rules = raw_data["holiday_pay_rules"]
        holiday_pay_rules["premium_rate_if_worked"] = Decimal(
            holiday_pay_rules["premium_rate_if_worked"]
        )

        # Convert vacation pay rates
        vacation_rules = raw_data["vacation_pay_rules"]
        for rate in vacation_rules["rates"]:
            rate["rate"] = Decimal(rate["rate"])

        return ProvinceHolidayConfig(
            province_code=metadata["province_code"],
            province_name=metadata["province_name"],
            year=metadata["year"],
            source=metadata["source"],
            last_updated=date.fromisoformat(metadata["last_updated"]),
            statutory_holidays=[
                HolidayDefinition(**h) for h in raw_data["statutory_holidays"]
            ],
            optional_holidays=[
                HolidayDefinition(**h) for h in raw_data.get("optional_holidays", [])
            ],
            holiday_pay_rules=HolidayPayRules(**holiday_pay_rules),
            vacation_pay_rules=VacationPayRules(**vacation_rules)
        )

    @classmethod
    def clear_cache(cls):
        """Clear configuration cache (useful for testing)."""
        cls._cache.clear()


# Example usage
if __name__ == "__main__":
    # Load Ontario 2025 holidays
    ontario_config = HolidayConfigLoader.load_province_config("ON", 2025)

    print(f"Province: {ontario_config.province_name}")
    print(f"Statutory Holidays: {len(ontario_config.statutory_holidays)}")

    # Check if specific date is holiday
    christmas = date(2025, 12, 25)
    if ontario_config.is_statutory_holiday(christmas):
        holiday = ontario_config.get_holiday_by_date(christmas)
        print(f"{holiday.name} is a statutory holiday")

    # Get holidays in Q1 2025
    q1_holidays = ontario_config.get_holidays_in_date_range(
        date(2025, 1, 1),
        date(2025, 3, 31)
    )
    print(f"Q1 2025 holidays: {len(q1_holidays)}")
```

---

## 🧮 Task 8.5: Integration with Payroll Calculator

### Enhanced PayrollRecord Model

**File: `backend/app/models/payroll.py`**

Add fields for holiday and vacation pay:

```python
class PayrollRecord(BaseModel):
    id: str
    employee_id: str
    pay_period_start: date
    pay_period_end: date
    pay_date: date

    # Earnings
    gross_regular: Decimal
    gross_overtime: Decimal = Decimal("0")

    # NEW: Holiday pay
    holiday_hours: Decimal = Decimal("0")          # Hours for holidays in period
    holiday_pay: Decimal = Decimal("0")            # Holiday pay amount
    holiday_premium_hours: Decimal = Decimal("0")  # Hours worked on holiday
    holiday_premium_pay: Decimal = Decimal("0")    # Premium for working holiday

    # NEW: Vacation pay
    vacation_hours_taken: Decimal = Decimal("0")   # Vacation hours taken this period
    vacation_pay_accrued: Decimal = Decimal("0")   # Vacation $ accrued this period
    vacation_pay_paid: Decimal = Decimal("0")      # Vacation $ paid out this period

    @computed_field
    @property
    def gross_earnings(self) -> Decimal:
        """Total gross including holidays and vacation."""
        return (
            self.gross_regular +
            self.gross_overtime +
            self.holiday_pay +
            self.holiday_premium_pay +
            self.vacation_pay_paid
        )

    # ... rest of existing fields (CPP, EI, taxes, etc.)
```

### Holiday Pay Integration

**File: `backend/app/services/payroll/payroll_calculator.py`**

Enhance calculator to include holiday pay:

```python
from .holiday_service import HolidayService
from .vacation_service import VacationService

class PayrollCalculator:
    """Enhanced payroll calculator with holiday and vacation support."""

    def __init__(self):
        self.holiday_service = HolidayService()
        self.vacation_service = VacationService()

    async def calculate_payroll(
        self,
        employee: Employee,
        pay_period_start: date,
        pay_period_end: date,
        gross_regular: Decimal,
        gross_overtime: Decimal = Decimal("0"),
        vacation_hours_taken: Decimal = Decimal("0"),
        hours_worked_on_holidays: Dict[date, Decimal] = None
    ) -> PayrollCalculationResult:
        """
        Calculate complete payroll including holidays and vacation.

        Args:
            employee: Employee record
            pay_period_start: Pay period start date
            pay_period_end: Pay period end date
            gross_regular: Regular gross earnings
            gross_overtime: Overtime earnings
            vacation_hours_taken: Vacation hours taken this period
            hours_worked_on_holidays: Dict of {holiday_date: hours_worked}

        Returns:
            Complete payroll calculation result
        """
        province = employee.province_of_employment
        year = pay_period_start.year

        # Step 1: Calculate holiday pay
        holiday_result = await self.holiday_service.calculate_holiday_pay(
            employee=employee,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            gross_regular=gross_regular,
            hours_worked_on_holidays=hours_worked_on_holidays or {}
        )

        # Step 2: Calculate vacation pay
        vacation_result = await self.vacation_service.calculate_vacation_pay(
            employee=employee,
            gross_earnings=gross_regular + gross_overtime,
            vacation_hours_taken=vacation_hours_taken
        )

        # Step 3: Calculate total gross
        total_gross = (
            gross_regular +
            gross_overtime +
            holiday_result.holiday_pay +
            holiday_result.premium_pay +
            vacation_result.vacation_pay_paid
        )

        # Step 4: Calculate deductions (CPP, EI, taxes) on total gross
        cpp = self._calculate_cpp(total_gross, employee)
        ei = self._calculate_ei(total_gross, employee)
        federal_tax = self._calculate_federal_tax(total_gross, employee)
        provincial_tax = self._calculate_provincial_tax(total_gross, employee, province)

        # Step 5: Build result
        return PayrollCalculationResult(
            gross_regular=gross_regular,
            gross_overtime=gross_overtime,
            holiday_pay=holiday_result.holiday_pay,
            holiday_premium_pay=holiday_result.premium_pay,
            vacation_pay_accrued=vacation_result.vacation_accrued,
            vacation_pay_paid=vacation_result.vacation_pay_paid,
            total_gross=total_gross,
            cpp_employee=cpp,
            ei_employee=ei,
            federal_tax=federal_tax,
            provincial_tax=provincial_tax,
            net_pay=total_gross - (cpp + ei + federal_tax + provincial_tax),
            calculation_details={
                "holidays_in_period": holiday_result.holidays,
                "vacation_balance_remaining": vacation_result.balance_remaining
            }
        )
```

### HolidayService Implementation

**File: `backend/app/services/payroll/holiday_service.py`**

```python
from decimal import Decimal
from datetime import date
from typing import Dict, List
from pydantic import BaseModel

from app.models.payroll import Employee
from .holiday_config_loader import HolidayConfigLoader, HolidayDefinition


class HolidayPayResult(BaseModel):
    """Result of holiday pay calculation."""
    holidays: List[HolidayDefinition]  # Holidays in pay period
    holiday_hours: Decimal              # Total holiday hours
    holiday_pay: Decimal                # Regular holiday pay
    premium_hours: Decimal              # Hours worked on holidays
    premium_pay: Decimal                # Premium pay for working holidays


class HolidayService:
    """Service for holiday pay calculations."""

    def __init__(self):
        self.config_loader = HolidayConfigLoader()

    async def calculate_holiday_pay(
        self,
        employee: Employee,
        pay_period_start: date,
        pay_period_end: date,
        gross_regular: Decimal,
        hours_worked_on_holidays: Dict[date, Decimal]
    ) -> HolidayPayResult:
        """
        Calculate holiday pay for pay period.

        Args:
            employee: Employee record
            pay_period_start: Pay period start
            pay_period_end: Pay period end
            gross_regular: Regular gross earnings (for calculation base)
            hours_worked_on_holidays: {holiday_date: hours_worked}

        Returns:
            Holiday pay calculation result
        """
        province = employee.province_of_employment.value
        year = pay_period_start.year

        # Load holiday configuration
        config = self.config_loader.load_province_config(province, year)

        # Find holidays in pay period
        holidays = config.get_holidays_in_date_range(
            pay_period_start,
            pay_period_end,
            include_optional=False  # Only statutory holidays
        )

        if not holidays:
            # No holidays in this pay period
            return HolidayPayResult(
                holidays=[],
                holiday_hours=Decimal("0"),
                holiday_pay=Decimal("0"),
                premium_hours=Decimal("0"),
                premium_pay=Decimal("0")
            )

        # Calculate holiday pay based on province rules
        method = config.holiday_pay_rules.calculation_method

        if method == "ontario_four_week_formula":
            daily_holiday_pay = self._calculate_ontario_holiday_pay(employee, gross_regular)
        elif method == "average_day_pay":
            daily_holiday_pay = self._calculate_bc_holiday_pay(employee)
        else:
            # Default: average day's pay
            daily_holiday_pay = self._calculate_average_day_pay(employee, gross_regular)

        # Total holiday pay (one day per holiday)
        holiday_hours = Decimal(str(len(holidays) * 8))  # Assume 8-hour days
        holiday_pay = daily_holiday_pay * len(holidays)

        # Calculate premium pay if worked on holidays
        premium_rate = config.holiday_pay_rules.premium_rate_if_worked
        premium_hours = sum(hours_worked_on_holidays.values(), Decimal("0"))
        premium_pay = Decimal("0")

        if premium_hours > 0:
            hourly_rate = self._get_hourly_rate(employee)
            premium_pay = premium_hours * hourly_rate * premium_rate

        return HolidayPayResult(
            holidays=holidays,
            holiday_hours=holiday_hours,
            holiday_pay=holiday_pay,
            premium_hours=premium_hours,
            premium_pay=premium_pay
        )

    def _calculate_ontario_holiday_pay(
        self,
        employee: Employee,
        gross_regular: Decimal
    ) -> Decimal:
        """Ontario: (wages in 4 weeks + vacation) / 20."""
        # Simplified: use current period gross as proxy
        # In production, would fetch actual 4-week history
        wages_4_weeks = gross_regular * 2  # Bi-weekly × 2 = 4 weeks
        vacation_4_weeks = wages_4_weeks * Decimal("0.04")
        return (wages_4_weeks + vacation_4_weeks) / Decimal("20")

    def _calculate_bc_holiday_pay(self, employee: Employee) -> Decimal:
        """BC: Average day's pay."""
        if employee.annual_salary:
            # Salaried: annual / periods / days per period
            pay_periods = self._get_pay_periods_per_year(employee.pay_frequency)
            return employee.annual_salary / pay_periods / Decimal("10")
        elif employee.hourly_rate:
            # Hourly: rate × average hours per day
            return employee.hourly_rate * Decimal("8")
        else:
            return Decimal("0")

    def _calculate_average_day_pay(
        self,
        employee: Employee,
        gross_regular: Decimal
    ) -> Decimal:
        """Generic: gross / work days in period."""
        days_in_period = self._get_work_days_per_period(employee.pay_frequency)
        return gross_regular / Decimal(str(days_in_period))

    def _get_hourly_rate(self, employee: Employee) -> Decimal:
        """Get employee's hourly rate."""
        if employee.hourly_rate:
            return employee.hourly_rate
        elif employee.annual_salary:
            # Convert salary to hourly
            annual_hours = Decimal("2080")  # 52 weeks × 40 hours
            return employee.annual_salary / annual_hours
        return Decimal("0")

    def _get_pay_periods_per_year(self, frequency) -> int:
        """Get number of pay periods per year."""
        frequency_map = {
            "weekly": 52,
            "bi_weekly": 26,
            "semi_monthly": 24,
            "monthly": 12
        }
        return frequency_map.get(frequency.value, 26)

    def _get_work_days_per_period(self, frequency) -> int:
        """Get work days per pay period."""
        days_map = {
            "weekly": 5,
            "bi_weekly": 10,
            "semi_monthly": 10,
            "monthly": 21
        }
        return days_map.get(frequency.value, 10)
```

### VacationService Implementation

**File: `backend/app/services/payroll/vacation_service.py`**

```python
from decimal import Decimal
from datetime import date
from pydantic import BaseModel

from app.models.payroll import Employee
from .holiday_config_loader import HolidayConfigLoader


class VacationPayResult(BaseModel):
    """Result of vacation pay calculation."""
    vacation_accrued: Decimal       # Vacation $ accrued this period
    vacation_pay_paid: Decimal      # Vacation $ paid out this period
    vacation_rate: Decimal          # Rate used (0.04 or 0.06)
    balance_remaining: Decimal      # Balance after this transaction
    years_of_service: Decimal       # Employee's years of service


class VacationService:
    """Service for vacation pay calculations."""

    def __init__(self):
        self.config_loader = HolidayConfigLoader()

    async def calculate_vacation_pay(
        self,
        employee: Employee,
        gross_earnings: Decimal,
        vacation_hours_taken: Decimal = Decimal("0"),
        current_balance: Decimal = Decimal("0")
    ) -> VacationPayResult:
        """
        Calculate vacation pay for pay period.

        Args:
            employee: Employee record
            gross_earnings: Gross earnings this period (regular + overtime)
            vacation_hours_taken: Vacation hours taken this period
            current_balance: Current vacation pay balance

        Returns:
            Vacation pay calculation result
        """
        province = employee.province_of_employment.value
        year = date.today().year

        # Load vacation rules
        config = self.config_loader.load_province_config(province, year)

        # Calculate years of service
        years_of_service = self._calculate_years_of_service(
            employee.hire_date,
            date.today()
        )

        # Get vacation pay rate
        vacation_rate = self._get_vacation_rate(
            config.vacation_pay_rules.rates,
            years_of_service
        )

        # Calculate accrual for this period
        vacation_accrued = gross_earnings * vacation_rate

        # Calculate payout if vacation taken
        vacation_pay_paid = Decimal("0")
        if vacation_hours_taken > 0:
            hourly_rate = self._get_hourly_rate(employee)
            vacation_pay_paid = vacation_hours_taken * hourly_rate

        # Update balance
        new_balance = current_balance + vacation_accrued - vacation_pay_paid

        return VacationPayResult(
            vacation_accrued=vacation_accrued,
            vacation_pay_paid=vacation_pay_paid,
            vacation_rate=vacation_rate,
            balance_remaining=new_balance,
            years_of_service=years_of_service
        )

    def _calculate_years_of_service(
        self,
        hire_date: date,
        calculation_date: date
    ) -> Decimal:
        """Calculate years of service with decimal precision."""
        days = (calculation_date - hire_date).days
        years = Decimal(str(days)) / Decimal("365.25")
        return years.quantize(Decimal("0.01"))

    def _get_vacation_rate(self, rates: list, years: Decimal) -> Decimal:
        """Get vacation pay rate based on years of service."""
        for rate_config in rates:
            min_years = Decimal(str(rate_config.min_years))
            max_years = (
                Decimal(str(rate_config.max_years))
                if rate_config.max_years is not None
                else Decimal("999")
            )

            if min_years <= years < max_years:
                return rate_config.rate

        # Default to last rate
        return rates[-1].rate

    def _get_hourly_rate(self, employee: Employee) -> Decimal:
        """Get employee's hourly rate."""
        if employee.hourly_rate:
            return employee.hourly_rate
        elif employee.annual_salary:
            annual_hours = Decimal("2080")
            return employee.annual_salary / annual_hours
        return Decimal("0")
```

---

## 🎨 Task 8.6: UI Enhancements

### Holiday Indicators in Payroll Table

Add visual indicators for pay periods containing holidays:

**File: `docs/planning/payroll/07_ui_design.md`** (Enhancement)

```html
<!-- Pay Period Selector with Holiday Indicator -->
<div class="flex items-center gap-4">
  <button on:click={previousPeriod}>
    <Icon name="chevron-left" />
  </button>

  <div class="flex flex-col items-center">
    <span class="text-lg font-semibold">
      {formatDateRange(currentPayPeriod.start, currentPayPeriod.end)}
    </span>

    {#if holidaysInPeriod.length > 0}
      <span class="text-xs text-primary flex items-center gap-1">
        <Icon name="gift" size={12} />
        {holidaysInPeriod.length} holiday{holidaysInPeriod.length > 1 ? 's' : ''}
        ({holidaysInPeriod.map(h => h.name).join(', ')})
      </span>
    {/if}
  </div>

  <button on:click={nextPeriod}>
    <Icon name="chevron-right" />
  </button>
</div>
```

### Vacation Balance Display

Show employee vacation balance in detail panel:

```html
<!-- Employee Detail Panel - Vacation Section -->
<div class="p-4 border-b">
  <h3 class="font-semibold mb-2">Vacation Balance</h3>

  <div class="grid grid-cols-2 gap-4">
    <div>
      <span class="text-sm text-gray-600">Hours Available</span>
      <p class="text-lg font-semibold">{employee.vacationHoursAvailable}h</p>
    </div>

    <div>
      <span class="text-sm text-gray-600">$ Balance</span>
      <p class="text-lg font-semibold">${formatMoney(employee.vacationPayBalance)}</p>
    </div>

    <div>
      <span class="text-sm text-gray-600">Accrual Rate</span>
      <p class="text-lg font-semibold">{employee.vacationRate * 100}%</p>
    </div>

    <div>
      <span class="text-sm text-gray-600">Years of Service</span>
      <p class="text-lg font-semibold">{employee.yearsOfService.toFixed(1)} years</p>
    </div>
  </div>
</div>
```

### Payroll Record with Holiday/Vacation Details

Enhanced payroll row showing holiday and vacation pay:

```html
<tr class="hover:bg-surface-100">
  <td class="p-4">
    {employee.firstName} {employee.lastName}
  </td>

  <td class="text-right p-4">
    {#if record.holidayPay > 0}
      <div class="flex flex-col">
        <span>${formatMoney(record.grossRegular + record.holidayPay)}</span>
        <span class="text-xs text-primary">
          +${formatMoney(record.holidayPay)} holiday
        </span>
      </div>
    {:else}
      ${formatMoney(record.grossRegular)}
    {/if}
  </td>

  <!-- ... other columns ... -->

  <td class="text-right p-4 font-semibold">
    ${formatMoney(record.netPay)}
  </td>

  <td class="p-4">
    <div class="flex gap-2">
      {#if record.holidayPay > 0}
        <span class="px-2 py-1 bg-primary-100 text-primary-700 rounded text-xs">
          Holiday
        </span>
      {/if}

      {#if record.vacationHoursTaken > 0}
        <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">
          Vacation
        </span>
      {/if}

      <button class="btn-icon" on:click={() => openPaystub(record)}>
        <Icon name="document" />
      </button>
    </div>
  </td>
</tr>
```

---

## ✅ Validation & Testing

### Holiday Calendar Validation

```python
# backend/tests/test_holiday_config.py
import pytest
from datetime import date
from backend.app.services.payroll.holiday_config_loader import HolidayConfigLoader


def test_ontario_2025_holidays():
    """Test Ontario 2025 holiday configuration."""
    config = HolidayConfigLoader.load_province_config("ON", 2025)

    # Should have 9 statutory holidays
    assert len(config.statutory_holidays) == 9

    # Check specific dates
    assert config.is_statutory_holiday(date(2025, 1, 1))   # New Year's
    assert config.is_statutory_holiday(date(2025, 12, 25))  # Christmas
    assert config.is_statutory_holiday(date(2025, 12, 26))  # Boxing Day

    # Check non-holiday
    assert not config.is_statutory_holiday(date(2025, 3, 17))  # Random day


def test_bc_2025_holidays():
    """Test BC 2025 holiday configuration."""
    config = HolidayConfigLoader.load_province_config("BC", 2025)

    # BC has 11 statutory holidays
    assert len(config.statutory_holidays) == 11

    # BC has Remembrance Day (Ontario doesn't)
    assert config.is_statutory_holiday(date(2025, 11, 11))

    # BC doesn't have Boxing Day (Ontario does)
    assert not config.is_statutory_holiday(date(2025, 12, 26))


def test_all_provinces_have_configs():
    """Test that all 12 provinces have 2025 configurations."""
    provinces = ["AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "SK", "YT"]

    for province in provinces:
        config = HolidayConfigLoader.load_province_config(province, 2025)
        assert config.province_code == province
        assert len(config.statutory_holidays) >= 6  # NL has minimum 6
```

### Holiday Pay Calculation Tests

```python
# backend/tests/test_holiday_service.py
import pytest
from decimal import Decimal
from datetime import date

from backend.app.services.payroll.holiday_service import HolidayService
from backend.app.models.payroll import Employee, Province, PayPeriodFrequency


@pytest.fixture
def ontario_employee():
    """Create test employee in Ontario."""
    return Employee(
        id="emp_001",
        first_name="Jane",
        last_name="Doe",
        sin="123456789",
        province_of_employment=Province.ON,
        federal_claim_amount=Decimal("16129.00"),
        provincial_claim_amount=Decimal("12747.00"),
        annual_salary=Decimal("52000.00"),
        pay_frequency=PayPeriodFrequency.BIWEEKLY,
        hire_date=date(2020, 1, 1)
    )


@pytest.mark.asyncio
async def test_ontario_holiday_pay(ontario_employee):
    """Test Ontario holiday pay calculation."""
    service = HolidayService()

    # Pay period containing Christmas (Dec 25, 2025)
    result = await service.calculate_holiday_pay(
        employee=ontario_employee,
        pay_period_start=date(2025, 12, 15),
        pay_period_end=date(2025, 12, 28),
        gross_regular=Decimal("2000.00"),
        hours_worked_on_holidays={}
    )

    # Should detect Christmas holiday
    assert len(result.holidays) == 2  # Christmas + Boxing Day
    assert result.holiday_pay > Decimal("0")

    # Ontario formula: (wages in 4 weeks + vacation) / 20
    # For bi-weekly at $2000/period:
    # 4 weeks wages = $4000, vacation = $160 (4%), total = $4160
    # Daily = $4160 / 20 = $208
    # 2 holidays × $208 = $416
    expected = Decimal("416.00")
    assert abs(result.holiday_pay - expected) < Decimal("1.00")  # Allow rounding


@pytest.mark.asyncio
async def test_worked_holiday_premium(ontario_employee):
    """Test premium pay for working on holiday."""
    service = HolidayService()

    # Employee works 8 hours on Christmas
    result = await service.calculate_holiday_pay(
        employee=ontario_employee,
        pay_period_start=date(2025, 12, 15),
        pay_period_end=date(2025, 12, 28),
        gross_regular=Decimal("2000.00"),
        hours_worked_on_holidays={
            date(2025, 12, 25): Decimal("8")
        }
    )

    # Should have both holiday pay AND premium pay
    assert result.holiday_pay > Decimal("0")
    assert result.premium_hours == Decimal("8")
    assert result.premium_pay > Decimal("0")

    # Premium should be 1.5× regular rate × 8 hours
    # $25/hour × 1.5 × 8 = $300
    expected_premium = Decimal("300.00")
    assert abs(result.premium_pay - expected_premium) < Decimal("10.00")
```

### Vacation Pay Tests

```python
# backend/tests/test_vacation_service.py
import pytest
from decimal import Decimal
from datetime import date

from backend.app.services.payroll.vacation_service import VacationService
from backend.app.models.payroll import Employee, Province, PayPeriodFrequency


@pytest.fixture
def employee_under_5_years():
    """Employee with 3 years of service."""
    return Employee(
        id="emp_002",
        first_name="John",
        last_name="Smith",
        sin="987654321",
        province_of_employment=Province.BC,
        federal_claim_amount=Decimal("16129.00"),
        provincial_claim_amount=Decimal("12932.00"),
        annual_salary=Decimal("60000.00"),
        pay_frequency=PayPeriodFrequency.BIWEEKLY,
        hire_date=date(2022, 6, 1)  # ~3 years ago
    )


@pytest.fixture
def employee_over_5_years():
    """Employee with 7 years of service."""
    return Employee(
        id="emp_003",
        first_name="Sarah",
        last_name="Johnson",
        sin="555666777",
        province_of_employment=Province.AB,
        federal_claim_amount=Decimal("16129.00"),
        provincial_claim_amount=Decimal("22323.00"),
        annual_salary=Decimal("75000.00"),
        pay_frequency=PayPeriodFrequency.BIWEEKLY,
        hire_date=date(2018, 3, 15)  # ~7 years ago
    )


@pytest.mark.asyncio
async def test_vacation_accrual_4_percent(employee_under_5_years):
    """Test 4% vacation accrual for employee under 5 years."""
    service = VacationService()

    result = await service.calculate_vacation_pay(
        employee=employee_under_5_years,
        gross_earnings=Decimal("2307.69"),  # Bi-weekly for $60k/year
        vacation_hours_taken=Decimal("0"),
        current_balance=Decimal("500.00")
    )

    # Should accrue 4% of gross
    expected_accrual = Decimal("2307.69") * Decimal("0.04")
    assert abs(result.vacation_accrued - expected_accrual) < Decimal("0.01")
    assert result.vacation_rate == Decimal("0.04")
    assert result.years_of_service < 5


@pytest.mark.asyncio
async def test_vacation_accrual_6_percent(employee_over_5_years):
    """Test 6% vacation accrual for employee over 5 years."""
    service = VacationService()

    result = await service.calculate_vacation_pay(
        employee=employee_over_5_years,
        gross_earnings=Decimal("2884.62"),  # Bi-weekly for $75k/year
        vacation_hours_taken=Decimal("0"),
        current_balance=Decimal("1200.00")
    )

    # Should accrue 6% of gross
    expected_accrual = Decimal("2884.62") * Decimal("0.06")
    assert abs(result.vacation_accrued - expected_accrual) < Decimal("0.01")
    assert result.vacation_rate == Decimal("0.06")
    assert result.years_of_service >= 5


@pytest.mark.asyncio
async def test_vacation_payout(employee_under_5_years):
    """Test vacation payout when employee takes time off."""
    service = VacationService()

    # Employee takes 40 hours (1 week) vacation
    result = await service.calculate_vacation_pay(
        employee=employee_under_5_years,
        gross_earnings=Decimal("2307.69"),
        vacation_hours_taken=Decimal("40"),
        current_balance=Decimal("1000.00")
    )

    # Should accrue 4% on gross
    expected_accrual = Decimal("2307.69") * Decimal("0.04")

    # Should pay out 40 hours at hourly rate ($60k/2080 hours = $28.85/hour)
    expected_payout = Decimal("40") * (Decimal("60000") / Decimal("2080"))

    assert abs(result.vacation_accrued - expected_accrual) < Decimal("0.01")
    assert abs(result.vacation_pay_paid - expected_payout) < Decimal("1.00")

    # Balance should be: previous + accrued - paid
    expected_balance = Decimal("1000.00") + expected_accrual - expected_payout
    assert abs(result.balance_remaining - expected_balance) < Decimal("1.00")
```

---

## 📚 Documentation Requirements

### RAG Documentation

Create detailed reference documents for RAG system:

1. **`backend/rag/cra_tax/canadian_statutory_holidays_2025.md`**
   - Complete list of holidays by province
   - Eligibility rules
   - Calculation formulas
   - Premium pay rules

2. **`backend/rag/cra_tax/canadian_vacation_pay_2025.md`**
   - Vacation entitlement by years of service
   - Accrual calculation methods
   - Payout options
   - Provincial variations

3. **`backend/rag/cra_tax/holiday_calendar_maintenance.md`**
   - How to update holiday configurations for new years
   - Moveable holiday calculation
   - Testing new configurations

### API Documentation

Document new API endpoints:

```python
# GET /api/v1/holidays/{province}/{year}
"""
Get statutory holidays for province and year.

Response:
{
  "province": "ON",
  "year": 2025,
  "holidays": [
    {
      "date": "2025-01-01",
      "name": "New Year's Day",
      "is_mandatory": true
    },
    ...
  ]
}
"""

# GET /api/v1/payroll/{ledger_id}/employees/{employee_id}/vacation
"""
Get employee vacation balance.

Response:
{
  "employee_id": "emp_001",
  "hours_available": 80,
  "hours_used": 24,
  "hours_remaining": 56,
  "pay_balance": 1500.00,
  "accrual_rate": 0.06,
  "years_of_service": 6.5
}
"""

# POST /api/v1/payroll/{ledger_id}/calculate
"""
Calculate payroll with holidays and vacation.

Request:
{
  "employee_id": "emp_001",
  "pay_period_start": "2025-12-15",
  "pay_period_end": "2025-12-28",
  "gross_regular": 2000.00,
  "vacation_hours_taken": 0,
  "hours_worked_on_holidays": {
    "2025-12-25": 8
  }
}

Response:
{
  "gross_regular": 2000.00,
  "holiday_pay": 416.00,
  "holiday_premium_pay": 300.00,
  "vacation_accrued": 109.44,
  "vacation_paid": 0,
  "total_gross": 2716.00,
  "cpp_employee": 135.80,
  "ei_employee": 46.17,
  "federal_tax": 350.00,
  "provincial_tax": 180.00,
  "net_pay": 2004.03
}
"""
```

---

## 🚀 Implementation Roadmap

### Week 1: Configuration Setup
- [ ] Create JSON holiday configurations for all 12 provinces (2025-2027)
- [ ] Implement `HolidayConfigLoader` class
- [ ] Write validation tests for all holiday configurations
- [ ] Document configuration structure

### Week 2: Holiday & Vacation Services
- [ ] Implement `HolidayService` with province-specific calculations
- [ ] Implement `VacationService` with accrual logic
- [ ] Enhance `PayrollRecord` model with new fields
- [ ] Write comprehensive unit tests

### Week 3: Integration & UI
- [ ] Integrate holiday/vacation into `PayrollCalculator`
- [ ] Add vacation balance tracking in Firestore
- [ ] Implement UI enhancements (holiday indicators, vacation display)
- [ ] End-to-end integration testing
- [ ] Create RAG documentation

---

## 🎓 Key Takeaways

### Why Configuration-Driven Approach?

1. **Maintainability**: Easy to update holidays when provinces change rules
2. **Accuracy**: Single source of truth from government sources
3. **Auditability**: JSON files can be version controlled and reviewed
4. **Extensibility**: Easy to add new years or provinces

### Provincial Differences Matter

- **Ontario**: Uses 1/20 formula (4-week average)
- **BC**: Uses average day's pay
- **Newfoundland**: Only 6 statutory holidays (fewest in Canada)
- **Nunavut**: 12 statutory holidays (most in Canada)

### Years of Service Milestones

- **5 years**: Vacation rate increases from 4% to 6%
- **10 years**: Federal employees get 8% (most provinces stay at 6%)
- Rate change may apply to full vacation year in some provinces

### Testing is Critical

- Validate against CRA PDOC calculator
- Test boundary conditions (exactly 5 years service, holiday on weekend, etc.)
- Verify all 12 provinces with real-world scenarios

---

**Next Phase**: [Phase 9: Reporting & Export](./09_reporting_export.md) (if applicable)

**Related Documents**:
- [Phase 1: Data Layer](./01_phase1_data_layer.md)
- [Phase 2: Calculations](./02_phase2_calculations.md)
- [Phase 6: Configuration Architecture](./06_configuration_architecture.md)
- [Phase 7: UI Design](./07_ui_design.md)
