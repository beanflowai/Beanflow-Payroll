<script lang="ts">
	import type {
		PayrollRunPayGroup,
		PayrollRecord,
		EmployeePayrollInput,
		EarningsBreakdown,
		Adjustment
	} from '$lib/types/payroll';
	import {
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		ADJUSTMENT_TYPE_LABELS,
		createDefaultPayrollInput
	} from '$lib/types/payroll';
	import { PayrollRecordExpandedRow, LeaveTypeBadge } from '$lib/components/payroll';

	interface Props {
		payGroup: PayrollRunPayGroup;
		expandedRecordId: string | null;
		onToggleExpand: (id: string) => void;
		onUpdateRecord: (recordId: string, employeeId: string, updates: Partial<EmployeePayrollInput>) => void;
	}

	let { payGroup, expandedRecordId, onToggleExpand, onUpdateRecord }: Props = $props();

	let isCollapsed = $state(false);

	// Local input state for editing (will be synced to parent on change)
	let localInputMap = $state<Map<string, Partial<EmployeePayrollInput>>>(new Map());

	// Track which records have leave/adjustment editing open
	let showLeaveEdit = $state<Set<string>>(new Set());
	let showAdjustmentEdit = $state<Set<string>>(new Set());

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}

	function formatPeriod(start: string, end: string): string {
		const startDate = new Date(start);
		const endDate = new Date(end);
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

	function handleHoursChange(record: PayrollRecord, field: 'regularHours' | 'overtimeHours', value: number) {
		const current = getLocalInput(record.id);
		const updated = { ...current, [field]: value };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { [field]: value });
	}

	function handleLeaveChange(record: PayrollRecord, type: 'vacation' | 'sick', hours: number) {
		const current = getLocalInput(record.id);
		// Merge local edits with existing record data
		const existingLeaves = current.leaveEntries ?? record.inputData?.leaveEntries ?? [];
		const newLeaveEntries = existingLeaves.filter((l) => l.type !== type);
		if (hours > 0) {
			newLeaveEntries.push({ type, hours });
		}
		const updated = { ...current, leaveEntries: newLeaveEntries };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { leaveEntries: newLeaveEntries });
	}

	function handleAddAdjustment(record: PayrollRecord) {
		const current = getLocalInput(record.id);
		// Merge local edits with existing record data
		const existingAdjs = current.adjustments ?? record.inputData?.adjustments ?? [];
		const newAdj: Adjustment = {
			id: crypto.randomUUID(),
			type: 'bonus',
			amount: 0,
			description: '',
			taxable: true
		};
		const newAdjs = [...existingAdjs, newAdj];
		const updated = { ...current, adjustments: newAdjs };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { adjustments: newAdjs });
	}

	function handleUpdateAdjustment(record: PayrollRecord, idx: number, updates: Partial<Adjustment>) {
		const current = getLocalInput(record.id);
		// Merge local edits with existing record data
		const existingAdjs = current.adjustments ?? record.inputData?.adjustments ?? [];
		const newAdjs = [...existingAdjs];
		newAdjs[idx] = { ...newAdjs[idx], ...updates };
		const updated = { ...current, adjustments: newAdjs };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { adjustments: newAdjs });
	}

	function handleRemoveAdjustment(record: PayrollRecord, idx: number) {
		const current = getLocalInput(record.id);
		// Merge local edits with existing record data
		const existingAdjs = current.adjustments ?? record.inputData?.adjustments ?? [];
		const newAdjs = existingAdjs.filter((_: Adjustment, i: number) => i !== idx);
		const updated = { ...current, adjustments: newAdjs };
		localInputMap = new Map(localInputMap).set(record.id, updated);
		onUpdateRecord(record.id, record.employeeId, { adjustments: newAdjs });
	}

	function toggleLeaveEdit(recordId: string) {
		const newSet = new Set(showLeaveEdit);
		if (newSet.has(recordId)) {
			newSet.delete(recordId);
		} else {
			newSet.add(recordId);
		}
		showLeaveEdit = newSet;
	}

	function toggleAdjustmentEdit(recordId: string) {
		const newSet = new Set(showAdjustmentEdit);
		if (newSet.has(recordId)) {
			newSet.delete(recordId);
		} else {
			newSet.add(recordId);
		}
		showAdjustmentEdit = newSet;
	}

	function getLeaveHours(record: PayrollRecord, type: 'vacation' | 'sick'): number {
		// Check local edits first
		const local = getLocalInput(record.id);
		const localEntry = local.leaveEntries?.find((l: { type: string; hours: number }) => l.type === type);
		if (localEntry !== undefined) {
			return localEntry.hours;
		}
		// Fall back to record's existing input_data
		const recordEntry = record.inputData?.leaveEntries?.find((l: { type: string; hours: number }) => l.type === type);
		return recordEntry?.hours ?? 0;
	}

	function getAdjustments(record: PayrollRecord): Adjustment[] {
		// Check local edits first
		const local = getLocalInput(record.id);
		if (local.adjustments !== undefined) {
			return local.adjustments;
		}
		// Fall back to record's existing input_data
		return record.inputData?.adjustments ?? [];
	}
