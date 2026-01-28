"""
Tests for paystub_data_builder.py module.

Uses MagicMock to simulate Pydantic models to avoid validation complexity.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.payroll.paystub_data_builder import (
    PROVINCE_NAMES,
    PaystubDataBuilder,
)


class TestProvinceNames:
    """Tests for PROVINCE_NAMES constant."""

    def test_contains_all_provinces(self):
        """Test that all 12 provinces/territories are included."""
        assert len(PROVINCE_NAMES) == 12

    def test_province_name_mapping(self):
        """Test correct province name mappings."""
        assert PROVINCE_NAMES["ON"] == "Ontario"
        assert PROVINCE_NAMES["BC"] == "British Columbia"
        assert PROVINCE_NAMES["AB"] == "Alberta"
        assert PROVINCE_NAMES["SK"] == "Saskatchewan"
        assert PROVINCE_NAMES["MB"] == "Manitoba"
        assert PROVINCE_NAMES["NT"] == "Northwest Territories"
        assert PROVINCE_NAMES["YT"] == "Yukon"
        assert PROVINCE_NAMES["NU"] == "Nunavut"


class TestBuildAddress:
    """Tests for _build_address method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    def test_full_address(self, builder: PaystubDataBuilder):
        """Test building a complete address."""
        result = builder._build_address(
            street="123 Main St",
            city="Toronto",
            province="ON",
            postal_code="M5V 1A1",
        )

        assert "123 Main St" in result
        assert "Toronto" in result
        assert "Ontario" in result
        assert "M5V 1A1" in result

    def test_address_without_street(self, builder: PaystubDataBuilder):
        """Test building address without street."""
        result = builder._build_address(
            street=None,
            city="Toronto",
            province="ON",
            postal_code="M5V 1A1",
        )

        assert "123 Main St" not in result
        assert "Toronto" in result
        assert "Ontario" in result

    def test_address_without_city(self, builder: PaystubDataBuilder):
        """Test building address without city."""
        result = builder._build_address(
            street="123 Main St",
            city=None,
            province="ON",
            postal_code="M5V 1A1",
        )

        assert "123 Main St" in result
        assert "Ontario" in result

    def test_address_without_postal_code(self, builder: PaystubDataBuilder):
        """Test building address without postal code."""
        result = builder._build_address(
            street="123 Main St",
            city="Toronto",
            province="ON",
            postal_code=None,
        )

        assert "123 Main St" in result
        assert "Toronto" in result
        assert "M5V" not in result

    def test_address_with_unknown_province(self, builder: PaystubDataBuilder):
        """Test building address with unknown province code."""
        result = builder._build_address(
            street="123 Main St",
            city="City",
            province="XX",
            postal_code="12345",
        )

        assert "XX" in result

    def test_empty_address(self, builder: PaystubDataBuilder):
        """Test building address with all None values except province."""
        result = builder._build_address(
            street=None,
            city=None,
            province="BC",
            postal_code=None,
        )

        assert "British Columbia" in result


