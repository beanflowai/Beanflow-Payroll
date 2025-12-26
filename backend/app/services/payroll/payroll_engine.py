"""
Payroll Engine - Orchestrates all payroll calculations.

Coordinates CPP, EI, Federal Tax, and Provincial Tax calculators
to produce complete payroll calculations for employees.

Reference: CRA T4127 (121st Edition, July 2025)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.models.payroll import PayFrequency, Province
from app.services.payroll.cpp_calculator import CPPCalculator, CppContribution
from app.services.payroll.ei_calculator import EICalculator, EiPremium
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator, FederalTaxResult
from app.services.payroll.provincial_tax_calculator import ProvincialTaxCalculator, ProvincialTaxResult

logger = logging.getLogger(__name__)


@dataclass
class EmployeePayrollInput:
    """Input data for calculating one employee's payroll."""

    employee_id: str
    province: Province
    pay_frequency: PayFrequency

    # Compensation
    gross_regular: Decimal
    gross_overtime: Decimal = Decimal("0")
    holiday_pay: Decimal = Decimal("0")
    holiday_premium_pay: Decimal = Decimal("0")
    vacation_pay: Decimal = Decimal("0")
    other_earnings: Decimal = Decimal("0")

    # TD1 Claim Amounts
    federal_claim_amount: Decimal = Decimal("16129")  # Default BPA
    provincial_claim_amount: Decimal = Decimal("12747")  # Default ON BPA

    # Pre-tax Deductions
    rrsp_per_period: Decimal = Decimal("0")
    union_dues_per_period: Decimal = Decimal("0")

    # Post-tax Deductions (not affecting tax calculation)
    garnishments: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")

    # YTD Values (for accurate annual maximum tracking)
    ytd_gross: Decimal = Decimal("0")
    ytd_pensionable_earnings: Decimal = Decimal("0")
    ytd_insurable_earnings: Decimal = Decimal("0")
    ytd_cpp_base: Decimal = Decimal("0")
    ytd_cpp_additional: Decimal = Decimal("0")
    ytd_ei: Decimal = Decimal("0")

    # Pay period date (for tax edition selection)
    pay_date: date | None = None

    # Exemptions
    is_cpp_exempt: bool = False
    is_ei_exempt: bool = False
    cpp2_exempt: bool = False

    @property
    def total_gross(self) -> Decimal:
        """Total gross earnings for this period."""
        return (
            self.gross_regular
            + self.gross_overtime
            + self.holiday_pay
            + self.holiday_premium_pay
            + self.vacation_pay
            + self.other_earnings
        )

    @property
    def pensionable_earnings(self) -> Decimal:
        """Earnings subject to CPP."""
        # Most earnings are pensionable
        return self.total_gross

    @property
    def insurable_earnings(self) -> Decimal:
        """Earnings subject to EI."""
        # Most earnings are insurable
        return self.total_gross


@dataclass
class PayrollCalculationResult:
    """Complete payroll calculation result for one employee."""

    employee_id: str
    province: str

    # Earnings
    gross_regular: Decimal
    gross_overtime: Decimal
    holiday_pay: Decimal
    holiday_premium_pay: Decimal
    vacation_pay: Decimal
    other_earnings: Decimal
    total_gross: Decimal

    # Employee Deductions
    cpp_base: Decimal
    cpp_additional: Decimal  # CPP2
    cpp_total: Decimal
    ei_employee: Decimal
    federal_tax: Decimal
    provincial_tax: Decimal
    rrsp: Decimal
    union_dues: Decimal
    garnishments: Decimal
    other_deductions: Decimal
    total_employee_deductions: Decimal

    # Employer Costs
    cpp_employer: Decimal
    ei_employer: Decimal
    total_employer_costs: Decimal

    # Net Pay
    net_pay: Decimal

    # Updated YTD
    new_ytd_gross: Decimal
    new_ytd_cpp: Decimal
    new_ytd_ei: Decimal
    new_ytd_federal_tax: Decimal
    new_ytd_provincial_tax: Decimal

    # Calculation Details (for audit/debugging)
    calculation_details: dict[str, Any] = field(default_factory=dict)


