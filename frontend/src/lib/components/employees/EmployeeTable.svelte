<script lang="ts">
	import type { Employee, ColumnGroup, EmployeeStatus } from '$lib/types/employee';
	import {
		PROVINCE_LABELS,
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		COLUMN_GROUP_LABELS,
		EMPLOYEE_STATUS_LABELS,
		calculateYearsOfService,
		canEditVacationBalance
	} from '$lib/types/employee';
	import { Avatar } from '$lib/components/shared';

	interface Props {
		employees: Employee[];
		selectedIds: Set<string>;
		activeColumnGroup: ColumnGroup;
		showSINMap: Record<string, boolean>;
		editingCell: { id: string; field: string } | null;
		onToggleSelectAll: () => void;
		onToggleSelect: (id: string) => void;
		onToggleSIN: (id: string) => void;
		onStartEdit: (id: string, field: string) => void;
		onStopEdit: () => void;
		onOpenDetails: (id: string) => void;
		onAddNewRow: () => void;
		onToggleCompensationType: (id: string) => void;
		onDeleteEmployee: (id: string) => void;
	}

	let {
		employees,
		selectedIds,
		activeColumnGroup,
		showSINMap,
		editingCell,
		onToggleSelectAll,
		onToggleSelect,
		onToggleSIN,
		onStartEdit,
		onStopEdit,
		onOpenDetails,
		onAddNewRow,
		onToggleCompensationType,
		onDeleteEmployee
	}: Props = $props();

	// Helpers
	function maskSIN(sin: string): string {
		const digits = sin.replace(/\D/g, '');
		return `***-***-${digits.slice(6)}`;
	}

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

	function isDraft(emp: Employee): boolean {
		return emp.status === 'draft';
	}

	function isNewRow(emp: Employee): boolean {
		return emp.id.startsWith('new-');
	}

	function getFullName(emp: Employee): string {
		return `${emp.firstName} ${emp.lastName}`;
	}

	function getCompensationType(emp: Employee): 'salary' | 'hourly' {
		// Check if hourlyRate is set (not null/undefined)
		return emp.hourlyRate !== null && emp.hourlyRate !== undefined ? 'hourly' : 'salary';
	}

	function getCompensationValue(emp: Employee): number {
		if (emp.hourlyRate !== null && emp.hourlyRate !== undefined) {
			return emp.hourlyRate;
		}
		return emp.annualSalary || 0;
	}

	const COMPENSATION_TYPE_LABELS = {
		salary: 'Salary',
		hourly: 'Hourly'
	};

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

