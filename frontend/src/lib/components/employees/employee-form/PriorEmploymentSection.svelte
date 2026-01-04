<script lang="ts">
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface HireDateInfo {
		showSection: boolean;
		message: string;
	}

	interface Props {
		hireDate: string;
		hireDateInfo: HireDateInfo;
		hasPriorEmployment: boolean;
		incomeLevel: 'low' | 'high';
		initialYtdCpp: number;
		initialYtdCpp2: number;
		initialYtdEi: number;
		canEditPriorYtd: boolean;
		maxCpp: number;
		maxCpp2: number;
		maxEi: number;
		highIncomeThreshold: number;
		errors: Record<string, string>;
		onHasPriorEmploymentChange: (value: boolean) => void;
		onIncomeLevelChange: (value: 'low' | 'high') => void;
		onInitialYtdCppChange: (value: number) => void;
		onInitialYtdCpp2Change: (value: number) => void;
		onInitialYtdEiChange: (value: number) => void;
	}

	let {
		hireDate,
		hireDateInfo,
		hasPriorEmployment,
		incomeLevel,
		initialYtdCpp,
		initialYtdCpp2,
		initialYtdEi,
		canEditPriorYtd,
		maxCpp,
		maxCpp2,
		maxEi,
		highIncomeThreshold,
		errors,
		onHasPriorEmploymentChange,
		onIncomeLevelChange,
		onInitialYtdCppChange,
		onInitialYtdCpp2Change,
		onInitialYtdEiChange
	}: Props = $props();

	// Format currency with no decimals for cleaner display
	function formatCurrencyNoDecimals(amount: number): string {
		return formatCurrency(amount, { maximumFractionDigits: 0 });
	}
</script>

