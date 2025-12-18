<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import type {
		PayrollRunWithGroups,
		PayrollRecord,
		HolidayWorkEntry,
		LeaveEntry,
		OvertimeEntry,
		PaystubStatus,
		UpcomingPayDate,
		PayGroupSummary
	} from '$lib/types/payroll';
	import type { Employee } from '$lib/types/employee';
	import { PAYROLL_STATUS_LABELS, PAY_FREQUENCY_LABELS, EMPLOYMENT_TYPE_LABELS } from '$lib/types/payroll';
	import { PROVINCE_LABELS } from '$lib/types/employee';
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
	import {
		getPayrollRunByPayDate,
		approvePayrollRun,
		getPayGroupsForPayDate,
		getPayGroupsWithEmployeesForPayDate,
		startPayrollRun,
		type BeforeRunData,
		type EmployeeHoursInput,
		type EmployeeForPayroll
	} from '$lib/services/payrollService';
	import { getDefaultRegularHours } from '$lib/types/payroll';
	import {
		getUnassignedEmployees,
		assignEmployeesToPayGroup
	} from '$lib/services/employeeService';

	// ===========================================
	// Route Params
	// ===========================================
	const payDate = $derived($page.params.payDate ?? '');

	// ===========================================
	// State
	// ===========================================
	let payrollRun = $state<PayrollRunWithGroups | null>(null);
	let payDateInfo = $state<UpcomingPayDate | null>(null);
	let beforeRunData = $state<BeforeRunData | null>(null);
	let isLoading = $state(true);
	let isStartingRun = $state(false);
	let error = $state<string | null>(null);
	let expandedRecordId = $state<string | null>(null);
	let showHolidayModal = $state(false);
	let showLeaveModal = $state(false);
	let showOvertimeModal = $state(false);
	let leaveEntries = $state<LeaveEntry[]>([]);
	let overtimeEntries = $state<OvertimeEntry[]>([]);
	let selectedLeaveEmployee = $state<PayrollRecord | null>(null);
	let selectedOvertimeEmployee = $state<PayrollRecord | null>(null);

	// Add Employees Modal State
	let showAddEmployeesModal = $state(false);
	let selectedPayGroup = $state<PayGroupSummary | null>(null);
	let unassignedEmployees = $state<Employee[]>([]);
	let selectedEmployeeIds = $state<Set<string>>(new Set());
	let isAssigning = $state(false);

	// Hours Input State - tracks hours for each hourly employee
	// Map of employeeId -> { regularHours, overtimeHours }
	let hoursInputMap = $state<Map<string, { regularHours: number; overtimeHours: number }>>(new Map());

	// ===========================================
	// Load Data
	// ===========================================
	async function loadPayrollRun() {
		if (!payDate) return;

		isLoading = true;
		error = null;

		try {
			// First, get pay groups for this date (always needed)
			const payGroupsResult = await getPayGroupsForPayDate(payDate);
			if (payGroupsResult.error) {
				error = payGroupsResult.error;
				return;
			}
			payDateInfo = payGroupsResult.data;

			// Then, try to get the payroll run if it exists
			const result = await getPayrollRunByPayDate(payDate);
			if (result.error) {
				error = result.error;
				return;
			}
			payrollRun = result.data;

			// If no payroll run exists, load employees for the "before run" view
			if (!payrollRun && payDateInfo) {
				const beforeResult = await getPayGroupsWithEmployeesForPayDate(payDate);
				if (beforeResult.error) {
					error = beforeResult.error;
					return;
				}
				beforeRunData = beforeResult.data;

				// Initialize hours input for hourly employees
				if (beforeRunData) {
					const newHoursMap = new Map<string, { regularHours: number; overtimeHours: number }>();
					for (const payGroup of beforeRunData.payGroups) {
						const defaultHours = getDefaultRegularHours(payGroup.payFrequency);
						for (const employee of payGroup.employees) {
							if (employee.compensationType === 'hourly') {
								newHoursMap.set(employee.id, {
									regularHours: defaultHours,
									overtimeHours: 0
								});
							}
						}
					}
					hoursInputMap = newHoursMap;
				}
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load payroll run';
		} finally {
			isLoading = false;
		}
	}

	// Load data when payDate changes
	$effect(() => {
		loadPayrollRun();
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

	// Count of hourly employees and those with missing hours
	const hourlyEmployeesCount = $derived(() => {
		if (!beforeRunData) return 0;
		let count = 0;
		for (const pg of beforeRunData.payGroups) {
			for (const emp of pg.employees) {
				if (emp.compensationType === 'hourly') count++;
			}
		}
		return count;
	});

	// Check if all hourly employees have valid hours input
	const allHourlyEmployeesHaveHours = $derived(() => {
		if (!beforeRunData) return true;
		for (const pg of beforeRunData.payGroups) {
			for (const emp of pg.employees) {
				if (emp.compensationType === 'hourly') {
					const hoursData = hoursInputMap.get(emp.id);
					if (!hoursData || hoursData.regularHours <= 0) {
						return false;
					}
				}
			}
		}
		return true;
	});

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

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}

	function formatCompensation(employee: { annualSalary?: number | null; hourlyRate?: number | null }): string {
		if (employee.annualSalary) {
			return `${formatCurrency(employee.annualSalary)}/yr`;
		} else if (employee.hourlyRate) {
			return `${formatCurrency(employee.hourlyRate)}/hr`;
		}
		return '--';
	}

	function updateHoursInput(employeeId: string, field: 'regularHours' | 'overtimeHours', value: number) {
		const current = hoursInputMap.get(employeeId) || { regularHours: 0, overtimeHours: 0 };
		const updated = { ...current, [field]: value };
		hoursInputMap = new Map(hoursInputMap).set(employeeId, updated);
	}

	function getHoursInput(employeeId: string): { regularHours: number; overtimeHours: number } {
		return hoursInputMap.get(employeeId) || { regularHours: 0, overtimeHours: 0 };
	}

	/**
	 * Calculate estimated gross pay for an employee before payroll run
	 * - Salaried: annual_salary / pay_periods_per_year
	 * - Hourly: hours × hourly_rate
	 */
	function calculateEstimatedGross(
		employee: EmployeeForPayroll,
		payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly'
	): number | null {
		if (employee.compensationType === 'salaried' && employee.annualSalary) {
			const periodsPerYear = payFrequency === 'weekly' ? 52 :
				payFrequency === 'bi_weekly' ? 26 :
				payFrequency === 'semi_monthly' ? 24 : 12;
			return employee.annualSalary / periodsPerYear;
		} else if (employee.compensationType === 'hourly' && employee.hourlyRate) {
			const hoursData = hoursInputMap.get(employee.id);
			if (hoursData && hoursData.regularHours > 0) {
				const regularPay = hoursData.regularHours * employee.hourlyRate;
				const overtimePay = (hoursData.overtimeHours || 0) * employee.hourlyRate * 1.5;
				return regularPay + overtimePay;
			}
			return null; // No hours entered yet
		}
		return null;
	}

	/**
	 * Calculate total estimated gross for a pay group
	 */
	function calculatePayGroupEstimatedGross(
		payGroup: { employees: EmployeeForPayroll[]; payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly' }
	): number | null {
		let total = 0;
		let hasAllData = true;
		for (const emp of payGroup.employees) {
			const gross = calculateEstimatedGross(emp, payGroup.payFrequency);
			if (gross === null) {
				hasAllData = false;
			} else {
				total += gross;
			}
		}
		// Return total if we have at least some data, null if no employees or all null
		return payGroup.employees.length > 0 && total > 0 ? total : (hasAllData ? 0 : null);
	}

	/**
	 * Calculate total estimated gross for all pay groups (for summary cards)
	 */
	const totalEstimatedGross = $derived(() => {
		if (!beforeRunData) return null;
		let total = 0;
		let hasAllData = true;
		for (const pg of beforeRunData.payGroups) {
			const pgGross = calculatePayGroupEstimatedGross(pg);
			if (pgGross === null) {
				hasAllData = false;
			} else {
				total += pgGross;
			}
		}
		return total > 0 ? total : (hasAllData ? 0 : null);
	});

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

	async function handleStartPayrollRun() {
		if (!beforeRunData || isStartingRun) return;

		// Validate that all hourly employees have hours entered
		if (!allHourlyEmployeesHaveHours()) {
			alert('Please enter hours for all hourly employees before starting the payroll run.');
			return;
		}

		isStartingRun = true;
		error = null;

		try {
			// Build hours input array for hourly employees
			const hoursInput: EmployeeHoursInput[] = [];
			for (const pg of beforeRunData.payGroups) {
				for (const emp of pg.employees) {
					if (emp.compensationType === 'hourly') {
						const hoursData = hoursInputMap.get(emp.id);
						if (hoursData) {
							hoursInput.push({
								employeeId: emp.id,
								regularHours: hoursData.regularHours,
								overtimeHours: hoursData.overtimeHours
							});
						}
					}
				}
			}

			const result = await startPayrollRun(payDate, hoursInput);
			if (result.error) {
				error = result.error;
				alert(`Failed to start payroll run: ${result.error}`);
				return;
			}

			// Update local state with the new payroll run
			payrollRun = result.data;
			beforeRunData = null;
		} catch (err) {
			const message = err instanceof Error ? err.message : 'Failed to start payroll run';
			error = message;
			alert(message);
		} finally {
			isStartingRun = false;
		}
	}

	async function handleApprove() {
		if (!payrollRun) return;

		try {
			const result = await approvePayrollRun(payrollRun.id);
			if (result.error) {
				alert(`Failed to approve: ${result.error}`);
				return;
			}

			// Update local state with approved run
			payrollRun = {
				...payrollRun,
				status: 'approved'
			};

			// Update records with paystub status (simulated)
			payrollRun.payGroups = payrollRun.payGroups.map((pg) => ({
				...pg,
				records: pg.records.map((record, index) => ({
					...record,
					paystubStatus: (index === 2 ? 'failed' : 'sent') as PaystubStatus,
					paystubSentAt: index === 2 ? undefined : new Date().toISOString(),
					paystubSentTo: `${record.employeeName.toLowerCase().replace(' ', '.')}@example.com`
				}))
			}));
		} catch (err) {
			alert(`Failed to approve: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
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

	// ===========================================
	// Add Employees Modal
	// ===========================================
	async function openAddEmployeesModal(payGroup: PayGroupSummary) {
		selectedPayGroup = payGroup;
		selectedEmployeeIds = new Set();

		// Load unassigned employees
		try {
			const result = await getUnassignedEmployees();
			if (result.error) {
				alert(`Failed to load employees: ${result.error}`);
				return;
			}
			unassignedEmployees = result.data;
			showAddEmployeesModal = true;
		} catch (err) {
			alert(`Failed to load employees: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	function closeAddEmployeesModal() {
		showAddEmployeesModal = false;
		selectedPayGroup = null;
		selectedEmployeeIds = new Set();
	}

	function toggleEmployeeSelect(id: string) {
		const newSet = new Set(selectedEmployeeIds);
		if (newSet.has(id)) {
			newSet.delete(id);
		} else {
			newSet.add(id);
		}
		selectedEmployeeIds = newSet;
	}

	function toggleSelectAllEmployees() {
		if (selectedEmployeeIds.size === unassignedEmployees.length) {
			selectedEmployeeIds = new Set();
		} else {
			selectedEmployeeIds = new Set(unassignedEmployees.map((e) => e.id));
		}
	}

	async function handleAssignEmployees() {
		if (!selectedPayGroup || selectedEmployeeIds.size === 0) return;

		isAssigning = true;
		try {
			const result = await assignEmployeesToPayGroup(Array.from(selectedEmployeeIds), selectedPayGroup.id);
			if (result.error) {
				alert(`Failed to assign employees: ${result.error}`);
				return;
			}

			closeAddEmployeesModal();
			// Reload data to reflect changes
			await loadPayrollRun();
		} catch (err) {
			alert(`Failed to assign employees: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			isAssigning = false;
		}
	}
</script>

<svelte:head>
	<title>Payroll Run - {payDate} - BeanFlow Payroll</title>
</svelte:head>

{#if isLoading}
	<!-- Loading State -->
	<div class="loading-state">
		<div class="loading-spinner"></div>
		<p>Loading payroll run...</p>
	</div>
{:else if error}
	<!-- Error State -->
	<div class="error-state">
		<div class="error-icon">
			<i class="fas fa-exclamation-triangle"></i>
		</div>
		<h2>Error Loading Payroll Run</h2>
		<p>{error}</p>
		<button class="btn-primary" onclick={() => loadPayrollRun()}>
			<i class="fas fa-redo"></i>
			<span>Try Again</span>
		</button>
	</div>
{:else if !payrollRun && !payDateInfo}
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
{:else if !payrollRun && beforeRunData}
	<!-- No payroll run yet - show full UI with placeholder data -->
	<div class="payroll-run-page">
		<!-- Header -->
		<header class="page-header">
			<button class="back-btn" onclick={handleBack}>
				<i class="fas fa-arrow-left"></i>
				<span>Back to Payroll</span>
			</button>

			<div class="header-content">
				<div class="header-main">
					<h1 class="page-title">Pay Date: {formatDate(beforeRunData.payDate)}</h1>
					<p class="page-subtitle">
						{beforeRunData.payGroups.length} Pay Group{beforeRunData.payGroups.length > 1 ? 's' : ''}
						&middot;
						{beforeRunData.totalEmployees} Employee{beforeRunData.totalEmployees > 1 ? 's' : ''}
					</p>
				</div>
				<div class="header-actions">
					<StatusBadge status="Not Started" variant="pill" />
					<button
						class="btn-primary"
						onclick={handleStartPayrollRun}
						disabled={isStartingRun || beforeRunData.totalEmployees === 0 || (hourlyEmployeesCount() > 0 && !allHourlyEmployeesHaveHours())}
					>
						{#if isStartingRun}
							<i class="fas fa-spinner fa-spin"></i>
							<span>Starting...</span>
						{:else}
							<i class="fas fa-play"></i>
							<span>Start Payroll Run</span>
						{/if}
					</button>
				</div>
			</div>
		</header>

		<!-- Holiday Alert -->
		{#if beforeRunData.holidays && beforeRunData.holidays.length > 0}
			<HolidayAlert holidays={beforeRunData.holidays} onManageHolidayHours={openHolidayModal} />
		{/if}

		<!-- Summary Cards - Show estimated values where available -->
		<div class="summary-cards-placeholder">
			<div class="summary-card">
				<div class="summary-label">Est. Gross</div>
				{#if totalEstimatedGross() !== null}
					<div class="summary-value estimated">{formatCurrency(totalEstimatedGross()!)}</div>
				{:else}
					<div class="summary-value placeholder">--</div>
				{/if}
			</div>
			<div class="summary-card">
				<div class="summary-label">Deductions</div>
				<div class="summary-value placeholder deduction">--</div>
			</div>
			<div class="summary-card highlight">
				<div class="summary-label">Net Pay</div>
				<div class="summary-value placeholder">--</div>
			</div>
			<div class="summary-card">
				<div class="summary-label">Employees</div>
				<div class="summary-value">{beforeRunData.totalEmployees}</div>
			</div>
		</div>

		<!-- Employer Costs - Placeholder -->
		<div class="employer-costs-placeholder">
			<div class="employer-cost-card">
				<div class="cost-label">Employer CPP</div>
				<div class="cost-value placeholder">--</div>
			</div>
			<div class="employer-cost-card">
				<div class="cost-label">Employer EI</div>
				<div class="cost-value placeholder">--</div>
			</div>
			<div class="employer-cost-card highlight">
				<div class="cost-label">Total Employer Cost</div>
				<div class="cost-value placeholder">--</div>
			</div>
		</div>

		<!-- Pay Group Sections with Employee List -->
		<div class="pay-groups-container">
			{#each beforeRunData.payGroups as payGroup (payGroup.id)}
				{@const pgEstimatedGross = calculatePayGroupEstimatedGross(payGroup)}
				<div class="pay-group-section">
					<!-- Section Header -->
					<div class="section-header-static">
						<div class="header-left">
							<div class="group-badge">
								<i class="fas fa-tag"></i>
							</div>
							<div class="group-info">
								<h3 class="group-name">{payGroup.name}</h3>
								<div class="group-meta">
									<span class="meta-item">
										{PAY_FREQUENCY_LABELS[payGroup.payFrequency] || payGroup.payFrequency}
									</span>
									<span class="meta-divider"></span>
									<span class="meta-item">
										{EMPLOYMENT_TYPE_LABELS[payGroup.employmentType] || payGroup.employmentType}
									</span>
									<span class="meta-divider"></span>
									<span class="meta-item">
										{formatDateRange(payGroup.periodStart, payGroup.periodEnd)}
									</span>
								</div>
							</div>
						</div>
						<div class="header-right">
							<div class="header-stats">
								<div class="stat">
									<span class="stat-value">{payGroup.employees.length}</span>
									<span class="stat-label">Employees</span>
								</div>
								<div class="stat">
									{#if pgEstimatedGross !== null}
										<span class="stat-value estimated">{formatCurrency(pgEstimatedGross)}</span>
									{:else}
										<span class="stat-value placeholder">--</span>
									{/if}
									<span class="stat-label">Est. Gross</span>
								</div>
								<div class="stat">
									<span class="stat-value placeholder">--</span>
									<span class="stat-label">Net Pay</span>
								</div>
							</div>
							<button
								class="btn-add-more-header"
								onclick={() => openAddEmployeesModal({
									id: payGroup.id,
									name: payGroup.name,
									payFrequency: payGroup.payFrequency,
									employmentType: payGroup.employmentType,
									employeeCount: payGroup.employees.length,
									estimatedGross: 0,
									periodStart: payGroup.periodStart,
									periodEnd: payGroup.periodEnd
								})}
							>
								<i class="fas fa-user-plus"></i>
								<span>Add</span>
							</button>
						</div>
					</div>

					<!-- Employee Table -->
					<div class="section-content">
						{#if payGroup.employees.length === 0}
							<div class="empty-employees">
								<i class="fas fa-user-plus"></i>
								<span>No employees assigned to this pay group</span>
								<button class="btn-add-employees" onclick={() => openAddEmployeesModal({
									id: payGroup.id,
									name: payGroup.name,
									payFrequency: payGroup.payFrequency,
									employmentType: payGroup.employmentType,
									employeeCount: 0,
									estimatedGross: 0,
									periodStart: payGroup.periodStart,
									periodEnd: payGroup.periodEnd
								})}>
									<i class="fas fa-plus"></i>
									Add Employees
								</button>
							</div>
						{:else}
							<table class="records-table">
								<thead>
									<tr>
										<th class="col-employee">Employee</th>
										<th class="col-type">Type</th>
										<th class="col-rate">Rate/Salary</th>
										<th class="col-hours">Hours</th>
										<th class="col-gross">Gross</th>
										<th class="col-deductions">Deductions</th>
										<th class="col-net">Net Pay</th>
										<th class="col-actions"></th>
									</tr>
								</thead>
								<tbody>
									{#each payGroup.employees as employee (employee.id)}
										{@const hoursData = getHoursInput(employee.id)}
										{@const estimatedGross = calculateEstimatedGross(employee, payGroup.payFrequency)}
										<tr>
											<td class="col-employee">
												<div class="employee-info">
													<span class="employee-name">{employee.firstName} {employee.lastName}</span>
												</div>
											</td>
											<td class="col-type">
												<span class="type-badge {employee.compensationType}">
													{employee.compensationType === 'salaried' ? 'Salary' : 'Hourly'}
												</span>
											</td>
											<td class="col-rate">
												<span class="rate-value">{formatCompensation(employee)}</span>
											</td>
											<td class="col-hours">
												{#if employee.compensationType === 'hourly'}
													<div class="hours-input-group">
														<input
															type="number"
															class="hours-input"
															min="0"
															max="200"
															step="0.5"
															value={hoursData.regularHours}
															onchange={(e) => updateHoursInput(employee.id, 'regularHours', parseFloat((e.target as HTMLInputElement).value) || 0)}
															placeholder="Hrs"
														/>
													</div>
												{:else}
													<span class="no-hours">-</span>
												{/if}
											</td>
											<td class="col-gross">
												{#if estimatedGross !== null}
													<span class="estimated-gross">{formatCurrency(estimatedGross)}</span>
												{:else}
													<span class="placeholder-cell">--</span>
												{/if}
											</td>
											<td class="col-deductions placeholder-cell">--</td>
											<td class="col-net">
												<span class="net-pay placeholder-cell">--</span>
											</td>
											<td class="col-actions"></td>
										</tr>
									{/each}
								</tbody>
							</table>
						{/if}
					</div>
				</div>
			{/each}
		</div>

		<!-- Info/Warning Message -->
		{#if hourlyEmployeesCount() > 0 && !allHourlyEmployeesHaveHours()}
			<div class="warning-message">
				<i class="fas fa-exclamation-triangle"></i>
				<span>Enter hours for all hourly employees before starting the payroll run.</span>
			</div>
		{:else}
			<div class="info-message">
				<i class="fas fa-info-circle"></i>
				<span>Click "Start Payroll Run" to calculate gross pay, deductions, and net pay for all employees.</span>
			</div>
		{/if}
	</div>
{:else if payrollRun}
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

<!-- Add Employees Modal (shared between setup and run views) -->
{#if showAddEmployeesModal && selectedPayGroup}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div class="modal-overlay" onclick={closeAddEmployeesModal}>
		<div class="modal-content" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h3>Add Employees to {selectedPayGroup.name}</h3>
				<button class="btn-close" onclick={closeAddEmployeesModal}>
					<i class="fas fa-times"></i>
				</button>
			</div>

			<div class="modal-body">
				{#if unassignedEmployees.length === 0}
					<div class="modal-empty">
						<i class="fas fa-info-circle"></i>
						<p>No unassigned employees available.</p>
						<p class="hint">All employees are already assigned to a pay group, or you need to add employees first.</p>
						<a href="/employees" class="btn-go-employees">
							<i class="fas fa-arrow-right"></i>
							Go to Employees
						</a>
					</div>
				{:else}
					<div class="select-all-row">
						<label class="checkbox-label">
							<input
								type="checkbox"
								checked={selectedEmployeeIds.size === unassignedEmployees.length}
								onchange={toggleSelectAllEmployees}
							/>
							<span>Select All ({unassignedEmployees.length})</span>
						</label>
					</div>

					<div class="employees-list">
						{#each unassignedEmployees as employee (employee.id)}
							<label class="employee-row">
								<input
									type="checkbox"
									checked={selectedEmployeeIds.has(employee.id)}
									onchange={() => toggleEmployeeSelect(employee.id)}
								/>
								<div class="employee-info">
									<span class="name">{employee.firstName} {employee.lastName}</span>
									<span class="details">
										{PROVINCE_LABELS[employee.provinceOfEmployment]} · {formatCompensation(employee)}
									</span>
								</div>
							</label>
						{/each}
					</div>
				{/if}
			</div>

			{#if unassignedEmployees.length > 0}
				<div class="modal-footer">
					<button class="btn-cancel" onclick={closeAddEmployeesModal}>Cancel</button>
					<button
						class="btn-assign"
						onclick={handleAssignEmployees}
						disabled={selectedEmployeeIds.size === 0 || isAssigning}
					>
						{#if isAssigning}
							<i class="fas fa-spinner fa-spin"></i>
							Assigning...
						{:else}
							<i class="fas fa-check"></i>
							Add {selectedEmployeeIds.size} Employee{selectedEmployeeIds.size !== 1 ? 's' : ''}
						{/if}
					</button>
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	.payroll-run-page {
		max-width: 1200px;
	}

	/* Loading State */
	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
	}

	.loading-spinner {
		width: 48px;
		height: 48px;
		border: 4px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: var(--spacing-4);
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	/* Error State */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 400px;
		text-align: center;
	}

	.error-icon {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		background: var(--color-error-100);
		color: var(--color-error-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 32px;
		margin-bottom: var(--spacing-4);
	}

	.error-state h2 {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.error-state p {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-6);
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

	/* Setup Page (when no payroll run exists) */
	.payroll-setup-page {
		max-width: 1200px;
	}

	.pay-groups-setup {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-6);
	}

	.pay-group-setup-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-5);
		transition: var(--transition-fast);
	}

	.pay-group-setup-card.no-employees {
		border: 2px dashed var(--color-warning-300);
		background: var(--color-warning-50);
	}

	.setup-card-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: var(--spacing-4);
	}

	.setup-card-title {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2);
	}

	.setup-card-badges {
		display: flex;
		gap: var(--spacing-2);
	}

	.badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		color: var(--color-surface-600);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.setup-card-stats {
		text-align: right;
	}

	.stat-value {
		display: block;
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-800);
	}

	.stat-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.setup-card-empty,
	.setup-card-ready {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4);
		border-radius: var(--radius-lg);
		gap: var(--spacing-3);
	}

	.setup-card-empty {
		background: var(--color-warning-100);
	}

	.setup-card-ready {
		background: var(--color-success-50);
	}

	.empty-message,
	.ready-message {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
	}

	.empty-message {
		color: var(--color-warning-700);
	}

	.ready-message {
		color: var(--color-success-700);
	}

	.btn-add-employees {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		white-space: nowrap;
	}

	.btn-add-employees:hover {
		background: var(--color-primary-600);
	}

	.btn-add-more {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: transparent;
		color: var(--color-success-700);
		border: 1px solid var(--color-success-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
		white-space: nowrap;
	}

	.btn-add-more:hover {
		background: var(--color-success-100);
	}

	.setup-actions {
		display: flex;
		justify-content: center;
	}

	.btn-large {
		padding: var(--spacing-4) var(--spacing-8);
		font-size: var(--font-size-title-small);
	}

	/* Modal Styles */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-4);
	}

	.modal-content {
		background: white;
		border-radius: var(--radius-xl);
		width: 100%;
		max-width: 500px;
		max-height: 80vh;
		display: flex;
		flex-direction: column;
		box-shadow: var(--shadow-md3-3);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-header h3 {
		margin: 0;
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.btn-close {
		width: 32px;
		height: 32px;
		border-radius: var(--radius-md);
		background: transparent;
		border: none;
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-close:hover {
		background: var(--color-surface-100);
	}

	.modal-body {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-4) var(--spacing-5);
	}

	.modal-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		padding: var(--spacing-6);
	}

	.modal-empty i {
		font-size: 32px;
		color: var(--color-surface-400);
		margin-bottom: var(--spacing-4);
	}

	.modal-empty p {
		color: var(--color-surface-600);
		margin: 0;
	}

	.modal-empty .hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-top: var(--spacing-2);
	}

	.btn-go-employees {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-top: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border-radius: var(--radius-md);
		text-decoration: none;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		transition: var(--transition-fast);
	}

	.btn-go-employees:hover {
		background: var(--color-primary-600);
	}

	.select-all-row {
		padding-bottom: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-100);
		margin-bottom: var(--spacing-3);
	}

	.employees-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.employee-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.employee-row:hover {
		background: var(--color-surface-50);
	}

	.employee-row input[type='checkbox'] {
		width: 18px;
		height: 18px;
		accent-color: var(--color-primary-500);
	}

	.employee-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.employee-info .name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-info .details {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		cursor: pointer;
	}

	.checkbox-label span {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-5);
		border-top: 1px solid var(--color-surface-100);
	}

	.btn-cancel {
		padding: var(--spacing-2) var(--spacing-4);
		background: transparent;
		color: var(--color-surface-600);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-cancel:hover {
		background: var(--color-surface-100);
	}

	.btn-assign {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-assign:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-assign:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 640px) {
		.pay-groups-setup {
			grid-template-columns: 1fr;
		}

		.setup-card-empty,
		.setup-card-ready {
			flex-direction: column;
			text-align: center;
		}
	}

	/* Before Run View - Placeholder Styles */
	.summary-cards-placeholder {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-4);
	}

	.summary-card {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-5);
		box-shadow: var(--shadow-md3-1);
	}

	.summary-card.highlight {
		background: var(--color-primary-600);
		color: white;
	}

	.summary-label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin-bottom: var(--spacing-2);
	}

	.summary-card.highlight .summary-label {
		color: rgba(255, 255, 255, 0.8);
	}

	.summary-value {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-800);
	}

	.summary-card.highlight .summary-value {
		color: white;
	}

	.summary-value.placeholder {
		color: var(--color-surface-400);
	}

	.summary-value.deduction {
		color: var(--color-error-500);
	}

	.employer-costs-placeholder {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-6);
	}

	.employer-cost-card {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-4);
		box-shadow: var(--shadow-md3-1);
	}

	.employer-cost-card.highlight {
		background: var(--color-surface-800);
		color: white;
	}

	.cost-label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin-bottom: var(--spacing-1);
	}

	.employer-cost-card.highlight .cost-label {
		color: rgba(255, 255, 255, 0.7);
	}

	.cost-value {
		font-size: var(--font-size-title-small);
		font-weight: var(--font-weight-bold);
		color: var(--color-surface-800);
	}

	.employer-cost-card.highlight .cost-value {
		color: white;
	}

	.cost-value.placeholder {
		color: var(--color-surface-400);
	}

	/* Pay Group Section for Before Run */
	.pay-group-section {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
		margin-bottom: var(--spacing-4);
	}

	.section-header-static {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-surface-50);
	}

	.section-header-static .header-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.section-header-static .group-badge {
		width: 36px;
		height: 36px;
		border-radius: var(--radius-md);
		background: var(--color-primary-100);
		color: var(--color-primary-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
	}

	.section-header-static .group-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.section-header-static .group-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.section-header-static .group-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.section-header-static .meta-item {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.section-header-static .meta-divider {
		width: 4px;
		height: 4px;
		border-radius: 50%;
		background: var(--color-surface-300);
	}

	.section-header-static .header-right {
		display: flex;
		align-items: center;
	}

	.section-header-static .header-stats {
		display: flex;
		gap: var(--spacing-6);
	}

	.section-header-static .stat {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}

	.section-header-static .stat-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.section-header-static .stat-value.placeholder {
		color: var(--color-surface-400);
	}

	.section-header-static .stat-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.btn-add-more-header {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-left: var(--spacing-4);
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-primary-50);
		color: var(--color-primary-600);
		border: 1px solid var(--color-primary-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add-more-header:hover {
		background: var(--color-primary-100);
		border-color: var(--color-primary-300);
	}

	.btn-add-more-header i {
		font-size: 12px;
	}

	.section-content {
		border-top: 1px solid var(--color-surface-200);
	}

	.empty-employees {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-8);
		gap: var(--spacing-3);
		color: var(--color-surface-500);
	}

	.empty-employees i {
		font-size: 32px;
	}

	/* Records Table for Before Run */
	.records-table {
		width: 100%;
		border-collapse: collapse;
	}

	.records-table th {
		text-align: left;
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.records-table td {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.records-table tbody tr:last-child td {
		border-bottom: none;
	}

	.col-employee {
		width: 22%;
	}

	.col-province {
		width: 8%;
	}

	.col-gross,
	.col-deductions,
	.col-net {
		width: 13%;
		text-align: right;
	}

	.col-leave {
		width: 10%;
	}

	.col-overtime {
		width: 10%;
	}

	.col-actions {
		width: 8%;
		text-align: right;
	}

	.records-table th.col-type,
	.records-table th.col-hours {
		text-align: center;
	}

	.records-table th.col-rate,
	.records-table th.col-gross,
	.records-table th.col-deductions,
	.records-table th.col-net,
	.records-table th.col-actions {
		text-align: right;
	}

	.employee-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.province-badge {
		display: inline-flex;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.net-pay {
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.no-leave,
	.no-overtime {
		color: var(--color-surface-400);
	}

	.placeholder-cell {
		color: var(--color-surface-400);
		text-align: right;
	}

	/* Info Message */
	.info-message {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-primary-50);
		border-radius: var(--radius-lg);
		color: var(--color-primary-700);
		font-size: var(--font-size-body-content);
		margin-top: var(--spacing-6);
	}

	.info-message i {
		font-size: 18px;
	}

	/* Warning Message */
	.warning-message {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-warning-50);
		border-radius: var(--radius-lg);
		color: var(--color-warning-700);
		font-size: var(--font-size-body-content);
		margin-top: var(--spacing-6);
		border: 1px solid var(--color-warning-200);
	}

	.warning-message i {
		font-size: 18px;
		color: var(--color-warning-500);
	}

	/* Type Badge */
	.type-badge {
		display: inline-flex;
		align-items: center;
		padding: 2px 8px;
		border-radius: var(--radius-full);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
	}

	.type-badge.salaried {
		background: var(--color-primary-50);
		color: var(--color-primary-700);
	}

	.type-badge.hourly {
		background: var(--color-success-50);
		color: var(--color-success-700);
	}

	/* Rate Value */
	.rate-value {
		font-family: var(--font-mono);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	/* Hours Input */
	.hours-input-group {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.hours-input {
		width: 70px;
		padding: var(--spacing-2) var(--spacing-3);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-family: var(--font-mono);
		text-align: center;
		transition: var(--transition-fast);
	}

	.hours-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.hours-input::-webkit-inner-spin-button,
	.hours-input::-webkit-outer-spin-button {
		opacity: 1;
	}

	.no-hours {
		color: var(--color-surface-400);
	}

	/* Estimated Gross */
	.estimated-gross {
		font-family: var(--font-mono);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	/* Estimated values (summary cards and stats) */
	.summary-value.estimated,
	.stat-value.estimated {
		color: var(--color-primary-600);
		font-weight: var(--font-weight-semibold);
	}

	/* Column widths for before run table */
	.col-type {
		width: 80px;
		text-align: center;
	}

	.col-rate {
		width: 120px;
		text-align: right;
	}

	.col-hours {
		width: 90px;
		text-align: center;
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	@media (max-width: 1024px) {
		.summary-cards-placeholder {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (max-width: 768px) {
		.summary-cards-placeholder {
			grid-template-columns: 1fr;
		}

		.employer-costs-placeholder {
			grid-template-columns: 1fr;
		}

		.section-header-static {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-3);
		}

		.section-header-static .header-right {
			width: 100%;
		}

		.section-header-static .header-stats {
			width: 100%;
			justify-content: space-between;
		}

		.section-header-static .stat {
			align-items: flex-start;
		}
	}
</style>
