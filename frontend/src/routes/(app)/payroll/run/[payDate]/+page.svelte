<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import type {
		PayrollRunWithGroups,
		PayrollRecord,
		Holiday,
		HolidayWorkEntry,
		LeaveEntry,
		OvertimeEntry,
		PaystubStatus
	} from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import { StatusBadge } from '$lib/components/shared';
	import {
		PayGroupSection,
		PayrollSummaryCards,
		HolidayAlert,
		HolidayWorkModal,
		LeaveAlert,
		LeaveModal,
		OvertimeModal
	} from '$lib/components/payroll';
	import { getMockPayrollRunWithGroups, getMockMonthlyExecutivesRun } from '$lib/mocks/payroll-dashboard';

	// ===========================================
	// Route Params
	// ===========================================
	const payDate = $derived($page.params.payDate ?? '');

	// ===========================================
	// State
	// ===========================================
	let payrollRun = $state<PayrollRunWithGroups | null>(null);
	let expandedRecordId = $state<string | null>(null);
	let showHolidayModal = $state(false);
	let showLeaveModal = $state(false);
	let showOvertimeModal = $state(false);
	let leaveEntries = $state<LeaveEntry[]>([]);
	let overtimeEntries = $state<OvertimeEntry[]>([]);
	let selectedLeaveEmployee = $state<PayrollRecord | null>(null);
	let selectedOvertimeEmployee = $state<PayrollRecord | null>(null);

	// Load data based on payDate
	$effect(() => {
		if (payDate === '2025-12-20') {
			payrollRun = getMockPayrollRunWithGroups(payDate);
		} else if (payDate === '2025-12-31') {
			payrollRun = getMockMonthlyExecutivesRun();
		} else {
			// For other dates, create a draft run
			payrollRun = null;
		}
	});

	// ===========================================
	// Computed
	// ===========================================
	const allRecords = $derived(
		payrollRun ? payrollRun.payGroups.flatMap((pg) => pg.records) : []
	);

	const isApprovedOrPaid = $derived(
		payrollRun?.status === 'approved' || payrollRun?.status === 'paid'
	);

	// Create a compatible PayrollRun object for existing components
	const payrollRunCompat = $derived(
		payrollRun
			? {
					id: payrollRun.id,
					periodStart: payrollRun.payGroups[0]?.periodStart || '',
					periodEnd: payrollRun.payGroups[0]?.periodEnd || '',
					payDate: payrollRun.payDate,
					status: payrollRun.status,
					totalEmployees: payrollRun.totalEmployees,
					totalGross: payrollRun.totalGross,
					totalCppEmployee: payrollRun.totalCppEmployee,
					totalCppEmployer: payrollRun.totalCppEmployer,
					totalEiEmployee: payrollRun.totalEiEmployee,
					totalEiEmployer: payrollRun.totalEiEmployer,
					totalFederalTax: payrollRun.totalFederalTax,
					totalProvincialTax: payrollRun.totalProvincialTax,
					totalDeductions: payrollRun.totalDeductions,
					totalNetPay: payrollRun.totalNetPay,
					totalEmployerCost: payrollRun.totalEmployerCost,
					holidays: payrollRun.holidays
				}
			: null
	);

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
			weekday: 'long',
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}

	// ===========================================
	// Actions
	// ===========================================
	function toggleExpand(id: string) {
		expandedRecordId = expandedRecordId === id ? null : id;
	}

	function handleBack() {
		goto('/payroll');
	}

	function openHolidayModal() {
		showHolidayModal = true;
	}

	function closeHolidayModal() {
		showHolidayModal = false;
	}

	function handleHolidayWorkSave(entries: HolidayWorkEntry[]) {
		console.log('Holiday work entries saved:', entries);
		showHolidayModal = false;
	}

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
		leaveEntries = entries;
		showLeaveModal = false;
	}

	function openOvertimeModal(employee?: PayrollRecord) {
		selectedOvertimeEmployee = employee || null;
		showOvertimeModal = true;
	}

	function closeOvertimeModal() {
		showOvertimeModal = false;
		selectedOvertimeEmployee = null;
	}

	function handleOvertimeSave(entries: OvertimeEntry[]) {
		console.log('Overtime entries saved:', entries);
		overtimeEntries = entries;
		showOvertimeModal = false;
	}

	function handleApprove() {
		if (!payrollRun) return;

		// Simulate approval
		payrollRun = {
			...payrollRun,
			status: 'approved'
		};

		// Update records with paystub status
		payrollRun.payGroups = payrollRun.payGroups.map((pg) => ({
			...pg,
			records: pg.records.map((record, index) => ({
				...record,
				paystubStatus: (index === 2 ? 'failed' : 'sent') as PaystubStatus,
				paystubSentAt: index === 2 ? undefined : new Date().toISOString(),
				paystubSentTo: `${record.employeeName.toLowerCase().replace(' ', '.')}@example.com`
			}))
		}));
	}

	function handleDownloadAllPaystubs() {
		alert('Download All Paystubs: This would download a ZIP file containing all paystubs.');
	}

	function handleResendAll() {
		alert('Resend All: This would resend paystubs to all employees via email.');
	}

	function handleDownloadPaystub(record: PayrollRecord) {
		alert(`Download Paystub: This would download the PDF for ${record.employeeName}.`);
	}

	function handleResendPaystub(record: PayrollRecord) {
		alert(`Resend Paystub: Email sent to ${record.employeeName}.`);
	}
</script>

<svelte:head>
	<title>Payroll Run - {payDate} - BeanFlow Payroll</title>
</svelte:head>

