<script lang="ts">
	import type { PayrollRecord } from '$lib/types/payroll';
	import type { GroupBenefits } from '$lib/types/pay-group';
	import { LEAVE_TYPE_LABELS, ADJUSTMENT_TYPE_LABELS } from '$lib/types/payroll';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		record: PayrollRecord;
		groupBenefits?: GroupBenefits;
	}

	let { record, groupBenefits }: Props = $props();

	// Derived values for Leave section
	const hasLeaveThisPeriod = $derived((record.leaveEntries?.length ?? 0) > 0);

	const totalLeavePay = $derived(
		record.leaveEntries?.reduce((sum, entry) => sum + entry.leavePay, 0) ?? 0
	);

	// Derived: earnings adjustments from inputData (for Other Earnings breakdown)
	const earningsAdjustments = $derived(
		(record.inputData?.adjustments ?? [])
			.filter((adj) => adj.type !== 'deduction' && adj.amount > 0)
			.sort((a, b) => b.amount - a.amount)
	);

	const hasEarningsAdjustments = $derived(earningsAdjustments.length > 0);
	const otherEarningsTotal = $derived(
		earningsAdjustments.reduce((sum, adj) => sum + adj.amount, 0)
	);

	// Derived: check if tax breakdown exists (bonus tax calculated separately)
	const hasTaxBreakdown = $derived(
		(record.federalTaxOnBonus ?? 0) > 0 || (record.provincialTaxOnBonus ?? 0) > 0
	);
</script>

