<script lang="ts">
	import type { EmployeePayrollInput, EarningsBreakdown, Adjustment } from '$lib/types/payroll';
	import { PAY_FREQUENCY_LABELS, EMPLOYMENT_TYPE_LABELS, ADJUSTMENT_TYPE_LABELS, createDefaultPayrollInput } from '$lib/types/payroll';
	import type { EmployeeForPayroll, PayGroupWithEmployees } from '$lib/services/payrollService';
	import { BeforeRunEmployeeRow } from '$lib/components/payroll';

	interface Props {
		payGroup: PayGroupWithEmployees;
		payrollInputMap: Map<string, EmployeePayrollInput>;
		expandedRecordId: string | null;
		estimatedGross: number | null;
		onToggleExpand: (id: string) => void;
		onAddEmployees: () => void;
		onUpdatePayrollInput: (employeeId: string, updates: Partial<EmployeePayrollInput>) => void;
		getEarningsBreakdown: (employee: EmployeeForPayroll) => EarningsBreakdown[];
		calculateEstimatedGross: (employee: EmployeeForPayroll) => number | null;
	}

	let {
		payGroup,
		payrollInputMap,
		expandedRecordId,
		estimatedGross,
		onToggleExpand,
		onAddEmployees,
		onUpdatePayrollInput,
		getEarningsBreakdown,
		calculateEstimatedGross
	}: Props = $props();

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 2
		}).format(amount);
	}

	function formatDateRange(start: string, end: string): string {
		const startDate = new Date(start);
		const endDate = new Date(end);
		const startStr = startDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		const endStr = endDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		return `${startStr} - ${endStr}`;
	}

	function getPayrollInput(employeeId: string): EmployeePayrollInput {
		return payrollInputMap.get(employeeId) || createDefaultPayrollInput(employeeId, 0);
	}

	function handleHoursChange(employeeId: string, field: 'regularHours' | 'overtimeHours', value: number) {
		const input = getPayrollInput(employeeId);
		onUpdatePayrollInput(employeeId, { [field]: value });
	}

	function handleEarningsEdit(employeeId: string, key: string, value: number) {
		const input = getPayrollInput(employeeId);
		if (key === 'regularPay') {
			const overrides = { ...input.overrides, regularPay: value };
			onUpdatePayrollInput(employeeId, { overrides });
		} else if (key === 'overtimePay') {
			onUpdatePayrollInput(employeeId, { overtimeHours: value });
		}
	}

	function handleLeaveChange(employeeId: string, type: 'vacation' | 'sick', hours: number) {
		const input = getPayrollInput(employeeId);
		const newLeaveEntries = input.leaveEntries.filter(l => l.type !== type);
		if (hours > 0) {
			newLeaveEntries.push({ type, hours });
		}
		onUpdatePayrollInput(employeeId, { leaveEntries: newLeaveEntries });
	}

	function handleAddAdjustment(employeeId: string) {
		const input = getPayrollInput(employeeId);
		const newAdj: Adjustment = {
			id: crypto.randomUUID(),
			type: 'bonus',
			amount: 0,
			description: '',
			taxable: true
		};
		onUpdatePayrollInput(employeeId, {
			adjustments: [...input.adjustments, newAdj]
		});
	}

	function handleUpdateAdjustment(employeeId: string, idx: number, updates: Partial<Adjustment>) {
		const input = getPayrollInput(employeeId);
		const newAdjs = [...input.adjustments];
		newAdjs[idx] = { ...newAdjs[idx], ...updates };
		onUpdatePayrollInput(employeeId, { adjustments: newAdjs });
	}

	function handleRemoveAdjustment(employeeId: string, idx: number) {
		const input = getPayrollInput(employeeId);
		const newAdjs = input.adjustments.filter((_, i) => i !== idx);
		onUpdatePayrollInput(employeeId, { adjustments: newAdjs });
	}
</script>

