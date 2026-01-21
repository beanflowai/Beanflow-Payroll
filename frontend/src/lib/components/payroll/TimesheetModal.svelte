<script lang="ts">
	import type { TimesheetEntry, Holiday } from '$lib/types/payroll';
	import {
		getTimesheetEntries,
		updateTimesheetEntries,
		calculateOvertimeSplit,
		type OvertimeCalculateResponse
	} from '$lib/services/timesheetService';
	import { getProvinceStandards, type OvertimeRules } from '$lib/services/configService';
	import type { Province } from '$lib/types/employee';
	import { formatDateRange } from '$lib/utils/overtimeCalculator';

	interface DailyEntry {
		workDate: string;
		dayOfWeek: number; // 0=Sun, 1=Mon, ...
		isHoliday: boolean;
		totalHours: number;
	}

	interface WeekData {
		weekNumber: number;
		startDate: string;
		entries: DailyEntry[];
	}

	interface Props {
		isOpen: boolean;
		employeeName: string;
		payrollRecordId: string;
		periodStart: string;
		periodEnd: string;
		holidays?: Holiday[];
		province: string;
		onClose: () => void;
		onSave: (totals: { regularHours: number; overtimeHours: number }) => void;
	}

	let {
		isOpen,
		employeeName,
		payrollRecordId,
		periodStart,
		periodEnd,
		holidays = [],
		province,
		onClose,
		onSave
	}: Props = $props();

	let weeklyData = $state<WeekData[]>([]);
	let overtimeRules = $state<OvertimeRules | null>(null);
	let loading = $state(false);
	let saving = $state(false);
	let error = $state<string | null>(null);
	let calculatedTotals = $state<OvertimeCalculateResponse>({
		regularHours: 0,
		overtimeHours: 0,
		doubleTimeHours: 0
	});
	let isCalculating = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	// Day names for header
	const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

	// Initialize modal
	$effect(() => {
		if (isOpen) {
			loadTimesheetData();
		}
	});

	// Parse an ISO date string as local date
	function parseLocalDate(dateStr: string): Date {
		const [year, month, day] = dateStr.split('-').map(Number);
		return new Date(year, month - 1, day);
	}

	// Format date as ISO string (YYYY-MM-DD)
	function formatIsoDate(date: Date): string {
		const year = date.getFullYear();
		const month = String(date.getMonth() + 1).padStart(2, '0');
		const day = String(date.getDate()).padStart(2, '0');
		return `${year}-${month}-${day}`;
	}

	// Generate daily entries for the pay period
	function generateDailyEntries(): DailyEntry[] {
		const entries: DailyEntry[] = [];
		const startDate = parseLocalDate(periodStart);
		const endDate = parseLocalDate(periodEnd);
		const holidaySet = new Set(holidays.map((h) => h.date));

		for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
			const dateStr = formatIsoDate(d);
			entries.push({
				workDate: dateStr,
				dayOfWeek: d.getDay(),
				isHoliday: holidaySet.has(dateStr),
				totalHours: 0
			});
		}

		return entries;
	}

	// Group entries into weeks (Mon-Sun)
	function groupIntoWeeks(entries: DailyEntry[]): WeekData[] {
		const weeks: WeekData[] = [];
		let currentWeek: DailyEntry[] = [];
		let weekNumber = 1;
		let weekStartDate = '';

		for (const entry of entries) {
			// Start new week on Monday (dayOfWeek === 1)
			if (entry.dayOfWeek === 1 && currentWeek.length > 0) {
				weeks.push({
					weekNumber: weekNumber++,
					startDate: weekStartDate,
					entries: currentWeek
				});
				currentWeek = [];
			}

			if (currentWeek.length === 0) {
				weekStartDate = entry.workDate;
			}
			currentWeek.push(entry);
		}

		// Push the last week
		if (currentWeek.length > 0) {
			weeks.push({
				weekNumber,
				startDate: weekStartDate,
				entries: currentWeek
			});
		}

		return weeks;
	}

	// Load existing timesheet data and overtime rules
	async function loadTimesheetData() {
		loading = true;
		error = null;

		try {
			// Load overtime rules from API
			const standards = await getProvinceStandards(province as Province);
			if (standards) {
				overtimeRules = standards.overtime;
			} else {
				// Fallback if API fails - use Federal defaults
				overtimeRules = {
					dailyThreshold: null,
					weeklyThreshold: 40,
					overtimeRate: 1.5,
					doubleTimeDaily: null,
					notes: 'Fallback rules'
				};
			}

			// Generate base entries
			const allEntries = generateDailyEntries();

			// Load existing timesheet data
			const result = await getTimesheetEntries(payrollRecordId);

			if (result.error) {
				error = result.error;
			} else if (result.data) {
				// Map existing entries to daily entries
				const entryMap = new Map(result.data.entries.map((e) => [e.workDate, e]));

				for (const entry of allEntries) {
					const existing = entryMap.get(entry.workDate);
					if (existing) {
						// Sum regular + overtime to get total hours
						entry.totalHours = (existing.regularHours ?? 0) + (existing.overtimeHours ?? 0);
					}
				}
			}

			// Group into weeks
			weeklyData = groupIntoWeeks(allEntries);

			// Initial calculation of totals
			await recalculateTotals();
		} catch (e) {
			error = 'Failed to load timesheet data';
			console.error(e);
		} finally {
			loading = false;
		}
	}

	// Calculate totals using backend API with debounce
	async function recalculateTotals() {
		if (!overtimeRules) {
			calculatedTotals = { regularHours: 0, overtimeHours: 0, doubleTimeHours: 0 };
			return;
		}

		const entries = weeklyData.flatMap((w) =>
			w.entries.map((e) => ({
				date: e.workDate,
				totalHours: e.totalHours,
				isHoliday: e.isHoliday
			}))
		);

		isCalculating = true;
		try {
			const result = await calculateOvertimeSplit({
				province,
				entries
			});
			// Check for calculation error
			if (result.error) {
				error = `Calculation failed: ${result.error}`;
				// Don't update calculatedTotals - keep last valid values
			} else {
				error = null; // Clear any previous error
				calculatedTotals = result; // Only update on success
			}
		} finally {
			isCalculating = false;
		}
	}

	// Debounced recalculation (300ms delay)
	function debouncedRecalculate() {
		if (debounceTimer) {
			clearTimeout(debounceTimer);
		}
		debounceTimer = setTimeout(() => {
			recalculateTotals();
		}, 300);
	}

	// Getter for computed totals (for template compatibility)
	function totals() {
		return calculatedTotals;
	}

	// Update entry value
	function updateEntry(weekIdx: number, entryIdx: number, value: string) {
		const num = parseFloat(value) || 0;
		if (num < 0) return;

		weeklyData[weekIdx].entries[entryIdx].totalHours = Math.min(num, 24);
		// Trigger reactivity
		weeklyData = [...weeklyData];
		// Recalculate totals via backend API
		debouncedRecalculate();
	}

	// Handle save
	async function handleSave() {
		saving = true;
		error = null;

		try {
			// Convert to TimesheetEntry format with calculated regular/overtime split
			const entries: TimesheetEntry[] = [];

			for (const week of weeklyData) {
				for (const entry of week.entries) {
					if (entry.totalHours > 0 && !entry.isHoliday) {
						// For saving, we need to split per-day if there's a daily threshold
						let regularHours = entry.totalHours;
						let overtimeHours = 0;

						if (overtimeRules?.dailyThreshold !== null && overtimeRules?.dailyThreshold !== undefined) {
							if (entry.totalHours > overtimeRules.dailyThreshold) {
								regularHours = overtimeRules.dailyThreshold;
								overtimeHours = entry.totalHours - overtimeRules.dailyThreshold;
							}
						}
						// For weekly-only provinces, we store full hours as regular
						// The backend will recalculate if needed

						entries.push({
							workDate: entry.workDate,
							regularHours,
							overtimeHours
						});
					} else if (!entry.isHoliday) {
						// Include zero-hour entries to clear previous data
						entries.push({
							workDate: entry.workDate,
							regularHours: 0,
							overtimeHours: 0
						});
					}
				}
			}

			const result = await updateTimesheetEntries(payrollRecordId, entries);

			if (result.error) {
				error = result.error;
				return;
			}

			// Call parent callback with calculated totals
			const calculatedTotals = totals();
			onSave({
				regularHours: calculatedTotals.regularHours,
				overtimeHours: calculatedTotals.overtimeHours
			});
			onClose();
		} catch (e) {
			error = 'Failed to save timesheet';
			console.error(e);
		} finally {
			saving = false;
		}
	}

	// Get holiday name for a date
	function getHolidayName(dateStr: string): string | undefined {
		return holidays.find((h) => h.date === dateStr)?.name;
	}
