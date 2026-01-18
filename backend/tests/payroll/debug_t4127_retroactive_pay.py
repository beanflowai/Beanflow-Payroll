#!/usr/bin/env python3
"""
T4127 Retroactive Pay Debug Script

Demonstrates how CRA PDOC calculates tax deductions for retroactive payments.
Reference: CRA T4127 Payroll Deductions Formulas (122nd Edition, January 2026)

KEY DIFFERENCE FROM BONUS:
- Bonus/retro: Taxable bonus (TB) is the difference between annual tax
  with the non-periodic payment and annual tax without it.

Retroactive payments are:
1. FULLY pensionable (CPP) and insurable (EI) in the current period
2. Regular tax withholding uses annual taxable income without the retro pay
3. Additional tax on retro pay (TB) is computed separately
4. Full retroactive amount is paid now (periods applied only affect spread inputs)
"""

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP, getcontext

getcontext().prec = 28


def D(value: str | int | float) -> Decimal:
    return Decimal(str(value))


def round_cent(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def truncate_cent(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_DOWN)


def clamp_min_zero(value: Decimal) -> Decimal:
    return value if value > 0 else Decimal("0")


def find_bracket(annual_income: Decimal, brackets: list[tuple[Decimal, Decimal, Decimal]]) -> tuple[Decimal, Decimal]:
    rate = brackets[0][1]
    constant = brackets[0][2]
    for threshold, bracket_rate, bracket_constant in brackets:
        if annual_income >= threshold:
            rate = bracket_rate
            constant = bracket_constant
    return rate, constant


def money(value: Decimal) -> str:
    return f"{round_cent(value):,.2f}"


# =========================
# 2026 constants (T4127-01-26e, January edition)
# =========================

# Federal brackets: (threshold, rate, constant)
FEDERAL_BRACKETS_2026 = [
    (D("0"), D("0.14"), D("0")),
    (D("58523"), D("0.205"), D("3804")),
    (D("117045"), D("0.26"), D("10241")),
    (D("181440"), D("0.29"), D("15685")),
    (D("258482"), D("0.33"), D("26024")),
]

# Ontario brackets (2026)
ON_BRACKETS_2026 = [
    (D("0"), D("0.0505"), D("0")),
    (D("53891"), D("0.0915"), D("2210")),
    (D("107785"), D("0.1116"), D("4376")),
    (D("150000"), D("0.1216"), D("5876")),
    (D("220000"), D("0.1316"), D("8076")),
]

# Federal credits
FEDERAL_K1_RATE = D("0.14")
FEDERAL_K2_RATE = D("0.14")
FEDERAL_K4_RATE = D("0.14")
FEDERAL_CEA = D("1501")

# Ontario credits
ON_K1_RATE = D("0.0505")
ON_K2_RATE = D("0.0505")
ON_SURTAX1_THRESHOLD = D("5818")  # Updated 2026
ON_SURTAX1_RATE = D("0.20")
ON_SURTAX2_THRESHOLD = D("7446")  # Updated 2026
ON_SURTAX2_RATE = D("0.36")

# Ontario Health Premium 2026 brackets (threshold, premium, rate, base)
# Format: (threshold, flat_premium_if_in_this_bracket, rate_for_next_bracket, base_for_rate_calculation)
ON_HEALTH_PREMIUM_BRACKETS = [
    (D("0"), D("0"), None, None),  # Below $20K: $0
    (D("20000"), D("0"), D("0.06"), D("0")),  # $20K-$25K: 6% over $20K
    (D("25000"), D("300"), None, None),  # $25K-$36K: $300 flat
    (D("36000"), D("300"), D("0.06"), D("300")),  # $36K-$38.5K: $300 + 6% over $36K
    (D("38500"), D("450"), None, None),  # $38.5K-$48K: $450 flat
    (D("48000"), D("450"), D("0.25"), D("450")),  # $48K-$48.6K: $450 + 25% over $48K
    (D("48600"), D("600"), None, None),  # $48.6K-$72K: $600 flat
    (D("72000"), D("600"), D("0.25"), D("600")),  # $72K-$72.6K: $600 + 25% over $72K
    (D("72600"), D("750"), None, None),  # $72.6K-$200K: $750 flat
    (D("200000"), D("750"), D("0.25"), D("750")),  # $200K-$200.6K: $750 + 25% over $200K
    (D("200600"), D("900"), None, None),  # Above $200.6K: $900 flat
]

# CPP / EI
CPP_BASE_RATE = D("0.0595")
CPP_BASE_RATE_FOR_CREDIT = D("0.0495")
CPP_ADDITIONAL_RATE = D("0.0100")
CPP2_RATE = D("0.04")
CPP_BASIC_EXEMPTION = D("3500")
CPP_YMPE = D("74600")
CPP_MAX_BASE_CONTRIB = D("4230.45")
CPP_MAX_CPP2_CONTRIB = D("416.00")
CPP_MAX_BASE_CREDIT = D("3519.45")

EI_RATE = D("0.0163")
EI_MAX_PREMIUM = D("1123.07")


def calc_ontario_health_premium(annual_income: Decimal) -> Decimal:
    """Calculate Ontario Health Premium using 2026 brackets."""
    premium = D("0")

    for i in range(len(ON_HEALTH_PREMIUM_BRACKETS) - 1):
        threshold, flat_premium, rate, base = ON_HEALTH_PREMIUM_BRACKETS[i]
        next_threshold = ON_HEALTH_PREMIUM_BRACKETS[i + 1][0]

        if annual_income >= threshold:
            if rate is not None:
                # This is a rate-based bracket leading to next flat bracket
                income_in_bracket = min(annual_income, next_threshold) - threshold
                premium = base + (rate * income_in_bracket)
            else:
                # This is a flat premium bracket
                premium = flat_premium
        else:
            break

    # Check if above all brackets
    if annual_income >= ON_HEALTH_PREMIUM_BRACKETS[-1][0]:
        premium = ON_HEALTH_PREMIUM_BRACKETS[-1][1]

    return round_cent(premium)


def calc_k2_components(
    annual_cpp_contrib: Decimal,
    annual_ei_premium: Decimal,
    k2_rate: Decimal,
    pay_months: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    cpp_base = round_cent(annual_cpp_contrib * (CPP_BASE_RATE_FOR_CREDIT / CPP_BASE_RATE))
    cpp_base = min(cpp_base, CPP_MAX_BASE_CREDIT * (pay_months / D("12")))
    ei_base = round_cent(annual_ei_premium)
    ei_base = min(ei_base, EI_MAX_PREMIUM * (pay_months / D("12")))
    k2 = round_cent(k2_rate * (cpp_base + ei_base))
    return k2, cpp_base, ei_base


def calc_t1_federal_raw(
    annual_income: Decimal,
    federal_claim: Decimal,
    annual_cpp_contrib: Decimal,
    annual_ei_premium: Decimal,
    pay_months: Decimal,
) -> tuple[Decimal, dict[str, Decimal]]:
    rate, constant = find_bracket(annual_income, FEDERAL_BRACKETS_2026)

    k1 = round_cent(FEDERAL_K1_RATE * federal_claim)
    k2, cpp_base, ei_base = calc_k2_components(
        annual_cpp_contrib, annual_ei_premium, FEDERAL_K2_RATE, pay_months
    )
    k4 = round_cent(min(FEDERAL_K4_RATE * annual_income, FEDERAL_K4_RATE * FEDERAL_CEA))

    t3_raw = (rate * annual_income) - constant - k1 - k2 - k4
    if t3_raw < 0:
        t3_raw = D("0")

    details = {
        "rate": rate,
        "constant": constant,
        "k1": k1,
        "k2": k2,
        "k2_cpp_base": cpp_base,
        "k2_ei_base": ei_base,
        "k4": k4,
        "t3_raw": t3_raw,
    }
    return t3_raw, details


def calc_t2_ontario_raw(
    annual_income: Decimal,
    provincial_claim: Decimal,
    annual_cpp_contrib: Decimal,
    annual_ei_premium: Decimal,
    pay_months: Decimal,
) -> tuple[Decimal, dict[str, Decimal]]:
    rate, constant = find_bracket(annual_income, ON_BRACKETS_2026)

    k1p = round_cent(ON_K1_RATE * provincial_claim)
    k2p, cpp_base, ei_base = calc_k2_components(
        annual_cpp_contrib, annual_ei_premium, ON_K2_RATE, pay_months
    )

    t4_raw = (rate * annual_income) - constant - k1p - k2p
    if t4_raw < 0:
        t4_raw = D("0")

    # Ontario Surtax (2026 thresholds)
    surtax = D("0")
    if t4_raw > ON_SURTAX2_THRESHOLD:
        surtax = (
            (ON_SURTAX1_RATE * (min(t4_raw, ON_SURTAX2_THRESHOLD) - ON_SURTAX1_THRESHOLD))
            + (ON_SURTAX2_RATE * (t4_raw - ON_SURTAX2_THRESHOLD))
        )
        surtax = clamp_min_zero(surtax)
    elif t4_raw > ON_SURTAX1_THRESHOLD:
        surtax = ON_SURTAX1_RATE * (t4_raw - ON_SURTAX1_THRESHOLD)
        surtax = clamp_min_zero(surtax)
    surtax = round_cent(surtax)

    # Ontario Health Premium (2026 brackets)
    health_premium = calc_ontario_health_premium(annual_income)

    t2_raw = t4_raw + surtax + health_premium

    details = {
        "rate": rate,
        "constant": constant,
        "k1p": k1p,
        "k2p": k2p,
        "k2_cpp_base": cpp_base,
        "k2_ei_base": ei_base,
        "t4_raw": t4_raw,
        "surtax": surtax,
        "health_premium": health_premium,
    }
    return t2_raw, details


def main() -> None:
    # =========================
    # Input (from PDOC test case ON_60K_RETROACTIVE)
    # =========================
    gross_pay = D("2307.69")  # I - Gross remuneration for the pay period
    retroactive = D("500.00")  # Retroactive pay amount
    retro_periods = 2  # Number of periods to spread retroactive pay
    retro_per_period = round_cent(retroactive / D(str(retro_periods)))
    province = "ON"
    federal_claim = D("16452.00")
    provincial_claim = D("12989")
    pay_periods = D("26")  # P - Number of pay periods in the year (bi-weekly)
    pay_months = D("12")  # PM - Number of months (full year)

    # Deductions
    f = D("0")  # RPP/RRSP per period
    f1 = D("0")  # Annual deductions authorized
    f2 = D("0")  # Alimony/maintenance (court-ordered)
    u1 = D("0")  # Union dues
    hd = D("0")  # Northern residents deduction

    # Year-to-date values (assumed zero for first pay period)
    cpp_ytd = D("0")
    cpp2_ytd = D("0")
    pensionable_ytd = D("0")
    ei_ytd = D("0")

    # =========================
    # Step 1: CPP/F5 calculations (retroactive is FULLY pensionable)
    # =========================
    exemption = truncate_cent(CPP_BASIC_EXEMPTION / pay_periods)

    # Pensionable income includes gross pay + FULL retroactive pay
    pensionable_income = gross_pay + retroactive

    # Calculate CPP base contribution
    c_base = CPP_BASE_RATE * (pensionable_income - exemption)
    c_base = clamp_min_zero(c_base)
    c_base = min(c_base, (CPP_MAX_BASE_CONTRIB * (pay_months / D("12"))) - cpp_ytd)
    c_base = round_cent(c_base)

    cpp_regular = CPP_BASE_RATE * (gross_pay - exemption)
    cpp_regular = clamp_min_zero(cpp_regular)
    cpp_regular = round_cent(cpp_regular)
    cpp_bonus = clamp_min_zero(c_base - cpp_regular)

    # Calculate CPP2 (additional CPP on earnings above YMPE)
    w = max(pensionable_ytd, CPP_YMPE * (pay_months / D("12")))
    c2 = (pensionable_ytd + pensionable_income - w) * CPP2_RATE
    c2 = clamp_min_zero(c2)
    c2 = min(c2, (CPP_MAX_CPP2_CONTRIB * (pay_months / D("12"))) - cpp2_ytd)
    c2 = round_cent(c2)

    # F5 = CPP additional + CPP2
    f5 = round_cent(c_base * (CPP_ADDITIONAL_RATE / CPP_BASE_RATE) + c2)

    # Split F5 between periodic (F5A) and non-periodic (F5B) portions.
    # PDOC uses the per-period retro amount for the split, even though CPP is
    # calculated on the full retroactive amount.
    pi = gross_pay + retro_per_period  # pensionable earnings this period (as paid)
    b = retro_per_period  # non-periodic amount paid this period
    if pi > 0:
        f5a = round_cent(f5 * ((pi - b) / pi))
        f5b = round_cent(f5 * (b / pi))
    else:
        f5a = D("0")
        f5b = D("0")

    # =========================
    # Step 2: EI calculation (retroactive is FULLY insurable)
    # =========================
    insurable_income = gross_pay + retroactive

    ei_this_period = round_cent(EI_RATE * insurable_income)
    ei_this_period = min(ei_this_period, (EI_MAX_PREMIUM * (pay_months / D("12"))) - ei_ytd)
    ei_regular = round_cent(EI_RATE * gross_pay)
    ei_bonus = clamp_min_zero(ei_this_period - ei_regular)

    # =========================
    # Step 3: Annual Taxable Income (Factor A)
    # =========================
    # Step 2 (regular): A = [P × (I - F - F2 - F5A - U1)] - HD - F1
    annual_taxable_regular = (pay_periods * (gross_pay - f - f2 - f5a - u1)) - hd - f1
    annual_taxable_regular = clamp_min_zero(annual_taxable_regular)
    annual_taxable_regular = round_cent(annual_taxable_regular)

    # Step 1 (with retro): A = regular A + (B - F5B)
    bonus_taxable = clamp_min_zero(retroactive - f5b)
    annual_taxable_with_bonus = annual_taxable_regular + bonus_taxable
    annual_taxable_with_bonus = round_cent(annual_taxable_with_bonus)

    # =========================
    # Step 4: Annual CPP/EI for K2 calculation
    # =========================
    # For K2, estimate annual CPP/EI on regular pay, then add bonus portion
    annual_cpp_regular = cpp_regular * pay_periods
    annual_ei_regular = ei_regular * pay_periods
    annual_cpp_with_bonus = annual_cpp_regular + cpp_bonus
    annual_ei_with_bonus = annual_ei_regular + ei_bonus

    # =========================
    # Step 5: Federal / Provincial taxes (raw annual)
    # =========================
    federal_raw_with_bonus, federal_details_with_bonus = calc_t1_federal_raw(
        annual_taxable_with_bonus,
        federal_claim,
        annual_cpp_with_bonus,
        annual_ei_with_bonus,
        pay_months,
    )

    federal_raw_regular, federal_details_regular = calc_t1_federal_raw(
        annual_taxable_regular,
        federal_claim,
        annual_cpp_regular,
        annual_ei_regular,
        pay_months,
    )

    ontario_raw_with_bonus, ontario_details_with_bonus = calc_t2_ontario_raw(
        annual_taxable_with_bonus,
        provincial_claim,
        annual_cpp_with_bonus,
        annual_ei_with_bonus,
        pay_months,
    )

    ontario_raw_regular, ontario_details_regular = calc_t2_ontario_raw(
        annual_taxable_regular,
        provincial_claim,
        annual_cpp_regular,
        annual_ei_regular,
        pay_months,
    )

    # =========================
    # Step 6: Pay period tax deductions
    # =========================
    # Regular tax is annual tax divided by pay periods.
    # Retro tax (TB) is the difference between annual tax with/without retro.
    federal_tax = round_cent(federal_raw_regular / pay_periods)
    provincial_tax = round_cent(ontario_raw_regular / pay_periods)
    federal_bonus_tax = round_cent(clamp_min_zero(federal_raw_with_bonus - federal_raw_regular))
    provincial_bonus_tax = round_cent(clamp_min_zero(ontario_raw_with_bonus - ontario_raw_regular))

    # =========================
    # Step 7: Net Pay Calculation
    # =========================
    # Net Pay = (Regular Pay + Retroactive Pay) - Deductions - Tax on Retro
    total_deductions = (
        c_base
        + c2
        + ei_this_period
        + federal_tax
        + provincial_tax
        + federal_bonus_tax
        + provincial_bonus_tax
    )
    net_pay = gross_pay + retroactive - total_deductions

    # =========================
    # Debug output
    # =========================
    print("== Inputs ==")
    print(f"Gross pay (I): {money(gross_pay)}")
    print(f"Retroactive pay: {money(retroactive)}")
    print(f"Retroactive periods: {retro_periods}")
    print(f"Retroactive per period (spread basis): {money(retro_per_period)}")
    print(f"Province: {province}")
    print(f"Federal claim (TC): {money(federal_claim)}")
    print(f"Provincial claim (TCP): {money(provincial_claim)}")
    print(f"Pay periods (P): {pay_periods}")
    print()

    print("== CPP / EI (retroactive is FULLY pensionable/insurable) ==")
    print(f"CPP exemption per period: {money(exemption)}")
    print(f"Pensionable income (I + Retroactive): {money(pensionable_income)}")
    print(f"CPP base (C): {money(c_base)}")
    print(f"CPP2 (C2): {money(c2)}")
    print(f"F5 (CPP additional + CPP2): {money(f5)}")
    print(f"F5A (periodic portion): {money(f5a)}")
    print(f"F5B (non-periodic portion): {money(f5b)}")
    print(f"Insurable income (I + Retroactive): {money(insurable_income)}")
    print(f"EI premium: {money(ei_this_period)}")
    print()

    print("== Annual Taxable Income (A) ==")
    print(f"Regular gross (per period): {money(gross_pay)}")
    print(f"Less F5A: {money(f5a)}")
    print(f"Net per period: {money(gross_pay - f5a)}")
    print(f"A without retro (Step 2): {money(annual_taxable_regular)}")
    print(f"A with retro (Step 1): {money(annual_taxable_with_bonus)}")
    print()

    print("== Federal (raw annual) ==")
    print(f"T1 (regular): {money(federal_raw_regular)}")
    print(f"T1 (with retro): {money(federal_raw_with_bonus)}")
    print(f"  Rate: {federal_details_regular['rate']:.2%}")
    print(f"  Constant: {money(federal_details_regular['constant'])}")
    print(f"  K1 (personal): {money(federal_details_regular['k1'])}")
    print(f"  K2 (CPP/EI regular): {money(federal_details_regular['k2'])}")
    print(f"  K2 (CPP/EI with retro): {money(federal_details_with_bonus['k2'])}")
    print(f"  K4 (employment): {money(federal_details_regular['k4'])}")
    print()

    print("== Ontario (raw annual) ==")
    print(f"T2 (regular): {money(ontario_raw_regular)}")
    print(f"T2 (with retro): {money(ontario_raw_with_bonus)}")
    print(f"  Rate: {ontario_details_regular['rate']:.2%}")
    print(f"  Constant: {money(ontario_details_regular['constant'])}")
    print(f"  K1P (personal): {money(ontario_details_regular['k1p'])}")
    print(f"  K2P (CPP/EI regular): {money(ontario_details_regular['k2p'])}")
    print(f"  K2P (CPP/EI with retro): {money(ontario_details_with_bonus['k2p'])}")
    print(f"  T4 (basic tax): {money(ontario_details_regular['t4_raw'])}")
    print(f"  Surtax: {money(ontario_details_regular['surtax'])}")
    print(f"  Health premium: {money(ontario_details_regular['health_premium'])}")
    print()

    print("== Pay Period Results ==")
    print(f"CPP base: {money(c_base)}")
    print(f"EI: {money(ei_this_period)}")
    print(f"Federal Tax (regular): {money(federal_tax)}")
    print(f"Provincial Tax (regular): {money(provincial_tax)}")
    print(f"Federal Tax (retro): {money(federal_bonus_tax)}")
    print(f"Provincial Tax (retro): {money(provincial_bonus_tax)}")
    print(f"Total deductions: {money(total_deductions)}")
    print()

    print("== Net Pay Calculation ==")
    print(f"Gross pay: {money(gross_pay)}")
    print(f"+ Retroactive pay: {money(retroactive)}")
    print(f"- Total deductions: {money(total_deductions)}")
    print(f"= Net Pay: {money(net_pay)}")
    print()

    print("== PDOC Expected Values (from fixture) ==")
    print("CPP: 159.05")
    print("EI: 45.77")
    print("Federal Tax: 204.83")
    print("Provincial Tax: 114.46")
    print("Federal Tax (retro): 97.36")
    print("Provincial Tax (retro): 43.85")
    print("Net Pay: 2142.37")
    print()

    # Comparison
    print("== Variance Analysis (vs PDOC expected) ==")
    cpp_variance = abs(c_base - D("159.05"))
    ei_variance = abs(ei_this_period - D("45.77"))
    federal_variance = abs(federal_tax - D("204.83"))
    provincial_variance = abs(provincial_tax - D("114.46"))
    federal_retro_variance = abs(federal_bonus_tax - D("97.36"))
    provincial_retro_variance = abs(provincial_bonus_tax - D("43.85"))
    net_variance = abs(net_pay - D("2142.37"))

    print(f"CPP variance: {money(cpp_variance)} {'✓ PASS' if cpp_variance <= D('0.05') else '✗ FAIL'}")
    print(f"EI variance: {money(ei_variance)} {'✓ PASS' if ei_variance <= D('0.05') else '✗ FAIL'}")
    print(f"Federal Tax variance: {money(federal_variance)} {'✓ PASS' if federal_variance <= D('0.05') else '✗ FAIL'}")
    print(f"Provincial Tax variance: {money(provincial_variance)} {'✓ PASS' if provincial_variance <= D('0.05') else '✗ FAIL'}")
    print(f"Federal Retro Tax variance: {money(federal_retro_variance)} {'✓ PASS' if federal_retro_variance <= D('0.05') else '✗ FAIL'}")
    print(f"Provincial Retro Tax variance: {money(provincial_retro_variance)} {'✓ PASS' if provincial_retro_variance <= D('0.05') else '✗ FAIL'}")
    print(f"Net Pay variance: {money(net_variance)} {'✓ PASS' if net_variance <= D('0.05') else '✗ FAIL'}")
    print()

    print("== PayrollEngine Results (for comparison) ==")
    print("CPP base: 159.05")
    print("EI: 45.77")
    print("Federal Tax: 201.79")
    print("Provincial Tax: 112.69")
    print("Net Pay: 2038.39")


if __name__ == "__main__":
    main()
