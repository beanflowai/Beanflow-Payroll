<script lang="ts">
	import type {
		PayrollRunWithGroups,
		PayrollRecord,
		EmployeePayrollInput,
		HolidayWorkEntry,
		CompensationType,
		PayrollDraftFilters
	} from '$lib/types/payroll';
	import { DEFAULT_PAYROLL_DRAFT_FILTERS } from '$lib/types/payroll';
	import { DraftPayGroupSection, HolidayAlert, HolidayWorkModal } from '$lib/components/payroll';
	import { filterPayrollRun, calculateFilterStats } from '$lib/utils/payrollFilterUtils';
	import PayrollDatePicker from './PayDatePicker.svelte';
	import Tooltip from '$lib/components/shared/Tooltip.svelte';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils';
	import PayrollDraftFiltersComponent from './PayrollDraftFilters.svelte';

	interface Props {
		payrollRun: PayrollRunWithGroups;
		hasModifiedRecords: boolean;
		isRecalculating: boolean;
		isFinalizing: boolean;
		isDeleting?: boolean;
		onRecalculate: () => void;
		onAutoCalculate?: (recordId: string) => void;
		onFinalize: () => void;
		onUpdateRecord: (
			recordId: string,
			employeeId: string,
			updates: Partial<EmployeePayrollInput>
		) => void;
		onAddEmployee?: (payGroupId: string) => void;
		onRemoveEmployee?: (employeeId: string) => void;
		onDeleteDraft?: () => void;
		onBack?: () => void;
		onPayDateChange?: (newPayDate: string) => Promise<void>;
		onPreviewPaystub?: (record: PayrollRecord) => void;
	}

	let {
		payrollRun,
		hasModifiedRecords,
		isRecalculating,
		isFinalizing,
		isDeleting = false,
		onRecalculate,
		onAutoCalculate,
		onFinalize,
		onUpdateRecord,
		onAddEmployee,
		onRemoveEmployee,
		onDeleteDraft,
		onBack,
		onPayDateChange,
		onPreviewPaystub
	}: Props = $props();

	let expandedRecordId = $state<string | null>(null);
	let showHolidayModal = $state(false);
	let isUpdatingPayDate = $state(false);
	let autoCalculateTimer = $state<ReturnType<typeof setTimeout> | null>(null);

	// Filter state
	let filters = $state<PayrollDraftFilters>(DEFAULT_PAYROLL_DRAFT_FILTERS);

	// Derived: filtered pay groups
	const filteredPayGroups = $derived(filterPayrollRun(payrollRun.payGroups, filters));

	// Derived: filter stats
	const filterStats = $derived(calculateFilterStats(payrollRun.payGroups, filteredPayGroups));

	const AUTO_CALCULATE_DEBOUNCE_MS = 500;

	function handleToggleExpand(id: string) {
		expandedRecordId = expandedRecordId === id ? null : id;
	}

	function openHolidayModal() {
		showHolidayModal = true;
	}

	function closeHolidayModal() {
		showHolidayModal = false;
	}

	function handleManualRecalculate() {
		if (autoCalculateTimer) {
			clearTimeout(autoCalculateTimer);
			autoCalculateTimer = null;
		}
		onRecalculate();
	}

	function triggerAutoCalculate(
		recordId: string,
		compensationType: CompensationType,
		regularHours: number
	) {
		if (!onAutoCalculate) return;
		if (autoCalculateTimer) clearTimeout(autoCalculateTimer);

		const shouldAutoCalculate =
			compensationType === 'salaried' || (compensationType === 'hourly' && regularHours > 0);

		if (!shouldAutoCalculate) return;

		autoCalculateTimer = setTimeout(() => {
			onAutoCalculate(recordId);
		}, AUTO_CALCULATE_DEBOUNCE_MS);
	}

	// Handle pay date update
	async function handlePayDateSave(newPayDate: string) {
		if (onPayDateChange) {
			isUpdatingPayDate = true;
			try {
				await onPayDateChange(newPayDate);
			} finally {
				isUpdatingPayDate = false;
			}
		}
	}

	function handleHolidayWorkSave(entries: HolidayWorkEntry[]) {
		// Group holiday work entries by employee
		const entriesByEmployee = new Map<
			string,
			Array<{
				holidayDate: string;
				holidayName: string;
				hoursWorked: number;
			}>
		>();

		for (const entry of entries) {
			const existing = entriesByEmployee.get(entry.employeeId) || [];
			existing.push({
				holidayDate: entry.holidayDate,
				holidayName: entry.holidayName,
				hoursWorked: entry.hoursWorked
			});
			entriesByEmployee.set(entry.employeeId, existing);
		}

		// Update each employee's record with their holiday work entries
		for (const [employeeId, holidayWorkEntries] of entriesByEmployee) {
			const record = allRecords.find((r) => r.employeeId === employeeId);
			if (record) {
				onUpdateRecord(record.id, employeeId, { holidayWorkEntries });
			}
		}

		showHolidayModal = false;
	}

	// Get all records for the holiday modal
	const allRecords = $derived(payrollRun.payGroups.flatMap((pg) => pg.records));

	// Tooltip content
	const tooltips = $derived({
		totalDeductions:
			'Amount withheld from employee pay: CPP, EI, income taxes, and other deductions',
		totalEmployerCost: `Employer CPP: ${formatCurrency(payrollRun.totalCppEmployer)} + Employer EI: ${formatCurrency(payrollRun.totalEiEmployer)}`,
		totalPayrollCost: 'Total Gross + Total Employer Cost',
		totalRemittance: 'Amount to remit to CRA: Employee & Employer CPP/EI + Income Taxes'
	});

	// Validation disabled condition
	const isValidationDisabled = $derived(
		payrollRun.totalGross === 0 || payrollRun.totalRemittance === 0
	);

	// Combined disabled state for button
	const isFinalizeDisabled = $derived(isFinalizing || hasModifiedRecords || isValidationDisabled);

	// Dynamic tooltip message based on disabled reason
	const finalizeTooltip = $derived(
		isFinalizing
			? 'Finalizing...'
			: hasModifiedRecords
				? 'Calculate first to save changes'
				: payrollRun.totalGross === 0 && payrollRun.totalRemittance === 0
					? 'Cannot finalize: No earnings or remittances'
					: payrollRun.totalGross === 0
						? 'Cannot finalize: Total gross pay is zero'
						: payrollRun.totalRemittance === 0
							? 'Cannot finalize: Total remittance is zero'
							: 'Finalize payroll run'
	);

	// Get province from first pay group (for pay date editing)
	const province = $derived(payrollRun.payGroups[0]?.province ?? 'SK');

	// Filter change handler
	function handleFiltersChange(newFilters: PayrollDraftFilters) {
		filters = newFilters;
	}
