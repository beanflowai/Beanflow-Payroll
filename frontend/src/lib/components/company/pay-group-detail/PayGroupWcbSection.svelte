<script lang="ts">
	// PayGroupWcbSection - WCB/Workers Compensation configuration with section-level edit mode
	import type { PayGroup } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
		onUpdate: (payGroup: PayGroup) => void;
	}

	let { payGroup, onUpdate }: Props = $props();

	// Edit mode state
	let isEditing = $state(false);

	// Form state
	let editEnabled = $state(false);
	let editIndustryClassCode = $state('');
	let editIndustryName = $state('');
	let editAssessmentRate = $state(0);
	let editMaxAssessableEarnings = $state<number | undefined>(undefined);

	// Enter edit mode
	function enterEditMode() {
		editEnabled = payGroup.wcbConfig.enabled;
		editIndustryClassCode = payGroup.wcbConfig.industryClassCode ?? '';
		editIndustryName = payGroup.wcbConfig.industryName ?? '';
		editAssessmentRate = payGroup.wcbConfig.assessmentRate;
		editMaxAssessableEarnings = payGroup.wcbConfig.maxAssessableEarnings;
		isEditing = true;
	}

	// Cancel edit
	function cancelEdit() {
		isEditing = false;
	}

	// Save changes
	function saveChanges() {
		const updated: PayGroup = {
			...payGroup,
			wcbConfig: {
				enabled: editEnabled,
				industryClassCode: editEnabled ? editIndustryClassCode || undefined : undefined,
				industryName: editEnabled ? editIndustryName || undefined : undefined,
				assessmentRate: editEnabled ? editAssessmentRate : 0,
				maxAssessableEarnings: editEnabled ? editMaxAssessableEarnings : undefined
			},
			updatedAt: new Date().toISOString()
		};
		onUpdate(updated);
		isEditing = false;
	}

	// Handle double-click
	function handleDoubleClick() {
		if (!isEditing) {
			enterEditMode();
		}
	}

	// Format currency
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
		}).format(amount);
	}

	// Format rate as percentage
	function formatRate(rate: number): string {
		return `$${rate.toFixed(2)} per $100`;
	}

	// Validation
	const isValid = $derived(!editEnabled || (editIndustryClassCode.length > 0 && editAssessmentRate > 0));
</script>

