/**
 * Mock data for Payroll Dashboard with multi pay group support
 */

import type {
	UpcomingPayDate,
	PayrollRunWithGroups,
	PayrollRecord,
	Holiday
} from '$lib/types/payroll';

// ===========================================
// Mock Holidays
// ===========================================
const mockHolidays: Holiday[] = [
	{ date: '2025-12-25', name: 'Christmas Day', province: 'ON' },
	{ date: '2025-12-26', name: 'Boxing Day', province: 'ON' }
];

// ===========================================
// Mock Employee Records by Pay Group
// ===========================================

// Bi-weekly Full-time employees
const biweeklyFulltimeRecords: PayrollRecord[] = [
	{
		id: 'rec-001',
		employeeId: 'emp-1',
		employeeName: 'Sarah Johnson',
		employeeProvince: 'ON',
		grossRegular: 3269.23,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 3269.23,
		cppEmployee: 158.76,
		cppAdditional: 0,
		eiEmployee: 55.58,
		federalTax: 420.0,
		provincialTax: 215.0,
		rrsp: 200.0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 1049.34,
		netPay: 2219.89,
		cppEmployer: 158.76,
		eiEmployer: 77.81,
		totalEmployerCost: 236.57,
		ytdGross: 45769.22,
		ytdCpp: 2222.64,
		ytdEi: 778.12,
		ytdFederalTax: 5880.0,
		ytdProvincialTax: 3010.0,
		ytdNetPay: 31078.46,
		holidayWorkHours: []
	},
	{
		id: 'rec-002',
		employeeId: 'emp-2',
		employeeName: 'Michael Chen',
		employeeProvince: 'BC',
		grossRegular: 3600.0,
		grossOvertime: 337.5,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 144.0,
		otherEarnings: 0,
		totalGross: 4081.5,
		cppEmployee: 198.16,
		cppAdditional: 0,
		eiEmployee: 69.39,
		federalTax: 580.0,
		provincialTax: 295.0,
		rrsp: 0,
		unionDues: 50.0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 1192.55,
		netPay: 2888.95,
		cppEmployer: 198.16,
		eiEmployer: 97.15,
		totalEmployerCost: 295.31,
		ytdGross: 57141.0,
		ytdCpp: 2774.24,
		ytdEi: 971.4,
		ytdFederalTax: 8120.0,
		ytdProvincialTax: 4130.0,
		ytdNetPay: 40445.36,
		holidayWorkHours: []
	},
	{
		id: 'rec-003',
		employeeId: 'emp-3',
		employeeName: 'Emily Davis',
		employeeProvince: 'ON',
		grossRegular: 2884.62,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 2884.62,
		cppEmployee: 140.11,
		cppAdditional: 0,
		eiEmployee: 49.04,
		federalTax: 300.0,
		provincialTax: 200.0,
		rrsp: 100.0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 789.15,
		netPay: 2095.47,
		cppEmployer: 140.11,
		eiEmployer: 68.66,
		totalEmployerCost: 208.77,
		ytdGross: 40384.68,
		ytdCpp: 1961.54,
		ytdEi: 686.56,
		ytdFederalTax: 4200.0,
		ytdProvincialTax: 2800.0,
		ytdNetPay: 29336.58,
		holidayWorkHours: []
	},
	{
		id: 'rec-004',
		employeeId: 'emp-4',
		employeeName: 'David Kim',
		employeeProvince: 'ON',
		grossRegular: 3076.92,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 3076.92,
		cppEmployee: 149.44,
		cppAdditional: 0,
		eiEmployee: 52.31,
		federalTax: 360.0,
		provincialTax: 195.0,
		rrsp: 150.0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 906.75,
		netPay: 2170.17,
		cppEmployer: 149.44,
		eiEmployer: 73.23,
		totalEmployerCost: 222.67,
		ytdGross: 43076.88,
		ytdCpp: 2092.16,
		ytdEi: 732.34,
		ytdFederalTax: 5040.0,
		ytdProvincialTax: 2730.0,
		ytdNetPay: 31182.38,
		holidayWorkHours: []
	},
	{
		id: 'rec-005',
		employeeId: 'emp-5',
		employeeName: 'Lisa Wang',
		employeeProvince: 'AB',
		grossRegular: 3461.54,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 3461.54,
		cppEmployee: 168.11,
		cppAdditional: 0,
		eiEmployee: 58.85,
		federalTax: 480.0,
		provincialTax: 180.0,
		rrsp: 200.0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 1086.96,
		netPay: 2374.58,
		cppEmployer: 168.11,
		eiEmployer: 82.39,
		totalEmployerCost: 250.5,
		ytdGross: 48461.56,
		ytdCpp: 2353.54,
		ytdEi: 823.9,
		ytdFederalTax: 6720.0,
		ytdProvincialTax: 2520.0,
		ytdNetPay: 34244.12,
		holidayWorkHours: []
	},
	{
		id: 'rec-006',
		employeeId: 'emp-6',
		employeeName: 'James Wilson',
		employeeProvince: 'ON',
		grossRegular: 2692.31,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 2692.31,
		cppEmployee: 130.78,
		cppAdditional: 0,
		eiEmployee: 45.77,
		federalTax: 280.0,
		provincialTax: 165.0,
		rrsp: 0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 621.55,
		netPay: 2070.76,
		cppEmployer: 130.78,
		eiEmployer: 64.08,
		totalEmployerCost: 194.86,
		ytdGross: 37692.34,
		ytdCpp: 1830.92,
		ytdEi: 640.78,
		ytdFederalTax: 3920.0,
		ytdProvincialTax: 2310.0,
		ytdNetPay: 27990.64,
		holidayWorkHours: []
	}
];

