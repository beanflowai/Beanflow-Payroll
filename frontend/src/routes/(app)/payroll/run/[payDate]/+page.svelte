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
		EmployeePayrollInput
	} from '$lib/types/payroll';
	import type { Employee } from '$lib/types/employee';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import { StatusBadge } from '$lib/components/shared';
	import {
		PayGroupSection,
		PayrollSummaryCards,
		HolidayAlert,
		HolidayWorkModal,
		LeaveAlert,
		LeaveModal,
		OvertimeModal,
		AddEmployeesModal,
		PayrollLoadingState,
		PayrollErrorState,
		PayrollNotFound,
		PayrollPageHeader,
		DraftPayrollView
	} from '$lib/components/payroll';
	import {
		getPayrollRunByPayDate,
		approvePayrollRun,
		getPayGroupsForPayDate,
		createOrGetPayrollRun,
		updatePayrollRecord,
		recalculatePayrollRun,
		finalizePayrollRun,
		revertToDraft,
		checkHasModifiedRecords,
		addEmployeeToRun,
		removeEmployeeFromRun,
		deletePayrollRun
	} from '$lib/services/payroll';
	import {
		getUnassignedEmployees,
		assignEmployeesToPayGroup
	} from '$lib/services/employeeService';
	import { formatFullDate } from '$lib/utils/dateUtils';

	// ===========================================
	// Route Params
	// ===========================================
	const payDate = $derived($page.params.payDate ?? '');

	// ===========================================
	// State
	// ===========================================
	let payrollRun = $state<PayrollRunWithGroups | null>(null);
	let payDateInfo = $state<UpcomingPayDate | null>(null);
	let isLoading = $state(true);
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
	let selectedPayGroupId = $state<string | null>(null);
	let unassignedEmployees = $state<Employee[]>([]);
	let isAssigning = $state(false);

	// Draft State Variables
	let hasModifiedRecords = $state(false);
	let isRecalculating = $state(false);
	let isFinalizing = $state(false);
	let isReverting = $state(false);
	let isDeletingDraft = $state(false);

	// ===========================================
	// Load Data
	// ===========================================
	async function loadPayrollRun() {
		if (!payDate) return;

		isLoading = true;
		error = null;

		try {
			// First, get pay groups for this date (for display info)
			const payGroupsResult = await getPayGroupsForPayDate(payDate);
			if (payGroupsResult.error) {
				error = payGroupsResult.error;
				return;
			}
			payDateInfo = payGroupsResult.data;

			// Use createOrGetPayrollRun - this will either get existing or create new draft
			const result = await createOrGetPayrollRun(payDate);
			if (result.error) {
				error = result.error;
				return;
			}

			payrollRun = result.data;

			// For draft runs: check for modified records
			if (payrollRun && payrollRun.status === 'draft') {
				const modifiedResult = await checkHasModifiedRecords(payrollRun.id);
				if (!modifiedResult.error) {
					hasModifiedRecords = modifiedResult.data ?? false;
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
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
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
	// Add/Remove Employees for Draft
	// ===========================================
	async function handleAddEmployee(payGroupId: string) {
		selectedPayGroupId = payGroupId;

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
		selectedPayGroupId = null;
	}

	async function handleAssignEmployeesFromModal(employeeIds: string[]) {
		if (!payrollRun || !selectedPayGroupId || employeeIds.length === 0) return;

		isAssigning = true;
		try {
			// First assign employees to the pay group
			const assignResult = await assignEmployeesToPayGroup(employeeIds, selectedPayGroupId);
			if (assignResult.error) {
				alert(`Failed to assign employees: ${assignResult.error}`);
				return;
			}

			// Then add each employee to the payroll run
			for (const employeeId of employeeIds) {
				const addResult = await addEmployeeToRun(payrollRun.id, employeeId);
				if (addResult.error) {
					console.warn(`Failed to add employee ${employeeId} to run:`, addResult.error);
				}
			}

			closeAddEmployeesModal();
			await loadPayrollRun();
		} catch (err) {
			alert(`Failed to assign employees: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			isAssigning = false;
		}
	}

	async function handleRemoveEmployee(employeeId: string) {
		if (!payrollRun) return;

		if (!confirm('Are you sure you want to remove this employee from the payroll run?')) {
			return;
		}

		try {
			const result = await removeEmployeeFromRun(payrollRun.id, employeeId);
			if (result.error) {
				alert(`Failed to remove employee: ${result.error}`);
				return;
			}

			// Reload to update the UI
			await loadPayrollRun();
		} catch (err) {
			alert(`Failed to remove employee: ${err instanceof Error ? err.message : 'Unknown error'}`);
		}
	}

	async function handleDeleteDraft() {
		if (!payrollRun) return;

		if (!confirm('Are you sure you want to delete this draft payroll run? This action cannot be undone.')) {
			return;
		}

		isDeletingDraft = true;
		try {
			const result = await deletePayrollRun(payrollRun.id);
			if (result.error) {
				alert(`Failed to delete draft: ${result.error}`);
				return;
			}

			// Navigate back to payroll dashboard
			goto('/payroll');
		} catch (err) {
			alert(`Failed to delete draft: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			isDeletingDraft = false;
		}
	}

	// ===========================================
	// Draft State Handlers
	// ===========================================
	async function handleUpdateDraftRecord(
		recordId: string,
		employeeId: string,
		updates: Partial<EmployeePayrollInput>
	) {
		if (!payrollRun || payrollRun.status !== 'draft') return;

		try {
			const result = await updatePayrollRecord(payrollRun.id, recordId, updates);
			if (result.error) {
				console.error('Failed to update record:', result.error);
				return;
			}
			// Mark that we have modified records
			hasModifiedRecords = true;
		} catch (err) {
			console.error('Failed to update record:', err);
		}
	}

	async function handleRecalculate() {
		if (!payrollRun || payrollRun.status !== 'draft') return;

		isRecalculating = true;
		try {
			const result = await recalculatePayrollRun(payrollRun.id);
			if (result.error) {
				alert(`Failed to recalculate: ${result.error}`);
				return;
			}
			// Update local state with recalculated data
			payrollRun = result.data;
			hasModifiedRecords = false;
		} catch (err) {
			alert(`Failed to recalculate: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			isRecalculating = false;
		}
	}

	async function handleFinalize() {
		if (!payrollRun || payrollRun.status !== 'draft') return;

		if (hasModifiedRecords) {
			alert('Please recalculate before finalizing. There are unsaved changes.');
			return;
		}

		isFinalizing = true;
		try {
			const result = await finalizePayrollRun(payrollRun.id);
			if (result.error) {
				alert(`Failed to finalize: ${result.error}`);
				return;
			}
			// Update local state - status should now be pending_approval
			payrollRun = result.data;
		} catch (err) {
			alert(`Failed to finalize: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			isFinalizing = false;
		}
	}

	async function handleRevertToDraft() {
		if (!payrollRun || payrollRun.status !== 'pending_approval') return;

		isReverting = true;
		try {
			const result = await revertToDraft(payrollRun.id);
			if (result.error) {
				alert(`Failed to revert: ${result.error}`);
				return;
			}
			// Update local state - status should now be draft
			payrollRun = result.data;
			hasModifiedRecords = false;
		} catch (err) {
			alert(`Failed to revert: ${err instanceof Error ? err.message : 'Unknown error'}`);
		} finally {
			isReverting = false;
		}
	}

	// Check if payroll run is in draft state
	const isDraft = $derived(payrollRun?.status === 'draft');
</script>

<svelte:head>
	<title>Payroll Run - {payDate} - BeanFlow Payroll</title>
</svelte:head>

{#if isLoading}
	<PayrollLoadingState />
{:else if error}
	<PayrollErrorState {error} onRetry={loadPayrollRun} />
{:else if !payrollRun && !payDateInfo}
	<PayrollNotFound payDateFormatted={formatFullDate(payDate)} onBack={handleBack} />
{:else if payrollRun && isDraft}
	<!-- Draft View - Editable Payroll Run (includes initial setup) -->
	<div class="max-w-[1200px]">
		<DraftPayrollView
			{payrollRun}
			{hasModifiedRecords}
			{isRecalculating}
			{isFinalizing}
			isDeleting={isDeletingDraft}
			onRecalculate={handleRecalculate}
			onFinalize={handleFinalize}
			onUpdateRecord={handleUpdateDraftRecord}
			onAddEmployee={handleAddEmployee}
			onRemoveEmployee={handleRemoveEmployee}
			onDeleteDraft={handleDeleteDraft}
			onBack={handleBack}
		/>
	</div>
{:else if payrollRun}
	<!-- Payroll Run View (pending_approval, approved, paid) -->
	<div class="max-w-[1200px]">
		<PayrollPageHeader
			payDateFormatted={formatFullDate(payrollRun.payDate)}
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
						class="flex items-center gap-2 py-3 px-5 bg-white text-surface-700 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:bg-surface-50 hover:border-surface-300 disabled:opacity-50 disabled:cursor-not-allowed"
						onclick={handleRevertToDraft}
						disabled={isReverting}
					>
						<i class="fas fa-undo"></i>
						<span>{isReverting ? 'Reverting...' : 'Revert to Draft'}</span>
					</button>
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
{#if showAddEmployeesModal && selectedPayGroupId && payrollRun}
	{@const payGroupData = payrollRun.payGroups.find(pg => pg.payGroupId === selectedPayGroupId)}
	{#if payGroupData}
		<AddEmployeesModal
			payGroup={{
				id: payGroupData.payGroupId,
				name: payGroupData.payGroupName,
				payFrequency: payGroupData.payFrequency,
				employmentType: payGroupData.employmentType,
				employeeCount: payGroupData.totalEmployees,
				estimatedGross: payGroupData.totalGross,
				periodStart: payGroupData.periodStart,
				periodEnd: payGroupData.periodEnd
			}}
			{unassignedEmployees}
			{isAssigning}
			onClose={closeAddEmployeesModal}
			onAssign={handleAssignEmployeesFromModal}
		/>
	{/if}
{/if}
