<script lang="ts">
	interface Props {
		amount: number | null | undefined;
		showSign?: boolean;
		currency?: string;
		maximumFractionDigits?: number;
	}

	let { amount, showSign = false, currency = 'CAD', maximumFractionDigits = 2 }: Props = $props();

	function formatCurrency(value: number | null | undefined): string {
		if (value == null) return '-';
		const formatted = new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency,
			minimumFractionDigits: maximumFractionDigits,
			maximumFractionDigits
		}).format(Math.abs(value));

		if (showSign && value < 0) {
			return `-${formatted}`;
		}
		return formatted;
	}

	const formattedAmount = $derived(formatCurrency(amount));
	const isNegative = $derived(amount != null && amount < 0);
</script>

<span class="money-display" class:negative={isNegative || showSign}>
	{#if showSign && amount != null && amount > 0}+{/if}{formattedAmount}
</span>

<style>
	.money-display {
		font-family: monospace;
	}

	.money-display.negative {
		color: var(--color-error-600);
	}
</style>
