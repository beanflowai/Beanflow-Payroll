<script lang="ts">
	import { goto } from '$app/navigation';
	import type { Employee, ColumnGroup } from '$lib/types/employee';
	import {
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		COLUMN_GROUP_LABELS,
		EMPLOYEE_STATUS_LABELS,
		PAY_PERIODS_PER_YEAR,
		formatVacationRate
	} from '$lib/types/employee';
	import { Avatar } from '$lib/components/shared';
	import { PortalStatusBadge } from '$lib/components/employees';
	import { formatDate } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		employees: Employee[];
		selectedIds: Set<string>;
		activeColumnGroup: ColumnGroup;
		onToggleSelectAll: () => void;
		onToggleSelect: (id: string) => void;
		onRowClick: (id: string) => void;
		onInviteToPortal?: (employee: Employee) => void;
	}

	let {
		employees,
		selectedIds,
		activeColumnGroup,
		onToggleSelectAll,
		onToggleSelect,
		onRowClick,
		onInviteToPortal
	}: Props = $props();

	// Track which employee's menu is open
	let openMenuId = $state<string | null>(null);

	function toggleMenu(e: MouseEvent, empId: string) {
		e.stopPropagation();
		openMenuId = openMenuId === empId ? null : empId;
	}

	function closeMenu() {
		openMenuId = null;
	}

	function handleMenuAction(e: MouseEvent, action: string, emp: Employee) {
		e.stopPropagation();
		closeMenu();

		switch (action) {
			case 'view':
				onRowClick(emp.id);
				break;
			case 'edit':
				goto(`/employees/${emp.id}`);
				break;
			case 'invite':
				onInviteToPortal?.(emp);
				break;
			case 'resend':
				onInviteToPortal?.(emp);
				break;
		}
	}

	// Close menu when clicking outside
	function handleClickOutside(e: MouseEvent) {
		if (openMenuId && !(e.target as HTMLElement).closest('.action-menu-container')) {
			closeMenu();
		}
	}

	// Helpers
	function formatCurrencyNoDecimals(amount: number | null | undefined): string {
		return formatCurrency(amount, { maximumFractionDigits: 0 });
	}

	function formatCompensation(emp: Employee): string {
		if (emp.hourlyRate) return `$${emp.hourlyRate.toFixed(2)}/hr`;
		if (emp.annualSalary) return `${formatCurrencyNoDecimals(emp.annualSalary)}/yr`;
		return '-';
	}

	function getFullName(emp: Employee): string {
		return `${emp.firstName} ${emp.lastName}`;
	}

	function getPerPeriodAmount(emp: Employee): string {
		if (!emp.annualSalary) return '-';
		const periods = PAY_PERIODS_PER_YEAR[emp.payFrequency] || 26;
		return formatCurrencyNoDecimals(emp.annualSalary / periods);
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

<svelte:window onclick={handleClickOutside} />

<!-- Column Group Tabs -->
<div class="column-group-tabs">
	{#each Object.entries(COLUMN_GROUP_LABELS) as [key, label] (key)}
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
							<span
								class="tooltip-trigger"
								title="Pay Frequency determines how often the employee is paid: Weekly (52/yr), Bi-weekly (26/yr), Semi-monthly (24/yr), or Monthly (12/yr)."
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-portal">
						<span class="header-with-tooltip">
							Portal
							<span
								class="tooltip-trigger"
								title="Employee Self-Service Portal access status. Employees can view paystubs, update personal info, and download T4s."
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-status">Status</th>
				{:else if activeColumnGroup === 'employment'}
					<th class="col-province">
						<span class="header-with-tooltip">
							Province
							<span
								class="tooltip-trigger"
								title="Province of Employment determines provincial tax rates. Use the province where the employee primarily works."
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-frequency">
						<span class="header-with-tooltip">
							Pay Freq
							<span
								class="tooltip-trigger"
								title="Pay Frequency determines how often the employee is paid: Weekly (52/yr), Bi-weekly (26/yr), Semi-monthly (24/yr), or Monthly (12/yr)."
							>
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
							<span
								class="tooltip-trigger"
								title="Gross pay per pay period, calculated as Annual Salary ÷ Pay Periods (Weekly=52, Bi-weekly=26, Semi-monthly=24, Monthly=12)"
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-vacation">
						<span class="header-with-tooltip">
							Vacation Rate
							<span
								class="tooltip-trigger"
								title="Percentage of gross pay accrued as vacation pay. Common rates: 4% (2 weeks), 6% (3 weeks), 8% (4 weeks)."
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-balance">
						<span class="header-with-tooltip">
							Vac Balance
							<span
								class="tooltip-trigger"
								title="Accumulated vacation pay balance. Updated automatically through payroll."
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
				{:else if activeColumnGroup === 'tax'}
					<th class="col-claim">
						<span class="header-with-tooltip">
							Fed Claim
							<span
								class="tooltip-trigger"
								title="Federal Basic Personal Amount from TD1 form. Reduces federal tax withheld. 2025 default: $16,129."
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-claim">
						<span class="header-with-tooltip">
							Prov Claim
							<span
								class="tooltip-trigger"
								title="Provincial Basic Personal Amount from TD1 provincial form. Varies by province."
							>
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-exempt">CPP Exempt</th>
					<th class="col-exempt">EI Exempt</th>
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
						<td class="col-portal">
							<PortalStatusBadge status={emp.portalStatus} />
						</td>
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
						<td class="col-vacation"
							>{emp.vacationConfig?.vacationRate
								? formatVacationRate(emp.vacationConfig.vacationRate)
								: 'Min.'}</td
						>
						<td class="col-balance money">{formatCurrencyNoDecimals(emp.vacationBalance)}</td>
					{:else if activeColumnGroup === 'tax'}
						<td class="col-claim money">{formatCurrencyNoDecimals(emp.federalAdditionalClaims)}</td>
						<td class="col-claim money"
							>{formatCurrencyNoDecimals(emp.provincialAdditionalClaims)}</td
						>
						<td class="col-exempt">
							<span class="exempt-value" class:yes={emp.isCppExempt}
								>{emp.isCppExempt ? 'Yes' : 'No'}</span
							>
						</td>
						<td class="col-exempt">
							<span class="exempt-value" class:yes={emp.isEiExempt}
								>{emp.isEiExempt ? 'Yes' : 'No'}</span
							>
						</td>
					{/if}

					<td class="col-actions">
						<div class="action-menu-container">
							<button class="action-btn" title="Actions" onclick={(e) => toggleMenu(e, emp.id)}>
								<i class="fas fa-ellipsis-v"></i>
							</button>
							{#if openMenuId === emp.id}
								<div class="action-menu">
									<button class="menu-item" onclick={(e) => handleMenuAction(e, 'view', emp)}>
										<i class="fas fa-eye"></i>
										View Details
									</button>
									<button class="menu-item" onclick={(e) => handleMenuAction(e, 'edit', emp)}>
										<i class="fas fa-edit"></i>
										Edit
									</button>
									<div class="menu-divider"></div>
									{#if emp.portalStatus === 'not_set'}
										<button class="menu-item" onclick={(e) => handleMenuAction(e, 'invite', emp)}>
											<i class="fas fa-envelope"></i>
											Invite to Portal
										</button>
									{:else if emp.portalStatus === 'invited'}
										<button class="menu-item" onclick={(e) => handleMenuAction(e, 'resend', emp)}>
											<i class="fas fa-redo"></i>
											Resend Invitation
										</button>
									{/if}
								</div>
							{/if}
						</div>
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
		overflow: visible;
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

	/* Action Menu */
	.action-menu-container {
		position: relative;
	}

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

	.action-menu {
		position: absolute;
		top: 100%;
		right: 0;
		z-index: 50;
		min-width: 180px;
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-2);
		padding: var(--spacing-1) 0;
		margin-top: var(--spacing-1);
	}

	.menu-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		width: 100%;
		padding: var(--spacing-2) var(--spacing-3);
		border: none;
		background: transparent;
		color: var(--color-surface-700);
		font-size: var(--font-size-body-content);
		text-align: left;
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.menu-item:hover {
		background: var(--color-surface-50);
		color: var(--color-primary-600);
	}

	.menu-item i {
		width: 16px;
		text-align: center;
		color: var(--color-surface-500);
	}

	.menu-item:hover i {
		color: var(--color-primary-500);
	}

	.menu-divider {
		height: 1px;
		background: var(--color-surface-100);
		margin: var(--spacing-1) 0;
	}

	/* Portal column */
	.col-portal {
		min-width: 100px;
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