<section class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
	<div class="flex justify-between items-center p-4 px-5 bg-surface-50 border-b border-surface-100 max-md:flex-col max-md:gap-3 max-md:items-start">
		<h2 class="flex items-center gap-2 text-title-medium font-semibold text-surface-800 m-0">
			<i class="fas fa-hard-hat text-warning-500"></i>
			Workers' Compensation (WCB)
		</h2>
		{#if isEditing}
			<div class="flex gap-2 max-md:w-full">
				<button
					class="inline-flex items-center gap-2 py-2 px-4 rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-transparent text-surface-600 border border-surface-200 hover:bg-surface-100 max-md:flex-1"
					onclick={cancelEdit}
				>
					Cancel
				</button>
				<button
					class="inline-flex items-center gap-2 py-2 px-4 rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-primary-500 text-white border-none hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed max-md:flex-1"
					onclick={saveChanges}
					disabled={!isValid}
				>
					Save
				</button>
			</div>
		{:else}
			<button
				class="inline-flex items-center gap-2 py-2 px-4 rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-transparent text-primary-600 border border-primary-200 hover:bg-primary-50 hover:border-primary-300"
				onclick={enterEditMode}
			>
				<i class="fas fa-pen"></i>
				Edit
			</button>
		{/if}
	</div>

	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="p-5" ondblclick={handleDoubleClick}>
		<div class="flex items-start gap-2 py-3 px-4 bg-surface-50 rounded-md mb-4 text-body-content text-surface-600">
			<i class="fas fa-info-circle text-primary-500 mt-0.5"></i>
			<span>
				Workers' Compensation Board (WCB) coverage provides insurance for workplace injuries.
				Employers pay premiums based on their industry classification code and assessment rate.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="flex flex-col gap-4">
				<div class="p-4 bg-warning-50 rounded-lg border border-warning-100">
					<label class="flex items-start gap-3 cursor-pointer">
						<input
							type="checkbox"
							class="w-5 h-5 mt-0.5 accent-primary-500 shrink-0"
							bind:checked={editEnabled}
						/>
						<span class="flex flex-col gap-1">
							<span class="text-body-content font-medium text-surface-800">Enable WCB for this Pay Group</span>
							<span class="text-auxiliary-text text-surface-500">
								Calculate and remit WCB premiums for employees in this group
							</span>
						</span>
					</label>
				</div>

				{#if editEnabled}
					<div class="flex flex-col gap-4 pl-4 border-l-[3px] border-warning-200">
						<div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
							<div class="flex flex-col gap-1">
								<label for="industryClassCode" class="text-auxiliary-text font-medium text-surface-600">Industry Class Code *</label>
								<input
									type="text"
									id="industryClassCode"
									bind:value={editIndustryClassCode}
									placeholder="e.g., 72300"
									class="p-3 border border-surface-200 rounded-md text-body-content text-surface-800 bg-white transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100 {editIndustryClassCode.length === 0 ? 'border-error-400' : ''}"
								/>
								<p class="text-auxiliary-text text-surface-500 mt-1">
									Your WCB industry classification code (contact your provincial WCB)
								</p>
							</div>

							<div class="flex flex-col gap-1">
								<label for="industryName" class="text-auxiliary-text font-medium text-surface-600">Industry Name</label>
								<input
									type="text"
									id="industryName"
									bind:value={editIndustryName}
									placeholder="e.g., Office Administrative Services"
									class="p-3 border border-surface-200 rounded-md text-body-content text-surface-800 bg-white transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
								/>
								<p class="text-auxiliary-text text-surface-500 mt-1">Description of your industry classification</p>
							</div>
						</div>

						<div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
							<div class="flex flex-col gap-1">
								<label for="assessmentRate" class="text-auxiliary-text font-medium text-surface-600">Assessment Rate (per $100) *</label>
								<div class="flex items-stretch">
									<span class="flex items-center px-3 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
									<input
										type="number"
										id="assessmentRate"
										bind:value={editAssessmentRate}
										min="0"
										step="0.01"
										placeholder="0.00"
										class="flex-1 p-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100 {editAssessmentRate <= 0 ? 'border-error-400' : ''}"
									/>
								</div>
								<p class="text-auxiliary-text text-surface-500 mt-1">
									Premium rate per $100 of assessable earnings (check your WCB rate sheet)
								</p>
							</div>

							<div class="flex flex-col gap-1">
								<label for="maxEarnings" class="text-auxiliary-text font-medium text-surface-600">Maximum Assessable Earnings</label>
								<div class="flex items-stretch">
									<span class="flex items-center px-3 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
									<input
										type="number"
										id="maxEarnings"
										bind:value={editMaxAssessableEarnings}
										min="0"
										step="1"
										placeholder="Optional"
										class="flex-1 p-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
									/>
								</div>
								<p class="text-auxiliary-text text-surface-500 mt-1">
									Annual cap on assessable earnings (set by your province)
								</p>
							</div>
						</div>
					</div>
				{/if}
			</div>

			<div class="flex items-start gap-2 mt-4 py-3 px-4 bg-info-50 border border-info-200 rounded-md text-auxiliary-text text-info-800">
				<i class="fas fa-map-marker-alt text-info-500 mt-0.5"></i>
				<span>
					<strong>Provincial Variations:</strong> WCB is administered provincially. In Ontario it's
					called WSIB, in BC it's WorkSafeBC, etc. Rates and maximum assessable earnings vary by
					province.
				</span>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="cursor-pointer" title="Double-click to edit">
				<div class="flex items-center gap-4 p-4 rounded-lg border {payGroup.wcbConfig.enabled ? 'bg-warning-50 border-warning-100' : 'bg-surface-50 border-surface-100'}">
					<div class="w-12 h-12 rounded-full flex items-center justify-center {payGroup.wcbConfig.enabled ? 'bg-warning-100' : 'bg-surface-200'}">
						{#if payGroup.wcbConfig.enabled}
							<i class="fas fa-shield-alt text-2xl text-warning-600"></i>
						{:else}
							<i class="fas fa-shield-virus text-2xl text-surface-400"></i>
						{/if}
					</div>
					<div class="flex flex-col gap-1">
						<span class="text-auxiliary-text text-surface-500">WCB Coverage</span>
						<span class="text-title-medium font-semibold text-surface-800">
							{payGroup.wcbConfig.enabled ? 'Enabled' : 'Not Enabled'}
						</span>
					</div>
				</div>

				{#if payGroup.wcbConfig.enabled}
					<div class="mt-4 flex flex-col gap-4">
						<div class="py-3 px-4 bg-primary-50 rounded-md flex flex-col gap-1">
							<div class="flex justify-between items-center">
								<span class="text-auxiliary-text text-surface-500">Industry Classification</span>
							</div>
							<div class="flex flex-col gap-1">
								<span class="text-title-medium font-bold text-primary-700 font-mono">{payGroup.wcbConfig.industryClassCode ?? '—'}</span>
								{#if payGroup.wcbConfig.industryName}
									<span class="text-body-content text-surface-700">{payGroup.wcbConfig.industryName}</span>
								{/if}
							</div>
						</div>

						<div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
							<div class="py-3 px-4 bg-surface-50 rounded-md flex flex-col gap-1">
								<span class="text-auxiliary-text text-surface-500">Assessment Rate</span>
								<span class="text-body-content font-semibold text-warning-700">
									{formatRate(payGroup.wcbConfig.assessmentRate)}
								</span>
							</div>

							<div class="py-3 px-4 bg-surface-50 rounded-md flex flex-col gap-1">
								<span class="text-auxiliary-text text-surface-500">Max Assessable Earnings</span>
								<span class="text-body-content font-semibold text-surface-800">
									{payGroup.wcbConfig.maxAssessableEarnings
										? formatCurrency(payGroup.wcbConfig.maxAssessableEarnings)
										: 'Not Set'}
								</span>
							</div>
						</div>

						<div class="flex items-center gap-2 py-3 px-4 bg-surface-100 rounded-md text-auxiliary-text text-surface-600">
							<i class="fas fa-calculator text-primary-500"></i>
							<span>
								Estimated annual premium for an employee earning $50,000:
								<strong>
									{formatCurrency((50000 / 100) * payGroup.wcbConfig.assessmentRate)}
								</strong>
							</span>
						</div>
					</div>
				{:else}
					<div class="flex items-start gap-3 mt-4 p-4 bg-surface-50 rounded-md border border-dashed border-surface-200">
						<i class="fas fa-exclamation-triangle text-warning-500 text-xl"></i>
						<div>
							<p class="m-0 text-body-content text-surface-600">
								WCB coverage is not enabled for this pay group. Employees will not have WCB
								premiums calculated.
							</p>
							<p class="mt-2 text-auxiliary-text text-surface-500">
								Note: Most employers are required by law to register with their provincial WCB.
								Exemptions may apply to certain industries or ownership structures.
							</p>
						</div>
					</div>
				{/if}
			</div>

			<p class="flex items-center gap-2 mt-4 pt-4 border-t border-dashed border-surface-200 text-auxiliary-text text-surface-400">
				<i class="fas fa-mouse-pointer"></i>
				Double-click anywhere to edit
			</p>
		{/if}
	</div>
</section>
