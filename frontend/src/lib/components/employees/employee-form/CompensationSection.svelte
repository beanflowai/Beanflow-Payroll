<script lang="ts">
	interface Props {
		compensationType: 'salaried' | 'hourly';
		annualSalary: number;
		hourlyRate: number;
		errors: Record<string, string>;
		onCompensationTypeChange: (type: 'salaried' | 'hourly') => void;
		onAnnualSalaryChange: (value: number) => void;
		onHourlyRateChange: (value: number) => void;
	}

	let {
		compensationType,
		annualSalary,
		hourlyRate,
		errors,
		onCompensationTypeChange,
		onAnnualSalaryChange,
		onHourlyRateChange
	}: Props = $props();
</script>

<section class="bg-white rounded-xl p-6 shadow-md3-1">
	<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Compensation</h3>
	<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
		<div class="flex flex-col gap-2 col-span-full">
			<span class="text-body-small font-medium text-surface-700">Compensation Type *</span>
			<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
				<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
					<input
						type="radio"
						name="compensationType"
						value="salaried"
						checked={compensationType === 'salaried'}
						onchange={() => onCompensationTypeChange('salaried')}
					/>
					<span>Annual Salary</span>
				</label>
				<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
					<input
						type="radio"
						name="compensationType"
						value="hourly"
						checked={compensationType === 'hourly'}
						onchange={() => onCompensationTypeChange('hourly')}
					/>
					<span>Hourly Rate</span>
				</label>
			</div>
		</div>

		{#if compensationType === 'salaried'}
			<div class="flex flex-col gap-2">
				<label for="annualSalary" class="text-body-small font-medium text-surface-700">Annual Salary *</label>
				<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
					<input
						id="annualSalary"
						type="number"
						class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
						value={annualSalary}
						oninput={(e) => onAnnualSalaryChange(parseFloat(e.currentTarget.value) || 0)}
						min="0"
						step="100"
					/>
				</div>
				{#if errors.annualSalary}
					<span class="text-auxiliary-text text-error-600">{errors.annualSalary}</span>
				{/if}
			</div>
		{:else}
			<div class="flex flex-col gap-2">
				<label for="hourlyRate" class="text-body-small font-medium text-surface-700">Hourly Rate *</label>
				<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
					<input
						id="hourlyRate"
						type="number"
						class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
						value={hourlyRate}
						oninput={(e) => onHourlyRateChange(parseFloat(e.currentTarget.value) || 0)}
						min="0"
						step="0.01"
					/>
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">/hr</span>
				</div>
				{#if errors.hourlyRate}
					<span class="text-auxiliary-text text-error-600">{errors.hourlyRate}</span>
				{/if}
			</div>
		{/if}
	</div>
</section>