<section class="bg-white rounded-xl p-6 shadow-md3-1">
	<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">
		Prior Employment This Year
	</h3>

	{#if hireDateInfo.showSection}
		<p class="text-body-small text-surface-500 m-0 mb-4 flex items-start gap-2">
			<i class="fas fa-info-circle text-primary-500 mt-0.5"></i>
			<span
				>If this employee worked for another employer earlier this year, enter their prior CPP/EI
				contributions to avoid over-deduction. Income tax is automatically adjusted through
				Cumulative Averaging.</span
			>
		</p>

		<!-- Mid-year hire prompt -->
		{#if hireDateInfo.message}
			<div
				class="flex items-start gap-3 p-3 bg-warning-50 border border-warning-200 rounded-lg text-warning-700 text-body-small mb-4"
			>
				<i class="fas fa-calendar-alt text-warning-500 mt-0.5"></i>
				<span>{hireDateInfo.message}</span>
			</div>
		{/if}

		<div class="flex flex-col gap-4">
			<!-- Question 1: Has prior employment? -->
			<div class="flex flex-col gap-2">
				<span class="text-body-small font-medium text-surface-700"
					>Has this employee worked for another employer this year?</span
				>
				{#if canEditPriorYtd}
					<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
						<label
							class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer"
						>
							<input
								type="radio"
								name="hasPriorEmployment"
								value="no"
								checked={!hasPriorEmployment}
								onchange={() => onHasPriorEmploymentChange(false)}
							/>
							<span>No - Started fresh this year</span>
						</label>
						<label
							class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer"
						>
							<input
								type="radio"
								name="hasPriorEmployment"
								value="yes"
								checked={hasPriorEmployment}
								onchange={() => onHasPriorEmploymentChange(true)}
							/>
							<span>Yes - Transferred from another employer</span>
						</label>
					</div>
				{:else}
					<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
						{hasPriorEmployment
							? 'Yes - Transferred from another employer'
							: 'No - Started fresh this year'}
						<span class="text-auxiliary-text text-surface-400 ml-2"
							>(locked after first payroll)</span
						>
					</div>
				{/if}
			</div>

			{#if hasPriorEmployment}
				<!-- Question 2: Income level -->
				<div class="flex flex-col gap-2">
					<span class="text-body-small font-medium text-surface-700"
						>Estimated annual income level?</span
					>
					{#if canEditPriorYtd}
						<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
							<label
								class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer"
							>
								<input
									type="radio"
									name="incomeLevel"
									value="low"
									checked={incomeLevel === 'low'}
									onchange={() => onIncomeLevelChange('low')}
								/>
								<span>Below ${highIncomeThreshold.toLocaleString()}/year</span>
							</label>
							<label
								class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer"
							>
								<input
									type="radio"
									name="incomeLevel"
									value="high"
									checked={incomeLevel === 'high'}
									onchange={() => onIncomeLevelChange('high')}
								/>
								<span>${highIncomeThreshold.toLocaleString()}/year or above</span>
							</label>
						</div>
					{:else}
						<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
							{incomeLevel === 'high'
								? `$${highIncomeThreshold.toLocaleString()}/year or above`
								: `Below $${highIncomeThreshold.toLocaleString()}/year`}
						</div>
					{/if}
				</div>

				{#if incomeLevel === 'low'}
					<!-- Low income notice -->
					<div
						class="flex items-center gap-3 p-3 bg-success-50 border border-success-200 rounded-lg text-success-700 text-body-small"
					>
						<i class="fas fa-check-circle text-success-500"></i>
						<span
							>No prior CPP/EI input needed - employees below ${highIncomeThreshold.toLocaleString()}/year
							rarely hit annual maximums.</span
						>
					</div>
				{:else}
					<!-- High income: Show YTD input fields -->
					<div class="grid grid-cols-3 gap-4 max-sm:grid-cols-1">
						<div class="flex flex-col gap-2">
							<label for="initialYtdCpp" class="text-body-small font-medium text-surface-700"
								>Prior CPP Contributions</label
							>
							{#if canEditPriorYtd}
								<div
									class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.initialYtdCpp
										? 'border-error-500'
										: 'border-surface-300'}"
								>
									<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
									<input
										id="initialYtdCpp"
										type="number"
										class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
										value={initialYtdCpp}
										oninput={(e) => onInitialYtdCppChange(parseFloat(e.currentTarget.value) || 0)}
										min="0"
										max={maxCpp}
										step="0.01"
									/>
								</div>
								{#if errors.initialYtdCpp}
									<span class="text-auxiliary-text text-error-600">{errors.initialYtdCpp}</span>
								{:else}
									<span class="text-auxiliary-text text-surface-500"
										>Max: ${maxCpp.toLocaleString()}</span
									>
								{/if}
							{:else}
								<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
									{formatCurrencyNoDecimals(initialYtdCpp)}
								</div>
							{/if}
						</div>

						<div class="flex flex-col gap-2">
							<label for="initialYtdEi" class="text-body-small font-medium text-surface-700"
								>Prior EI Premiums</label
							>
							{#if canEditPriorYtd}
								<div
									class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.initialYtdEi
										? 'border-error-500'
										: 'border-surface-300'}"
								>
									<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
									<input
										id="initialYtdEi"
										type="number"
										class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
										value={initialYtdEi}
										oninput={(e) => onInitialYtdEiChange(parseFloat(e.currentTarget.value) || 0)}
										min="0"
										max={maxEi}
										step="0.01"
									/>
								</div>
								{#if errors.initialYtdEi}
									<span class="text-auxiliary-text text-error-600">{errors.initialYtdEi}</span>
								{:else}
									<span class="text-auxiliary-text text-surface-500"
										>Max: ${maxEi.toLocaleString()}</span
									>
								{/if}
							{:else}
								<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
									{formatCurrencyNoDecimals(initialYtdEi)}
								</div>
							{/if}
						</div>

						<div class="flex flex-col gap-2">
							<label for="initialYtdCpp2" class="text-body-small font-medium text-surface-700">
								Prior CPP2
								<span class="text-surface-400">(optional)</span>
							</label>
							{#if canEditPriorYtd}
								<div
									class="flex items-center border rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10 {errors.initialYtdCpp2
										? 'border-error-500'
										: 'border-surface-300'}"
								>
									<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
									<input
										id="initialYtdCpp2"
										type="number"
										class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
										value={initialYtdCpp2}
										oninput={(e) => onInitialYtdCpp2Change(parseFloat(e.currentTarget.value) || 0)}
										min="0"
										max={maxCpp2}
										step="0.01"
									/>
								</div>
								{#if errors.initialYtdCpp2}
									<span class="text-auxiliary-text text-error-600">{errors.initialYtdCpp2}</span>
								{:else}
									<span class="text-auxiliary-text text-surface-500"
										>For income &gt;$71,300. Max: ${maxCpp2.toLocaleString()}</span
									>
								{/if}
							{:else}
								<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
									{formatCurrencyNoDecimals(initialYtdCpp2)}
								</div>
							{/if}
						</div>
					</div>

					<!-- Help text -->
					<div
						class="flex items-start gap-2 p-3 bg-primary-50 border border-primary-200 rounded-lg text-primary-700 text-body-small"
					>
						<i class="fas fa-lightbulb text-primary-500 mt-0.5"></i>
						<span
							>These values can be found on the employee's most recent pay stub from their previous
							employer.</span
						>
					</div>
				{/if}
			{/if}
		</div>
	{:else if hireDate}
		<!-- Section hidden - show reason -->
		<div
			class="flex items-start gap-3 p-4 bg-surface-50 border border-surface-200 rounded-lg text-surface-600 text-body-small"
		>
			<i class="fas fa-calendar-check text-surface-400 mt-0.5"></i>
			<span>{hireDateInfo.message || 'Not applicable for this hire date.'}</span>
		</div>
	{:else}
		<!-- No hire date entered yet -->
		<div
			class="flex items-start gap-3 p-4 bg-surface-50 border border-surface-200 rounded-lg text-surface-500 text-body-small"
		>
			<i class="fas fa-calendar text-surface-400 mt-0.5"></i>
			<span>Enter a hire date to see prior employment options.</span>
		</div>
	{/if}
</section>
