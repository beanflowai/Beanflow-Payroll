<script lang="ts">
	/**
	 * Employee Portal - Leave Balances Page
	 * Shows vacation and sick leave balances with history
	 */
	import LeaveBalanceCard from '$lib/components/employee-portal/LeaveBalanceCard.svelte';
	import { getMyLeaveBalance, type LeaveBalanceResponse } from '$lib/services/employeePortalService';
	import type { EmployeeLeaveBalance, LeaveHistoryEntry } from '$lib/types/employee-portal';
	import { formatShortDate } from '$lib/utils/dateUtils';

	// State
	let selectedYear = $state(new Date().getFullYear());
	const availableYears = [2025, 2024, 2023];

	let leaveBalance = $state<EmployeeLeaveBalance>({
		vacationHours: 0,
		vacationDollars: 0,
		vacationAccrualRate: 4,
		vacationYtdAccrued: 0,
		vacationYtdUsed: 0,
		sickHoursRemaining: 0,
		sickHoursAllowance: 0,
		sickHoursUsedThisYear: 0
	});
	let leaveHistory = $state<LeaveHistoryEntry[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Fetch leave balance when year changes
	$effect(() => {
		loadLeaveBalance(selectedYear);
	});

	async function loadLeaveBalance(year: number) {
		loading = true;
		error = null;

		try {
			const response = await getMyLeaveBalance(year);
			leaveBalance = {
				vacationHours: response.vacationHours,
				vacationDollars: response.vacationDollars,
				vacationAccrualRate: response.vacationAccrualRate,
				vacationYtdAccrued: response.vacationYtdAccrued,
				vacationYtdUsed: response.vacationYtdUsed,
				sickHoursRemaining: response.sickHoursRemaining,
				sickHoursAllowance: response.sickHoursAllowance,
				sickHoursUsedThisYear: response.sickHoursUsedThisYear
			};
			leaveHistory = response.leaveHistory;
		} catch (err) {
			console.error('Failed to load leave balance:', err);
			error = 'Unable to load leave balances. Please try again later.';
		} finally {
			loading = false;
		}
	}

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
		<div class="year-selector">
			<select bind:value={selectedYear} class="year-select">
				{#each availableYears as year}
					<option value={year}>{year}</option>
				{/each}
			</select>
		</div>
	</header>

	<!-- Loading State -->
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading leave balances...</p>
		</div>
	{:else if error}
		<!-- Error State -->
		<div class="error-state">
			<p>{error}</p>
		</div>
	{:else}
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
			<h2 class="section-title">Leave History ({selectedYear})</h2>
			{#if leaveHistory.length === 0}
				<div class="empty-state">
					<p>No leave usage recorded for {selectedYear}.</p>
				</div>
			{:else}
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
									<td class="hours-cell">{entry.hours.toFixed(1)}h</td>
									<td class="balance-cell">
										{entry.balanceAfterHours.toFixed(1)}h
										{#if entry.balanceAfterDollars}
											<span class="balance-dollars">({formatMoney(entry.balanceAfterDollars)})</span>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
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
	{/if}
</div>

<style>
	.leave-page {
		max-width: 900px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-6);
	}

	.page-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.year-selector {
		display: flex;
		align-items: center;
	}

	.year-select {
		padding: var(--spacing-2) var(--spacing-3);
		font-size: var(--font-size-body-content);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		background: white;
		cursor: pointer;
	}

	.year-select:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.loading-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-12);
		color: var(--color-surface-600);
	}

	.spinner {
		width: 32px;
		height: 32px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500);
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: var(--spacing-4);
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.error-state {
		padding: var(--spacing-8);
		text-align: center;
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-lg);
		color: var(--color-error-700);
	}

	.empty-state {
		padding: var(--spacing-8);
		text-align: center;
		background: var(--color-surface-50);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		color: var(--color-surface-600);
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
