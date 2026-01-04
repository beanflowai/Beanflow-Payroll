<script lang="ts">
	interface Props {
		label: string;
		value: string | number;
		variant?: 'default' | 'highlight' | 'accent' | 'small';
		valueClass?: string;
	}

	let { label, value, variant = 'default', valueClass = '' }: Props = $props();
</script>

<div
	class="summary-card"
	class:highlight={variant === 'highlight'}
	class:accent={variant === 'accent'}
	class:small={variant === 'small'}
>
	<span class="summary-label">{label}</span>
	<span class="summary-value {valueClass}">{value}</span>
</div>

<style>
	.summary-card {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
		padding: var(--spacing-5);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
	}

	.summary-card.small {
		padding: var(--spacing-4);
	}

	.summary-card.highlight {
		background: var(--gradient-primary);
	}

	.summary-card.highlight .summary-label,
	.summary-card.highlight .summary-value {
		color: white;
	}

	.summary-card.accent {
		background: var(--color-surface-800);
	}

	.summary-card.accent .summary-label,
	.summary-card.accent .summary-value {
		color: white;
	}

	.summary-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.summary-value {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.summary-card.small .summary-value {
		font-size: var(--font-size-title-medium);
	}

	:global(.summary-value.deductions) {
		color: var(--color-error-600);
	}
</style>