</script>

<div class="flex flex-col gap-5">
	<!-- Header with Status Banner -->
	<div class="flex flex-col gap-3">
		<div class="flex justify-between items-center flex-wrap gap-3">
			<div class="flex items-center gap-3">
				<div
					class="inline-flex items-center gap-2 px-3 py-2 rounded-full text-sm font-semibold bg-amber-100 text-amber-700"
				>
					<i class="fas fa-edit"></i>
					Draft
				</div>
				<PayrollDatePicker
					value={payrollRun.payDate}
					periodEnd={payrollRun.payGroups[0]?.periodEnd ?? payrollRun.periodEnd}
					{province}
					onValueChange={() => {}}
					onSave={handlePayDateSave}
					onCancel={() => {}}
				/>
			</div>
			<div class="flex gap-3">
				{#if onBack}
					<button
						class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium cursor-pointer transition-all bg-transparent border-none text-gray-600 hover:bg-gray-100 hover:text-gray-800 disabled:opacity-60 disabled:cursor-not-allowed"
						onclick={onBack}
					>
						<i class="fas fa-arrow-left"></i>
						Back
					</button>
				{/if}
				{#if onDeleteDraft}
					<button
						class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium cursor-pointer transition-all bg-white border border-red-300 text-red-600 hover:bg-red-50 hover:border-red-400 disabled:opacity-60 disabled:cursor-not-allowed"
						onclick={onDeleteDraft}
						disabled={isDeleting}
					>
						{#if isDeleting}
							<i class="fas fa-spinner fa-spin"></i>
							Deleting...
						{:else}
							<i class="fas fa-trash"></i>
							Delete Draft
						{/if}
					</button>
				{/if}
				<button
					class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium cursor-pointer transition-all bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400 disabled:opacity-60 disabled:cursor-not-allowed"
					onclick={handleManualRecalculate}
					disabled={isRecalculating}
				>
					{#if isRecalculating}
						<i class="fas fa-spinner fa-spin"></i>
						Calculating...
					{:else}
						<i class="fas fa-calculator"></i>
						Calculate
					{/if}
				</button>
				<button
					class="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-base font-medium cursor-pointer transition-all bg-gradient-to-br from-blue-600 to-purple-600 border-none text-white hover:opacity-90 hover:-translate-y-px disabled:opacity-60 disabled:cursor-not-allowed"
					onclick={onFinalize}
					disabled={isFinalizeDisabled}
					title={finalizeTooltip}
				>
					{#if isFinalizing}
						<i class="fas fa-spinner fa-spin"></i>
						Finalizing...
					{:else}
						<i class="fas fa-check-circle"></i>
						Finalize
					{/if}
				</button>
			</div>
		</div>

		<!-- Warning Banner (when modified) -->
		{#if hasModifiedRecords}
			<div
				class="flex items-center gap-3 px-4 py-3 bg-amber-50 border border-amber-300 rounded-lg text-amber-800 text-base"
			>
				<i class="fas fa-exclamation-triangle text-amber-600 text-lg"></i>
				<span>
					<strong>Unsaved Changes:</strong> You have modified employee data. Click
					<strong>Calculate</strong> to update CPP, EI, and tax calculations.
				</span>
			</div>
		{/if}

		<!-- Validation Warning Banner -->
		{#if isValidationDisabled}
			<div
				class="flex items-center gap-3 px-4 py-3 bg-red-50 border border-red-300 rounded-lg text-red-800 text-base"
			>
				<i class="fas fa-exclamation-circle text-red-600 text-lg"></i>
				<span>
					<strong>Cannot Finalize:</strong>
					{payrollRun.totalGross === 0 && payrollRun.totalRemittance === 0
						? 'Total gross pay and remittance are both zero. Add employees or earnings before finalizing.'
						: payrollRun.totalGross === 0
							? 'Total gross pay is zero. Add employees or earnings before finalizing.'
							: 'Total remittance is zero. Review payroll calculations before finalizing.'}
				</span>
			</div>
		{/if}

		<!-- Holiday Alert -->
		{#if payrollRun.holidays && payrollRun.holidays.length > 0}
			<HolidayAlert holidays={payrollRun.holidays} onManageHolidayHours={openHolidayModal} />
		{/if}
	</div>

	<!-- Summary Cards - Row 1: Employee Perspective -->
	<div class="grid grid-cols-4 gap-4 max-lg:grid-cols-2 max-md:grid-cols-1">
		<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
			<div
				class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-blue-100 text-blue-600"
			>
				<i class="fas fa-dollar-sign"></i>
			</div>
			<div class="flex flex-col gap-0.5">
				<span class="text-xl font-bold text-gray-800">{formatCurrency(payrollRun.totalGross)}</span>
				<span class="text-xs text-gray-500">Total Gross</span>
			</div>
		</div>
		<Tooltip content={tooltips.totalDeductions}>
			<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
				<div
					class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-amber-100 text-amber-600"
				>
					<i class="fas fa-minus-circle"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-red-600"
						>-{formatCurrency(payrollRun.totalDeductions)}</span
					>
					<span class="text-xs text-gray-500">Total Deductions</span>
				</div>
			</div>
		</Tooltip>
		<div
			class="flex items-center gap-4 px-5 py-4 bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-2xl shadow-md"
		>
			<div
				class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-green-600 text-white"
			>
				<i class="fas fa-wallet"></i>
			</div>
			<div class="flex flex-col gap-0.5">
				<span class="text-xl font-bold text-gray-800">{formatCurrency(payrollRun.totalNetPay)}</span
				>
				<span class="text-xs text-gray-500">Total Net Pay</span>
			</div>
		</div>
		<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
			<div
				class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-purple-100 text-purple-600"
			>
				<i class="fas fa-users"></i>
			</div>
			<div class="flex flex-col gap-0.5">
				<span class="text-xl font-bold text-gray-800">{payrollRun.totalEmployees}</span>
				<span class="text-xs text-gray-500">Employees</span>
			</div>
		</div>
	</div>

	<!-- Summary Cards - Row 2: Employer Perspective -->
	<div class="grid grid-cols-3 gap-4 max-md:grid-cols-1">
		<Tooltip content={tooltips.totalEmployerCost}>
			<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
				<div
					class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-cyan-100 text-cyan-600"
				>
					<i class="fas fa-building"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-gray-800"
						>{formatCurrency(payrollRun.totalEmployerCost)}</span
					>
					<span class="text-xs text-gray-500">Total Employer Cost</span>
				</div>
			</div>
		</Tooltip>
		<Tooltip content={tooltips.totalPayrollCost}>
			<div
				class="flex items-center gap-4 px-5 py-4 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl shadow-md"
			>
				<div
					class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-white/20 text-white"
				>
					<i class="fas fa-receipt"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-white"
						>{formatCurrency(payrollRun.totalPayrollCost)}</span
					>
					<span class="text-xs text-white/80">Total Payroll Cost</span>
				</div>
			</div>
		</Tooltip>
		<Tooltip content={tooltips.totalRemittance}>
			<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
				<div
					class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-orange-100 text-orange-600"
				>
					<i class="fas fa-paper-plane"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-gray-800"
						>{formatCurrency(payrollRun.totalRemittance)}</span
					>
					<span class="text-xs text-gray-500">Total Remittance</span>
				</div>
			</div>
		</Tooltip>
	</div>

	<!-- Deduction Breakdown -->
	<div class="bg-white rounded-2xl shadow-md px-5 py-4">
		<h3 class="text-base font-semibold text-gray-700 m-0 mb-3">Deduction & Remittance Breakdown</h3>
		<div class="grid grid-cols-3 gap-3 max-lg:grid-cols-2 max-md:grid-cols-1">
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">CPP (Employee)</span>
				<span class="text-base font-medium text-gray-800"
					>{formatCurrency(payrollRun.totalCppEmployee)}</span
				>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">CPP (Employer)</span>
				<span class="text-base font-medium text-cyan-600"
					>{formatCurrency(payrollRun.totalCppEmployer)}</span
				>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">EI (Employee)</span>
				<span class="text-base font-medium text-gray-800"
					>{formatCurrency(payrollRun.totalEiEmployee)}</span
				>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">EI (Employer)</span>
				<span class="text-base font-medium text-cyan-600"
					>{formatCurrency(payrollRun.totalEiEmployer)}</span
				>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">Federal Tax</span>
				<span class="text-base font-medium text-gray-800"
					>{formatCurrency(payrollRun.totalFederalTax)}</span
				>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">Provincial Tax</span>
				<span class="text-base font-medium text-gray-800"
					>{formatCurrency(payrollRun.totalProvincialTax)}</span
				>
			</div>
		</div>
	</div>

	<!-- Employee Filters -->
	<PayrollDraftFiltersComponent
		{filters}
		payGroups={payrollRun.payGroups.map((pg) => ({
			payGroupId: pg.payGroupId,
			payGroupName: pg.payGroupName
		}))}
		stats={filterStats}
		onFiltersChange={handleFiltersChange}
	/>

	<!-- Pay Group Sections -->
	<div class="flex flex-col gap-4">
		{#each filteredPayGroups as payGroup (payGroup.payGroupId)}
			<DraftPayGroupSection
				{payGroup}
				holidays={payrollRun.holidays ?? []}
				{expandedRecordId}
				{isRecalculating}
				onToggleExpand={handleToggleExpand}
				{onUpdateRecord}
				onAutoCalculateTrigger={triggerAutoCalculate}
				{onAddEmployee}
				{onRemoveEmployee}
				{onPreviewPaystub}
			/>
		{/each}
	</div>
</div>

<!-- Holiday Work Modal -->
{#if showHolidayModal && payrollRun.holidays && payrollRun.holidays.length > 0}
	<HolidayWorkModal
		holidays={payrollRun.holidays}
		payrollRecords={allRecords}
		periodStart={payrollRun.payGroups[0]?.periodStart || ''}
		periodEnd={payrollRun.payGroups[0]?.periodEnd || ''}
		onClose={closeHolidayModal}
		onSave={handleHolidayWorkSave}
	/>
{/if}
