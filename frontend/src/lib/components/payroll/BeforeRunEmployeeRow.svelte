<script lang="ts">
	import type { EmployeePayrollInput, EarningsBreakdown, Adjustment } from '$lib/types/payroll';
	import type { EmployeeForPayroll } from '$lib/services/payrollService';
	import { BeforeRunEmployeeExpandedRow } from '$lib/components/payroll';

	interface Props {
		employee: EmployeeForPayroll;
		input: EmployeePayrollInput;
		estimatedGross: number | null;
		earningsBreakdown: EarningsBreakdown[];
		isExpanded: boolean;
		onToggleExpand: () => void;
		onHoursChange: (field: 'regularHours' | 'overtimeHours', value: number) => void;
		onEarningsEdit: (key: string, value: number) => void;
		onLeaveChange: (type: 'vacation' | 'sick', hours: number) => void;
		onAddAdjustment: () => void;
		onUpdateAdjustment: (idx: number, updates: Partial<Adjustment>) => void;
		onRemoveAdjustment: (idx: number) => void;
	}

	let {
		employee,
		input,
		estimatedGross,
		earningsBreakdown,
		isExpanded,
		onToggleExpand,
		onHoursChange,
		onEarningsEdit,
		onLeaveChange,
		onAddAdjustment,
		onUpdateAdjustment,
		onRemoveAdjustment
	}: Props = $props();

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	function formatCompensation(): string {
		if (employee.annualSalary) {
			return formatCurrency(employee.annualSalary) + '/yr';
		} else if (employee.hourlyRate) {
			return formatCurrency(employee.hourlyRate) + '/hr';
		}
		return '--';
	}

	const totalLeaveHours = $derived(input.leaveEntries.reduce((sum, l) => sum + l.hours, 0));
</script>

<tr class="transition-colors duration-150 hover:bg-surface-50" class:bg-primary-50={isExpanded}>
	<td class="py-3 px-4 border-b border-surface-100 align-middle min-w-[180px]">
		<div class="flex flex-col gap-1">
			<span class="text-body-content font-medium text-surface-800">{employee.firstName} {employee.lastName}</span>
		</div>
	</td>
	<td class="py-3 px-4 border-b border-surface-100 align-middle min-w-[80px]">
		<span
			class="inline-block py-1 px-2 rounded-full text-caption font-medium"
			class:bg-info-100={employee.compensationType === 'hourly'}
			class:text-info-700={employee.compensationType === 'hourly'}
			class:bg-success-100={employee.compensationType === 'salaried'}
			class:text-success-700={employee.compensationType === 'salaried'}
		>
			{employee.compensationType === 'salaried' ? 'Salary' : 'Hourly'}
		</span>
	</td>
	<td class="py-3 px-4 border-b border-surface-100 align-middle min-w-[120px]">
		<span class="text-body-content font-medium text-surface-700">{formatCompensation()}</span>
	</td>
	<td class="py-3 px-4 border-b border-surface-100 align-middle min-w-[90px]">
		{#if employee.compensationType === 'hourly'}
			<div class="flex items-center">
				<input
					type="number"
					class="w-[70px] py-2 border border-surface-300 rounded-md text-body-small text-center transition-all duration-150 focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
					min="0"
					max="200"
					step="0.5"
					value={input.regularHours}
					onchange={(e) => onHoursChange('regularHours', parseFloat((e.target as HTMLInputElement).value) || 0)}
					placeholder="Hrs"
				/>
			</div>
		{:else}
			<span class="text-surface-400 text-body-content">-</span>
		{/if}
	</td>
	<td class="py-3 px-4 border-b border-surface-100 align-middle min-w-[90px]">
		<div class="flex items-center">
			<input
				type="number"
				class="w-[70px] py-2 border border-warning-300 rounded-md text-body-small text-center transition-all duration-150 focus:outline-none focus:border-warning-500 focus:ring-2 focus:ring-warning-100"
				min="0"
				max="100"
				step="0.5"
				value={input.overtimeHours}
				onchange={(e) => onHoursChange('overtimeHours', parseFloat((e.target as HTMLInputElement).value) || 0)}
				placeholder="OT"
			/>
		</div>
	</td>
	<td class="py-3 px-4 border-b border-surface-100 align-middle min-w-[70px]">
		{#if totalLeaveHours > 0}
			<span class="inline-block py-1 px-2 bg-warning-100 text-warning-700 rounded-full text-caption font-medium">{totalLeaveHours}h</span>
		{:else}
			<span class="text-surface-400 text-body-content">-</span>
		{/if}
	</td>
	<td class="py-3 px-4 border-b border-surface-100 align-middle min-w-[110px] text-right">
		{#if estimatedGross !== null}
			<span class="text-body-content font-semibold text-success-600">{formatCurrency(estimatedGross)}</span>
		{:else}
			<span class="text-surface-400">--</span>
		{/if}
	</td>
	<td class="py-3 px-4 border-b border-surface-100 align-middle w-[50px] text-center">
		<button
			class="flex items-center justify-center w-8 h-8 rounded-md border-none cursor-pointer transition-all duration-150"
			class:bg-surface-100={!isExpanded}
			class:text-surface-500={!isExpanded}
			class:hover:bg-surface-200={!isExpanded}
			class:hover:text-surface-700={!isExpanded}
			class:bg-primary-100={isExpanded}
			class:text-primary-600={isExpanded}
			onclick={onToggleExpand}
			aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
		>
			<i class="fas fa-chevron-{isExpanded ? 'up' : 'down'}"></i>
		</button>
	</td>
</tr>
{#if isExpanded}
	<tr>
		<td colspan="8" class="p-0 bg-surface-50">
			<BeforeRunEmployeeExpandedRow
				{input}
				{earningsBreakdown}
				{estimatedGross}
				{onEarningsEdit}
				{onLeaveChange}
				{onAddAdjustment}
				{onUpdateAdjustment}
				{onRemoveAdjustment}
			/>
		</td>
	</tr>
{/if}
