<script lang="ts">
	import type { PayrollRun, PayrollRecord } from '$lib/types/payroll';
	import { Avatar } from '$lib/components/shared';
	import PayrollRecordExpandedRow from './PayrollRecordExpandedRow.svelte';
	import PaystubStatusBadge from './PaystubStatusBadge.svelte';
	import LeaveTypeBadge from './LeaveTypeBadge.svelte';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		payrollRun: PayrollRun;
		payrollRecords: PayrollRecord[];
		expandedRecordId: string | null;
		onToggleExpand: (id: string) => void;
		onDownloadPaystub?: (record: PayrollRecord) => void;
		onResendPaystub?: (record: PayrollRecord) => void;
		onLeaveClick?: (record: PayrollRecord) => void;
	}

	let {
		payrollRun,
		payrollRecords,
		expandedRecordId,
		onToggleExpand,
		onDownloadPaystub,
		onResendPaystub,
		onLeaveClick
	}: Props = $props();

	// Helper to get leave summary for a record
	function getLeaveDisplay(record: PayrollRecord): {
		hasLeave: boolean;
		display: string;
		entries: { type: 'vacation' | 'sick'; hours: number }[];
	} {
		const entries = record.leaveEntries || [];
		if (entries.length === 0) {
			return { hasLeave: false, display: '-', entries: [] };
		}

		// Group by leave type
		const vacationHours = entries
			.filter((e) => e.leaveType === 'vacation')
			.reduce((sum, e) => sum + e.hours, 0);
		const sickHours = entries
			.filter((e) => e.leaveType === 'sick')
			.reduce((sum, e) => sum + e.hours, 0);

		const parts: { type: 'vacation' | 'sick'; hours: number }[] = [];
		if (vacationHours > 0) parts.push({ type: 'vacation', hours: vacationHours });
		if (sickHours > 0) parts.push({ type: 'sick', hours: sickHours });

		return { hasLeave: true, display: '', entries: parts };
	}

	// Show paystub column only when approved or paid
	const showPaystubColumn = $derived(
		payrollRun.status === 'approved' || payrollRun.status === 'paid'
	);

	// Track which row has open actions menu
	let openActionsMenuId = $state<string | null>(null);

	function toggleActionsMenu(id: string, event: MouseEvent) {
		event.stopPropagation();
		openActionsMenuId = openActionsMenuId === id ? null : id;
	}

	function closeActionsMenu() {
		openActionsMenuId = null;
	}

	function handleDownload(record: PayrollRecord, event: MouseEvent) {
		event.stopPropagation();
		closeActionsMenu();
		onDownloadPaystub?.(record);
	}

	function handleResend(record: PayrollRecord, event: MouseEvent) {
		event.stopPropagation();
		closeActionsMenu();
		onResendPaystub?.(record);
	}

	function handleRetry(record: PayrollRecord) {
		onResendPaystub?.(record);
	}

	const otherDeductionsTotal = $derived(
		payrollRecords.reduce(
			(sum, r) => sum + r.rrsp + r.unionDues + r.garnishments + r.otherDeductions,
			0
		)
	);
</script>

