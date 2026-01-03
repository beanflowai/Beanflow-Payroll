<script lang="ts">
	import type { Employee } from '$lib/types/employee';
	import type { CompensationHistory, CompensationType } from '$lib/types/compensation';
	import { updateCompensation } from '$lib/services/compensationService';
	import { getCurrentDate } from '$lib/utils/dateUtils';

	interface Props {
		employee: Employee;
		currentCompensation: CompensationHistory | null;
		onClose: () => void;
		onSuccess: () => void;
	}

	let { employee, currentCompensation, onClose, onSuccess }: Props = $props();

	// Extract initial values from currentCompensation (form snapshot pattern)
	const initial = (() => {
		const comp = currentCompensation;
		return {
			compensationType: (comp?.compensationType || 'salary') as CompensationType,
			annualSalary: comp?.annualSalary?.toString() || '',
			hourlyRate: comp?.hourlyRate?.toString() || '',
		};
	})();

	// Form state
	let compensationType = $state<CompensationType>(initial.compensationType);
	let annualSalary = $state<string>(initial.annualSalary);
	let hourlyRate = $state<string>(initial.hourlyRate);
	let effectiveDate = $state<string>(getCurrentDate());
	let changeReason = $state<string>('');

	// UI state
	let isSubmitting = $state(false);
	let error = $state<string | null>(null);

	// Validation
	let validationErrors = $derived(() => {
		const errors: Record<string, string> = {};

		if (compensationType === 'salary') {
			const salary = parseFloat(annualSalary);
			if (!annualSalary || isNaN(salary) || salary <= 0) {
				errors.annualSalary = 'Please enter a valid annual salary';
			}
		} else {
			const rate = parseFloat(hourlyRate);
			if (!hourlyRate || isNaN(rate) || rate <= 0) {
				errors.hourlyRate = 'Please enter a valid hourly rate';
			}
		}

		if (!effectiveDate) {
			errors.effectiveDate = 'Please select an effective date';
		}

		return errors;
	});

	let isValid = $derived(Object.keys(validationErrors()).length === 0);

	// Handle type change
	function handleTypeChange(type: CompensationType) {
		compensationType = type;
		// Reset amount fields when switching types
		if (type === 'salary') {
			hourlyRate = '';
		} else {
			annualSalary = '';
		}
	}

	// Handle form submission
	async function handleSubmit(e: Event) {
		e.preventDefault();

		if (!isValid) return;

		isSubmitting = true;
		error = null;

		try {
			const result = await updateCompensation(employee.id, {
				compensationType,
				annualSalary: compensationType === 'salary' ? parseFloat(annualSalary) : null,
				hourlyRate: compensationType === 'hourly' ? parseFloat(hourlyRate) : null,
				effectiveDate,
				changeReason: changeReason.trim() || null
			});

			if (result.error) {
				error = result.error.message;
				return;
			}

			onSuccess();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to update compensation';
		} finally {
			isSubmitting = false;
		}
	}

	// Handle overlay click
	function handleOverlayClick(e: MouseEvent) {
		if (e.target === e.currentTarget) {
			onClose();
		}
	}

	// Get full name
	function getFullName(): string {
		return `${employee.firstName} ${employee.lastName}`;
	}
</script>

<div
	class="modal-overlay"
	onclick={handleOverlayClick}
	onkeydown={(e) => e.key === 'Escape' && onClose()}
	role="dialog"
	aria-modal="true"
	tabindex="-1"