class PayrollEngine:
    """
    Orchestrates complete payroll calculations.

    Coordinates all calculators:
    - CPP Calculator: Base CPP + CPP2 (additional)
    - EI Calculator: Employee and employer premiums
    - Federal Tax Calculator: T4127 Option 1 formula
    - Provincial Tax Calculator: Province-specific calculations

    Usage:
        engine = PayrollEngine(year=2025)
        result = engine.calculate(employee_input)
    """

    def __init__(self, year: int = 2025):
        """
        Initialize payroll engine.

        Args:
            year: Tax year for all calculations
        """
        self.year = year
        self._cpp_calculators: dict[int, CPPCalculator] = {}
        self._ei_calculators: dict[int, EICalculator] = {}
        self._federal_calculators: dict[tuple[int, date | None], FederalTaxCalculator] = {}
        self._provincial_calculators: dict[tuple[str, int], ProvincialTaxCalculator] = {}

    def _get_cpp_calculator(self, pay_periods: int) -> CPPCalculator:
        """Get or create CPP calculator for pay frequency."""
        if pay_periods not in self._cpp_calculators:
            self._cpp_calculators[pay_periods] = CPPCalculator(pay_periods, self.year)
        return self._cpp_calculators[pay_periods]

    def _get_ei_calculator(self, pay_periods: int) -> EICalculator:
        """Get or create EI calculator for pay frequency."""
        if pay_periods not in self._ei_calculators:
            self._ei_calculators[pay_periods] = EICalculator(pay_periods, self.year)
        return self._ei_calculators[pay_periods]

    def _get_federal_calculator(
        self, pay_periods: int, pay_date: date | None = None
    ) -> FederalTaxCalculator:
        """Get or create federal tax calculator for pay frequency and date."""
        key = (pay_periods, pay_date)
        if key not in self._federal_calculators:
            self._federal_calculators[key] = FederalTaxCalculator(
                pay_periods, self.year, pay_date
            )
        return self._federal_calculators[key]

    def _get_provincial_calculator(
        self, province: str, pay_periods: int
    ) -> ProvincialTaxCalculator:
        """Get or create provincial tax calculator."""
        key = (province, pay_periods)
        if key not in self._provincial_calculators:
            self._provincial_calculators[key] = ProvincialTaxCalculator(
                province, pay_periods, self.year
            )
        return self._provincial_calculators[key]

    def _round(self, value: Decimal) -> Decimal:
        """Round to 2 decimal places."""
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate(self, input_data: EmployeePayrollInput) -> PayrollCalculationResult:
        """
        Calculate complete payroll for one employee.

        Processing order:
        1. Calculate CPP contributions
        2. Calculate EI premiums
        3. Calculate annual taxable income
        4. Calculate federal tax
        5. Calculate provincial tax
        6. Calculate net pay and employer costs

        Args:
            input_data: Employee payroll input data

        Returns:
            Complete payroll calculation result
        """
        pay_periods = input_data.pay_frequency.periods_per_year
        province_code = input_data.province.value

        # Get calculators
        cpp_calc = self._get_cpp_calculator(pay_periods)
        ei_calc = self._get_ei_calculator(pay_periods)
        federal_calc = self._get_federal_calculator(pay_periods, input_data.pay_date)
        provincial_calc = self._get_provincial_calculator(province_code, pay_periods)

        calculation_details: dict[str, Any] = {
            "pay_periods_per_year": pay_periods,
            "province": province_code,
            "year": self.year,
        }

        # =========================================================================
        # Step 1: Calculate CPP
        # =========================================================================
        if input_data.is_cpp_exempt:
            cpp_result = CppContribution(
                base=Decimal("0"),
                additional=Decimal("0"),
                enhancement=Decimal("0"),
                total=Decimal("0"),
                employer=Decimal("0"),
            )
        else:
            cpp_result = cpp_calc.calculate_total_cpp(
                input_data.pensionable_earnings,
                input_data.ytd_pensionable_earnings,
                input_data.ytd_cpp_base,
                input_data.ytd_cpp_additional,
                input_data.cpp2_exempt,
            )

        calculation_details["cpp"] = {
            "pensionable_earnings": str(input_data.pensionable_earnings),
            "ytd_cpp_base": str(input_data.ytd_cpp_base),
            "ytd_cpp_additional": str(input_data.ytd_cpp_additional),
            "base": str(cpp_result.base),
            "additional": str(cpp_result.additional),
            "enhancement": str(cpp_result.enhancement),
            "total": str(cpp_result.total),
            "employer": str(cpp_result.employer),
            "exempt": input_data.is_cpp_exempt,
            "cpp2_exempt": input_data.cpp2_exempt,
        }

        # =========================================================================
        # Step 2: Calculate EI
        # =========================================================================
        if input_data.is_ei_exempt:
            ei_result = EiPremium(employee=Decimal("0"), employer=Decimal("0"))
        else:
            ei_result = ei_calc.calculate_total_premium(
                input_data.insurable_earnings,
                input_data.ytd_insurable_earnings,
                input_data.ytd_ei,
            )

        calculation_details["ei"] = {
            "insurable_earnings": str(input_data.insurable_earnings),
            "ytd_ei": str(input_data.ytd_ei),
            "employee": str(ei_result.employee),
            "employer": str(ei_result.employer),
            "exempt": input_data.is_ei_exempt,
        }

        # =========================================================================
        # Step 3: Calculate Annual Taxable Income
        # Note: Both F2 (CPP enhancement) and CPP2 are deducted from taxable income
        # per CRA T4127: A = P × (I - F - F2 - U1 - CPP2)
        # =========================================================================
        annual_taxable = federal_calc.calculate_annual_taxable_income(
            input_data.total_gross,
            input_data.rrsp_per_period,
            input_data.union_dues_per_period,
            cpp_result.additional,     # CPP2 is deductible from taxable income
            cpp_result.enhancement,    # F2: CPP enhancement (1% portion)
        )

        calculation_details["income"] = {
            "gross_per_period": str(input_data.total_gross),
            "rrsp_per_period": str(input_data.rrsp_per_period),
            "union_dues_per_period": str(input_data.union_dues_per_period),
            "cpp_enhancement_per_period": str(cpp_result.enhancement),
            "cpp2_per_period": str(cpp_result.additional),
            "annual_taxable_income": str(annual_taxable),
        }

        # =========================================================================
        # Step 4: Calculate Federal Tax
        # =========================================================================
        federal_result = federal_calc.calculate_federal_tax(
            annual_taxable,
            input_data.federal_claim_amount,
            cpp_result.base,  # Only base CPP for tax credit
            ei_result.employee,
        )

        calculation_details["federal_tax"] = {
            "annual_taxable_income": str(federal_result.annual_taxable_income),
            "tax_rate": str(federal_result.tax_rate),
            "constant_K": str(federal_result.constant_k),
            "K1_personal_credits": str(federal_result.personal_credits_k1),
            "K2_cpp_ei_credits": str(federal_result.cpp_ei_credits_k2),
            "K4_employment_credit": str(federal_result.employment_credit_k4),
            "T3_basic_tax": str(federal_result.basic_federal_tax_t3),
            "T1_annual_tax": str(federal_result.annual_federal_tax_t1),
            "tax_per_period": str(federal_result.tax_per_period),
        }

        # =========================================================================
        # Step 5: Calculate Provincial Tax
        # =========================================================================
        provincial_result = provincial_calc.calculate_provincial_tax(
            annual_taxable,
            input_data.provincial_claim_amount,
            cpp_result.base,
            ei_result.employee,
        )

        calculation_details["provincial_tax"] = {
            "province": provincial_result.province_code,
            "annual_taxable_income": str(provincial_result.annual_taxable_income),
            "tax_rate": str(provincial_result.tax_rate),
            "constant_KP": str(provincial_result.constant_kp),
            "K1P_personal_credits": str(provincial_result.personal_credits_k1p),
            "K2P_cpp_ei_credits": str(provincial_result.cpp_ei_credits_k2p),
            "K5P_supplemental": str(provincial_result.supplemental_credit_k5p),
            "T4_basic_tax": str(provincial_result.basic_provincial_tax_t4),
            "V1_surtax": str(provincial_result.surtax_v1),
            "V2_health_premium": str(provincial_result.health_premium_v2),
            "S_tax_reduction": str(provincial_result.tax_reduction_s),
            "T2_annual_tax": str(provincial_result.annual_provincial_tax_t2),
            "tax_per_period": str(provincial_result.tax_per_period),
        }

        # =========================================================================
        # Step 6: Calculate Totals
        # =========================================================================
        total_employee_deductions = (
            cpp_result.total
            + ei_result.employee
            + federal_result.tax_per_period
            + provincial_result.tax_per_period
            + input_data.rrsp_per_period
            + input_data.union_dues_per_period
            + input_data.garnishments
            + input_data.other_deductions
        )

        net_pay = input_data.total_gross - total_employee_deductions

        total_employer_costs = cpp_result.employer + ei_result.employer

        # =========================================================================
        # Step 7: Update YTD
        # =========================================================================
        new_ytd_gross = input_data.ytd_gross + input_data.total_gross
        new_ytd_cpp = input_data.ytd_cpp_base + input_data.ytd_cpp_additional + cpp_result.total
        new_ytd_ei = input_data.ytd_ei + ei_result.employee

        return PayrollCalculationResult(
            employee_id=input_data.employee_id,
            province=province_code,
            # Earnings
            gross_regular=input_data.gross_regular,
            gross_overtime=input_data.gross_overtime,
            holiday_pay=input_data.holiday_pay,
            holiday_premium_pay=input_data.holiday_premium_pay,
            vacation_pay=input_data.vacation_pay,
            other_earnings=input_data.other_earnings,
            total_gross=input_data.total_gross,
            # Employee Deductions
            cpp_base=cpp_result.base,
            cpp_additional=cpp_result.additional,
            cpp_total=cpp_result.total,
            ei_employee=ei_result.employee,
            federal_tax=federal_result.tax_per_period,
            provincial_tax=provincial_result.tax_per_period,
            rrsp=input_data.rrsp_per_period,
            union_dues=input_data.union_dues_per_period,
            garnishments=input_data.garnishments,
            other_deductions=input_data.other_deductions,
            total_employee_deductions=self._round(total_employee_deductions),
            # Employer Costs
            cpp_employer=cpp_result.employer,
            ei_employer=ei_result.employer,
            total_employer_costs=self._round(total_employer_costs),
            # Net Pay
            net_pay=self._round(net_pay),
            # Updated YTD
            new_ytd_gross=new_ytd_gross,
            new_ytd_cpp=new_ytd_cpp,
            new_ytd_ei=new_ytd_ei,
            new_ytd_federal_tax=Decimal("0"),  # Would need existing YTD
            new_ytd_provincial_tax=Decimal("0"),  # Would need existing YTD
            # Details
            calculation_details=calculation_details,
        )

    def calculate_batch(
        self, inputs: list[EmployeePayrollInput]
    ) -> list[PayrollCalculationResult]:
        """
        Calculate payroll for multiple employees.

        Args:
            inputs: List of employee payroll inputs

        Returns:
            List of calculation results
        """
        return [self.calculate(input_data) for input_data in inputs]

    def validate_input(self, input_data: EmployeePayrollInput) -> list[str]:
        """
        Validate input data before calculation.

        Args:
            input_data: Employee payroll input

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: list[str] = []

        if input_data.gross_regular < Decimal("0"):
            errors.append("Gross regular pay cannot be negative")

        if input_data.gross_overtime < Decimal("0"):
            errors.append("Gross overtime pay cannot be negative")

        if input_data.federal_claim_amount < Decimal("0"):
            errors.append("Federal claim amount cannot be negative")

        if input_data.provincial_claim_amount < Decimal("0"):
            errors.append("Provincial claim amount cannot be negative")

        if input_data.ytd_gross < Decimal("0"):
            errors.append("YTD gross cannot be negative")

        return errors