// Bi-weekly Part-time employees
const biweeklyParttimeRecords: PayrollRecord[] = [
	{
		id: 'rec-007',
		employeeId: 'emp-7',
		employeeName: 'Amy Thompson',
		employeeProvince: 'ON',
		grossRegular: 1200.0,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 1200.0,
		cppEmployee: 58.28,
		cppAdditional: 0,
		eiEmployee: 20.4,
		federalTax: 80.0,
		provincialTax: 45.0,
		rrsp: 0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 203.68,
		netPay: 996.32,
		cppEmployer: 58.28,
		eiEmployer: 28.56,
		totalEmployerCost: 86.84,
		ytdGross: 16800.0,
		ytdCpp: 815.92,
		ytdEi: 285.6,
		ytdFederalTax: 1120.0,
		ytdProvincialTax: 630.0,
		ytdNetPay: 13948.48,
		holidayWorkHours: []
	},
	{
		id: 'rec-008',
		employeeId: 'emp-8',
		employeeName: 'Brian Lee',
		employeeProvince: 'ON',
		grossRegular: 1500.0,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 1500.0,
		cppEmployee: 72.85,
		cppAdditional: 0,
		eiEmployee: 25.5,
		federalTax: 110.0,
		provincialTax: 60.0,
		rrsp: 0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 268.35,
		netPay: 1231.65,
		cppEmployer: 72.85,
		eiEmployer: 35.7,
		totalEmployerCost: 108.55,
		ytdGross: 21000.0,
		ytdCpp: 1019.9,
		ytdEi: 357.0,
		ytdFederalTax: 1540.0,
		ytdProvincialTax: 840.0,
		ytdNetPay: 17243.1,
		holidayWorkHours: []
	}
];

// Monthly Executive employees
const monthlyExecutiveRecords: PayrollRecord[] = [
	{
		id: 'rec-009',
		employeeId: 'emp-9',
		employeeName: 'Robert Martinez',
		employeeProvince: 'ON',
		grossRegular: 12500.0,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 12500.0,
		cppEmployee: 607.0,
		cppAdditional: 188.0,
		eiEmployee: 0, // EI exempt
		federalTax: 2800.0,
		provincialTax: 1450.0,
		rrsp: 500.0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 5545.0,
		netPay: 6955.0,
		cppEmployer: 607.0,
		eiEmployer: 0,
		totalEmployerCost: 607.0,
		ytdGross: 137500.0,
		ytdCpp: 6677.0,
		ytdEi: 0,
		ytdFederalTax: 30800.0,
		ytdProvincialTax: 15950.0,
		ytdNetPay: 76505.0,
		holidayWorkHours: []
	},
	{
		id: 'rec-010',
		employeeId: 'emp-10',
		employeeName: 'Jennifer Brown',
		employeeProvince: 'ON',
		grossRegular: 10000.0,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 10000.0,
		cppEmployee: 485.6,
		cppAdditional: 0,
		eiEmployee: 0, // EI exempt
		federalTax: 2100.0,
		provincialTax: 1100.0,
		rrsp: 400.0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 4085.6,
		netPay: 5914.4,
		cppEmployer: 485.6,
		eiEmployer: 0,
		totalEmployerCost: 485.6,
		ytdGross: 110000.0,
		ytdCpp: 5341.6,
		ytdEi: 0,
		ytdFederalTax: 23100.0,
		ytdProvincialTax: 12100.0,
		ytdNetPay: 65058.4,
		holidayWorkHours: []
	},
	{
		id: 'rec-011',
		employeeId: 'emp-11',
		employeeName: 'William Taylor',
		employeeProvince: 'ON',
		grossRegular: 8500.0,
		grossOvertime: 0,
		holidayPay: 0,
		holidayPremiumPay: 0,
		vacationPayPaid: 0,
		otherEarnings: 0,
		totalGross: 8500.0,
		cppEmployee: 412.76,
		cppAdditional: 0,
		eiEmployee: 0, // EI exempt
		federalTax: 1700.0,
		provincialTax: 900.0,
		rrsp: 300.0,
		unionDues: 0,
		garnishments: 0,
		otherDeductions: 0,
		totalDeductions: 3312.76,
		netPay: 5187.24,
		cppEmployer: 412.76,
		eiEmployer: 0,
		totalEmployerCost: 412.76,
		ytdGross: 93500.0,
		ytdCpp: 4540.36,
		ytdEi: 0,
		ytdFederalTax: 18700.0,
		ytdProvincialTax: 9900.0,
		ytdNetPay: 57059.64,
		holidayWorkHours: []
	}
];

