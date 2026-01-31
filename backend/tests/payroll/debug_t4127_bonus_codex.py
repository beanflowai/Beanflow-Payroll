#!/usr/bin/env python3
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

# British Columbia brackets (Table 8.1 uses whole-dollar constants)
BC_BRACKETS_2026 = [
    (D("0"), D("0.0506"), D("0")),
    (D("50363"), D("0.077"), D("1330")),
    (D("100728"), D("0.105"), D("4150")),
    (D("115648"), D("0.1229"), D("6220")),
    (D("140430"), D("0.147"), D("9604")),
    (D("190405"), D("0.168"), D("13603")),
    (D("265545"), D("0.205"), D("23428")),
]

# Federal credits
FEDERAL_K1_RATE = D("0.14")
FEDERAL_K2_RATE = D("0.14")
FEDERAL_K4_RATE = D("0.14")
FEDERAL_CEA = D("1501")

# BC credits
BC_K1_RATE = D("0.0506")
BC_K2_RATE = D("0.0506")
BC_TAX_REDUCTION = {
    "base_reduction": D("575.00"),
    "reduction_rate": D("0.0356"),
    "phase_out_start": D("25570.00"),
    "phase_out_end": D("41722.00"),
}

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


def calc_t2_bc_raw(
    annual_income: Decimal,
    provincial_claim: Decimal,
    annual_cpp_contrib: Decimal,
    annual_ei_premium: Decimal,
    pay_months: Decimal,
) -> tuple[Decimal, dict[str, Decimal]]:
    rate, constant = find_bracket(annual_income, BC_BRACKETS_2026)

    k1p = round_cent(BC_K1_RATE * provincial_claim)
    k2p, cpp_base, ei_base = calc_k2_components(
        annual_cpp_contrib, annual_ei_premium, BC_K2_RATE, pay_months
    )

    t4_raw = (rate * annual_income) - constant - k1p - k2p
    if t4_raw < 0:
        t4_raw = D("0")

    tax_reduction = D("0")
    if annual_income <= BC_TAX_REDUCTION["phase_out_start"]:
        tax_reduction = min(t4_raw, BC_TAX_REDUCTION["base_reduction"])
    elif annual_income <= BC_TAX_REDUCTION["phase_out_end"]:
        reduced = BC_TAX_REDUCTION["base_reduction"] - (
            (annual_income - BC_TAX_REDUCTION["phase_out_start"]) * BC_TAX_REDUCTION["reduction_rate"]
        )
        tax_reduction = min(t4_raw, round_cent(reduced))

    t2_raw = t4_raw - tax_reduction
    if t2_raw < 0:
        t2_raw = D("0")

    details = {
        "rate": rate,
        "constant": constant,
        "k1p": k1p,
        "k2p": k2p,
        "k2_cpp_base": cpp_base,
        "k2_ei_base": ei_base,
        "tax_reduction": tax_reduction,
        "t4_raw": t4_raw,
    }
    return t2_raw, details


