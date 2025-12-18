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
					{#if estimatedGross !== null}
						<span class="stat-value estimated">{formatCurrency(estimatedGross)}</span>
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
			<button class="btn-add-more-header" onclick={onAddEmployees}>
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
				<button class="btn-add-employees" onclick={onAddEmployees}>
					<i class="fas fa-plus"></i>
					Add Employees
				</button>
			</div>
		{:else}
			<table class="records-table before-run-table">
				<thead>
					<tr>
						<th class="col-employee">Employee</th>
						<th class="col-type">Type</th>
						<th class="col-rate">Rate/Salary</th>
						<th class="col-hours">Hours</th>
						<th class="col-overtime">Overtime</th>
						<th class="col-leave">Leave</th>
						<th class="col-gross">Est. Gross</th>
						<th class="col-expand"></th>
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

<style>
	.pay-group-section {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	/* Section Header */
	.section-header-static {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.group-badge {
		width: 40px;
		height: 40px;
		border-radius: var(--radius-lg);
		background: var(--gradient-primary);
		color: white;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 16px;
	}

	.group-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.group-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.group-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-caption);
		color: var(--color-surface-500);
	}

	.meta-divider {
		width: 4px;
		height: 4px;
		border-radius: 50%;
		background: var(--color-surface-300);
	}

	.header-right {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
	}

	.header-stats {
		display: flex;
		gap: var(--spacing-5);
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}

	.stat-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.stat-value.estimated {
		color: var(--color-success-600);
	}

	.stat-value.placeholder {
		color: var(--color-surface-400);
	}

	.stat-label {
		font-size: var(--font-size-caption);
		color: var(--color-surface-500);
	}

	.btn-add-more-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		background: var(--color-primary-50);
		color: var(--color-primary-600);
		border: 1px solid var(--color-primary-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add-more-header:hover {
		background: var(--color-primary-100);
		border-color: var(--color-primary-300);
	}

	/* Section Content */
	.section-content {
		padding: 0;
	}

	/* Empty State */
	.empty-employees {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-8);
		text-align: center;
		color: var(--color-surface-500);
	}

	.empty-employees i {
		font-size: 32px;
		margin-bottom: var(--spacing-3);
		color: var(--color-surface-300);
	}

	.empty-employees span {
		font-size: var(--font-size-body-content);
		margin-bottom: var(--spacing-4);
	}

	.btn-add-employees {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--gradient-primary);
		color: white;
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add-employees:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	/* Records Table */
	.records-table {
		width: 100%;
		border-collapse: collapse;
	}

	.records-table thead {
		background: var(--color-surface-100);
	}

	.records-table th {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-caption);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-align: left;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-bottom: 1px solid var(--color-surface-200);
	}

	.records-table th.col-gross {
		text-align: right;
	}

	.records-table th.col-expand {
		width: 50px;
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.section-header-static {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-3);
		}

		.header-right {
			width: 100%;
			justify-content: space-between;
		}
	}

	@media (max-width: 768px) {
		.header-stats {
			gap: var(--spacing-3);
		}

		.records-table {
			font-size: var(--font-size-body-small);
		}

		.records-table th {
			padding: var(--spacing-2) var(--spacing-3);
		}
	}
</style>
