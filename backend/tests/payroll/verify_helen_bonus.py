import logging
import sys
from decimal import Decimal
from datetime import date
from app.services.payroll.payroll_engine import PayrollEngine, EmployeePayrollInput
from app.models.payroll import PayFrequency, Province

# Configure logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def test_helen_zhao_bonus():
    engine = PayrollEngine(year=2026)
    
    # Helen Zhao Case:
    # Monthly, BC, $3333.33 regular, $60000 bonus
    # Federal Claim: 16452, BC Claim: 13216
    
    input_data = EmployeePayrollInput(
        employee_id="helen-zhao",
        province=Province.BC,
        pay_frequency=PayFrequency.MONTHLY,
        gross_regular=Decimal("3333.33"),
        bonus_earnings=Decimal("60000.00"),
        federal_claim_amount=Decimal("16452.00"),
        provincial_claim_amount=Decimal("13216.00"),
        pay_date=date(2026, 2, 1),
        ytd_gross=Decimal("0"),
        ytd_bonus_earnings=Decimal("0"),
        ytd_cpp_base=Decimal("0"),
        ytd_ei=Decimal("0")
    )
    
    result = engine.calculate(input_data)
    
    print(f"Results for Helen Zhao (BC, Monthly, $3333.33 + $60k bonus):")
    print(f"Total Gross: {result.total_gross}")
    print(f"CPP: {result.cpp_total}")
    print(f"EI: {result.ei_employee}")
    print(f"Federal Tax on Income: {result.federal_tax_on_income}")
    print(f"Federal Tax on Bonus: {result.federal_tax_on_bonus}")
    print(f"Provincial Tax on Income: {result.provincial_tax_on_income}")
    print(f"Provincial Tax on Bonus: {result.provincial_tax_on_bonus}")
    print(f"Total Federal Tax: {result.federal_tax}")
    print(f"Total Provincial Tax: {result.provincial_tax}")
    print(f"Net Pay: {result.net_pay}")
    
    # Expected from PDOC:
    # Fed on Income: 223.88
    # Fed on Bonus: 10641.95
    # Prov on Income: 94.60
    # Prov on Bonus: 4254.47
    # CPP: 3750.98
    # EI: 1032.33
    
    diff_fed_bonus = abs(result.federal_tax_on_bonus - Decimal("10641.95"))
    diff_prov_bonus = abs(result.provincial_tax_on_bonus - Decimal("4254.47"))
    
    print(f"\nDiscrepancy (Federal Bonus): {diff_fed_bonus}")
    print(f"Discrepancy (Provincial Bonus): {diff_prov_bonus}")

if __name__ == "__main__":
    test_helen_zhao_bonus()
