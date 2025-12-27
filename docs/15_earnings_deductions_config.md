# Earnings, Benefits, and Deductions Configuration

**Last Updated**: 2025-12-26
**Related**: [Database Schema](./13_database_schema.md)

---

## Overview

This document describes the structured configuration for Earnings, Taxable Benefits, and Deductions in Pay Groups. The configuration is designed to be CRA-compliant while remaining flexible for various Canadian payroll scenarios.

---

## Database Columns

The `pay_groups` table includes three JSONB configuration columns:

| Column | Purpose |
|--------|---------|
| `earnings_config` | Bonus, commission, allowances, expense reimbursement, custom earnings |
| `taxable_benefits_config` | Automobile, housing, travel assistance, board/lodging, life insurance |
| `deductions_config` | RRSP, union dues, garnishments, charitable donations, custom deductions |

---

## 1. Earnings Configuration

### EarningsConfig Structure

```typescript
interface EarningsConfig {
  enabled: boolean;
  bonus: BonusConfig;
  commission: CommissionConfig;
  expenseReimbursement: ExpenseReimbursementConfig;
  allowances: AllowanceConfig[];
  customEarnings: CustomEarning[];
}
```

### 1.1 Bonus Configuration

CRA distinguishes between discretionary and non-discretionary bonuses:

```typescript
interface BonusConfig {
  enabled: boolean;
  discretionaryEnabled: boolean;      // NOT included in overtime/vacation base
  nonDiscretionaryEnabled: boolean;   // Included in overtime/vacation base (CRA rule)
  defaultTaxable: boolean;
}
```

| Bonus Type | Overtime Base | Vacation Pay Base | Example |
|------------|---------------|-------------------|---------|
| Discretionary | Excluded | Excluded | Gift, spot bonus |
| Non-Discretionary | Included | Included | Performance bonus, sales target bonus |

### 1.2 Commission Configuration

```typescript
type CommissionCalculationType = 'percentage_gross' | 'sales_percentage' | 'fixed';

interface CommissionConfig {
  enabled: boolean;
  calculationType: CommissionCalculationType;
  defaultAmount: number;
  requiresSalesInput: boolean;        // For sales_percentage type
  includeInOvertimeBase: boolean;     // CRA: commission may be included
}
```

### 1.3 Allowances

CRA T4130 specifies taxability rules for various allowances:

```typescript
type AllowanceType =
  | 'meal'           // Non-taxable if <= $23 + overtime + occasional
  | 'travel'         // Non-taxable if reasonable (70c/km)
  | 'housing'        // Always taxable
  | 'moving'         // Non-taxable if <= $650
  | 'northern_zone'  // $11/day northern, $5.50/day intermediate
  | 'tool'           // Tradesperson tools
  | 'uniform'        // Non-taxable if employer-required
  | 'cell_phone'     // Non-taxable if business use
  | 'other';

interface AllowanceConfig {
  id: string;
  type: AllowanceType;
  name: string;
  enabled: boolean;
  calculationType: 'fixed' | 'per_diem' | 'per_km';
  defaultAmount: number;
  ratePerKm?: number;
  requiresOvertime?: boolean;  // For meal allowance
  taxableOverride?: boolean;
  description?: string;
}
```

### 1.4 Custom Earnings

```typescript
interface CustomEarning {
  id: string;
  name: string;
  calculationType: 'fixed' | 'percentage';
  amount: number;
  taxable: boolean;
  includeInVacationPay: boolean;
  includeInOvertimeBase: boolean;
  isDefaultEnabled: boolean;
  description?: string;
}
```

---

## 2. Taxable Benefits Configuration

CRA T4130 governs taxable benefit calculations.

### TaxableBenefitsConfig Structure

```typescript
interface TaxableBenefitsConfig {
  enabled: boolean;
  automobile: AutomobileBenefitConfig;
  housing: HousingBenefitConfig;
  travelAssistance: TravelAssistanceBenefitConfig;
  boardLodging: BoardLodgingBenefitConfig;
  groupLifeInsurance: GroupLifeInsuranceBenefitConfig;
  customBenefits: CustomTaxableBenefit[];
}
```

### 2.1 Automobile Benefit (CRA Standby Charge)