<!-- Excel-like Table -->
<div class="table-container">
	<table class="excel-table">
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
					<th class="col-sin">SIN</th>
					<th class="col-email">Email</th>
					<th class="col-status">Status</th>
				{:else if activeColumnGroup === 'employment'}
					<th class="col-province">
						<span class="header-with-tooltip">
							Province
							<span class="tooltip-trigger" title="Province of Employment determines provincial tax rates. Use the province where the employee primarily works, not the company location.">
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
							<span class="tooltip-trigger" title="Percentage of gross pay accrued as vacation pay. Common rates: 4% (2 weeks), 6% (3 weeks), 8% (4 weeks). Accrued each pay period.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-balance">
						<span class="header-with-tooltip">
							Vac Balance
							<span class="tooltip-trigger" title="Accumulated vacation pay balance. Updated automatically through payroll. For active employees, use 'Adjust Balance' in details for corrections.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
				{:else if activeColumnGroup === 'tax'}
					<th class="col-claim">
						<span class="header-with-tooltip">
							Fed Claim
							<span class="tooltip-trigger" title="Federal Basic Personal Amount from TD1 form. Reduces federal tax withheld. 2024 default: $15,705. Enter $0 if employee claims no credits.">
								<i class="fas fa-info-circle"></i>
							</span>
						</span>
					</th>
					<th class="col-claim">
						<span class="header-with-tooltip">
							Prov Claim
							<span class="tooltip-trigger" title="Provincial Basic Personal Amount from TD1 provincial form. Varies by province. Reduces provincial tax withheld.">
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
							<span class="tooltip-trigger" title="RRSP contribution deducted each pay period. Reduces taxable income. Ensure total annual contributions don't exceed employee's RRSP room.">
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

				<th class="col-actions">Actions</th>
			</tr>
		</thead>
		<tbody>
			{#each employees as emp (emp.id)}
				<tr class:terminated={emp.status === 'terminated'} class:draft={emp.status === 'draft'} class:selected={selectedIds.has(emp.id)}>
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
							<div class="name-group">
								{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'firstName')}
									<div class="name-edit-row">
										<input
											type="text"
											class="inline-edit"
											placeholder="First name"
											value={emp.firstName}
											onblur={() => !isNewRow(emp) && onStopEdit()}
											autofocus
										/>
										<input
											type="text"
											class="inline-edit"
											placeholder="Last name"
											value={emp.lastName}
											onblur={() => !isNewRow(emp) && onStopEdit()}
										/>
									</div>
								{:else}
									<span
										class="name"
										ondblclick={() => onStartEdit(emp.id, 'firstName')}
										role="button"
										tabindex="0"
									>
										{emp.firstName || emp.lastName ? `${emp.firstName} ${emp.lastName}` : 'Enter name...'}
									</span>
								{/if}
							</div>
						</div>
					</td>

					{#if activeColumnGroup === 'personal'}
						<td class="col-sin">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'sin')}
								<input
									type="text"
									class="inline-edit"
									placeholder="123-456-789"
									value={emp.sin}
									onblur={() => !isNewRow(emp) && onStopEdit()}
									autofocus
								/>
							{:else if emp.sin}
								<button
									class="sin-toggle"
									onclick={() => onToggleSIN(emp.id)}
									ondblclick={() => onStartEdit(emp.id, 'sin')}
								>
									{showSINMap[emp.id] ? emp.sin : maskSIN(emp.sin)}
									<i class="fas" class:fa-eye={!showSINMap[emp.id]} class:fa-eye-slash={showSINMap[emp.id]}></i>
								</button>
							{:else}
								<span
									class="editable placeholder"
									ondblclick={() => onStartEdit(emp.id, 'sin')}
									role="button"
									tabindex="0"
								>
									Enter SIN...
								</span>
							{/if}
						</td>
						<td class="col-email">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'email')}
								<input
									type="email"
									class="inline-edit"
									placeholder="email@example.com"
									value={emp.email}
									onblur={() => !isNewRow(emp) && onStopEdit()}
									autofocus
								/>
							{:else}
								<span
									class="editable"
									class:placeholder={!emp.email}
									ondblclick={() => onStartEdit(emp.id, 'email')}
									role="button"
									tabindex="0"
								>
									{emp.email || 'Enter email...'}
								</span>
							{/if}
						</td>
						<td class="col-status">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'status')}
								<div class="status-edit-group">
									<select
										class="inline-select status-select"
										value={emp.status}
										onblur={() => !isNewRow(emp) && emp.status !== 'terminated' && onStopEdit()}
									>
										<!-- Draft is a system state, not user-selectable -->
										<option value="active">Active</option>
										<option value="terminated">Terminated</option>
									</select>
									{#if emp.status === 'terminated'}
										<input
											type="date"
											class="inline-edit termination-date"
											value={emp.terminationDate || ''}
											placeholder="Termination date"
											onblur={() => !isNewRow(emp) && onStopEdit()}
										/>
									{/if}
								</div>
							{:else}
								<div class="status-display-group">
									<span
										class="status-badge"
										class:active={emp.status === 'active'}
										class:draft={emp.status === 'draft'}
										ondblclick={() => onStartEdit(emp.id, 'status')}
										role="button"
										tabindex="0"
									>
										{EMPLOYEE_STATUS_LABELS[emp.status]}
									</span>
									{#if emp.terminationDate}
										<span class="termination-date-display">
											{formatDate(emp.terminationDate)}
										</span>
									{/if}
								</div>
							{/if}
						</td>
					{:else if activeColumnGroup === 'employment'}
						<td class="col-province">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'province')}
								<select
									class="inline-select"
									value={emp.provinceOfEmployment}
									onblur={() => !isNewRow(emp) && onStopEdit()}
								>
									{#each Object.entries(PROVINCE_LABELS) as [code, name]}
										<option value={code}>{code}</option>
									{/each}
								</select>
							{:else}
								<span
									class="editable"
									ondblclick={() => onStartEdit(emp.id, 'province')}
									role="button"
									tabindex="0"
								>
									{emp.provinceOfEmployment}
								</span>
							{/if}
						</td>
						<td class="col-frequency">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'payFrequency')}
								<select
									class="inline-select"
									value={emp.payFrequency}
									onblur={() => !isNewRow(emp) && onStopEdit()}
								>
									{#each Object.entries(PAY_FREQUENCY_LABELS) as [code, name]}
										<option value={code}>{name}</option>
									{/each}
								</select>
							{:else}
								<span
									class="editable"
									ondblclick={() => onStartEdit(emp.id, 'payFrequency')}
									role="button"
									tabindex="0"
								>
									{PAY_FREQUENCY_LABELS[emp.payFrequency]}
								</span>
							{/if}
						</td>
						<td class="col-type">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'employmentType')}
								<select
									class="inline-select"
									value={emp.employmentType}
									onblur={() => !isNewRow(emp) && onStopEdit()}
								>
									{#each Object.entries(EMPLOYMENT_TYPE_LABELS) as [code, name]}
										<option value={code}>{name}</option>
									{/each}
								</select>
							{:else}
								<span
									class="type-badge"
									ondblclick={() => onStartEdit(emp.id, 'employmentType')}
									role="button"
									tabindex="0"
								>
									{EMPLOYMENT_TYPE_LABELS[emp.employmentType]}
								</span>
							{/if}
						</td>
						<td class="col-date">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'hireDate')}
								<input
									type="date"
									class="inline-edit"
									value={emp.hireDate}
									onblur={() => !isNewRow(emp) && onStopEdit()}
								/>
							{:else}
								<span
									class="editable"
									ondblclick={() => onStartEdit(emp.id, 'hireDate')}
									role="button"
									tabindex="0"
								>
									{formatDate(emp.hireDate)}
								</span>
							{/if}
						</td>
					{:else if activeColumnGroup === 'compensation'}
						<td class="col-salary">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'salary')}
								<div class="salary-input-compact">
									<input
										type="number"
										class="inline-edit money"
										placeholder={getCompensationType(emp) === 'hourly' ? '0.00' : '0'}
										step={getCompensationType(emp) === 'hourly' ? '0.01' : '1'}
										value={getCompensationValue(emp)}
										onblur={() => !isNewRow(emp) && onStopEdit()}
										autofocus
									/>
									<button
										type="button"
										class="unit-toggle"
										class:hourly={getCompensationType(emp) === 'hourly'}
										title="Click to switch between salary and hourly"
										onclick={() => onToggleCompensationType(emp.id)}
									>
										{getCompensationType(emp) === 'hourly' ? '/hr' : '/yr'}
									</button>
								</div>
							{:else}
								<span
									class="editable money"
									class:placeholder={!emp.annualSalary && !emp.hourlyRate}
									ondblclick={() => onStartEdit(emp.id, 'salary')}
									role="button"
									tabindex="0"
								>
									{emp.annualSalary || emp.hourlyRate ? formatCompensation(emp) : 'Enter salary...'}
								</span>
							{/if}
						</td>
						<td class="col-period money">
							{getPerPeriodAmount(emp)}
						</td>
						<td class="col-vacation">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'vacationRate')}
								<select
									class="inline-select"
									value={emp.vacationConfig.vacationRate}
									onblur={() => !isNewRow(emp) && onStopEdit()}
								>
									<option value="0.04">4%</option>
									<option value="0.06">6%</option>
									<option value="0.08">8%</option>
								</select>
							{:else}
								<span
									class="editable"
									ondblclick={() => onStartEdit(emp.id, 'vacationRate')}
									role="button"
									tabindex="0"
								>
									{(parseFloat(emp.vacationConfig.vacationRate) * 100).toFixed(0)}%
								</span>
							{/if}
						</td>
						<td class="col-balance">
							{#if canEditVacationBalance(emp) && (isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'vacationBalance'))}
								<!-- Editable only for new/draft employees -->
								<input
									type="number"
									class="inline-edit money"
									placeholder="0"
									value={emp.vacationBalance}
									onblur={() => !isNewRow(emp) && onStopEdit()}
									autofocus
								/>
							{:else if canEditVacationBalance(emp)}
								<!-- Draft employee - can double-click to edit -->
								<span
									class="editable money"
									ondblclick={() => onStartEdit(emp.id, 'vacationBalance')}
									role="button"
									tabindex="0"
								>
									{formatCurrency(emp.vacationBalance)}
								</span>
							{:else}
								<!-- Active/terminated employee - read-only with tooltip -->
								<span
									class="money readonly"
									title="Balance is managed by payroll. Use 'Adjust Balance' in employee details for corrections."
								>
									{formatCurrency(emp.vacationBalance)}
								</span>
							{/if}
						</td>
					{:else if activeColumnGroup === 'tax'}
						<td class="col-claim">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'federalClaim')}
								<input
									type="number"
									class="inline-edit money"
									placeholder="16129"
									value={emp.federalClaimAmount || 0}
									onblur={() => !isNewRow(emp) && onStopEdit()}
									autofocus
								/>
							{:else}
								<span class="editable money" ondblclick={() => onStartEdit(emp.id, 'federalClaim')} role="button" tabindex="0">
									{formatCurrency(emp.federalClaimAmount)}
								</span>
							{/if}
						</td>
						<td class="col-claim">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'provincialClaim')}
								<input
									type="number"
									class="inline-edit money"
									placeholder="12399"
									value={emp.provincialClaimAmount || 0}
									onblur={() => !isNewRow(emp) && onStopEdit()}
									autofocus
								/>
							{:else}
								<span class="editable money" ondblclick={() => onStartEdit(emp.id, 'provincialClaim')} role="button" tabindex="0">
									{formatCurrency(emp.provincialClaimAmount)}
								</span>
							{/if}
						</td>
						<td class="col-exempt">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'cppExempt')}
								<input
									type="checkbox"
									checked={emp.isCppExempt}
									class="checkbox editing"
									onblur={() => !isNewRow(emp) && onStopEdit()}
								/>
							{:else}
								<span
									class="editable exempt-value"
									class:exempt-yes={emp.isCppExempt}
									ondblclick={() => onStartEdit(emp.id, 'cppExempt')}
									role="button"
									tabindex="0"
								>
									{emp.isCppExempt ? 'Yes' : 'No'}
								</span>
							{/if}
						</td>
						<td class="col-exempt">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'eiExempt')}
								<input
									type="checkbox"
									checked={emp.isEiExempt}
									class="checkbox editing"
									onblur={() => !isNewRow(emp) && onStopEdit()}
								/>
							{:else}
								<span
									class="editable exempt-value"
									class:exempt-yes={emp.isEiExempt}
									ondblclick={() => onStartEdit(emp.id, 'eiExempt')}
									role="button"
									tabindex="0"
								>
									{emp.isEiExempt ? 'Yes' : 'No'}
								</span>
							{/if}
						</td>
					{:else if activeColumnGroup === 'deductions'}
						<td class="col-amount">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'rrsp')}
								<input
									type="number"
									class="inline-edit money"
									placeholder="0"
									value={emp.rrspPerPeriod || 0}
									onblur={() => !isNewRow(emp) && onStopEdit()}
									autofocus
								/>
							{:else}
								<span class="editable money" ondblclick={() => onStartEdit(emp.id, 'rrsp')} role="button" tabindex="0">
									{formatCurrency(emp.rrspPerPeriod)}
								</span>
							{/if}
						</td>
						<td class="col-amount">
							{#if isNewRow(emp) || (editingCell?.id === emp.id && editingCell?.field === 'unionDues')}
								<input
									type="number"
									class="inline-edit money"
									placeholder="0"
									value={emp.unionDuesPerPeriod || 0}
									onblur={() => !isNewRow(emp) && onStopEdit()}
									autofocus
								/>
							{:else}
								<span class="editable money" ondblclick={() => onStartEdit(emp.id, 'unionDues')} role="button" tabindex="0">
									{formatCurrency(emp.unionDuesPerPeriod)}
								</span>
							{/if}
						</td>
					{/if}

					<td class="col-actions">
						{#if isDraft(emp)}
							<button class="action-btn delete-btn" onclick={() => onDeleteEmployee(emp.id)} title="Delete employee">
								<i class="fas fa-trash-alt"></i>
							</button>
						{/if}
						<button class="action-btn" onclick={() => onOpenDetails(emp.id)} title="View details">
							<i class="fas fa-chevron-right"></i>
						</button>
					</td>
				</tr>
			{/each}
		</tbody>
	</table>

	<!-- Add Row Button -->
	<button class="add-row-btn" onclick={onAddNewRow}>
		<i class="fas fa-plus"></i>
		<span>Add Employee</span>
	</button>
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

	/* Excel-like Table */
	.excel-table {
		width: 100%;
		border-collapse: collapse;
		font-size: var(--font-size-body-content);
	}

	.excel-table th {
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

	.excel-table td {
		padding: var(--spacing-2) var(--spacing-4);
		border-bottom: 1px solid var(--color-surface-100);
		vertical-align: middle;
	}

	.excel-table tr:hover td {
		background: var(--color-surface-50);
	}

	.excel-table tr.terminated td {
		opacity: 0.6;
	}

	.excel-table tr.selected td {
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
		width: 70px;
	}

	/* Employee Cell */
	.employee-cell {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.name-group .name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		cursor: text;
	}

	.name-edit-row {
		display: flex;
		gap: var(--spacing-2);
	}

	/* Salary Input Compact */
	.salary-input-compact {
		display: inline-flex;
		align-items: center;
		border: 1px solid var(--color-primary-400);
		border-radius: var(--radius-sm);
		overflow: hidden;
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.salary-input-compact .inline-edit {
		border: none;
		border-radius: 0;
		box-shadow: none;
		width: 80px;
		padding: var(--spacing-1) var(--spacing-2);
	}

	.salary-input-compact .inline-edit:focus {
		box-shadow: none;
	}

	.unit-toggle {
		padding: var(--spacing-1) var(--spacing-2);
		border: none;
		border-left: 1px solid var(--color-surface-200);
		background: var(--color-surface-50);
		color: var(--color-surface-600);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.unit-toggle:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	.unit-toggle.hourly {
		background: var(--color-primary-50);
		color: var(--color-primary-600);
	}

	.name-edit-row .inline-edit {
		width: 120px;
	}

	/* Editable cells */
	.editable {
		cursor: text;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-sm);
		transition: var(--transition-fast);
	}

	.editable:hover {
		background: var(--color-surface-100);
	}

	.editable.placeholder {
		color: var(--color-surface-400);
		font-style: italic;
	}

	.money {
		font-family: monospace;
	}

	.readonly {
		color: var(--color-surface-500);
		cursor: not-allowed;
	}

	.readonly:hover {
		background: transparent;
	}

	.inline-edit {
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-primary-400);
		border-radius: var(--radius-sm);
		font-size: inherit;
		outline: none;
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.inline-select {
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-sm);
		font-size: inherit;
		background: transparent;
		cursor: pointer;
	}

	.inline-select:hover {
		border-color: var(--color-primary-400);
	}

	/* SIN Toggle */
	.sin-toggle {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-1) var(--spacing-2);
		border: none;
		background: transparent;
		font-family: monospace;
		font-size: inherit;
		color: var(--color-surface-700);
		cursor: pointer;
		border-radius: var(--radius-sm);
		transition: var(--transition-fast);
	}

	.sin-toggle:hover {
		background: var(--color-surface-100);
	}

	.sin-toggle i {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-400);
	}

	/* Badges */
	.type-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.type-badge:hover {
		opacity: 0.8;
	}

	.status-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-3);
		background: var(--color-surface-100);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.status-badge:hover {
		opacity: 0.8;
	}

	.status-badge.active {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge.draft {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.status-select {
		padding: var(--spacing-1) var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
	}

	/* Status Edit Group */
	.status-edit-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.termination-date {
		font-size: var(--font-size-auxiliary-text);
		padding: var(--spacing-1) var(--spacing-2);
	}

	/* Status Display Group */
	.status-display-group {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: var(--spacing-1);
	}

	.termination-date-display {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Checkbox */
	.checkbox {
		width: 16px;
		height: 16px;
		cursor: pointer;
	}

	.checkbox:disabled {
		cursor: default;
		opacity: 0.7;
	}

	.checkbox:disabled:hover {
		cursor: text;
	}

	.checkbox.editing {
		outline: 2px solid var(--color-primary-400);
		outline-offset: 2px;
	}

	/* Exempt Value Display */
	.exempt-value {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.exempt-value.exempt-yes {
		color: var(--color-success-700);
	}

	/* Action Button */
	td.col-actions {
		display: flex;
		gap: var(--spacing-1);
		justify-content: flex-end;
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

	.action-btn.delete-btn:hover {
		background: var(--color-error-50);
		color: var(--color-error-600);
	}

	/* Add Row Button */
	.add-row-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		width: 100%;
		padding: var(--spacing-3);
		border: none;
		background: transparent;
		color: var(--color-surface-500);
		font-size: var(--font-size-body-content);
		cursor: pointer;
		border-top: 1px dashed var(--color-surface-200);
		transition: var(--transition-fast);
	}

	.add-row-btn:hover {
		background: var(--color-surface-50);
		color: var(--color-primary-600);
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

		.excel-table {
			min-width: 700px;
		}
	}
</style>
