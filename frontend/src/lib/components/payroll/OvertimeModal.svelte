<script lang="ts">
	import type { OvertimeEntry, PayrollRecord } from '$lib/types/payroll';
	import { Avatar } from '$lib/components/shared';

	interface OvertimeRow {
		rowId: string;
		employeeId: string;
		employeeName: string;
		hours: number;
		hourlyRate: number;
		multiplier: number;
	}

	interface Props {
		payrollRecords: PayrollRecord[];
		periodStart: string;
		periodEnd: string;
		existingOvertimeEntries?: OvertimeEntry[];
		onClose: () => void;
		onSave: (entries: OvertimeEntry[]) => void;
	}

	let {
		payrollRecords,
		periodStart,
		periodEnd,
		existingOvertimeEntries = [],
		onClose,
		onSave
	}: Props = $props();

	// Default overtime multiplier
	const DEFAULT_MULTIPLIER = 1.5;

	// Available employees derived from payrollRecords
	const availableEmployees = $derived(
		payrollRecords.map((r) => ({
			id: r.employeeId,
			name: r.employeeName,
			hourlyRate: r.grossRegular / 80 // Approximate hourly rate (biweekly)
		}))
	);

	// State: overtime rows
	let overtimeRows = $state<OvertimeRow[]>([]);
	let initialized = $state(false);

	// Initialize from existing entries
	$effect(() => {
		if (initialized) return;

		if (existingOvertimeEntries.length > 0) {
			overtimeRows = existingOvertimeEntries.map((entry) => {
				const emp = availableEmployees.find((e) => e.id === entry.employeeId);
				return {
					rowId: entry.id || crypto.randomUUID(),
					employeeId: entry.employeeId,
					employeeName: entry.employeeName,
					hours: entry.hours,
					hourlyRate: entry.hourlyRate || emp?.hourlyRate || 0,
					multiplier: entry.multiplier || DEFAULT_MULTIPLIER
				};
			});
			initialized = true;
		}
	});

	// Combobox state
	let openDropdowns = $state<Set<string>>(new Set());
	let searchTexts = $state<Map<string, string>>(new Map());

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
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		}).format(amount);
	}

	// Calculate overtime pay for a row
	function calculateOvertimePay(row: OvertimeRow): number {
		return row.hours * row.hourlyRate * row.multiplier;
	}

	// Row management
	function addRow() {
		const newRow: OvertimeRow = {
			rowId: crypto.randomUUID(),
			employeeId: '',
			employeeName: '',
			hours: 0,
			hourlyRate: 0,
			multiplier: DEFAULT_MULTIPLIER
		};
		overtimeRows = [...overtimeRows, newRow];
	}

	function removeRow(rowId: string) {
		overtimeRows = overtimeRows.filter((r) => r.rowId !== rowId);
		// Clean up combobox state
		openDropdowns.delete(rowId);
		searchTexts.delete(rowId);
	}

	function updateRow(rowId: string, updates: Partial<OvertimeRow>) {
		const idx = overtimeRows.findIndex((r) => r.rowId === rowId);
		if (idx !== -1) {
			overtimeRows[idx] = { ...overtimeRows[idx], ...updates };
			overtimeRows = [...overtimeRows];
		}
	}

	// Combobox helpers
	function getExcludedIds(currentRowId: string): Set<string> {
		const excluded = new Set<string>();
		for (const row of overtimeRows) {
			if (row.rowId !== currentRowId && row.employeeId) {
				excluded.add(row.employeeId);
			}
		}
		return excluded;
	}

	function getFilteredEmployees(
		rowId: string
	): { id: string; name: string; hourlyRate: number }[] {
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
		employee: { id: string; name: string; hourlyRate: number }
	) {
		updateRow(rowId, {
			employeeId: employee.id,
			employeeName: employee.name,
			hourlyRate: employee.hourlyRate
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

	function handleHoursChange(rowId: string, value: string) {
		const hours = parseFloat(value) || 0;
		updateRow(rowId, { hours });
	}

	// Save handler
	function handleSave() {
		const entries: OvertimeEntry[] = [];

		for (const row of overtimeRows) {
			if (row.employeeId && row.hours > 0) {
				entries.push({
					id: row.rowId,
					employeeId: row.employeeId,
					employeeName: row.employeeName,
					hours: row.hours,
					hourlyRate: row.hourlyRate,
					multiplier: row.multiplier,
					overtimePay: calculateOvertimePay(row)
				});
			}
		}

		onSave(entries);
	}

	// Calculate total overtime
	const totalOvertimePay = $derived(
		overtimeRows.reduce((sum, row) => sum + calculateOvertimePay(row), 0)
	);

	const totalOvertimeHours = $derived(
		overtimeRows.reduce((sum, row) => sum + (row.employeeId ? row.hours : 0), 0)
	);
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
			<h2>Overtime Hours - {formatDateRange(periodStart, periodEnd)}</h2>
			<button class="close-btn" onclick={onClose} aria-label="Close modal">
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-content">
			<p class="modal-description">Record overtime hours worked during this pay period:</p>

			{#if overtimeRows.length > 0}
				<table class="overtime-table">
					<thead>
						<tr>
							<th class="col-employee">Employee</th>
							<th class="col-hours">Hours</th>
							<th class="col-rate">Rate</th>
							<th class="col-pay">Overtime Pay</th>
							<th class="col-actions"></th>
						</tr>
					</thead>
					<tbody>
						{#each overtimeRows as row (row.rowId)}
							{@const isDropdownOpen = openDropdowns.has(row.rowId)}
							{@const filteredEmployees = getFilteredEmployees(row.rowId)}
							{@const displayValue = searchTexts.get(row.rowId) ?? row.employeeName}
							{@const overtimePay = calculateOvertimePay(row)}
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
								<td class="col-hours">
									<input
										type="number"
										class="hours-input"
										data-hours-input={row.rowId}
										placeholder="0.0"
										min="0"
										max="40"
										step="0.5"
										value={row.hours || ''}
										disabled={!row.employeeId}
										oninput={(e) => handleHoursChange(row.rowId, e.currentTarget.value)}
									/>
								</td>
								<td class="col-rate">
									{#if row.employeeId}
										<span class="rate-display">
											{formatCurrency(row.hourlyRate)} <span class="multiplier">×{row.multiplier}</span>
										</span>
									{:else}
										<span class="rate-placeholder">-</span>
									{/if}
								</td>
								<td class="col-pay">
									{#if row.employeeId && row.hours > 0}
										<span class="pay-amount">{formatCurrency(overtimePay)}</span>
									{:else}
										<span class="pay-placeholder">-</span>
									{/if}
								</td>
								<td class="col-actions">
									<button
										class="delete-btn"
										onclick={() => removeRow(row.rowId)}
										aria-label="Remove overtime entry"
									>
										<i class="fas fa-trash"></i>
									</button>
								</td>
							</tr>
						{/each}
					</tbody>
					{#if overtimeRows.length > 0 && totalOvertimeHours > 0}
						<tfoot>
							<tr class="total-row">
								<td class="col-employee"><strong>Total</strong></td>
								<td class="col-hours"><strong>{totalOvertimeHours}h</strong></td>
								<td class="col-rate"></td>
								<td class="col-pay"><strong>{formatCurrency(totalOvertimePay)}</strong></td>
								<td class="col-actions"></td>
							</tr>
						</tfoot>
					{/if}
				</table>
			{/if}

			<button class="add-row-btn" onclick={addRow}>
				<i class="fas fa-plus"></i>
				<span>Add Row</span>
			</button>

			<div class="modal-info">
				<i class="fas fa-info-circle"></i>
				<span>
					Overtime is calculated at <strong>1.5× regular hourly rate</strong> per Employment Standards Act requirements.
				</span>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" onclick={onClose}>Cancel</button>
			<button class="btn-primary" onclick={handleSave}>Save Overtime</button>
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
		max-width: 700px;
		max-height: 90vh;
		display: flex;
		flex-direction: column;
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
	.overtime-table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 0;
	}

	.overtime-table th {
		text-align: left;
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		border-bottom: 1px solid var(--color-surface-200);
	}

	.overtime-table td {
		padding: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-100);
		vertical-align: middle;
	}

	.col-employee {
		width: 35%;
	}

	.col-hours {
		width: 15%;
	}

	.col-rate {
		width: 20%;
	}

	.col-pay {
		width: 20%;
	}

	.col-actions {
		width: 10%;
		text-align: right;
	}

	/* Total row */
	.total-row {
		background: var(--color-surface-50);
	}

	.total-row td {
		border-bottom: none;
		padding-top: var(--spacing-4);
		padding-bottom: var(--spacing-4);
	}

	/* Rate display */
	.rate-display {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.multiplier {
		color: var(--color-primary-600);
		font-weight: var(--font-weight-medium);
	}

	.rate-placeholder,
	.pay-placeholder {
		color: var(--color-surface-400);
	}

	.pay-amount {
		font-weight: var(--font-weight-medium);
		color: var(--color-success-600);
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
