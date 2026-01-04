<script lang="ts">
	import type { EmployeeTaxClaim, Province } from '$lib/types/employee';
	import { PROVINCE_LABELS } from '$lib/types/employee';
	import type { BPADefaultsBothEditions } from '$lib/services/taxConfigService';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		taxYear: number;
		claim: EmployeeTaxClaim | null;
		bpaDefaults: BPADefaultsBothEditions | null;
		province: Province;
		isExpanded: boolean;
		isCurrentYear: boolean;
		readonly?: boolean;
		onUpdate: (year: number, federalAdditional: number, provincialAdditional: number) => void;
		onToggleExpand: () => void;
	}

	let {
		taxYear,
		claim,
		bpaDefaults,
		province,
		isExpanded,
		isCurrentYear,
		readonly = false,
		onUpdate,
		onToggleExpand
	}: Props = $props();

	// Local state for form inputs - initialized with current claim values
	// svelte-ignore state_referenced_locally
	let federalAdditional = $state(claim?.federalAdditionalClaims ?? 0);
	// svelte-ignore state_referenced_locally
	let provincialAdditional = $state(claim?.provincialAdditionalClaims ?? 0);

	// Sync local state when claim changes (this is intentional - claim prop updates externally)
	$effect(() => {
		federalAdditional = claim?.federalAdditionalClaims ?? 0;
		provincialAdditional = claim?.provincialAdditionalClaims ?? 0;
	});

	// Derived BPA values for both editions
	const federalBPAJan = $derived(bpaDefaults?.jan?.federalBPA ?? 0);
	const federalBPAJul = $derived(bpaDefaults?.jul?.federalBPA ?? 0);
	const provincialBPAJan = $derived(bpaDefaults?.jan?.provincialBPA ?? 0);
	const provincialBPAJul = $derived(bpaDefaults?.jul?.provincialBPA ?? 0);

	// Handle input changes
	function handleFederalChange(value: number) {
		federalAdditional = value;
		onUpdate(taxYear, federalAdditional, provincialAdditional);
	}

	function handleProvincialChange(value: number) {
		provincialAdditional = value;
		onUpdate(taxYear, federalAdditional, provincialAdditional);
	}

	// Format currency with no decimals for cleaner display
	function formatCurrencyNoDecimals(amount: number): string {
		return formatCurrency(amount, { maximumFractionDigits: 0 });
	}

</script>

<div
	class="border border-surface-200 rounded-lg overflow-hidden {isCurrentYear
		? 'border-primary-300'
		: ''}"
>
	<!-- Header -->
	<button
		type="button"
		class="w-full flex items-center justify-between p-4 bg-surface-50 hover:bg-surface-100 transition-colors cursor-pointer border-none text-left"
		onclick={onToggleExpand}
	>
		<div class="flex items-center gap-3">
			<span class="font-semibold text-surface-700">{taxYear} Tax Year</span>
			{#if isCurrentYear}
				<span
					class="px-2 py-0.5 bg-primary-100 text-primary-700 text-auxiliary-text rounded-full font-medium"
				>
					Current
				</span>
			{/if}
		</div>
		<i class="fas fa-chevron-{isExpanded ? 'up' : 'down'} text-surface-400"></i>
	</button>

	<!-- Content -->
	{#if isExpanded}
		<div class="p-4 bg-white">
			<div class="grid grid-cols-2 gap-6 max-md:grid-cols-1 max-lg:grid-cols-1">
				<!-- Federal TD1 -->
				<div class="flex flex-col gap-3">
					<h4 class="text-body-small font-semibold text-surface-600 m-0 flex items-center gap-2">
						<i class="fas fa-flag text-primary-400"></i>
						Federal TD1
					</h4>

					<div class="grid grid-cols-3 gap-3">
						<!-- BPA Jan-Jun -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text font-medium text-surface-500">BPA (Jan-Jun)</span>
							<div class="p-2 bg-surface-100 rounded text-body-small text-surface-600 font-medium">
								{formatCurrencyNoDecimals(federalBPAJan)}
							</div>
						</div>

						<!-- BPA Jul-Dec -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text font-medium text-surface-500">BPA (Jul-Dec)</span>
							<div class="p-2 bg-surface-100 rounded text-body-small text-surface-600 font-medium">
								{formatCurrencyNoDecimals(federalBPAJul)}
							</div>
						</div>

						<!-- Additional -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text font-medium text-surface-500">Additional</span>
							{#if readonly}
								<div class="p-2 bg-surface-100 rounded text-body-small text-surface-600">
									{formatCurrencyNoDecimals(federalAdditional)}
								</div>
							{:else}
								<div
									class="flex items-center border border-surface-300 rounded overflow-hidden text-body-small focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500/20"
								>
									<span class="px-2 bg-surface-100 text-surface-500 text-auxiliary-text">$</span>
									<input
										type="number"
										class="flex-1 p-2 border-none text-body-small focus:outline-none focus:ring-0 w-full min-w-0"
										value={federalAdditional}
										onchange={(e) => handleFederalChange(parseInt(e.currentTarget.value) || 0)}
										min="0"
										step="1"
									/>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- Provincial TD1 -->
				<div class="flex flex-col gap-3">
					<h4 class="text-body-small font-semibold text-surface-600 m-0 flex items-center gap-2">
						<i class="fas fa-map-marker-alt text-secondary-400"></i>
						Provincial TD1 ({PROVINCE_LABELS[province]})
					</h4>

					<div class="grid grid-cols-3 gap-3">
						<!-- BPA Jan-Jun -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text font-medium text-surface-500">BPA (Jan-Jun)</span>
							<div class="p-2 bg-surface-100 rounded text-body-small text-surface-600 font-medium">
								{formatCurrencyNoDecimals(provincialBPAJan)}
							</div>
						</div>

						<!-- BPA Jul-Dec -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text font-medium text-surface-500">BPA (Jul-Dec)</span>
							<div class="p-2 bg-surface-100 rounded text-body-small text-surface-600 font-medium">
								{formatCurrencyNoDecimals(provincialBPAJul)}
							</div>
						</div>

						<!-- Additional -->
						<div class="flex flex-col gap-1">
							<span class="text-auxiliary-text font-medium text-surface-500">Additional</span>
							{#if readonly}
								<div class="p-2 bg-surface-100 rounded text-body-small text-surface-600">
									{formatCurrencyNoDecimals(provincialAdditional)}
								</div>
							{:else}
								<div
									class="flex items-center border border-surface-300 rounded overflow-hidden text-body-small focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500/20"
								>
									<span class="px-2 bg-surface-100 text-surface-500 text-auxiliary-text">$</span>
									<input
										type="number"
										class="flex-1 p-2 border-none text-body-small focus:outline-none focus:ring-0 w-full min-w-0"
										value={provincialAdditional}
										onchange={(e) => handleProvincialChange(parseInt(e.currentTarget.value) || 0)}
										min="0"
										step="1"
									/>
								</div>
							{/if}
						</div>
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>
