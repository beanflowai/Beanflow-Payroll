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

<tr class:expanded={isExpanded}>
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
		<span class="rate-value">{formatCompensation()}</span>
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
					value={input.regularHours}
					onchange={(e) => onHoursChange('regularHours', parseFloat((e.target as HTMLInputElement).value) || 0)}
					placeholder="Hrs"
				/>
			</div>
		{:else}
			<span class="no-hours">-</span>
		{/if}
	</td>
	<td class="col-overtime">
		<div class="hours-input-group">
			<input
				type="number"
				class="hours-input overtime-input"
				min="0"
				max="100"
				step="0.5"
				value={input.overtimeHours}
				onchange={(e) => onHoursChange('overtimeHours', parseFloat((e.target as HTMLInputElement).value) || 0)}
				placeholder="OT"
			/>
		</div>
	</td>
	<td class="col-leave">
		{#if totalLeaveHours > 0}
			<span class="leave-badge">{totalLeaveHours}h</span>
		{:else}
			<span class="no-leave">-</span>
		{/if}
	</td>
	<td class="col-gross">
		{#if estimatedGross !== null}
			<span class="estimated-gross">{formatCurrency(estimatedGross)}</span>
		{:else}
			<span class="placeholder-cell">--</span>
		{/if}
	</td>
	<td class="col-expand">
		<button
			class="btn-expand"
			class:expanded={isExpanded}
			onclick={onToggleExpand}
			aria-label={isExpanded ? 'Collapse details' : 'Expand details'}
		>
			<i class="fas fa-chevron-{isExpanded ? 'up' : 'down'}"></i>
		</button>
	</td>
</tr>
{#if isExpanded}
	<tr class="expanded-row">
		<td colspan="8">
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

<style>
	tr {
		transition: background-color var(--transition-fast);
	}

	tr:hover {
		background: var(--color-surface-50);
	}

	tr.expanded {
		background: var(--color-primary-50);
	}

	td {
		padding: var(--spacing-3) var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-100);
		vertical-align: middle;
	}

	.expanded-row td {
		padding: 0;
		background: var(--color-surface-50);
	}

	/* Employee Column */
	.col-employee {
		min-width: 180px;
	}

	.employee-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.employee-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	/* Type Badge */
	.col-type {
		min-width: 80px;
	}

	.type-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-caption);
		font-weight: var(--font-weight-medium);
	}

	.type-badge.hourly {
		background: var(--color-info-100);
		color: var(--color-info-700);
	}

	.type-badge.salaried {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	/* Rate Column */
	.col-rate {
		min-width: 120px;
	}

	.rate-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	/* Hours Input */
	.col-hours,
	.col-overtime {
		min-width: 90px;
	}

	.hours-input-group {
		display: flex;
		align-items: center;
	}

	.hours-input {
		width: 70px;
		padding: var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-small);
		text-align: center;
		transition: var(--transition-fast);
	}

	.hours-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.hours-input.overtime-input {
		border-color: var(--color-warning-300);
	}

	.hours-input.overtime-input:focus {
		border-color: var(--color-warning-500);
		box-shadow: 0 0 0 2px var(--color-warning-100);
	}

	.no-hours {
		color: var(--color-surface-400);
		font-size: var(--font-size-body-content);
	}

	/* Leave Column */
	.col-leave {
		min-width: 70px;
	}

	.leave-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-warning-100);
		color: var(--color-warning-700);
		border-radius: var(--radius-full);
		font-size: var(--font-size-caption);
		font-weight: var(--font-weight-medium);
	}

	.no-leave {
		color: var(--color-surface-400);
		font-size: var(--font-size-body-content);
	}

	/* Gross Column */
	.col-gross {
		min-width: 110px;
		text-align: right;
	}

	.estimated-gross {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-success-600);
	}

	.placeholder-cell {
		color: var(--color-surface-400);
	}

	/* Expand Button */
	.col-expand {
		width: 50px;
		text-align: center;
	}

	.btn-expand {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 32px;
		height: 32px;
		background: var(--color-surface-100);
		border: none;
		border-radius: var(--radius-md);
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-expand:hover {
		background: var(--color-surface-200);
		color: var(--color-surface-700);
	}

	.btn-expand.expanded {
		background: var(--color-primary-100);
		color: var(--color-primary-600);
	}

	/* Responsive */
	@media (max-width: 768px) {
		td {
			padding: var(--spacing-2) var(--spacing-3);
		}

		.hours-input {
			width: 60px;
		}
	}
</style>