{#if !payrollRun}
	<div class="not-found">
		<div class="not-found-icon">
			<i class="fas fa-calendar-times"></i>
		</div>
		<h2>Payroll Run Not Found</h2>
		<p>No payroll run exists for {formatDate(payDate)}.</p>
		<button class="btn-primary" onclick={handleBack}>
			<i class="fas fa-arrow-left"></i>
			<span>Back to Payroll</span>
		</button>
	</div>
{:else}
	<div class="payroll-run-page">
		<!-- Header -->
		<header class="page-header">
			<button class="back-btn" onclick={handleBack}>
				<i class="fas fa-arrow-left"></i>
				<span>Back to Payroll</span>
			</button>

			<div class="header-content">
				<div class="header-main">
					<h1 class="page-title">Pay Date: {formatDate(payrollRun.payDate)}</h1>
					{#if payrollRun.payGroups.length > 0}
						<p class="page-subtitle">
							{payrollRun.payGroups.length} Pay Group{payrollRun.payGroups.length > 1 ? 's' : ''}
							&middot;
							{payrollRun.totalEmployees} Employee{payrollRun.totalEmployees > 1 ? 's' : ''}
						</p>
					{/if}
				</div>
				<div class="header-actions">
					<StatusBadge status={PAYROLL_STATUS_LABELS[payrollRun.status]} variant="pill" />
					<button class="btn-secondary">
						<i class="fas fa-file-csv"></i>
						<span>Export CSV</span>
					</button>
					{#if isApprovedOrPaid}
						<button class="btn-secondary" onclick={handleDownloadAllPaystubs}>
							<i class="fas fa-file-archive"></i>
							<span>Download All Paystubs</span>
						</button>
						<button class="btn-primary" onclick={handleResendAll}>
							<i class="fas fa-paper-plane"></i>
							<span>Resend All</span>
						</button>
					{:else}
						<button class="btn-primary" onclick={handleApprove}>
							<i class="fas fa-check"></i>
							<span>Approve & Send Paystubs</span>
						</button>
					{/if}
				</div>
			</div>
		</header>

		<!-- Holiday Alert -->
		{#if payrollRun.holidays && payrollRun.holidays.length > 0}
			<HolidayAlert holidays={payrollRun.holidays} onManageHolidayHours={openHolidayModal} />
		{/if}

		<!-- Leave Alert -->
		<LeaveAlert {leaveEntries} onManageLeaveHours={() => openLeaveModal()} />

		<!-- Summary Cards -->
		{#if payrollRunCompat}
			<PayrollSummaryCards payrollRun={payrollRunCompat} />
		{/if}

		<!-- Pay Group Sections -->
		<div class="pay-groups-container">
			{#each payrollRun.payGroups as payGroup (payGroup.payGroupId)}
				<PayGroupSection
					{payGroup}
					runStatus={payrollRun.status}
					{expandedRecordId}
					onToggleExpand={toggleExpand}
					onDownloadPaystub={handleDownloadPaystub}
					onResendPaystub={handleResendPaystub}
					onLeaveClick={openLeaveModal}
					onOvertimeClick={openOvertimeModal}
				/>
			{/each}
		</div>
	</div>

	<!-- Holiday Work Modal -->
	{#if showHolidayModal && payrollRunCompat}
		<HolidayWorkModal
			holidays={payrollRun.holidays || []}
			payrollRecords={allRecords}
			periodStart={payrollRunCompat.periodStart}
			periodEnd={payrollRunCompat.periodEnd}
			onClose={closeHolidayModal}
			onSave={handleHolidayWorkSave}
		/>
	{/if}

	<!-- Leave Modal -->
	{#if showLeaveModal && payrollRunCompat}
		<LeaveModal
			payrollRecords={allRecords}
			periodStart={payrollRunCompat.periodStart}
			periodEnd={payrollRunCompat.periodEnd}
			existingLeaveEntries={leaveEntries}
			selectedEmployee={selectedLeaveEmployee ?? undefined}
			onClose={closeLeaveModal}
			onSave={handleLeaveSave}
		/>
	{/if}

	<!-- Overtime Modal -->
	{#if showOvertimeModal && payrollRunCompat}
		<OvertimeModal
			payrollRecords={allRecords}
			periodStart={payrollRunCompat.periodStart}
			periodEnd={payrollRunCompat.periodEnd}
			existingOvertimeEntries={overtimeEntries}
			selectedEmployee={selectedOvertimeEmployee ?? undefined}
			onClose={closeOvertimeModal}
			onSave={handleOvertimeSave}
		/>
	{/if}
{/if}

<style>
	.payroll-run-page {
		max-width: 1200px;
	}

	/* Not Found */
	.not-found {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
	}

	.not-found-icon {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		background: var(--color-surface-100);
		color: var(--color-surface-400);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 32px;
		margin-bottom: var(--spacing-4);
	}

	.not-found h2 {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.not-found p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6);
	}

	/* Header */
	.page-header {
		margin-bottom: var(--spacing-6);
	}

	.back-btn {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) 0;
		background: none;
		border: none;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-primary-600);
		cursor: pointer;
		margin-bottom: var(--spacing-4);
		transition: var(--transition-fast);
	}

	.back-btn:hover {
		color: var(--color-primary-700);
	}

	.back-btn i {
		font-size: 12px;
	}

	.header-content {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		flex-wrap: wrap;
		gap: var(--spacing-4);
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
		flex-wrap: wrap;
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
		text-decoration: none;
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

	/* Pay Groups Container */
	.pay-groups-container {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.header-content {
			flex-direction: column;
		}

		.header-actions {
			width: 100%;
		}
	}
</style>
