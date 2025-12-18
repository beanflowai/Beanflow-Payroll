<script lang="ts">
	interface Props {
		estimatedGross: number | null;
		totalEmployees: number;
	}

	let { estimatedGross, totalEmployees }: Props = $props();

	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD'
		}).format(amount);
	}
</script>

<div class="grid grid-cols-4 gap-4 mb-4 max-lg:grid-cols-2 max-md:grid-cols-1">
	<div class="bg-white rounded-xl p-5 shadow-md3-1">
		<div class="text-auxiliary-text font-medium text-surface-500 uppercase tracking-wide mb-2">Est. Gross</div>
		{#if estimatedGross !== null}
			<div class="text-title-large font-bold text-primary-600">{formatCurrency(estimatedGross)}</div>
		{:else}
			<div class="text-title-large font-bold text-surface-400">--</div>
		{/if}
	</div>
	<div class="bg-white rounded-xl p-5 shadow-md3-1">
		<div class="text-auxiliary-text font-medium text-surface-500 uppercase tracking-wide mb-2">Deductions</div>
		<div class="text-title-large font-bold text-surface-400">--</div>
	</div>
	<div class="bg-primary-600 text-white rounded-xl p-5 shadow-md3-1">
		<div class="text-auxiliary-text font-medium text-white/80 uppercase tracking-wide mb-2">Net Pay</div>
		<div class="text-title-large font-bold text-white">--</div>
	</div>
	<div class="bg-white rounded-xl p-5 shadow-md3-1">
		<div class="text-auxiliary-text font-medium text-surface-500 uppercase tracking-wide mb-2">Employees</div>
		<div class="text-title-large font-bold text-surface-800">{totalEmployees}</div>
	</div>
</div>
