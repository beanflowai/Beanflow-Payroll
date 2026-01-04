<script lang="ts">
	/**
	 * Employee Portal - Paystubs List Page
	 * Shows list of paystubs with year filter and YTD summary
	 */
	import { onMount, getContext } from 'svelte';
	import PaystubCard from '$lib/components/employee-portal/PaystubCard.svelte';
	import {
		getMyPaystubs,
		getMyT4Documents,
		downloadMyT4,
		getAvailableYears
	} from '$lib/services/employeePortalService';
	import type {
		PaystubSummary,
		PaystubYTD,
		TaxDocument,
		PortalCompanyContext
	} from '$lib/types/employee-portal';
	import { PORTAL_COMPANY_CONTEXT_KEY } from '$lib/types/employee-portal';
	import { Skeleton, AlertBanner, EmptyState } from '$lib/components/shared';
	import { formatCurrency } from '$lib/utils/formatUtils';
	import { formatDate } from '$lib/utils/dateUtils';

	// Get company context from layout
	const portalContext = getContext<PortalCompanyContext>(PORTAL_COMPANY_CONTEXT_KEY);
	const companyId = $derived(portalContext?.company?.id ?? null);

	// State
	let selectedYear = $state(new Date().getFullYear());
	let availableYears = $state<number[]>([new Date().getFullYear()]);

	let paystubs = $state<PaystubSummary[]>([]);
	let ytdSummary = $state<PaystubYTD>({
		grossEarnings: 0,
		cppPaid: 0,
		eiPaid: 0,
		taxPaid: 0
	});
	let loading = $state(true);
	let error = $state<string | null>(null);

	// T4 Documents state
	let taxDocuments = $state<TaxDocument[]>([]);
	let loadingT4s = $state(true);
	let downloadingT4Year = $state<number | null>(null);

	// Fetch paystubs when year changes
	$effect(() => {
		loadPaystubs(selectedYear);
	});

	// Load T4 documents and available years on mount
	onMount(async () => {
		const [, years] = await Promise.all([
			loadT4Documents(),
			getAvailableYears(companyId ?? undefined)
		]);
		availableYears = years;
	});

	async function loadPaystubs(year: number) {
		loading = true;
		error = null;

		try {
			const response = await getMyPaystubs(year, 20, companyId ?? undefined);
			paystubs = response.paystubs;
			ytdSummary = response.ytdSummary;
		} catch (err) {
			console.error('Failed to load paystubs:', err);
			error = 'Unable to load paystubs. Please try again later.';
			paystubs = [];
		} finally {
			loading = false;
		}
	}

	async function loadT4Documents() {
		loadingT4s = true;
		try {
			const response = await getMyT4Documents(companyId ?? undefined);
			taxDocuments = response.taxDocuments;
		} catch (err) {
			console.error('Failed to load T4 documents:', err);
			// Don't show error - T4s may not be available yet
			taxDocuments = [];
		} finally {
			loadingT4s = false;
		}
	}

	function handleDownload(_paystubId: string) {
		// Paystub PDF download - pending backend implementation
	}

	async function handleT4Download(doc: TaxDocument) {
		downloadingT4Year = doc.year;
		try {
			const result = await downloadMyT4(doc.year, companyId ?? undefined);
			if (result.error) {
				console.error('T4 download failed:', result.error);
				// Could show a toast notification here
			}
		} finally {
			downloadingT4Year = null;
		}
	}
</script>

