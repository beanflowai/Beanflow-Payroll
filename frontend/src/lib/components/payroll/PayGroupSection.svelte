<script lang="ts">
	import type { PayrollRunPayGroup, PayrollRecord, PayrollRunStatus } from '$lib/types/payroll';
	import { PAY_FREQUENCY_LABELS, EMPLOYMENT_TYPE_LABELS } from '$lib/types/payroll';
	import { PayrollRecordExpandedRow, LeaveTypeBadge } from '$lib/components/payroll';

	interface Props {
		payGroup: PayrollRunPayGroup;
		runStatus: PayrollRunStatus;
		expandedRecordId: string | null;
		onToggleExpand: (id: string) => void;
		onDownloadPaystub?: (record: PayrollRecord) => void;
		onResendPaystub?: (record: PayrollRecord) => void;
		onLeaveClick?: (record: PayrollRecord) => void;
		onOvertimeClick?: (record: PayrollRecord) => void;
	}

	let {
		payGroup,
		runStatus,
		expandedRecordId,
		onToggleExpand,
		onDownloadPaystub,
		onResendPaystub,
		onLeaveClick,
		onOvertimeClick
	}: Props = $props();

	let isCollapsed = $state(false);

	// Helpers
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

	const isApprovedOrPaid = $derived(runStatus === 'approved' || runStatus === 'paid');
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
					<span class="stat-value">{formatCurrency(payGroup.totalNetPay)}</span>
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
						<th class="col-province">Province</th>
						<th class="col-gross">Gross</th>
						<th class="col-leave">Leave</th>
						<th class="col-overtime">Overtime</th>
						<th class="col-deductions">Deductions</th>
						<th class="col-net">Net Pay</th>
						{#if isApprovedOrPaid}
							<th class="col-actions">Paystub</th>
						{:else}
							<th class="col-actions"></th>
						{/if}
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
								</div>
							</td>
							<td class="col-province">
								<span class="province-badge">{record.employeeProvince}</span>
							</td>
							<td class="col-gross">{formatCurrency(record.totalGross)}</td>
							<td
								class="col-leave"
								onclick={(e) => {
									e.stopPropagation();
									onLeaveClick?.(record);
								}}
							>
								{#if record.leaveEntries && record.leaveEntries.length > 0}
									<div class="leave-badges">
										{#each record.leaveEntries as entry}
											<LeaveTypeBadge type={entry.leaveType} hours={entry.hours} compact />
										{/each}
									</div>
								{:else}
									<span class="no-leave">-</span>
								{/if}
							</td>
							<td
								class="col-overtime"
								onclick={(e) => {
									e.stopPropagation();
									onOvertimeClick?.(record);
								}}
							>
								{#if record.overtimeEntries && record.overtimeEntries.length > 0}
									{@const totalHours = record.overtimeEntries.reduce((sum, e) => sum + e.hours, 0)}
									<span class="overtime-badge">
										<i class="fas fa-clock"></i>
										{totalHours}h
									</span>
								{:else}
									<span class="no-overtime">-</span>
								{/if}
							</td>
							<td class="col-deductions">{formatCurrency(record.totalDeductions)}</td>
							<td class="col-net">
								<span class="net-pay">{formatCurrency(record.netPay)}</span>
							</td>
							<td class="col-actions">
								{#if isApprovedOrPaid}
									<div class="action-buttons">
										<button
											class="action-btn"
											title="Download Paystub"
											onclick={(e) => {
												e.stopPropagation();
												onDownloadPaystub?.(record);
											}}
										>
											<i class="fas fa-download"></i>
										</button>
										<button
											class="action-btn"
											title="Resend Paystub"
											onclick={(e) => {
												e.stopPropagation();
												onResendPaystub?.(record);
											}}
										>
											<i class="fas fa-paper-plane"></i>
										</button>
									</div>
								{:else}
									<button
										class="expand-btn"
										title={expandedRecordId === record.id ? 'Collapse' : 'Expand'}
									>
										<i class="fas fa-chevron-{expandedRecordId === record.id ? 'up' : 'down'}"></i>
									</button>
								{/if}
							</td>
						</tr>
						{#if expandedRecordId === record.id}
							<PayrollRecordExpandedRow {record} colspan={8} />
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
	}

	.section-header {
		width: 100%;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-surface-50);
		border: none;
		cursor: pointer;
		transition: var(--transition-fast);
		text-align: left;
	}

	.section-header:hover {
		background: var(--color-surface-100);
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
		background: var(--color-primary-100);
		color: var(--color-primary-600);
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

	.stat-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.section-content {
		border-top: 1px solid var(--color-surface-200);
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
		background: var(--color-primary-50);
	}

	.records-table tbody tr:last-child td {
		border-bottom: none;
	}

	.col-employee {
		width: 22%;
	}

	.col-province {
		width: 8%;
	}

	.col-gross,
	.col-deductions,
	.col-net {
		width: 13%;
		text-align: right;
	}

	.col-leave {
		width: 10%;
		cursor: pointer;
	}

	.col-leave:hover {
		background: var(--color-surface-100);
	}

	.col-overtime {
		width: 10%;
		cursor: pointer;
	}

	.col-overtime:hover {
		background: var(--color-surface-100);
	}

	.col-actions {
		width: 8%;
		text-align: right;
	}

	.leave-badges {
		display: flex;
		gap: var(--spacing-1);
		flex-wrap: wrap;
	}

	.no-leave,
	.no-overtime {
		color: var(--color-surface-400);
	}

	.overtime-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-success-100);
		color: var(--color-success-700);
		border-radius: var(--radius-sm);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.overtime-badge i {
		font-size: 10px;
	}

	.records-table th.col-gross,
	.records-table th.col-deductions,
	.records-table th.col-net,
	.records-table th.col-actions {
		text-align: right;
	}

	.employee-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
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

	.net-pay {
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.action-buttons {
		display: flex;
		gap: var(--spacing-2);
		justify-content: flex-end;
	}

	.action-btn,
	.expand-btn {
		padding: var(--spacing-2);
		background: none;
		border: none;
		border-radius: var(--radius-md);
		color: var(--color-surface-500);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.action-btn:hover,
	.expand-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	@media (max-width: 1024px) {
		.header-stats {
			gap: var(--spacing-4);
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

		.records-table {
			font-size: var(--font-size-auxiliary-text);
		}

		.records-table th,
		.records-table td {
			padding: var(--spacing-2) var(--spacing-3);
		}
	}
</style>
