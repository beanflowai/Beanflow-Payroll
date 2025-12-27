<script lang="ts">
	import type {
		PayrollRunWithGroups,
		PayrollRunPayGroup,
		EmployeePayrollInput
	} from '$lib/types/payroll';
	import { DraftPayGroupSection } from '$lib/components/payroll';
	import Tooltip from '$lib/components/shared/Tooltip.svelte';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils';

	interface Props {
		payrollRun: PayrollRunWithGroups;
		hasModifiedRecords: boolean;
		isRecalculating: boolean;
		isFinalizing: boolean;
		isDeleting?: boolean;
		onRecalculate: () => void;
		onFinalize: () => void;
		onUpdateRecord: (recordId: string, employeeId: string, updates: Partial<EmployeePayrollInput>) => void;
		onAddEmployee?: (payGroupId: string) => void;
		onRemoveEmployee?: (employeeId: string) => void;
		onDeleteDraft?: () => void;
		onBack?: () => void;
	}

	let {
		payrollRun,
		hasModifiedRecords,
		isRecalculating,
		isFinalizing,
		isDeleting = false,
		onRecalculate,
		onFinalize,
		onUpdateRecord,
		onAddEmployee,
		onRemoveEmployee,
		onDeleteDraft,
		onBack
	}: Props = $props();

	let expandedRecordId = $state<string | null>(null);

	function handleToggleExpand(id: string) {
		expandedRecordId = expandedRecordId === id ? null : id;
	}

	// Tooltip content
	const tooltips = $derived({
		totalDeductions: 'Amount withheld from employee pay: CPP, EI, income taxes, and other deductions',
		totalEmployerCost: `Employer CPP: ${formatCurrency(payrollRun.totalCppEmployer)} + Employer EI: ${formatCurrency(payrollRun.totalEiEmployer)}`,
		totalPayrollCost: 'Total Gross + Total Employer Cost',
		totalRemittance: 'Amount to remit to CRA: Employee & Employer CPP/EI + Income Taxes'
	});
</script>

<div class="flex flex-col gap-5">
	<!-- Header with Status Banner -->
	<div class="flex flex-col gap-3">
		<div class="flex justify-between items-center flex-wrap gap-3">
			<div class="flex items-center gap-3">
				<div class="inline-flex items-center gap-2 px-3 py-2 rounded-full text-sm font-semibold bg-amber-100 text-amber-700">
					<i class="fas fa-edit"></i>
					Draft
				</div>
				<h1 class="text-2xl font-bold text-gray-800 m-0">Pay Date: {formatShortDate(payrollRun.payDate)}</h1>
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
					onclick={onRecalculate}
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
					disabled={isFinalizing || hasModifiedRecords}
					title={hasModifiedRecords ? 'Calculate first to save changes' : 'Finalize payroll run'}
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
			<div class="flex items-center gap-3 px-4 py-3 bg-amber-50 border border-amber-300 rounded-lg text-amber-800 text-base">
				<i class="fas fa-exclamation-triangle text-amber-600 text-lg"></i>
				<span>
					<strong>Unsaved Changes:</strong> You have modified employee data. Click
					<strong>Calculate</strong> to update CPP, EI, and tax calculations.
				</span>
			</div>
		{/if}
	</div>

	<!-- Summary Cards - Row 1: Employee Perspective -->
	<div class="grid grid-cols-4 gap-4 max-lg:grid-cols-2 max-md:grid-cols-1">
		<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
			<div class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-blue-100 text-blue-600">
				<i class="fas fa-dollar-sign"></i>
			</div>
			<div class="flex flex-col gap-0.5">
				<span class="text-xl font-bold text-gray-800">{formatCurrency(payrollRun.totalGross)}</span>
				<span class="text-xs text-gray-500">Total Gross</span>
			</div>
		</div>
		<Tooltip content={tooltips.totalDeductions}>
			<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
				<div class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-amber-100 text-amber-600">
					<i class="fas fa-minus-circle"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-red-600">-{formatCurrency(payrollRun.totalDeductions)}</span>
					<span class="text-xs text-gray-500">Total Deductions</span>
				</div>
			</div>
		</Tooltip>
		<div class="flex items-center gap-4 px-5 py-4 bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-2xl shadow-md">
			<div class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-green-600 text-white">
				<i class="fas fa-wallet"></i>
			</div>
			<div class="flex flex-col gap-0.5">
				<span class="text-xl font-bold text-gray-800">{formatCurrency(payrollRun.totalNetPay)}</span>
				<span class="text-xs text-gray-500">Total Net Pay</span>
			</div>
		</div>
		<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
			<div class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-purple-100 text-purple-600">
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
				<div class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-cyan-100 text-cyan-600">
					<i class="fas fa-building"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-gray-800">{formatCurrency(payrollRun.totalEmployerCost)}</span>
					<span class="text-xs text-gray-500">Total Employer Cost</span>
				</div>
			</div>
		</Tooltip>
		<Tooltip content={tooltips.totalPayrollCost}>
			<div class="flex items-center gap-4 px-5 py-4 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl shadow-md">
				<div class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-white/20 text-white">
					<i class="fas fa-receipt"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-white">{formatCurrency(payrollRun.totalPayrollCost)}</span>
					<span class="text-xs text-white/80">Total Payroll Cost</span>
				</div>
			</div>
		</Tooltip>
		<Tooltip content={tooltips.totalRemittance}>
			<div class="flex items-center gap-4 px-5 py-4 bg-white rounded-2xl shadow-md">
				<div class="w-12 h-12 rounded-lg flex items-center justify-center text-xl bg-orange-100 text-orange-600">
					<i class="fas fa-paper-plane"></i>
				</div>
				<div class="flex flex-col gap-0.5">
					<span class="text-xl font-bold text-gray-800">{formatCurrency(payrollRun.totalRemittance)}</span>
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
				<span class="text-base font-medium text-gray-800">{formatCurrency(payrollRun.totalCppEmployee)}</span>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">CPP (Employer)</span>
				<span class="text-base font-medium text-cyan-600">{formatCurrency(payrollRun.totalCppEmployer)}</span>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">EI (Employee)</span>
				<span class="text-base font-medium text-gray-800">{formatCurrency(payrollRun.totalEiEmployee)}</span>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">EI (Employer)</span>
				<span class="text-base font-medium text-cyan-600">{formatCurrency(payrollRun.totalEiEmployer)}</span>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">Federal Tax</span>
				<span class="text-base font-medium text-gray-800">{formatCurrency(payrollRun.totalFederalTax)}</span>
			</div>
			<div class="flex justify-between px-3 py-2 bg-gray-50 rounded-md">
				<span class="text-base text-gray-600">Provincial Tax</span>
				<span class="text-base font-medium text-gray-800">{formatCurrency(payrollRun.totalProvincialTax)}</span>
			</div>
		</div>
	</div>

	<!-- Pay Group Sections -->
	<div class="flex flex-col gap-4">
		{#each payrollRun.payGroups as payGroup (payGroup.payGroupId)}
			<DraftPayGroupSection
				{payGroup}
				{expandedRecordId}
				onToggleExpand={handleToggleExpand}
				{onUpdateRecord}
				{onAddEmployee}
				{onRemoveEmployee}
			/>
		{/each}
	</div>
</div>
