<script lang="ts">
	// PayGroupBenefitsSection - Group Benefits configuration with section-level edit mode
	import type { PayGroup, BenefitConfig, LifeInsuranceConfig } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
		onUpdate: (payGroup: PayGroup) => void;
	}

	let { payGroup, onUpdate }: Props = $props();

	// Edit mode state
	let isEditing = $state(false);

	// Form state - deep copy to avoid mutation
	let editEnabled = $state(false);
	let editHealth = $state<BenefitConfig>({ enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false });
	let editDental = $state<BenefitConfig>({ enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false });
	let editVision = $state<BenefitConfig>({ enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false });
	let editLifeInsurance = $state<LifeInsuranceConfig>({ enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false, coverageAmount: 0 });
	let editDisability = $state<BenefitConfig>({ enabled: false, employeeDeduction: 0, employerContribution: 0, isTaxable: false });

	// Enter edit mode
	function enterEditMode() {
		editEnabled = payGroup.groupBenefits.enabled;
		editHealth = { ...payGroup.groupBenefits.health };
		editDental = { ...payGroup.groupBenefits.dental };
		editVision = { ...payGroup.groupBenefits.vision };
		editLifeInsurance = { ...payGroup.groupBenefits.lifeInsurance };
		editDisability = { ...payGroup.groupBenefits.disability };
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
			groupBenefits: {
				enabled: editEnabled,
				health: editHealth,
				dental: editDental,
				vision: editVision,
				lifeInsurance: editLifeInsurance,
				disability: editDisability
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
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		}).format(amount);
	}

	// Count enabled benefits for view mode
	const enabledBenefitsCount = $derived(() => {
		let count = 0;
		if (payGroup.groupBenefits.health.enabled) count++;
		if (payGroup.groupBenefits.dental.enabled) count++;
		if (payGroup.groupBenefits.vision.enabled) count++;
		if (payGroup.groupBenefits.lifeInsurance.enabled) count++;
		if (payGroup.groupBenefits.disability.enabled) count++;
		return count;
	});

	// Calculate totals for view mode
	const totalEmployeeDeduction = $derived(() => {
		let total = 0;
		if (payGroup.groupBenefits.health.enabled) total += payGroup.groupBenefits.health.employeeDeduction;
		if (payGroup.groupBenefits.dental.enabled) total += payGroup.groupBenefits.dental.employeeDeduction;
		if (payGroup.groupBenefits.vision.enabled) total += payGroup.groupBenefits.vision.employeeDeduction;
		if (payGroup.groupBenefits.lifeInsurance.enabled) total += payGroup.groupBenefits.lifeInsurance.employeeDeduction;
		if (payGroup.groupBenefits.disability.enabled) total += payGroup.groupBenefits.disability.employeeDeduction;
		return total;
	});

	const totalEmployerContribution = $derived(() => {
		let total = 0;
		if (payGroup.groupBenefits.health.enabled) total += payGroup.groupBenefits.health.employerContribution;
		if (payGroup.groupBenefits.dental.enabled) total += payGroup.groupBenefits.dental.employerContribution;
		if (payGroup.groupBenefits.vision.enabled) total += payGroup.groupBenefits.vision.employerContribution;
		if (payGroup.groupBenefits.lifeInsurance.enabled) total += payGroup.groupBenefits.lifeInsurance.employerContribution;
		if (payGroup.groupBenefits.disability.enabled) total += payGroup.groupBenefits.disability.employerContribution;
		return total;
	});

	// Benefit type info for display
	const benefitTypes = [
		{ key: 'health', label: 'Health', icon: 'fa-heart', description: 'Medical, prescription drugs' },
		{ key: 'dental', label: 'Dental', icon: 'fa-tooth', description: 'Dental care coverage' },
		{ key: 'vision', label: 'Vision', icon: 'fa-eye', description: 'Eye exams, glasses, contacts' },
		{ key: 'lifeInsurance', label: 'Life Insurance', icon: 'fa-shield-alt', description: 'Death benefit coverage' },
		{ key: 'disability', label: 'Disability', icon: 'fa-wheelchair', description: 'Short/long term disability' }
	] as const;
</script>