<section class="section">
	<h2 class="section-title">Employee Payroll Details</h2>
	<div class="table-container">
		<table class="payroll-table">
			<thead>
				<tr>
					<th class="col-expand"></th>
					<th class="col-employee">Employee</th>
					<th class="col-amount">Gross</th>
					<th class="col-leave">Leave</th>
					<th class="col-amount">CPP</th>
					<th class="col-amount">EI</th>
					<th class="col-amount">Fed Tax</th>
					<th class="col-amount">Prov Tax</th>
					<th class="col-amount">Other Ded.</th>
					<th class="col-amount highlight-col">Net Pay</th>
					{#if showPaystubColumn}
						<th class="col-paystub">Paystub</th>
						<th class="col-actions"></th>
					{/if}
				</tr>
			</thead>
			<tbody>
				{#each payrollRecords as record (record.id)}
					{@const leaveInfo = getLeaveDisplay(record)}
					<!-- Main Row -->
					<tr
						class="main-row"
						class:expanded={expandedRecordId === record.id}
						onclick={() => onToggleExpand(record.id)}
					>
						<td class="col-expand">
							<button class="expand-btn" aria-label="Expand row details">
								<i
									class="fas"
									class:fa-chevron-down={expandedRecordId === record.id}
									class:fa-chevron-right={expandedRecordId !== record.id}
								></i>
							</button>
						</td>
						<td class="col-employee">
							<div class="employee-cell">
								<Avatar name={record.employeeName} />
								<div class="employee-info">
									<span class="employee-name">{record.employeeName}</span>
									<span class="employee-province">{record.employeeProvince}</span>
								</div>
							</div>
						</td>
						<td class="col-amount">{formatCurrency(record.totalGross)}</td>
						<td
							class="col-leave"
							onclick={(e) => {
								e.stopPropagation();
								onLeaveClick?.(record);
							}}
						>
							{#if leaveInfo.hasLeave}
								<div class="leave-badges">
									{#each leaveInfo.entries as entry (entry.type)}
										<LeaveTypeBadge type={entry.type} hours={entry.hours} compact />
									{/each}
								</div>
							{:else}
								<span class="no-leave">-</span>
							{/if}
						</td>
						<td class="col-amount">{formatCurrency(record.cppEmployee)}</td>
						<td class="col-amount">{formatCurrency(record.eiEmployee)}</td>
						<td class="col-amount">{formatCurrency(record.federalTax)}</td>
						<td class="col-amount">{formatCurrency(record.provincialTax)}</td>
						<td class="col-amount">
							{formatCurrency(
								record.rrsp + record.unionDues + record.garnishments + record.otherDeductions
							)}
						</td>
						<td class="col-amount net-pay">{formatCurrency(record.netPay)}</td>
						{#if showPaystubColumn}
							<td class="col-paystub" onclick={(e) => e.stopPropagation()}>
								<PaystubStatusBadge
									status={record.paystubStatus || 'pending'}
									sentAt={record.paystubSentAt}
									onRetry={() => handleRetry(record)}
								/>
							</td>
							<td class="col-actions" onclick={(e) => e.stopPropagation()}>
								<div class="actions-wrapper">
									<button
										class="actions-btn"
										onclick={(e) => toggleActionsMenu(record.id, e)}
										aria-label="Actions"
									>
										<i class="fas fa-ellipsis-v"></i>
									</button>
									{#if openActionsMenuId === record.id}
										<div class="actions-menu">
											<button class="menu-item" onclick={(e) => handleDownload(record, e)}>
												<i class="fas fa-download"></i>
												<span>Download Paystub</span>
											</button>
											<button class="menu-item" onclick={(e) => handleResend(record, e)}>
												<i class="fas fa-paper-plane"></i>
												<span>Resend Paystub</span>
											</button>
										</div>
									{/if}
								</div>
							</td>
						{/if}
					</tr>

					<!-- Expanded Detail Row -->
					{#if expandedRecordId === record.id}
						<PayrollRecordExpandedRow {record} />
					{/if}
				{/each}
			</tbody>
			<tfoot>
				<tr class="totals-row">
					<td></td>
					<td class="col-employee"><strong>TOTALS</strong></td>
					<td class="col-amount"><strong>{formatCurrency(payrollRun.totalGross)}</strong></td>
					<td class="col-leave"></td>
					<td class="col-amount"><strong>{formatCurrency(payrollRun.totalCppEmployee)}</strong></td>
					<td class="col-amount"><strong>{formatCurrency(payrollRun.totalEiEmployee)}</strong></td>
					<td class="col-amount"><strong>{formatCurrency(payrollRun.totalFederalTax)}</strong></td>
					<td class="col-amount"
						><strong>{formatCurrency(payrollRun.totalProvincialTax)}</strong></td
					>
					<td class="col-amount"><strong>{formatCurrency(otherDeductionsTotal)}</strong></td>
					<td class="col-amount net-pay"
						><strong>{formatCurrency(payrollRun.totalNetPay)}</strong></td
					>
					{#if showPaystubColumn}
						<td></td>
						<td></td>
					{/if}
				</tr>
			</tfoot>
		</table>
	</div>
</section>

<style>
	/* Section */
	.section {
		margin-bottom: var(--spacing-8);
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4);
	}

	/* Table */
	.table-container {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.payroll-table {
		width: 100%;
		border-collapse: collapse;
	}

	.payroll-table th {
		text-align: left;
		padding: var(--spacing-4) var(--spacing-4);
		background: var(--color-surface-50);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		border-bottom: 1px solid var(--color-surface-200);
		white-space: nowrap;
	}

	.payroll-table th.col-amount {
		text-align: right;
	}

	.payroll-table th.highlight-col {
		background: var(--color-primary-50);
	}

	.payroll-table td {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.payroll-table .main-row {
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.payroll-table .main-row:hover td {
		background: var(--color-surface-50);
	}

	.payroll-table .main-row.expanded td {
		background: var(--color-primary-50);
		border-bottom-color: var(--color-primary-100);
	}

	.payroll-table .totals-row td {
		background: var(--color-surface-50);
		border-top: 2px solid var(--color-surface-200);
		font-weight: var(--font-weight-semibold);
	}

	.col-expand {
		width: 40px;
		text-align: center;
	}

	.col-employee {
		min-width: 180px;
	}

	.col-amount {
		text-align: right;
		font-family: monospace;
		white-space: nowrap;
	}

	.net-pay {
		color: var(--color-success-700);
		font-weight: var(--font-weight-semibold);
	}

	/* Leave Column */
	.col-leave {
		min-width: 90px;
		text-align: center;
		cursor: pointer;
	}

	.col-leave:hover {
		background: var(--color-surface-100);
	}

	.leave-badges {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-1);
		justify-content: center;
	}

	.no-leave {
		color: var(--color-surface-400);
	}

	.expand-btn {
		padding: var(--spacing-1);
		border: none;
		background: transparent;
		color: var(--color-surface-400);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.expand-btn:hover {
		color: var(--color-primary-600);
	}

	.employee-cell {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.employee-info {
		display: flex;
		flex-direction: column;
	}

	.employee-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.employee-province {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Paystub Column */
	.col-paystub {
		min-width: 120px;
	}

	/* Actions Column */
	.col-actions {
		width: 50px;
		text-align: center;
	}

	.actions-wrapper {
		position: relative;
	}

	.actions-btn {
		padding: var(--spacing-2);
		border: none;
		background: transparent;
		color: var(--color-surface-500);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.actions-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.actions-menu {
		position: absolute;
		right: 0;
		top: 100%;
		z-index: 100;
		background: white;
		border-radius: var(--radius-lg);
		box-shadow: var(--shadow-md3-2);
		min-width: 180px;
		overflow: hidden;
		animation: fadeIn 0.15s ease-out;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(-4px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	.menu-item {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		width: 100%;
		padding: var(--spacing-3) var(--spacing-4);
		border: none;
		background: transparent;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		cursor: pointer;
		text-align: left;
		transition: var(--transition-fast);
	}

	.menu-item:hover {
		background: var(--color-surface-50);
	}

	.menu-item i {
		width: 16px;
		color: var(--color-surface-500);
	}

	/* Responsive */
	@media (max-width: 768px) {
		.table-container {
			overflow-x: auto;
		}

		.payroll-table {
			min-width: 800px;
		}
	}
</style>
