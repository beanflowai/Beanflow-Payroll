<script lang="ts">
	// PayGroupDeductionsSection - Custom Deductions table with add/edit/delete
	import type { PayGroup, CustomDeduction, DeductionType, CalculationType, DeductionCategory } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
		onUpdate: (payGroup: PayGroup) => void;
	}

	let { payGroup, onUpdate }: Props = $props();

	// Edit mode state
	let isEditing = $state(false);

	// Form state for the entire deductions list
	let editDeductions = $state<CustomDeduction[]>([]);

	// Modal state for adding/editing a single deduction
	let showDeductionModal = $state(false);
	let editingDeductionIndex = $state<number | null>(null);
	let modalDeduction = $state<CustomDeduction>({
		id: '',
		name: '',
		category: 'other',
		taxTreatment: 'post_tax',
		calculationType: 'fixed',
		amount: 0,
		isEmployerContribution: false,
		isDefaultEnabled: true
	});

	// Enter edit mode
	function enterEditMode() {
		const customDeductions = payGroup.deductionsConfig?.customDeductions ?? [];
		editDeductions = customDeductions.map((d) => ({ ...d }));
		isEditing = true;
	}

	// Cancel edit
	function cancelEdit() {
		isEditing = false;
		showDeductionModal = false;
		editingDeductionIndex = null;
	}

	// Save changes
	function saveChanges() {
		const updated: PayGroup = {
			...payGroup,
			deductionsConfig: {
				...payGroup.deductionsConfig,
				customDeductions: editDeductions
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

	// Open modal for new deduction
	function openAddModal() {
		editingDeductionIndex = null;
		modalDeduction = {
			id: `cd-${Date.now()}`,
			name: '',
			category: 'other',
			taxTreatment: 'post_tax',
			calculationType: 'fixed',
			amount: 0,
			isEmployerContribution: false,
			isDefaultEnabled: true
		};
		showDeductionModal = true;
	}

	// Open modal for editing existing deduction
	function openEditModal(index: number) {
		editingDeductionIndex = index;
		modalDeduction = { ...editDeductions[index] };
		showDeductionModal = true;
	}

	// Save modal deduction
	function saveDeduction() {
		if (editingDeductionIndex !== null) {
			// Update existing
			editDeductions[editingDeductionIndex] = { ...modalDeduction };
		} else {
			// Add new
			editDeductions = [...editDeductions, { ...modalDeduction }];
		}
		showDeductionModal = false;
		editingDeductionIndex = null;
	}

	// Delete deduction
	function deleteDeduction(index: number) {
		editDeductions = editDeductions.filter((_, i) => i !== index);
	}

	// Close modal
	function closeModal() {
		showDeductionModal = false;
		editingDeductionIndex = null;
	}

	// Format currency
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			minimumFractionDigits: 0,
			maximumFractionDigits: 2
		}).format(amount);
	}

	// Format deduction tax treatment
	function formatTaxTreatment(taxTreatment: DeductionType): string {
		return taxTreatment === 'pre_tax' ? 'Pre-Tax' : 'Post-Tax';
	}

	// Format calculation type
	function formatCalculation(type: CalculationType, amount: number): string {
		return type === 'percentage' ? `${amount}%` : formatCurrency(amount);
	}

	// Modal validation
	const isModalValid = $derived(
		modalDeduction.name.trim().length > 0 && modalDeduction.amount > 0
	);
</script>