<tr class="detail-row">
	<td colspan="9">
		<div class="detail-content">
			<!-- Earnings Breakdown -->
			<div class="breakdown-section">
				<h4 class="breakdown-title">Earnings</h4>
				<div class="breakdown-grid">
					<div class="breakdown-item">
						<span class="item-label">Regular Pay</span>
						<span class="item-value">{formatCurrency(record.grossRegular)}</span>
					</div>
					{#if record.vacationAccrued > 0}
						<div class="breakdown-item vacation-earned">
							<span class="item-label">
								<span class="vacation-icon">🏖️</span>
								Vacation Earned
							</span>
							<span class="item-value vacation-value">{formatCurrency(record.vacationAccrued)}</span
							>
						</div>
					{/if}
					{#if record.grossOvertime > 0}
						<div class="breakdown-item overtime-item">
							<span class="item-label overtime-label">
								<i class="fas fa-clock"></i>
								Overtime
							</span>
							<span class="item-value overtime-value">
								{#if record.overtimeEntries && record.overtimeEntries.length > 0}
									{@const totalHours = record.overtimeEntries.reduce((sum, e) => sum + e.hours, 0)}
									<span class="overtime-detail">{totalHours}h ×1.5</span>
								{/if}
								{formatCurrency(record.grossOvertime)}
							</span>
						</div>
					{/if}
					{#if record.holidayPay > 0}
						<div class="breakdown-item">
							<span class="item-label">Holiday Pay</span>
							<span class="item-value">{formatCurrency(record.holidayPay)}</span>
						</div>
					{/if}
					{#if record.holidayPremiumPay > 0}
						<div class="breakdown-item">
							<span class="item-label">Holiday Premium</span>
							<span class="item-value">{formatCurrency(record.holidayPremiumPay)}</span>
						</div>
					{/if}
					{#if record.vacationPayPaid > 0}
						<div class="breakdown-item">
							<span class="item-label">Vacation Pay</span>
							<span class="item-value">{formatCurrency(record.vacationPayPaid)}</span>
						</div>
					{/if}
					<!-- Other Earnings breakdown (Bonus, Retroactive Pay, etc.) -->
					{#if hasEarningsAdjustments}
						<div class="breakdown-item other-earnings-item">
							<span class="item-label">Other Earnings</span>
							<span class="item-value">{formatCurrency(otherEarningsTotal)}</span>
						</div>
						<!-- Breakdown items (max 4) -->
						{#each earningsAdjustments.slice(0, 4) as adj (adj.id)}
							<div class="breakdown-subitem">
								<span class="subitem-prefix">└─</span>
								<span class="subitem-label"
									>{ADJUSTMENT_TYPE_LABELS[adj.type]?.label ?? adj.type}:</span
								>
								<span class="subitem-value">{formatCurrency(adj.amount)}</span>
							</div>
						{/each}
						{#if earningsAdjustments.length > 4}
							<div class="breakdown-subitem more-items">
								<span class="subitem-prefix">└─</span>
								<span class="subitem-label">+{earningsAdjustments.length - 4} more items</span>
							</div>
						{/if}
					{/if}
					<div class="breakdown-item total">
						<span class="item-label">Total Gross</span>
						<span class="item-value">{formatCurrency(record.totalGross)}</span>
					</div>
				</div>
			</div>

			<!-- Deductions Breakdown -->
			<div class="breakdown-section">
				<h4 class="breakdown-title">Deductions</h4>
				<div class="breakdown-grid">
					<div class="breakdown-item">
						<span class="item-label">CPP (Base)</span>
						<span class="item-value auto-tag">
							{formatCurrency(record.cppEmployee)}
							<span class="tag">auto</span>
						</span>
					</div>
					{#if record.cppAdditional > 0}
						<div class="breakdown-item">
							<span class="item-label">CPP2 (Enhanced)</span>
							<span class="item-value auto-tag">
								{formatCurrency(record.cppAdditional)}
								<span class="tag">auto</span>
							</span>
						</div>
					{/if}
					<div class="breakdown-item">
						<span class="item-label">EI</span>
						<span class="item-value auto-tag">
							{formatCurrency(record.eiEmployee)}
							<span class="tag">auto</span>
						</span>
					</div>
					<!-- Federal Tax with breakdown when bonus exists -->
					{#if hasTaxBreakdown}
						<div class="breakdown-item">
							<span class="item-label">Federal Tax</span>
							<span class="item-value auto-tag">
								{formatCurrency(record.federalTax)}
								<span class="tag">auto</span>
							</span>
						</div>
						<div class="breakdown-subitem">
							<span class="subitem-prefix">└─</span>
							<span class="subitem-label">On Income:</span>
							<span class="subitem-value">{formatCurrency(record.federalTaxOnIncome ?? 0)}</span>
						</div>
						<div class="breakdown-subitem">
							<span class="subitem-prefix">└─</span>
							<span class="subitem-label">On Bonus:</span>
							<span class="subitem-value">{formatCurrency(record.federalTaxOnBonus ?? 0)}</span>
						</div>
					{:else}
						<div class="breakdown-item">
							<span class="item-label">Federal Tax</span>
							<span class="item-value auto-tag">
								{formatCurrency(record.federalTax)}
								<span class="tag">auto</span>
							</span>
						</div>
					{/if}
					<!-- Provincial Tax with breakdown when bonus exists -->
					{#if hasTaxBreakdown}
						<div class="breakdown-item">
							<span class="item-label">Provincial Tax</span>
							<span class="item-value auto-tag">
								{formatCurrency(record.provincialTax)}
								<span class="tag">auto</span>
							</span>
						</div>
						<div class="breakdown-subitem">
							<span class="subitem-prefix">└─</span>
							<span class="subitem-label">On Income:</span>
							<span class="subitem-value">{formatCurrency(record.provincialTaxOnIncome ?? 0)}</span>
						</div>
						<div class="breakdown-subitem">
							<span class="subitem-prefix">└─</span>
							<span class="subitem-label">On Bonus:</span>
							<span class="subitem-value">{formatCurrency(record.provincialTaxOnBonus ?? 0)}</span>
						</div>
					{:else}
						<div class="breakdown-item">
							<span class="item-label">Provincial Tax</span>
							<span class="item-value auto-tag">
								{formatCurrency(record.provincialTax)}
								<span class="tag">auto</span>
							</span>
						</div>
					{/if}
					{#if record.rrsp > 0}
						<div class="breakdown-item">
							<span class="item-label">RRSP</span>
							<span class="item-value">{formatCurrency(record.rrsp)}</span>
						</div>
					{/if}
					{#if record.unionDues > 0}
						<div class="breakdown-item">
							<span class="item-label">Union Dues</span>
							<span class="item-value">{formatCurrency(record.unionDues)}</span>
						</div>
					{/if}
					<!-- Benefits breakdown (if groupBenefits available) or aggregate -->
					{#if groupBenefits?.enabled}
						{#if groupBenefits.health?.enabled}
							<div class="breakdown-item">
								<span class="item-label">Health</span>
								<span class="item-value"
									>{formatCurrency(groupBenefits.health.employeeDeduction)}</span
								>
							</div>
						{/if}
						{#if groupBenefits.dental?.enabled}
							<div class="breakdown-item">
								<span class="item-label">Dental</span>
								<span class="item-value"
									>{formatCurrency(groupBenefits.dental.employeeDeduction)}</span
								>
							</div>
						{/if}
						{#if groupBenefits.vision?.enabled}
							<div class="breakdown-item">
								<span class="item-label">Vision</span>
								<span class="item-value"
									>{formatCurrency(groupBenefits.vision.employeeDeduction)}</span
								>
							</div>
						{/if}
						{#if groupBenefits.lifeInsurance?.enabled}
							<div class="breakdown-item">
								<span class="item-label">Life Insurance</span>
								<span class="item-value"
									>{formatCurrency(groupBenefits.lifeInsurance.employeeDeduction)}</span
								>
							</div>
						{/if}
						{#if groupBenefits.disability?.enabled}
							<div class="breakdown-item">
								<span class="item-label">Disability</span>
								<span class="item-value"
									>{formatCurrency(groupBenefits.disability.employeeDeduction)}</span
								>
							</div>
						{/if}
					{:else if record.otherDeductions > 0}
						<div class="breakdown-item benefits-item">
							<span class="item-label benefits-label">
								<span class="benefits-icon">🏥</span>
								Benefits & Other
							</span>
							<span class="item-value">{formatCurrency(record.otherDeductions)}</span>
						</div>
					{/if}
					<div class="breakdown-item total">
						<span class="item-label">Total Deductions</span>
						<span class="item-value deductions">-{formatCurrency(record.totalDeductions)}</span>
					</div>
				</div>
			</div>

			<!-- Leave Breakdown -->
			<div class="breakdown-section leave-section">
				<h4 class="breakdown-title">Leave</h4>
				<div class="breakdown-grid">
					{#if hasLeaveThisPeriod}
						<!-- This Period Leave Entries -->
						{#each record.leaveEntries ?? [] as entry (entry.leaveType)}
							<div
								class="breakdown-item leave-item"
								class:vacation={entry.leaveType === 'vacation'}
								class:sick={entry.leaveType === 'sick'}
							>
								<span class="item-label leave-label-row">
									<span class="leave-icon">{LEAVE_TYPE_LABELS[entry.leaveType].icon}</span>
									{LEAVE_TYPE_LABELS[entry.leaveType].full}
								</span>
								<span class="item-value leave-value-row">
									<span class="leave-detail"
										>{entry.hours}h × {formatCurrency(entry.payRate)}/h</span
									>
									{formatCurrency(entry.leavePay)}
								</span>
							</div>
						{/each}

						<!-- Total Leave Pay -->
						{#if totalLeavePay > 0}
							<div class="breakdown-item total">
								<span class="item-label">Total Leave Pay</span>
								<span class="item-value">{formatCurrency(totalLeavePay)}</span>
							</div>
						{/if}
					{:else}
						<!-- Empty State -->
						<div class="leave-empty-state">
							<span class="empty-text">No leave this period</span>
						</div>
					{/if}

					<!-- Section Divider -->
					<div class="section-divider"></div>

					<!-- YTD Leave Usage -->
					<div class="leave-subsection">
						<span class="subsection-header">Year-to-Date Usage</span>
						<div class="ytd-leave-grid">
							<div class="ytd-leave-item vacation">
								<span class="ytd-leave-icon">{LEAVE_TYPE_LABELS.vacation.icon}</span>
								<span class="ytd-leave-value">{record.ytdVacationHours ?? 0}h</span>
								<span class="ytd-leave-label">Vacation</span>
							</div>
							<div class="ytd-leave-item sick">
								<span class="ytd-leave-icon">{LEAVE_TYPE_LABELS.sick.icon}</span>
								<span class="ytd-leave-value">{record.ytdSickHours ?? 0}h</span>
								<span class="ytd-leave-label">Sick</span>
							</div>
						</div>
					</div>

					<!-- Section Divider -->
					<div class="section-divider"></div>

					<!-- Balance Section -->
					<div class="leave-subsection">
						<span class="subsection-header">Remaining Balance</span>
						<div class="balance-grid">
							<div class="balance-item vacation">
								<span class="balance-label">
									<span class="leave-icon">{LEAVE_TYPE_LABELS.vacation.icon}</span>
									Vacation
								</span>
								<span class="balance-value-container">
									{#if record.vacationPayoutMethod === 'accrual'}
										<span class="balance-hours">{record.vacationBalanceHours ?? 0}h</span>
										{#if record.vacationBalanceDollars}
											<span class="balance-dollars"
												>{formatCurrency(record.vacationBalanceDollars)}</span
											>
										{/if}
									{:else}
										<span class="balance-hours text-surface-500">—</span>
									{/if}
								</span>
							</div>
							<div class="balance-item sick">
								<span class="balance-label">
									<span class="leave-icon">{LEAVE_TYPE_LABELS.sick.icon}</span>
									Sick
								</span>
								<span class="balance-value-container">
									<span class="balance-hours">{record.sickBalanceHours ?? 0}h</span>
								</span>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Net Pay -->
			<div class="breakdown-section net-section">
				<div class="net-pay-display">
					<span class="net-label">Net Pay</span>
					<span class="net-value">{formatCurrency(record.netPay)}</span>
				</div>
			</div>

			<!-- YTD Summary -->
			<div class="ytd-section">
				<h4 class="ytd-title">Year-to-Date</h4>
				<div class="ytd-grid">
					<div class="ytd-item">
						<span class="ytd-label">Gross</span>
						<span class="ytd-value">{formatCurrency(record.ytdGross)}</span>
					</div>
					<div class="ytd-item">
						<span class="ytd-label">CPP</span>
						<span class="ytd-value">{formatCurrency(record.ytdCpp)}</span>
					</div>
					<div class="ytd-item">
						<span class="ytd-label">EI</span>
						<span class="ytd-value">{formatCurrency(record.ytdEi)}</span>
					</div>
					<div class="ytd-item">
						<span class="ytd-label">Fed Tax</span>
						<span class="ytd-value">{formatCurrency(record.ytdFederalTax)}</span>
					</div>
					<div class="ytd-item">
						<span class="ytd-label">Prov Tax</span>
						<span class="ytd-value">{formatCurrency(record.ytdProvincialTax)}</span>
					</div>
					<div class="ytd-item highlight">
						<span class="ytd-label">Net Pay</span>
						<span class="ytd-value">{formatCurrency(record.ytdNetPay)}</span>
					</div>
				</div>
			</div>
		</div>
	</td>
</tr>

<style>
	/* Detail Row */
	.detail-row td {
		padding: 0;
		background: var(--color-surface-50);
	}

	.detail-content {
		display: grid;
		grid-template-columns: 1fr 1fr 1fr;
		gap: var(--spacing-5);
		padding: var(--spacing-5);
	}

	.breakdown-section {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		box-shadow: var(--shadow-md3-1);
	}

	.breakdown-section.net-section {
		grid-column: 1 / -1;
		background: var(--gradient-primary);
		text-align: center;
	}

	.breakdown-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin: 0 0 var(--spacing-3);
		padding-bottom: var(--spacing-2);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.breakdown-grid {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.breakdown-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-1) 0;
	}

	.breakdown-item.total {
		margin-top: var(--spacing-2);
		padding-top: var(--spacing-2);
		border-top: 1px solid var(--color-surface-200);
		font-weight: var(--font-weight-semibold);
	}

	.item-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.item-value {
		font-size: var(--font-size-body-content);
		font-family: monospace;
		color: var(--color-surface-800);
	}

	.item-value.auto-tag {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.item-value .tag {
		font-size: 10px;
		padding: 1px 6px;
		background: var(--color-surface-100);
		color: var(--color-surface-500);
		border-radius: var(--radius-sm);
		font-family: var(--font-family-primary);
		text-transform: uppercase;
	}

	.item-value.deductions {
		color: var(--color-error-600);
	}

	/* Breakdown sub-items (for Other Earnings and Tax breakdown) */
	.breakdown-subitem {
		display: flex;
		align-items: center;
		padding: var(--spacing-1) 0;
		padding-left: var(--spacing-4);
	}

	.subitem-prefix {
		color: var(--color-surface-400);
		margin-right: var(--spacing-1);
		font-family: monospace;
		font-size: var(--font-size-body-content);
	}

	.subitem-label {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
	}

	.subitem-value {
		font-size: var(--font-size-body-content);
		font-family: monospace;
		color: var(--color-surface-600);
		margin-left: auto;
	}

	.breakdown-subitem.more-items .subitem-label {
		font-style: italic;
		color: var(--color-surface-400);
	}

	/* Other Earnings highlight */
	.other-earnings-item {
		background: var(--color-success-50);
		border-radius: var(--radius-md);
		padding: var(--spacing-2) !important;
		margin: var(--spacing-1) 0;
	}

	.other-earnings-item .item-label {
		color: var(--color-success-700);
	}

	.other-earnings-item .item-value {
		color: var(--color-success-700);
		font-weight: var(--font-weight-medium);
	}

	/* Overtime styling */
	.overtime-item {
		background: var(--color-success-50);
		border-radius: var(--radius-md);
		padding: var(--spacing-2) !important;
		margin: var(--spacing-1) 0;
	}

	.overtime-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		color: var(--color-success-700);
	}

	.overtime-label i {
		font-size: var(--font-size-auxiliary-text);
	}

	.overtime-value {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
		color: var(--color-success-700);
		font-weight: var(--font-weight-medium);
	}

	.overtime-detail {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		font-family: var(--font-family-primary);
	}

	/* Vacation Earned styling */
	.vacation-earned {
		background: var(--color-info-50);
		border-radius: var(--radius-md);
		padding: var(--spacing-2) !important;
		margin: var(--spacing-1) 0;
	}

	.vacation-earned .item-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		color: var(--color-info-700);
	}

	.vacation-icon {
		font-size: var(--font-size-body-content);
	}

	.vacation-value {
		color: var(--color-info-700);
		font-weight: var(--font-weight-medium);
	}

	/* Benefits styling */
	.benefits-item {
		background: var(--color-warning-50);
		border-radius: var(--radius-md);
		padding: var(--spacing-2) !important;
		margin: var(--spacing-1) 0;
	}

	.benefits-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		color: var(--color-warning-700);
	}

	.benefits-icon {
		font-size: var(--font-size-body-content);
	}

	.benefits-item .item-value {
		color: var(--color-warning-700);
	}

	.net-pay-display {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-2);
	}

	.net-label {
		font-size: var(--font-size-auxiliary-text);
		color: rgba(255, 255, 255, 0.8);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.net-value {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: white;
	}

	/* YTD Section */
	.ytd-section {
		grid-column: 1 / -1;
		background: var(--color-surface-100);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
	}

	.ytd-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin: 0 0 var(--spacing-3);
	}

	.ytd-grid {
		display: grid;
		grid-template-columns: repeat(6, 1fr);
		gap: var(--spacing-3);
	}

	.ytd-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		text-align: center;
		padding: var(--spacing-2);
		background: white;
		border-radius: var(--radius-md);
	}

	.ytd-item.highlight {
		background: var(--color-success-100);
	}

	.ytd-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.ytd-value {
		font-size: var(--font-size-body-content);
		font-family: monospace;
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.ytd-item.highlight .ytd-value {
		color: var(--color-success-700);
	}

	/* Leave Section - inherits .breakdown-section styling */

	/* Leave Items with Color Coding */
	.leave-item.vacation .item-label,
	.leave-item.vacation .item-value {
		color: var(--color-info-700);
	}

	.leave-item.sick .item-label,
	.leave-item.sick .item-value {
		color: var(--color-warning-700);
	}

	.leave-label-row {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	.leave-icon {
		font-size: var(--font-size-body-content);
	}

	.leave-value-row {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}

	.leave-detail {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		font-family: var(--font-family-primary);
	}

	/* Empty State */
	.leave-empty-state {
		padding: var(--spacing-3) 0;
		text-align: center;
	}

	.empty-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-400);
		font-style: italic;
	}

	/* Section Divider */
	.section-divider {
		height: 1px;
		background: var(--color-surface-100);
		margin: var(--spacing-3) 0;
	}

	/* Leave Subsections */
	.leave-subsection {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.subsection-header {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.3px;
	}

	/* YTD Leave Grid */
	.ytd-leave-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: var(--spacing-2);
	}

	.ytd-leave-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: var(--spacing-2);
		border-radius: var(--radius-md);
		background: var(--color-surface-50);
	}

	.ytd-leave-item.vacation {
		background: var(--color-info-50);
	}

	.ytd-leave-item.sick {
		background: var(--color-warning-50);
	}

	.ytd-leave-icon {
		font-size: var(--font-size-body-content);
	}

	.ytd-leave-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		font-family: monospace;
	}

	.ytd-leave-item.vacation .ytd-leave-value {
		color: var(--color-info-700);
	}

	.ytd-leave-item.sick .ytd-leave-value {
		color: var(--color-warning-700);
	}

	.ytd-leave-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Balance Grid */
	.balance-grid {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.balance-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-2);
		border-radius: var(--radius-md);
		background: var(--color-surface-50);
	}

	.balance-item.vacation {
		background: var(--color-info-50);
	}

	.balance-item.sick {
		background: var(--color-warning-50);
	}

	.balance-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.balance-value-container {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 2px;
	}

	.balance-hours {
		font-size: var(--font-size-body-content);
		font-family: monospace;
		font-weight: var(--font-weight-semibold);
	}

	.balance-item.vacation .balance-hours {
		color: var(--color-info-700);
	}

	.balance-item.sick .balance-hours {
		color: var(--color-warning-700);
	}

	.balance-dollars {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		font-family: monospace;
		font-weight: var(--font-weight-regular);
	}

	/* Responsive */
	@media (max-width: 1024px) {
		.detail-content {
			grid-template-columns: 1fr 1fr;
		}

		.leave-section {
			grid-column: 1 / -1;
		}
	}

	@media (max-width: 768px) {
		.detail-content {
			grid-template-columns: 1fr;
		}

		.ytd-grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}
</style>
