<script lang="ts">
	import type { PayrollRun, PayrollRecord, Holiday, HolidayWorkEntry, LeaveEntry, OvertimeEntry, PaystubStatus } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import { StatusBadge } from '$lib/components/shared';
	import {
		PayrollSummaryCards,
		PayrollRecordTable,
		HolidayAlert,
		HolidayWorkModal,
		LeaveAlert,
		LeaveModal,
		OvertimeModal
	} from '$lib/components/payroll';

	// ===========================================
	// Mock Data
	// ===========================================
	const mockHolidays: Holiday[] = [
		{ date: '2025-12-25', name: 'Christmas Day', province: 'ON' },
		{ date: '2025-12-26', name: 'Boxing Day', province: 'ON' }
	];

	const mockPayrollRun: PayrollRun = {
		id: 'pr-001',
		periodStart: '2025-12-01',
		periodEnd: '2025-12-15',
		payDate: '2025-12-20',
		status: 'pending_approval', // Default state - use Approve button to see paystub UI
		totalEmployees: 4,
		totalGross: 11538.46,
		totalCppEmployee: 560.42,
		totalCppEmployer: 560.42,
		totalEiEmployee: 196.15,
		totalEiEmployer: 274.61,
		totalFederalTax: 1320.0,
		totalProvincialTax: 680.0,
		totalDeductions: 2756.57,
		totalNetPay: 8781.89,
		totalEmployerCost: 835.03,
		holidays: mockHolidays
	};

	const mockPayrollRecords: PayrollRecord[] = [
		{
			id: 'rec-001',
			employeeId: '1',
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
			employeeId: '2',
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
			employeeId: '3',
			employeeName: 'Emily Davis',
			employeeProvince: 'ON',
			grossRegular: 2166.67,
			grossOvertime: 0,
			holidayPay: 0,
			holidayPremiumPay: 0,
			vacationPayPaid: 0,
			otherEarnings: 0,
			totalGross: 2166.67,
			cppEmployee: 105.23,
			cppAdditional: 0,
			eiEmployee: 36.83,
			federalTax: 180.0,
			provincialTax: 95.0,
			rrsp: 100.0,
			unionDues: 0,
			garnishments: 0,
			otherDeductions: 0,
			totalDeductions: 517.06,
			netPay: 1649.61,
			cppEmployer: 105.23,
			eiEmployer: 51.56,
			totalEmployerCost: 156.79,
			ytdGross: 30333.38,
			ytdCpp: 1473.22,
			ytdEi: 515.62,
			ytdFederalTax: 2520.0,
			ytdProvincialTax: 1330.0,
			ytdNetPay: 23094.54,
			holidayWorkHours: []
		},
		{
			id: 'rec-004',
			employeeId: '4',
			employeeName: 'James Wilson',
			employeeProvince: 'AB',
			grossRegular: 2000.0,
			grossOvertime: 0,
			holidayPay: 0,
			holidayPremiumPay: 0,
			vacationPayPaid: 0,
			otherEarnings: 0,
			totalGross: 2000.0,
			cppEmployee: 0,
			cppAdditional: 0,
			eiEmployee: 0,
			federalTax: 140.0,
			provincialTax: 75.0,
			rrsp: 0,
			unionDues: 0,
			garnishments: 0,
			otherDeductions: 0,
			totalDeductions: 215.0,
			netPay: 1785.0,
			cppEmployer: 0,
			eiEmployer: 0,
			totalEmployerCost: 0,
			ytdGross: 24000.0,
			ytdCpp: 0,
			ytdEi: 0,
			ytdFederalTax: 1680.0,
			ytdProvincialTax: 900.0,
			ytdNetPay: 21420.0,
			holidayWorkHours: []
		}
	];

	// ===========================================
	// State
	// ===========================================
	let payrollRun = $state(mockPayrollRun);
	let payrollRecords = $state(mockPayrollRecords);
	let expandedRecordId = $state<string | null>(null);
	let showHolidayModal = $state(false);
	let showLeaveModal = $state(false);
	let showOvertimeModal = $state(false);
	let leaveEntries = $state<LeaveEntry[]>([]);
	let overtimeEntries = $state<OvertimeEntry[]>([]);
	let selectedLeaveEmployee = $state<PayrollRecord | null>(null);

	// ===========================================
	// Helpers
	// ===========================================
	function formatDateRange(start: string, end: string): string {
		const startDate = new Date(start);
		const endDate = new Date(end);
		return `${startDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })} - ${endDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' })}`;
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	// ===========================================
	// Actions
	// ===========================================
	function toggleExpand(id: string) {
		expandedRecordId = expandedRecordId === id ? null : id;
	}

	function openHolidayModal() {
		showHolidayModal = true;
	}

	function closeHolidayModal() {
		showHolidayModal = false;
	}

	function handleHolidayWorkSave(entries: HolidayWorkEntry[]) {
		// Process saved holiday work entries
		console.log('Holiday work entries saved:', entries);

		// Update payroll records with holiday work hours
		// In a real implementation, this would trigger recalculation
		payrollRecords = payrollRecords.map((record) => {
			const employeeEntries = entries.filter((e) => e.employeeId === record.employeeId);
			return {
				...record,
				holidayWorkHours: employeeEntries
			};
		});

		showHolidayModal = false;
	}

	// ===========================================
	// Leave Actions
	// ===========================================
	function openLeaveModal(employee?: PayrollRecord) {
		selectedLeaveEmployee = employee || null;
		showLeaveModal = true;
	}

	function closeLeaveModal() {
		showLeaveModal = false;
		selectedLeaveEmployee = null;
	}

	function handleLeaveSave(entries: LeaveEntry[]) {
		console.log('Leave entries saved:', entries);

		// Update leave entries state
		leaveEntries = entries;

		// Update payroll records with leave entries
		payrollRecords = payrollRecords.map((record) => {
			const employeeLeave = entries.filter((e) => e.employeeId === record.employeeId);
			const vacationHours = employeeLeave
				.filter((e) => e.leaveType === 'vacation')
				.reduce((sum, e) => sum + e.hours, 0);
			const sickHours = employeeLeave
				.filter((e) => e.leaveType === 'sick')
				.reduce((sum, e) => sum + e.hours, 0);
			const vacationPay = employeeLeave
				.filter((e) => e.leaveType === 'vacation')
				.reduce((sum, e) => sum + e.leavePay, 0);
			const sickPay = employeeLeave
				.filter((e) => e.leaveType === 'sick')
				.reduce((sum, e) => sum + e.leavePay, 0);

			return {
				...record,
				leaveEntries: employeeLeave,
				vacationHoursTaken: vacationHours,
				sickHoursTaken: sickHours,
				vacationPayPaid: record.vacationPayPaid + vacationPay,
				sickPayPaid: sickPay
			};
		});

		showLeaveModal = false;
	}

	// ===========================================
	// Overtime Actions
	// ===========================================
	function openOvertimeModal() {
		showOvertimeModal = true;
	}

	function closeOvertimeModal() {
		showOvertimeModal = false;
	}

	function handleOvertimeSave(entries: OvertimeEntry[]) {
		console.log('Overtime entries saved:', entries);

		// Update overtime entries state
		overtimeEntries = entries;

		// Update payroll records with overtime entries
		payrollRecords = payrollRecords.map((record) => {
			const employeeOvertime = entries.filter((e) => e.employeeId === record.employeeId);
			const totalOvertimePay = employeeOvertime.reduce((sum, e) => sum + e.overtimePay, 0);

			return {
				...record,
				overtimeEntries: employeeOvertime,
				grossOvertime: totalOvertimePay,
				totalGross: record.grossRegular + totalOvertimePay + record.holidayPay + record.holidayPremiumPay + record.vacationPayPaid + record.otherEarnings
			};
		});

		showOvertimeModal = false;
	}

	// ===========================================
	// Approve Action
	// ===========================================
	function handleApprove() {
		// Simulate approval: change status and set paystub statuses
		payrollRun = {
			...payrollRun,
			status: 'approved'
		};

		// Simulate sending paystubs (3 sent, 1 failed for demo)
		payrollRecords = payrollRecords.map((record, index) => ({
			...record,
			paystubStatus: (index === 2 ? 'failed' : 'sent') as PaystubStatus,
			paystubSentAt: index === 2 ? undefined : new Date().toISOString(),
			paystubSentTo: `${record.employeeName.toLowerCase().replace(' ', '.')}@example.com`
		}));
	}

	// ===========================================
	// Paystub Actions
	// ===========================================
	function handleDownloadAllPaystubs() {
		console.log('Downloading all paystubs as ZIP...');
		// Mock implementation - would trigger ZIP download
		alert('Download All Paystubs: This would download a ZIP file containing all paystubs.');
	}

	function handleResendAll() {
		console.log('Resending all paystubs...');
		// Mock implementation - would resend emails
		alert('Resend All: This would resend paystubs to all employees via email.');
	}

	function handleDownloadPaystub(record: PayrollRecord) {
		console.log('Downloading paystub for:', record.employeeName);
		alert(`Download Paystub: This would download the PDF for ${record.employeeName}.`);
	}

	function handleResendPaystub(record: PayrollRecord) {
		console.log('Resending paystub to:', record.employeeName);
		// Mock implementation - update status to sending, then sent
		payrollRecords = payrollRecords.map((r) => {
			if (r.id === record.id) {
				return {
					...r,
					paystubStatus: 'sent' as const,
					paystubSentAt: new Date().toISOString()
				};
			}
			return r;
		});
		alert(`Resend Paystub: Email sent to ${record.paystubSentTo || record.employeeName}.`);
	}

	// Check if payroll is approved or paid (show paystub actions)
	const isApprovedOrPaid = $derived(
		payrollRun.status === 'approved' || payrollRun.status === 'paid'
	);
</script>

<svelte:head>
	<title>Run Payroll - BeanFlow Payroll</title>
</svelte:head>

<div class="payroll-page">
	<!-- Header -->
	<header class="page-header">
		<div class="header-content">
			<div class="breadcrumb">
				<a href="/payroll/history">Payroll</a>
				<i class="fas fa-chevron-right"></i>
				<span>{formatDateRange(payrollRun.periodStart, payrollRun.periodEnd)}</span>
			</div>
			<h1 class="page-title">Pay Period: {formatDateRange(payrollRun.periodStart, payrollRun.periodEnd)}</h1>
			<p class="page-subtitle">Pay Date: {formatDate(payrollRun.payDate)}</p>
		</div>
		<div class="header-actions">
			<StatusBadge status={PAYROLL_STATUS_LABELS[payrollRun.status]} variant="pill" />
			<button class="btn-secondary">
				<i class="fas fa-file-csv"></i>
				<span>Export CSV</span>
			</button>
			{#if isApprovedOrPaid}
				<!-- Approved/Paid state: Show paystub actions -->
				<button class="btn-secondary" onclick={handleDownloadAllPaystubs}>
					<i class="fas fa-file-archive"></i>
					<span>Download All Paystubs</span>
				</button>
				<button class="btn-primary" onclick={handleResendAll}>
					<i class="fas fa-paper-plane"></i>
					<span>Resend All</span>
				</button>
			{:else}
				<!-- Pre-approval state: Show approve button -->
				<button class="btn-primary" onclick={handleApprove}>
					<i class="fas fa-check"></i>
					<span>Approve</span>
				</button>
			{/if}
		</div>
	</header>

	<!-- Holiday Alert -->
	<HolidayAlert holidays={payrollRun.holidays || []} onManageHolidayHours={openHolidayModal} />

	<!-- Leave Alert -->
	<LeaveAlert {leaveEntries} onManageLeaveHours={() => openLeaveModal()} />

	<!-- Overtime Section -->
	<div class="overtime-section">
		<div class="overtime-content">
			<div class="overtime-info">
				<i class="fas fa-clock"></i>
				<span>
					{#if overtimeEntries.length > 0}
						{@const totalHours = overtimeEntries.reduce((sum, e) => sum + e.hours, 0)}
						{@const totalPay = overtimeEntries.reduce((sum, e) => sum + e.overtimePay, 0)}
						<strong>{totalHours}h overtime</strong> recorded ({new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD' }).format(totalPay)})
					{:else}
						No overtime recorded for this period
					{/if}
				</span>
			</div>
			<button class="manage-btn" onclick={openOvertimeModal}>
				<i class="fas fa-edit"></i>
				<span>Manage Overtime</span>
			</button>
		</div>
	</div>

	<!-- Summary Cards -->
	<PayrollSummaryCards {payrollRun} />

	<!-- Employee Payroll Table -->
	<PayrollRecordTable
		{payrollRun}
		{payrollRecords}
		{expandedRecordId}
		onToggleExpand={toggleExpand}
		onDownloadPaystub={handleDownloadPaystub}
		onResendPaystub={handleResendPaystub}
		onLeaveClick={openLeaveModal}
	/>
</div>

<!-- Holiday Work Modal -->
{#if showHolidayModal}
	<HolidayWorkModal
		holidays={payrollRun.holidays || []}
		{payrollRecords}
		periodStart={payrollRun.periodStart}
		periodEnd={payrollRun.periodEnd}
		onClose={closeHolidayModal}
		onSave={handleHolidayWorkSave}
	/>
{/if}

<!-- Leave Modal -->
{#if showLeaveModal}
	<LeaveModal
		{payrollRecords}
		periodStart={payrollRun.periodStart}
		periodEnd={payrollRun.periodEnd}
		existingLeaveEntries={leaveEntries}
		selectedEmployee={selectedLeaveEmployee ?? undefined}
		onClose={closeLeaveModal}
		onSave={handleLeaveSave}
	/>
{/if}

<!-- Overtime Modal -->
{#if showOvertimeModal}
	<OvertimeModal
		{payrollRecords}
		periodStart={payrollRun.periodStart}
		periodEnd={payrollRun.periodEnd}
		existingOvertimeEntries={overtimeEntries}
		onClose={closeOvertimeModal}
		onSave={handleOvertimeSave}
	/>
{/if}

<style>
	.payroll-page {
		max-width: 1200px;
	}

	/* Header */
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: var(--spacing-6);
		flex-wrap: wrap;
		gap: var(--spacing-4);
	}

	.breadcrumb {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-bottom: var(--spacing-2);
	}

	.breadcrumb a {
		color: var(--color-primary-600);
		text-decoration: none;
	}

	.breadcrumb a:hover {
		text-decoration: underline;
	}

	.breadcrumb i {
		font-size: 10px;
	}

	.page-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.page-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	.header-actions {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.btn-primary,
	.btn-secondary {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	/* Overtime Section */
	.overtime-section {
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		margin-bottom: var(--spacing-6);
	}

	.overtime-content {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--spacing-4);
	}

	.overtime-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.overtime-info i {
		color: var(--color-primary-600);
		font-size: var(--font-size-title-small);
	}

	.manage-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		background: white;
		color: var(--color-surface-700);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.manage-btn:hover {
		background: var(--color-surface-100);
		border-color: var(--color-surface-400);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.page-header {
			flex-direction: column;
		}

		.header-actions {
			width: 100%;
			flex-wrap: wrap;
		}
	}
</style>
