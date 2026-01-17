import sys
from decimal import Decimal, ROUND_HALF_UP

# =============================================================================
# CONSTANTS 2026
# =============================================================================

# CPP/EI 2026
CPP_RATE_TOTAL = Decimal("0.0595")
CPP_RATE_BASE = Decimal("0.0495")
CPP_RATE_ENHANCED = Decimal("0.0100")
CPP_BASIC_EXEMPTION = Decimal("3500.00")
CPP_YMPE = Decimal("74600.00")
CPP_YAMPE = Decimal("85000.00")
CPP_MAX_BASE_CONTRIBUTION = Decimal("4230.45") # 4.95% * (74600 - 3500) presumably approx
# Actually from JSON: 4230.45
CPP2_RATE = Decimal("0.04") # Second bracket

EI_RATE = Decimal("0.0163")
EI_MAX_PREMIUM = Decimal("1123.07") # From JSON

# FEDERAL 2026 (Jan)
FED_BPA = Decimal("16452.00")
FED_CEA = Decimal("1501.00") # Canada Employment Amount
FED_RATES = [
    (Decimal("0"), Decimal("0.14"), Decimal("0")),
    (Decimal("58523"), Decimal("0.205"), Decimal("3804")),
    (Decimal("117045"), Decimal("0.26"), Decimal("10241")),
    (Decimal("181440"), Decimal("0.29"), Decimal("15685")),
    (Decimal("258482"), Decimal("0.33"), Decimal("26024"))
]
FED_K1_RATE = Decimal("0.14")
FED_K2_RATE = Decimal("0.14")
FED_K4_RATE = Decimal("0.14")

# BC 2026 (Jan)
BC_BPA = Decimal("13216.00")
BC_RATES = [
    (Decimal("0"), Decimal("0.0506"), Decimal("0")),
    (Decimal("50363"), Decimal("0.077"), Decimal("1329.58")),
    (Decimal("100728"), Decimal("0.105"), Decimal("4149.96")),
    (Decimal("115648"), Decimal("0.1229"), Decimal("6220.06")),
    (Decimal("140430"), Decimal("0.147"), Decimal("9604.42")),
    (Decimal("190405"), Decimal("0.168"), Decimal("13602.92")),
    (Decimal("265545"), Decimal("0.205"), Decimal("23428.09"))
]
BC_K1P_RATE = Decimal("0.0506") # Lowest bracket rate
BC_TAX_REDUCTION = {
    "base": Decimal("575.00"),
    "rate": Decimal("0.0356"),
    "start": Decimal("25570.00"),
    "end": Decimal("41722.00")
}

# Values from User Request
PAY_PERIODS = 12
REGULAR_GROSS = Decimal("5000.00")
BONUS = Decimal("1000.00")
FED_CLAIM = Decimal("16452.00") # Matches FED_BPA
PROV_CLAIM = Decimal("13216.00") # Matches BC_BPA

def to_currency(d: Decimal) -> Decimal:
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def find_bracket(income: Decimal, brackets: list):
    # brackets expected to be sorted by threshold ascending
    # format: (threshold_upper, rate, constant_from_prev)
    # Actually my constant structure above might be (threshold_start, rate, k) which is standard T4127 Table 1
    # T4127 tables:
    # Income Range | Tax Rate (R) | Constant (K)
    # First bracket usually: 0 to T1 | R1 | 0
    # Second: T1 to T2 | R2 | K2 = R2*T1 - Tax(T1) ...
    
    # My FED_RATES above:
    # 58523, 0.14, 0 -> Up to 58523.
    # Actually wait. T4127 Table usually says:
    # "Taxable Income ... Not over 58,523 ... Pay 14%"
    # "Over 58,523 but not over 117,045 ... Pay 20.5% on excess over 58,523 plus 8,193" <-- No, T4127 option 1 method uses K constant.
    # Formula: T3 = (R x A) - K.
    # Let's verify K for bracket 2.
    # At 58523.01. Tax should be roughly 14% of first bracket. 
    # Logic: K corrects for the lower rate on previous brackets.
    # K = (CurrentRate - PrevRate) * Threshold + PrevK
    # K1 = 0
    # K2 = (0.205 - 0.14) * 58523 = 0.065 * 58523 = 3803.995 -> 3804. YES.
    
    # So my structure (Threshold, Rate, Constant) uses Threshold as the UPPER bound of previous?
    # No, typically "Threshold" in configs is the START of the bracket.
    # JSON said: { "threshold": 58523, "rate": 0.205, "constant": 3804 }
    # This means IF >= 58523, use this.
    
    selected_r = Decimal("0")
    selected_k = Decimal("0")
    
    # Assuming list is sorted by threshold ASC
    # We want the highest threshold that is <= income
    
    # My arrays above:
    # (58523, ...) which is the START of 2nd bracket in JSON.
    # First bracket is 0.
    
    # Re-structuring FED_RATES to match logic:
    # using checks >= threshold.
    
    # Just iterate and keep the last one that matches
    r = Decimal("0")
    k = Decimal("0")
    for thresh, rate, const in brackets:
        if income >= thresh:
            r = rate
            k = const
        else:
            break
    return r, k

