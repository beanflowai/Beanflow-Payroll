<script lang="ts">
	interface Props {
		value: number;
		onSave: (newValue: number) => void;
		formatValue?: (value: number) => string;
		min?: number;
		max?: number;
		step?: number;
		disabled?: boolean;
		suffix?: string;
	}

	let {
		value,
		onSave,
		formatValue,
		min = 0,
		max,
		step = 0.01,
		disabled = false,
		suffix
	}: Props = $props();

	let isEditing = $state(false);
	let editValue = $state('');
	let inputRef = $state<HTMLInputElement | null>(null);

	function startEdit() {
		if (disabled) return;
		editValue = value.toString();
		isEditing = true;
		// Focus input after render
		setTimeout(() => inputRef?.focus(), 0);
	}

	function save() {
		const newValue = parseFloat(editValue) || 0;
		if (newValue !== value) {
			onSave(newValue);
		}
		isEditing = false;
	}

	function cancel() {
		isEditing = false;
		editValue = '';
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			save();
		} else if (e.key === 'Escape') {
			cancel();
		}
	}

	const displayValue = $derived(formatValue ? formatValue(value) : value.toString());
</script>

{#if isEditing}
	<div class="inline-edit-wrapper">
		<input
			bind:this={inputRef}
			type="number"
			class="inline-edit-input"
			bind:value={editValue}
			{min}
			{max}
			{step}
			onblur={save}
			onkeydown={handleKeydown}
		/>
		{#if suffix}
			<span class="input-suffix">{suffix}</span>
		{/if}
	</div>
{:else}
	<button
		class="inline-edit-display"
		class:disabled
		ondblclick={startEdit}
		title={disabled ? '' : 'Double-click to edit'}
	>
		<span class="display-value">{displayValue}</span>
		{#if !disabled}
			<span class="edit-icon">
				<i class="fas fa-pencil-alt"></i>
			</span>
		{/if}
	</button>
{/if}

<style>
	.inline-edit-wrapper {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	.inline-edit-display {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		background: transparent;
		border: 1px solid transparent;
		border-radius: var(--radius-sm);
		padding: var(--spacing-1) var(--spacing-2);
		cursor: pointer;
		transition: var(--transition-fast);
		font-family: var(--font-mono);
		font-size: inherit;
	}

	.inline-edit-display:hover:not(.disabled) {
		background: var(--color-surface-100);
		border-color: var(--color-surface-300);
	}

	.inline-edit-display:hover:not(.disabled) .edit-icon {
		opacity: 1;
	}

	.inline-edit-display.disabled {
		cursor: default;
	}

	.display-value {
		color: var(--color-surface-700);
	}

	.edit-icon {
		opacity: 0;
		color: var(--color-surface-400);
		font-size: 0.75rem;
		transition: var(--transition-fast);
	}

	.inline-edit-input {
		width: 80px;
		padding: var(--spacing-1) var(--spacing-2);
		border: 1px solid var(--color-primary-500);
		border-radius: var(--radius-sm);
		font-family: var(--font-mono);
		font-size: inherit;
		outline: none;
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.inline-edit-input::-webkit-inner-spin-button,
	.inline-edit-input::-webkit-outer-spin-button {
		-webkit-appearance: none;
		margin: 0;
	}

	.inline-edit-input[type='number'] {
		-moz-appearance: textfield;
	}

	.input-suffix {
		color: var(--color-surface-500);
		font-size: var(--font-size-body-small);
	}
</style>
