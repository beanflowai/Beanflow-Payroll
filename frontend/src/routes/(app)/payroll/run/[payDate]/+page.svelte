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
		PayGroupSummary,
		EmployeePayrollInput,
		EarningsBreakdown
	} from '$lib/types/payroll';
	import type { Employee } from '$lib/types/employee';
	import {
		PAYROLL_STATUS_LABELS,
		LEAVE_TYPE_LABELS,
		ADJUSTMENT_TYPE_LABELS,
		createDefaultPayrollInput
	} from '$lib/types/payroll';
	import { StatusBadge } from '$lib/components/shared';
	import {
		PayGroupSection,
		PayrollSummaryCards,
		HolidayAlert,
		HolidayWorkModal,
		LeaveAlert,
		LeaveModal,
		OvertimeModal,
		BeforeRunPayGroupSection,
		AddEmployeesModal,
		BeforeRunSummaryCards,
		BeforeRunEmployerCosts,
		PayrollLoadingState,
		PayrollErrorState,
		PayrollNotFound,
		PayrollPageHeader,
		PayrollInfoMessage
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
	let isAssigning = $state(false);

	// Payroll Input State - tracks all payroll input data for each employee
	let payrollInputMap = $state<Map<string, EmployeePayrollInput>>(new Map());

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

				// Initialize payroll input for all employees
				if (beforeRunData) {
					const newInputMap = new Map<string, EmployeePayrollInput>();
					for (const payGroup of beforeRunData.payGroups) {
						const defaultHours = getDefaultRegularHours(payGroup.payFrequency);
						for (const employee of payGroup.employees) {
							const input = createDefaultPayrollInput(
								employee.id,
								employee.compensationType === 'hourly' ? defaultHours : 0
							);
							newInputMap.set(employee.id, input);
						}
					}
					payrollInputMap = newInputMap;
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
					const input = payrollInputMap.get(emp.id);
					if (!input || input.regularHours <= 0) {
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

	function getPayrollInput(employeeId: string): EmployeePayrollInput {
		return payrollInputMap.get(employeeId) || createDefaultPayrollInput(employeeId);
	}

	function updatePayrollInput(employeeId: string, updates: Partial<EmployeePayrollInput>) {
		const current = getPayrollInput(employeeId);
		payrollInputMap = new Map(payrollInputMap).set(employeeId, { ...current, ...updates });
	}

	function calculateEstimatedGross(
		employee: EmployeeForPayroll,
		payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly'
	): number | null {
		const input = payrollInputMap.get(employee.id);

		// Salaried employees
		if (employee.compensationType === 'salaried' && employee.annualSalary) {
			const periodsPerYear = payFrequency === 'weekly' ? 52 :
				payFrequency === 'bi_weekly' ? 26 :
				payFrequency === 'semi_monthly' ? 24 : 12;
			let gross = employee.annualSalary / periodsPerYear;

			if (input?.overrides?.regularPay !== undefined) {
				gross = input.overrides.regularPay;
			}

			if (input?.adjustments) {
				for (const adj of input.adjustments) {
					if (adj.type === 'deduction') {
						gross -= adj.amount;
					} else {
						gross += adj.amount;
					}
				}
			}

			return gross;
		}

		// Hourly employees
		if (employee.compensationType === 'hourly' && employee.hourlyRate) {
			if (!input || input.regularHours <= 0) {
				return null;
			}

			const hourlyRate = employee.hourlyRate;
			let regularPay = input.regularHours * hourlyRate;
			if (input.overrides?.regularPay !== undefined) {
				regularPay = input.overrides.regularPay;
			}

			let overtimePay = (input.overtimeHours || 0) * hourlyRate * 1.5;
			if (input.overrides?.overtimePay !== undefined) {
				overtimePay = input.overrides.overtimePay;
			}

			let leavePay = 0;
			if (input.leaveEntries) {
				for (const leave of input.leaveEntries) {
					leavePay += leave.hours * hourlyRate;
				}
			}

			let holidayPay = 0;
			if (input.holidayWorkEntries) {
				for (const hw of input.holidayWorkEntries) {
					holidayPay += hw.hoursWorked * hourlyRate * 1.5;
				}
			}
			if (input.overrides?.holidayPay !== undefined) {
				holidayPay = input.overrides.holidayPay;
			}

			let adjustmentTotal = 0;
			if (input.adjustments) {
				for (const adj of input.adjustments) {
					if (adj.type === 'deduction') {
						adjustmentTotal -= adj.amount;
					} else {
						adjustmentTotal += adj.amount;
					}
				}
			}

			return regularPay + overtimePay + leavePay + holidayPay + adjustmentTotal;
		}

		return null;
	}

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
		return payGroup.employees.length > 0 && total > 0 ? total : (hasAllData ? 0 : null);
	}

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

	function getEarningsBreakdown(
		employee: EmployeeForPayroll,
		payFrequency: 'weekly' | 'bi_weekly' | 'semi_monthly' | 'monthly'
	): EarningsBreakdown[] {
		const input = payrollInputMap.get(employee.id);
		const breakdown: EarningsBreakdown[] = [];

		// Salaried employees
		if (employee.compensationType === 'salaried' && employee.annualSalary) {
			const periodsPerYear = payFrequency === 'weekly' ? 52 :
				payFrequency === 'bi_weekly' ? 26 :
				payFrequency === 'semi_monthly' ? 24 : 12;
			const defaultRegularPay = employee.annualSalary / periodsPerYear;
			const regularPay = input?.overrides?.regularPay ?? defaultRegularPay;
			breakdown.push({
				key: 'regular_pay',
				label: 'Regular Pay',
				amount: regularPay,
				detail: `${formatCurrency(employee.annualSalary)}/yr / ${periodsPerYear}`,
				editable: true,
				editType: 'amount',
				editValue: regularPay
			});

			const overtimeHours = input?.overtimeHours || 0;
			const impliedHourlyRate = employee.annualSalary / (periodsPerYear * (payFrequency === 'weekly' ? 40 : payFrequency === 'bi_weekly' ? 80 : payFrequency === 'semi_monthly' ? 86.67 : 173.33));
			const overtimePay = overtimeHours * impliedHourlyRate * 1.5;
			breakdown.push({
				key: 'overtime',
				label: 'Overtime',
				amount: overtimePay,
				detail: overtimeHours > 0 ? `${overtimeHours}h @ ${formatCurrency(impliedHourlyRate * 1.5)}` : undefined,
				editable: true,
				editType: 'hours',
				editValue: overtimeHours
			});
		}
		// Hourly employees
		else if (employee.compensationType === 'hourly' && employee.hourlyRate && input) {
			const hourlyRate = employee.hourlyRate;

			if (input.regularHours > 0) {
				const regularPay = input.overrides?.regularPay ?? (input.regularHours * hourlyRate);
				breakdown.push({
					key: 'regular_pay',
					label: 'Regular Pay',
					amount: regularPay,
					detail: `${input.regularHours}h @ ${formatCurrency(hourlyRate)}`,
					editable: false
				});
			}

			const overtimeHours = input.overtimeHours || 0;
			const overtimePay = input.overrides?.overtimePay ?? (overtimeHours * hourlyRate * 1.5);
			breakdown.push({
				key: 'overtime',
				label: 'Overtime',
				amount: overtimePay,
				detail: overtimeHours > 0 ? `${overtimeHours}h @ ${formatCurrency(hourlyRate * 1.5)}` : undefined,
				editable: true,
				editType: 'hours',
				editValue: overtimeHours
			});

			if (input.leaveEntries && input.leaveEntries.length > 0) {
				for (const leave of input.leaveEntries) {
					const leavePay = leave.hours * hourlyRate;
					const leaveLabel = LEAVE_TYPE_LABELS[leave.type];
					breakdown.push({
						key: `leave_${leave.type}`,
						label: `${leaveLabel.icon} ${leaveLabel.full}`,
						amount: leavePay,
						detail: `${leave.hours}h @ ${formatCurrency(hourlyRate)}`,
						editable: false
					});
				}
			}

			if (input.holidayWorkEntries && input.holidayWorkEntries.length > 0) {
				for (const hw of input.holidayWorkEntries) {
					const holidayPay = hw.hoursWorked * hourlyRate * 1.5;
					breakdown.push({
						key: `holiday_${hw.holidayDate}`,
						label: `Holiday: ${hw.holidayName}`,
						amount: holidayPay,
						detail: `${hw.hoursWorked}h @ ${formatCurrency(hourlyRate * 1.5)}`,
						editable: false
					});
				}
			}
		}

		// Adjustments
		if (input?.adjustments) {
			for (const adj of input.adjustments) {
				const adjLabel = ADJUSTMENT_TYPE_LABELS[adj.type];
				breakdown.push({
					key: `adj_${adj.id}`,
					label: `${adjLabel.icon} ${adj.description || adjLabel.label}`,
					amount: adj.type === 'deduction' ? -adj.amount : adj.amount,
					editable: false
				});
			}
		}

		return breakdown;
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

	async function handleStartPayrollRun() {
		if (!beforeRunData || isStartingRun) return;

		if (!allHourlyEmployeesHaveHours()) {
			alert('Please enter hours for all hourly employees before starting the payroll run.');
			return;
		}

		isStartingRun = true;
		error = null;

		try {
			const hoursInput: EmployeeHoursInput[] = [];
			for (const pg of beforeRunData.payGroups) {
				for (const emp of pg.employees) {
					if (emp.compensationType === 'hourly') {
						const input = payrollInputMap.get(emp.id);
						if (input) {
							hoursInput.push({
								employeeId: emp.id,
								regularHours: input.regularHours,
								overtimeHours: input.overtimeHours
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

			payrollRun = {
				...payrollRun,
				status: 'approved'
			};

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
	}

	async function handleAssignEmployeesFromModal(employeeIds: string[]) {
		if (!selectedPayGroup || employeeIds.length === 0) return;

		isAssigning = true;
		try {
			const result = await assignEmployeesToPayGroup(employeeIds, selectedPayGroup.id);
			if (result.error) {
				alert(`Failed to assign employees: ${result.error}`);
				return;
			}

			closeAddEmployeesModal();
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
	<PayrollLoadingState />
{:else if error}
	<PayrollErrorState {error} onRetry={loadPayrollRun} />
{:else if !payrollRun && !payDateInfo}
	<PayrollNotFound payDateFormatted={formatDate(payDate)} onBack={handleBack} />
{:else if !payrollRun && beforeRunData}
	<!-- Before Run View -->
	<div class="max-w-[1200px]">
		<PayrollPageHeader
			payDateFormatted={formatDate(beforeRunData.payDate)}
			payGroupCount={beforeRunData.payGroups.length}
			employeeCount={beforeRunData.totalEmployees}
			onBack={handleBack}
		>
			{#snippet actions()}
				<StatusBadge status="Not Started" variant="pill" />
				<button
					class="flex items-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-all duration-150 hover:opacity-90 hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
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
			{/snippet}
		</PayrollPageHeader>

		<!-- Holiday Alert -->
		{#if beforeRunData.holidays && beforeRunData.holidays.length > 0}
			<HolidayAlert holidays={beforeRunData.holidays} onManageHolidayHours={openHolidayModal} />
		{/if}

		<!-- Summary Cards -->
		<BeforeRunSummaryCards
			estimatedGross={totalEstimatedGross()}
			totalEmployees={beforeRunData.totalEmployees}
		/>

		<!-- Employer Costs -->
		<BeforeRunEmployerCosts />

		<!-- Pay Group Sections -->
		<div class="flex flex-col gap-4">
			{#each beforeRunData.payGroups as payGroup (payGroup.id)}
				{@const pgEstimatedGross = calculatePayGroupEstimatedGross(payGroup)}
				<BeforeRunPayGroupSection
					{payGroup}
					{payrollInputMap}
					{expandedRecordId}
					estimatedGross={pgEstimatedGross}
					onToggleExpand={toggleExpand}
					onAddEmployees={() => openAddEmployeesModal({
						id: payGroup.id,
						name: payGroup.name,
						payFrequency: payGroup.payFrequency,
						employmentType: payGroup.employmentType,
						employeeCount: payGroup.employees.length,
						estimatedGross: 0,
						periodStart: payGroup.periodStart,
						periodEnd: payGroup.periodEnd
					})}
					onUpdatePayrollInput={updatePayrollInput}
					getEarningsBreakdown={(emp) => getEarningsBreakdown(emp, payGroup.payFrequency)}
					calculateEstimatedGross={(emp) => calculateEstimatedGross(emp, payGroup.payFrequency)}
				/>
			{/each}
		</div>

		<!-- Info/Warning Message -->
		{#if hourlyEmployeesCount() > 0 && !allHourlyEmployeesHaveHours()}
			<PayrollInfoMessage
				variant="warning"
				message="Enter hours for all hourly employees before starting the payroll run."
			/>
		{:else}
			<PayrollInfoMessage
				variant="info"
				message="Click &quot;Start Payroll Run&quot; to calculate gross pay, deductions, and net pay for all employees."
			/>
		{/if}
	</div>
{:else if payrollRun}
	<!-- Payroll Run View -->
	<div class="max-w-[1200px]">
		<PayrollPageHeader
			payDateFormatted={formatDate(payrollRun.payDate)}
			payGroupCount={payrollRun.payGroups.length}
			employeeCount={payrollRun.totalEmployees}
			onBack={handleBack}
		>
			{#snippet actions()}
				<StatusBadge status={PAYROLL_STATUS_LABELS[payrollRun.status]} variant="pill" />
				<button class="flex items-center gap-2 py-3 px-5 bg-white text-surface-700 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:bg-surface-50 hover:border-surface-300">
					<i class="fas fa-file-csv"></i>
					<span>Export CSV</span>
				</button>
				{#if isApprovedOrPaid}
					<button
						class="flex items-center gap-2 py-3 px-5 bg-white text-surface-700 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:bg-surface-50 hover:border-surface-300"
						onclick={handleDownloadAllPaystubs}
					>
						<i class="fas fa-file-archive"></i>
						<span>Download All Paystubs</span>
					</button>
					<button
						class="flex items-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-all duration-150 hover:opacity-90 hover:-translate-y-px"
						onclick={handleResendAll}
					>
						<i class="fas fa-paper-plane"></i>
						<span>Resend All</span>
					</button>
				{:else}
					<button
						class="flex items-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-all duration-150 hover:opacity-90 hover:-translate-y-px"
						onclick={handleApprove}
					>
						<i class="fas fa-check"></i>
						<span>Approve & Send Paystubs</span>
					</button>
				{/if}
			{/snippet}
		</PayrollPageHeader>

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
		<div class="flex flex-col gap-4">
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

<!-- Add Employees Modal -->
{#if showAddEmployeesModal && selectedPayGroup}
	<AddEmployeesModal
		payGroup={selectedPayGroup}
		{unassignedEmployees}
		{isAssigning}
		onClose={closeAddEmployeesModal}
		onAssign={handleAssignEmployeesFromModal}
	/>
{/if}