class TestBuildEarnings:
    """Tests for _build_earnings method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    @pytest.fixture
    def base_employee(self) -> MagicMock:
        """Create a base employee mock."""
        employee = MagicMock()
        employee.hourly_rate = None  # Salaried employee by default
        employee.annual_salary = Decimal("52000")
        employee.standard_hours_per_week = Decimal("40")
        employee.pay_frequency = MagicMock()
        employee.pay_frequency.value = "bi_weekly"
        return employee

    @pytest.fixture
    def base_record(self) -> MagicMock:
        """Create a base payroll record mock."""
        record = MagicMock()
        record.gross_regular = Decimal("2000")
        record.gross_overtime = Decimal("0")
        record.holiday_pay = Decimal("0")
        record.holiday_premium_pay = Decimal("0")
        record.vacation_pay_paid = Decimal("0")
        record.other_earnings = Decimal("0")
        record.bonus_earnings = Decimal("0")
        record.regular_hours_worked = None
        record.overtime_hours_worked = Decimal("0")
        return record

    def test_regular_earnings_only(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test building earnings with only regular earnings (salaried employee)."""
        earnings = builder._build_earnings(base_record, base_employee, [])

        assert len(earnings) == 1
        # Salaried employees show "Regular Salary" with hours and rate
        assert earnings[0].description == "Regular Salary"
        assert earnings[0].current == Decimal("2000")
        assert earnings[0].ytd == Decimal("2000")
        # Verify hours and rate are calculated for salaried employees
        assert earnings[0].qty is not None  # bi-weekly hours (80.00)
        assert earnings[0].rate is not None  # implied hourly rate ($25/hr)

    def test_earnings_with_overtime(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test building earnings with overtime."""
        base_record.gross_overtime = Decimal("300")

        earnings = builder._build_earnings(base_record, base_employee, [])

        assert len(earnings) == 2
        overtime_line = next(e for e in earnings if e.description == "Overtime")
        assert overtime_line.current == Decimal("300")

    def test_earnings_with_holiday_pay(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test building earnings with holiday pay."""
        base_record.holiday_pay = Decimal("150")
        base_record.holiday_premium_pay = Decimal("50")

        earnings = builder._build_earnings(base_record, base_employee, [])

        assert len(earnings) == 2
        holiday_line = next(e for e in earnings if e.description == "Holiday Pay")
        assert holiday_line.current == Decimal("200")  # 150 + 50

    def test_earnings_with_vacation_pay(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test building earnings with vacation pay."""
        base_record.vacation_pay_paid = Decimal("500")

        earnings = builder._build_earnings(base_record, base_employee, [])

        assert len(earnings) == 2
        vacation_line = next(e for e in earnings if e.description == "Vacation Pay")
        assert vacation_line.current == Decimal("500")

    def test_earnings_with_other_earnings(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test building earnings with other earnings."""
        base_record.other_earnings = Decimal("100")

        earnings = builder._build_earnings(base_record, base_employee, [])

        assert len(earnings) == 2
        other_line = next(e for e in earnings if e.description == "Other Earnings")
        assert other_line.current == Decimal("100")

    def test_earnings_ytd_calculation_with_history(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test YTD calculation with historical records."""
        # Create historical records
        hist_record = MagicMock()
        hist_record.gross_regular = Decimal("2000")
        hist_record.gross_overtime = Decimal("100")
        hist_record.holiday_pay = Decimal("0")
        hist_record.holiday_premium_pay = Decimal("0")
        hist_record.vacation_pay_paid = Decimal("0")
        hist_record.other_earnings = Decimal("0")
        hist_record.bonus_earnings = Decimal("0")

        base_record.gross_overtime = Decimal("200")

        earnings = builder._build_earnings(base_record, base_employee, [hist_record])

        # Salaried employees show "Regular Salary" with hours and rate
        regular_line = next(e for e in earnings if e.description == "Regular Salary")
        assert regular_line.ytd == Decimal("4000")  # 2000 + 2000

        overtime_line = next(e for e in earnings if e.description == "Overtime")
        assert overtime_line.ytd == Decimal("300")  # 100 + 200

    def test_earnings_with_hours_for_hourly_employee(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test building earnings with hours for hourly employee."""
        base_employee.hourly_rate = Decimal("25.00")
        base_employee.annual_salary = None
        base_record.regular_hours_worked = Decimal("80")
        base_record.overtime_hours_worked = Decimal("5")
        base_record.gross_overtime = Decimal("187.50")  # 5 * 25 * 1.5

        earnings = builder._build_earnings(base_record, base_employee, [])

        assert len(earnings) == 2
        regular_line = next(e for e in earnings if e.description == "Regular Earnings")
        assert regular_line.qty == "80:00"
        assert regular_line.rate == Decimal("25.00")

        overtime_line = next(e for e in earnings if e.description == "Overtime")
        assert overtime_line.qty == "5:00"
        assert overtime_line.rate == Decimal("37.50")  # 25 * 1.5

    def test_earnings_with_hours_and_rate_for_salaried_employee(
        self, builder: PaystubDataBuilder, base_record: MagicMock, base_employee: MagicMock
    ):
        """Test building earnings with hours and rate for salaried employee."""
        earnings = builder._build_earnings(base_record, base_employee, [])

        assert len(earnings) == 1
        regular_line = earnings[0]
        # Salaried employees now show calculated hours and equivalent hourly rate
        assert regular_line.description == "Regular Salary"
        assert regular_line.qty == "80.00"  # bi-weekly hours (40 * 2)
        assert regular_line.rate == Decimal("25.00")  # $52000 / (40 * 52) = $25/hr


class TestBuildTaxes:
    """Tests for _build_taxes method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    @pytest.fixture
    def base_record(self) -> MagicMock:
        """Create a base payroll record mock."""
        record = MagicMock()
        record.cpp_employee = Decimal("100")
        record.cpp_additional = Decimal("20")
        record.ei_employee = Decimal("50")
        record.federal_tax = Decimal("300")
        record.provincial_tax = Decimal("150")
        record.ytd_cpp = Decimal("240")
        record.ytd_ei = Decimal("100")
        record.ytd_federal_tax = Decimal("600")
        record.ytd_provincial_tax = Decimal("300")
        return record

    def test_all_tax_lines(self, builder: PaystubDataBuilder, base_record: MagicMock):
        """Test building all tax lines."""
        taxes = builder._build_taxes(base_record)

        assert len(taxes) == 4

        descriptions = [t.description for t in taxes]
        assert "CPP" in descriptions
        assert "EI" in descriptions
        assert "Federal Tax" in descriptions
        assert "Provincial Tax" in descriptions

    def test_cpp_combines_base_and_additional(
        self, builder: PaystubDataBuilder, base_record: MagicMock
    ):
        """Test that CPP combines base and additional contributions."""
        taxes = builder._build_taxes(base_record)

        cpp_line = next(t for t in taxes if t.description == "CPP")
        # CPP = cpp_employee + cpp_additional = 100 + 20 = 120, shown as negative
        assert cpp_line.current == Decimal("-120")

    def test_taxes_are_negative(self, builder: PaystubDataBuilder, base_record: MagicMock):
        """Test that all tax values are negative (deductions)."""
        taxes = builder._build_taxes(base_record)

        for tax in taxes:
            assert tax.current < 0
            assert tax.ytd < 0

    def test_zero_taxes_not_included(self, builder: PaystubDataBuilder):
        """Test that zero taxes are not included in output."""
        record = MagicMock()
        record.cpp_employee = Decimal("0")
        record.cpp_additional = Decimal("0")
        record.ei_employee = Decimal("0")
        record.federal_tax = Decimal("0")
        record.provincial_tax = Decimal("0")
        record.ytd_cpp = Decimal("0")
        record.ytd_ei = Decimal("0")
        record.ytd_federal_tax = Decimal("0")
        record.ytd_provincial_tax = Decimal("0")

        taxes = builder._build_taxes(record)

        assert len(taxes) == 0


class TestBuildBenefits:
    """Tests for _build_benefits method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    @pytest.fixture
    def group_benefits(self) -> MagicMock:
        """Create a group benefits mock with all enabled."""
        gb = MagicMock()
        gb.enabled = True

        # Health - non-taxable
        gb.health = MagicMock()
        gb.health.enabled = True
        gb.health.employer_contribution = Decimal("100")
        gb.health.employee_deduction = Decimal("50")
        gb.health.is_taxable = False

        # Dental - non-taxable
        gb.dental = MagicMock()
        gb.dental.enabled = True
        gb.dental.employer_contribution = Decimal("50")
        gb.dental.employee_deduction = Decimal("25")
        gb.dental.is_taxable = False

        # Vision - non-taxable
        gb.vision = MagicMock()
        gb.vision.enabled = True
        gb.vision.employer_contribution = Decimal("30")
        gb.vision.employee_deduction = Decimal("15")
        gb.vision.is_taxable = False

        # Life insurance - always taxable for employer contrib
        gb.life_insurance = MagicMock()
        gb.life_insurance.enabled = True
        gb.life_insurance.employer_contribution = Decimal("40")
        gb.life_insurance.employee_deduction = Decimal("20")
        gb.life_insurance.is_taxable = True

        # Disability - taxable
        gb.disability = MagicMock()
        gb.disability.enabled = True
        gb.disability.employer_contribution = Decimal("60")
        gb.disability.employee_deduction = Decimal("30")
        gb.disability.is_taxable = True

        return gb

    def test_separates_taxable_and_non_taxable(
        self, builder: PaystubDataBuilder, group_benefits: MagicMock
    ):
        """Test that benefits are separated into taxable and non-taxable."""
        non_taxable, taxable, deductions = builder._build_benefits(group_benefits, [])

        # Health, Dental, Vision are non-taxable
        assert len(non_taxable) == 3
        # Life and Disability are taxable
        assert len(taxable) == 2
        # All employee deductions
        assert len(deductions) == 5

    def test_calculates_ytd_correctly(self, builder: PaystubDataBuilder, group_benefits: MagicMock):
        """Test that YTD is calculated based on period count."""
        hist_record = MagicMock()  # One historical record

        non_taxable, _, _ = builder._build_benefits(group_benefits, [hist_record])

        # With 1 historical record + 1 current period = 2 periods
        health_line = next(b for b in non_taxable if "Health" in b.description)
        assert health_line.ytd == Decimal("200")  # 100 * 2 periods

    def test_deductions_are_negative(self, builder: PaystubDataBuilder, group_benefits: MagicMock):
        """Test that employee deductions are negative."""
        _, _, deductions = builder._build_benefits(group_benefits, [])

        for d in deductions:
            assert d.current < 0
            assert d.ytd < 0

    def test_disabled_benefits_not_included(self, builder: PaystubDataBuilder):
        """Test that disabled benefits are not included."""
        gb = MagicMock()
        gb.enabled = True

        # All benefits disabled
        gb.health = MagicMock()
        gb.health.enabled = False
        gb.dental = MagicMock()
        gb.dental.enabled = False
        gb.vision = MagicMock()
        gb.vision.enabled = False
        gb.life_insurance = MagicMock()
        gb.life_insurance.enabled = False
        gb.disability = MagicMock()
        gb.disability.enabled = False

        non_taxable, taxable, deductions = builder._build_benefits(gb, [])

        assert len(non_taxable) == 0
        assert len(taxable) == 0
        assert len(deductions) == 0

    def test_zero_contributions_not_included(self, builder: PaystubDataBuilder):
        """Test that zero contribution benefits are not included."""
        gb = MagicMock()
        gb.enabled = True

        gb.health = MagicMock()
        gb.health.enabled = True
        gb.health.employer_contribution = Decimal("0")
        gb.health.employee_deduction = Decimal("0")
        gb.health.is_taxable = False

        gb.dental = MagicMock()
        gb.dental.enabled = False
        gb.vision = MagicMock()
        gb.vision.enabled = False
        gb.life_insurance = MagicMock()
        gb.life_insurance.enabled = False
        gb.disability = MagicMock()
        gb.disability.enabled = False

        non_taxable, taxable, deductions = builder._build_benefits(gb, [])

        assert len(non_taxable) == 0
        assert len(taxable) == 0
        assert len(deductions) == 0


class TestBuildVacation:
    """Tests for _build_vacation method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    def test_vacation_info_with_balance(self, builder: PaystubDataBuilder):
        """Test vacation info when there's a balance."""
        record = MagicMock()
        record.vacation_accrued = Decimal("100")
        record.vacation_pay_paid = Decimal("0")
        record.vacation_hours_taken = Decimal("0")

        employee = MagicMock()
        employee.vacation_balance = Decimal("500")

        vacation = builder._build_vacation(record, employee)

        assert vacation is not None
        assert vacation.earned == Decimal("100")
        assert vacation.available == Decimal("600")  # 500 + 100 - 0

    def test_vacation_info_with_hours_taken(self, builder: PaystubDataBuilder):
        """Test vacation info when hours are taken."""
        record = MagicMock()
        record.vacation_accrued = Decimal("100")
        record.vacation_pay_paid = Decimal("200")
        record.vacation_hours_taken = Decimal("8")

        employee = MagicMock()
        employee.vacation_balance = Decimal("500")

        vacation = builder._build_vacation(record, employee)

        assert vacation is not None
        assert vacation.ytdUsed == Decimal("8")
        assert vacation.available == Decimal("400")  # 500 + 100 - 200

    def test_vacation_info_none_when_no_activity(self, builder: PaystubDataBuilder):
        """Test vacation info is None when no vacation activity."""
        record = MagicMock()
        record.vacation_accrued = Decimal("0")
        record.vacation_pay_paid = Decimal("0")
        record.vacation_hours_taken = Decimal("0")

        employee = MagicMock()
        employee.vacation_balance = Decimal("0")

        vacation = builder._build_vacation(record, employee)

        assert vacation is None


class TestBuildSickLeave:
    """Tests for _build_sick_leave method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    def test_sick_leave_with_balance(self, builder: PaystubDataBuilder):
        """Test sick leave info when there's a balance."""
        employee = MagicMock()
        employee.sick_balance = Decimal("5")

        sick_leave = builder._build_sick_leave(employee)

        assert sick_leave is not None
        assert sick_leave.paidDaysRemaining == Decimal("5")

    def test_sick_leave_none_when_no_balance(self, builder: PaystubDataBuilder):
        """Test sick leave info is None when no balance."""
        employee = MagicMock()
        employee.sick_balance = Decimal("0")

        sick_leave = builder._build_sick_leave(employee)

        assert sick_leave is None

    def test_sick_leave_none_balance(self, builder: PaystubDataBuilder):
        """Test sick leave info when balance is None."""
        employee = MagicMock()
        employee.sick_balance = None

        sick_leave = builder._build_sick_leave(employee)

        assert sick_leave is None


class TestCalculateYtdNetPay:
    """Tests for _calculate_ytd_net_pay method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    def test_ytd_net_pay_with_history(self, builder: PaystubDataBuilder):
        """Test YTD net pay calculation with historical records."""
        current = MagicMock()
        current.net_pay = Decimal("2000")

        hist1 = MagicMock()
        hist1.net_pay = Decimal("1800")
        hist2 = MagicMock()
        hist2.net_pay = Decimal("1900")

        ytd_net = builder._calculate_ytd_net_pay(current, [hist1, hist2])

        assert ytd_net == Decimal("5700")  # 2000 + 1800 + 1900

    def test_ytd_net_pay_without_history(self, builder: PaystubDataBuilder):
        """Test YTD net pay with no historical records."""
        current = MagicMock()
        current.net_pay = Decimal("2000")

        ytd_net = builder._calculate_ytd_net_pay(current, [])

        assert ytd_net == Decimal("2000")


class TestBuildPayRate:
    """Tests for _build_pay_rate method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    def test_pay_rate_with_annual_salary(self, builder: PaystubDataBuilder):
        """Test pay rate with annual salary."""
        employee = MagicMock()
        employee.annual_salary = Decimal("75000")
        employee.hourly_rate = None

        pay_rate = builder._build_pay_rate(employee)

        assert pay_rate == "$75,000.00/yr"

    def test_pay_rate_with_hourly_rate(self, builder: PaystubDataBuilder):
        """Test pay rate with hourly rate."""
        employee = MagicMock()
        employee.annual_salary = None
        employee.hourly_rate = Decimal("25.50")

        pay_rate = builder._build_pay_rate(employee)

        assert pay_rate == "$25.50/hr"

    def test_pay_rate_prefers_salary_over_hourly(self, builder: PaystubDataBuilder):
        """Test that salary is preferred over hourly rate."""
        employee = MagicMock()
        employee.annual_salary = Decimal("75000")
        employee.hourly_rate = Decimal("25.50")

        pay_rate = builder._build_pay_rate(employee)

        assert pay_rate == "$75,000.00/yr"

    def test_pay_rate_none_when_no_rate(self, builder: PaystubDataBuilder):
        """Test pay rate is None when no rate set."""
        employee = MagicMock()
        employee.annual_salary = None
        employee.hourly_rate = None

        pay_rate = builder._build_pay_rate(employee)

        assert pay_rate is None

    def test_pay_rate_none_when_zero_values(self, builder: PaystubDataBuilder):
        """Test pay rate is None when values are zero."""
        employee = MagicMock()
        employee.annual_salary = Decimal("0")
        employee.hourly_rate = Decimal("0")

        pay_rate = builder._build_pay_rate(employee)

        assert pay_rate is None


class TestBuildFullPaystub:
    """Tests for the full build method."""

    @pytest.fixture
    def builder(self) -> PaystubDataBuilder:
        """Create a PaystubDataBuilder instance."""
        return PaystubDataBuilder()

    @pytest.fixture
    def mock_record(self) -> MagicMock:
        """Create a mock payroll record."""
        record = MagicMock()
        record.gross_regular = Decimal("2000")
        record.gross_overtime = Decimal("200")
        record.holiday_pay = Decimal("0")
        record.holiday_premium_pay = Decimal("0")
        record.vacation_pay_paid = Decimal("0")
        record.other_earnings = Decimal("0")
        record.bonus_earnings = Decimal("0")
        record.cpp_employee = Decimal("100")
        record.cpp_additional = Decimal("10")
        record.ei_employee = Decimal("50")
        record.federal_tax = Decimal("300")
        record.provincial_tax = Decimal("150")
        record.ytd_gross = Decimal("4400")
        record.ytd_cpp = Decimal("220")
        record.ytd_ei = Decimal("100")
        record.ytd_federal_tax = Decimal("600")
        record.ytd_provincial_tax = Decimal("300")
        record.vacation_accrued = Decimal("88")
        record.vacation_hours_taken = Decimal("0")
        record.net_pay = Decimal("1590")
        return record

    @pytest.fixture
    def mock_employee(self) -> MagicMock:
        """Create a mock employee."""
        emp = MagicMock()
        emp.first_name = "John"
        emp.last_name = "Doe"
        emp.address_street = "123 Main St"
        emp.address_city = "Toronto"
        emp.province_of_employment = MagicMock()
        emp.province_of_employment.value = "ON"
        emp.address_postal_code = "M5V 1A1"
        emp.occupation = "Developer"
        emp.annual_salary = Decimal("52000")
        emp.hourly_rate = None
        emp.vacation_balance = Decimal("500")
        emp.sick_balance = Decimal("5")
        return emp

    @pytest.fixture
    def mock_payroll_run(self) -> MagicMock:
        """Create a mock payroll run."""
        run = MagicMock()
        run.period_start = date(2025, 1, 1)
        run.period_end = date(2025, 1, 15)
        run.pay_date = date(2025, 1, 17)
        return run

    @pytest.fixture
    def mock_company(self) -> MagicMock:
        """Create a mock company."""
        company = MagicMock()
        company.company_name = "Acme Corp"
        company.address_street = "456 Business Ave"
        company.address_city = "Toronto"
        company.province = MagicMock()
        company.province.value = "ON"
        company.address_postal_code = "M5V 2B2"
        company.logo_url = None
        return company

    def test_build_complete_paystub(
        self,
        builder: PaystubDataBuilder,
        mock_record: MagicMock,
        mock_employee: MagicMock,
        mock_payroll_run: MagicMock,
        mock_company: MagicMock,
    ):
        """Test building a complete paystub."""
        paystub = builder.build(
            record=mock_record,
            employee=mock_employee,
            payroll_run=mock_payroll_run,
            pay_group=None,
            company=mock_company,
            ytd_records=[],
            masked_sin="***-***-123",
        )

        assert paystub.employeeName == "John Doe"
        assert "123 Main St" in paystub.employeeAddress
        assert paystub.sinMasked == "***-***-123"
        assert paystub.occupation == "Developer"
        assert paystub.employerName == "Acme Corp"
        assert paystub.periodStart == date(2025, 1, 1)
        assert paystub.periodEnd == date(2025, 1, 15)
        assert paystub.payDate == date(2025, 1, 17)
        assert paystub.netPay == Decimal("1590")
        assert paystub.payRate == "$52,000.00/yr"

    def test_build_paystub_without_masked_sin(
        self,
        builder: PaystubDataBuilder,
        mock_record: MagicMock,
        mock_employee: MagicMock,
        mock_payroll_run: MagicMock,
        mock_company: MagicMock,
    ):
        """Test building paystub without providing masked SIN."""
        paystub = builder.build(
            record=mock_record,
            employee=mock_employee,
            payroll_run=mock_payroll_run,
            pay_group=None,
            company=mock_company,
            ytd_records=[],
        )

        # Should use placeholder
        assert paystub.sinMasked == "***-***-***"

    def test_build_paystub_with_logo_bytes(
        self,
        builder: PaystubDataBuilder,
        mock_record: MagicMock,
        mock_employee: MagicMock,
        mock_payroll_run: MagicMock,
        mock_company: MagicMock,
    ):
        """Test building paystub with logo bytes."""
        logo_bytes = b"PNG_DATA_HERE"

        paystub = builder.build(
            record=mock_record,
            employee=mock_employee,
            payroll_run=mock_payroll_run,
            pay_group=None,
            company=mock_company,
            ytd_records=[],
            logo_bytes=logo_bytes,
        )

        assert paystub.logoBytes == logo_bytes

    def test_build_paystub_with_pay_group_benefits(
        self,
        builder: PaystubDataBuilder,
        mock_record: MagicMock,
        mock_employee: MagicMock,
        mock_payroll_run: MagicMock,
        mock_company: MagicMock,
    ):
        """Test building paystub with pay group benefits."""
        pay_group = MagicMock()
        pay_group.group_benefits = MagicMock()
        pay_group.group_benefits.enabled = True
        pay_group.group_benefits.health = MagicMock()
        pay_group.group_benefits.health.enabled = True
        pay_group.group_benefits.health.employer_contribution = Decimal("100")
        pay_group.group_benefits.health.employee_deduction = Decimal("50")
        pay_group.group_benefits.health.is_taxable = False
        pay_group.group_benefits.dental = MagicMock()
        pay_group.group_benefits.dental.enabled = False
        pay_group.group_benefits.vision = MagicMock()
        pay_group.group_benefits.vision.enabled = False
        pay_group.group_benefits.life_insurance = MagicMock()
        pay_group.group_benefits.life_insurance.enabled = False
        pay_group.group_benefits.disability = MagicMock()
        pay_group.group_benefits.disability.enabled = False

        paystub = builder.build(
            record=mock_record,
            employee=mock_employee,
            payroll_run=mock_payroll_run,
            pay_group=pay_group,
            company=mock_company,
            ytd_records=[],
        )

        assert len(paystub.nonTaxableBenefits) == 1
        assert paystub.nonTaxableBenefits[0].description == "Health - Employer"
        assert len(paystub.benefitDeductions) == 1
        assert paystub.benefitDeductions[0].description == "Health - Employee"
