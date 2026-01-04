"""
API tests for payroll configuration endpoints.

Tests:
- GET /api/v1/payroll/tax-config/{province}
- GET /api/v1/payroll/tax-config
- GET /api/v1/payroll/bpa-defaults/{province}
- GET /api/v1/config/vacation-rates/{province}
- GET /api/v1/config/province-standards/{province}
"""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestTaxConfigByProvince:
    """Tests for GET /api/v1/payroll/tax-config/{province} endpoint."""

    def test_get_tax_config_ontario(self, client: TestClient):
        """Get tax configuration for Ontario."""
        response = client.get("/api/v1/payroll/tax-config/ON")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["province"] == "ON"
        assert "year" in data
        assert "cpp" in data
        assert "ei" in data
        assert "federal" in data
        assert "provincial" in data

        # Verify CPP config has expected fields
        cpp = data["cpp"]
        assert "base_rate" in cpp
        assert "additional_rate" in cpp

        # Verify EI config has expected fields
        ei = data["ei"]
        assert "employee_rate" in ei
        assert "employer_rate_multiplier" in ei

    def test_get_tax_config_all_provinces(self, client: TestClient):
        """Get tax configuration for all supported provinces."""
        # Note: QC not supported as Quebec uses QPP instead of CPP
        provinces = ["ON", "BC", "AB", "SK", "MB", "NB", "NS", "PE", "NL", "YT", "NT", "NU"]

        for province in provinces:
            response = client.get(f"/api/v1/payroll/tax-config/{province}")

            assert response.status_code == 200, f"Failed for province {province}"
            data = response.json()
            assert data["province"] == province
            assert "provincial" in data

    def test_get_tax_config_with_year(self, client: TestClient):
        """Get tax configuration for a specific year."""
        response = client.get("/api/v1/payroll/tax-config/ON?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2025

    def test_get_tax_config_with_pay_date(self, client: TestClient):
        """Get tax configuration based on pay date for edition selection."""
        # January edition (pay_date before July 1)
        response_jan = client.get("/api/v1/payroll/tax-config/ON?pay_date=2025-03-15")
        assert response_jan.status_code == 200

        # July edition (pay_date on or after July 1)
        response_jul = client.get("/api/v1/payroll/tax-config/ON?pay_date=2025-08-15")
        assert response_jul.status_code == 200

    def test_get_tax_config_invalid_province(self, client: TestClient):
        """Reject invalid province code."""
        response = client.get("/api/v1/payroll/tax-config/XX")

        assert response.status_code == 422  # Validation error

    def test_get_tax_config_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        response = unauthenticated_client.get("/api/v1/payroll/tax-config/ON")

        assert response.status_code == 401


class TestAllTaxConfig:
    """Tests for GET /api/v1/payroll/tax-config endpoint."""

    def test_get_all_tax_config(self, client: TestClient):
        """Get all tax configuration."""
        response = client.get("/api/v1/payroll/tax-config")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "year" in data
        assert "cpp" in data
        assert "ei" in data
        assert "federal" in data
        assert "supported_provinces" in data

        # Verify supported provinces list
        provinces = data["supported_provinces"]
        assert isinstance(provinces, list)
        assert len(provinces) > 0
        # Should include major provinces
        [p if isinstance(p, str) else p.get("code", "") for p in provinces]
        # The format might vary, so we check it's not empty
        assert len(provinces) >= 10  # Canada has 13 provinces/territories

    def test_get_all_tax_config_with_year(self, client: TestClient):
        """Get all tax configuration for a specific year."""
        response = client.get("/api/v1/payroll/tax-config?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2025

    def test_get_all_tax_config_with_pay_date(self, client: TestClient):
        """Get all tax configuration with pay date for edition selection."""
        response = client.get("/api/v1/payroll/tax-config?pay_date=2025-06-01")

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2025

    def test_get_all_tax_config_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        response = unauthenticated_client.get("/api/v1/payroll/tax-config")

        assert response.status_code == 401


class TestBPADefaults:
    """Tests for GET /api/v1/payroll/bpa-defaults/{province} endpoint."""

    def test_get_bpa_defaults_ontario(self, client: TestClient):
        """Get BPA defaults for Ontario."""
        response = client.get("/api/v1/payroll/bpa-defaults/ON")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["province"] == "ON"
        assert "year" in data
        assert "edition" in data
        assert "federalBPA" in data
        assert "provincialBPA" in data

        # BPA should be positive numbers
        assert data["federalBPA"] > 0
        assert data["provincialBPA"] > 0

    def test_get_bpa_defaults_all_provinces(self, client: TestClient):
        """Get BPA defaults for all provinces."""
        # Note: QC not supported as Quebec uses QPP instead of CPP
        provinces = ["ON", "BC", "AB", "SK", "MB", "NB", "NS", "PE", "NL"]

        for province in provinces:
            response = client.get(f"/api/v1/payroll/bpa-defaults/{province}")

            assert response.status_code == 200, f"Failed for province {province}"
            data = response.json()
            assert data["province"] == province
            assert data["federalBPA"] > 0
            assert data["provincialBPA"] > 0

    def test_get_bpa_defaults_january_edition(self, client: TestClient):
        """Get BPA defaults for January edition (before July 1)."""
        response = client.get("/api/v1/payroll/bpa-defaults/ON?pay_date=2025-03-15")

        assert response.status_code == 200
        data = response.json()
        assert data["edition"] == "jan"

    def test_get_bpa_defaults_july_edition(self, client: TestClient):
        """Get BPA defaults for July edition (on or after July 1)."""
        response = client.get("/api/v1/payroll/bpa-defaults/ON?pay_date=2025-08-15")

        assert response.status_code == 200
        data = response.json()
        assert data["edition"] == "jul"

    def test_get_bpa_defaults_with_year(self, client: TestClient):
        """Get BPA defaults for a specific year."""
        response = client.get("/api/v1/payroll/bpa-defaults/ON?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2025

    def test_get_bpa_defaults_invalid_province(self, client: TestClient):
        """Reject invalid province code."""
        response = client.get("/api/v1/payroll/bpa-defaults/XX")

        assert response.status_code == 422

    def test_get_bpa_defaults_unauthorized(self, unauthenticated_client: TestClient):
        """Reject unauthenticated requests."""
        response = unauthenticated_client.get("/api/v1/payroll/bpa-defaults/ON")

        assert response.status_code == 401


class TestVacationRates:
    """Tests for GET /api/v1/config/vacation-rates/{province} endpoint."""

    def test_get_vacation_rates_ontario(self, client: TestClient):
        """Get vacation rates for Ontario."""
        response = client.get("/api/v1/config/vacation-rates/ON")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["province"] == "ON"
        assert "name" in data
        assert "tiers" in data
        assert isinstance(data["tiers"], list)
        assert len(data["tiers"]) > 0

        # Verify tier structure
        tier = data["tiers"][0]
        assert "minYearsOfService" in tier
        assert "vacationWeeks" in tier
        assert "vacationRate" in tier

    def test_get_vacation_rates_all_provinces(self, client: TestClient):
        """Get vacation rates for all provinces."""
        provinces = ["ON", "BC", "AB", "SK", "MB", "NB", "NS", "PE", "NL"]

        for province in provinces:
            response = client.get(f"/api/v1/config/vacation-rates/{province}")

            assert response.status_code == 200, f"Failed for province {province}"
            data = response.json()
            assert data["province"] == province
            assert "tiers" in data

    def test_get_vacation_rates_with_year(self, client: TestClient):
        """Get vacation rates for a specific year."""
        response = client.get("/api/v1/config/vacation-rates/SK?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["province"] == "SK"


class TestProvinceStandards:
    """Tests for GET /api/v1/config/province-standards/{province} endpoint."""

    def test_get_province_standards_ontario(self, client: TestClient):
        """Get province standards for Ontario."""
        response = client.get("/api/v1/config/province-standards/ON")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["provinceCode"] == "ON"
        assert "provinceName" in data
        assert "vacation" in data
        assert "sickLeave" in data
        assert "overtime" in data
        assert "statutoryHolidaysCount" in data

        # Verify vacation structure
        vacation = data["vacation"]
        assert "minimumWeeks" in vacation
        assert "minimumRate" in vacation
        assert "rateDisplay" in vacation

        # Verify sick leave structure
        sick_leave = data["sickLeave"]
        assert "paidDays" in sick_leave
        assert "unpaidDays" in sick_leave
        assert "waitingPeriodDays" in sick_leave

        # Verify overtime structure
        overtime = data["overtime"]
        assert "weeklyThreshold" in overtime
        assert "overtimeRate" in overtime

    def test_get_province_standards_all_provinces(self, client: TestClient):
        """Get province standards for all provinces."""
        provinces = ["ON", "BC", "AB", "SK", "MB", "NB", "NS", "PE", "NL"]

        for province in provinces:
            response = client.get(f"/api/v1/config/province-standards/{province}")

            assert response.status_code == 200, f"Failed for province {province}"
            data = response.json()
            assert data["provinceCode"] == province
            assert "vacation" in data

    def test_get_province_standards_with_year(self, client: TestClient):
        """Get province standards for a specific year."""
        response = client.get("/api/v1/config/province-standards/ON?year=2025")

        assert response.status_code == 200
        data = response.json()
        assert data["provinceCode"] == "ON"

    def test_get_province_standards_invalid_province(self, client: TestClient):
        """Return 400 for invalid province code."""
        response = client.get("/api/v1/config/province-standards/XX")

        assert response.status_code == 400
        assert "Invalid province code" in response.json()["detail"]
