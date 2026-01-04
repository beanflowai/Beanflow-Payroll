<script lang="ts">
	import type {
		PayrollRunPayGroup,
		PayrollRecord,
		EmployeePayrollInput,
		Adjustment,
		AdjustmentType,
		Holiday
	} from '$lib/types/payroll';
	import {
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		ADJUSTMENT_TYPE_LABELS
	} from '$lib/types/payroll';
	import type { CustomDeduction } from '$lib/types/pay-group';
	import { formatCurrency } from '$lib/utils/formatUtils';

	// Adjustment type options for dropdown menus
	const EARNINGS_TYPES: AdjustmentType[] = [
		'bonus',
		'retroactive_pay',
		'taxable_benefit',
		'reimbursement',
		'other'
	];
	const DEDUCTIONS_TYPES: AdjustmentType[] = ['deduction'];

	interface Props {
		payGroup: PayrollRunPayGroup;
		holidays?: Holiday[];
		expandedRecordId: string | null;
		onToggleExpand: (id: string) => void;
		onUpdateRecord: (
			recordId: string,
			employeeId: string,
			updates: Partial<EmployeePayrollInput>
		) => void;
		onAddEmployee?: (payGroupId: string) => void;
		onRemoveEmployee?: (employeeId: string) => void;
	}

	let {
		payGroup,
		holidays = [],
		expandedRecordId,
		onToggleExpand,
		onUpdateRecord,
		onAddEmployee,
		onRemoveEmployee
	}: Props = $props();

	let isCollapsed = $state(false);

	// Track which record's type selection menu is open
	let showEarningsMenu = $state<string | null>(null);
	let showDeductionsMenu = $state<string | null>(null);

	// Local input state for editing
	let localInputMap = $state<Map<string, Partial<EmployeePayrollInput>>>(new Map());

	function formatPeriod(start: string, end: string): string {
		// Parse date strings as local dates (not UTC) to avoid timezone shift
		const [startYear, startMonth, startDay] = start.split('-').map(Number);
		const [endYear, endMonth, endDay] = end.split('-').map(Number);
		const startDate = new Date(startYear, startMonth - 1, startDay);
		const endDate = new Date(endYear, endMonth - 1, endDay);
		const startStr = startDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		const endStr = endDate.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
		return `${startStr} - ${endStr}`;
	}

	function toggleCollapse() {
		isCollapsed = !isCollapsed;
	}

	function getLocalInput(recordId: string): Partial<EmployeePayrollInput> {
		return localInputMap.get(recordId) || {};
	}

	function handleHoursChange(
		record: PayrollRecord,
		field: 'regularHours' | 'overtimeHours',
		value: number
	) {
		const current = getLocalInput(record.id);
		const updated = { ...current, [field]: value };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { [field]: value });
	}

	function handleLeaveChange(record: PayrollRecord, type: 'vacation' | 'sick', hours: number) {
		const current = getLocalInput(record.id);
		const existingLeaves = current.leaveEntries ?? record.inputData?.leaveEntries ?? [];

		// Simple: just update the leave entry for this type
		let newLeaveEntries = existingLeaves.filter((l) => l.type !== type);
		if (hours > 0) {
			newLeaveEntries.push({ type, hours });
		}

		const updated = { ...current, leaveEntries: newLeaveEntries };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { leaveEntries: newLeaveEntries });
	}

	function handleAddAdjustment(record: PayrollRecord, type: AdjustmentType) {
		const current = getLocalInput(record.id);
		const existingAdjs = getAdjustments(record);
		const typeInfo = ADJUSTMENT_TYPE_LABELS[type];
		const newAdj: Adjustment = {
			id: crypto.randomUUID(),
			type: type,
			amount: 0,
			description: '',
			taxable: typeInfo?.taxable ?? true
		};
		const newAdjs = [...existingAdjs, newAdj];
		const updated = { ...current, adjustments: newAdjs };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { adjustments: newAdjs });
		// Close menus
		showEarningsMenu = null;
		showDeductionsMenu = null;
	}

	function handleAddCustomDeduction(record: PayrollRecord, customDeduction: CustomDeduction) {
		const current = getLocalInput(record.id);
		const existingAdjs = getAdjustments(record);

		// Calculate amount based on calculation type
		let amount = customDeduction.amount;
		if (customDeduction.calculationType === 'percentage') {
			// Calculate from gross pay
			amount = (record.totalGross * customDeduction.amount) / 100;
			// Round to 2 decimal places
			amount = Math.round(amount * 100) / 100;
		}

		const newAdj: Adjustment = {
			id: crypto.randomUUID(),
			type: 'deduction',
			amount: amount,
			description: customDeduction.name,
			taxable: false, // Deductions are not taxable income additions
			customDeductionId: customDeduction.id,
			isPreTax: customDeduction.taxTreatment === 'pre_tax'
		};
		const newAdjs = [...existingAdjs, newAdj];
		const updated = { ...current, adjustments: newAdjs };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { adjustments: newAdjs });
		// Close menu
		showDeductionsMenu = null;
	}

	function handleUpdateAdjustment(
		record: PayrollRecord,
		idx: number,
		updates: Partial<Adjustment>
	) {
		const current = getLocalInput(record.id);
		const existingAdjs = getAdjustments(record);
		const newAdjs = [...existingAdjs];
		newAdjs[idx] = { ...newAdjs[idx], ...updates };
		const updated = { ...current, adjustments: newAdjs };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { adjustments: newAdjs });
	}

	function handleRemoveAdjustment(record: PayrollRecord, idx: number) {
		const current = getLocalInput(record.id);
		const existingAdjs = getAdjustments(record);
		const newAdjs = existingAdjs.filter((_: Adjustment, i: number) => i !== idx);
		const updated = { ...current, adjustments: newAdjs };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { adjustments: newAdjs });
	}

	function getLeaveHours(record: PayrollRecord, type: 'vacation' | 'sick'): number {
		const local = getLocalInput(record.id);
		const localEntry = local.leaveEntries?.find(
			(l: { type: string; hours: number }) => l.type === type
		);
		if (localEntry !== undefined) {
			return localEntry.hours;
		}
		const recordEntry = record.inputData?.leaveEntries?.find(
			(l: { type: string; hours: number }) => l.type === type
		);
		return recordEntry?.hours ?? 0;
	}

	function getTotalLeaveHours(record: PayrollRecord): number {
		return getLeaveHours(record, 'vacation') + getLeaveHours(record, 'sick');
	}

	/**
	 * Calculate vacation pay for the given vacation hours
	 * Uses the employee's hourly rate (or annual_salary / 2080 for salaried)
	 */
	function calculateVacationPay(record: PayrollRecord, vacationHours: number): number {
		if (vacationHours <= 0) return 0;
		// Use vacation hourly rate if available, otherwise calculate from salary/hourly
		const hourlyRate =
			record.vacationHourlyRate ??
			record.hourlyRate ??
			(record.annualSalary ? record.annualSalary / 2080 : 0);
		return vacationHours * hourlyRate;
	}

	/**
	 * Check if vacation balance is insufficient for the requested vacation pay
	 */
	function hasInsufficientBalance(record: PayrollRecord): boolean {
		// Only check for accrual method
		if (record.vacationPayoutMethod !== 'accrual') return false;

		const vacationHours = getLeaveHours(record, 'vacation');
		if (vacationHours <= 0) return false;

		const vacationPay = calculateVacationPay(record, vacationHours);
		// Available balance = old balance + accrued this period - paid this period
		const availableBalance =
			(record.vacationBalance ?? 0) + record.vacationAccrued - (record.vacationPayPaid ?? 0);
		return vacationPay > availableBalance;
	}

	function getAdjustments(record: PayrollRecord): Adjustment[] {
		const local = getLocalInput(record.id);
		if (local.adjustments !== undefined) {
			return local.adjustments;
		}
		// Ensure all adjustments have IDs (for backward compatibility with old data)
		const rawAdjs = record.inputData?.adjustments ?? [];
		return rawAdjs.map((adj, idx) => ({
			...adj,
			id: adj.id ?? `legacy-${record.id}-${idx}`
		}));
	}

	function getEarningsAdjustments(record: PayrollRecord): Adjustment[] {
		return getAdjustments(record).filter((adj) => EARNINGS_TYPES.includes(adj.type));
	}

	function getDeductionAdjustments(record: PayrollRecord): Adjustment[] {
		return getAdjustments(record).filter((adj) => DEDUCTIONS_TYPES.includes(adj.type));
	}

	function getDeductionLabel(adj: Adjustment): string {
		// If it's a custom deduction with a description, use that
		if (adj.description) {
			return adj.description;
		}
		// Otherwise use the generic "Deduction" label
		return ADJUSTMENT_TYPE_LABELS[adj.type]?.label ?? 'Deduction';
	}

	function getDeductionTaxType(adj: Adjustment): string | null {
		if (adj.isPreTax === true) return 'Pre-tax';
		if (adj.isPreTax === false) return 'Post-tax';
		return null;
	}

	// Format HOURS/RATE column display
	function formatHoursRate(record: PayrollRecord): string {
		if (record.compensationType === 'salaried' && record.annualSalary) {
			return formatCurrency(record.annualSalary) + '/yr';
		} else if (record.compensationType === 'hourly' && record.hourlyRate) {
			const hours = record.regularHoursWorked ?? 0;
			return `${hours}h @ ${formatCurrency(record.hourlyRate)}`;
		}
		return '--';
	}

	// Check if record needs recalculation (modified or not yet calculated)
	function isUncalculated(record: PayrollRecord): boolean {
		// Check if record is marked as modified
		if (record.isModified) return true;
		// Check if statutory deductions are zero (indicates not yet calculated)
		const hasZeroDeductions =
			record.cppEmployee === 0 &&
			record.eiEmployee === 0 &&
			record.federalTax === 0 &&
			record.provincialTax === 0;
		// For salaried employees with gross > 0, zero deductions means uncalculated
		if (record.grossRegular > 0 && hasZeroDeductions) return true;
		return false;
	}

	function handleRemoveEmployee(e: MouseEvent, employeeId: string) {
		e.stopPropagation();
		if (onRemoveEmployee) {
			onRemoveEmployee(employeeId);
		}
	}

	function handleAddEmployee(e: MouseEvent) {
		e.stopPropagation();
		if (onAddEmployee) {
			onAddEmployee(payGroup.payGroupId);
		}
	}

	/**
	 * Check if there's a holiday for this employee's province in the current pay period
	 */
	function hasHolidayForEmployee(record: PayrollRecord): boolean {
		return holidays.some((h) => h.province === record.employeeProvince);
	}

	/**
	 * Handle Holiday Pay Exempt checkbox change
	 * Updates input_data with holidayPayExempt flag
	 */
	function handleHolidayPayExemptChange(record: PayrollRecord, exempt: boolean) {
		onUpdateRecord(record.id, record.employeeId, { holidayPayExempt: exempt });
	}
