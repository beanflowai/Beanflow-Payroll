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

	// Track all input elements for programmatic focus management
	let inputRefs = $state<Map<string, HTMLInputElement>>(new Map());

	// Track current focused position
	let focusedPosition = $state<{ weekIdx: number; dayIdx: number } | null>(null);

	// Local input values to prevent re-render during editing
	let localInputValues = $state<Map<string, string>>(new Map());

	// Day names for header (index 0=Mon, ..., 6=Sun)
	const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

	/**
	 * Convert JavaScript dayOfWeek (0=Sun, 1=Mon, ..., 6=Sat) to dayIdx (0=Mon, ..., 6=Sun)
	 * This is the single source of truth for day index conversion.
	 */
	function dayOfWeekToDayIdx(dayOfWeek: number): number {
		return dayOfWeek === 0 ? 6 : dayOfWeek - 1;
	}

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

		const entry = weeklyData[weekIdx].entries[entryIdx];
		entry.totalHours = Math.min(num, 24);
		// Trigger reactivity by reassigning the entry (Svelte 5 $state tracks object mutations)
		weeklyData[weekIdx].entries[entryIdx] = { ...entry };
		// Recalculate totals via backend API
		debouncedRecalculate();
	}

	// Commit input value from local state to actual data
	function commitInputValue(weekIdx: number, entryIdx: number, value: string) {
		updateEntry(weekIdx, entryIdx, value);
	}

	// Handle input focus - initialize local value
	function handleInputFocus(weekIdx: number, entryIdx: number, currentValue: number) {
		const key = getInputKey(weekIdx, entryIdx);
		// Only initialize local value if not already set
		if (!localInputValues.has(key)) {
			localInputValues.set(key, currentValue > 0 ? String(currentValue) : '');
		}
	}

	// Handle input change - update local value only
	function handleInputChange(weekIdx: number, entryIdx: number, value: string) {
		const key = getInputKey(weekIdx, entryIdx);
		localInputValues.set(key, value);
	}

	// Handle input blur - commit the value
	function handleInputBlur(weekIdx: number, entryIdx: number) {
		const key = getInputKey(weekIdx, entryIdx);
		const value = localInputValues.get(key) || '0';
		commitInputValue(weekIdx, entryIdx, value);
		localInputValues.delete(key);
	}

	// Get display value for input - use local value if editing, otherwise use actual value
	function getInputDisplayValue(weekIdx: number, entryIdx: number, actualValue: number): string {
		const key = getInputKey(weekIdx, entryIdx);
		const localValue = localInputValues.get(key);
		if (localValue !== undefined) {
			return localValue;
		}
		return actualValue > 0 ? String(actualValue) : '';
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

	// Generate unique key for each input
	function getInputKey(weekIdx: number, dayIdx: number): string {
		return `${weekIdx}-${dayIdx}`;
	}

	// Action to register input element in refs map
	function registerInput(node: HTMLInputElement, params: { weekIdx: number; dayIdx: number }) {
		const key = getInputKey(params.weekIdx, params.dayIdx);
		inputRefs.set(key, node);
		return {
			destroy() {
				inputRefs.delete(key);
			}
		};
	}

	// Check if a cell has a valid input (not holiday, exists, in bounds)
	function isValidInputCell(weekIdx: number, dayIdx: number): boolean {
		if (weekIdx < 0 || weekIdx >= weeklyData.length) return false;
		const week = weeklyData[weekIdx];
		if (dayIdx < 0 || dayIdx >= week.entries.length) return false;
		return !week.entries[dayIdx].isHoliday;
	}

	// Find next valid position with boundary checks
	function findNextPosition(
		currentWeekIdx: number,
		currentDayIdx: number,
		direction: 'up' | 'down' | 'left' | 'right'
	): { weekIdx: number; dayIdx: number } | null {
		let targetWeekIdx = currentWeekIdx;
		let targetDayIdx = currentDayIdx;

		switch (direction) {
			case 'up':
				targetWeekIdx = Math.max(0, currentWeekIdx - 1);
				break;
			case 'down':
				targetWeekIdx = Math.min(weeklyData.length - 1, currentWeekIdx + 1);
				break;
			case 'left':
				targetDayIdx = Math.max(0, currentDayIdx - 1);
				break;
			case 'right':
				targetDayIdx = Math.min(6, currentDayIdx + 1);
				break;
		}

		if (isValidInputCell(targetWeekIdx, targetDayIdx)) {
			return { weekIdx: targetWeekIdx, dayIdx: targetDayIdx };
		}

		// Skip holidays - find next valid cell in direction
		return skipHolidayCells(targetWeekIdx, targetDayIdx, direction);
	}

	// Skip holiday cells recursively
	function skipHolidayCells(
		weekIdx: number,
		dayIdx: number,
		direction: 'up' | 'down' | 'left' | 'right'
	): { weekIdx: number; dayIdx: number } | null {
		const maxIterations = 14;
		let iterations = 0;

		while (iterations < maxIterations) {
			iterations++;

			if (weekIdx < 0 || weekIdx >= weeklyData.length) return null;
			if (dayIdx < 0 || dayIdx >= 7) return null;

			if (isValidInputCell(weekIdx, dayIdx)) {
				return { weekIdx, dayIdx };
			}

			switch (direction) {
				case 'up':
					weekIdx--;
					break;
				case 'down':
					weekIdx++;
					break;
				case 'left':
					dayIdx--;
					if (dayIdx < 0) {
						dayIdx = 6;
						weekIdx--;
					}
					break;
				case 'right':
					dayIdx++;
					if (dayIdx > 6) {
						dayIdx = 0;
						weekIdx++;
					}
					break;
			}
		}

		return null;
	}

	// Focus specific input
	function focusInput(weekIdx: number, dayIdx: number): boolean {
		// Commit any pending input from the previously focused cell
		const prevFocused = focusedPosition;
		if (prevFocused) {
			const prevKey = getInputKey(prevFocused.weekIdx, prevFocused.dayIdx);
			if (localInputValues.has(prevKey)) {
				const prevWeek = weeklyData[prevFocused.weekIdx];
				if (prevWeek) {
					// Use unified dayOfWeekToDayIdx conversion
					const entryIndex = prevWeek.entries.findIndex(
						(e) => dayOfWeekToDayIdx(e.dayOfWeek) === prevFocused.dayIdx
					);
					if (entryIndex >= 0) {
						handleInputBlur(prevFocused.weekIdx, entryIndex);
					}
				}
			}
		}

		const key = getInputKey(weekIdx, dayIdx);
		const input = inputRefs.get(key);

		if (input) {
			input.focus();
			input.select();
			focusedPosition = { weekIdx, dayIdx };
			return true;
		}

		return false;
	}

	// Check if we should allow default browser behavior (text editing)
	function shouldAllowDefaultBehavior(event: KeyboardEvent, input: HTMLInputElement): boolean {
		const key = event.key;

		if (['ArrowLeft', 'ArrowRight'].includes(key)) {
			const selectionStart = input.selectionStart ?? 0;
			const selectionEnd = input.selectionEnd ?? 0;
			const valueLength = input.value.length;

			if (valueLength > 0 && selectionStart !== selectionEnd) {
				return true; // Allow navigation within selection
			}

			if (key === 'ArrowLeft' && selectionStart > 0) {
				return true;
			}

			if (key === 'ArrowRight' && selectionStart < valueLength) {
				return true;
			}
		}

		if (['Home', 'End'].includes(key)) {
			return true;
		}

		return false;
	}

	// Handle keyboard navigation
	function handleKeydown(event: KeyboardEvent, weekIdx: number, dayIdx: number) {
		const input = event.currentTarget as HTMLInputElement;

		if (shouldAllowDefaultBehavior(event, input)) {
			return;
		}

		let nextPosition: { weekIdx: number; dayIdx: number } | null = null;

		switch (event.key) {
			case 'ArrowUp':
				event.preventDefault();
				nextPosition = findNextPosition(weekIdx, dayIdx, 'up');
				break;
			case 'ArrowDown':
				event.preventDefault();
				nextPosition = findNextPosition(weekIdx, dayIdx, 'down');
				break;
			case 'ArrowLeft':
				event.preventDefault();
				nextPosition = findNextPosition(weekIdx, dayIdx, 'left');
				break;
			case 'ArrowRight':
				event.preventDefault();
				nextPosition = findNextPosition(weekIdx, dayIdx, 'right');
				break;
			case 'Enter':
				event.preventDefault();
				// Commit current input before navigating
				const key = getInputKey(weekIdx, dayIdx);
				if (localInputValues.has(key)) {
					const week = weeklyData[weekIdx];
					// Use unified dayOfWeekToDayIdx conversion
					const entryIdx = week.entries.findIndex(
						(e) => dayOfWeekToDayIdx(e.dayOfWeek) === dayIdx
					);
					if (entryIdx >= 0) {
						handleInputBlur(weekIdx, entryIdx);
					}
				}
				nextPosition = findNextPosition(weekIdx, dayIdx, 'right');
				break;
		}

		if (nextPosition) {
			focusInput(nextPosition.weekIdx, nextPosition.dayIdx);
		}
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
										(e) => dayNames[dayOfWeekToDayIdx(e.dayOfWeek)] === dayName
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
												{@const entryIdx = week.entries.indexOf(entry)}
												<input
													type="number"
													class="hours-input"
													min="0"
													max="24"
													step="0.5"
													value={getInputDisplayValue(weekIdx, entryIdx, entry.totalHours)}
													oninput={(e) =>
														handleInputChange(weekIdx, entryIdx, e.currentTarget.value)}
													onfocus={() => {
														focusedPosition = { weekIdx, dayIdx };
														handleInputFocus(weekIdx, entryIdx, entry.totalHours);
													}}
													onblur={() => handleInputBlur(weekIdx, entryIdx)}
													onkeydown={(e) => handleKeydown(e, weekIdx, dayIdx)}
													use:registerInput={{ weekIdx, dayIdx }}
													placeholder=""
													aria-label="Hours for {entry.workDate}"
													data-week={weekIdx}
													data-day={dayIdx}
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
							<strong>Regular:</strong> {totals().regularHours.toFixed(2)}h
						</span>
						<span class="summary-divider">|</span>
						<span class="summary-item">
							<strong>Overtime:</strong> {totals().overtimeHours.toFixed(2)}h
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
