"""Tests for benefits calculator."""

from decimal import Decimal

import pytest

from app.services.payroll_run.benefits_calculator import BenefitsCalculator


class TestCalculateBenefitsDeduction:
    """Tests for calculate_benefits_deduction method."""

    def test_disabled_benefits_returns_zero(self):
        """Test that disabled benefits returns zero."""
        group_benefits = {"enabled": False}
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("0")

    def test_empty_benefits_returns_zero(self):
        """Test that empty benefits dict returns zero."""
        group_benefits = {}
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("0")

    def test_health_benefits_only(self):
        """Test health benefits deduction only."""
        group_benefits = {
            "enabled": True,
            "health": {
                "enabled": True,
                "employeeDeduction": 50.00,
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("50")

    def test_dental_benefits_only(self):
        """Test dental benefits deduction only."""
        group_benefits = {
            "enabled": True,
            "dental": {
                "enabled": True,
                "employeeDeduction": 25.50,
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("25.5")

    def test_life_insurance_only(self):
        """Test life insurance deduction only."""
        group_benefits = {
            "enabled": True,
            "lifeInsurance": {
                "enabled": True,
                "employeeDeduction": 15.00,
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("15")

    def test_vision_benefits_only(self):
        """Test vision benefits deduction only."""
        group_benefits = {
            "enabled": True,
            "vision": {
                "enabled": True,
                "employeeDeduction": 10.00,
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("10")

    def test_disability_benefits_only(self):
        """Test disability benefits deduction only."""
        group_benefits = {
            "enabled": True,
            "disability": {
                "enabled": True,
                "employeeDeduction": 20.00,
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("20")

    def test_all_benefits_combined(self):
        """Test all benefits combined."""
        group_benefits = {
            "enabled": True,
            "health": {
                "enabled": True,
                "employeeDeduction": 50.00,
            },
            "dental": {
                "enabled": True,
                "employeeDeduction": 25.00,
            },
            "lifeInsurance": {
                "enabled": True,
                "employeeDeduction": 15.00,
            },
            "vision": {
                "enabled": True,
                "employeeDeduction": 10.00,
            },
            "disability": {
                "enabled": True,
                "employeeDeduction": 20.00,
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        # 50 + 25 + 15 + 10 + 20 = 120
        assert result == Decimal("120")

    def test_disabled_individual_benefits(self):
        """Test that disabled individual benefits are not counted."""
        group_benefits = {
            "enabled": True,
            "health": {
                "enabled": True,
                "employeeDeduction": 50.00,
            },
            "dental": {
                "enabled": False,  # Disabled
                "employeeDeduction": 25.00,
            },
            "lifeInsurance": {
                "enabled": True,
                "employeeDeduction": 15.00,
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        # 50 + 15 = 65 (dental not included)
        assert result == Decimal("65")

    def test_missing_employee_deduction_defaults_to_zero(self):
        """Test that missing employeeDeduction defaults to zero."""
        group_benefits = {
            "enabled": True,
            "health": {
                "enabled": True,
                # employeeDeduction missing
            },
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("0")

    def test_none_benefit_configs(self):
        """Test that None benefit configs are handled."""
        group_benefits = {
            "enabled": True,
            "health": None,
            "dental": None,
        }
        result = BenefitsCalculator.calculate_benefits_deduction(group_benefits)
        assert result == Decimal("0")


class TestCalculateTaxableBenefits:
    """Tests for calculate_taxable_benefits method."""

    def test_disabled_benefits_returns_zero(self):
        """Test that disabled benefits returns zero."""
        group_benefits = {"enabled": False}
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("0")

    def test_empty_benefits_returns_zero(self):
        """Test that empty benefits dict returns zero."""
        group_benefits = {}
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("0")

    def test_life_insurance_employer_contribution(self):
        """Test life insurance employer contribution is taxable."""
        group_benefits = {
            "enabled": True,
            "lifeInsurance": {
                "enabled": True,
                "employerContribution": 100.00,
            },
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("100")

    def test_disabled_life_insurance(self):
        """Test that disabled life insurance returns zero."""
        group_benefits = {
            "enabled": True,
            "lifeInsurance": {
                "enabled": False,
                "employerContribution": 100.00,
            },
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("0")

    def test_zero_employer_contribution(self):
        """Test that zero employer contribution returns zero."""
        group_benefits = {
            "enabled": True,
            "lifeInsurance": {
                "enabled": True,
                "employerContribution": 0,
            },
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("0")

    def test_other_benefits_not_taxable(self):
        """Test that health, dental, vision, disability are NOT taxable."""
        group_benefits = {
            "enabled": True,
            "health": {
                "enabled": True,
                "employerContribution": 200.00,
            },
            "dental": {
                "enabled": True,
                "employerContribution": 100.00,
            },
            "vision": {
                "enabled": True,
                "employerContribution": 50.00,
            },
            "disability": {
                "enabled": True,
                "employerContribution": 75.00,
            },
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        # Only life insurance is taxable, so should be 0
        assert result == Decimal("0")

    def test_mixed_benefits_only_life_taxable(self):
        """Test that only life insurance is counted in taxable benefits."""
        group_benefits = {
            "enabled": True,
            "health": {
                "enabled": True,
                "employerContribution": 200.00,
            },
            "lifeInsurance": {
                "enabled": True,
                "employerContribution": 50.00,
            },
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        # Only life insurance (50) is taxable
        assert result == Decimal("50")

    def test_none_life_insurance_config(self):
        """Test that None life insurance config is handled."""
        group_benefits = {
            "enabled": True,
            "lifeInsurance": None,
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("0")

    def test_missing_employer_contribution(self):
        """Test that missing employerContribution defaults to zero."""
        group_benefits = {
            "enabled": True,
            "lifeInsurance": {
                "enabled": True,
                # employerContribution missing
            },
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("0")

    def test_decimal_precision(self):
        """Test that decimal values are handled correctly."""
        group_benefits = {
            "enabled": True,
            "lifeInsurance": {
                "enabled": True,
                "employerContribution": 123.45,
            },
        }
        result = BenefitsCalculator.calculate_taxable_benefits(group_benefits)
        assert result == Decimal("123.45")