```typescript
interface AutomobileBenefitConfig {
  enabled: boolean;
  // Standby Charge calculation
  vehicleCost: number;
  isLeased: boolean;
  monthlyLeaseCost?: number;
  daysAvailablePerMonth: number;
  // Operating Expense Benefit
  personalKilometers: number;
  totalKilometers?: number;
  useOperatingExpenseBenefit: boolean;
  operatingExpenseRate: number;  // 2025: $0.34/km
  // GST/HST
  includesGstHst: boolean;
  gstHstRate: number;  // e.g., 0.13 for Ontario
  // Overrides
  calculatedMonthlyBenefit?: number;
  manualMonthlyOverride?: number;
}
```

**Standby Charge Formula**:
- Owned vehicle: 2% × cost × days available / 30
- Leased vehicle: 2/3 × monthly lease cost × days available / 30

### 2.2 Housing Benefit

```typescript
interface HousingBenefitConfig {
  enabled: boolean;
  monthlyValue: number;
  includesUtilities: boolean;
  utilitiesValue?: number;
}
```

### 2.3 Travel Assistance (Northern Zone)

```typescript
interface TravelAssistanceBenefitConfig {
  enabled: boolean;
  isPrescribedZone: boolean;      // Northern zone
  isIntermediateZone: boolean;    // Half rate
  annualValue: number;
  tripsPerYear: number;
}
```

### 2.4 Board and Lodging

```typescript
interface BoardLodgingBenefitConfig {
  enabled: boolean;
  valueType: 'daily' | 'monthly';
  value: number;
  isSubsidized: boolean;
  employeeContribution?: number;
}
```

### 2.5 Group Life Insurance

```typescript
interface GroupLifeInsuranceBenefitConfig {
  enabled: boolean;
  coverageAmount: number;
  employerPremium: number;
  employeePremium: number;
  useCraRates: boolean;
}
```

### 2.6 Custom Taxable Benefits

```typescript
interface CustomTaxableBenefit {
  id: string;
  name: string;
  calculationType: 'fixed_monthly' | 'fixed_per_period' | 'annual';
  amount: number;
  subjectToCppEi: boolean;
  isDefaultEnabled: boolean;
  description?: string;
}
```

---

## 3. Deductions Configuration

### DeductionsConfig Structure

```typescript
interface DeductionsConfig {
  enabled: boolean;
  rrsp: RrspDeductionConfig;
  unionDues: UnionDuesConfig;
  garnishments: GarnishmentDeductionConfig;
  charitableDonations: CharitableDonationConfig;
  customDeductions: CustomDeduction[];
}
```

### 3.1 RRSP Deductions

```typescript
interface RrspDeductionConfig {
  enabled: boolean;
  calculationType: 'fixed' | 'percentage';
  amount: number;
  employerMatchEnabled: boolean;
  employerMatchPercentage?: number;
  employerMatchMaxAmount?: number;
  respectAnnualLimit: boolean;
  isDefaultEnabled: boolean;
}
```

### 3.2 Union Dues

```typescript
interface UnionDuesConfig {
  enabled: boolean;
  calculationType: 'fixed' | 'percentage';
  amount: number;
  unionName?: string;
  isDefaultEnabled: boolean;
}
```

### 3.3 Garnishments

```typescript
interface GarnishmentDeductionConfig {
  enabled: boolean;
  allowGarnishments: boolean;
  // Note: Individual garnishments stored per-employee
}
```

### 3.4 Charitable Donations

```typescript
interface ApprovedCharity {
  id: string;
  name: string;
  registrationNumber: string;
  defaultAmount?: number;
}

interface CharitableDonationConfig {
  enabled: boolean;
  approvedCharities: ApprovedCharity[];
  isDefaultEnabled: boolean;
}
```

### 3.5 Custom Deductions

Replaces the former `customDeductions` array at the PayGroup level:

```typescript
type DeductionCategory =
  | 'rrsp'              // Pre-tax, annual limit
  | 'union_dues'        // Pre-tax, 100% tax deductible
  | 'professional_dues' // Pre-tax
  | 'parking'           // Post-tax typically
  | 'charitable'        // Post-tax, tax receipt
  | 'garnishment'       // Post-tax, court-ordered
  | 'loan_repayment'    // Post-tax
  | 'equipment'         // Post-tax
  | 'other';

interface CustomDeduction {
  id: string;
  name: string;
  category: DeductionCategory;
  taxTreatment: 'pre_tax' | 'post_tax';
  calculationType: 'fixed' | 'percentage';
  amount: number;
  isEmployerContribution: boolean;
  employerAmount?: number;
  annualLimit?: number;
  perPayPeriodLimit?: number;
  isDefaultEnabled: boolean;
  description?: string;
}
```