def calc_cpp_deduction(gross: Decimal, is_bonus: bool = False):
    # Simplified for this specific test case (Income < YMPE)
    # Returns (Total_Ded, Base_Contrib, Enhanced_Ded)
    # Note: F5 = Enhanced + CPP2.
    # Contrib = Base + Enhanced + CPP2.
    
    if gross <= 0: return Decimal(0), Decimal(0), Decimal(0)
    
    # Per Pay Exemption
    exemption = CPP_BASIC_EXEMPTION / PAY_PERIODS
    
    # For Bonus: T4127 usually says "Take 5.95% of bonus, no exemption if paid with regular?" or something.
    # BUT Step 1 calculation annualizes.
    # We will compute annualized CPP deduction carefully.
    
    # ACTUALLY, strict T4127 Step 1:
    # F5A = CPP deduction allocated to regular pay.
    # F5B = CPP deduction allocated to bonus.
    
    # For Regular Pay (5000):
    contributory = max(Decimal(0), gross - exemption)
    # Check YMPE limits?
    # Annualized gross = 60000. < 74600. So no YMPE cap per period effectively if simple.
    
    base = to_currency(contributory * CPP_RATE_BASE)
    enhanced = to_currency(contributory * CPP_RATE_ENHANCED)
    
    return base, enhanced

def calc_bonus_cpp(bonus_amount: Decimal):
    # Bonus CPP usually has no exemption applied if paid with regular?
    # Or strict T4127 bonus method:
    # "Deduct CPP... from the bonus... limit to max"
    # We assume regular pay already took exemption?
    # In this specific case matches PDOC:
    # PDOC Input: 5000 reg, 1000 bonus.
    # 5000 uses exemption. 
    # 1000 uses NO exemption?
    
    base = to_currency(bonus_amount * CPP_RATE_BASE)
    enhanced = to_currency(bonus_amount * CPP_RATE_ENHANCED)
    return base, enhanced

# -----------------
# EXECUTION
# -----------------

print("--- DEBUG T4127 BONUS CALCULATION 2026 ---")

# 1. SETUP VALUES
P = Decimal(PAY_PERIODS)
I = REGULAR_GROSS
B = BONUS
F = Decimal(0) # RRSP
U1 = Decimal(0) # Union

# CPP Calculation (Reg)
cpp_reg_base, cpp_reg_enh = calc_cpp_deduction(I)
# F5A = Enhanced part (plus C2 if any, none here)
F5A = cpp_reg_enh
print(f"Regular Pay: {I}")
print(f"CPP Reg Base: {cpp_reg_base}, Enhanced (F5A): {F5A}")

# CPP Calculation (Bonus)
cpp_bonus_base, cpp_bonus_enh = calc_bonus_cpp(B)
F5B = cpp_bonus_enh
print(f"Bonus Pay: {B}")
print(f"CPP Bonus Base: {cpp_bonus_base}, Enhanced (F5B): {F5B}")

# K2 Credit Calculation
ei_reg = to_currency(I * EI_RATE)
ei_bonus = to_currency(B * EI_RATE)

# 1. Regular K2 (for Step 2)
annual_cpp_base_reg = min(cpp_reg_base * P, CPP_MAX_BASE_CONTRIBUTION)
annual_ei_reg = min(ei_reg * P, EI_MAX_PREMIUM)
print(f"Annual Reg Base CPP: {annual_cpp_base_reg}")
print(f"Annual Reg EI: {annual_ei_reg}")

# 2. Total K2 (for Step 1)
annual_cpp_base_total = (cpp_reg_base * P) + cpp_bonus_base
annual_cpp_base_total = min(annual_cpp_base_total, CPP_MAX_BASE_CONTRIBUTION)
print(f"Annual Max Base CPP: {CPP_MAX_BASE_CONTRIBUTION}")
print(f"Total Annual Base CPP for K2: {annual_cpp_base_total}")

annual_ei_total = (ei_reg * P) + ei_bonus
annual_ei_total = min(annual_ei_total, EI_MAX_PREMIUM)
print(f"Total Annual EI for K2: {annual_ei_total}")

# 2. CALCULATE STEP 1 INCOME (Annualized with Bonus)
# A = [P × (I – F – F2 – F5A – U1)] – HD – F1 + (B – F3 – F5B) + (B1 – F4 – F5BYTD)
term1 = P * (I - F - Decimal(0) - F5A - U1)
term2 = (B - Decimal(0) - F5B)
A1 = term1 + term2
print(f"\nStep 1 Annual Income A: {A1}")

# 3. CALCULATE STEP 2 INCOME (Annualized without Bonus)
# A = [P × (I – F – F2 – F5A – U1)] – HD – F1 + (B1 – F4 – F5BYTD)
term2_step2 = Decimal(0) # Since B1=0
A2 = term1 + term2_step2
print(f"Step 2 Annual Income A: {A2}")