<div class="paystubs-page">
	<header class="page-header">
		<h1 class="page-title">Paystubs</h1>
		<div class="year-selector">
			<select bind:value={selectedYear} class="year-select">
				{#each availableYears as year (year)}
					<option value={year}>{year}</option>
				{/each}
			</select>
		</div>
	</header>

	<!-- Loading State -->
	{#if loading}
		<div class="skeleton-grid">
			{#each Array(4) as _unused, idx (idx)}
				<Skeleton variant="rounded" height="120px" />
			{/each}
		</div>
	{:else if error}
		<AlertBanner type="error" title="Failed to load paystubs" message={error}>
			<button class="retry-btn mt-2" onclick={() => loadPaystubs(selectedYear)}>Try Again</button>
		</AlertBanner>
	{:else if paystubs.length === 0}
		<EmptyState
			icon="fa-file-invoice-dollar"
			title="No paystubs found"
			description={`No paystubs found for ${selectedYear}.`}
			variant="card"
		/>
	{:else}
		<!-- Paystub List -->
		<section class="paystubs-list">
			{#each paystubs as paystub (paystub.id)}
				<PaystubCard {paystub} onDownload={() => handleDownload(paystub.id)} />
			{/each}
		</section>

		<!-- YTD Summary -->
		<section class="ytd-section" id="ytd">
			<h2 class="section-title">Year-to-Date Summary ({selectedYear})</h2>
			<div class="ytd-card">
				<div class="ytd-grid">
					<div class="ytd-item">
						<span class="ytd-label">Gross Earnings</span>
						<span class="ytd-value">{formatCurrency(ytdSummary.grossEarnings)}</span>
					</div>
					<div class="ytd-item">
						<span class="ytd-label">CPP Paid</span>
						<span class="ytd-value">{formatCurrency(ytdSummary.cppPaid)}</span>
					</div>
					<div class="ytd-item">
						<span class="ytd-label">EI Paid</span>
						<span class="ytd-value">{formatCurrency(ytdSummary.eiPaid)}</span>
					</div>
					<div class="ytd-item">
						<span class="ytd-label">Tax Paid</span>
						<span class="ytd-value">{formatCurrency(ytdSummary.taxPaid)}</span>
					</div>
				</div>
			</div>
		</section>
	{/if}

	<!-- Tax Documents -->
	<section class="documents-section" id="documents">
		<h2 class="section-title">Tax Documents</h2>
		{#if loadingT4s}
			<div class="documents-loading">
				<div class="spinner small"></div>
				<span>Loading tax documents...</span>
			</div>
		{:else if taxDocuments.length === 0}
			<div class="documents-empty">
				<p>No tax documents available yet.</p>
			</div>
		{:else}
			<div class="documents-list">
				{#each taxDocuments as doc (doc.id)}
					<div class="document-item">
						<div class="document-info">
							<span class="document-icon">
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
									<polyline points="14,2 14,8 20,8" />
								</svg>
							</span>
							<div class="document-details">
								<span class="document-name">{doc.type} - {doc.year}</span>
								<span class="document-date">Generated {formatDate(doc.generatedAt)}</span>
							</div>
						</div>
						<button
							class="download-btn"
							onclick={() => handleT4Download(doc)}
							disabled={downloadingT4Year === doc.year}
						>
							{#if downloadingT4Year === doc.year}
								<div class="spinner tiny"></div>
								<span>Downloading...</span>
							{:else}
								<svg viewBox="0 0 20 20" fill="currentColor">
									<path
										fill-rule="evenodd"
										d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
										clip-rule="evenodd"
									/>
								</svg>
								<span>Download</span>
							{/if}
						</button>
					</div>
				{/each}
			</div>
		{/if}
	</section>
</div>

<style>
	.paystubs-page {
		max-width: 800px;
		margin: 0 auto;
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-bottom: var(--spacing-6);
	}

	.page-title {
		font-size: var(--font-size-headline-minimum);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
		margin: 0;
	}

	.year-select {
		padding: var(--spacing-2) var(--spacing-4);
		font-size: var(--font-size-body-content);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		background: white;
		color: var(--color-surface-800);
		cursor: pointer;
	}

	.year-select:focus {
		outline: none;
		border-color: var(--color-primary-500);
	}

	/* Skeleton Grid */
	.skeleton-grid {
		display: grid;
		gap: var(--spacing-4);
	}

	.retry-btn {
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

	.paystubs-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-8);
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-4) 0;
	}

	.ytd-section {
		margin-bottom: var(--spacing-8);
	}

	.ytd-card {
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-5);
		box-shadow: var(--shadow-md3-1);
	}

	.ytd-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
		gap: var(--spacing-4);
	}

	.ytd-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.ytd-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.ytd-value {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
	}

	.documents-section {
		margin-bottom: var(--spacing-8);
	}

	.documents-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.document-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		background: white;
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		box-shadow: var(--shadow-md3-1);
	}

	.document-info {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.document-icon {
		width: 40px;
		height: 40px;
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--color-surface-600);
	}

	.document-icon svg {
		width: 20px;
		height: 20px;
	}

	.document-details {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.document-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-900);
	}

	.document-date {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.download-btn {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-primary-500);
		background: transparent;
		border: 1px solid var(--color-primary-300);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.download-btn:hover {
		background: var(--color-primary-50);
		border-color: var(--color-primary-500);
	}

	.download-btn svg {
		width: 16px;
		height: 16px;
	}

	.download-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Documents loading/empty states */
	.documents-loading {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-6);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		color: var(--color-surface-600);
	}

	.documents-empty {
		padding: var(--spacing-6);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		text-align: center;
		color: var(--color-surface-600);
	}

	.documents-empty p {
		margin: 0;
	}

	.spinner.small {
		width: 20px;
		height: 20px;
		border-width: 2px;
	}

	.spinner.tiny {
		width: 14px;
		height: 14px;
		border-width: 2px;
	}

	/* Mobile adjustments */
	@media (max-width: 640px) {
		.page-header {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-3);
		}

		.page-title {
			font-size: var(--font-size-title-large);
		}

		.document-item {
			flex-direction: column;
			align-items: flex-start;
			gap: var(--spacing-3);
		}

		.download-btn {
			width: 100%;
			justify-content: center;
		}
	}
</style>
