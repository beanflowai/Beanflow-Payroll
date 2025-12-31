<script lang="ts">
	/**
	 * Employee Portal - Paystub Detail Page
	 * Shows full paystub details for a specific pay period
	 */
	import { page } from '$app/stores';
	import PaystubDetail from '$lib/components/employee-portal/PaystubDetail.svelte';
	import { getPaystubDetail } from '$lib/services/employeePortalService';
	import type { PaystubDetail as PaystubDetailType } from '$lib/types/employee-portal';

	const paystubId = $page.params.id ?? '';

	// State
	let paystub = $state<PaystubDetailType | null>(null);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Fetch paystub on mount
	$effect(() => {
		loadPaystub();
	});

	async function loadPaystub() {
		loading = true;
		error = null;

		if (!paystubId) {
			error = 'Paystub ID is required';
			loading = false;
			return;
		}

		try {
			paystub = await getPaystubDetail(paystubId);
		} catch (err) {
			console.error('Failed to load paystub:', err);
			error = 'Unable to load paystub details. Please try again later.';
			paystub = null;
		} finally {
			loading = false;
		}
	}

	function handleDownload() {
		// TODO: Implement PDF download
		console.log('Download PDF for paystub:', paystubId);
	}
</script>

<div class="paystub-detail-page">
	<header class="page-header">
		<a href="/employee/paystubs" class="back-link">
			<svg viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
					clip-rule="evenodd"
				/>
			</svg>
			Back to Paystubs
		</a>
		{#if paystub}
			<button class="download-btn" onclick={handleDownload}>
				<svg viewBox="0 0 20 20" fill="currentColor">
					<path
						fill-rule="evenodd"
						d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
						clip-rule="evenodd"
					/>
				</svg>
				Download PDF
			</button>
		{/if}
	</header>

	<!-- Loading State -->
	{#if loading}
		<div class="loading-state">
			<div class="spinner"></div>
			<p>Loading paystub...</p>
		</div>
	{:else if error}
		<!-- Error State -->
		<div class="error-state">
			<p>{error}</p>
			<button class="retry-btn" onclick={loadPaystub}>Try Again</button>
		</div>
	{:else if paystub}
		<PaystubDetail {paystub} onDownload={handleDownload} />
	{:else}
		<!-- Not Found State -->
		<div class="empty-state">
			<p>Paystub not found.</p>
			<a href="/employee/paystubs" class="back-btn">Back to Paystubs</a>
		</div>
	{/if}
</div>

<style>
	.paystub-detail-page {
		max-width: 700px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--spacing-6);
	}

	.back-link {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		text-decoration: none;
		transition: color var(--transition-fast);
	}

	.back-link:hover {
		color: var(--color-surface-900);
	}

	.back-link svg {
		width: 16px;
		height: 16px;
	}

	.download-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: white;
		background: var(--color-primary-500);
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.download-btn:hover {
		background: var(--color-primary-600);
	}

	.download-btn svg {
		width: 16px;
		height: 16px;
	}

	/* Loading State */
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

	/* Error State */
	.error-state {
		text-align: center;
		padding: var(--spacing-8);
		background: var(--color-error-50);
		border-radius: var(--radius-lg);
		color: var(--color-error-700);
	}

	.retry-btn {
		margin-top: var(--spacing-4);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-error-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		cursor: pointer;
	}

	.retry-btn:hover {
		background: var(--color-error-600);
	}

	/* Empty State */
	.empty-state {
		text-align: center;
		padding: var(--spacing-12);
		color: var(--color-surface-600);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
	}

	.back-btn {
		display: inline-block;
		margin-top: var(--spacing-4);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border-radius: var(--radius-md);
		text-decoration: none;
	}

	.back-btn:hover {
		background: var(--color-primary-600);
	}

	/* Mobile adjustments */
	@media (max-width: 640px) {
		.page-header {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-4);
		}

		.download-btn {
			width: 100%;
			justify-content: center;
		}
	}
</style>
