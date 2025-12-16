<script lang="ts">
	import type { LeaveType, LeaveEntry, PayrollRecord } from '$lib/types/payroll';
	import { LEAVE_TYPE_LABELS } from '$lib/types/payroll';
	import { Avatar } from '$lib/components/shared';

	interface LeaveRow {
		rowId: string;
		employeeId: string;
		employeeName: string;
		leaveType: LeaveType;
		hours: number;
		payRate: number;
		vacationBalanceHours: number;
		vacationBalanceDollars: number;
		sickBalanceHours: number;
	}

	interface Props {
		payrollRecords: PayrollRecord[];
		periodStart: string;
		periodEnd: string;
		existingLeaveEntries?: LeaveEntry[];
		selectedEmployee?: PayrollRecord; // When provided, shows single-employee mode
		onClose: () => void;
		onSave: (entries: LeaveEntry[]) => void;
	}

	let {
		payrollRecords,
		periodStart,
		periodEnd,
		existingLeaveEntries = [],
		selectedEmployee,
		onClose,
		onSave
	}: Props = $props();

	// Single employee mode
	const isSingleEmployeeMode = $derived(!!selectedEmployee);

	// Available employees derived from payrollRecords
	const availableEmployees = $derived(
		payrollRecords.map((r) => ({
			id: r.employeeId,
			name: r.employeeName,
			payRate: r.grossRegular / 80, // Approximate hourly rate (biweekly)
			vacationBalanceHours: r.vacationBalanceHours ?? 80,
			vacationBalanceDollars: r.vacationBalanceDollars ?? 2000,
			sickBalanceHours: r.sickBalanceHours ?? 40
		}))
	);

	// State: leave rows
	let leaveRows = $state<LeaveRow[]>([]);
	let initialized = $state(false);

	// Single employee state (for simplified mode)
	let singleLeaveType = $state<LeaveType>('vacation');
	let singleHours = $state<number>(0);

	// Get employee info for single employee mode
	const singleEmployeeInfo = $derived(() => {
		if (!selectedEmployee) return null;
		const emp = availableEmployees.find((e) => e.id === selectedEmployee.employeeId);
		return {
			id: selectedEmployee.employeeId,
			name: selectedEmployee.employeeName,
			payRate: emp?.payRate ?? selectedEmployee.grossRegular / 80,
			vacationBalanceHours: emp?.vacationBalanceHours ?? 80,
			vacationBalanceDollars: emp?.vacationBalanceDollars ?? 2000,
			sickBalanceHours: emp?.sickBalanceHours ?? 40
		};
	});

	// Initialize from existing entries or selected employee
	$effect(() => {
		if (initialized) return;

		if (isSingleEmployeeMode && selectedEmployee) {
			// Check if there's existing leave for this employee
			const existingForEmployee = existingLeaveEntries.filter(
				(e) => e.employeeId === selectedEmployee.employeeId
			);
			if (existingForEmployee.length > 0) {
				// Use the first entry's type and sum hours
				singleLeaveType = existingForEmployee[0].leaveType;
				singleHours = existingForEmployee.reduce((sum, e) => sum + e.hours, 0);
			}
			initialized = true;
		} else if (existingLeaveEntries.length > 0) {
			leaveRows = existingLeaveEntries.map((entry) => {
				const emp = availableEmployees.find((e) => e.id === entry.employeeId);
				return {
					rowId: entry.id || crypto.randomUUID(),
					employeeId: entry.employeeId,
					employeeName: entry.employeeName,
					leaveType: entry.leaveType,
					hours: entry.hours,
					payRate: entry.payRate,
					vacationBalanceHours: emp?.vacationBalanceHours ?? 80,
					vacationBalanceDollars: emp?.vacationBalanceDollars ?? 2000,
					sickBalanceHours: emp?.sickBalanceHours ?? 40
				};
			});
			initialized = true;
		}
	});

	// Combobox state
	let openDropdowns = $state<Set<string>>(new Set());
	let searchTexts = $state<Map<string, string>>(new Map());

	// Leave type options
	const leaveTypes: LeaveType[] = ['vacation', 'sick'];

	// Helpers
	function formatDateRange(start: string, end: string): string {
		const startDate = new Date(start);
		const endDate = new Date(end);
		return `${startDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' })} - ${endDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' })}`;
	}

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	// Row management
	function addRow() {
		const newRow: LeaveRow = {
			rowId: crypto.randomUUID(),
			employeeId: '',
			employeeName: '',
			leaveType: 'vacation',
			hours: 0,
			payRate: 0,
			vacationBalanceHours: 0,
			vacationBalanceDollars: 0,
			sickBalanceHours: 0
		};
		leaveRows = [...leaveRows, newRow];
	}

	function removeRow(rowId: string) {
		leaveRows = leaveRows.filter((r) => r.rowId !== rowId);
		// Clean up combobox state
		openDropdowns.delete(rowId);
		searchTexts.delete(rowId);
	}

	function updateRow(rowId: string, updates: Partial<LeaveRow>) {
		const idx = leaveRows.findIndex((r) => r.rowId === rowId);
		if (idx !== -1) {
			leaveRows[idx] = { ...leaveRows[idx], ...updates };
			leaveRows = [...leaveRows];
		}
	}

	// Combobox helpers
	function getExcludedIds(currentRowId: string): Set<string> {
		const excluded = new Set<string>();
		for (const row of leaveRows) {
			if (row.rowId !== currentRowId && row.employeeId) {
				excluded.add(row.employeeId);
			}
		}
		return excluded;
	}

	function getFilteredEmployees(
		rowId: string
	): { id: string; name: string; payRate: number; vacationBalanceHours: number; vacationBalanceDollars: number; sickBalanceHours: number }[] {
		const excludedIds = getExcludedIds(rowId);
		const searchText = searchTexts.get(rowId) || '';

		return availableEmployees.filter((emp) => {
			if (excludedIds.has(emp.id)) return false;
			if (searchText && !emp.name.toLowerCase().includes(searchText.toLowerCase())) {
				return false;
			}
			return true;
		});
	}

	function openDropdown(rowId: string) {
		openDropdowns.add(rowId);
		openDropdowns = new Set(openDropdowns);
	}

	function closeDropdown(rowId: string) {
		openDropdowns.delete(rowId);
		openDropdowns = new Set(openDropdowns);
	}

	function handleComboboxBlur(rowId: string) {
		// Delay to allow click on dropdown item
		setTimeout(() => {
			closeDropdown(rowId);
		}, 150);
	}

	function selectEmployee(
		rowId: string,
		employee: {
			id: string;
			name: string;
			payRate: number;
			vacationBalanceHours: number;
			vacationBalanceDollars: number;
			sickBalanceHours: number;
		}
	) {
		updateRow(rowId, {
			employeeId: employee.id,
			employeeName: employee.name,
			payRate: employee.payRate,
			vacationBalanceHours: employee.vacationBalanceHours,
			vacationBalanceDollars: employee.vacationBalanceDollars,
			sickBalanceHours: employee.sickBalanceHours
		});
		searchTexts.set(rowId, employee.name);
		searchTexts = new Map(searchTexts);
		closeDropdown(rowId);

		// Focus hours input after selection
		setTimeout(() => {
			const hoursInput = document.querySelector(
				`input[data-hours-input="${rowId}"]`
			) as HTMLInputElement;
			if (hoursInput) {
				hoursInput.focus();
			}
		}, 50);
	}

	function handleSearchInput(rowId: string, value: string) {
		searchTexts.set(rowId, value);
		searchTexts = new Map(searchTexts);
	}

	function handleLeaveTypeChange(rowId: string, value: string) {
		updateRow(rowId, { leaveType: value as LeaveType });
	}

	function handleHoursChange(rowId: string, value: string) {
		const hours = parseFloat(value) || 0;
		updateRow(rowId, { hours });
	}

	// Balance display
	function getBalanceDisplay(row: LeaveRow): string {
		if (!row.employeeId) return '-';

		if (row.leaveType === 'vacation') {
			const remainingHours = row.vacationBalanceHours - row.hours;
			const remainingDollars = row.vacationBalanceDollars - row.hours * row.payRate;
			return `${remainingHours.toFixed(0)}h (${formatCurrency(remainingDollars)})`;
		} else {
			const remainingHours = row.sickBalanceHours - row.hours;
			return `${remainingHours.toFixed(0)}h remaining`;
		}
	}

	// Single employee balance display
	const singleBalanceDisplay = $derived(() => {
		const emp = singleEmployeeInfo();
		if (!emp) return '-';

		if (singleLeaveType === 'vacation') {
			const remainingHours = emp.vacationBalanceHours - singleHours;
			const remainingDollars = emp.vacationBalanceDollars - singleHours * emp.payRate;
			return {
				before: `${emp.vacationBalanceHours}h (${formatCurrency(emp.vacationBalanceDollars)})`,
				after: `${remainingHours.toFixed(0)}h (${formatCurrency(remainingDollars)})`
			};
		} else {
			const remainingHours = emp.sickBalanceHours - singleHours;
			return {
				before: `${emp.sickBalanceHours}h`,
				after: `${remainingHours.toFixed(0)}h`
			};
		}
	});

	// Save handler
	function handleSave() {
		const entries: LeaveEntry[] = [];

		if (isSingleEmployeeMode && selectedEmployee) {
			// Single employee mode - only save if hours > 0
			const emp = singleEmployeeInfo();
			if (singleHours > 0 && emp) {
				// Keep other employees' existing entries
				const otherEntries = existingLeaveEntries.filter(
					(e) => e.employeeId !== selectedEmployee.employeeId
				);
				entries.push(...otherEntries);

				// Add this employee's entry
				entries.push({
					id: crypto.randomUUID(),
					employeeId: selectedEmployee.employeeId,
					employeeName: selectedEmployee.employeeName,
					leaveType: singleLeaveType,
					hours: singleHours,
					payRate: emp.payRate,
					leavePay: singleHours * emp.payRate
				});
			} else {
				// Hours is 0, remove this employee's leave but keep others
				const otherEntries = existingLeaveEntries.filter(
					(e) => e.employeeId !== selectedEmployee.employeeId
				);
				entries.push(...otherEntries);
			}
		} else {
			// Multi-employee mode
			for (const row of leaveRows) {
				if (row.employeeId && row.hours > 0) {
					entries.push({
						id: row.rowId,
						employeeId: row.employeeId,
						employeeName: row.employeeName,
						leaveType: row.leaveType,
						hours: row.hours,
						payRate: row.payRate,
						leavePay: row.hours * row.payRate
					});
				}
			}
		}

		onSave(entries);
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<div class="modal-overlay" onclick={onClose} role="presentation">
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div
		class="modal"
		onclick={(e) => e.stopPropagation()}
		role="dialog"
		aria-modal="true"
		tabindex="-1"
	>
		<div class="modal-header">
			{#if isSingleEmployeeMode && selectedEmployee}
				<div class="header-with-employee">
					<Avatar name={selectedEmployee.employeeName} size="medium" />
					<div class="header-text">
						<h2>{selectedEmployee.employeeName}</h2>
						<span class="header-subtitle">Record Leave - {formatDateRange(periodStart, periodEnd)}</span>
					</div>
				</div>
			{:else}
				<h2>Leave Hours - {formatDateRange(periodStart, periodEnd)}</h2>
			{/if}
			<button class="close-btn" onclick={onClose} aria-label="Close modal">
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-content">
			{#if isSingleEmployeeMode && selectedEmployee}
				<!-- Single Employee Mode -->
				{@const balanceInfo = singleBalanceDisplay()}
				<div class="single-employee-form">
					<div class="form-row">
						<label class="form-label">Leave Type</label>
						<div class="leave-type-buttons">
							{#each leaveTypes as lt}
								<button
									class="leave-type-btn"
									class:active={singleLeaveType === lt}
									class:vacation={lt === 'vacation'}
									class:sick={lt === 'sick'}
									onclick={() => (singleLeaveType = lt)}
								>
									<span class="type-icon">{LEAVE_TYPE_LABELS[lt].icon}</span>
									<span class="type-label">{LEAVE_TYPE_LABELS[lt].full}</span>
								</button>
							{/each}
						</div>
					</div>

					<div class="form-row">
						<label class="form-label" for="leave-hours">Hours</label>
						<input
							id="leave-hours"
							type="number"
							class="hours-input-large"
							placeholder="0.0"
							min="0"
							max="80"
							step="0.5"
							bind:value={singleHours}
						/>
					</div>

					<div class="balance-card">
						<div class="balance-header">
							<span class="balance-icon">{LEAVE_TYPE_LABELS[singleLeaveType].icon}</span>
							<span class="balance-title">{LEAVE_TYPE_LABELS[singleLeaveType].full} Balance</span>
						</div>
						{#if typeof balanceInfo === 'object'}
							<div class="balance-row">
								<span class="balance-label">Current Balance:</span>
								<span class="balance-value">{balanceInfo.before}</span>
							</div>
							<div class="balance-row">
								<span class="balance-label">After This Leave:</span>
								<span class="balance-value highlight">{balanceInfo.after}</span>
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<!-- Multi-Employee Mode -->
				<p class="modal-description">Record leave taken during this pay period:</p>

				{#if leaveRows.length > 0}
					<table class="leave-table">
						<thead>
							<tr>
								<th class="col-employee">Employee</th>
								<th class="col-type">Leave Type</th>
								<th class="col-hours">Hours</th>
								<th class="col-balance">Balance</th>
								<th class="col-actions"></th>
							</tr>
						</thead>
						<tbody>
							{#each leaveRows as row (row.rowId)}
								{@const isDropdownOpen = openDropdowns.has(row.rowId)}
								{@const filteredEmployees = getFilteredEmployees(row.rowId)}
								{@const displayValue = searchTexts.get(row.rowId) ?? row.employeeName}
								<tr>
									<td class="col-employee">
										<div class="combobox" class:open={isDropdownOpen}>
											<div class="combobox-input-wrapper">
												<input
													type="text"
													class="combobox-input"
													placeholder="Select employee..."
													value={displayValue}
													onfocus={() => openDropdown(row.rowId)}
													onblur={() => handleComboboxBlur(row.rowId)}
													oninput={(e) => handleSearchInput(row.rowId, e.currentTarget.value)}
												/>
												<i class="fas fa-chevron-down combobox-icon"></i>
											</div>

											{#if isDropdownOpen}
												<ul class="combobox-dropdown">
													{#each filteredEmployees as emp}
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<li
															class="combobox-option"
															onmousedown={() => selectEmployee(row.rowId, emp)}
															role="option"
															aria-selected={row.employeeId === emp.id}
															tabindex="-1"
														>
															<Avatar name={emp.name} size="small" />
															<span>{emp.name}</span>
														</li>
													{/each}
													{#if filteredEmployees.length === 0}
														<li class="combobox-no-results">No employees found</li>
													{/if}
												</ul>
											{/if}
										</div>
									</td>
									<td class="col-type">
										<select
											class="type-select"
											value={row.leaveType}
											disabled={!row.employeeId}
											onchange={(e) => handleLeaveTypeChange(row.rowId, e.currentTarget.value)}
										>
											{#each leaveTypes as lt}
												<option value={lt}>
													{LEAVE_TYPE_LABELS[lt].icon}
													{LEAVE_TYPE_LABELS[lt].full}
												</option>
											{/each}
										</select>
									</td>
									<td class="col-hours">
										<input
											type="number"
											class="hours-input"
											data-hours-input={row.rowId}
											placeholder="0.0"
											min="0"
											max="80"
											step="0.5"
											value={row.hours || ''}
											disabled={!row.employeeId}
											oninput={(e) => handleHoursChange(row.rowId, e.currentTarget.value)}
										/>
									</td>
									<td class="col-balance">
										<span class="balance-text">{getBalanceDisplay(row)}</span>
									</td>
									<td class="col-actions">
										<button
											class="delete-btn"
											onclick={() => removeRow(row.rowId)}
											aria-label="Remove leave entry"
										>
											<i class="fas fa-trash"></i>
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				{/if}

				<button class="add-row-btn" onclick={addRow}>
					<i class="fas fa-plus"></i>
					<span>Add Row</span>
				</button>

				<div class="modal-info">
					<i class="fas fa-info-circle"></i>
					<span>
						Leave Types:
						<ul>
							<li><strong>Vacation:</strong> Paid from accrued balance</li>
							<li><strong>Sick:</strong> Paid per provincial requirements</li>
						</ul>
					</span>
				</div>
			{/if}
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" onclick={onClose}>Cancel</button>
			<button class="btn-primary" onclick={handleSave}>Save Leave</button>
		</div>
	</div>
</div>

<style>
	/* Modal */
	.modal-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-4);
	}

	.modal {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-3);
		width: 100%;
		max-width: 750px;
		max-height: 90vh;
		display: flex;
		flex-direction: column;
	}

	/* Single employee mode - smaller modal */
	.modal:has(.single-employee-form) {
		max-width: 450px;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-header h2 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	/* Header with employee avatar */
	.header-with-employee {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.header-text {
		display: flex;
		flex-direction: column;
	}

	.header-text h2 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.header-subtitle {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Single Employee Form */
	.single-employee-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-5);
	}

	.form-row {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.form-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.leave-type-buttons {
		display: flex;
		gap: var(--spacing-3);
	}

	.leave-type-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-4);
		border: 2px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		background: white;
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.leave-type-btn:hover {
		border-color: var(--color-surface-300);
		background: var(--color-surface-50);
	}

	.leave-type-btn.active.vacation {
		border-color: var(--color-info-400, #60a5fa);
		background: var(--color-info-50, #eff6ff);
	}

	.leave-type-btn.active.sick {
		border-color: var(--color-warning-400, #fb923c);
		background: var(--color-warning-50, #fff7ed);
	}

	.type-icon {
		font-size: var(--font-size-title-medium);
	}

	.type-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.hours-input-large {
		width: 100%;
		padding: var(--spacing-4);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-title-medium);
		text-align: center;
		transition: var(--transition-fast);
	}

	.hours-input-large:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	/* Balance Card */
	.balance-card {
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
	}

	.balance-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-3);
		padding-bottom: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.balance-icon {
		font-size: var(--font-size-body-content);
	}

	.balance-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
	}

	.balance-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-2) 0;
	}

	.balance-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.balance-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.balance-value.highlight {
		color: var(--color-primary-600);
		font-weight: var(--font-weight-semibold);
	}

	.close-btn {
		padding: var(--spacing-2);
		border: none;
		background: transparent;
		color: var(--color-surface-400);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.close-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.modal-content {
		flex: 1;
		overflow-y: auto;
		padding: var(--spacing-5);
	}

	.modal-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4);
	}

	/* Table */
	.leave-table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 0;
	}

	.leave-table th {
		text-align: left;
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		border-bottom: 1px solid var(--color-surface-200);
	}

	.leave-table td {
		padding: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-100);
		vertical-align: middle;
	}

	.col-employee {
		width: 35%;
	}

	.col-type {
		width: 25%;
	}

	.col-hours {
		width: 15%;
	}

	.col-balance {
		width: 20%;
	}

	.col-actions {
		width: 5%;
		text-align: right;
	}

	/* Combobox */
	.combobox {
		position: relative;
	}

	.combobox-input-wrapper {
		position: relative;
	}

	.combobox-input {
		width: 100%;
		padding: var(--spacing-2) var(--spacing-3);
		padding-right: var(--spacing-8);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		background: white;
		transition: var(--transition-fast);
	}

	.combobox-input:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.combobox-input::placeholder {
		color: var(--color-surface-400);
	}

	.combobox-icon {
		position: absolute;
		right: var(--spacing-3);
		top: 50%;
		transform: translateY(-50%);
		color: var(--color-surface-400);
		pointer-events: none;
		font-size: var(--font-size-auxiliary-text);
		transition: var(--transition-fast);
	}

	.combobox.open .combobox-icon {
		transform: translateY(-50%) rotate(180deg);
	}

	.combobox-dropdown {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		max-height: 200px;
		overflow-y: auto;
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-md3-1);
		z-index: 10;
		margin-top: var(--spacing-1);
		list-style: none;
		padding: 0;
		margin-bottom: 0;
	}

	.combobox-option {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.combobox-option:hover {
		background: var(--color-surface-50);
	}

	.combobox-no-results {
		padding: var(--spacing-3);
		color: var(--color-surface-500);
		font-size: var(--font-size-body-content);
		text-align: center;
	}

	/* Type Select */
	.type-select {
		width: 100%;
		padding: var(--spacing-2) var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		background: white;
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.type-select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.type-select:disabled {
		background: var(--color-surface-50);
		color: var(--color-surface-400);
		cursor: not-allowed;
	}

	/* Hours Input */
	.hours-input {
		width: 80px;
		padding: var(--spacing-2);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		text-align: center;
		transition: var(--transition-fast);
	}

	.hours-input:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.hours-input:disabled {
		background: var(--color-surface-50);
		color: var(--color-surface-400);
		cursor: not-allowed;
	}

	/* Balance */
	.balance-text {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	/* Delete Button */
	.delete-btn {
		padding: var(--spacing-2);
		border: none;
		background: transparent;
		color: var(--color-surface-400);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.delete-btn:hover {
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

	/* Info Box */
	.modal-info {
		display: flex;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-primary-50);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		margin-top: var(--spacing-4);
	}

	.modal-info i {
		color: var(--color-primary-600);
		margin-top: 2px;
	}

	.modal-info ul {
		margin: var(--spacing-2) 0 0;
		padding-left: var(--spacing-5);
	}

	.modal-info li {
		margin-bottom: var(--spacing-1);
	}

	/* Footer */
	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-5);
		border-top: 1px solid var(--color-surface-100);
	}

	.btn-primary,
	.btn-secondary {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}
</style>
