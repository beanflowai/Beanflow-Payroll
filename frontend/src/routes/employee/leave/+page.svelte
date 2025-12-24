<script lang="ts">
	/**
	 * Employee Portal - Leave Balances Page
	 * Shows vacation and sick leave balances with history
	 */
	import LeaveBalanceCard from '$lib/components/employee-portal/LeaveBalanceCard.svelte';
	import type { EmployeeLeaveBalance, LeaveHistoryEntry } from '$lib/types/employee-portal';
	import { formatShortDate } from '$lib/utils/dateUtils';

	// Mock data for static UI
	const leaveBalance: EmployeeLeaveBalance = {
		vacationHours: 74,
		vacationDollars: 1850.0,
		vacationAccrualRate: 4,
		vacationYtdAccrued: 92,
		vacationYtdUsed: 18,
		sickHoursRemaining: 36,
		sickHoursAllowance: 40,
		sickHoursUsedThisYear: 4
	};

	const leaveHistory: LeaveHistoryEntry[] = [
		{
			date: '2025-11-25',
			endDate: '2025-11-26',
			type: 'vacation',
			hours: 16,
			balanceAfterHours: 74,
			balanceAfterDollars: 1850
		},
		{
			date: '2025-10-15',
			type: 'sick',
			hours: 4,
			balanceAfterHours: 36
		},
		{
			date: '2025-08-12',
			endDate: '2025-08-16',
			type: 'vacation',
			hours: 40,
			balanceAfterHours: 90,
			balanceAfterDollars: 2250
		},
		{
			date: '2025-07-01',
			type: 'vacation',
			hours: 8,
			balanceAfterHours: 130,
			balanceAfterDollars: 3250
		}
	];

	function formatDate(dateStr: string): string {
		return formatShortDate(dateStr);
	}

	function formatDateRange(start: string, end?: string): string {
		if (end) {
			return `${formatDate(start)} - ${formatDate(end)}`;
		}
		return formatDate(start);
	}

	function formatMoney(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}
</script>

<div class="leave-page">
	<header class="page-header">
		<h1 class="page-title">Leave Balances</h1>
	</header>

	<!-- Balance Cards -->
	<section class="balance-section">
		<div class="balance-cards">
			<LeaveBalanceCard
				type="vacation"
				hoursRemaining={leaveBalance.vacationHours}
				dollarsValue={leaveBalance.vacationDollars}
				accrualRate={leaveBalance.vacationAccrualRate}
				ytdAccrued={leaveBalance.vacationYtdAccrued}
				ytdUsed={leaveBalance.vacationYtdUsed}
			/>
			<LeaveBalanceCard
				type="sick"
				hoursRemaining={leaveBalance.sickHoursRemaining}
				allowance={leaveBalance.sickHoursAllowance}
				usedThisYear={leaveBalance.sickHoursUsedThisYear}
			/>
		</div>
	</section>

	<!-- Leave History -->
	<section class="history-section">
		<h2 class="section-title">Leave History (2025)</h2>
		<div class="history-table-container">
			<table class="history-table">
				<thead>
					<tr>
						<th>Date</th>
						<th>Type</th>
						<th>Hours</th>
						<th>Balance After</th>
					</tr>
				</thead>
				<tbody>
					{#each leaveHistory as entry}
						<tr>
							<td class="date-cell">{formatDateRange(entry.date, entry.endDate)}</td>
							<td>
								<span class="type-badge" class:vacation={entry.type === 'vacation'} class:sick={entry.type === 'sick'}>
									{entry.type === 'vacation' ? 'Vacation' : 'Sick'}
								</span>
							</td>
							<td class="hours-cell">{entry.hours}h</td>
							<td class="balance-cell">
								{entry.balanceAfterHours}h
								{#if entry.balanceAfterDollars}
									<span class="balance-dollars">({formatMoney(entry.balanceAfterDollars)})</span>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	</section>

	<!-- Info Note -->
	<section class="info-section">
		<div class="info-card">
			<svg class="info-icon" viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
					clip-rule="evenodd"
				/>
			</svg>
			<div class="info-content">
				<p class="info-title">About Your Leave</p>
				<ul class="info-list">
					<li>Vacation accrues at {leaveBalance.vacationAccrualRate}% of your regular earnings each pay period.</li>
					<li>Unused sick leave does not carry over to the next year.</li>
					<li>To request time off, please contact your manager or HR.</li>
				</ul>
			</div>
		</div>
	</section>
</div>

<style>
	.leave-page {
		max-width: 900px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: var(--spacing-6);
	}

	.page-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.balance-section {
		margin-bottom: var(--spacing-8);
	}

	.balance-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
		gap: var(--spacing-4);
	}

	.history-section {
		margin-bottom: var(--spacing-8);
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4) 0;
	}

	.history-table-container {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.history-table {
		width: 100%;
		border-collapse: collapse;
	}

	.history-table th,
	.history-table td {
		padding: var(--spacing-4);
		text-align: left;
	}

	.history-table th {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-200);
	}

	.history-table td {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.history-table tbody tr:last-child td {
		border-bottom: none;
	}

	.history-table tbody tr:hover {
		background: var(--color-surface-50);
	}

	.date-cell {
		font-weight: var(--font-weight-medium);
	}

	.type-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-sm);
	}

	.type-badge.vacation {
		background: var(--color-primary-100);
		color: var(--color-primary-700);
	}

	.type-badge.sick {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.hours-cell {
		font-weight: var(--font-weight-medium);
	}

	.balance-cell {
		font-weight: var(--font-weight-medium);
	}

	.balance-dollars {
		font-weight: var(--font-weight-regular);
		color: var(--color-surface-600);
		margin-left: var(--spacing-1);
	}

	.info-section {
		margin-bottom: var(--spacing-8);
	}

	.info-card {
		display: flex;
		gap: var(--spacing-4);
		padding: var(--spacing-5);
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
	}

	.info-icon {
		width: 24px;
		height: 24px;
		flex-shrink: 0;
		color: var(--color-surface-500);
	}

	.info-content {
		flex: 1;
	}

	.info-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-2) 0;
	}

	.info-list {
		margin: 0;
		padding-left: var(--spacing-5);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		line-height: 1.6;
	}

	.info-list li {
		margin-bottom: var(--spacing-1);
	}

	/* Mobile adjustments */
	@media (max-width: 640px) {
		.page-title {
			font-size: var(--font-size-title-large);
		}

		.balance-cards {
			grid-template-columns: 1fr;
		}

		.history-table-container {
			overflow-x: auto;
		}

		.history-table {
			min-width: 500px;
		}

		.info-card {
			flex-direction: column;
			gap: var(--spacing-3);
		}
	}
</style>