// ===========================================
// Upcoming Pay Dates for Dashboard
// ===========================================

export function getMockUpcomingPayDates(): UpcomingPayDate[] {
	return [
		{
			payDate: '2025-12-20',
			payGroups: [
				{
					id: 'pg-1',
					name: 'Bi-weekly Full-time',
					payFrequency: 'bi_weekly',
					employmentType: 'full_time',
					employeeCount: 6,
					estimatedGross: 19466.12,
					periodStart: '2025-12-01',
					periodEnd: '2025-12-14'
				},
				{
					id: 'pg-3',
					name: 'Bi-weekly Part-time',
					payFrequency: 'bi_weekly',
					employmentType: 'part_time',
					employeeCount: 2,
					estimatedGross: 2700.0,
					periodStart: '2025-12-01',
					periodEnd: '2025-12-14'
				}
			],
			totalEmployees: 8,
			totalEstimatedGross: 22166.12,
			runStatus: 'pending_approval',
			runId: 'run-001'
		},
		{
			payDate: '2025-12-31',
			payGroups: [
				{
					id: 'pg-2',
					name: 'Monthly Executives',
					payFrequency: 'monthly',
					employmentType: 'full_time',
					employeeCount: 3,
					estimatedGross: 31000.0,
					periodStart: '2025-12-01',
					periodEnd: '2025-12-31'
				}
			],
			totalEmployees: 3,
			totalEstimatedGross: 31000.0
		},
		{
			payDate: '2026-01-03',
			payGroups: [
				{
					id: 'pg-1',
					name: 'Bi-weekly Full-time',
					payFrequency: 'bi_weekly',
					employmentType: 'full_time',
					employeeCount: 6,
					estimatedGross: 19466.12,
					periodStart: '2025-12-15',
					periodEnd: '2025-12-28'
				},
				{
					id: 'pg-3',
					name: 'Bi-weekly Part-time',
					payFrequency: 'bi_weekly',
					employmentType: 'part_time',
					employeeCount: 2,
					estimatedGross: 2700.0,
					periodStart: '2025-12-15',
					periodEnd: '2025-12-28'
				}
			],
			totalEmployees: 8,
			totalEstimatedGross: 22166.12
		}
	];
}

// ===========================================
// Payroll Run with Groups (for detail page)
// ===========================================

