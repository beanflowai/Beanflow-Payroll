<script lang="ts">
	import type { Holiday, PayrollRecord, HolidayWorkEntry } from '$lib/types/payroll';
	import { Avatar } from '$lib/components/shared';
	import { formatShortDate } from '$lib/utils/dateUtils';

	interface HolidayWorkRow {
		rowId: string;
		employeeId: string;
		employeeName: string;
		hoursWorked: number;
	}

	interface Props {
		holidays: Holiday[];
		payrollRecords: PayrollRecord[];
		periodStart: string;
		periodEnd: string;
		onClose: () => void;
		onSave: (entries: HolidayWorkEntry[]) => void;
	}

	let { holidays, payrollRecords, periodStart, periodEnd, onClose, onSave }: Props = $props();

	// Available employees derived from payrollRecords
	const availableEmployees = $derived(
		payrollRecords.map((r) => ({ id: r.employeeId, name: r.employeeName }))
	);

	// State: Map<holidayDate, HolidayWorkRow[]>
	let holidayWorkState = $state<Map<string, HolidayWorkRow[]>>(new Map());
	let initialized = $state(false);

	// Initialize state when component mounts - load existing data from payrollRecords
	$effect(() => {
		if (!initialized && holidays.length > 0) {
			const initialState = new Map<string, HolidayWorkRow[]>();

			// Initialize empty arrays for each holiday
			for (const holiday of holidays) {
				initialState.set(holiday.date, []);
			}

			// Extract existing holidayWorkEntries from all payroll records
			for (const record of payrollRecords) {
				const existingEntries = record.inputData?.holidayWorkEntries ?? [];
				for (const entry of existingEntries) {
					const rows = initialState.get(entry.holidayDate);
					if (rows) {
						rows.push({
							rowId: crypto.randomUUID(),
							employeeId: record.employeeId,
							employeeName: record.employeeName,
							hoursWorked: entry.hoursWorked
						});
					}
				}
			}

			holidayWorkState = initialState;

			// Also initialize searchTexts for existing rows
			const newSearchTexts = new Map<string, string>();
			for (const [, rows] of initialState) {
				for (const row of rows) {
					if (row.employeeName) {
						newSearchTexts.set(row.rowId, row.employeeName);
					}
				}
			}
			searchTexts = newSearchTexts;

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

	// Row management
	function addRow(holidayDate: string) {
		const rows = holidayWorkState.get(holidayDate) || [];
		const newRow: HolidayWorkRow = {
			rowId: crypto.randomUUID(),
			employeeId: '',
			employeeName: '',
			hoursWorked: 0
		};
		holidayWorkState.set(holidayDate, [...rows, newRow]);
		holidayWorkState = new Map(holidayWorkState);
	}

	function removeRow(holidayDate: string, rowId: string) {
		const rows = holidayWorkState.get(holidayDate) || [];
		holidayWorkState.set(
			holidayDate,
			rows.filter((r) => r.rowId !== rowId)
		);
		holidayWorkState = new Map(holidayWorkState);
		// Clean up combobox state
		openDropdowns.delete(rowId);
		searchTexts.delete(rowId);
	}

	function updateRow(holidayDate: string, rowId: string, updates: Partial<HolidayWorkRow>) {
		const rows = holidayWorkState.get(holidayDate) || [];
		const idx = rows.findIndex((r) => r.rowId === rowId);
		if (idx !== -1) {
			rows[idx] = { ...rows[idx], ...updates };
			holidayWorkState.set(holidayDate, [...rows]);
			holidayWorkState = new Map(holidayWorkState);
		}
	}

	// Combobox helpers
	function getExcludedIds(holidayDate: string, currentRowId: string): Set<string> {
		const rows = holidayWorkState.get(holidayDate) || [];
		const excluded = new Set<string>();
		for (const row of rows) {
			if (row.rowId !== currentRowId && row.employeeId) {
				excluded.add(row.employeeId);
			}
		}
		return excluded;
	}

	function getFilteredEmployees(holidayDate: string, rowId: string): { id: string; name: string }[] {
		const excludedIds = getExcludedIds(holidayDate, rowId);
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
		holidayDate: string,
		rowId: string,
		employee: { id: string; name: string }
	) {
		updateRow(holidayDate, rowId, {
			employeeId: employee.id,
			employeeName: employee.name
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

	function handleHoursChange(holidayDate: string, rowId: string, value: string) {
		const hours = parseFloat(value) || 0;
		updateRow(holidayDate, rowId, { hoursWorked: hours });
	}

	// Save handler
	function handleSave() {
		const entries: HolidayWorkEntry[] = [];

		for (const holiday of holidays) {
			const rows = holidayWorkState.get(holiday.date) || [];
			for (const row of rows) {
				if (row.employeeId && row.hoursWorked > 0) {
					entries.push({
						employeeId: row.employeeId,
						employeeName: row.employeeName,
						holidayDate: holiday.date,
						holidayName: holiday.name,
						hoursWorked: row.hoursWorked
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
	<div class="modal" onclick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" tabindex="-1">
		<div class="modal-header">
			<h2>Holiday Hours - {formatDateRange(periodStart, periodEnd)}</h2>
			<button class="close-btn" onclick={onClose} aria-label="Close modal">
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-content">
			{#each holidays as holiday}
				{@const rows = holidayWorkState.get(holiday.date) || []}
				<div class="holiday-section">
					<div class="holiday-info">
						<i class="fas fa-gift"></i>
						<div>
							<strong>{holiday.name}</strong>
							<span class="holiday-date">{formatShortDate(holiday.date)} - {holiday.province}</span>
						</div>
					</div>
					<p class="holiday-note">
						Regular employees receive holiday pay automatically.
						Record hours for employees who <strong>worked</strong> on this holiday:
					</p>

					{#if rows.length > 0}
						<table class="holiday-table">
							<thead>
								<tr>
									<th>Employee</th>
									<th>Hours Worked</th>
									<th></th>
								</tr>
							</thead>
							<tbody>
								{#each rows as row (row.rowId)}
									{@const isDropdownOpen = openDropdowns.has(row.rowId)}
									{@const filteredEmployees = getFilteredEmployees(holiday.date, row.rowId)}
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
																onmousedown={() => selectEmployee(holiday.date, row.rowId, emp)}
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
												max="24"
												step="0.5"
												value={row.hoursWorked || ''}
												disabled={!row.employeeId}
												oninput={(e) => handleHoursChange(holiday.date, row.rowId, e.currentTarget.value)}
											/>
										</td>
										<td class="col-actions">
											<button
												class="delete-btn"
												onclick={() => removeRow(holiday.date, row.rowId)}
												aria-label="Remove employee"
											>
												<i class="fas fa-trash"></i>
											</button>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					{/if}

					<button class="add-row-btn" onclick={() => addRow(holiday.date)}>
						<i class="fas fa-plus"></i>
						<span>Add Employee</span>
					</button>
				</div>
			{/each}

			<div class="modal-info">
				<i class="fas fa-info-circle"></i>
				<span>
					Employees who worked will receive:
					<ul>
						<li>Regular holiday pay (auto-calculated)</li>
						<li>Premium pay at 1.5x regular rate for hours worked</li>
					</ul>
				</span>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" onclick={onClose}>Cancel</button>
			<button class="btn-primary" onclick={handleSave}>Save Hours</button>
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

	.holiday-section {
		margin-bottom: var(--spacing-5);
	}

	.holiday-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		margin-bottom: var(--spacing-3);
	}

	.holiday-info i {
		font-size: var(--font-size-title-medium);
		color: var(--color-warning-600);
	}

	.holiday-info strong {
		display: block;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
	}

	.holiday-date {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.holiday-note {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4);
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
	}

	/* Table */
	.holiday-table {
		width: 100%;
		border-collapse: collapse;
		margin-bottom: 0;
	}

	.holiday-table th {
		text-align: left;
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		border-bottom: 1px solid var(--color-surface-200);
	}

	.holiday-table td {
		padding: var(--spacing-3);
		border-bottom: 1px solid var(--color-surface-100);
		vertical-align: middle;
	}

	.col-employee {
		width: 55%;
	}

	.col-hours {
		width: 25%;
	}

	.col-actions {
		width: 20%;
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