---

## 4. Default Values

### 4.1 Default Earnings Config

```typescript
const DEFAULT_EARNINGS_CONFIG: EarningsConfig = {
  enabled: false,
  bonus: {
    enabled: false,
    discretionaryEnabled: false,
    nonDiscretionaryEnabled: false,
    defaultTaxable: true
  },
  commission: {
    enabled: false,
    calculationType: 'fixed',
    defaultAmount: 0,
    requiresSalesInput: false,
    includeInOvertimeBase: false
  },
  expenseReimbursement: {
    enabled: false,
    requireReceipts: true,
    categories: []
  },
  allowances: [],
  customEarnings: []
};
```

### 4.2 Default Taxable Benefits Config

```typescript
const DEFAULT_TAXABLE_BENEFITS_CONFIG: TaxableBenefitsConfig = {
  enabled: false,
  automobile: {
    enabled: false,
    vehicleCost: 0,
    isLeased: false,
    daysAvailablePerMonth: 30,
    personalKilometers: 0,
    useOperatingExpenseBenefit: false,
    operatingExpenseRate: 0.34,  // 2025 CRA rate
    includesGstHst: true,
    gstHstRate: 0.13
  },
  housing: { enabled: false, monthlyValue: 0, includesUtilities: false },
  travelAssistance: {
    enabled: false,
    isPrescribedZone: false,
    isIntermediateZone: false,
    annualValue: 0,
    tripsPerYear: 2
  },
  boardLodging: { enabled: false, valueType: 'daily', value: 0, isSubsidized: false },
  groupLifeInsurance: {
    enabled: false,
    coverageAmount: 0,
    employerPremium: 0,
    employeePremium: 0,
    useCraRates: true
  },
  customBenefits: []
};
```

### 4.3 Default Deductions Config

```typescript
const DEFAULT_DEDUCTIONS_CONFIG: DeductionsConfig = {
  enabled: true,
  rrsp: {
    enabled: false,
    calculationType: 'fixed',
    amount: 0,
    employerMatchEnabled: false,
    respectAnnualLimit: true,
    isDefaultEnabled: false
  },
  unionDues: {
    enabled: false,
    calculationType: 'fixed',
    amount: 0,
    isDefaultEnabled: false
  },
  garnishments: { enabled: true, allowGarnishments: true },
  charitableDonations: {
    enabled: false,
    approvedCharities: [],
    isDefaultEnabled: false
  },
  customDeductions: []
};
```

---

## 5. CRA Compliance Notes

### 5.1 Discretionary vs Non-Discretionary Bonuses

Per CRA guidelines:
- **Discretionary**: Given at employer's sole discretion, not based on pre-set criteria
- **Non-Discretionary**: Based on production targets, sales goals, or other measurable criteria

Non-discretionary bonuses must be included in overtime and vacation pay calculations.

### 5.2 Automobile Standby Charge

CRA T4130 requires calculating:
1. **Standby Charge**: 2% of vehicle cost per month (or 2/3 of lease cost)
2. **Operating Expense Benefit**: $0.34/km for personal use (2025 rate)

Reduction available if personal use is less than 50% of total kilometers.

### 5.3 RRSP Contribution Limits

2025 RRSP contribution limit: 18% of previous year's earned income, up to $32,490 maximum.
The system should track YTD contributions to avoid over-contribution.

### 5.4 Pre-Tax vs Post-Tax Deductions

| Category | Tax Treatment | CPP/EI |
|----------|---------------|--------|
| RRSP | Pre-tax | Reduces pensionable earnings |
| Union Dues | Pre-tax | Does not reduce CPP/EI |
| Parking | Post-tax | No effect |
| Garnishment | Post-tax | No effect |

---

## 6. Implementation Phases

### Phase 1 (MVP)
- `deductionsConfig.customDeductions` - migrated from old `customDeductions`
- `deductionsConfig.rrsp` (basic)
- `earningsConfig.bonus` (basic discretionary/non-discretionary flag)
- `earningsConfig.customEarnings`