<section class="bg-white rounded-xl shadow-md3-1 overflow-hidden">
	<div class="flex justify-between items-center py-4 px-5 bg-surface-50 border-b border-surface-100 max-md:flex-col max-md:gap-3 max-md:items-start">
		<h2 class="flex items-center gap-2 text-title-medium font-semibold text-surface-800 m-0">
			<i class="fas fa-receipt text-info-500"></i>
			Custom Deductions
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
				Define custom deductions that can be applied to employees in this pay group. These can
				include RRSP contributions, parking fees, charitable donations, or any other recurring
				deductions.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="flex flex-col gap-4">
				{#if editDeductions.length > 0}
					<div class="border border-surface-200 rounded-lg overflow-hidden">
						<div class="grid grid-cols-[2fr_1fr_1fr_1fr_80px_100px] gap-3 py-3 px-4 bg-surface-100 text-auxiliary-text font-semibold text-surface-600 uppercase max-md:hidden">
							<span>Name</span>
							<span>Type</span>
							<span>Amount</span>
							<span>Employer Match</span>
							<span>Default</span>
							<span>Actions</span>
						</div>
						{#each editDeductions as deduction, index}
							<div class="grid grid-cols-[2fr_1fr_1fr_1fr_80px_100px] gap-3 py-3 px-4 border-t border-surface-100 items-center hover:bg-surface-50 max-md:grid-cols-1 max-md:gap-2 max-md:p-4">
								<span class="max-md:before:content-[attr(data-label)] max-md:before:font-medium max-md:before:text-surface-500 max-md:before:mr-2">
									<span class="font-medium text-surface-800 block">{deduction.name}</span>
									{#if deduction.description}
										<span class="text-auxiliary-text text-surface-500">{deduction.description}</span>
									{/if}
								</span>
								<span>
									<span class="inline-block py-1 px-2 rounded-full text-auxiliary-text {deduction.taxTreatment === 'pre_tax' ? 'bg-primary-50 text-primary-700' : 'bg-surface-100 text-surface-600'}">
										{formatTaxTreatment(deduction.taxTreatment)}
									</span>
								</span>
								<span>
									{formatCalculation(deduction.calculationType, deduction.amount)}
									{#if deduction.calculationType === 'percentage'}
										<span class="text-auxiliary-text text-surface-500 ml-1">of gross</span>
									{/if}
								</span>
								<span class="text-success-600 font-medium">
									{#if deduction.isEmployerContribution && deduction.employerAmount}
										{deduction.calculationType === 'percentage'
											? `${deduction.employerAmount}%`
											: formatCurrency(deduction.employerAmount)}
									{:else}
										—
									{/if}
								</span>
								<span>
									{#if deduction.isDefaultEnabled}
										<i class="fas fa-check-circle text-success-500"></i>
									{:else}
										<i class="fas fa-minus-circle text-surface-400"></i>
									{/if}
								</span>
								<span class="flex gap-1">
									<button class="w-8 h-8 flex items-center justify-center border-none bg-transparent text-surface-500 rounded-md cursor-pointer transition-[150ms] hover:bg-surface-100 hover:text-primary-600" onclick={() => openEditModal(index)} title="Edit">
										<i class="fas fa-pen"></i>
									</button>
									<button class="w-8 h-8 flex items-center justify-center border-none bg-transparent text-surface-500 rounded-md cursor-pointer transition-[150ms] hover:bg-error-50 hover:text-error-600" onclick={() => deleteDeduction(index)} title="Delete">
										<i class="fas fa-trash"></i>
									</button>
								</span>
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-8 px-4 text-surface-500">
						<i class="fas fa-receipt text-[32px] mb-3 text-surface-300"></i>
						<p class="text-body-content m-0 mb-2">No custom deductions defined</p>
					</div>
				{/if}

				<button class="inline-flex items-center gap-2 py-3 px-4 bg-primary-50 text-primary-600 border border-dashed border-primary-300 rounded-md text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-primary-100 hover:border-solid" onclick={openAddModal}>
					<i class="fas fa-plus"></i>
					Add Deduction
				</button>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="cursor-pointer" title="Double-click to edit">
				{#if (payGroup.deductionsConfig?.customDeductions ?? []).length > 0}
					<div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
						{#each payGroup.deductionsConfig?.customDeductions ?? [] as deduction}
							<div class="p-4 bg-surface-50 rounded-lg border border-surface-100">
								<div class="flex justify-between items-start mb-2">
									<span class="text-body-content font-semibold text-surface-800">{deduction.name}</span>
									<span class="inline-block py-1 px-2 rounded-full text-auxiliary-text {deduction.taxTreatment === 'pre_tax' ? 'bg-primary-50 text-primary-700' : 'bg-surface-100 text-surface-600'}">
										{formatTaxTreatment(deduction.taxTreatment)}
									</span>
								</div>
								{#if deduction.description}
									<p class="text-auxiliary-text text-surface-500 m-0 mb-3">{deduction.description}</p>
								{/if}
								<div class="flex flex-col gap-2">
									<div class="flex justify-between items-center">
										<span class="text-auxiliary-text text-surface-500">Amount</span>
										<span class="text-body-content font-medium text-surface-800">
											{formatCalculation(deduction.calculationType, deduction.amount)}
											{#if deduction.calculationType === 'percentage'}
												<span class="text-auxiliary-text text-surface-500 font-normal">of gross pay</span>
											{/if}
										</span>
									</div>
									{#if deduction.isEmployerContribution && deduction.employerAmount}
										<div class="flex justify-between items-center">
											<span class="text-auxiliary-text text-surface-500">Employer Match</span>
											<span class="text-body-content font-medium text-success-600">
												{deduction.calculationType === 'percentage'
													? `${deduction.employerAmount}%`
													: formatCurrency(deduction.employerAmount)}
											</span>
										</div>
									{/if}
									<div class="flex justify-between items-center">
										<span class="text-auxiliary-text text-surface-500">Default Enabled</span>
										<span class="text-body-content font-medium">
											{#if deduction.isDefaultEnabled}
												<span class="text-success-600">Yes</span>
											{:else}
												<span class="text-surface-500">No (opt-in)</span>
											{/if}
										</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="text-center py-8 px-4 text-surface-500">
						<i class="fas fa-receipt text-[32px] mb-3 text-surface-300"></i>
						<p class="text-body-content m-0 mb-2">No custom deductions defined for this pay group</p>
						<span class="text-auxiliary-text">
							Custom deductions can include RRSP contributions, parking fees, charitable donations,
							and more.
						</span>
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

<!-- Add/Edit Deduction Modal -->
{#if showDeductionModal}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-[1000]" onclick={closeModal}>
		<div class="bg-white rounded-xl w-full max-w-[500px] max-h-[90vh] overflow-y-auto shadow-md3-3" onclick={(e) => e.stopPropagation()}>
			<div class="flex justify-between items-center py-4 px-5 border-b border-surface-100">
				<h3 class="m-0 text-title-medium font-semibold text-surface-800">{editingDeductionIndex !== null ? 'Edit' : 'Add'} Deduction</h3>
				<button class="w-8 h-8 flex items-center justify-center border-none bg-transparent text-surface-500 rounded-md cursor-pointer hover:bg-surface-100" onclick={closeModal}>
					<i class="fas fa-times"></i>
				</button>
			</div>

			<div class="p-5 flex flex-col gap-4">
				<div class="flex flex-col gap-1">
					<label for="deduction-name" class="text-auxiliary-text font-medium text-surface-600">Name *</label>
					<input
						type="text"
						id="deduction-name"
						class="p-3 border border-surface-200 rounded-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
						bind:value={modalDeduction.name}
						placeholder="e.g., RRSP Contribution"
					/>
				</div>

				<div class="flex flex-col gap-1">
					<label for="deduction-description" class="text-auxiliary-text font-medium text-surface-600">Description</label>
					<input
						type="text"
						id="deduction-description"
						class="p-3 border border-surface-200 rounded-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
						bind:value={modalDeduction.description}
						placeholder="Optional description"
					/>
				</div>

				<div class="grid grid-cols-2 gap-4 max-md:grid-cols-1">
					<div class="flex flex-col gap-1">
						<label for="deduction-type" class="text-auxiliary-text font-medium text-surface-600">Tax Treatment</label>
						<select id="deduction-type" class="p-3 border border-surface-200 rounded-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100" bind:value={modalDeduction.taxTreatment}>
							<option value="pre_tax">Pre-Tax</option>
							<option value="post_tax">Post-Tax</option>
						</select>
						<p class="text-auxiliary-text text-surface-500 mt-1 m-0">
							{modalDeduction.taxTreatment === 'pre_tax'
								? 'Deducted before tax calculations (reduces taxable income)'
								: 'Deducted after tax calculations'}
						</p>
					</div>

					<div class="flex flex-col gap-1">
						<label for="calc-type" class="text-auxiliary-text font-medium text-surface-600">Calculation Type</label>
						<select id="calc-type" class="p-3 border border-surface-200 rounded-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100" bind:value={modalDeduction.calculationType}>
							<option value="fixed">Fixed Amount</option>
							<option value="percentage">Percentage of Gross</option>
						</select>
					</div>
				</div>

				<div class="flex flex-col gap-1">
					<label for="amount" class="text-auxiliary-text font-medium text-surface-600">
						Amount *
						{#if modalDeduction.calculationType === 'percentage'}
							(%)
						{/if}
					</label>
					<div class="flex items-stretch">
						<span class="flex items-center px-3 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">
							{modalDeduction.calculationType === 'percentage' ? '%' : '$'}
						</span>
						<input
							type="number"
							id="amount"
							class="flex-1 p-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
							bind:value={modalDeduction.amount}
							min="0"
							step={modalDeduction.calculationType === 'percentage' ? '0.5' : '1'}
						/>
					</div>
				</div>

				<div class="flex flex-col gap-1">
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" class="w-[18px] h-[18px] accent-primary-500" bind:checked={modalDeduction.isEmployerContribution} />
						<span>Employer contributes to this deduction</span>
					</label>
				</div>

				{#if modalDeduction.isEmployerContribution}
					<div class="flex flex-col gap-1 ml-6 pl-4 border-l-2 border-primary-100">
						<label for="employer-amount" class="text-auxiliary-text font-medium text-surface-600">Employer Contribution Amount</label>
						<div class="flex items-stretch">
							<span class="flex items-center px-3 bg-surface-100 border border-surface-200 border-r-0 rounded-l-md text-body-content text-surface-500">
								{modalDeduction.calculationType === 'percentage' ? '%' : '$'}
							</span>
							<input
								type="number"
								id="employer-amount"
								class="flex-1 p-3 border border-surface-200 rounded-r-md text-body-content text-surface-800 bg-white focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
								bind:value={modalDeduction.employerAmount}
								min="0"
								step={modalDeduction.calculationType === 'percentage' ? '0.5' : '1'}
							/>
						</div>
					</div>
				{/if}

				<div class="flex flex-col gap-1">
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" class="w-[18px] h-[18px] accent-primary-500" bind:checked={modalDeduction.isDefaultEnabled} />
						<span>Enabled by default for new employees</span>
					</label>
					<p class="text-auxiliary-text text-surface-500 mt-1 m-0">
						{modalDeduction.isDefaultEnabled
							? 'New employees will have this deduction applied automatically'
							: 'Employees must opt-in to this deduction'}
					</p>
				</div>
			</div>

			<div class="flex justify-end gap-3 py-4 px-5 border-t border-surface-100">
				<button class="inline-flex items-center gap-2 py-2 px-4 rounded-md text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-transparent text-surface-600 border border-surface-200 hover:bg-surface-100" onclick={closeModal}>Cancel</button>
				<button class="inline-flex items-center gap-2 py-3 px-5 bg-primary-500 text-white border-none rounded-md text-body-content font-medium cursor-pointer transition-[150ms] hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed" onclick={saveDeduction} disabled={!isModalValid}>
					{editingDeductionIndex !== null ? 'Save Changes' : 'Add Deduction'}
				</button>
			</div>
		</div>
	</div>
{/if}