<section class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
	<div class="flex justify-between items-center py-4 px-5 bg-surface-50 border-b border-surface-100 max-md:flex-col max-md:gap-3 max-md:items-start">
		<h2 class="flex items-center gap-2 text-title-medium font-semibold text-surface-800 m-0">
			<i class="fas fa-heartbeat text-success-500"></i>
			Group Benefits
		</h2>
		{#if isEditing}
			<div class="flex gap-2 max-md:w-full">
				<button class="inline-flex items-center gap-2 py-2 px-4 rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-transparent text-surface-600 border border-surface-200 hover:bg-surface-100 max-md:flex-1" onclick={cancelEdit}>Cancel</button>
				<button class="inline-flex items-center gap-2 py-2 px-4 rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-primary-500 text-white border-none hover:bg-primary-600 max-md:flex-1" onclick={saveChanges}>Save</button>
			</div>
		{:else}
			<button class="inline-flex items-center gap-2 py-2 px-4 rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-transparent text-primary-600 border border-primary-200 hover:bg-primary-50 hover:border-primary-300" onclick={enterEditMode}>
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
				Configure default benefit deductions and employer contributions for employees in this pay
				group. Individual employees can have benefits adjusted on their profiles.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="flex flex-col gap-4">
				<div class="p-4 bg-success-50 rounded-lg border border-success-100">
					<label class="flex items-start gap-3 cursor-pointer">
						<input type="checkbox" class="w-5 h-5 mt-0.5 accent-primary-500 shrink-0" bind:checked={editEnabled} />
						<span class="flex flex-col gap-1">
							<span class="text-body-content font-medium text-surface-800">Enable Group Benefits</span>
							<span class="text-auxiliary-text text-surface-500">
								Apply benefit deductions to employees in this pay group
							</span>
						</span>
					</label>
				</div>

				{#if editEnabled}
					<div class="flex flex-col gap-3">
						<!-- Health -->
						<div class="p-4 rounded-lg border transition-[150ms] {editHealth.enabled ? 'bg-white border-surface-200' : 'bg-surface-50 border-surface-200'}">
							<div class="mb-3">
								<label class="flex items-center gap-2 cursor-pointer text-body-content font-medium text-surface-800">
									<input type="checkbox" class="w-[18px] h-[18px] accent-primary-500" bind:checked={editHealth.enabled} />
									<i class="fas fa-heart text-primary-500"></i>
									<span>Health</span>
								</label>
							</div>
							{#if editHealth.enabled}
								<div class="flex flex-col gap-3 pl-6 border-l-2 border-primary-100">
									<div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employee Deduction</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editHealth.employeeDeduction} min="0" step="0.01" />
											</div>
										</div>
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employer Contribution</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editHealth.employerContribution} min="0" step="0.01" />
											</div>
										</div>
									</div>
									<label class="flex items-center gap-2 text-auxiliary-text text-surface-600 cursor-pointer">
										<input type="checkbox" class="w-4 h-4 accent-warning-500" bind:checked={editHealth.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Dental -->
						<div class="p-4 rounded-lg border transition-[150ms] {editDental.enabled ? 'bg-white border-surface-200' : 'bg-surface-50 border-surface-200'}">
							<div class="mb-3">
								<label class="flex items-center gap-2 cursor-pointer text-body-content font-medium text-surface-800">
									<input type="checkbox" class="w-[18px] h-[18px] accent-primary-500" bind:checked={editDental.enabled} />
									<i class="fas fa-tooth text-primary-500"></i>
									<span>Dental</span>
								</label>
							</div>
							{#if editDental.enabled}
								<div class="flex flex-col gap-3 pl-6 border-l-2 border-primary-100">
									<div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employee Deduction</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editDental.employeeDeduction} min="0" step="0.01" />
											</div>
										</div>
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employer Contribution</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editDental.employerContribution} min="0" step="0.01" />
											</div>
										</div>
									</div>
									<label class="flex items-center gap-2 text-auxiliary-text text-surface-600 cursor-pointer">
										<input type="checkbox" class="w-4 h-4 accent-warning-500" bind:checked={editDental.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Vision -->
						<div class="p-4 rounded-lg border transition-[150ms] {editVision.enabled ? 'bg-white border-surface-200' : 'bg-surface-50 border-surface-200'}">
							<div class="mb-3">
								<label class="flex items-center gap-2 cursor-pointer text-body-content font-medium text-surface-800">
									<input type="checkbox" class="w-[18px] h-[18px] accent-primary-500" bind:checked={editVision.enabled} />
									<i class="fas fa-eye text-primary-500"></i>
									<span>Vision</span>
								</label>
							</div>
							{#if editVision.enabled}
								<div class="flex flex-col gap-3 pl-6 border-l-2 border-primary-100">
									<div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employee Deduction</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editVision.employeeDeduction} min="0" step="0.01" />
											</div>
										</div>
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employer Contribution</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editVision.employerContribution} min="0" step="0.01" />
											</div>
										</div>
									</div>
									<label class="flex items-center gap-2 text-auxiliary-text text-surface-600 cursor-pointer">
										<input type="checkbox" class="w-4 h-4 accent-warning-500" bind:checked={editVision.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Life Insurance -->
						<div class="p-4 rounded-lg border transition-[150ms] {editLifeInsurance.enabled ? 'bg-white border-surface-200' : 'bg-surface-50 border-surface-200'}">
							<div class="mb-3">
								<label class="flex items-center gap-2 cursor-pointer text-body-content font-medium text-surface-800">
									<input type="checkbox" class="w-[18px] h-[18px] accent-primary-500" bind:checked={editLifeInsurance.enabled} />
									<i class="fas fa-shield-alt text-primary-500"></i>
									<span>Life Insurance</span>
								</label>
							</div>
							{#if editLifeInsurance.enabled}
								<div class="flex flex-col gap-3 pl-6 border-l-2 border-primary-100">
									<div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employee Deduction</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editLifeInsurance.employeeDeduction} min="0" step="0.01" />
											</div>
										</div>
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employer Contribution</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editLifeInsurance.employerContribution} min="0" step="0.01" />
											</div>
										</div>
									</div>
									<div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Coverage Amount</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editLifeInsurance.coverageAmount} min="0" step="1000" />
											</div>
										</div>
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Coverage Multiplier</span>
											<select class="py-2 px-3 border border-surface-200 rounded-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editLifeInsurance.coverageMultiplier}>
												<option value={undefined}>Fixed Amount</option>
												<option value={1}>1x Salary</option>
												<option value={2}>2x Salary</option>
												<option value={3}>3x Salary</option>
											</select>
										</div>
									</div>
									<label class="flex items-center gap-2 text-auxiliary-text text-surface-600 cursor-pointer">
										<input type="checkbox" class="w-4 h-4 accent-warning-500" bind:checked={editLifeInsurance.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Disability -->
						<div class="p-4 rounded-lg border transition-[150ms] {editDisability.enabled ? 'bg-white border-surface-200' : 'bg-surface-50 border-surface-200'}">
							<div class="mb-3">
								<label class="flex items-center gap-2 cursor-pointer text-body-content font-medium text-surface-800">
									<input type="checkbox" class="w-[18px] h-[18px] accent-primary-500" bind:checked={editDisability.enabled} />
									<i class="fas fa-wheelchair text-primary-500"></i>
									<span>Disability</span>
								</label>
							</div>
							{#if editDisability.enabled}
								<div class="flex flex-col gap-3 pl-6 border-l-2 border-primary-100">
									<div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employee Deduction</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editDisability.employeeDeduction} min="0" step="0.01" />
											</div>
										</div>
										<div class="flex flex-col gap-1">
											<span class="text-auxiliary-text text-surface-500">Employer Contribution</span>
											<div class="flex items-stretch">
												<span class="flex items-center px-2 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">$</span>
												<input type="number" class="flex-1 min-w-0 py-2 px-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100" bind:value={editDisability.employerContribution} min="0" step="0.01" />
											</div>
										</div>
									</div>
									<label class="flex items-center gap-2 text-auxiliary-text text-surface-600 cursor-pointer">
										<input type="checkbox" class="w-4 h-4 accent-warning-500" bind:checked={editDisability.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>

			<div class="flex items-start gap-2 mt-4 py-3 px-4 bg-info-50 border border-info-200 rounded-md text-auxiliary-text text-info-800">
				<i class="fas fa-calculator text-info-500 mt-0.5"></i>
				<span>
					<strong>Taxable Benefits:</strong> Employer-paid portions of certain benefits (e.g., group
					life insurance over $10,000) are taxable benefits that must be reported on T4s.
				</span>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="cursor-pointer" title="Double-click to edit">
				<div class="flex items-center gap-4 p-4 rounded-lg border {payGroup.groupBenefits.enabled ? 'bg-success-50 border-success-100' : 'bg-surface-50 border-surface-100'}">
					<div class="w-12 h-12 rounded-full flex items-center justify-center {payGroup.groupBenefits.enabled ? 'bg-success-100' : 'bg-surface-200'}">
						{#if payGroup.groupBenefits.enabled}
							<i class="fas fa-heartbeat text-2xl text-success-600"></i>
						{:else}
							<i class="fas fa-heart-broken text-2xl text-surface-400"></i>
						{/if}
					</div>
					<div class="flex flex-col gap-1">
						<span class="text-auxiliary-text text-surface-500">Group Benefits</span>
						<span class="text-title-medium font-semibold text-surface-800">
							{payGroup.groupBenefits.enabled ? `${enabledBenefitsCount()} Active` : 'Not Enabled'}
						</span>
					</div>
				</div>

				{#if payGroup.groupBenefits.enabled}
					<div class="grid grid-cols-2 gap-3 mt-4 max-md:grid-cols-1">
						{#each benefitTypes as benefit}
							{@const config = benefit.key === 'lifeInsurance'
								? payGroup.groupBenefits.lifeInsurance
								: payGroup.groupBenefits[benefit.key]}
							<div class="p-3 rounded-md border {config.enabled ? 'bg-white border-success-200' : 'bg-surface-50 border-surface-100'}">
								<div class="flex items-center gap-2 mb-2">
									<i class="fas {benefit.icon} {config.enabled ? 'text-success-500' : 'text-surface-400'}"></i>
									<span class="flex-1 text-body-content font-medium text-surface-800">{benefit.label}</span>
									<span class="py-1 px-2 rounded-full text-[10px] uppercase font-semibold {config.enabled ? 'bg-success-100 text-success-700' : 'bg-surface-200 text-surface-500'}">
										{config.enabled ? 'Active' : 'Inactive'}
									</span>
								</div>
								{#if config.enabled}
									<div class="flex gap-4 mb-2">
										<div class="flex flex-col gap-0.5">
											<span class="text-[10px] uppercase text-surface-400">Employee</span>
											<span class="text-body-content font-medium text-surface-700">{formatCurrency(config.employeeDeduction)}/pay</span>
										</div>
										<div class="flex flex-col gap-0.5">
											<span class="text-[10px] uppercase text-surface-400">Employer</span>
											<span class="text-body-content font-medium text-surface-700">{formatCurrency(config.employerContribution)}/pay</span>
										</div>
									</div>
									{#if config.isTaxable}
										<span class="inline-block py-0.5 px-2 bg-warning-100 text-warning-700 rounded-sm text-[10px] font-medium">Taxable Benefit</span>
									{/if}
								{/if}
							</div>
						{/each}
					</div>

					<div class="grid grid-cols-2 gap-4 mt-4 pt-4 border-t border-surface-200 max-md:grid-cols-1">
						<div class="flex flex-col gap-1 p-3 bg-primary-50 rounded-md">
							<span class="text-auxiliary-text text-surface-500">Total Employee Deduction</span>
							<span class="text-title-medium font-bold text-primary-700">{formatCurrency(totalEmployeeDeduction())}/pay period</span>
						</div>
						<div class="flex flex-col gap-1 p-3 bg-primary-50 rounded-md">
							<span class="text-auxiliary-text text-surface-500">Total Employer Contribution</span>
							<span class="text-title-medium font-bold text-primary-700">{formatCurrency(totalEmployerContribution())}/pay period</span>
						</div>
					</div>
				{:else}
					<div class="mt-4 p-4 bg-surface-50 rounded-md border border-dashed border-surface-200">
						<p class="m-0 text-body-content text-surface-600">
							Group benefits are not enabled for this pay group. Employees will not have benefit
							deductions applied.
						</p>
					</div>
				{/if}
			</div>

			<p class="flex items-center gap-2 mt-4 pt-4 border-t border-dashed border-surface-200 text-auxiliary-text text-surface-400 m-0">
				<i class="fas fa-mouse-pointer"></i>
				Double-click anywhere to edit
			</p>
		{/if}
	</div>
</section>
