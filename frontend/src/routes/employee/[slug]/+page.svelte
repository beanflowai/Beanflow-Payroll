<script lang="ts">
	/**
	 * Employee Portal - Dashboard Page (with Company Slug)
	 * Main landing page showing summary cards and quick actions
	 */
	import { onMount, getContext } from 'svelte';
	import { page } from '$app/stores';
	import DashboardCard from '$lib/components/employee-portal/DashboardCard.svelte';
	import QuickActionCard from '$lib/components/employee-portal/QuickActionCard.svelte';
	import {
		getCurrentEmployee,
		getMyPaystubs,
		getMyLeaveBalance
	} from '$lib/services/employeePortalService';
	import { PORTAL_COMPANY_CONTEXT_KEY, type PortalCompanyContext } from '$lib/types/employee-portal';

	const portalContext = getContext<PortalCompanyContext>(PORTAL_COMPANY_CONTEXT_KEY);
	const slug = $derived($page.params.slug);
	const companyId = $derived(portalContext?.company?.id ?? null);

	// State
	let employeeName = $state('');
	let lastPay = $state({ amount: '--', date: '' });
	let vacation = $state({ hours: '--', dollars: '' });
	let sickLeave = $state({ hours: '--', label: 'remaining' });
	let loading = $state(true);

	onMount(async () => {
		await loadDashboardData();
	});

	async function loadDashboardData() {
		loading = true;
		try {
			// Load employee name (scoped to company)
			const employee = await getCurrentEmployee(companyId ?? undefined);
			employeeName = employee.firstName;

			// Load last paystub
			const currentYear = new Date().getFullYear();
			const paystubData = await getMyPaystubs(currentYear, 1, companyId ?? undefined);
			if (paystubData.paystubs.length > 0) {
				const latest = paystubData.paystubs[0];
				lastPay = {
					amount: formatMoney(latest.netPay),
					date: formatDate(latest.payDate)
				};
			}

			// Load leave balances
			const leaveData = await getMyLeaveBalance(currentYear, companyId ?? undefined);
			vacation = {
				hours: `${leaveData.vacationHours.toFixed(0)} hours`,
				dollars: `(${formatMoney(leaveData.vacationDollars)})`
			};
			sickLeave = {
				hours: `${leaveData.sickHoursRemaining.toFixed(0)} hours`,
				label: 'remaining'
			};
		} catch (err) {
			console.error('Failed to load dashboard data:', err);
		} finally {
			loading = false;
		}
	}

	function formatMoney(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}

	function formatDate(dateStr: string): string {
		return new Date(dateStr).toLocaleDateString('en-CA', {
			month: 'short',
			day: 'numeric',
			year: 'numeric'
		});
	}
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
				actionHref="/employee/{slug}/paystubs"
			/>
			<DashboardCard
				icon="vacation"
				label="Vacation"
				value={vacation.hours}
				subValue={vacation.dollars}
				actionLabel="View Details"
				actionHref="/employee/{slug}/leave"
			/>
			<DashboardCard
				icon="sick"
				label="Sick Leave"
				value={sickLeave.hours}
				subValue={sickLeave.label}
				actionLabel="View Details"
				actionHref="/employee/{slug}/leave"
			/>
		</div>
	</section>

	<!-- Quick Actions -->
	<section class="actions-section">
		<h2 class="section-title">Quick Actions</h2>
		<div class="quick-actions-grid">
			<QuickActionCard icon="paystubs" label="View Paystubs" href="/employee/{slug}/paystubs" />
			<QuickActionCard icon="profile" label="Update Profile" href="/employee/{slug}/profile" />
			<QuickActionCard icon="bank" label="Bank Details" href="/employee/{slug}/profile#bank" />
			<QuickActionCard icon="tax" label="Tax Info (TD1)" href="/employee/{slug}/profile#tax" />
			<QuickActionCard icon="ytd" label="YTD Summary" href="/employee/{slug}/paystubs#ytd" />
			<QuickActionCard icon="download" label="Download T4" href="/employee/{slug}/paystubs#documents" />
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
