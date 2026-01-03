<script lang="ts">
	import type { T4ValidationResult, T4SummaryData } from '$lib/types/t4';
	import {
		validateT4ForCRA,
		downloadT4Xml,
		recordT4Submission
	} from '$lib/services/t4Service';

	// Props
	interface Props {
		companyId: string;
		taxYear: number;
		isOpen: boolean;
		onClose: () => void;
		onSubmissionComplete: (summary: T4SummaryData) => void;
	}

	let { companyId, taxYear, isOpen, onClose, onSubmissionComplete }: Props = $props();

	// State
	type Step = 'validation' | 'submission';
	let currentStep = $state<Step>('validation');
	let validating = $state(false);
	let validationResult = $state<T4ValidationResult | null>(null);
	let validationError = $state<string | null>(null);
	let downloadingXml = $state(false);

	// Submission form state
	let confirmationNumber = $state('');
	let submissionNotes = $state('');
	let submitting = $state(false);
	let submitError = $state<string | null>(null);

	// Reset state when modal opens
	$effect(() => {
		if (isOpen) {
			currentStep = 'validation';
			validationResult = null;
			validationError = null;
			confirmationNumber = '';
			submissionNotes = '';
			submitError = null;
			// Auto-start validation
			handleValidate();
		}
	});

	// Validate T4 XML
	async function handleValidate() {
		validating = true;
		validationError = null;
		validationResult = null;

		const result = await validateT4ForCRA(companyId, taxYear);

		validating = false;

		if (result.error) {
			validationError = result.error;
		} else if (result.data) {
			validationResult = result.data;
		}
	}

	// Download XML
	async function handleDownloadXml() {
		downloadingXml = true;
		const result = await downloadT4Xml(companyId, taxYear);
		downloadingXml = false;

		if (result.error) {
			validationError = result.error;
		}
	}

	// Open CRA portal
	function handleOpenCRAPortal() {
		if (validationResult?.craPortalUrl) {
			window.open(validationResult.craPortalUrl, '_blank', 'noopener,noreferrer');
		}
	}

	// Proceed to submission step
	function handleProceedToSubmission() {
		currentStep = 'submission';
	}

	// Go back to validation step
	function handleBackToValidation() {
		currentStep = 'validation';
		submitError = null;
	}

	// Record submission
	async function handleRecordSubmission() {
		if (!confirmationNumber.trim()) {
			submitError = 'Confirmation number is required';
			return;
		}

		submitting = true;
		submitError = null;

		const result = await recordT4Submission(companyId, taxYear, {
			confirmationNumber: confirmationNumber.trim(),
			submissionNotes: submissionNotes.trim() || undefined
		});

		submitting = false;

		if (result.error) {
			submitError = result.error;
		} else if (result.data) {
			onSubmissionComplete(result.data);
			onClose();
		}
	}

	// Close modal
	function handleClose() {
		if (!validating && !submitting) {
			onClose();
		}
	}
</script>

