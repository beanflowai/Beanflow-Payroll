/**
 * Mock Pay Group Data for UI Development
 *
 * These mock pay groups demonstrate different policy configurations
 * for testing the Pay Group detail page UI.
 */

import type { PayGroup } from '$lib/types/pay-group';

/**
 * Mock Pay Groups with various policy configurations
 */
export const MOCK_PAY_GROUPS: PayGroup[] = [
	{
		id: 'pg-1',
		companyId: 'company-1',
		name: 'Bi-weekly Full-time',
		description: 'Standard bi-weekly payroll for full-time office employees',
		payFrequency: 'bi_weekly',
		employmentType: 'full_time',
		nextPayDate: '2025-12-26',
		periodStartDay: 'monday',
		leaveEnabled: true,

		// Statutory: Standard (no exemptions)
		statutoryDefaults: {
			cppExemptByDefault: false,
			cpp2ExemptByDefault: false,
			eiExemptByDefault: false
		},

		// Overtime: Bank time enabled with Ontario rules
		overtimePolicy: {
			bankTimeEnabled: true,
			bankTimeRate: 1.5,
			bankTimeExpiryMonths: 3,
			requireWrittenAgreement: true
		},

		// WCB: Enabled for office workers
		wcbConfig: {
			enabled: true,
			industryClassCode: '72300',
			industryName: 'Office Administrative Services',
			assessmentRate: 0.25,
			maxAssessableEarnings: 112500
		},

		// Benefits: Full package
		groupBenefits: {
			enabled: true,
			health: {
				enabled: true,
				employeeDeduction: 50,
				employerContribution: 150,
				isTaxable: false
			},
			dental: {
				enabled: true,
				employeeDeduction: 25,
				employerContribution: 75,
				isTaxable: false
			},
			vision: {
				enabled: true,
				employeeDeduction: 10,
				employerContribution: 30,
				isTaxable: false
			},
			lifeInsurance: {
				enabled: true,
				employeeDeduction: 15,
				employerContribution: 35,
				isTaxable: true, // Employer portion is taxable benefit
				coverageAmount: 100000,
				coverageMultiplier: 2
			},
			disability: {
				enabled: false,
				employeeDeduction: 0,
				employerContribution: 0,
				isTaxable: false
			}
		},

		// Custom deductions
		customDeductions: [
			{
				id: 'cd-1',
				name: 'Parking',
				type: 'post_tax',
				calculationType: 'fixed',
				amount: 50,
				isEmployerContribution: false,
				isDefaultEnabled: true,
				description: 'Monthly parking deduction'
			},
			{
				id: 'cd-2',
				name: 'RRSP',
				type: 'pre_tax',
				calculationType: 'percentage',
				amount: 5,
				isEmployerContribution: true,
				employerAmount: 3,
				isDefaultEnabled: false,
				description: 'RRSP contribution with 3% employer match'
			},
			{
				id: 'cd-3',
				name: 'Charity Donation',
				type: 'post_tax',
				calculationType: 'fixed',
				amount: 25,
				isEmployerContribution: false,
				isDefaultEnabled: false,
				description: 'United Way donation'
			}
		],

		createdAt: '2025-01-15T10:00:00Z',
		updatedAt: '2025-12-01T14:30:00Z'
	},
	{
		id: 'pg-2',
		companyId: 'company-1',
		name: 'Monthly Executives',
		description: 'Monthly payroll for executive team members',
		payFrequency: 'monthly',
		employmentType: 'full_time',
		nextPayDate: '2025-12-31',
		periodStartDay: '1st_of_month',
		leaveEnabled: true,

		// Statutory: EI exempt (executives often are shareholders)
		statutoryDefaults: {
			cppExemptByDefault: false,
			cpp2ExemptByDefault: false,
			eiExemptByDefault: true
		},

		// Overtime: No bank time (executives typically don't track OT)
		overtimePolicy: {
			bankTimeEnabled: false,
			bankTimeRate: 1.5,
			bankTimeExpiryMonths: 3,
			requireWrittenAgreement: false
		},

		// WCB: Enabled
		wcbConfig: {
			enabled: true,
			industryClassCode: '72300',
			industryName: 'Office Administrative Services',
			assessmentRate: 0.25,
			maxAssessableEarnings: 112500
		},

		// Benefits: Premium package
		groupBenefits: {
			enabled: true,
			health: {
				enabled: true,
				employeeDeduction: 0, // Fully employer-paid
				employerContribution: 300,
				isTaxable: false
			},
			dental: {
				enabled: true,
				employeeDeduction: 0,
				employerContribution: 150,
				isTaxable: false
			},
			vision: {
				enabled: true,
				employeeDeduction: 0,
				employerContribution: 75,
				isTaxable: false
			},
			lifeInsurance: {
				enabled: true,
				employeeDeduction: 0,
				employerContribution: 100,
				isTaxable: true,
				coverageAmount: 500000,
				coverageMultiplier: 3
			},
			disability: {
				enabled: true,
				employeeDeduction: 0,
				employerContribution: 80,
				isTaxable: false
			}
		},

		// Custom deductions
		customDeductions: [
			{
				id: 'cd-4',
				name: 'Executive RRSP',
				type: 'pre_tax',
				calculationType: 'percentage',
				amount: 10,
				isEmployerContribution: true,
				employerAmount: 5,
				isDefaultEnabled: true,
				description: 'Enhanced RRSP with 5% employer match'
			}
		],

		createdAt: '2025-02-01T09:00:00Z',
		updatedAt: '2025-11-15T11:00:00Z'
	},
	{
		id: 'pg-3',
		companyId: 'company-1',
		name: 'Bi-weekly Part-time',
		description: 'Bi-weekly payroll for part-time and casual staff',
		payFrequency: 'bi_weekly',
		employmentType: 'part_time',
		nextPayDate: '2025-12-26',
		periodStartDay: 'monday',
		leaveEnabled: true,

		// Statutory: Standard
		statutoryDefaults: {
			cppExemptByDefault: false,
			cpp2ExemptByDefault: false,
			eiExemptByDefault: false
		},

		// Overtime: Bank time enabled
		overtimePolicy: {
			bankTimeEnabled: true,
			bankTimeRate: 1.5,
			bankTimeExpiryMonths: 6,
			requireWrittenAgreement: true
		},

		// WCB: Enabled
		wcbConfig: {
			enabled: true,
			industryClassCode: '44110',
			industryName: 'Retail Trade',
			assessmentRate: 1.05,
			maxAssessableEarnings: 112500
		},

		// Benefits: Minimal (part-time often don't get full benefits)
		groupBenefits: {
			enabled: false,
			health: {
				enabled: false,
				employeeDeduction: 0,
				employerContribution: 0,
				isTaxable: false
			},
			dental: {
				enabled: false,
				employeeDeduction: 0,
				employerContribution: 0,
				isTaxable: false
			},
			vision: {
				enabled: false,
				employeeDeduction: 0,
				employerContribution: 0,
				isTaxable: false
			},
			lifeInsurance: {
				enabled: false,
				employeeDeduction: 0,
				employerContribution: 0,
				isTaxable: false,
				coverageAmount: 0
			},
			disability: {
				enabled: false,
				employeeDeduction: 0,
				employerContribution: 0,
				isTaxable: false
			}
		},

		// Custom deductions: None
		customDeductions: [],

		createdAt: '2025-03-10T14:00:00Z',
		updatedAt: '2025-10-20T16:45:00Z'
	}
];

/**
 * Get a mock pay group by ID
 */
export function getMockPayGroup(id: string): PayGroup | undefined {
	return MOCK_PAY_GROUPS.find((pg) => pg.id === id);
}

/**
 * Get all mock pay groups for a company
 */
export function getMockPayGroupsForCompany(companyId: string): PayGroup[] {
	return MOCK_PAY_GROUPS.filter((pg) => pg.companyId === companyId);
}

/**
 * Add a new pay group to mock data
 */
export function addMockPayGroup(payGroup: PayGroup): void {
	MOCK_PAY_GROUPS.push(payGroup);
}

/**
 * Update a pay group in mock data
 */
export function updateMockPayGroup(payGroup: PayGroup): void {
	const index = MOCK_PAY_GROUPS.findIndex((pg) => pg.id === payGroup.id);
	if (index !== -1) {
		MOCK_PAY_GROUPS[index] = payGroup;
	}
}

/**
 * Delete a pay group from mock data
 */
export function deleteMockPayGroup(id: string): void {
	const index = MOCK_PAY_GROUPS.findIndex((pg) => pg.id === id);
	if (index !== -1) {
		MOCK_PAY_GROUPS.splice(index, 1);
	}
}