# 4. TAX CALCULATION FUNCTION
def calculate_fed_tax(AnnualIncome, k2_base_cpp, k2_ei):
    # T3 = (R × A) - K - K1 - K2 - K3 - K4
    A = AnnualIncome
    R, K = find_bracket(A, FED_RATES)
    
    # K1
    K1 = to_currency(FED_CLAIM * FED_K1_RATE)
    # K2
    K2 = to_currency((k2_base_cpp + k2_ei) * FED_K2_RATE)
    # K4 (CEA)
    # Lesser of 0.14*A or 0.14*CEA
    k4_a = to_currency(A * FED_K4_RATE)
    k4_max = to_currency(FED_CEA * FED_K4_RATE)
    K4 = min(k4_a, k4_max)
    
    T3 = (R * A) - K - K1 - K2 - Decimal(0) - K4
    T3 = max(T3, Decimal(0))
    
    return T3

def calculate_bc_tax(AnnualIncome, k2_base_cpp, k2_ei):
    # BC Tax
    A = AnnualIncome
    R, K = find_bracket(A, BC_RATES)
    
    K1P = to_currency(PROV_CLAIM * BC_K1P_RATE)
    K2P = to_currency((k2_base_cpp + k2_ei) * BC_K1P_RATE)
    
    BasicProvTax = (R * A) - K - K1P - K2P
    BasicProvTax = max(BasicProvTax, Decimal(0))
    
    # Tax Reduction
    NI = A
    reduction = Decimal(0)
    if NI <= BC_TAX_REDUCTION["start"]:
        reduction = BC_TAX_REDUCTION["base"]
    elif NI > BC_TAX_REDUCTION["end"]:
        reduction = Decimal(0)
    else:
        diff = NI - BC_TAX_REDUCTION["start"]
        clawback = to_currency(diff * BC_TAX_REDUCTION["rate"])
        reduction = BC_TAX_REDUCTION["base"] - clawback
        reduction = max(reduction, Decimal(0))
        
    ProvTax = BasicProvTax - reduction
    ProvTax = max(ProvTax, Decimal(0))
    
    return ProvTax

# 5. EXECUTE CALCULATIONS
# CRITICAL FINDING:
# To match PDOC Total Tax (638.60), we MUST use separate K2 values for Step 1 and Step 2.
# - Step 1 (Income + Bonus) uses K2 based on Reg + Bonus CPP.
# - Step 2 (Income Only) uses K2 based on Reg CPP Only.
# This ensures that the "Tax on Bonus" (Tax1 - Tax2) is reduced by the additional K2 credit generated by the bonus.
# If we used the SAME K2 for both (as per some interpretations), the Total Tax would be much lower (577.75) 
# because Step 2 Tax would be lower (higher credit), leading to a much smaller Step 1 - Step 2 difference.
#
# Current Result with Separate K2:
# Total Fed: 638.60 (Match Clean)
# Splits are off by +/- 0.10, likely due to rounding differences in 'Tax on Income' definition.

# Step 1 Tax uses TOTAL K2
fed_tax_1 = calculate_fed_tax(A1, annual_cpp_base_total, annual_ei_total)
bc_tax_1 = calculate_bc_tax(A1, annual_cpp_base_total, annual_ei_total)

# Step 2 Tax uses REGULAR K2
fed_tax_2 = calculate_fed_tax(A2, annual_cpp_base_reg, annual_ei_reg)
bc_tax_2 = calculate_bc_tax(A2, annual_cpp_base_reg, annual_ei_reg)

# Bonus Tax
fed_bonus_tax = fed_tax_1 - fed_tax_2
bc_bonus_tax = bc_tax_1 - bc_tax_2

# Regular Tax (Per Period)
# Regular tax is derived from Tax(Step2) / P ?
# No, "Federal Tax on Income" output in PDOC usually refers to the tax on the REGULAR portion.
# Which is simple annualization of regular pay.
# Step 2 result is the Annualized Regular Tax.
# So Reg Tax Per Period = fed_tax_2 / P
fed_reg_tax = to_currency(fed_tax_2 / P)
bc_reg_tax = to_currency(bc_tax_2 / P)

# Totals
total_fed = fed_reg_tax + fed_bonus_tax
total_bc = bc_reg_tax + bc_bonus_tax

print("\n--- RESULTS ---")
print(f"Federal Tax on Income: {fed_reg_tax} (Expected: 444.76)")
print(f"Federal Tax on Bonus: {fed_bonus_tax} (Expected: 193.84)")
print(f"Total Federal: {total_fed} (Expected: 638.60)")
print("---")
print(f"Provincial Tax on Income: {bc_reg_tax} (Expected: 198.86)")
print(f"Provincial Tax on Bonus: {bc_bonus_tax} (Expected: 72.94)")
print(f"Total Provincial: {total_bc} (Expected: 271.80)")

print("\n--- DIFF ---")
print(f"Fed Income Diff: {fed_reg_tax - Decimal('444.76')}")
print(f"Fed Bonus Diff: {fed_bonus_tax - Decimal('193.84')}")
print(f"Prov Income Diff: {bc_reg_tax - Decimal('198.86')}")
print(f"Prov Bonus Diff: {bc_bonus_tax - Decimal('72.94')}")