def main() -> None:
    # =========================
    # Input (matching the PDOC test case)
    # =========================
    regular_gross = D("5000")  # I
    bonus = D("1000")  # B
    province = "BC"
    federal_claim = D("16452")
    provincial_claim = D("13216")
    pay_periods = D("12")  # P
    pay_months = D("12")  # PM

    # YTD bonus and deductions
    bonus_ytd = D("0")  # B1
    f3 = D("0")  # RPP/RRSP on current bonus
    f4 = D("0")  # RPP/RRSP on YTD bonuses
    f5b_ytd = D("0")  # CPP additional on YTD bonuses

    # Regular deductions (not used in this scenario)
    f = D("0")  # RPP/RRSP on regular pay
    f1 = D("0")  # annual deductions authorized by CRA
    f2 = D("0")  # court-ordered alimony
    u1 = D("0")  # union dues
    hd = D("0")  # northern residents deduction

    # CPP/EI year-to-date (assumed zero)
    cpp_ytd = D("0")  # D
    cpp2_ytd = D("0")  # D2
    pensionable_ytd = D("0")  # PIYTD

    # =========================
    # CPP/F5 calculations (pay period with bonus)
    # =========================
    exemption = truncate_cent(CPP_BASIC_EXEMPTION / pay_periods)
    pensionable_income = regular_gross + bonus

    c_base = CPP_BASE_RATE * (pensionable_income - exemption)
    c_base = clamp_min_zero(c_base)
    c_base = min(c_base, (CPP_MAX_BASE_CONTRIB * (pay_months / D("12"))) - cpp_ytd)
    c_base = round_cent(c_base)

    w = max(pensionable_ytd, CPP_YMPE * (pay_months / D("12")))
    c2 = (pensionable_ytd + pensionable_income - w) * CPP2_RATE
    c2 = clamp_min_zero(c2)
    c2 = min(c2, (CPP_MAX_CPP2_CONTRIB * (pay_months / D("12"))) - cpp2_ytd)
    c2 = round_cent(c2)

    f5 = round_cent(c_base * (CPP_ADDITIONAL_RATE / CPP_BASE_RATE) + c2)
    if pensionable_income != 0:
        f5a = round_cent(f5 * ((pensionable_income - bonus) / pensionable_income))
        f5b = round_cent(f5 * (bonus / pensionable_income))
    else:
        f5a = D("0")
        f5b = D("0")

    # =========================
    # Annual taxable income (Step 1/2)
    # =========================
    regular_annual = (pay_periods * (regular_gross - f - f2 - f5a - u1)) - hd - f1
    regular_annual = clamp_min_zero(regular_annual)

    bonus_net = clamp_min_zero(bonus - f3 - f5b)
    bonus_ytd_net = clamp_min_zero(bonus_ytd - f4 - f5b_ytd)

    annual_with_bonus = round_cent(regular_annual + bonus_net + bonus_ytd_net)
    annual_without_bonus = round_cent(regular_annual + bonus_ytd_net)

    # =========================
    # CPP/EI amounts for K2 (regular vs bonus)
    # =========================
    cpp_regular = round_cent(CPP_BASE_RATE * (regular_gross - exemption))
    cpp_regular = clamp_min_zero(cpp_regular)
    cpp_bonus = round_cent(CPP_BASE_RATE * bonus)
    cpp_bonus_ytd = round_cent(CPP_BASE_RATE * bonus_ytd)

    ei_regular = round_cent(EI_RATE * regular_gross)
    ei_bonus = round_cent(EI_RATE * bonus)
    ei_bonus_ytd = round_cent(EI_RATE * bonus_ytd)

    annual_cpp_no_bonus = round_cent((pay_periods * cpp_regular) + cpp_bonus_ytd)
    annual_cpp_with_bonus = round_cent((pay_periods * cpp_regular) + cpp_bonus + cpp_bonus_ytd)
    annual_ei_no_bonus = round_cent((pay_periods * ei_regular) + ei_bonus_ytd)
    annual_ei_with_bonus = round_cent((pay_periods * ei_regular) + ei_bonus + ei_bonus_ytd)

    # =========================
    # Federal / Provincial taxes (raw annual)
    # =========================
    federal_with_bonus_raw, federal_with_details = calc_t1_federal_raw(
        annual_with_bonus,
        federal_claim,
        annual_cpp_with_bonus,
        annual_ei_with_bonus,
        pay_months,
    )
    federal_without_bonus_raw, federal_without_details = calc_t1_federal_raw(
        annual_without_bonus,
        federal_claim,
        annual_cpp_no_bonus,
        annual_ei_no_bonus,
        pay_months,
    )

    bc_with_bonus_raw, bc_with_details = calc_t2_bc_raw(
        annual_with_bonus,
        provincial_claim,
        annual_cpp_with_bonus,
        annual_ei_with_bonus,
        pay_months,
    )
    bc_without_bonus_raw, bc_without_details = calc_t2_bc_raw(
        annual_without_bonus,
        provincial_claim,
        annual_cpp_no_bonus,
        annual_ei_no_bonus,
        pay_months,
    )

    # =========================
    # Final pay-period outputs
    # =========================
    federal_income = round_cent(federal_without_bonus_raw / pay_periods)
    federal_bonus = round_cent(federal_with_bonus_raw - federal_without_bonus_raw)
    provincial_income = round_cent(bc_without_bonus_raw / pay_periods)
    provincial_bonus = round_cent(bc_with_bonus_raw - bc_without_bonus_raw)

    total_federal = round_cent(federal_income + federal_bonus)
    total_provincial = round_cent(provincial_income + provincial_bonus)

    # =========================
    # Debug output
    # =========================
    print("== Inputs ==")
    print(f"Regular gross (I): {money(regular_gross)}")
    print(f"Bonus (B): {money(bonus)}")
    print(f"Province: {province}")
    print(f"Federal claim (TC): {money(federal_claim)}")
    print(f"Provincial claim (TCP): {money(provincial_claim)}")
    print(f"Pay periods (P): {pay_periods}")
    print(f"Pay months (PM): {pay_months}")
    print()

    print("== CPP / EI (pay period with bonus) ==")
    print(f"CPP exemption per period: {money(exemption)}")
    print(f"CPP base (C): {money(c_base)}")
    print(f"CPP2 (C2): {money(c2)}")
    print(f"F5 total: {money(f5)}")
    print(f"F5A (regular): {money(f5a)}")
    print(f"F5B (bonus): {money(f5b)}")
    print(f"CPP regular (for K2): {money(cpp_regular)}")
    print(f"CPP bonus (for K2): {money(cpp_bonus)}")
    print(f"EI regular (for K2): {money(ei_regular)}")
    print(f"EI bonus (for K2): {money(ei_bonus)}")
    print()

    print("== Annual taxable income (A) ==")
    print(f"A with bonus: {money(annual_with_bonus)}")
    print(f"A without bonus: {money(annual_without_bonus)}")
    print()

    print("== Federal (raw annual) ==")
    print(f"T1 with bonus (raw): {money(federal_with_bonus_raw)}")
    print(f"T1 without bonus (raw): {money(federal_without_bonus_raw)}")
    print(f"K1: {money(federal_with_details['k1'])}")
    print(f"K2: {money(federal_with_details['k2'])}")
    print(f"  CPP base: {money(federal_with_details['k2_cpp_base'])}")
    print(f"  EI base: {money(federal_with_details['k2_ei_base'])}")
    print(f"K4: {money(federal_with_details['k4'])}")
    print()

    print("== British Columbia (raw annual) ==")
    print(f"T2 with bonus (raw): {money(bc_with_bonus_raw)}")
    print(f"T2 without bonus (raw): {money(bc_without_bonus_raw)}")
    print(f"K1P: {money(bc_with_details['k1p'])}")
    print(f"K2P: {money(bc_with_details['k2p'])}")
    print(f"  CPP base: {money(bc_with_details['k2_cpp_base'])}")
    print(f"  EI base: {money(bc_with_details['k2_ei_base'])}")
    if bc_with_details["tax_reduction"] > 0:
        print(f"S (tax reduction): {money(bc_with_details['tax_reduction'])}")
    print()

    print("== Pay Period Results (PDOC comparison) ==")
    print(f"Federal Tax on Income: {money(federal_income)}")
    print(f"Federal Tax on Bonus: {money(federal_bonus)}")
    print(f"Provincial Tax on Income: {money(provincial_income)}")
    print(f"Provincial Tax on Bonus: {money(provincial_bonus)}")
    print(f"Total Federal: {money(total_federal)}")
    print(f"Total Provincial: {money(total_provincial)}")


if __name__ == "__main__":
    main()