### Phase 2
- `earningsConfig.commission`
- `earningsConfig.allowances` (meal, travel)
- `deductionsConfig.unionDues`
- `taxableBenefitsConfig.automobile` (simplified)

### Phase 3+
- Full automobile benefit calculation (CRA T4130)
- Northern zone allowances
- Housing benefits
- Garnishment integration
- RRSP annual limit tracking

---

## 7. Group Benefits Configuration (Added 2025-12-26)

### Overview

Group benefits are employer-sponsored benefit plans that may include employee payroll deductions. The `group_benefits` JSONB column in the `pay_groups` table stores these configurations.

### GroupBenefits Structure

```typescript
interface GroupBenefits {
  enabled: boolean;
  health?: BenefitPlan;
  dental?: BenefitPlan;
  vision?: BenefitPlan;
  lifeInsurance?: LifeInsurancePlan;
  disability?: BenefitPlan;
}

interface BenefitPlan {
  enabled: boolean;
  employeeDeduction: number;  // Per-period employee deduction
}

interface LifeInsurancePlan {
  enabled: boolean;
  employeeDeduction: number;      // Per-period employee deduction
  employerContribution: number;   // Per-period employer contribution (taxable benefit)
}
```

### CRA Tax Treatment

| Benefit Type | Employee Deduction | Employer Contribution |
|--------------|-------------------|----------------------|
| Health | Post-tax deduction | Non-taxable |
| Dental | Post-tax deduction | Non-taxable |
| Vision | Post-tax deduction | Non-taxable |
| Life Insurance | Post-tax deduction | **Taxable benefit** (pensionable, NOT insurable) |
| Disability | Post-tax deduction | Non-taxable |

### Payroll Calculation Integration

**File: `backend/app/services/payroll_run_service.py`**

```python
# Calculate benefits deduction from pay group
group_benefits = pay_group.get("group_benefits") or {}
benefits_deduction = Decimal("0")

if group_benefits.get("enabled"):
    # Health
    health = group_benefits.get("health") or {}
    if health.get("enabled"):
        benefits_deduction += Decimal(str(health.get("employeeDeduction", 0)))

    # Dental
    dental = group_benefits.get("dental") or {}
    if dental.get("enabled"):
        benefits_deduction += Decimal(str(dental.get("employeeDeduction", 0)))

    # Life Insurance
    life = group_benefits.get("lifeInsurance") or {}
    if life.get("enabled"):
        benefits_deduction += Decimal(str(life.get("employeeDeduction", 0)))

    # Vision
    vision = group_benefits.get("vision") or {}
    if vision.get("enabled"):
        benefits_deduction += Decimal(str(vision.get("employeeDeduction", 0)))

    # Disability
    disability = group_benefits.get("disability") or {}
    if disability.get("enabled"):
        benefits_deduction += Decimal(str(disability.get("employeeDeduction", 0)))

# Add benefits to other_deductions
total_other_deductions = result.other_deductions + benefits_deduction
```

### Life Insurance Taxable Benefit

The employer's life insurance contribution is a taxable benefit and is included in:
- **Pensionable earnings** (for CPP calculation)
- **Taxable income** (for income tax calculation)
- But NOT in **insurable earnings** (EI is not applied)

```python
# Extract taxable benefits (life insurance employer contribution)
taxable_benefits_pensionable = Decimal("0")
if group_benefits.get("enabled"):
    life = group_benefits.get("lifeInsurance") or {}
    if life.get("enabled"):
        employer_life = Decimal(str(life.get("employerContribution", 0)))
        if employer_life > 0:
            taxable_benefits_pensionable += employer_life
```

### UI Display

Benefits deductions are displayed in the payroll UI:
- **DraftPayGroupSection.svelte**: Shows individual benefit deductions (Health, Dental, Vision, Life Insurance, Disability)
- **PayrollRecordExpandedRow.svelte**: Shows total benefits with 🏥 icon and orange styling

### Default Configuration

```typescript
const DEFAULT_GROUP_BENEFITS: GroupBenefits = {
  enabled: false
};
```

---

## Related Documents

- [Database Schema](./13_database_schema.md) - Pay Groups table definition
- [Phase 2: Calculations](./02_phase2_calculations.md) - Tax calculation logic
- [Tax Rates 2025](../.claude/skills/tax-rates-2025/SKILL.md) - Current tax rates
