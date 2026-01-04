"""
Tests for app/models.payroll module.

Tests Employee model computed fields and serialization.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.payroll import (
    Employee,
    EmployeeCreate,
    EmployeeResponse,
    EmployeeTaxClaim,
    EmployeeTaxClaimBase,
    EmploymentType,
    PayFrequency,
    Province,
    VacationConfig,
)


class TestEmployeeModel:
    """Tests for Employee model."""

    def get_minimal_employee_data(self):
        """Helper to create minimal valid employee data."""
        return {
            "id": uuid4(),
            "user_id": "test-user-id",
            "company_id": "test-company",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "sin_encrypted": "encrypted",
            "province_of_employment": Province.BC,
            "pay_frequency": PayFrequency.BIWEEKLY,
            "hire_date": "2024-01-01",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

    def test_employee_full_name_computed_field(self):
        """Test that full_name computed field works (line 276)."""
        employee = Employee(**self.get_minimal_employee_data())

        # Access the computed field directly
        assert employee.full_name == "John Doe"

    def test_employee_is_active_with_no_termination_date(self):
        """Test that is_active returns True when no termination_date (line 282)."""
        employee = Employee(**self.get_minimal_employee_data())

        assert employee.is_active is True

    def test_employee_is_active_with_termination_date(self):
        """Test that is_active returns False when termination_date is set."""
        data = self.get_minimal_employee_data()
        data["termination_date"] = "2024-12-31"
        employee = Employee(**data)

        assert employee.is_active is False

    def test_employee_model_dump_includes_computed_fields(self):
        """Test that model_dump includes computed fields."""
        employee = Employee(**self.get_minimal_employee_data())

        # model_dump should include computed fields when mode='json'
        data = employee.model_dump(mode='json')
        assert "full_name" in data
        assert data["full_name"] == "John Doe"
        assert "is_active" in data
        assert data["is_active"] is True

    def test_employee_response_has_full_name(self):
        """Test EmployeeResponse includes computed full_name field."""
        response = EmployeeResponse(
            id=uuid4(),
            first_name="Test",
            last_name="User",
            full_name="Test User",
            sin_masked="***-***-999",
            email="test@example.com",
            province_of_employment=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            employment_type=EmploymentType.FULL_TIME,
            address_street="123 Main St",
            address_city="Vancouver",
            address_postal_code="V6B 1A1",
            occupation="Developer",
            annual_salary=Decimal("60000"),
            hourly_rate=None,
            federal_additional_claims=Decimal("0"),
            provincial_additional_claims=Decimal("0"),
            is_cpp_exempt=False,
            is_ei_exempt=False,
            cpp2_exempt=False,
            hire_date=date(2024, 1, 1),
            termination_date=None,
            vacation_config=VacationConfig(),
            vacation_balance=Decimal("0"),
            is_active=True,
            initial_ytd_cpp=Decimal("0"),
            initial_ytd_cpp2=Decimal("0"),
            initial_ytd_ei=Decimal("0"),
            initial_ytd_year=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        assert response.full_name == "Test User"

    def test_employee_serialization_roundtrip(self):
        """Test Employee can be serialized and deserialized with computed fields."""
        data = self.get_minimal_employee_data()
        data["first_name"] = "Alice"
        data["last_name"] = "Johnson"
        data["email"] = "alice@example.com"

        employee = Employee(**data)

        # Serialize to dict
        dumped = employee.model_dump(mode='json')
        assert dumped["full_name"] == "Alice Johnson"
        assert dumped["is_active"] is True

        # The computed fields should be accessible
        assert employee.full_name == "Alice Johnson"
        assert employee.is_active is True


class TestEmployeeValidation:
    """Tests for Employee model validation."""

    def test_employee_requires_hire_date(self):
        """Test that Employee requires hire_date."""
        with pytest.raises(ValidationError) as exc_info:
            Employee(
                id=uuid4(),
                user_id="test-user-id",
                company_id="test-company",
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                sin_encrypted="encrypted",
                province_of_employment=Province.BC,
                pay_frequency=PayFrequency.BIWEEKLY,
                # hire_date is missing
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        assert "hire_date" in str(exc_info.value)

    def test_employee_requires_province_and_frequency(self):
        """Test that Employee requires province and pay_frequency."""
        with pytest.raises(ValidationError) as exc_info:
            Employee(
                id=uuid4(),
                user_id="test-user-id",
                company_id="test-company",
                first_name="John",
                last_name="Doe",
                email="john.doe@example.com",
                sin_encrypted="encrypted",
                hire_date="2024-01-01",
                # Missing province_of_employment and pay_frequency
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

        errors = exc_info.value.errors()
        error_fields = {e["loc"][0] for e in errors}
        assert "province_of_employment" in error_fields
        assert "pay_frequency" in error_fields

    def test_employee_date_fields_accept_strings(self):
        """Test that date fields accept ISO format strings."""
        employee = Employee(
            id=uuid4(),
            user_id="test-user-id",
            company_id="test-company",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            sin_encrypted="encrypted",
            province_of_employment=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            hire_date="2024-01-15",  # String date
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Pydantic auto-converts strings to date objects
        assert employee.hire_date == date(2024, 1, 15)

    def test_employee_date_fields_with_termination(self):
        """Test employee with termination_date field."""
        employee = Employee(
            id=uuid4(),
            user_id="test-user-id",
            company_id="test-company",
            first_name="Jane",
            last_name="Smith",
            email="jane@example.com",
            sin_encrypted="encrypted",
            province_of_employment=Province.ON,
            pay_frequency=PayFrequency.WEEKLY,
            hire_date="2023-01-01",
            termination_date="2024-12-31",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Pydantic auto-converts strings to date objects
        assert employee.hire_date == date(2023, 1, 1)
        assert employee.termination_date == date(2024, 12, 31)
        assert employee.is_active is False


class TestPayFrequencyEnum:
    """Tests for PayFrequency enum."""

    def test_periods_per_year_property(self):
        """Test periods_per_year property for all frequencies (line 51)."""
        assert PayFrequency.WEEKLY.periods_per_year == 52
        assert PayFrequency.BIWEEKLY.periods_per_year == 26
        assert PayFrequency.SEMI_MONTHLY.periods_per_year == 24
        assert PayFrequency.MONTHLY.periods_per_year == 12


class TestEmployeeCreate:
    """Tests for EmployeeCreate model."""

    def test_employee_create_requires_sin(self):
        """Test that EmployeeCreate requires SIN."""
        with pytest.raises(ValidationError) as exc_info:
            EmployeeCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                province_of_employment=Province.BC,
                pay_frequency=PayFrequency.BIWEEKLY,
                hire_date="2024-01-01",
                # SIN is missing
            )

        assert "sin" in str(exc_info.value)

    def test_employee_create_validates_sin_length(self):
        """Test that EmployeeCreate validates SIN length."""
        # Test SIN too short
        with pytest.raises(ValidationError):
            EmployeeCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                sin="12345678",  # Too short
                province_of_employment=Province.BC,
                pay_frequency=PayFrequency.BIWEEKLY,
                hire_date="2024-01-01",
            )

        # Test SIN too long
        with pytest.raises(ValidationError):
            EmployeeCreate(
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                sin="1234567890",  # Too long
                province_of_employment=Province.BC,
                pay_frequency=PayFrequency.BIWEEKLY,
                hire_date="2024-01-01",
            )

    def test_employee_create_accepts_valid_sin(self):
        """Test that EmployeeCreate accepts valid 9-digit SIN."""
        employee = EmployeeCreate(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            sin="123456789",
            province_of_employment=Province.BC,
            pay_frequency=PayFrequency.BIWEEKLY,
            hire_date="2024-01-01",
        )

        assert employee.sin == "123456789"


class TestEmployeeTaxClaim:
    """Tests for EmployeeTaxClaim model."""

    def test_federal_total_claim_computed_field(self):
        """Test federal_total_claim computed field (line 341)."""
        claim = EmployeeTaxClaimBase(
            tax_year=2025,
            federal_bpa=Decimal("15000"),
            federal_additional_claims=Decimal("5000"),
            provincial_bpa=Decimal("10000"),
            provincial_additional_claims=Decimal("3000"),
        )

        assert claim.federal_total_claim == Decimal("20000")

    def test_provincial_total_claim_computed_field(self):
        """Test provincial_total_claim computed field (line 347)."""
        claim = EmployeeTaxClaimBase(
            tax_year=2025,
            federal_bpa=Decimal("15000"),
            federal_additional_claims=Decimal("5000"),
            provincial_bpa=Decimal("10000"),
            provincial_additional_claims=Decimal("3000"),
        )

        assert claim.provincial_total_claim == Decimal("13000")

    def test_total_claim_with_zero_additional(self):
        """Test total claims when additional claims are zero."""
        claim = EmployeeTaxClaimBase(
            tax_year=2025,
            federal_bpa=Decimal("15000"),
            federal_additional_claims=Decimal("0"),
            provincial_bpa=Decimal("10000"),
            provincial_additional_claims=Decimal("0"),
        )

        assert claim.federal_total_claim == Decimal("15000")
        assert claim.provincial_total_claim == Decimal("10000")

    def test_total_claim_serialization(self):
        """Test that total claims are included in serialization."""
        claim = EmployeeTaxClaimBase(
            tax_year=2025,
            federal_bpa=Decimal("15000"),
            federal_additional_claims=Decimal("2000"),
            provincial_bpa=Decimal("10000"),
            provincial_additional_claims=Decimal("1000"),
        )

        # model_dump should include computed fields
        data = claim.model_dump(mode='json')
        assert "federal_total_claim" in data
        assert data["federal_total_claim"] == "17000"
        assert "provincial_total_claim" in data
        assert data["provincial_total_claim"] == "11000"