</script>

<div class="bg-white rounded-xl shadow-md3-1 overflow-hidden mb-4 border-2 border-neutral-200">
	<!-- Section Header -->
	<button
		class="w-full flex items-center justify-between py-4 px-5 bg-white border-none cursor-pointer transition-all duration-150 text-left hover:bg-neutral-100"
		onclick={toggleCollapse}
	>
		<div class="flex items-center gap-3">
			<i class="fas fa-chevron-{isCollapsed ? 'right' : 'down'} text-xs text-surface-500 w-4"></i>
			<div
				class="w-9 h-9 rounded-lg bg-warning-100 text-warning-700 flex items-center justify-center text-sm"
			>
				<i class="fas fa-tag"></i>
			</div>
			<div class="flex flex-col gap-1">
				<h3 class="text-body-content font-semibold text-surface-800 m-0">
					{payGroup.payGroupName}
				</h3>
				<div class="flex items-center gap-2">
					<span class="text-caption text-surface-600">
						{PAY_FREQUENCY_LABELS[payGroup.payFrequency] || payGroup.payFrequency}
					</span>
					<span class="w-1 h-1 rounded-full bg-surface-300"></span>
					<span class="text-caption text-surface-600">
						{EMPLOYMENT_TYPE_LABELS[payGroup.employmentType] || payGroup.employmentType}
					</span>
					<span class="w-1 h-1 rounded-full bg-surface-300"></span>
					<span class="text-caption text-surface-600">
						{formatPeriod(payGroup.periodStart, payGroup.periodEnd)}
					</span>
				</div>
			</div>
		</div>
		<div class="flex items-center gap-6">
			<div class="flex flex-col items-end">
				<span class="text-body-content font-semibold text-surface-800"
					>{payGroup.totalEmployees}</span
				>
				<span class="text-caption text-surface-500">Employees</span>
			</div>
			<div class="flex flex-col items-end">
				<span class="text-body-content font-semibold text-surface-800"
					>{formatCurrency(payGroup.totalGross)}</span
				>
				<span class="text-caption text-surface-500">Gross</span>
			</div>
			<div class="flex flex-col items-end">
				<span class="text-body-content font-semibold text-surface-800"
					>{formatCurrency(payGroup.totalDeductions)}</span
				>
				<span class="text-caption text-surface-500">Deductions</span>
			</div>
			<div class="flex flex-col items-end">
				<span class="text-body-content font-semibold text-success-600"
					>{formatCurrency(payGroup.totalNetPay)}</span
				>
				<span class="text-caption text-surface-500">Net Pay</span>
			</div>
			<!-- svelte-ignore node_invalid_placement_ssr -->
			{#if onAddEmployee}
				<button
					class="p-2 bg-primary-50 border border-primary-200 rounded-lg text-primary-600 cursor-pointer transition-all duration-150 hover:bg-primary-100 hover:border-primary-300"
					title="Add Employee"
					onclick={handleAddEmployee}
				>
					<i class="fas fa-user-plus"></i>
				</button>
			{/if}
		</div>
	</button>

	<!-- Section Content -->
	{#if !isCollapsed}
		<div class="border-t border-neutral-200">
			<table class="w-full border-collapse">
				<thead>
					<tr class="bg-surface-50">
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200 w-[18%]"
							>Employee</th
						>
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-center uppercase tracking-wider border-b border-surface-200 w-[8%]"
							>Province</th
						>
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-left uppercase tracking-wider border-b border-surface-200 w-[15%]"
							>Hours/Rate</th
						>
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-right uppercase tracking-wider border-b border-surface-200 w-[14%]"
							>Earnings</th
						>
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-right uppercase tracking-wider border-b border-surface-200 w-[14%]"
							>Deductions</th
						>
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-center uppercase tracking-wider border-b border-surface-200 w-[10%]"
							>Leave</th
						>
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-right uppercase tracking-wider border-b border-surface-200 w-[14%]"
							>Net Pay</th
						>
						<th
							class="py-3 px-4 text-caption font-semibold text-surface-600 text-right uppercase tracking-wider border-b border-surface-200 w-[5%]"
						></th>
					</tr>
				</thead>
				<tbody>
					{#each payGroup.records as record (record.id)}
						<!-- Main Row -->
						<tr
							class="cursor-pointer transition-all duration-150 {expandedRecordId === record.id
								? 'bg-neutral-50'
								: 'hover:bg-surface-50'}"
							onclick={() => onToggleExpand(record.id)}
						>
							<td class="py-3 px-4 text-body-content text-surface-700 border-b border-surface-100">
								<div class="flex items-center gap-2">
									<div class="flex flex-col gap-0.5">
										<div class="flex items-center gap-2">
											<span class="font-medium text-surface-800">{record.employeeName}</span>
											{#if isUncalculated(record)}
												<span
													class="inline-flex items-center px-1.5 py-0.5 bg-warning-100 text-warning-700 rounded text-caption font-medium"
												>
													Est.
												</span>
											{/if}
										</div>
										<span class="text-caption text-surface-500 capitalize"
											>{record.compensationType}</span
										>
									</div>
									{#if onRemoveEmployee}
										<button
											class="ml-auto p-1.5 bg-transparent border-none text-surface-400 cursor-pointer rounded transition-all duration-150 hover:bg-error-50 hover:text-error-500"
											title="Remove from payroll"
											onclick={(e) => handleRemoveEmployee(e, record.employeeId)}
										>
											<i class="fas fa-user-minus text-sm"></i>
										</button>
									{/if}
								</div>
							</td>
							<td
								class="py-3 px-4 text-body-content text-surface-700 border-b border-surface-100 text-center"
							>
								<span
									class="inline-flex py-1 px-2 bg-surface-100 rounded text-caption font-medium text-surface-700"
								>
									{record.employeeProvince}
								</span>
							</td>
							<td class="py-3 px-4 text-body-content text-surface-700 border-b border-surface-100">
								<span class="font-medium text-surface-700">{formatHoursRate(record)}</span>
							</td>
							<td
								class="py-3 px-4 text-body-content text-surface-700 border-b border-surface-100 text-right"
							>
								{formatCurrency(record.totalGross)}
							</td>
							<td
								class="py-3 px-4 text-body-content text-surface-700 border-b border-surface-100 text-right"
							>
								{formatCurrency(record.totalDeductions)}
							</td>
							<td
								class="py-3 px-4 text-body-content text-surface-700 border-b border-surface-100 text-center"
							>
								{#if getTotalLeaveHours(record) > 0}
									<span class="text-warning-600 font-medium">{getTotalLeaveHours(record)}h</span>
								{:else}
									<span class="text-surface-400">0h</span>
								{/if}
							</td>
							<td class="py-3 px-4 text-body-content border-b border-surface-100 text-right">
								<span class="font-semibold text-success-600">{formatCurrency(record.netPay)}</span>
							</td>
							<td class="py-3 px-4 text-body-content border-b border-surface-100 text-right">
								<button
									class="p-2 bg-transparent border-none rounded-lg text-surface-500 cursor-pointer transition-all duration-150 hover:bg-surface-100 hover:text-primary-600"
									title={expandedRecordId === record.id ? 'Collapse' : 'Expand'}
								>
									<i class="fas fa-chevron-{expandedRecordId === record.id ? 'up' : 'down'}"></i>
								</button>
							</td>
						</tr>

						<!-- Expanded Row -->
						{#if expandedRecordId === record.id}
							<tr class="bg-neutral-50">
								<td colspan="8" class="p-0">
									<div class="p-5">
										<!-- Three Column Grid: EARNINGS | DEDUCTIONS | LEAVE -->
										<div class="grid grid-cols-3 gap-5">
											<!-- EARNINGS Column -->
											<div class="flex flex-col gap-3">
												<h4
													class="text-caption font-semibold text-surface-600 uppercase tracking-wider m-0 pb-2 border-b border-surface-200"
												>
													Earnings
												</h4>
												<div class="flex flex-col gap-2">
													<!-- Regular Pay -->
													<div class="flex flex-col gap-1">
														<div class="flex justify-between items-center">
															<span class="text-body-content text-surface-600">Regular Pay</span>
															<span class="text-body-content text-surface-800"
																>{formatCurrency(record.grossRegular)}</span
															>
														</div>
														<!-- Regular Hours input (only for hourly employees) -->
														{#if record.compensationType === 'hourly'}
															<!-- svelte-ignore a11y_no_static_element_interactions -->
															<!-- svelte-ignore a11y_click_events_have_key_events -->
															<div
																class="flex justify-between items-center gap-2 pl-4"
																onclick={(e) => e.stopPropagation()}
															>
																<span class="text-body-small text-surface-500">Regular Hours</span>
																<div class="flex items-center gap-1">
																	<input
																		type="number"
																		class="amount-input w-16 py-1 px-2 border border-surface-300 rounded text-body-small text-center focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
																		value={record.regularHoursWorked ?? 0}
																		min="0"
																		step="0.5"
																		onchange={(e) => {
																			let val = parseFloat(e.currentTarget.value) || 0;
																			if (val < 0) val = 0;
																			e.currentTarget.value = val.toString();
																			handleHoursChange(record, 'regularHours', val);
																		}}
																	/>
																	<span class="text-caption text-surface-500">hrs</span>
																</div>
															</div>
														{/if}
													</div>

													<!-- Vacation Earned -->
													{#if record.vacationAccrued > 0}
														<div class="flex justify-between items-center">
															<span class="text-body-content text-surface-600">Vacation Earned</span
															>
															<span class="text-body-content text-surface-800"
																>{formatCurrency(record.vacationAccrued)}</span
															>
														</div>
													{/if}

													<!-- Overtime -->
													<div class="flex flex-col gap-1">
														<div class="flex justify-between items-center">
															<span class="text-body-content text-surface-600">Overtime</span>
															<span class="text-body-content text-surface-800"
																>{formatCurrency(record.grossOvertime)}</span
															>
														</div>
														<!-- Overtime Hours input (for both hourly and salaried) -->
														<!-- svelte-ignore a11y_no_static_element_interactions -->
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<div
															class="flex justify-between items-center gap-2 pl-4"
															onclick={(e) => e.stopPropagation()}
														>
															<span class="text-body-small text-surface-500">Overtime Hours</span>
															<div class="flex items-center gap-1">
																<input
																	type="number"
																	class="amount-input w-16 py-1 px-2 border border-surface-300 rounded text-body-small text-center focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
																	value={record.overtimeHoursWorked ?? 0}
																	min="0"
																	step="0.5"
																	onchange={(e) => {
																		let val = parseFloat(e.currentTarget.value) || 0;
																		if (val < 0) val = 0;
																		e.currentTarget.value = val.toString();
																		handleHoursChange(record, 'overtimeHours', val);
																	}}
																/>
																<span class="text-caption text-surface-500">hrs</span>
															</div>
														</div>
													</div>

													<!-- Holiday Pay with Exempt toggle (only shown when pay period has holidays for this province) -->
													{#if hasHolidayForEmployee(record)}
														<!-- svelte-ignore a11y_no_static_element_interactions -->
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<div
															class="flex justify-between items-center"
															onclick={(e) => e.stopPropagation()}
														>
															<div class="flex items-center gap-2">
																<span class="text-body-content text-surface-600">Holiday Pay</span>
																<label
																	class="flex items-center gap-1 text-body-small text-surface-500 cursor-pointer"
																>
																	<input
																		type="checkbox"
																		class="w-3.5 h-3.5 rounded border-surface-300 accent-primary-600"
																		checked={record.inputData?.holidayPayExempt ?? false}
																		onchange={(e) =>
																			handleHolidayPayExemptChange(record, e.currentTarget.checked)}
																	/>
																	<span>Exempt</span>
																</label>
															</div>
															<span class="text-body-content text-surface-800"
																>{formatCurrency(record.holidayPay)}</span
															>
														</div>
													{/if}

													<!-- Vacation Pay (if any) -->
													{#if record.vacationPayPaid > 0}
														<div class="flex justify-between items-center">
															<span class="text-body-content text-surface-600">Vacation Pay</span>
															<span class="text-body-content text-surface-800"
																>{formatCurrency(record.vacationPayPaid)}</span
															>
														</div>
													{/if}

													<!-- Holiday Premium (if any) -->
													{#if record.holidayPremiumPay > 0}
														<div class="flex justify-between items-center">
															<span class="text-body-content text-surface-600">Holiday Premium</span
															>
															<span class="text-body-content text-surface-800"
																>{formatCurrency(record.holidayPremiumPay)}</span
															>
														</div>
													{/if}

													<!-- Other Earnings (if any) -->
													{#if record.otherEarnings > 0}
														<div class="flex justify-between items-center">
															<span class="text-body-content text-surface-600">Other Earnings</span>
															<span class="text-body-content text-surface-800"
																>{formatCurrency(record.otherEarnings)}</span
															>
														</div>
													{/if}

													<!-- User-added earnings adjustments -->
													{#each getEarningsAdjustments(record) as adj, _idx (adj.id)}
														{@const adjIdx = getAdjustments(record).indexOf(adj)}
														{@const typeInfo = ADJUSTMENT_TYPE_LABELS[adj.type]}
														<!-- svelte-ignore a11y_no_static_element_interactions -->
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<div
															class="flex flex-col gap-1 py-2"
															onclick={(e) => e.stopPropagation()}
														>
															<!-- Row 1: Type label + Delete -->
															<div class="flex items-center justify-between">
																<span class="text-body-content text-surface-700"
																	>{typeInfo?.label}</span
																>
																<button
																	class="p-1 bg-transparent border-none text-error-500 cursor-pointer rounded hover:bg-error-50 hover:text-error-600"
																	title="Remove"
																	onclick={() => handleRemoveAdjustment(record, adjIdx)}
																>
																	<i class="fas fa-times text-xs"></i>
																</button>
															</div>
															<!-- Row 2: Note + Amount (indented) -->
															<div class="flex items-center gap-2 pl-4">
																<input
																	type="text"
																	class="flex-1 py-1 px-2 border border-surface-200 rounded text-body-small focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
																	value={adj.description}
																	placeholder="Note"
																	onchange={(e) =>
																		handleUpdateAdjustment(record, adjIdx, {
																			description: e.currentTarget.value
																		})}
																/>
																<input
																	type="number"
																	class="amount-input w-24 py-1 px-2 border border-surface-300 rounded text-body-small text-right focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
																	value={adj.amount}
																	step="0.01"
																	min={adj.type === 'other' ? undefined : 0}
																	onchange={(e) => {
																		let val = parseFloat(e.currentTarget.value) || 0;
																		// Only 'other' type allows negative values
																		if (adj.type !== 'other' && val < 0) val = 0;
																		e.currentTarget.value = val.toString();
																		handleUpdateAdjustment(record, adjIdx, { amount: val });
																	}}
																/>
															</div>
														</div>
													{/each}

													<!-- Add Earnings Button with Dropdown -->
													<!-- svelte-ignore a11y_no_static_element_interactions -->
													<!-- svelte-ignore a11y_click_events_have_key_events -->
													<div class="relative" onclick={(e) => e.stopPropagation()}>
														<button
															class="w-full flex items-center justify-center gap-2 py-2 bg-surface-50 border border-dashed border-surface-300 rounded text-body-small text-surface-600 cursor-pointer transition-all duration-150 hover:bg-primary-50 hover:border-primary-300 hover:text-primary-600"
															onclick={() => {
																showEarningsMenu =
																	showEarningsMenu === record.id ? null : record.id;
																showDeductionsMenu = null;
															}}
														>
															<i class="fas fa-plus text-xs"></i>
															Add
															<i class="fas fa-chevron-up text-xs"></i>
														</button>

														{#if showEarningsMenu === record.id}
															<div
																class="absolute left-0 bottom-full mb-1 bg-white border border-surface-200 rounded-lg shadow-lg z-20 min-w-[180px] py-1"
															>
																{#each EARNINGS_TYPES as type (type)}
																	{@const info = ADJUSTMENT_TYPE_LABELS[type]}
																	<button
																		class="w-full px-3 py-2 text-left text-body-small text-surface-700 hover:bg-surface-50 flex items-center gap-2 border-none bg-transparent cursor-pointer"
																		onclick={() => handleAddAdjustment(record, type)}
																	>
																		<span>{info.icon}</span>
																		<span>{info.label}</span>
																	</button>
																{/each}
															</div>
														{/if}
													</div>

													<!-- Total Gross -->
													<div
														class="flex justify-between items-center pt-2 border-t border-surface-200 font-semibold"
													>
														<span class="text-body-content text-surface-600">Total Gross</span>
														<span class="text-body-content text-surface-800"
															>{formatCurrency(record.totalGross)}</span
														>
													</div>
												</div>
											</div>

											<!-- DEDUCTIONS Column -->
											<div class="flex flex-col gap-3">
												<h4
													class="text-caption font-semibold text-surface-600 uppercase tracking-wider m-0 pb-2 border-b border-surface-200"
												>
													Deductions
												</h4>
												<div class="flex flex-col gap-2">
													<!-- CPP -->
													<div class="flex justify-between items-center">
														<span class="text-body-content text-surface-600">CPP</span>
														<span class="text-body-content text-surface-800"
															>{formatCurrency(record.cppEmployee + record.cppAdditional)}</span
														>
													</div>

													<!-- EI -->
													<div class="flex justify-between items-center">
														<span class="text-body-content text-surface-600">EI</span>
														<span class="text-body-content text-surface-800"
															>{formatCurrency(record.eiEmployee)}</span
														>
													</div>

													<!-- Federal Tax -->
													<div class="flex justify-between items-center">
														<span class="text-body-content text-surface-600">Federal Tax</span>
														<span class="text-body-content text-surface-800"
															>{formatCurrency(record.federalTax)}</span
														>
													</div>

													<!-- Provincial Tax -->
													<div class="flex justify-between items-center">
														<span class="text-body-content text-surface-600">Provincial Tax</span>
														<span class="text-body-content text-surface-800"
															>{formatCurrency(record.provincialTax)}</span
														>
													</div>

													<!-- Benefits (from Pay Group group_benefits) -->
													{#if payGroup.groupBenefits?.enabled}
														{#if payGroup.groupBenefits.health?.enabled}
															<div class="flex justify-between items-center">
																<span class="text-body-content text-surface-600">Health</span>
																<span class="text-body-content text-surface-800"
																	>{formatCurrency(
																		payGroup.groupBenefits.health.employeeDeduction
																	)}</span
																>
															</div>
														{/if}
														{#if payGroup.groupBenefits.dental?.enabled}
															<div class="flex justify-between items-center">
																<span class="text-body-content text-surface-600">Dental</span>
																<span class="text-body-content text-surface-800"
																	>{formatCurrency(
																		payGroup.groupBenefits.dental.employeeDeduction
																	)}</span
																>
															</div>
														{/if}
														{#if payGroup.groupBenefits.vision?.enabled}
															<div class="flex justify-between items-center">
																<span class="text-body-content text-surface-600">Vision</span>
																<span class="text-body-content text-surface-800"
																	>{formatCurrency(
																		payGroup.groupBenefits.vision.employeeDeduction
																	)}</span
																>
															</div>
														{/if}
														{#if payGroup.groupBenefits.lifeInsurance?.enabled}
															<div class="flex justify-between items-center">
																<span class="text-body-content text-surface-600"
																	>Life Insurance</span
																>
																<span class="text-body-content text-surface-800"
																	>{formatCurrency(
																		payGroup.groupBenefits.lifeInsurance.employeeDeduction
																	)}</span
																>
															</div>
														{/if}
														{#if payGroup.groupBenefits.disability?.enabled}
															<div class="flex justify-between items-center">
																<span class="text-body-content text-surface-600">Disability</span>
																<span class="text-body-content text-surface-800"
																	>{formatCurrency(
																		payGroup.groupBenefits.disability.employeeDeduction
																	)}</span
																>
															</div>
														{/if}
													{/if}

													<!-- User-added deduction adjustments -->
													{#each getDeductionAdjustments(record) as adj, _idx (adj.id)}
														{@const adjIdx = getAdjustments(record).indexOf(adj)}
														{@const deductionLabel = getDeductionLabel(adj)}
														{@const taxType = getDeductionTaxType(adj)}
														<!-- svelte-ignore a11y_no_static_element_interactions -->
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<div
															class="flex flex-col gap-1 py-2"
															onclick={(e) => e.stopPropagation()}
														>
															<!-- Row 1: Deduction name + Tax type badge + Delete -->
															<div class="flex items-center justify-between">
																<div class="flex items-center gap-2">
																	<span class="text-body-content text-surface-700"
																		>{deductionLabel}</span
																	>
																	{#if taxType}
																		<span
																			class="text-caption px-1.5 py-0.5 rounded {taxType ===
																			'Pre-tax'
																				? 'bg-primary-100 text-primary-700'
																				: 'bg-surface-100 text-surface-600'}"
																		>
																			{taxType}
																		</span>
																	{/if}
																</div>
																<button
																	class="p-1 bg-transparent border-none text-error-500 cursor-pointer rounded hover:bg-error-50 hover:text-error-600"
																	title="Remove"
																	onclick={() => handleRemoveAdjustment(record, adjIdx)}
																>
																	<i class="fas fa-times text-xs"></i>
																</button>
															</div>
															<!-- Row 2: Note (if custom deduction, show readonly) + Amount -->
															<div class="flex items-center gap-2 pl-4">
																{#if adj.customDeductionId}
																	<!-- For custom deductions, show a simple amount input -->
																	<span class="flex-1 text-body-small text-surface-500">Amount</span
																	>
																{:else}
																	<!-- For ad-hoc deductions, allow note editing -->
																	<input
																		type="text"
																		class="flex-1 py-1 px-2 border border-surface-200 rounded text-body-small focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
																		value={adj.description}
																		placeholder="Note"
																		onchange={(e) =>
																			handleUpdateAdjustment(record, adjIdx, {
																				description: e.currentTarget.value
																			})}
																	/>
																{/if}
																<input
																	type="number"
																	class="amount-input w-24 py-1 px-2 border border-surface-300 rounded text-body-small text-right focus:outline-none focus:border-primary-500 focus:ring-2 focus:ring-primary-100"
																	value={adj.amount}
																	step="0.01"
																	min="0"
																	onchange={(e) => {
																		let val = parseFloat(e.currentTarget.value) || 0;
																		// Deductions cannot be negative
																		if (val < 0) val = 0;
																		e.currentTarget.value = val.toString();
																		handleUpdateAdjustment(record, adjIdx, { amount: val });
																	}}
																/>
															</div>
														</div>
													{/each}

													<!-- Add Deduction Button with Dropdown -->
													<!-- svelte-ignore a11y_no_static_element_interactions -->
													<!-- svelte-ignore a11y_click_events_have_key_events -->
													<div class="relative" onclick={(e) => e.stopPropagation()}>
														<button
															class="w-full flex items-center justify-center gap-2 py-2 bg-surface-50 border border-dashed border-surface-300 rounded text-body-small text-surface-600 cursor-pointer transition-all duration-150 hover:bg-primary-50 hover:border-primary-300 hover:text-primary-600"
															onclick={() => {
																showDeductionsMenu =
																	showDeductionsMenu === record.id ? null : record.id;
																showEarningsMenu = null;
															}}
														>
															<i class="fas fa-plus text-xs"></i>
															Add
															<i class="fas fa-chevron-up text-xs"></i>
														</button>

														{#if showDeductionsMenu === record.id}
															<div
																class="absolute left-0 bottom-full mb-1 bg-white border border-surface-200 rounded-lg shadow-lg z-20 min-w-[200px] py-1"
															>
																<!-- Custom deductions from pay group -->
																{#if payGroup.deductionsConfig?.customDeductions && payGroup.deductionsConfig.customDeductions.length > 0}
																	{#each payGroup.deductionsConfig.customDeductions as customDed (customDed.name)}
																		<button
																			class="w-full px-3 py-2 text-left text-body-small text-surface-700 hover:bg-surface-50 flex items-center justify-between border-none bg-transparent cursor-pointer"
																			onclick={() => handleAddCustomDeduction(record, customDed)}
																		>
																			<div class="flex items-center gap-2">
																				<span>➖</span>
																				<span>{customDed.name}</span>
																			</div>
																			<span
																				class="text-caption px-1.5 py-0.5 rounded {customDed.taxTreatment ===
																				'pre_tax'
																					? 'bg-primary-100 text-primary-700'
																					: 'bg-surface-100 text-surface-500'}"
																			>
																				{customDed.taxTreatment === 'pre_tax' ? 'Pre' : 'Post'}
																			</span>
																		</button>
																	{/each}
																	<div class="border-t border-surface-100 my-1"></div>
																{/if}
																<!-- Other/Ad-hoc deduction option -->
																<button
																	class="w-full px-3 py-2 text-left text-body-small text-surface-700 hover:bg-surface-50 flex items-center gap-2 border-none bg-transparent cursor-pointer"
																	onclick={() => handleAddAdjustment(record, 'deduction')}
																>
																	<span>📝</span>
																	<span>Other Deduction</span>
																</button>
															</div>
														{/if}
													</div>

													<!-- Total Deductions -->
													<div
														class="flex justify-between items-center pt-2 border-t border-surface-200 font-semibold"
													>
														<span class="text-body-content text-surface-600">Total</span>
														<span class="text-body-content text-surface-800"
															>{formatCurrency(record.totalDeductions)}</span
														>
													</div>
												</div>
											</div>

											<!-- LEAVE Column -->
											<div class="flex flex-col gap-3">
												<h4
													class="text-caption font-semibold text-surface-600 uppercase tracking-wider m-0 pb-2 border-b border-surface-200"
												>
													Leave
												</h4>
												<div class="flex flex-col gap-2">
													<!-- Vacation Used -->
													{#if true}
														{@const vacationHours = getLeaveHours(record, 'vacation')}
														{@const vacationPay = calculateVacationPay(record, vacationHours)}
														{@const availableVacationDollars =
															(record.vacationBalance ?? 0) +
															record.vacationAccrued -
															(record.vacationPayPaid ?? 0)}
														{@const vacationDisabled =
															record.vacationPayoutMethod === 'accrual' &&
															availableVacationDollars <= 0}
														{@const insufficientBalance = hasInsufficientBalance(record)}
														{@const availableSickHours = record.sickBalanceHours ?? 0}
														<!-- svelte-ignore a11y_no_static_element_interactions -->
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<div class="flex flex-col gap-1" onclick={(e) => e.stopPropagation()}>
															<div class="flex justify-between items-center gap-2">
																<span class="text-body-content text-surface-600">Vacation Used</span
																>
																<div class="flex items-center gap-1">
																	<input
																		type="number"
																		class="w-16 py-1 px-2 border rounded text-body-small text-center focus:outline-none focus:ring-2 {vacationDisabled
																			? 'bg-surface-100 text-surface-400 cursor-not-allowed border-surface-200'
																			: insufficientBalance
																				? 'border-error-400 focus:border-error-500 focus:ring-error-100'
																				: 'border-surface-300 focus:border-primary-500 focus:ring-primary-100'}"
																		value={vacationHours}
																		min="0"
																		step="0.5"
																		disabled={vacationDisabled}
																		onchange={(e) =>
																			handleLeaveChange(
																				record,
																				'vacation',
																				parseFloat(e.currentTarget.value) || 0
																			)}
																	/>
																	<span class="text-caption text-surface-500">hrs</span>
																</div>
															</div>
															<!-- Show calculated vacation pay when hours > 0 -->
															{#if vacationHours > 0}
																<div class="flex justify-between items-center pl-4">
																	<span class="text-caption text-surface-500"
																		>= Vacation Pay ({vacationHours} hrs)</span
																	>
																	<span class="text-body-small text-surface-700 font-medium"
																		>{formatCurrency(vacationPay)}</span
																	>
																</div>
															{/if}
															<!-- Disabled hint -->
															{#if vacationDisabled}
																<div class="flex items-center gap-1 pl-4 text-surface-500">
																	<i class="fas fa-info-circle text-xs"></i>
																	<span class="text-caption">No vacation balance available</span>
																</div>
															{/if}
															<!-- Insufficient balance warning -->
															{#if insufficientBalance && !vacationDisabled}
																<div class="flex items-center gap-1 pl-4 text-error-600">
																	<i class="fas fa-exclamation-triangle text-xs"></i>
																	<span class="text-caption">Insufficient balance</span>
																</div>
															{/if}
														</div>

														<!-- Sick Used -->
														{@const sickHours = getLeaveHours(record, 'sick')}
														{@const paidSickHours = Math.min(sickHours, availableSickHours)}
														{@const unpaidSickHours = Math.max(0, sickHours - availableSickHours)}
														<!-- svelte-ignore a11y_no_static_element_interactions -->
														<!-- svelte-ignore a11y_click_events_have_key_events -->
														<div class="flex flex-col gap-1" onclick={(e) => e.stopPropagation()}>
															<div class="flex justify-between items-center gap-2">
																<span class="text-body-content text-surface-600">Sick Used</span>
																<div class="flex items-center gap-1">
																	<input
																		type="number"
																		class="w-16 py-1 px-2 border rounded text-body-small text-center focus:outline-none focus:ring-2 border-surface-300 focus:border-primary-500 focus:ring-primary-100"
																		value={sickHours}
																		min="0"
																		step="0.5"
																		onchange={(e) =>
																			handleLeaveChange(
																				record,
																				'sick',
																				parseFloat(e.currentTarget.value) || 0
																			)}
																	/>
																	<span class="text-caption text-surface-500">hrs</span>
																</div>
															</div>
															<!-- Sick hours breakdown when entered -->
															{#if sickHours > 0}
																<div class="pl-4 space-y-0.5">
																	{#if paidSickHours > 0}
																		<div class="flex justify-between text-caption text-success-600">
																			<span>└ Paid Sick</span>
																			<span>{paidSickHours} hrs</span>
																		</div>
																	{/if}
																	{#if unpaidSickHours > 0}
																		<div class="flex justify-between text-caption text-warning-600">
																			<span>└ Unpaid (deducted)</span>
																			<span>{unpaidSickHours} hrs</span>
																		</div>
																	{/if}
																</div>
															{/if}
														</div>
													{/if}

													<!-- Separator -->
													<div class="border-t border-surface-200 my-1"></div>

													<!-- Available Balances -->
													<div class="space-y-1">
														<!-- Vacation Balance (for accrual method employees) -->
														{#if record.vacationPayoutMethod === 'accrual'}
															<div class="flex justify-between items-center">
																<span class="text-body-content text-surface-600"
																	>Available Vacation</span
																>
																<span
																	class="text-body-content font-medium {hasInsufficientBalance(
																		record
																	)
																		? 'text-error-600'
																		: 'text-surface-800'}"
																>
																	{formatCurrency(
																		(record.vacationBalance ?? 0) +
																			record.vacationAccrued -
																			(record.vacationPayPaid ?? 0)
																	)}
																</span>
															</div>
														{:else if record.vacationPayoutMethod === 'pay_as_you_go'}
															<div class="flex items-center gap-1 text-surface-500">
																<i class="fas fa-info-circle text-xs"></i>
																<span class="text-caption">Vacation: Pay-as-you-go</span>
															</div>
														{/if}

														<!-- Sick Balance -->
														<div class="flex justify-between items-center">
															<span class="text-body-content text-surface-600">Available Sick</span>
															<span class="text-body-content font-medium text-surface-800">
																{record.sickBalanceHours ?? 0} hrs
															</span>
														</div>
													</div>
												</div>
											</div>
										</div>

										<!-- Net Pay Summary -->
										<div
											class="flex justify-end items-center gap-4 mt-4 pt-4 border-t-2 border-surface-200"
										>
											<span class="text-body-content font-semibold text-surface-600">Net Pay</span>
											<span class="text-title font-bold text-success-600"
												>{formatCurrency(record.netPay)}</span
											>
										</div>
									</div>
								</td>
							</tr>
						{/if}
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<style>
	/* Hide number input spinners */
	.amount-input::-webkit-inner-spin-button,
	.amount-input::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}
	.amount-input {
		appearance: textfield;
		-moz-appearance: textfield;
	}
</style>
