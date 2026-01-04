<script lang="ts">
	import type { Employee, VacationPayoutMethod } from '$lib/types/employee';
	import type { VacationRatesConfig } from '$lib/services/configService';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		vacationRatePreset: string;
		customVacationRate: number;
		vacationPayoutMethod: VacationPayoutMethod;
		vacationBalance: number;
		vacationRatesConfig: VacationRatesConfig | null;
		hasPayrollRecords: boolean;
		mode: 'create' | 'edit';
		employee: Employee | null;
		errors: Record<string, string>;
		onVacationRatePresetChange: (value: string) => void;
		onCustomVacationRateChange: (value: number) => void;
		onVacationPayoutMethodChange: (value: VacationPayoutMethod) => void;
		onVacationBalanceChange: (value: number) => void;
	}

	let {
		vacationRatePreset,
		customVacationRate,
		vacationPayoutMethod,
		vacationBalance,
		vacationRatesConfig,
		hasPayrollRecords,
		mode,
		employee,
		errors,
		onVacationRatePresetChange,
		onCustomVacationRateChange,
		onVacationPayoutMethodChange,
		onVacationBalanceChange
	}: Props = $props();

	// Dynamic vacation rate options based on province config
	const vacationRateOptions = $derived(() => {
		const options: { value: string; label: string }[] = [
			{ value: '0', label: 'None (Owner/Contractor)' }
		];

		if (vacationRatesConfig) {
			for (const tier of vacationRatesConfig.tiers) {
				const pct = (parseFloat(tier.vacationRate) * 100).toFixed(2).replace(/\.?0+$/, '');
				const label = `${pct}% (${tier.vacationWeeks} weeks${tier.minYearsOfService > 0 ? `, ${tier.minYearsOfService}+ years` : ''})`;
				options.push({ value: tier.vacationRate, label });
			}
		} else {
			// Fallback to standard options if config not loaded
			options.push(
				{ value: '0.04', label: '4% (2 weeks)' },
				{ value: '0.06', label: '6% (3 weeks, 5+ years)' },
				{ value: '0.08', label: '8% (4 weeks, Federal 10+)' }
			);
		}

		options.push({ value: 'custom', label: 'Custom Rate' });
		return options;
	});

	// Format currency with no decimals for cleaner display
	function formatCurrencyNoDecimals(amount: number): string {
		return formatCurrency(amount, { maximumFractionDigits: 0 });
	}

	// Derived: Can edit vacation balance
	const canEditBalance = $derived(mode === 'create' || !hasPayrollRecords);
</script>

<section class="bg-white rounded-xl p-6 shadow-md3-1">
	<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">
		Vacation Settings
	</h3>
	<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
		<div class="flex flex-col gap-2">
			<label for="vacationRate" class="text-body-small font-medium text-surface-700"
				>Vacation Rate</label
			>
			<select
				id="vacationRate"
				class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
				value={vacationRatePreset}
				onchange={(e) => onVacationRatePresetChange(e.currentTarget.value)}
			>
				{#each vacationRateOptions() as { value, label } (value)}
					<option {value}>{label}</option>
				{/each}
			</select>
			{#if vacationRatesConfig && vacationRatePreset !== '0' && vacationRatePreset !== 'custom'}
				{@const minimumRate = vacationRatesConfig.tiers[0]?.vacationRate ?? '0.04'}
				{#if parseFloat(vacationRatePreset) < parseFloat(minimumRate)}
					<span class="text-auxiliary-text text-warning-600 flex items-center gap-1">
						<i class="fas fa-exclamation-triangle"></i>
						Provincial minimum for {vacationRatesConfig.name} is {(parseFloat(minimumRate) * 100)
							.toFixed(2)
							.replace(/\.?0+$/, '')}%
					</span>
				{/if}
			{/if}
		</div>

		{#if vacationRatePreset === 'custom'}
			<div class="flex flex-col gap-2">
				<label for="customVacationRate" class="text-body-small font-medium text-surface-700"
					>Custom Rate (%) *</label
				>
				<div
					class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.customVacationRate
						? 'border-error-500'
						: 'border-surface-300'}"
				>
					<input
						id="customVacationRate"
						type="number"
						inputmode="decimal"
						class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
						value={customVacationRate}
						oninput={(e) => onCustomVacationRateChange(parseFloat(e.currentTarget.value) || 0)}
						min="0"
						max="100"
						step="0.01"
						placeholder="e.g., 5.77"
					/>
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">%</span>
				</div>
				{#if errors.customVacationRate}
					<span class="text-auxiliary-text text-error-600">{errors.customVacationRate}</span>
				{:else}
					<span class="text-auxiliary-text text-surface-500"
						>Enter any percentage (e.g., 5.77 for Saskatchewan 3+ weeks)</span
					>
				{/if}
			</div>
		{/if}

		{#if vacationRatePreset !== '0'}
			<div class="flex flex-col gap-2">
				<label for="vacationMethod" class="text-body-small font-medium text-surface-700"
					>Payout Method</label
				>
				<select
					id="vacationMethod"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					value={vacationPayoutMethod}
					onchange={(e) =>
						onVacationPayoutMethodChange(e.currentTarget.value as VacationPayoutMethod)}
				>
					<option value="accrual">Accrual (pay when vacation taken)</option>
					<option value="pay_as_you_go">Pay as you go (add to each paycheck)</option>
				</select>
			</div>

			{#if vacationPayoutMethod === 'accrual'}
				{#if canEditBalance}
					<div class="flex flex-col gap-2">
						<label for="vacationBalance" class="text-body-small font-medium text-surface-700">
							{mode === 'create' ? 'Initial Vacation Balance' : 'Vacation Balance'}
						</label>
						<div
							class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10"
						>
							<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
							<input
								id="vacationBalance"
								type="number"
								class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
								value={vacationBalance}
								oninput={(e) => onVacationBalanceChange(parseFloat(e.currentTarget.value) || 0)}
								min="0"
								step="0.01"
							/>
						</div>
						<span class="text-auxiliary-text text-surface-500">
							{mode === 'create'
								? 'Opening balance for vacation pay accrual'
								: 'Editable until first payroll is processed'}
						</span>
					</div>
				{:else}
					<div class="flex flex-col gap-2">
						<span class="text-body-small font-medium text-surface-700">Current Balance</span>
						<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
							{formatCurrencyNoDecimals(employee?.vacationBalance ?? 0)}
							<span class="text-auxiliary-text text-surface-400 ml-2">(managed by payroll)</span>
						</div>
					</div>
				{/if}
			{/if}
		{/if}
	</div>
</section>