<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
	<!-- Section Header -->
	<div class="flex justify-between items-center py-4 px-5 bg-surface-50 border-b border-surface-200 max-lg:flex-col max-lg:items-start max-lg:gap-3">
		<div class="flex items-center gap-3">
			<div class="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-600 to-secondary-600 text-white flex items-center justify-center text-base">
				<i class="fas fa-tag"></i>
			</div>
			<div class="flex flex-col gap-1">
				<h3 class="text-body-content font-semibold text-surface-800 m-0">{payGroup.name}</h3>
				<div class="flex items-center gap-2 text-caption text-surface-500">
					<span>{PAY_FREQUENCY_LABELS[payGroup.payFrequency] || payGroup.payFrequency}</span>
					<span class="w-1 h-1 rounded-full bg-surface-300"></span>
					<span>{EMPLOYMENT_TYPE_LABELS[payGroup.employmentType] || payGroup.employmentType}</span>
					<span class="w-1 h-1 rounded-full bg-surface-300"></span>
					<span>{formatDateRange(payGroup.periodStart, payGroup.periodEnd)}</span>
				</div>
			</div>
		</div>
		<div class="flex items-center gap-4 max-lg:w-full max-lg:justify-between">
			<div class="flex gap-5 max-md:gap-3">
				<div class="flex flex-col items-end gap-0.5">
					<span class="text-body-content font-semibold text-surface-800">{payGroup.employees.length}</span>
					<span class="text-caption text-surface-500">Employees</span>
				</div>
				<div class="flex flex-col items-end gap-0.5">
					{#if estimatedGross !== null}
						<span class="text-body-content font-semibold text-success-600">{formatCurrency(estimatedGross)}</span>
					{:else}
						<span class="text-body-content font-semibold text-surface-400">--</span>
					{/if}
					<span class="text-caption text-surface-500">Est. Gross</span>
				</div>
				<div class="flex flex-col items-end gap-0.5">
					<span class="text-body-content font-semibold text-surface-400">--</span>
					<span class="text-caption text-surface-500">Net Pay</span>
				</div>
			</div>
			<button
				class="flex items-center gap-2 py-2 px-3 bg-primary-50 text-primary-600 border border-primary-200 rounded-lg text-body-small font-medium cursor-pointer transition-all duration-150 hover:bg-primary-100 hover:border-primary-300"
				onclick={onAddEmployees}
			>
				<i class="fas fa-user-plus"></i>
				<span>Add</span>
			</button>
		</div>
	</div>

	<!-- Employee Table -->
	<div class="p-0">
		{#if payGroup.employees.length === 0}
			<div class="flex flex-col items-center justify-center py-8 text-center text-surface-500">
				<i class="fas fa-user-plus text-[32px] mb-3 text-surface-300"></i>
				<span class="text-body-content mb-4">No employees assigned to this pay group</span>
				<button
					class="flex items-center gap-2 py-2 px-4 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-small font-medium cursor-pointer transition-all duration-150 hover:opacity-90 hover:-translate-y-px"
					onclick={onAddEmployees}
				>
					<i class="fas fa-plus"></i>
					Add Employees
				</button>
			</div>
		{:else}
			<table class="w-full border-collapse">
				<thead class="bg-surface-100">
					<tr>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200">Employee</th>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200">Type</th>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200">Rate/Salary</th>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200">Hours</th>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200">Overtime</th>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200">Leave</th>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-right uppercase tracking-wider border-b border-surface-200">Est. Gross</th>
						<th class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200 w-[50px]"></th>
					</tr>
				</thead>
				<tbody>
					{#each payGroup.employees as employee (employee.id)}
						{@const input = getPayrollInput(employee.id)}
						{@const empEstimatedGross = calculateEstimatedGross(employee)}
						{@const empEarningsBreakdown = getEarningsBreakdown(employee)}
						<BeforeRunEmployeeRow
							{employee}
							{input}
							estimatedGross={empEstimatedGross}
							earningsBreakdown={empEarningsBreakdown}
							isExpanded={expandedRecordId === employee.id}
							onToggleExpand={() => onToggleExpand(employee.id)}
							onHoursChange={(field, value) => handleHoursChange(employee.id, field, value)}
							onEarningsEdit={(key, value) => handleEarningsEdit(employee.id, key, value)}
							onLeaveChange={(type, hours) => handleLeaveChange(employee.id, type, hours)}
							onAddAdjustment={() => handleAddAdjustment(employee.id)}
							onUpdateAdjustment={(idx, updates) => handleUpdateAdjustment(employee.id, idx, updates)}
							onRemoveAdjustment={(idx) => handleRemoveAdjustment(employee.id, idx)}
						/>
					{/each}
				</tbody>
			</table>
		{/if}
	</div>
</div>