{#if isOpen}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 bg-black/50 z-40 flex items-center justify-center"
		onclick={handleClose}
		onkeydown={(e) => e.key === 'Escape' && handleClose()}
		role="button"
		tabindex="-1"
	>
		<!-- Modal -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<div
			class="bg-white rounded-xl shadow-lg w-full max-w-lg max-h-[90vh] overflow-hidden"
			onclick={(e) => e.stopPropagation()}
			role="dialog"
			aria-modal="true"
			aria-labelledby="modal-title"
			tabindex="-1"
		>
			<!-- Header -->
			<div class="flex items-center justify-between px-6 py-4 border-b border-surface-100">
				<h2 id="modal-title" class="text-title-medium font-semibold text-surface-800 m-0">
					{#if currentStep === 'validation'}
						Submit T4 to CRA
					{:else}
						Record CRA Submission
					{/if}
				</h2>
				<button
					class="w-8 h-8 flex items-center justify-center bg-transparent border-none text-surface-500 hover:text-surface-700 hover:bg-surface-100 rounded-full cursor-pointer transition-colors"
					onclick={handleClose}
					disabled={validating || submitting}
					aria-label="Close modal"
				>
					<i class="fas fa-times"></i>
				</button>
			</div>

			<!-- Body -->
			<div class="px-6 py-4 max-h-[60vh] overflow-y-auto">
				{#if currentStep === 'validation'}
					<!-- Validation Step -->
					{#if validating}
						<!-- Loading -->
						<div class="flex flex-col items-center justify-center py-8">
							<i class="fas fa-spinner fa-spin text-3xl text-primary-500 mb-4"></i>
							<p class="text-body-content text-surface-600 m-0">Validating T4 XML...</p>
						</div>
					{:else if validationError}
						<!-- Validation Error -->
						<div class="bg-error-50 rounded-lg p-4 mb-4">
							<div class="flex items-start gap-3">
								<i class="fas fa-exclamation-circle text-error-500 mt-0.5"></i>
								<div>
									<p class="text-body-content font-medium text-error-700 m-0 mb-1">
										Validation Failed
									</p>
									<p class="text-body-content text-error-600 m-0">{validationError}</p>
								</div>
							</div>
						</div>
						<button
							class="w-full px-4 py-2 bg-surface-100 text-surface-700 border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-surface-200"
							onclick={handleValidate}
						>
							<i class="fas fa-sync-alt mr-2"></i>
							Retry Validation
						</button>
					{:else if validationResult}
						{#if validationResult.isValid}
							<!-- Validation Passed -->
							<div class="bg-success-50 rounded-lg p-4 mb-4">
								<div class="flex items-start gap-3">
									<i class="fas fa-check-circle text-success-500 mt-0.5"></i>
									<div>
										<p class="text-body-content font-medium text-success-700 m-0 mb-1">
											Validation Passed
										</p>
										<p class="text-body-content text-success-600 m-0">
											Your T4 XML is ready for CRA submission.
										</p>
									</div>
								</div>
							</div>

							<!-- Warnings -->
							{#if validationResult.warnings.length > 0}
								<div class="bg-warning-50 rounded-lg p-4 mb-4">
									<p class="text-body-content font-medium text-warning-700 m-0 mb-2">
										<i class="fas fa-exclamation-triangle mr-2"></i>
										Warnings ({validationResult.warnings.length})
									</p>
									<ul class="m-0 pl-6 space-y-1">
										{#each validationResult.warnings as warning}
											<li class="text-auxiliary-text text-warning-600">
												{warning.message}
											</li>
										{/each}
									</ul>
								</div>
							{/if}

							<!-- Instructions -->
							<div class="bg-surface-50 rounded-lg p-4 mb-4">
								<p class="text-body-content font-medium text-surface-800 m-0 mb-3">
									Submission Steps:
								</p>
								<ol class="m-0 pl-5 space-y-2">
									<li class="text-body-content text-surface-600">
										Download the T4 XML file
									</li>
									<li class="text-body-content text-surface-600">
										Open CRA's Internet File Transfer portal
									</li>
									<li class="text-body-content text-surface-600">
										Upload the XML file and complete the submission
									</li>
									<li class="text-body-content text-surface-600">
										Return here to record your confirmation number
									</li>
								</ol>
							</div>

							<!-- Action Buttons -->
							<div class="flex gap-3 mb-4">
								<button
									class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-success-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-success-700 disabled:opacity-50"
									onclick={handleDownloadXml}
									disabled={downloadingXml}
								>
									{#if downloadingXml}
										<i class="fas fa-spinner fa-spin"></i>
									{:else}
										<i class="fas fa-download"></i>
									{/if}
									<span>Download XML</span>
								</button>
								<button
									class="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-primary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-primary-700"
									onclick={handleOpenCRAPortal}
								>
									<i class="fas fa-external-link-alt"></i>
									<span>Open CRA Portal</span>
								</button>
							</div>
						{:else}
							<!-- Validation Failed with Errors -->
							<div class="bg-error-50 rounded-lg p-4 mb-4">
								<p class="text-body-content font-medium text-error-700 m-0 mb-2">
									<i class="fas fa-times-circle mr-2"></i>
									Validation Errors ({validationResult.errors.length})
								</p>
								<ul class="m-0 pl-6 space-y-1">
									{#each validationResult.errors as error}
										<li class="text-auxiliary-text text-error-600">
											{error.message}
											{#if error.field}
												<span class="text-error-400">({error.field})</span>
											{/if}
										</li>
									{/each}
								</ul>
							</div>
							<p class="text-body-content text-surface-600 m-0 mb-4">
								Please fix the errors above and regenerate the T4 Summary before submitting to CRA.
							</p>
						{/if}
					{/if}
				{:else}
					<!-- Submission Step -->
					<div class="space-y-4">
						<p class="text-body-content text-surface-600 m-0">
							After uploading your T4 XML to CRA, enter the confirmation number below to complete the
							submission process.
						</p>

						{#if submitError}
							<div class="bg-error-50 rounded-lg p-3">
								<p class="text-body-content text-error-600 m-0">
									<i class="fas fa-exclamation-circle mr-2"></i>
									{submitError}
								</p>
							</div>
						{/if}

						<div>
							<label for="confirmation-number" class="block text-body-content text-surface-700 mb-1">
								CRA Confirmation Number <span class="text-error-500">*</span>
							</label>
							<input
								id="confirmation-number"
								type="text"
								bind:value={confirmationNumber}
								placeholder="e.g., 1234567890"
								class="w-full px-3 py-2 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
								disabled={submitting}
							/>
						</div>

						<div>
							<label for="submission-notes" class="block text-body-content text-surface-700 mb-1">
								Notes (optional)
							</label>
							<textarea
								id="submission-notes"
								bind:value={submissionNotes}
								placeholder="Any additional notes about this submission..."
								rows="3"
								class="w-full px-3 py-2 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
								disabled={submitting}
							></textarea>
						</div>
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="flex justify-between gap-3 px-6 py-4 border-t border-surface-100 bg-surface-50">
				{#if currentStep === 'validation'}
					<button
						class="px-4 py-2 bg-surface-200 text-surface-700 border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-surface-300"
						onclick={handleClose}
						disabled={validating}
					>
						Cancel
					</button>
					{#if validationResult?.isValid}
						<button
							class="px-4 py-2 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-all hover:opacity-90 hover:-translate-y-px"
							onclick={handleProceedToSubmission}
						>
							I've Submitted to CRA
							<i class="fas fa-arrow-right ml-2"></i>
						</button>
					{/if}
				{:else}
					<button
						class="px-4 py-2 bg-surface-200 text-surface-700 border-none rounded-lg text-body-content font-medium cursor-pointer transition-colors hover:bg-surface-300"
						onclick={handleBackToValidation}
						disabled={submitting}
					>
						<i class="fas fa-arrow-left mr-2"></i>
						Back
					</button>
					<button
						class="px-4 py-2 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer shadow-md3-1 transition-all hover:opacity-90 hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed"
						onclick={handleRecordSubmission}
						disabled={submitting || !confirmationNumber.trim()}
					>
						{#if submitting}
							<i class="fas fa-spinner fa-spin mr-2"></i>
							Recording...
						{:else}
							<i class="fas fa-check mr-2"></i>
							Record Submission
						{/if}
					</button>
				{/if}
			</div>
		</div>
	</div>
{/if}
