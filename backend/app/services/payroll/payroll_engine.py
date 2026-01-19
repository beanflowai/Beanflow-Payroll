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
from app.services.payroll.bonus_tax_calculator import BonusTaxCalculator
from app.services.payroll.cpp_calculator import CPPCalculator, CppContribution
from app.services.payroll.ei_calculator import EICalculator, EiPremium
from app.services.payroll.federal_tax_calculator import FederalTaxCalculator
from app.services.payroll.provincial_tax_calculator import (
    ProvincialTaxCalculator,
)
from app.services.payroll.retroactive_tax_calculator import RetroactiveTaxCalculator

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
    bonus_earnings: Decimal = Decimal("0")  # Lump-sum payments (e.g., bonuses, commissions)
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

    # Tier 6: TD1 Form Fields
    # Employer RRSP contributions (affects EI insurability)
    employer_rrsp_per_period: Decimal = Decimal("0")
    employer_rrsp_withdrawal_restricted: bool = False  # If true, NOT EI insurable

    # Retroactive payments
    retroactive_pay_amount: Decimal = Decimal("0")
    retroactive_pay_periods: int = 1  # Number of periods to spread payment

    # Prescribed zone deductions (Northern living allowance)
    prescribed_zone_deduction_annual: Decimal = Decimal("0")

    # Alimony/maintenance payments (court-ordered)
    alimony_per_period: Decimal = Decimal("0")

    # Tax-exempt reserve income (military/RCMP)
    reserve_income_exempt: Decimal = Decimal("0")
    reserve_income_pensionable: bool = False  # If true, included in CPP pensionable

    # Other annual deductions (claimed on TD1)
    child_care_expenses_annual: Decimal = Decimal("0")
    medical_expenses_annual: Decimal = Decimal("0")
    charitable_donations_annual: Decimal = Decimal("0")

    # RPP/PRPP contributions (deducted at source)
    rpp_per_period: Decimal = Decimal("0")  # Registered Pension Plan
    prpp_per_period: Decimal = Decimal("0")  # Pooled Registered Pension Plan

    # Post-tax Deductions (not affecting tax calculation)
    garnishments: Decimal = Decimal("0")
    other_deductions: Decimal = Decimal("0")

    # YTD Values (for accurate annual maximum tracking)
    ytd_gross: Decimal = Decimal("0")
    ytd_bonus_earnings: Decimal = Decimal("0")
    ytd_pensionable_earnings: Decimal = Decimal("0")
    ytd_insurable_earnings: Decimal = Decimal("0")
    ytd_cpp_base: Decimal = Decimal("0")
    ytd_cpp_additional: Decimal = Decimal("0")
    ytd_ei: Decimal = Decimal("0")
    ytd_federal_tax: Decimal = Decimal("0")
    ytd_provincial_tax: Decimal = Decimal("0")

    # Pay period date (for tax edition selection)
    pay_date: date | None = None

    # Exemptions
    is_cpp_exempt: bool = False
    is_ei_exempt: bool = False
    cpp2_exempt: bool = False

    # Taxable Benefits (employer-paid benefits that are taxable)
    # Life insurance employer premium is pensionable but NOT insurable
    taxable_benefits_pensionable: Decimal = Decimal("0")

    # Taxable benefits that ARE insurable (e.g., non-cash benefits for EI)
    taxable_benefits_insurable: Decimal = Decimal("0")

    # CPP proration for mid-year starts (number of pensionable months 1-12)
    pensionable_months: int | None = None

    @property
    def total_gross(self) -> Decimal:
        """Total gross earnings for this period."""
        return (
            self.gross_regular
            + self.gross_overtime
            + self.bonus_earnings
            + self.holiday_pay
            + self.holiday_premium_pay
            + self.vacation_pay
            + self.other_earnings
        )

    @property
    def pensionable_earnings(self) -> Decimal:
        """Earnings subject to CPP (includes pensionable taxable benefits and retroactive pay)."""
        return self.total_gross + self.taxable_benefits_pensionable + self.retroactive_pay_amount

    @property
    def insurable_earnings(self) -> Decimal:
        """Earnings subject to EI (includes insurable taxable benefits and retroactive pay)."""
        return self.total_gross + self.taxable_benefits_insurable + self.retroactive_pay_amount

    @property
    def taxable_income_per_period(self) -> Decimal:
        """Gross income for tax calculation (includes taxable benefits)."""
        return self.total_gross + self.taxable_benefits_pensionable


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
    bonus_earnings: Decimal  # Lump-sum payments taxed using bonus tax method
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

    # Tax breakdown for income vs bonus (for PDOC-style display)
    federal_tax_on_income: Decimal = Decimal("0")
    provincial_tax_on_income: Decimal = Decimal("0")
    federal_tax_on_bonus: Decimal = Decimal("0")
    provincial_tax_on_bonus: Decimal = Decimal("0")

    # Tax breakdown for retroactive pay (same marginal method as bonus)
    federal_tax_on_retroactive: Decimal = Decimal("0")
    provincial_tax_on_retroactive: Decimal = Decimal("0")

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
        self._federal_calculators: dict[tuple[int, date], FederalTaxCalculator] = {}
        self._provincial_calculators: dict[tuple[str, int, date | None], ProvincialTaxCalculator] = {}
        self._bonus_calculators: dict[tuple[str, int, date | None], BonusTaxCalculator] = {}

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
        self, province: str, pay_periods: int, pay_date: date | None = None
    ) -> ProvincialTaxCalculator:
        """Get or create provincial tax calculator for province, pay frequency, and date."""
        key = (province, pay_periods, pay_date)
        if key not in self._provincial_calculators:
            self._provincial_calculators[key] = ProvincialTaxCalculator(
                province, pay_periods, self.year, pay_date
            )
        return self._provincial_calculators[key]

    def _get_bonus_calculator(
        self, province: str, pay_periods: int, pay_date: date | None = None
    ) -> BonusTaxCalculator:
        """Get or create bonus tax calculator for province and pay frequency."""
        key = (province, pay_periods, pay_date)
        if key not in self._bonus_calculators:
            self._bonus_calculators[key] = BonusTaxCalculator(
                province, pay_periods, self.year, pay_date
            )
        return self._bonus_calculators[key]

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
        provincial_calc = self._get_provincial_calculator(
            province_code, pay_periods, input_data.pay_date
        )

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
                f5=Decimal("0"),
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
                input_data.pensionable_months,
            )

        calculation_details["cpp"] = {
            "pensionable_earnings": str(input_data.pensionable_earnings),
            "ytd_cpp_base": str(input_data.ytd_cpp_base),
            "ytd_cpp_additional": str(input_data.ytd_cpp_additional),
            "base": str(cpp_result.base),
            "additional": str(cpp_result.additional),
            "f5": str(cpp_result.f5),
            "total": str(cpp_result.total),
            "employer": str(cpp_result.employer),
            "exempt": input_data.is_cpp_exempt,
            "cpp2_exempt": input_data.cpp2_exempt,
        }

        # =========================================================================
        # Step 3: Calculate Annual Taxable Income & Split Regular vs Bonus/Retro
        # Per CRA T4127: A = P × (I - F - F5 - U1)
        # where F5 = F2 + C2 (CPP enhancement + CPP2)
        # taxable_income_per_period includes taxable benefits (e.g., life insurance
        # employer contribution)
        #
        # IMPORTANT: Bonus income uses marginal rate method, not annualization.
        # =========================================================================
        has_bonus = input_data.bonus_earnings > Decimal("0")
        has_retroactive = input_data.retroactive_pay_amount > Decimal("0")

        regular_earnings = (
            input_data.gross_regular
            + input_data.gross_overtime
            + input_data.holiday_pay
            + input_data.holiday_premium_pay
            + input_data.vacation_pay
            + input_data.other_earnings
        )
        regular_gross = regular_earnings + input_data.taxable_benefits_pensionable
        regular_pensionable_earnings = regular_gross
        regular_insurable_earnings = regular_earnings + input_data.taxable_benefits_insurable

        # =========================================================================
        # Step 2: Calculate EI (after regular_insurable_earnings is defined)
        # =========================================================================
        # IMPORTANT: EI must be calculated separately for regular and bonus portions
        # to match PDOC behavior. Both regular and bonus EI are capped by remaining MIE,
        # but the bonus EI calculation uses YTD values that include the regular period.
        #
        # NOTE: The actual YTD insurable earnings must be derived from ytd_ei (not
        # from ytd_insurable_earnings, which may be capped for display purposes).
        # =========================================================================
        regular_ei = Decimal("0")
        bonus_ei = Decimal("0")
        if input_data.is_ei_exempt:
            ei_result = EiPremium(employee=Decimal("0"), employer=Decimal("0"))
        else:
            # Derive actual YTD insurable from ytd_ei (more accurate than fixture value)
            # If ytd_ei > 0, calculate actual ytd_insurable = ytd_ei / rate
            # Otherwise use the provided ytd_insurable_earnings
            if input_data.ytd_ei > Decimal("0") and ei_calc.employee_rate > Decimal("0"):
                actual_ytd_insurable = input_data.ytd_ei / ei_calc.employee_rate
            else:
                actual_ytd_insurable = input_data.ytd_insurable_earnings

            # Calculate EI on regular earnings
            regular_ei = ei_calc.calculate_ei_premium(
                regular_insurable_earnings,
                actual_ytd_insurable,
                input_data.ytd_ei,
            )

            # Calculate EI on bonus (with updated YTD values)
            if has_bonus:
                # YTD insurable for bonus calc = actual YTD + regular insurable
                ytd_for_bonus = actual_ytd_insurable + regular_insurable_earnings
                # YTD EI for bonus calc = existing YTD + regular EI
                ytd_ei_for_bonus = input_data.ytd_ei + regular_ei
                bonus_ei = ei_calc.calculate_ei_premium(
                    input_data.bonus_earnings,
                    ytd_for_bonus,
                    ytd_ei_for_bonus,
                )

            total_ei = regular_ei + bonus_ei
            ei_result = EiPremium(employee=total_ei, employer=total_ei * Decimal("1.4"))

        calculation_details["ei"] = {
            "insurable_earnings": str(input_data.insurable_earnings),
            "regular_insurable_earnings": str(regular_insurable_earnings),
            "bonus_earnings": str(input_data.bonus_earnings) if has_bonus else "0",
            "ytd_ei": str(input_data.ytd_ei),
            "employee": str(ei_result.employee),
            "employer": str(ei_result.employer),
            "exempt": input_data.is_ei_exempt,
        }

        regular_cpp_result = cpp_result
        regular_ei_result = EiPremium(employee=regular_ei, employer=regular_ei * Decimal("1.4"))
        if has_bonus or has_retroactive:
            if input_data.is_cpp_exempt:
                regular_cpp_result = CppContribution(
                    base=Decimal("0"),
                    additional=Decimal("0"),
                    f5=Decimal("0"),
                    total=Decimal("0"),
                    employer=Decimal("0"),
                )
            else:
                regular_cpp_result = cpp_calc.calculate_total_cpp(
                    regular_pensionable_earnings,
                    input_data.ytd_pensionable_earnings,
                    input_data.ytd_cpp_base,
                    input_data.ytd_cpp_additional,
                    input_data.cpp2_exempt,
                    input_data.pensionable_months,
                )

            # regular_ei_result already holds the regular portion (split above).

        retro_f5a = None
        retro_f5b = None
        if has_retroactive:
            retro_periods = max(1, input_data.retroactive_pay_periods)
            retro_per_period = self._round(
                input_data.retroactive_pay_amount / Decimal(str(retro_periods))
            )
            pi = regular_pensionable_earnings + retro_per_period
            if pi > Decimal("0"):
                retro_f5a = self._round(cpp_result.f5 * ((pi - retro_per_period) / pi))
                retro_f5b = self._round(cpp_result.f5 * (retro_per_period / pi))
            else:
                retro_f5a = Decimal("0")
                retro_f5b = Decimal("0")

        # Split income: regular (annualized) vs bonus (marginal method)
        if has_bonus:
            total_pensionable = input_data.pensionable_earnings
            bonus_pensionable = input_data.bonus_earnings
            if total_pensionable > Decimal("0"):
                f5a = self._round(
                    cpp_result.f5 * ((total_pensionable - bonus_pensionable) / total_pensionable)
                )
                f5b = self._round(cpp_result.f5 * (bonus_pensionable / total_pensionable))
            else:
                f5a = Decimal("0")
                f5b = Decimal("0")

            # For annualization, calculate regular income's annual taxable
            annual_taxable_regular = federal_calc.calculate_annual_taxable_income(
                regular_gross,
                input_data.rrsp_per_period,
                input_data.union_dues_per_period,
                f5a,
            )
            per_period_taxable_regular = self._round(annual_taxable_regular / Decimal(str(pay_periods)))

            # Bonus method base should be the ANNUAL GROSS (regular annualized + prior bonuses)
            # The calculator will handle F5 deductions internally for marginal rates.
            bonus_base_annual_gross = (regular_gross * Decimal(str(pay_periods))) + input_data.ytd_bonus_earnings

            calculation_details["income"] = {
                "has_bonus": True,
                "bonus_amount": str(input_data.bonus_earnings),
                "regular_gross_per_period": str(regular_gross),
                "annual_taxable_regular": str(annual_taxable_regular),
                "regular_taxable_per_period": str(per_period_taxable_regular),
                "bonus_base_annual_gross": str(bonus_base_annual_gross),
                "ytd_bonus_earnings": str(input_data.ytd_bonus_earnings),
                "rrsp_per_period": str(input_data.rrsp_per_period),
                "union_dues_per_period": str(input_data.union_dues_per_period),
                "cpp_f5_per_period": str(regular_cpp_result.f5),
                "cpp_f5a_per_period": str(f5a),
                "cpp_f5b_per_period": str(f5b),
            }
        else:
            f5_for_regular = cpp_result.f5
            if has_retroactive and retro_f5a is not None:
                f5_for_regular = retro_f5a
            # No bonus - use traditional annualization for all income
            annual_taxable_regular = federal_calc.calculate_annual_taxable_income(
                regular_gross,
                input_data.rrsp_per_period,
                input_data.union_dues_per_period,
                f5_for_regular,
            )
            calculation_details["income"] = {
                "has_bonus": False,
                "gross_per_period": str(regular_gross),
                "taxable_benefits_pensionable": str(input_data.taxable_benefits_pensionable),
                "taxable_income_per_period": str(regular_gross),
                "rrsp_per_period": str(input_data.rrsp_per_period),
                "union_dues_per_period": str(input_data.union_dues_per_period),
                "cpp_f5_per_period": str(f5_for_regular),
                "annual_taxable_income": str(annual_taxable_regular),
            }
            if has_retroactive and retro_f5b is not None:
                calculation_details["income"]["retro_f5a_per_period"] = str(retro_f5a)
                calculation_details["income"]["retro_f5b_per_period"] = str(retro_f5b)

        # =========================================================================
        # Step 4: Calculate Federal Tax
        # Regular income uses annualization; bonus uses marginal rate method.
        # =========================================================================
        if has_bonus:
            # Calculate tax on regular income (annualization method)
            federal_result_regular = federal_calc.calculate_federal_tax(
                annual_taxable_regular,
                input_data.federal_claim_amount,
                regular_cpp_result.base,
                regular_ei_result.employee,
                ytd_cpp_base=input_data.ytd_cpp_base,
                ytd_ei=input_data.ytd_ei,
                pensionable_months=input_data.pensionable_months,
            )

            # Calculate tax on bonus (marginal rate method)
            bonus_calc = self._get_bonus_calculator(province_code, pay_periods, input_data.pay_date)
            bonus_result = bonus_calc.calculate_bonus_tax(
                bonus_amount=input_data.bonus_earnings,
                ytd_taxable_income=bonus_base_annual_gross,
                federal_claim_amount=input_data.federal_claim_amount,
                provincial_claim_amount=input_data.provincial_claim_amount,
                pensionable_months=input_data.pensionable_months,
                rrsp_per_period=input_data.rrsp_per_period,
                union_dues_per_period=input_data.union_dues_per_period,
                regular_gross_per_period=regular_gross,
                ytd_bonus_earnings=input_data.ytd_bonus_earnings,
                total_cpp_base_per_period=cpp_result.base,
                regular_cpp_base_per_period=regular_cpp_result.base,
                total_ei_per_period=ei_result.employee,
                regular_ei_per_period=regular_ei_result.employee,
                f5a_per_period=f5a,
                f5b_per_period=f5b,
            )

            federal_tax_per_period = federal_result_regular.tax_per_period + bonus_result.federal_tax
            provincial_tax_per_period = Decimal("0")  # Will be set in Step 5

            calculation_details["federal_tax"] = {
                "method": "split_regular_bonus",
                "regular_tax": str(federal_result_regular.tax_per_period),
                "bonus_tax": str(bonus_result.federal_tax),
                "total_tax_per_period": str(federal_tax_per_period),
                "regular_annual_taxable": str(federal_result_regular.annual_taxable_income),
                "bonus_base_annual": str(bonus_result.ytd_taxable_income),
                "bonus_amount": str(bonus_result.bonus_amount),
                "regular_cpp": str(regular_cpp_result.base),
                "regular_ei": str(regular_ei_result.employee),
            }
        else:
            # Traditional calculation for regular pay only
            federal_result_regular = federal_calc.calculate_federal_tax(
                annual_taxable_regular,
                input_data.federal_claim_amount,
                regular_cpp_result.base,
                regular_ei_result.employee,
                ytd_cpp_base=input_data.ytd_cpp_base,
                ytd_ei=input_data.ytd_ei,
                pensionable_months=input_data.pensionable_months,
            )
            federal_tax_per_period = federal_result_regular.tax_per_period

            calculation_details["federal_tax"] = {
                "method": "annualization",
                "annual_taxable_income": str(federal_result_regular.annual_taxable_income),
                "tax_rate": str(federal_result_regular.tax_rate),
                "constant_K": str(federal_result_regular.constant_k),
                "K1_personal_credits": str(federal_result_regular.personal_credits_k1),
                "K2_cpp_ei_credits": str(federal_result_regular.cpp_ei_credits_k2),
                "K4_employment_credit": str(federal_result_regular.employment_credit_k4),
                "T3_basic_tax": str(federal_result_regular.basic_federal_tax_t3),
                "T1_annual_tax": str(federal_result_regular.annual_federal_tax_t1),
                "tax_per_period": str(federal_result_regular.tax_per_period),
            }

        # =========================================================================
        # Step 5: Calculate Provincial Tax
        # Regular income uses annualization; bonus uses marginal rate method.
        # =========================================================================
        if has_bonus:
            # Provincial tax on regular income
            provincial_result_regular = provincial_calc.calculate_provincial_tax(
                annual_taxable_regular,
                input_data.provincial_claim_amount,
                regular_cpp_result.base,
                regular_ei_result.employee,
                ytd_cpp_base=input_data.ytd_cpp_base,
                ytd_ei=input_data.ytd_ei,
                pensionable_months=input_data.pensionable_months,
            )

            # bonus_result already calculated in Step 4
            provincial_tax_per_period = provincial_result_regular.tax_per_period + bonus_result.provincial_tax

            calculation_details["provincial_tax"] = {
                "method": "split_regular_bonus",
                "regular_tax": str(provincial_result_regular.tax_per_period),
                "bonus_tax": str(bonus_result.provincial_tax),
                "total_tax_per_period": str(provincial_tax_per_period),
                "province": provincial_result_regular.province_code,
                "regular_cpp": str(regular_cpp_result.base),
                "regular_ei": str(regular_ei_result.employee),
            }
        else:
            # Traditional calculation
            provincial_result_regular = provincial_calc.calculate_provincial_tax(
                annual_taxable_regular,
                input_data.provincial_claim_amount,
                regular_cpp_result.base,
                regular_ei_result.employee,
                ytd_cpp_base=input_data.ytd_cpp_base,
                ytd_ei=input_data.ytd_ei,
                pensionable_months=input_data.pensionable_months,
            )
            provincial_tax_per_period = provincial_result_regular.tax_per_period

            calculation_details["provincial_tax"] = {
                "method": "annualization",
                "province": provincial_result_regular.province_code,
                "annual_taxable_income": str(provincial_result_regular.annual_taxable_income),
                "tax_rate": str(provincial_result_regular.tax_rate),
                "constant_KP": str(provincial_result_regular.constant_kp),
                "K1P_personal_credits": str(provincial_result_regular.personal_credits_k1p),
                "K2P_cpp_ei_credits": str(provincial_result_regular.cpp_ei_credits_k2p),
                "K4P_employment_credit": str(provincial_result_regular.employment_credit_k4p),
                "K5P_supplemental": str(provincial_result_regular.supplemental_credit_k5p),
                "T4_basic_tax": str(provincial_result_regular.basic_provincial_tax_t4),
                "V1_surtax": str(provincial_result_regular.surtax_v1),
                "V2_health_premium": str(provincial_result_regular.health_premium_v2),
                "S_tax_reduction": str(provincial_result_regular.tax_reduction_s),
                "T2_annual_tax": str(provincial_result_regular.annual_provincial_tax_t2),
                "tax_per_period": str(provincial_result_regular.tax_per_period),
            }

        # =========================================================================
        # Step 5.5: Calculate Retroactive Tax (before totals)
        # Uses marginal rate method: Tax(YTD + Retro) - Tax(YTD)
        # =========================================================================
        federal_tax_regular = federal_tax_per_period
        provincial_tax_regular = provincial_tax_per_period
        federal_tax_total = federal_tax_per_period
        provincial_tax_total = provincial_tax_per_period

        if has_retroactive:
            retro_calc = RetroactiveTaxCalculator(
                province_code=province_code,
                pay_periods_per_year=pay_periods,
                year=self.year,
                pay_date=input_data.pay_date,
            )

            # Calculate retroactive tax using dedicated calculator
            retro_result = retro_calc.calculate_retroactive_tax(
                retroactive_amount=input_data.retroactive_pay_amount,
                retroactive_periods=input_data.retroactive_pay_periods,
                gross_regular=regular_gross,
                cpp_per_period=cpp_result.base,
                ei_per_period=ei_result.employee,
                f5_per_period=cpp_result.f5,
                regular_cpp_per_period=regular_cpp_result.base,
                regular_ei_per_period=regular_ei_result.employee,
                f5a_per_period=retro_f5a,
                f5b_per_period=retro_f5b,
                federal_claim_amount=input_data.federal_claim_amount,
                provincial_claim_amount=input_data.provincial_claim_amount,
                rrsp_per_period=input_data.rrsp_per_period,
                union_dues_per_period=input_data.union_dues_per_period,
                pensionable_months=input_data.pensionable_months or 12,
            )
            federal_tax_on_retroactive = self._round(retro_result.federal_tax)
            provincial_tax_on_retroactive = self._round(retro_result.provincial_tax)

            calculation_details["retroactive_tax"] = {
                "retroactive_amount": str(input_data.retroactive_pay_amount),
                "retroactive_periods": input_data.retroactive_pay_periods,
                "federal_tax": str(federal_tax_on_retroactive),
                "provincial_tax": str(provincial_tax_on_retroactive),
                "federal_tax_on_regular": str(retro_result.federal_tax_on_regular),
                "federal_tax_on_total": str(retro_result.federal_tax_on_total),
            }

            # Add retroactive tax to total tax per period
            federal_tax_total = federal_tax_total + federal_tax_on_retroactive
            provincial_tax_total = provincial_tax_total + provincial_tax_on_retroactive
        else:
            federal_tax_on_retroactive = Decimal("0")
            provincial_tax_on_retroactive = Decimal("0")

        # =========================================================================
        # Step 6: Calculate Totals
        # =========================================================================
        total_employee_deductions = (
            cpp_result.total
            + ei_result.employee
            + federal_tax_total
            + provincial_tax_total
            + input_data.rrsp_per_period
            + input_data.union_dues_per_period
            + input_data.garnishments
            + input_data.other_deductions
        )

        # PDOC: Net = Total cash income - Total deductions
        # Total cash income = Regular + Taxable benefits + Retroactive pay
        net_pay = (
            input_data.taxable_income_per_period
            + input_data.retroactive_pay_amount
            - total_employee_deductions
        )

        total_employer_costs = cpp_result.employer + ei_result.employer

        # =========================================================================
        # Step 7: Update YTD
        # =========================================================================
        new_ytd_gross = input_data.ytd_gross + input_data.total_gross
        new_ytd_cpp = input_data.ytd_cpp_base + input_data.ytd_cpp_additional + cpp_result.total
        new_ytd_ei = input_data.ytd_ei + ei_result.employee

        # =========================================================================
        # Step 8: Calculate Tax Breakdown (income vs bonus vs retroactive)
        # =========================================================================
        if has_bonus:
            # Split: regular income uses annualization, bonus uses marginal rate
            federal_tax_on_income = self._round(federal_result_regular.tax_per_period)
            federal_tax_on_bonus = self._round(bonus_result.federal_tax)
            provincial_tax_on_income = self._round(provincial_result_regular.tax_per_period)
            provincial_tax_on_bonus = self._round(bonus_result.provincial_tax)
        else:
            # No bonus: income tax = regular tax (without retroactive)
            federal_tax_on_income = self._round(federal_tax_regular)
            federal_tax_on_bonus = Decimal("0")
            provincial_tax_on_income = self._round(provincial_tax_regular)
            provincial_tax_on_bonus = Decimal("0")

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
            bonus_earnings=input_data.bonus_earnings,
            total_gross=input_data.total_gross,
            # Employee Deductions
            cpp_base=cpp_result.base,
            cpp_additional=cpp_result.additional,
            cpp_total=cpp_result.total,
            ei_employee=ei_result.employee,
            federal_tax=self._round(federal_tax_regular),
            provincial_tax=self._round(provincial_tax_regular),
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
            new_ytd_federal_tax=input_data.ytd_federal_tax + federal_tax_total,
            new_ytd_provincial_tax=input_data.ytd_provincial_tax + provincial_tax_total,
            # Tax breakdown (income vs bonus vs retroactive)
            federal_tax_on_income=federal_tax_on_income,
            provincial_tax_on_income=provincial_tax_on_income,
            federal_tax_on_bonus=federal_tax_on_bonus,
            provincial_tax_on_bonus=provincial_tax_on_bonus,
            federal_tax_on_retroactive=federal_tax_on_retroactive,
            provincial_tax_on_retroactive=provincial_tax_on_retroactive,
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