>
	<div class="modal-content">
		<div class="modal-header">
			<h2>Adjust Compensation</h2>
			<p class="modal-subtitle">{getFullName()}</p>
			<button class="close-btn" onclick={onClose} aria-label="Close">
				<i class="fas fa-times"></i>
			</button>
		</div>

		{#if error}
			<div class="error-message">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
			</div>
		{/if}

		<form onsubmit={handleSubmit}>
			<!-- Compensation Type -->
			<fieldset class="form-group">
				<legend class="form-label">Compensation Type</legend>
				<div class="type-selector">
					<button
						type="button"
						class="type-btn"
						class:active={compensationType === 'salary'}
						onclick={() => handleTypeChange('salary')}
					>
						<i class="fas fa-money-bill-wave"></i>
						Salaried
					</button>
					<button
						type="button"
						class="type-btn"
						class:active={compensationType === 'hourly'}
						onclick={() => handleTypeChange('hourly')}
					>
						<i class="fas fa-clock"></i>
						Hourly
					</button>
				</div>
			</fieldset>

			<!-- Amount -->
			{#if compensationType === 'salary'}
				<div class="form-group">
					<label class="form-label" for="annualSalary">
						Annual Salary
						<span class="required">*</span>
					</label>
					<div class="input-wrapper">
						<span class="input-prefix">$</span>
						<input
							type="text"
							inputmode="decimal"
							id="annualSalary"
							bind:value={annualSalary}
							placeholder="60000.00"
							class="form-input with-prefix"
							class:error={validationErrors().annualSalary}
						/>
						<span class="input-suffix">/year</span>
					</div>
					{#if validationErrors().annualSalary}
						<span class="error-text">{validationErrors().annualSalary}</span>
					{/if}
				</div>
			{:else}
				<div class="form-group">
					<label class="form-label" for="hourlyRate">
						Hourly Rate
						<span class="required">*</span>
					</label>
					<div class="input-wrapper">
						<span class="input-prefix">$</span>
						<input
							type="text"
							inputmode="decimal"
							id="hourlyRate"
							bind:value={hourlyRate}
							placeholder="25.00"
							class="form-input with-prefix"
							class:error={validationErrors().hourlyRate}
						/>
						<span class="input-suffix">/hour</span>
					</div>
					{#if validationErrors().hourlyRate}
						<span class="error-text">{validationErrors().hourlyRate}</span>
					{/if}
				</div>
			{/if}

			<!-- Effective Date -->
			<div class="form-group">
				<label class="form-label" for="effectiveDate">
					Effective Date
					<span class="required">*</span>
				</label>
				<input
					type="date"
					id="effectiveDate"
					bind:value={effectiveDate}
					class="form-input"
					class:error={validationErrors().effectiveDate}
				/>
				{#if validationErrors().effectiveDate}
					<span class="error-text">{validationErrors().effectiveDate}</span>
				{/if}
				<span class="help-text">
					The date when this compensation change takes effect
				</span>
			</div>

			<!-- Change Reason -->
			<div class="form-group">
				<label class="form-label" for="changeReason">
					Change Reason
					<span class="optional">(optional)</span>
				</label>
				<input
					type="text"
					id="changeReason"
					bind:value={changeReason}
					placeholder="e.g., Annual review, Promotion, Initial hire"
					class="form-input"
				/>
			</div>

			<!-- Actions -->
			<div class="modal-actions">
				<button type="button" class="btn-cancel" onclick={onClose} disabled={isSubmitting}>
					Cancel
				</button>
				<button type="submit" class="btn-submit" disabled={isSubmitting || !isValid}>
					{#if isSubmitting}
						<i class="fas fa-spinner fa-spin"></i>
						Saving...
					{:else}
						<i class="fas fa-check"></i>
						Save Changes
					{/if}
				</button>
			</div>
		</form>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-4);
	}

	.modal-content {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-lg);
		width: 100%;
		max-width: 480px;
		max-height: 90vh;
		overflow-y: auto;
	}

	.modal-header {
		position: relative;
		padding: var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-header h2 {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.modal-subtitle {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
		margin: var(--spacing-1) 0 0;
	}

	.close-btn {
		position: absolute;
		top: var(--spacing-4);
		right: var(--spacing-4);
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		background: transparent;
		border: none;
		color: var(--color-surface-400);
		cursor: pointer;
		border-radius: var(--radius-md);
		transition: var(--transition-fast);
	}

	.close-btn:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.error-message {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin: var(--spacing-4) var(--spacing-5) 0;
		padding: var(--spacing-3);
		background: var(--color-error-50);
		border: 1px solid var(--color-error-200);
		border-radius: var(--radius-lg);
		color: var(--color-error-700);
		font-size: var(--font-size-body-small);
	}

	form {
		padding: var(--spacing-5);
	}

	.form-group {
		margin-bottom: var(--spacing-4);
		border: none;
		padding: 0;
	}

	.form-label {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		margin-bottom: var(--spacing-2);
	}

	.required {
		color: var(--color-error-500);
	}

	.optional {
		font-weight: var(--font-weight-normal);
		color: var(--color-surface-400);
	}

	.type-selector {
		display: flex;
		gap: var(--spacing-3);
	}

	.type-btn {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: white;
		border: 2px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.type-btn:hover {
		border-color: var(--color-surface-300);
		background: var(--color-surface-50);
	}

	.type-btn.active {
		border-color: var(--color-primary-500);
		background: var(--color-primary-50);
		color: var(--color-primary-700);
	}

	.input-wrapper {
		display: flex;
		align-items: center;
		position: relative;
	}

	.input-prefix {
		position: absolute;
		left: var(--spacing-3);
		color: var(--color-surface-500);
		font-size: var(--font-size-body-content);
		pointer-events: none;
	}

	.input-suffix {
		position: absolute;
		right: var(--spacing-3);
		color: var(--color-surface-400);
		font-size: var(--font-size-body-small);
		pointer-events: none;
	}

	.form-input {
		width: 100%;
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		transition: var(--transition-fast);
	}

	.form-input.with-prefix {
		padding-left: var(--spacing-8);
		padding-right: var(--spacing-12);
	}

	.form-input:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-input.error {
		border-color: var(--color-error-400);
	}

	.form-input.error:focus {
		box-shadow: 0 0 0 3px var(--color-error-100);
	}

	.error-text {
		display: block;
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-error-600);
		margin-top: var(--spacing-1);
	}

	.help-text {
		display: block;
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-top: var(--spacing-1);
	}

	.modal-actions {
		display: flex;
		gap: var(--spacing-3);
		justify-content: flex-end;
		margin-top: var(--spacing-5);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-100);
	}

	.btn-cancel,
	.btn-submit {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-cancel {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-300);
	}

	.btn-cancel:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-400);
	}

	.btn-cancel:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.btn-submit {
		background: var(--gradient-primary);
		color: white;
		border: none;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-submit:hover:not(:disabled) {
		opacity: 0.9;
	}

	.btn-submit:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Responsive */
	@media (max-width: 480px) {
		.modal-overlay {
			padding: var(--spacing-2);
		}

		.modal-content {
			max-height: 95vh;
		}

		.type-selector {
			flex-direction: column;
		}

		.modal-actions {
			flex-direction: column-reverse;
		}

		.btn-cancel,
		.btn-submit {
			width: 100%;
		}
	}
</style>
