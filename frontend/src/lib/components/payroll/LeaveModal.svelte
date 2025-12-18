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
<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-[1000] p-4" onclick={onClose} role="presentation">
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div
		class="bg-white rounded-xl shadow-md3-3 w-full flex flex-col {isSingleEmployeeMode ? 'max-w-[450px]' : 'max-w-[750px]'} max-h-[90vh]"
		onclick={(e) => e.stopPropagation()}
		role="dialog"
		aria-modal="true"
		tabindex="-1"
	>
		<div class="flex items-center justify-between p-5 border-b border-surface-100">
			{#if isSingleEmployeeMode && selectedEmployee}
				<div class="flex items-center gap-3">
					<Avatar name={selectedEmployee.employeeName} size="medium" />
					<div class="flex flex-col">
						<h2 class="text-title-medium font-semibold text-surface-800 m-0">{selectedEmployee.employeeName}</h2>
						<span class="text-auxiliary-text text-surface-500">Record Leave - {formatDateRange(periodStart, periodEnd)}</span>
					</div>
				</div>
			{:else}
				<h2 class="text-title-medium font-semibold text-surface-800 m-0">Leave Hours - {formatDateRange(periodStart, periodEnd)}</h2>
			{/if}
			<button class="p-2 border-none bg-transparent text-surface-400 cursor-pointer rounded-md transition-[150ms] hover:bg-surface-100 hover:text-surface-700" onclick={onClose} aria-label="Close modal">
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="flex-1 overflow-y-auto p-5">
			{#if isSingleEmployeeMode && selectedEmployee}
				<!-- Single Employee Mode -->
				{@const balanceInfo = singleBalanceDisplay()}
				<div class="flex flex-col gap-5">
					<div class="flex flex-col gap-2">
						<label class="text-body-content font-medium text-surface-700">Leave Type</label>
						<div class="flex gap-3">
							{#each leaveTypes as lt}
								<button
									class="flex-1 flex items-center justify-center gap-2 p-4 border-2 rounded-lg bg-white cursor-pointer transition-[150ms] {singleLeaveType === lt
										? lt === 'vacation'
											? 'border-blue-400 bg-blue-50'
											: 'border-orange-400 bg-orange-50'
										: 'border-surface-200 hover:border-surface-300 hover:bg-surface-50'}"
									onclick={() => (singleLeaveType = lt)}
								>
									<span class="text-title-medium">{LEAVE_TYPE_LABELS[lt].icon}</span>
									<span class="text-body-content font-medium text-surface-700">{LEAVE_TYPE_LABELS[lt].full}</span>
								</button>
							{/each}
						</div>
					</div>

					<div class="flex flex-col gap-2">
						<label class="text-body-content font-medium text-surface-700" for="leave-hours">Hours</label>
						<input
							id="leave-hours"
							type="number"
							class="w-full p-4 border border-surface-200 rounded-lg text-title-medium text-center transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
							placeholder="0.0"
							min="0"
							max="80"
							step="0.5"
							bind:value={singleHours}
						/>
					</div>

					<div class="bg-surface-50 rounded-lg p-4">
						<div class="flex items-center gap-2 mb-3 pb-3 border-b border-surface-200">
							<span class="text-body-content">{LEAVE_TYPE_LABELS[singleLeaveType].icon}</span>
							<span class="text-body-content font-semibold text-surface-700">{LEAVE_TYPE_LABELS[singleLeaveType].full} Balance</span>
						</div>
						{#if typeof balanceInfo === 'object'}
							<div class="flex justify-between items-center py-2">
								<span class="text-body-content text-surface-600">Current Balance:</span>
								<span class="text-body-content font-medium text-surface-800">{balanceInfo.before}</span>
							</div>
							<div class="flex justify-between items-center py-2">
								<span class="text-body-content text-surface-600">After This Leave:</span>
								<span class="text-body-content font-semibold text-primary-600">{balanceInfo.after}</span>
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<!-- Multi-Employee Mode -->
				<p class="text-body-content text-surface-600 m-0 mb-4">Record leave taken during this pay period:</p>

				{#if leaveRows.length > 0}
					<table class="w-full border-collapse mb-0">
						<thead>
							<tr>
								<th class="text-left p-3 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase border-b border-surface-200 w-[35%]">Employee</th>
								<th class="text-left p-3 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase border-b border-surface-200 w-[25%]">Leave Type</th>
								<th class="text-left p-3 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase border-b border-surface-200 w-[15%]">Hours</th>
								<th class="text-left p-3 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase border-b border-surface-200 w-[20%]">Balance</th>
								<th class="text-right p-3 bg-surface-50 text-auxiliary-text font-semibold text-surface-600 uppercase border-b border-surface-200 w-[5%]"></th>
							</tr>
						</thead>
						<tbody>
							{#each leaveRows as row (row.rowId)}
								{@const isDropdownOpen = openDropdowns.has(row.rowId)}
								{@const filteredEmployees = getFilteredEmployees(row.rowId)}
								{@const displayValue = searchTexts.get(row.rowId) ?? row.employeeName}
								<tr>
									<td class="p-3 border-b border-surface-100 align-middle">
										<div class="relative {isDropdownOpen ? 'open' : ''}">
											<div class="relative">
												<input
													type="text"
													class="w-full py-2 px-3 pr-8 border border-surface-200 rounded-md text-body-content bg-white transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100 placeholder:text-surface-400"
													placeholder="Select employee..."
													value={displayValue}
													onfocus={() => openDropdown(row.rowId)}
													onblur={() => handleComboboxBlur(row.rowId)}
													oninput={(e) => handleSearchInput(row.rowId, e.currentTarget.value)}
												/>
												<i class="fas fa-chevron-down absolute right-3 top-1/2 -translate-y-1/2 text-surface-400 pointer-events-none text-auxiliary-text transition-[150ms] {isDropdownOpen ? 'rotate-180' : ''}"></i>
											</div>

											{#if isDropdownOpen}
												<ul class="absolute top-full left-0 right-0 max-h-[200px] overflow-y-auto bg-white border border-surface-200 rounded-md shadow-md3-1 z-10 mt-1 list-none p-0 mb-0">
													{#each filteredEmployees as emp}
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<li
															class="flex items-center gap-2 py-2 px-3 cursor-pointer transition-[150ms] hover:bg-surface-50"
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
														<li class="p-3 text-surface-500 text-body-content text-center">No employees found</li>
													{/if}
												</ul>
											{/if}
										</div>
									</td>
									<td class="p-3 border-b border-surface-100 align-middle">
										<select
											class="w-full py-2 px-3 border border-surface-200 rounded-md text-body-content bg-white cursor-pointer transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100 disabled:bg-surface-50 disabled:text-surface-400 disabled:cursor-not-allowed"
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
									<td class="p-3 border-b border-surface-100 align-middle">
										<input
											type="number"
											class="w-20 p-2 border border-surface-200 rounded-md text-body-content text-center transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100 disabled:bg-surface-50 disabled:text-surface-400 disabled:cursor-not-allowed"
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
									<td class="p-3 border-b border-surface-100 align-middle">
										<span class="text-auxiliary-text text-surface-600">{getBalanceDisplay(row)}</span>
									</td>
									<td class="p-3 border-b border-surface-100 align-middle text-right">
										<button
											class="p-2 border-none bg-transparent text-surface-400 cursor-pointer rounded-md transition-[150ms] hover:bg-error-50 hover:text-error-600"
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

				<button class="flex items-center justify-center gap-2 w-full p-3 border-none bg-transparent text-surface-500 text-body-content cursor-pointer border-t border-dashed border-surface-200 transition-[150ms] hover:bg-surface-50 hover:text-primary-600" onclick={addRow}>
					<i class="fas fa-plus"></i>
					<span>Add Row</span>
				</button>

				<div class="flex gap-3 p-4 bg-primary-50 rounded-lg text-body-content text-surface-700 mt-4">
					<i class="fas fa-info-circle text-primary-600 mt-0.5"></i>
					<span>
						Leave Types:
						<ul class="mt-2 pl-5 mb-0">
							<li class="mb-1"><strong>Vacation:</strong> Paid from accrued balance</li>
							<li class="mb-1"><strong>Sick:</strong> Paid per provincial requirements</li>
						</ul>
					</span>
				</div>
			{/if}
		</div>

		<div class="flex justify-end gap-3 py-4 px-5 border-t border-surface-100">
			<button class="flex items-center gap-2 py-3 px-5 bg-white text-surface-700 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-surface-50 hover:border-surface-300" onclick={onClose}>Cancel</button>
			<button class="flex items-center gap-2 py-3 px-5 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-[150ms] hover:opacity-90 hover:-translate-y-px" onclick={handleSave}>Save Leave</button>
		</div>
	</div>
</div>
