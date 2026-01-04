<script lang="ts">
	import type { Province, EmployeeTaxClaim } from '$lib/types/employee';
	import type { BPADefaults } from '$lib/services/taxConfigService';
	import TaxYearClaimsCard from '../TaxYearClaimsCard.svelte';

	interface Props {
		taxClaimsByYear: Map<number, EmployeeTaxClaim>;
		bpaDefaultsByYear: Map<number, BPADefaults>;
		province: Province;
		isCppExempt: boolean;
		isEiExempt: boolean;
		cpp2Exempt: boolean;
		showProvinceChangeWarning: boolean;
		taxClaimsLoading: boolean;
		currentTaxYear: number;
		previousTaxYear: number;
		currentYearExpanded: boolean;
		previousYearExpanded: boolean;
		onClaimUpdate: (year: number, fedAdditional: number, provAdditional: number) => void;
		onCppExemptChange: (value: boolean) => void;
		onEiExemptChange: (value: boolean) => void;
		onCpp2ExemptChange: (value: boolean) => void;
		onDismissWarning: () => void;
		onToggleCurrentYearExpand: () => void;
		onTogglePreviousYearExpand: () => void;
	}

	let {
		taxClaimsByYear,
		bpaDefaultsByYear,
		province,
		isCppExempt,
		isEiExempt,
		cpp2Exempt,
		showProvinceChangeWarning,
		taxClaimsLoading,
		currentTaxYear,
		previousTaxYear,
		currentYearExpanded,
		previousYearExpanded,
		onClaimUpdate,
		onCppExemptChange,
		onEiExemptChange,
		onCpp2ExemptChange,
		onDismissWarning,
		onToggleCurrentYearExpand,
		onTogglePreviousYearExpand
	}: Props = $props();
</script>

<section class="bg-white rounded-xl p-6 shadow-md3-1">
	<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">
		Tax Information (TD1)
	</h3>
	<p class="text-body-small text-surface-500 m-0 mb-4 flex items-center gap-2">
		<i class="fas fa-info-circle text-primary-500"></i>
		Enter additional claims from TD1 forms (spouse, dependants, etc.) for each tax year.
	</p>

	{#if showProvinceChangeWarning}
		<div
			class="flex items-center gap-3 p-3 mb-4 bg-warning-50 border border-warning-200 rounded-lg text-warning-700 text-body-small"
		>
			<i class="fas fa-exclamation-triangle text-warning-500"></i>
			<span
				>Province changed. Please review your additional TD1 claims for all years before saving.</span
			>
			<button
				type="button"
				class="ml-auto bg-transparent border-none text-warning-500 cursor-pointer p-1 opacity-70 hover:opacity-100"
				onclick={onDismissWarning}
				aria-label="Dismiss warning"
			>
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	{#if taxClaimsLoading}
		<div class="flex items-center justify-center p-8 text-surface-500">
			<i class="fas fa-spinner fa-spin mr-2"></i>
			<span>Loading tax claims...</span>
		</div>
	{:else}
		<!-- Multi-year Tax Claims Cards -->
		<div class="flex flex-col gap-4 mb-6">
			<!-- Current Year -->
			<TaxYearClaimsCard
				taxYear={currentTaxYear}
				claim={taxClaimsByYear.get(currentTaxYear) ?? null}
				bpaDefaults={bpaDefaultsByYear.get(currentTaxYear) ?? null}
				{province}
				isExpanded={currentYearExpanded}
				isCurrentYear={true}
				onUpdate={onClaimUpdate}
				onToggleExpand={onToggleCurrentYearExpand}
			/>

			<!-- Previous Year -->
			<TaxYearClaimsCard
				taxYear={previousTaxYear}
				claim={taxClaimsByYear.get(previousTaxYear) ?? null}
				bpaDefaults={bpaDefaultsByYear.get(previousTaxYear) ?? null}
				{province}
				isExpanded={previousYearExpanded}
				isCurrentYear={false}
				onUpdate={onClaimUpdate}
				onToggleExpand={onTogglePreviousYearExpand}
			/>
		</div>
	{/if}

	<!-- Exemptions (unchanged, employee-level) -->
	<div class="mt-6 pt-6 border-t border-surface-200">
		<div class="flex flex-col gap-2">
			<span class="text-body-small font-medium text-surface-700">Exemptions</span>
			<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
				<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
					<input
						type="checkbox"
						checked={isCppExempt}
						onchange={(e) => onCppExemptChange(e.currentTarget.checked)}
					/>
					<span>CPP Exempt</span>
				</label>
				<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
					<input
						type="checkbox"
						checked={isEiExempt}
						onchange={(e) => onEiExemptChange(e.currentTarget.checked)}
					/>
					<span>EI Exempt</span>
				</label>
				<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
					<input
						type="checkbox"
						checked={cpp2Exempt}
						onchange={(e) => onCpp2ExemptChange(e.currentTarget.checked)}
					/>
					<span>CPP2 Exempt</span>
					<span
						class="text-surface-400 cursor-help"
						title="CPT30 form on file - exempt from additional CPP contributions"
					>
						<i class="fas fa-info-circle"></i>
					</span>
				</label>
			</div>
		</div>
	</div>
</section>
