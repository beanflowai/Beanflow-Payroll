"""Paystub data models for PDF generation."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

__all__ = [
    "EarningLine",
    "TaxLine",
    "BenefitLine",
    "VacationInfo",
    "SickLeaveInfo",
    "PaystubData",
]


@dataclass
class EarningLine:
    """Single earning line item."""

    description: str
    qty: str | None  # e.g., "130:00" for hours or None for salary
    rate: Decimal | None  # Hourly rate or None for salary
    current: Decimal
    ytd: Decimal


@dataclass
class TaxLine:
    """Single tax deduction line item."""

    description: str
    current: Decimal  # Negative value (deduction)
    ytd: Decimal  # Negative value (deduction)


@dataclass
class BenefitLine:
    """Single benefit line item (employer contribution or employee deduction)."""

    description: str
    current: Decimal
    ytd: Decimal


@dataclass
class VacationInfo:
    """Vacation tracking information."""

    earned: Decimal  # Current period accrual
    ytdUsed: Decimal  # YTD hours/dollars used  # noqa: N815
    available: Decimal  # Current available balance


@dataclass
class SickLeaveInfo:
    """Sick leave tracking information."""

    paidDaysRemaining: Decimal  # Remaining paid sick days  # noqa: N815
    unpaidDaysRemaining: Decimal  # Remaining unpaid sick days  # noqa: N815
    daysUsedYtd: Decimal  # YTD days used  # noqa: N815


@dataclass
class PaystubData:
    """Complete data structure for paystub PDF generation.

    This model collects all necessary information to render a paystub PDF.
    All monetary values should use Decimal for precision.
    """

    # === Employee Info ===
    employeeName: str
    employeeAddress: str | None  # Full address (multi-line ok)
    sinMasked: str  # Format: "***-***-XXX"

    # === Employer Info ===
    employerName: str
    employerAddress: str

    # === Period Info ===
    periodStart: date
    periodEnd: date
    payDate: date

    # === Earnings ===
    earnings: list[EarningLine] = field(default_factory=list)
    totalEarnings: Decimal = Decimal("0")
    ytdEarnings: Decimal = Decimal("0")

    # === Taxes (all values should be negative for deductions) ===
    taxes: list[TaxLine] = field(default_factory=list)
    totalTaxes: Decimal = Decimal("0")  # Sum of current taxes (negative)
    ytdTaxes: Decimal = Decimal("0")  # Sum of YTD taxes (negative)

    # === Non-taxable Company Items (employer contributions, positive values) ===
    nonTaxableBenefits: list[BenefitLine] = field(default_factory=list)

    # === Taxable Company Items (employer-paid life insurance, positive values) ===
    taxableBenefits: list[BenefitLine] = field(default_factory=list)

    # === Adjustments to Net Pay (employee deductions, negative values) ===
    benefitDeductions: list[BenefitLine] = field(default_factory=list)
    totalBenefitDeductions: Decimal = Decimal("0")  # Sum (negative)
    ytdBenefitDeductions: Decimal = Decimal("0")  # Sum (negative)

    # === Totals ===
    netPay: Decimal = Decimal("0")
    ytdNetPay: Decimal | None = None

    # === Vacation ===
    vacation: VacationInfo | None = None

    # === Sick Leave ===
    sickLeave: SickLeaveInfo | None = None  # noqa: N815

    # === Optional fields ===
    occupation: str | None = None
    memo: str | None = None  # e.g., "Pay Period: 11/01/2025 - 11/30/2025"
    logoUrl: str | None = None  # Company logo URL for paystub branding
    logoBytes: bytes | None = None  # Pre-downloaded logo bytes (preferred over URL)
    payRate: str | None = None  # e.g., "$100,000.00/yr" or "$25.00/hr"
