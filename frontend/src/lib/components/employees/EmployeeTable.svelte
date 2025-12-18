<script lang="ts">
	import type { Employee, ColumnGroup } from '$lib/types/employee';
	import {
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		COLUMN_GROUP_LABELS,
		EMPLOYEE_STATUS_LABELS
	} from '$lib/types/employee';
	import { Avatar } from '$lib/components/shared';

	interface Props {
		employees: Employee[];
		selectedIds: Set<string>;
		activeColumnGroup: ColumnGroup;
		onToggleSelectAll: () => void;
		onToggleSelect: (id: string) => void;
		onRowClick: (id: string) => void;
	}

	let {
		employees,
		selectedIds,
		activeColumnGroup,
		onToggleSelectAll,
		onToggleSelect,
		onRowClick
	}: Props = $props();

	// Helpers
	function formatCurrency(amount: number | null | undefined): string {
		if (amount == null) return '-';
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			maximumFractionDigits: 0
		}).format(amount);
	}

	function formatCompensation(emp: Employee): string {
		if (emp.hourlyRate) return `$${emp.hourlyRate.toFixed(2)}/hr`;
		if (emp.annualSalary) return `${formatCurrency(emp.annualSalary)}/yr`;
		return '-';
	}

	function formatDate(dateStr: string | null | undefined): string {
		if (!dateStr) return '-';
		return new Date(dateStr).toLocaleDateString('en-CA', {
			year: 'numeric',
			month: 'short',
			day: 'numeric'
		});
	}

	function getFullName(emp: Employee): string {
		return `${emp.firstName} ${emp.lastName}`;
	}

	// Pay periods per year based on frequency
	const PAY_PERIODS_MAP: Record<string, number> = {
		weekly: 52,
		bi_weekly: 26,
		semi_monthly: 24,
		monthly: 12
	};

	function getPerPeriodAmount(emp: Employee): string {
		if (!emp.annualSalary) return '-';
		const periods = PAY_PERIODS_MAP[emp.payFrequency] || 26;
		return formatCurrency(emp.annualSalary / periods);
	}

	function handleRowClick(e: MouseEvent, empId: string) {
		// Don't trigger row click if clicking on checkbox
		const target = e.target as HTMLElement;
		if (target.tagName === 'INPUT' && target.getAttribute('type') === 'checkbox') {
			return;
		}
		onRowClick(empId);
	}
</script>