</script>

{#if isOpen}
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
				<h2>Detailed Timesheet - {employeeName}</h2>
				<button class="close-btn" onclick={onClose} aria-label="Close modal">
					<i class="fas fa-times"></i>
				</button>
			</div>

			<div class="modal-content">
				{#if loading}
					<div class="loading-state">
						<i class="fas fa-spinner fa-spin"></i>
						<span>Loading timesheet...</span>
					</div>
				{:else if error}
					<div class="error-state">
						<i class="fas fa-exclamation-triangle"></i>
						<span>{error}</span>
					</div>
				{:else}
					<p class="period-info">{formatDateRange(periodStart, periodEnd)}</p>

					<!-- Excel-style Calendar Grid -->
					<div class="calendar-grid">
						<!-- Header Row -->
						<div class="grid-header">
							<div class="week-label"></div>
							{#each dayNames as day}
								<div class="day-header">{day}</div>
							{/each}
						</div>

						<!-- Week Rows -->
						{#each weeklyData as week, weekIdx (week.weekNumber)}
							<div class="grid-row">
								<div class="week-label">Wk{week.weekNumber}</div>
								{#each dayNames as dayName, dayIdx}
									{@const entry = week.entries.find(
										(e) => ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][e.dayOfWeek] === dayName
									)}
									{#if entry}
										<div
											class="day-cell"
											class:is-holiday={entry.isHoliday}
											class:is-weekend={entry.dayOfWeek === 0 || entry.dayOfWeek === 6}
											title={entry.isHoliday ? getHolidayName(entry.workDate) : entry.workDate}
										>
											<span class="date-badge" aria-hidden="true">
												{entry.workDate.split('-')[2]}
											</span>
											{#if entry.isHoliday}
												<i class="fas fa-gift holiday-icon"></i>
											{:else}
												<input
													type="number"
													class="hours-input"
													min="0"
													max="24"
													step="0.5"
													value={entry.totalHours || ''}
													oninput={(e) =>
														updateEntry(weekIdx, week.entries.indexOf(entry), e.currentTarget.value)}
													placeholder=""
													aria-label="Hours for {entry.workDate}"
												/>
											{/if}
										</div>
									{:else}
										<div class="day-cell empty"></div>
									{/if}
								{/each}
							</div>
						{/each}
					</div>

					<!-- Summary Row -->
					<div class="summary-row">
						<span class="summary-item">
							<strong>Regular:</strong> {totals().regularHours.toFixed(1)}h
						</span>
						<span class="summary-divider">|</span>
						<span class="summary-item">
							<strong>Overtime:</strong> {totals().overtimeHours.toFixed(1)}h
						</span>
						{#if overtimeRules}
							<span class="rules-hint">
								({province}: {overtimeRules.dailyThreshold
									? `${overtimeRules.dailyThreshold}h/day`
									: `${overtimeRules.weeklyThreshold}h/week`})
							</span>
						{/if}
					</div>
				{/if}
			</div>

			<div class="modal-footer">
				<button class="btn-secondary" onclick={onClose} disabled={saving}>Cancel</button>
				<button class="btn-primary" onclick={handleSave} disabled={saving || loading || isCalculating || !!error}>
					{#if saving}
						<i class="fas fa-spinner fa-spin"></i>
						Saving...
					{:else}
						Save & Apply
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
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
		max-width: 680px;
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

	.loading-state,
	.error-state {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-8);
		justify-content: center;
		color: var(--color-surface-600);
	}

	.error-state {
		color: var(--color-error-600);
	}

	.period-info {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4);
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		text-align: center;
		font-weight: var(--font-weight-medium);
	}

	/* Excel-style Calendar Grid */
	.calendar-grid {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		margin-bottom: var(--spacing-4);
	}

	.grid-header,
	.grid-row {
		display: grid;
		grid-template-columns: 50px repeat(7, 1fr);
		gap: var(--spacing-1);
	}

	.week-label {
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-500);
	}

	.day-header {
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
	}

	.day-cell {
		display: flex;
		align-items: center;
		justify-content: center;
		min-height: 44px;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		background: white;
		transition: var(--transition-fast);
		position: relative;
	}

	.day-cell.is-weekend {
		background: var(--color-surface-50);
	}

	.day-cell.is-holiday {
		background: var(--color-warning-50);
		border-color: var(--color-warning-200);
	}

	.day-cell.empty {
		background: var(--color-surface-50);
		border-style: dashed;
	}

	/* Date Badge - Always show day of month */
	.date-badge {
		position: absolute;
		top: 2px;
		left: 4px;
		font-size: 10px;
		font-weight: 500;
		color: var(--color-surface-500, #99999a);
		line-height: 1;
		pointer-events: none;
		z-index: 1;
	}

	/* Holiday cells: badge matches holiday theme */
	.day-cell.is-holiday .date-badge {
		color: var(--color-warning-500, #ff6d24);
		font-weight: 600;
	}

	/* Weekend cells: slightly darker for contrast */
	.day-cell.is-weekend .date-badge {
		color: var(--color-surface-600, #6d6d6e);
	}

	/* Empty cells: no badge */
	.day-cell.empty .date-badge {
		display: none;
	}

	.holiday-icon {
		color: var(--color-warning-500);
		font-size: var(--font-size-body-content);
	}

	.hours-input {
		width: 100%;
		height: 100%;
		padding: var(--spacing-2) var(--spacing-2) var(--spacing-2) var(--spacing-5);
		border: none;
		background: transparent;
		font-size: var(--font-size-body-content);
		text-align: center;
		border-radius: var(--radius-md);
		-moz-appearance: textfield;
	}

	.hours-input::-webkit-inner-spin-button,
	.hours-input::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	.hours-input:focus {
		outline: none;
		box-shadow: inset 0 0 0 2px var(--color-primary-400);
	}

	/* Summary Row */
	.summary-row {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-100);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
	}

	.summary-item {
		color: var(--color-surface-700);
	}

	.summary-divider {
		color: var(--color-surface-300);
	}

	.rules-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-left: var(--spacing-2);
	}

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

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-primary:hover:not(:disabled) {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	/* Mobile responsive adjustments */
	@media (max-width: 768px) {
		.date-badge {
			top: 1px;
			left: 2px;
			font-size: 9px;
		}

		.hours-input {
			padding-left: var(--spacing-4);
		}
	}
</style>
