<script lang="ts">
	/**
	 * Employee Portal - Dashboard Page
	 * Main landing page showing summary cards and quick actions
	 */
	import DashboardCard from '$lib/components/employee-portal/DashboardCard.svelte';
	import QuickActionCard from '$lib/components/employee-portal/QuickActionCard.svelte';

	// Mock data for static UI
	const employeeName = 'Sarah';
	const lastPay = {
		amount: '$2,195.45',
		date: 'Dec 20, 2025'
	};
	const vacation = {
		hours: '74 hours',
		dollars: '($1,850.00)'
	};
	const sickLeave = {
		hours: '36 hours',
		label: 'remaining'
	};
</script>

<div class="dashboard-page">
	<header class="page-header">
		<h1 class="welcome-message">Welcome back, {employeeName}!</h1>
	</header>

	<!-- Summary Cards -->
	<section class="summary-section">
		<div class="summary-cards">
			<DashboardCard
				icon="money"
				label="Last Pay"
				value={lastPay.amount}
				subValue={lastPay.date}
				actionLabel="View Paystub"
				actionHref="/employee/paystubs"
			/>
			<DashboardCard
				icon="vacation"
				label="Vacation"
				value={vacation.hours}
				subValue={vacation.dollars}
				actionLabel="View Details"
				actionHref="/employee/leave"
			/>
			<DashboardCard
				icon="sick"
				label="Sick Leave"
				value={sickLeave.hours}
				subValue={sickLeave.label}
				actionLabel="View Details"
				actionHref="/employee/leave"
			/>
		</div>
	</section>

	<!-- Quick Actions -->
	<section class="actions-section">
		<h2 class="section-title">Quick Actions</h2>
		<div class="quick-actions-grid">
			<QuickActionCard icon="paystubs" label="View Paystubs" href="/employee/paystubs" />
			<QuickActionCard icon="profile" label="Update Profile" href="/employee/profile" />
			<QuickActionCard icon="bank" label="Bank Details" href="/employee/profile#bank" />
			<QuickActionCard icon="tax" label="Tax Info (TD1)" href="/employee/profile#tax" />
			<QuickActionCard icon="ytd" label="YTD Summary" href="/employee/paystubs#ytd" />
			<QuickActionCard icon="download" label="Download T4" href="/employee/paystubs#documents" />
		</div>
	</section>
</div>

<style>
	.dashboard-page {
		max-width: 1000px;
		margin: 0 auto;
	}

	.page-header {
		margin-bottom: var(--spacing-6);
	}

	.welcome-message {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.summary-section {
		margin-bottom: var(--spacing-8);
	}

	.summary-cards {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: var(--spacing-4);
	}

	.actions-section {
		margin-bottom: var(--spacing-8);
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4) 0;
	}

	.quick-actions-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		gap: var(--spacing-3);
	}

	/* Mobile adjustments */
	@media (max-width: 640px) {
		.welcome-message {
			font-size: var(--font-size-title-large);
		}

		.summary-cards {
			grid-template-columns: 1fr;
		}

		.quick-actions-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>
