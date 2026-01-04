<script lang="ts">
	/**
	 * EditBankInfoModal - Edit bank information form
	 * Changes require employer approval
	 */
	import BaseModal from '$lib/shared-base/BaseModal.svelte';
	import type { BankInfoFormData } from '$lib/types/employee-portal';
	import { CANADIAN_BANKS } from '$lib/types/employee-portal';

	interface Props {
		visible: boolean;
		initialData: {
			bankName: string;
			transitNumber: string;
			institutionNumber: string;
			accountNumber: string;
		};
		onclose: () => void;
		onSubmit: (data: BankInfoFormData) => void;
	}

	let { visible = $bindable(), initialData, onclose, onSubmit }: Props = $props();

	// Extract initial values once at component creation (form snapshot pattern)
	const initial = (() => {
		const data = initialData;
		return {
			bankName: data.bankName,
			transitNumber: data.transitNumber,
			institutionNumber: data.institutionNumber
		};
	})();

	// Form state
	let bankName = $state(initial.bankName);
	let transitNumber = $state(initial.transitNumber);
	let institutionNumber = $state(initial.institutionNumber);
	let accountNumber = $state(''); // Always start empty for security
	let voidChequeFile = $state<File | null>(null);
	let dragOver = $state(false);

	let isSubmitting = $state(false);

	// Validation
	const transitValid = $derived(/^\d{5}$/.test(transitNumber));
	const institutionValid = $derived(/^\d{3}$/.test(institutionNumber));
	const accountValid = $derived(accountNumber.length >= 7 && accountNumber.length <= 12);

	function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		if (input.files && input.files[0]) {
			voidChequeFile = input.files[0];
		}
	}

	function handleDrop(event: DragEvent) {
		event.preventDefault();
		dragOver = false;
		if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
			const file = event.dataTransfer.files[0];
			if (file.type.match(/^image\/|application\/pdf$/)) {
				voidChequeFile = file;
			}
		}
	}

	function handleDragOver(event: DragEvent) {
		event.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	function removeFile() {
		voidChequeFile = null;
	}

	function handleSubmit() {
		if (!transitValid || !institutionValid || !accountValid) {
			return;
		}

		isSubmitting = true;

		const data: BankInfoFormData = {
			bankName,
			transitNumber,
			institutionNumber,
			accountNumber,
			voidChequeFile: voidChequeFile || undefined
		};

		setTimeout(() => {
			isSubmitting = false;
			onSubmit(data);
			onclose();
		}, 500);
	}
</script>

<BaseModal {visible} {onclose} size="medium" title="Edit Bank Information">
	<form
		class="edit-form"
		onsubmit={(e) => {
			e.preventDefault();
			handleSubmit();
		}}
	>
		<!-- Warning Banner -->
		<div class="warning-banner">
			<svg class="warning-icon" viewBox="0 0 20 20" fill="currentColor">
				<path
					fill-rule="evenodd"
					d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
					clip-rule="evenodd"
				/>
			</svg>
			<span
				>Changes to bank information will be reviewed by your employer before taking effect. Your
				next pay will use the new account once approved.</span
			>
		</div>

		<!-- Bank Name -->
		<div class="form-group">
			<label for="bankName" class="form-label">Bank Name</label>
			<select id="bankName" class="form-select" bind:value={bankName}>
				{#each CANADIAN_BANKS as bank (bank.name)}
					<option value={bank.name}>{bank.name}</option>
				{/each}
			</select>
		</div>

		<!-- Transit Number -->
		<div class="form-group">
			<label for="transitNumber" class="form-label">Transit Number (5 digits)</label>
			<input
				id="transitNumber"
				type="text"
				class="form-input"
				class:invalid={transitNumber && !transitValid}
				bind:value={transitNumber}
				placeholder="12345"
				maxlength="5"
				pattern="\d{5}"
			/>
			{#if transitNumber && !transitValid}
				<span class="error-text">Transit number must be exactly 5 digits</span>
			{/if}
		</div>

		<!-- Institution Number -->
		<div class="form-group">
			<label for="institutionNumber" class="form-label">Institution Number (3 digits)</label>
			<input
				id="institutionNumber"
				type="text"
				class="form-input"
				class:invalid={institutionNumber && !institutionValid}
				bind:value={institutionNumber}
				placeholder="004"
				maxlength="3"
				pattern="\d{3}"
			/>
			{#if institutionNumber && !institutionValid}
				<span class="error-text">Institution number must be exactly 3 digits</span>
			{/if}
		</div>

		<!-- Account Number -->
		<div class="form-group">
			<label for="accountNumber" class="form-label">Account Number</label>
			<input
				id="accountNumber"
				type="text"
				class="form-input"
				class:invalid={accountNumber && !accountValid}
				bind:value={accountNumber}
				placeholder="Enter your full account number"
			/>
			{#if accountNumber && !accountValid}
				<span class="error-text">Account number must be 7-12 digits</span>
			{/if}
			<span class="current-account">Current: {initialData.accountNumber}</span>
		</div>

		<div class="form-divider"></div>

		<!-- Void Cheque Upload -->
		<div class="form-group">
			<span class="form-label">Upload void cheque (optional)</span>
			<div
				class="file-upload-zone"
				class:drag-over={dragOver}
				class:has-file={voidChequeFile}
				ondrop={handleDrop}
				ondragover={handleDragOver}
				ondragleave={handleDragLeave}
				role="button"
				tabindex="0"
			>
				{#if voidChequeFile}
					<div class="file-preview">
						<svg
							class="file-icon"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
						>
							<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
							<polyline points="14,2 14,8 20,8" />
						</svg>
						<span class="file-name">{voidChequeFile.name}</span>
						<button type="button" class="remove-file" onclick={removeFile} aria-label="Remove file">
							<svg viewBox="0 0 20 20" fill="currentColor">
								<path
									fill-rule="evenodd"
									d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
					</div>
				{:else}
					<div class="upload-prompt">
						<svg
							class="upload-icon"
							viewBox="0 0 24 24"
							fill="none"
							stroke="currentColor"
							stroke-width="2"
						>
							<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
							<polyline points="17,8 12,3 7,8" />
							<line x1="12" y1="3" x2="12" y2="15" />
						</svg>
						<span class="upload-text">Drop file here or click to upload</span>
						<span class="upload-hint">PNG, JPG, PDF (max 5MB)</span>
					</div>
					<input
						type="file"
						class="file-input"
						accept="image/png,image/jpeg,application/pdf"
						onchange={handleFileSelect}
					/>
				{/if}
			</div>
		</div>

		<!-- Actions -->
		<div class="form-actions">
			<button type="button" class="btn-cancel" onclick={onclose} disabled={isSubmitting}>
				Cancel
			</button>
			<button
				type="submit"
				class="btn-submit"
				disabled={isSubmitting || !transitValid || !institutionValid || !accountValid}
			>
				{#if isSubmitting}
					Submitting...
				{:else}
					Submit for Review
				{/if}
			</button>
		</div>
	</form>
</BaseModal>

<style>
	.edit-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.warning-banner {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-warning-800);
		line-height: 1.5;
	}

	.warning-icon {
		width: 20px;
		height: 20px;
		flex-shrink: 0;
		color: var(--color-warning-500);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.form-label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.form-input,
	.form-select {
		padding: var(--spacing-3) var(--spacing-4);
		font-size: var(--font-size-body-content);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		transition: all var(--transition-fast);
		width: 100%;
		box-sizing: border-box;
	}

	.form-input:focus,
	.form-select:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-input.invalid {
		border-color: var(--color-error-500);
	}

	.form-input.invalid:focus {
		box-shadow: 0 0 0 3px var(--color-error-100);
	}

	.error-text {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-error-500);
	}

	.current-account {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.form-divider {
		height: 1px;
		background: var(--color-surface-200);
		margin: var(--spacing-2) 0;
	}

	.file-upload-zone {
		position: relative;
		border: 2px dashed var(--color-surface-300);
		border-radius: var(--radius-md);
		padding: var(--spacing-6);
		text-align: center;
		transition: all var(--transition-fast);
		cursor: pointer;
	}

	.file-upload-zone:hover,
	.file-upload-zone.drag-over {
		border-color: var(--color-primary-400);
		background: var(--color-primary-50);
	}

	.file-upload-zone.has-file {
		border-style: solid;
		border-color: var(--color-success-400);
		background: var(--color-success-50);
	}

	.upload-prompt {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: var(--spacing-2);
	}

	.upload-icon {
		width: 32px;
		height: 32px;
		color: var(--color-surface-400);
	}

	.upload-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.upload-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.file-input {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		opacity: 0;
		cursor: pointer;
	}

	.file-preview {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.file-icon {
		width: 24px;
		height: 24px;
		color: var(--color-success-600);
	}

	.file-name {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		flex: 1;
		text-align: left;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.remove-file {
		background: none;
		border: none;
		padding: var(--spacing-1);
		cursor: pointer;
		color: var(--color-surface-500);
		transition: color var(--transition-fast);
	}

	.remove-file:hover {
		color: var(--color-error-500);
	}

	.remove-file svg {
		width: 16px;
		height: 16px;
	}

	.form-actions {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		margin-top: var(--spacing-4);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.btn-cancel,
	.btn-submit {
		padding: var(--spacing-3) var(--spacing-6);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: all var(--transition-fast);
	}

	.btn-cancel {
		background: transparent;
		color: var(--color-surface-600);
		border: 1px solid var(--color-surface-300);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--color-surface-100);
	}

	.btn-submit {
		background: var(--color-primary-500);
		color: white;
		border: none;
	}

	.btn-submit:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-cancel:disabled,
	.btn-submit:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}
</style>