export function getMockPayrollRunWithGroups(payDate: string): PayrollRunWithGroups | null {
	// Only return data for December 20 (the one with pending_approval status)
	if (payDate !== '2025-12-20') {
		return null;
	}

	const biweeklyFTGross = biweeklyFulltimeRecords.reduce((sum, r) => sum + r.totalGross, 0);
	const biweeklyFTDeductions = biweeklyFulltimeRecords.reduce((sum, r) => sum + r.totalDeductions, 0);
	const biweeklyFTNetPay = biweeklyFulltimeRecords.reduce((sum, r) => sum + r.netPay, 0);
	const biweeklyFTEmployerCost = biweeklyFulltimeRecords.reduce((sum, r) => sum + r.totalEmployerCost, 0);

	const biweeklyPTGross = biweeklyParttimeRecords.reduce((sum, r) => sum + r.totalGross, 0);
	const biweeklyPTDeductions = biweeklyParttimeRecords.reduce((sum, r) => sum + r.totalDeductions, 0);
	const biweeklyPTNetPay = biweeklyParttimeRecords.reduce((sum, r) => sum + r.netPay, 0);
	const biweeklyPTEmployerCost = biweeklyParttimeRecords.reduce((sum, r) => sum + r.totalEmployerCost, 0);

	return {
		id: 'run-001',
		payDate: '2025-12-20',
		status: 'pending_approval',
		payGroups: [
			{
				payGroupId: 'pg-1',
				payGroupName: 'Bi-weekly Full-time',
				payFrequency: 'bi_weekly',
				employmentType: 'full_time',
				periodStart: '2025-12-01',
				periodEnd: '2025-12-14',
				totalEmployees: biweeklyFulltimeRecords.length,
				totalGross: biweeklyFTGross,
				totalDeductions: biweeklyFTDeductions,
				totalNetPay: biweeklyFTNetPay,
				totalEmployerCost: biweeklyFTEmployerCost,
				records: biweeklyFulltimeRecords
			},
			{
				payGroupId: 'pg-3',
				payGroupName: 'Bi-weekly Part-time',
				payFrequency: 'bi_weekly',
				employmentType: 'part_time',
				periodStart: '2025-12-01',
				periodEnd: '2025-12-14',
				totalEmployees: biweeklyParttimeRecords.length,
				totalGross: biweeklyPTGross,
				totalDeductions: biweeklyPTDeductions,
				totalNetPay: biweeklyPTNetPay,
				totalEmployerCost: biweeklyPTEmployerCost,
				records: biweeklyParttimeRecords
			}
		],
		totalEmployees: biweeklyFulltimeRecords.length + biweeklyParttimeRecords.length,
		totalGross: biweeklyFTGross + biweeklyPTGross,
		totalCppEmployee:
			biweeklyFulltimeRecords.reduce((sum, r) => sum + r.cppEmployee, 0) +
			biweeklyParttimeRecords.reduce((sum, r) => sum + r.cppEmployee, 0),
		totalCppEmployer:
			biweeklyFulltimeRecords.reduce((sum, r) => sum + r.cppEmployer, 0) +
			biweeklyParttimeRecords.reduce((sum, r) => sum + r.cppEmployer, 0),
		totalEiEmployee:
			biweeklyFulltimeRecords.reduce((sum, r) => sum + r.eiEmployee, 0) +
			biweeklyParttimeRecords.reduce((sum, r) => sum + r.eiEmployee, 0),
		totalEiEmployer:
			biweeklyFulltimeRecords.reduce((sum, r) => sum + r.eiEmployer, 0) +
			biweeklyParttimeRecords.reduce((sum, r) => sum + r.eiEmployer, 0),
		totalFederalTax:
			biweeklyFulltimeRecords.reduce((sum, r) => sum + r.federalTax, 0) +
			biweeklyParttimeRecords.reduce((sum, r) => sum + r.federalTax, 0),
		totalProvincialTax:
			biweeklyFulltimeRecords.reduce((sum, r) => sum + r.provincialTax, 0) +
			biweeklyParttimeRecords.reduce((sum, r) => sum + r.provincialTax, 0),
		totalDeductions: biweeklyFTDeductions + biweeklyPTDeductions,
		totalNetPay: biweeklyFTNetPay + biweeklyPTNetPay,
		totalEmployerCost: biweeklyFTEmployerCost + biweeklyPTEmployerCost,
		holidays: mockHolidays
	};
}

// ===========================================
// Helper: Get Payroll Run for Monthly Executives
// ===========================================

export function getMockMonthlyExecutivesRun(): PayrollRunWithGroups {
	const execGross = monthlyExecutiveRecords.reduce((sum, r) => sum + r.totalGross, 0);
	const execDeductions = monthlyExecutiveRecords.reduce((sum, r) => sum + r.totalDeductions, 0);
	const execNetPay = monthlyExecutiveRecords.reduce((sum, r) => sum + r.netPay, 0);
	const execEmployerCost = monthlyExecutiveRecords.reduce((sum, r) => sum + r.totalEmployerCost, 0);

	return {
		id: 'run-002',
		payDate: '2025-12-31',
		status: 'draft',
		payGroups: [
			{
				payGroupId: 'pg-2',
				payGroupName: 'Monthly Executives',
				payFrequency: 'monthly',
				employmentType: 'full_time',
				periodStart: '2025-12-01',
				periodEnd: '2025-12-31',
				totalEmployees: monthlyExecutiveRecords.length,
				totalGross: execGross,
				totalDeductions: execDeductions,
				totalNetPay: execNetPay,
				totalEmployerCost: execEmployerCost,
				records: monthlyExecutiveRecords
			}
		],
		totalEmployees: monthlyExecutiveRecords.length,
		totalGross: execGross,
		totalCppEmployee: monthlyExecutiveRecords.reduce((sum, r) => sum + r.cppEmployee + r.cppAdditional, 0),
		totalCppEmployer: monthlyExecutiveRecords.reduce((sum, r) => sum + r.cppEmployer, 0),
		totalEiEmployee: monthlyExecutiveRecords.reduce((sum, r) => sum + r.eiEmployee, 0),
		totalEiEmployer: monthlyExecutiveRecords.reduce((sum, r) => sum + r.eiEmployer, 0),
		totalFederalTax: monthlyExecutiveRecords.reduce((sum, r) => sum + r.federalTax, 0),
		totalProvincialTax: monthlyExecutiveRecords.reduce((sum, r) => sum + r.provincialTax, 0),
		totalDeductions: execDeductions,
		totalNetPay: execNetPay,
		totalEmployerCost: execEmployerCost,
		holidays: []
	};
}
