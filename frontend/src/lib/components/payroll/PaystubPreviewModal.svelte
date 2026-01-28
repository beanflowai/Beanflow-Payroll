<script lang="ts">
	import BaseModal from '$lib/shared-base/BaseModal.svelte';
	import PaystubWebPreview from './PaystubWebPreview.svelte';
	import { previewPaystub } from '$lib/services/payroll/run-paystubs';
	import type { PayrollRecord, PayrollRunPayGroup, PayrollRunStatus } from '$lib/types/payroll';

	interface Props {
		record: PayrollRecord;
		payGroup?: PayrollRunPayGroup;
		runStatus: PayrollRunStatus;
		payDate?: string;
		onClose: () => void;
	}

	let { record, payGroup, runStatus, payDate, onClose }: Props = $props();

	// State for PDF loading
	let pdfUrl = $state<string | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);
	let lastLoadedRecordId = $state<string | null>(null);

	// Determine if we should show PDF (pending_approval, approved, paid) or web preview (draft)
	const showPdf = $derived(runStatus !== 'draft');

	// Load PDF for non-draft states, re-fetch when record changes
	$effect(() => {
		if (showPdf && record.id && record.id !== lastLoadedRecordId) {
			// Revoke previous URL before creating new one (without reading pdfUrl as dependency)
			revokePreviousUrl();
			lastLoadedRecordId = record.id;
			loadPdfPreview();
		}
	});

	// Cleanup PDF URL on unmount
	$effect(() => {
		return () => {
			revokePreviousUrl();
		};
	});

	function revokePreviousUrl() {
		if (pdfUrl) {
			URL.revokeObjectURL(pdfUrl);
			pdfUrl = null;
		}
	}

	async function loadPdfPreview() {
		loading = true;
		error = null;

		// Capture record ID at request time to prevent race conditions
		const requestedRecordId = record.id;
		const result = await previewPaystub(requestedRecordId);

		// Verify this response is still for the current record (user may have switched)
		if (requestedRecordId !== record.id) {
			return; // Stale response, ignore it
		}

		if (result.error) {
			error = result.error;
		} else if (result.data) {
			pdfUrl = URL.createObjectURL(result.data);
		}

		loading = false;
	}

	async function handleRetry() {
		await loadPdfPreview();
	}
</script>

<BaseModal
	visible={true}
	onclose={onClose}
	size={showPdf ? 'large' : 'medium'}
	title="Paystub Preview - {record.employeeName}"
>
	{#snippet children()}
		<div class="preview-container">
			{#if !showPdf}
				<!-- Draft: Web component preview -->
				<PaystubWebPreview {record} {payGroup} {payDate} />
			{:else}
				<!-- Non-draft: PDF preview -->
				{#if loading}
					<div class="loading-container">
						<i class="fas fa-spinner fa-spin text-4xl text-primary-500"></i>
						<p class="loading-text">Generating paystub preview...</p>
					</div>
				{:else if error}
					<div class="error-container">
						<div class="error-icon">
							<i class="fas fa-exclamation-circle"></i>
						</div>
						<h4 class="error-title">Failed to Load Preview</h4>
						<p class="error-message">{error}</p>
						<button class="retry-button" onclick={handleRetry}>
							<i class="fas fa-redo"></i>
							Retry
						</button>
					</div>
				{:else if pdfUrl}
					<iframe src={pdfUrl} class="pdf-viewer" title="Paystub PDF Preview"></iframe>
				{/if}
			{/if}
		</div>
	{/snippet}
</BaseModal>

<style>
	.preview-container {
		min-height: 400px;
		display: flex;
		flex-direction: column;
	}

	/* Loading State */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-10);
		gap: var(--spacing-4);
	}

	.loading-text {
		color: var(--color-surface-600);
		font-size: var(--font-size-body-content);
	}

	/* Error State */
	.error-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-10);
		gap: var(--spacing-3);
		text-align: center;
	}

	.error-icon {
		font-size: 2.5rem;
		color: var(--color-error-500);
	}

	.error-title {
		margin: 0;
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-900);
	}

	.error-message {
		margin: 0;
		color: var(--color-surface-600);
		font-size: var(--font-size-body-content);
		max-width: 400px;
	}

	.retry-button {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: background var(--transition-fast);
	}

	.retry-button:hover {
		background: var(--color-primary-600);
	}

	/* PDF Viewer */
	.pdf-viewer {
		flex: 1;
		width: 100%;
		min-height: 70vh;
		border: none;
		border-radius: var(--radius-lg);
		background: var(--color-surface-100);
	}
</style>