</script>

<div class="pay-group-section" class:collapsed={isCollapsed}>
	<!-- Section Header -->
	<button class="section-header" onclick={toggleCollapse}>
		<div class="header-left">
			<i class="fas fa-chevron-{isCollapsed ? 'right' : 'down'} collapse-icon"></i>
			<div class="group-badge">
				<i class="fas fa-tag"></i>
			</div>
			<div class="group-info">
				<h3 class="group-name">{payGroup.payGroupName}</h3>
				<div class="group-meta">
					<span class="meta-item">
						{PAY_FREQUENCY_LABELS[payGroup.payFrequency] || payGroup.payFrequency}
					</span>
					<span class="meta-divider"></span>
					<span class="meta-item">
						{EMPLOYMENT_TYPE_LABELS[payGroup.employmentType] || payGroup.employmentType}
					</span>
					<span class="meta-divider"></span>
					<span class="meta-item">
						{formatPeriod(payGroup.periodStart, payGroup.periodEnd)}
					</span>
				</div>
			</div>
		</div>
		<div class="header-right">
			<div class="header-stats">
				<div class="stat">
					<span class="stat-value">{payGroup.totalEmployees}</span>
					<span class="stat-label">Employees</span>
				</div>
				<div class="stat">
					<span class="stat-value">{formatCurrency(payGroup.totalGross)}</span>
					<span class="stat-label">Gross</span>
				</div>
				<div class="stat">
					<span class="stat-value">{formatCurrency(payGroup.totalDeductions)}</span>
					<span class="stat-label">Deductions</span>
				</div>
				<div class="stat">
					<span class="stat-value net-pay-value">{formatCurrency(payGroup.totalNetPay)}</span>
					<span class="stat-label">Net Pay</span>
				</div>
			</div>
		</div>
	</button>

	<!-- Section Content -->
	{#if !isCollapsed}
		<div class="section-content">
			<table class="records-table">
				<thead>
					<tr>
						<th class="col-employee">Employee</th>
						<th class="col-rate">Rate/Salary</th>
						<th class="col-hours">Hours</th>
						<th class="col-overtime">OT</th>
						<th class="col-gross">Gross</th>
						<th class="col-deductions">Deductions</th>
						<th class="col-net">Net Pay</th>
						<th class="col-actions"></th>
					</tr>
				</thead>
				<tbody>
					{#each payGroup.records as record (record.id)}
						<tr
							class:expanded={expandedRecordId === record.id}
							onclick={() => onToggleExpand(record.id)}
						>
							<td class="col-employee">
								<div class="employee-info">
									<span class="employee-name">{record.employeeName}</span>
									<span class="employee-type">{record.compensationType}</span>
								</div>
							</td>
							<td class="col-rate">
								<span class="rate-value">
									{#if record.compensationType === 'salaried' && record.annualSalary}
										{formatCurrency(record.annualSalary)}/yr
									{:else if record.hourlyRate}
										{formatCurrency(record.hourlyRate)}/hr
									{:else}
										--
									{/if}
								</span>
							</td>
							<td class="col-hours" onclick={(e) => e.stopPropagation()}>
								{#if record.compensationType === 'hourly'}
									<input
										type="number"
										class="hours-input"
										value={record.regularHoursWorked ?? 0}
										min="0"
										step="0.5"
										onchange={(e) =>
											handleHoursChange(record, 'regularHours', parseFloat(e.currentTarget.value) || 0)}
									/>
								{:else}
									<span class="salaried-indicator">Salary</span>
								{/if}
							</td>
							<td class="col-overtime" onclick={(e) => e.stopPropagation()}>
								<input
									type="number"
									class="hours-input small"
									value={record.overtimeHoursWorked ?? 0}
									min="0"
									step="0.5"
									onchange={(e) =>
										handleHoursChange(record, 'overtimeHours', parseFloat(e.currentTarget.value) || 0)}
								/>
							</td>
							<td class="col-gross">{formatCurrency(record.totalGross)}</td>
							<td class="col-deductions">{formatCurrency(record.totalDeductions)}</td>
							<td class="col-net">
								<span class="net-pay">{formatCurrency(record.netPay)}</span>
							</td>
							<td class="col-actions">
								<button
									class="expand-btn"
									title={expandedRecordId === record.id ? 'Collapse' : 'Expand'}
								>
									<i class="fas fa-chevron-{expandedRecordId === record.id ? 'up' : 'down'}"></i>
								</button>
							</td>
						</tr>
						{#if expandedRecordId === record.id}
							<tr class="expanded-row">
								<td colspan="8">
									<div class="expanded-content">
										<div class="expanded-grid">
											<!-- Employee Info Column -->
											<div class="detail-column">
												<h4 class="column-title">Employee Info</h4>
												<div class="detail-items">
													<div class="detail-item">
														<span class="detail-label">Province</span>
														<span class="detail-value">
															<span class="province-badge">{record.employeeProvince}</span>
														</span>
													</div>
												</div>
											</div>

											<!-- Earnings Column -->
											<div class="detail-column">
												<h4 class="column-title">Earnings</h4>
												<div class="detail-items">
													<div class="detail-item">
														<span class="detail-label">Regular Pay</span>
														<span class="detail-value">{formatCurrency(record.grossRegular)}</span>
													</div>
													{#if record.grossOvertime > 0}
														<div class="detail-item">
															<span class="detail-label">Overtime</span>
															<span class="detail-value">{formatCurrency(record.grossOvertime)}</span>
														</div>
													{/if}
													{#if record.holidayPay > 0}
														<div class="detail-item">
															<span class="detail-label">Holiday Pay</span>
															<span class="detail-value">{formatCurrency(record.holidayPay)}</span>
														</div>
													{/if}
													{#if record.vacationPayPaid > 0}
														<div class="detail-item">
															<span class="detail-label">Vacation Pay</span>
															<span class="detail-value">{formatCurrency(record.vacationPayPaid)}</span>
														</div>
													{/if}
													<div class="detail-item total">
														<span class="detail-label">Total Gross</span>
														<span class="detail-value">{formatCurrency(record.totalGross)}</span>
													</div>
												</div>
											</div>

											<!-- Deductions Column -->
											<div class="detail-column">
												<h4 class="column-title">Deductions</h4>
												<div class="detail-items">
													<div class="detail-item">
														<span class="detail-label">CPP</span>
														<span class="detail-value">{formatCurrency(record.cppEmployee + record.cppAdditional)}</span>
													</div>
													<div class="detail-item">
														<span class="detail-label">EI</span>
														<span class="detail-value">{formatCurrency(record.eiEmployee)}</span>
													</div>
													<div class="detail-item">
														<span class="detail-label">Federal Tax</span>
														<span class="detail-value">{formatCurrency(record.federalTax)}</span>
													</div>
													<div class="detail-item">
														<span class="detail-label">Provincial Tax</span>
														<span class="detail-value">{formatCurrency(record.provincialTax)}</span>
													</div>
													<div class="detail-item total">
														<span class="detail-label">Total Deductions</span>
														<span class="detail-value">{formatCurrency(record.totalDeductions)}</span>
													</div>
												</div>
											</div>

											<!-- Quick Edit Column -->
											<div class="detail-column edit-column">
												<h4 class="column-title">Quick Edit</h4>
												<div class="edit-actions">
													<!-- Leave Section -->
													<button
														class="edit-btn"
														class:active={showLeaveEdit.has(record.id)}
														onclick={(e) => {
															e.stopPropagation();
															toggleLeaveEdit(record.id);
														}}
													>
														<i class="fas fa-calendar-alt"></i>
														{showLeaveEdit.has(record.id) ? 'Hide Leave' : 'Add Leave'}
													</button>
													{#if showLeaveEdit.has(record.id)}
														<div class="inline-edit-section" onclick={(e) => e.stopPropagation()}>
															<div class="leave-inputs">
																<div class="leave-input-row">
																	<label class="leave-label">Vacation</label>
																	<input
																		type="number"
																		class="leave-input"
																		value={getLeaveHours(record, 'vacation')}
																		min="0"
																		step="0.5"
																		placeholder="0"
																		onchange={(e) =>
																			handleLeaveChange(record, 'vacation', parseFloat(e.currentTarget.value) || 0)}
																	/>
																	<span class="leave-unit">hrs</span>
																</div>
																<div class="leave-input-row">
																	<label class="leave-label">Sick</label>
																	<input
																		type="number"
																		class="leave-input"
																		value={getLeaveHours(record, 'sick')}
																		min="0"
																		step="0.5"
																		placeholder="0"
																		onchange={(e) =>
																			handleLeaveChange(record, 'sick', parseFloat(e.currentTarget.value) || 0)}
																	/>
																	<span class="leave-unit">hrs</span>
																</div>
															</div>
														</div>
													{/if}

													<!-- Adjustment Section -->
													<button
														class="edit-btn"
														class:active={showAdjustmentEdit.has(record.id)}
														onclick={(e) => {
															e.stopPropagation();
															toggleAdjustmentEdit(record.id);
														}}
													>
														<i class="fas fa-sliders-h"></i>
														{showAdjustmentEdit.has(record.id) ? 'Hide Adjustments' : 'Adjustments'}
													</button>
													{#if showAdjustmentEdit.has(record.id)}
														<div class="inline-edit-section" onclick={(e) => e.stopPropagation()}>
															<div class="adjustments-list">
																{#each getAdjustments(record) as adj, idx (adj.id)}
																	<div class="adjustment-item">
																		<select
																			class="adj-type-select"
																			value={adj.type}
																			onchange={(e) =>
																				handleUpdateAdjustment(record, idx, { type: e.currentTarget.value as Adjustment['type'] })}
																		>
																			{#each Object.entries(ADJUSTMENT_TYPE_LABELS) as [typeKey, typeInfo]}
																				<option value={typeKey}>{typeInfo.label}</option>
																			{/each}
																		</select>
																		<input
																			type="number"
																			class="adj-amount-input"
																			value={adj.amount}
																			step="0.01"
																			placeholder="$0.00"
																			onchange={(e) =>
																				handleUpdateAdjustment(record, idx, { amount: parseFloat(e.currentTarget.value) || 0 })}
																		/>
																		<input
																			type="text"
																			class="adj-desc-input"
																			value={adj.description}
																			placeholder="Description"
																			onchange={(e) =>
																				handleUpdateAdjustment(record, idx, { description: e.currentTarget.value })}
																		/>
																		<label class="adj-taxable">
																			<input
																				type="checkbox"
																				checked={adj.taxable}
																				onchange={(e) =>
																					handleUpdateAdjustment(record, idx, { taxable: e.currentTarget.checked })}
																			/>
																			<span>Tax</span>
																		</label>
																		<button
																			class="adj-remove-btn"
																			title="Remove adjustment"
																			onclick={() => handleRemoveAdjustment(record, idx)}
																		>
																			<i class="fas fa-times"></i>
																		</button>
																	</div>
																{/each}
																<button
																	class="add-adj-btn"
																	onclick={() => handleAddAdjustment(record)}
																>
																	<i class="fas fa-plus"></i>
																	Add Adjustment
																</button>
															</div>
														</div>
													{/if}
												</div>
											</div>
										</div>

										<!-- Net Pay Summary -->
										<div class="net-pay-summary">
											<span class="net-pay-label">Net Pay</span>
											<span class="net-pay-amount">{formatCurrency(record.netPay)}</span>
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
	.pay-group-section {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
		margin-bottom: var(--spacing-4);
		border: 2px solid var(--color-warning-200);
	}

	.section-header {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-warning-50);
		border: none;
		cursor: pointer;
		transition: var(--transition-fast);
		text-align: left;
	}

	.section-header:hover {
		background: var(--color-warning-100);
	}

	.header-left {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.collapse-icon {
		font-size: 12px;
		color: var(--color-surface-500);
		width: 16px;
	}

	.group-badge {
		width: 36px;
		height: 36px;
		border-radius: var(--radius-md);
		background: var(--color-warning-100);
		color: var(--color-warning-700);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 14px;
	}

	.group-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.group-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.group-meta {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.meta-item {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.meta-divider {
		width: 4px;
		height: 4px;
		border-radius: 50%;
		background: var(--color-surface-300);
	}

	.header-right {
		display: flex;
		align-items: center;
	}

	.header-stats {
		display: flex;
		gap: var(--spacing-6);
	}

	.stat {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
	}

	.stat-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.stat-value.net-pay-value {
		color: var(--color-success-600);
	}

	.stat-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.section-content {
		border-top: 1px solid var(--color-warning-200);
	}

	/* Table Styles */
	.records-table {
		width: 100%;
		border-collapse: collapse;
	}

	.records-table th {
		text-align: left;
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.records-table td {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.records-table tbody tr {
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.records-table tbody tr:hover td {
		background: var(--color-surface-50);
	}

	.records-table tbody tr.expanded td {
		background: var(--color-warning-50);
	}

	.col-employee {
		width: 16%;
	}

	.col-rate {
		width: 12%;
	}

	.rate-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.col-hours,
	.col-overtime {
		width: 8%;
		text-align: center;
	}

	.records-table th.col-hours,
	.records-table th.col-overtime {
		text-align: center;
	}

	.col-gross,
	.col-deductions,
	.col-net {
		width: 15%;
		text-align: right;
	}

	.col-actions {
		width: 4%;
		text-align: right;
	}

	.records-table th.col-gross,
	.records-table th.col-deductions,
	.records-table th.col-net,
	.records-table th.col-actions {
		text-align: right;
	}

	.employee-info {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.employee-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-type {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		text-transform: capitalize;
	}

	.province-badge {
		display: inline-flex;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.hours-input {
		width: 70px;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-body-content);
		text-align: center;
	}

	.hours-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.hours-input.small {
		width: 50px;
	}

	.salaried-indicator {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-surface-100);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.net-pay {
		font-weight: var(--font-weight-semibold);
		color: var(--color-success-600);
	}

	.expand-btn {
		padding: var(--spacing-2);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.expand-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	/* Expanded Row Styles */
	.expanded-row td {
		padding: 0 !important;
		background: var(--color-warning-50) !important;
	}

	.expanded-content {
		padding: var(--spacing-4) var(--spacing-5);
	}

	.expanded-grid {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr 1fr;
		gap: var(--spacing-5);
	}

	.detail-column {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.column-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin: 0;
		padding-bottom: var(--spacing-2);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.detail-items {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.detail-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.detail-item.total {
		padding-top: var(--spacing-2);
		border-top: 1px solid var(--color-surface-200);
		font-weight: var(--font-weight-semibold);
	}

	.detail-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.detail-value {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
	}

	.edit-column {
		background: var(--color-surface-50);
		padding: var(--spacing-3);
		border-radius: var(--radius-md);
	}

	.edit-actions {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.edit-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-3);
		background: white;
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.edit-btn:hover {
		background: var(--color-primary-50);
		border-color: var(--color-primary-300);
		color: var(--color-primary-600);
	}

	.edit-btn.active {
		background: var(--color-primary-50);
		border-color: var(--color-primary-400);
		color: var(--color-primary-700);
	}

	/* Inline Edit Section */
	.inline-edit-section {
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		padding: var(--spacing-3);
		margin-top: var(--spacing-2);
	}

	/* Leave Inputs */
	.leave-inputs {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.leave-input-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.leave-label {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-600);
		width: 60px;
	}

	.leave-input {
		width: 70px;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-body-content);
		text-align: center;
	}

	.leave-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.leave-unit {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Adjustments List */
	.adjustments-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.adjustment-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		flex-wrap: wrap;
	}

	.adj-type-select {
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-body-small);
		background: white;
		min-width: 100px;
	}

	.adj-type-select:focus {
		outline: none;
		border-color: var(--color-primary-500);
	}

	.adj-amount-input {
		width: 90px;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-body-small);
		text-align: right;
	}

	.adj-amount-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
	}

	.adj-desc-input {
		flex: 1;
		min-width: 100px;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-body-small);
	}

	.adj-desc-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
	}

	.adj-taxable {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		cursor: pointer;
	}

	.adj-taxable input {
		cursor: pointer;
	}

	.adj-remove-btn {
		padding: var(--spacing-1);
		background: none;
		border: none;
		color: var(--color-error-500);
		cursor: pointer;
		border-radius: var(--radius-sm);
		transition: var(--transition-fast);
	}

	.adj-remove-btn:hover {
		background: var(--color-error-50);
		color: var(--color-error-600);
	}

	.add-adj-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2);
		background: var(--color-surface-50);
		border: 1px dashed var(--color-surface-300);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-body-small);
		color: var(--color-surface-600);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.add-adj-btn:hover {
		background: var(--color-primary-50);
		border-color: var(--color-primary-300);
		color: var(--color-primary-600);
	}

	.net-pay-summary {
		display: flex;
		justify-content: flex-end;
		align-items: center;
		gap: var(--spacing-4);
		margin-top: var(--spacing-4);
		padding-top: var(--spacing-4);
		border-top: 2px solid var(--color-surface-200);
	}

	.net-pay-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
	}

	.net-pay-amount {
		font-size: var(--font-size-title);
		font-weight: var(--font-weight-bold);
		color: var(--color-success-600);
	}

	@media (max-width: 1024px) {
		.header-stats {
			gap: var(--spacing-4);
		}

		.expanded-grid {
			grid-template-columns: 1fr 1fr 1fr;
		}
	}

	@media (max-width: 768px) {
		.section-header {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-3);
		}

		.header-right {
			width: 100%;
		}

		.header-stats {
			width: 100%;
			justify-content: space-between;
		}

		.stat {
			align-items: flex-start;
		}

		.expanded-grid {
			grid-template-columns: 1fr 1fr;
		}
	}
</style>
