<script lang="ts">
	/**
	 * FormField - Reusable form field wrapper component
	 * Provides consistent styling for labels, inputs, errors, and help text
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		label: string;
		id?: string;
		required?: boolean;
		optional?: boolean;
		error?: string | null;
		helpText?: string;
		layout?: 'vertical' | 'horizontal';
		class?: string;
		children: Snippet;
	}

	let {
		label,
		id,
		required = false,
		optional = false,
		error = null,
		helpText,
		layout = 'vertical',
		class: className = '',
		children
	}: Props = $props();

	const hasError = $derived(!!error);
</script>

<div class="form-field {layout} {className}" class:has-error={hasError}>
	<label class="form-label" for={id}>
		{label}
		{#if required}
			<span class="required">*</span>
		{/if}
		{#if optional}
			<span class="optional">(optional)</span>
		{/if}
	</label>

	<div class="field-content">
		<div class="input-area">
			{@render children()}
		</div>

		{#if error}
			<div class="error-message" role="alert">
				<i class="fas fa-exclamation-circle"></i>
				<span>{error}</span>
			</div>
		{/if}

		{#if helpText && !error}
			<p class="help-text">{helpText}</p>
		{/if}
	</div>
</div>

<style>
	.form-field {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.form-field.horizontal {
		flex-direction: row;
		align-items: flex-start;
		gap: var(--spacing-4);
	}

	.form-field.horizontal .form-label {
		min-width: 140px;
		padding-top: var(--spacing-2);
	}

	.form-field.horizontal .field-content {
		flex: 1;
	}

	.form-label {
		display: block;
		font-size: var(--font-size-form-label);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
		line-height: var(--line-height-form-label);
	}

	.required {
		color: var(--color-error-500);
		margin-left: var(--spacing-1);
	}

	.optional {
		color: var(--color-surface-400);
		font-weight: var(--font-weight-regular);
		font-size: var(--font-size-body-small);
		margin-left: var(--spacing-1);
	}

	.field-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.input-area {
		display: flex;
		flex-direction: column;
	}

	/* Apply error styling to form controls within field */
	.has-error :global(.form-control),
	.has-error :global(.form-input),
	.has-error :global(.form-select),
	.has-error :global(input),
	.has-error :global(select),
	.has-error :global(textarea) {
		border-color: var(--color-error-500);
	}

	.has-error :global(.form-control:focus),
	.has-error :global(.form-input:focus),
	.has-error :global(.form-select:focus),
	.has-error :global(input:focus),
	.has-error :global(select:focus),
	.has-error :global(textarea:focus) {
		border-color: var(--color-error-500);
		box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-error-500) 10%, transparent);
	}

	.error-message {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-1);
		font-size: var(--font-size-body-small);
		color: var(--color-error-600);
		line-height: var(--line-height-form-label);
	}

	.error-message i {
		font-size: 12px;
		margin-top: 2px;
		flex-shrink: 0;
	}

	.help-text {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
		margin: 0;
		line-height: var(--line-height-form-label);
	}
</style>