<!-- Column Group Tabs -->
<div class="column-group-tabs">
	{#each Object.entries(COLUMN_GROUP_LABELS) as [key, label]}
		<button
			class="column-tab"
			class:active={activeColumnGroup === key}
			onclick={() => (activeColumnGroup = key as ColumnGroup)}
		>
			{label}
		</button>
	{/each}
</div>

<!-- Table -->
<div class="table-container">
	<table class="data-table">
		<thead>
			<tr>
				<th class="col-checkbox">
					<input
						type="checkbox"
						checked={selectedIds.size === employees.length && employees.length > 0}
						onchange={onToggleSelectAll}
					/>
				</th>
				<th class="col-name">Name</th>

				{#if activeColumnGroup === 'personal'}
					<th class="col-type">Emp Type</th>
					<th class="col-frequency">
						<span class="header-with-tooltip">
							Pay Freq
							<span class="tooltip-trigger" title="Pay Frequency determines how often the employee is paid: Weekly (52/yr), Bi-weekly (26/yr), Semi-monthly (24/yr), or Monthly (12/yr).">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-date">Hire Date</th>
					<th class="col-status">Status</th>
				{:else if activeColumnGroup === 'employment'}
					<th class="col-province">
						<span class="header-with-tooltip">
							Province
							<span class="tooltip-trigger" title="Province of Employment determines provincial tax rates. Use the province where the employee primarily works.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-frequency">
						<span class="header-with-tooltip">
							Pay Freq
							<span class="tooltip-trigger" title="Pay Frequency determines how often the employee is paid: Weekly (52/yr), Bi-weekly (26/yr), Semi-monthly (24/yr), or Monthly (12/yr).">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-type">Type</th>
					<th class="col-date">Hire Date</th>
				{:else if activeColumnGroup === 'compensation'}
					<th class="col-salary">Salary/Rate</th>
					<th class="col-period">
						<span class="header-with-tooltip">
							Per Period
							<span class="tooltip-trigger" title="Gross pay per pay period, calculated as Annual Salary ÷ Pay Periods (Weekly=52, Bi-weekly=26, Semi-monthly=24, Monthly=12)">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-vacation">
						<span class="header-with-tooltip">
							Vacation Rate
							<span class="tooltip-trigger" title="Percentage of gross pay accrued as vacation pay. Common rates: 4% (2 weeks), 6% (3 weeks), 8% (4 weeks).">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-balance">
						<span class="header-with-tooltip">
							Vac Balance
							<span class="tooltip-trigger" title="Accumulated vacation pay balance. Updated automatically through payroll.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
				{:else if activeColumnGroup === 'tax'}
					<th class="col-claim">
						<span class="header-with-tooltip">
							Fed Claim
							<span class="tooltip-trigger" title="Federal Basic Personal Amount from TD1 form. Reduces federal tax withheld. 2025 default: $16,129.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-claim">
						<span class="header-with-tooltip">
							Prov Claim
							<span class="tooltip-trigger" title="Provincial Basic Personal Amount from TD1 provincial form. Varies by province.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-exempt">CPP Exempt</th>
					<th class="col-exempt">EI Exempt</th>
				{:else if activeColumnGroup === 'deductions'}
					<th class="col-amount">
						<span class="header-with-tooltip">
							RRSP/Period
							<span class="tooltip-trigger" title="RRSP contribution deducted each pay period. Reduces taxable income.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-amount">
						<span class="header-with-tooltip">
							Union Dues
							<span class="tooltip-trigger" title="Union dues deducted each pay period. Tax-deductible for employee. Reported on T4 Box 44.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
				{/if}

				<th class="col-actions"></th>
			</tr>
		</thead>
		<tbody>
			{#each employees as emp (emp.id)}
				<tr
					class:terminated={emp.status === 'terminated'}
					class:draft={emp.status === 'draft'}
					class:selected={selectedIds.has(emp.id)}
					onclick={(e) => handleRowClick(e, emp.id)}
				>
					<td class="col-checkbox">
						<input
							type="checkbox"
							checked={selectedIds.has(emp.id)}
							onchange={() => onToggleSelect(emp.id)}
						/>
					</td>
					<td class="col-name">
						<div class="employee-cell">
							<Avatar name={getFullName(emp)} size="small" />
							<span class="name">{getFullName(emp)}</span>
						</div>
					</td>

					{#if activeColumnGroup === 'personal'}
						<td class="col-type">
							<span class="type-badge">{EMPLOYMENT_TYPE_LABELS[emp.employmentType]}</span>
						</td>
						<td class="col-frequency">{PAY_FREQUENCY_LABELS[emp.payFrequency]}</td>
						<td class="col-date">{formatDate(emp.hireDate)}</td>
						<td class="col-status">
							<div class="status-display">
								<span
									class="status-badge"
									class:active={emp.status === 'active'}
									class:draft={emp.status === 'draft'}
									class:terminated={emp.status === 'terminated'}
								>
									{EMPLOYEE_STATUS_LABELS[emp.status]}
								</span>
								{#if emp.terminationDate}
									<span class="termination-date">{formatDate(emp.terminationDate)}</span>
								{/if}
							</div>
						</td>
					{:else if activeColumnGroup === 'employment'}
						<td class="col-province">{emp.provinceOfEmployment}</td>
						<td class="col-frequency">{PAY_FREQUENCY_LABELS[emp.payFrequency]}</td>
						<td class="col-type">
							<span class="type-badge">{EMPLOYMENT_TYPE_LABELS[emp.employmentType]}</span>
						</td>
						<td class="col-date">{formatDate(emp.hireDate)}</td>
					{:else if activeColumnGroup === 'compensation'}
						<td class="col-salary money">{formatCompensation(emp)}</td>
						<td class="col-period money">{getPerPeriodAmount(emp)}</td>
						<td class="col-vacation">{(parseFloat(emp.vacationConfig?.vacationRate ?? '0.04') * 100).toFixed(0)}%</td>
						<td class="col-balance money">{formatCurrency(emp.vacationBalance)}</td>
					{:else if activeColumnGroup === 'tax'}
						<td class="col-claim money">{formatCurrency(emp.federalClaimAmount)}</td>
						<td class="col-claim money">{formatCurrency(emp.provincialClaimAmount)}</td>
						<td class="col-exempt">
							<span class="exempt-value" class:yes={emp.isCppExempt}>{emp.isCppExempt ? 'Yes' : 'No'}</span>
						</td>
						<td class="col-exempt">
							<span class="exempt-value" class:yes={emp.isEiExempt}>{emp.isEiExempt ? 'Yes' : 'No'}</span>
						</td>
					{:else if activeColumnGroup === 'deductions'}
						<td class="col-amount money">{formatCurrency(emp.rrspPerPeriod)}</td>
						<td class="col-amount money">{formatCurrency(emp.unionDuesPerPeriod)}</td>
					{/if}

					<td class="col-actions">
						<button class="action-btn" title="View details">
							<i class="fas fa-chevron-right"></i>
						</button>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>

	{#if employees.length === 0}
		<div class="empty-state">
			<i class="fas fa-users"></i>
			<p>No employees found</p>
		</div>
	{/if}
</div>

<style>
	/* Column Group Tabs */
	.column-group-tabs {
		display: flex;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-200);
		padding-bottom: var(--spacing-3);
	}

	.column-tab {
		padding: var(--spacing-2) var(--spacing-4);
		border: none;
		background: transparent;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		cursor: pointer;
		border-bottom: 2px solid transparent;
		margin-bottom: -13px;
		transition: var(--transition-fast);
	}

	.column-tab:hover {
		color: var(--color-primary-600);
	}

	.column-tab.active {
		color: var(--color-primary-600);
		border-bottom-color: var(--color-primary-500);
	}

	/* Table Container */
	.table-container {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	/* Data Table */
	.data-table {
		width: 100%;
		border-collapse: collapse;
		font-size: var(--font-size-body-content);
	}

	.data-table th {
		text-align: left;
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-50);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		border-bottom: 1px solid var(--color-surface-200);
		white-space: nowrap;
	}

	/* Header with tooltip */
	.header-with-tooltip {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	.tooltip-trigger {
		color: var(--color-surface-400);
		font-size: 0.75rem;
		cursor: help;
		transition: var(--transition-fast);
	}

	.tooltip-trigger:hover {
		color: var(--color-primary-500);
	}

	.data-table td {
		padding: var(--spacing-3) var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-100);
		vertical-align: middle;
	}

	.data-table tbody tr {
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.data-table tbody tr:hover td {
		background: var(--color-surface-50);
	}

	.data-table tbody tr.terminated td {
		opacity: 0.6;
	}

	.data-table tbody tr.selected td {
		background: var(--color-primary-50);
	}

	/* Column widths */
	.col-checkbox {
		width: 40px;
		text-align: center;
	}

	.col-name {
		min-width: 200px;
	}

	.col-actions {
		width: 50px;
		text-align: right;
	}

	/* Employee Cell */
	.employee-cell {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.employee-cell .name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	/* Money columns */
	.money {
		font-family: monospace;
	}

	/* Badges */
	.type-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
	}

	.status-display {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: var(--spacing-1);
	}

	.status-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-3);
		background: var(--color-surface-100);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
	}

	.status-badge.active {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge.draft {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.status-badge.terminated {
		background: var(--color-surface-200);
		color: var(--color-surface-600);
	}

	.termination-date {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Exempt Value */
	.exempt-value {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.exempt-value.yes {
		color: var(--color-success-700);
	}

	/* Action Button */
	.action-btn {
		padding: var(--spacing-2);
		border: none;
		background: transparent;
		color: var(--color-surface-400);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.action-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-10);
		color: var(--color-surface-400);
	}

	.empty-state i {
		font-size: 48px;
		margin-bottom: var(--spacing-4);
	}

	.empty-state p {
		font-size: var(--font-size-body-content);
		margin: 0;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.column-group-tabs {
			overflow-x: auto;
			flex-wrap: nowrap;
			-webkit-overflow-scrolling: touch;
		}

		.table-container {
			overflow-x: auto;
		}

		.data-table {
			min-width: 700px;
		}
	}
</style>
