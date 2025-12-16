<script lang="ts">
	// PayGroupDeductionsSection - Custom Deductions table with add/edit/delete
	import type { PayGroup, CustomDeduction, DeductionType, CalculationType } from '$lib/types/pay-group';

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
		type: 'post_tax',
		calculationType: 'fixed',
		amount: 0,
		isEmployerContribution: false,
		isDefaultEnabled: true
	});

	// Enter edit mode
	function enterEditMode() {
		editDeductions = payGroup.customDeductions.map((d) => ({ ...d }));
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
			customDeductions: editDeductions,
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
			type: 'post_tax',
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

	// Format deduction type
	function formatType(type: DeductionType): string {
		return type === 'pre_tax' ? 'Pre-Tax' : 'Post-Tax';
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

<section class="info-section">
	<div class="section-header">
		<h2 class="section-title">
			<i class="fas fa-receipt"></i>
			Custom Deductions
		</h2>
		{#if isEditing}
			<div class="header-actions">
				<button class="btn-cancel" onclick={cancelEdit}>Cancel</button>
				<button class="btn-save" onclick={saveChanges}>Save</button>
			</div>
		{:else}
			<button class="btn-edit" onclick={enterEditMode}>
				<i class="fas fa-pen"></i>
				Edit
			</button>
		{/if}
	</div>

	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="section-content" ondblclick={handleDoubleClick}>
		<div class="section-description">
			<i class="fas fa-info-circle"></i>
			<span>
				Define custom deductions that can be applied to employees in this pay group. These can
				include RRSP contributions, parking fees, charitable donations, or any other recurring
				deductions.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="deductions-editor">
				{#if editDeductions.length > 0}
					<div class="deductions-table">
						<div class="table-header">
							<span class="col-name">Name</span>
							<span class="col-type">Type</span>
							<span class="col-amount">Amount</span>
							<span class="col-employer">Employer Match</span>
							<span class="col-default">Default</span>
							<span class="col-actions">Actions</span>
						</div>
						{#each editDeductions as deduction, index}
							<div class="table-row">
								<span class="col-name">
									<span class="deduction-name">{deduction.name}</span>
									{#if deduction.description}
										<span class="deduction-desc">{deduction.description}</span>
									{/if}
								</span>
								<span class="col-type">
									<span class="type-badge" class:pre-tax={deduction.type === 'pre_tax'}>
										{formatType(deduction.type)}
									</span>
								</span>
								<span class="col-amount">
									{formatCalculation(deduction.calculationType, deduction.amount)}
									{#if deduction.calculationType === 'percentage'}
										<span class="calc-type">of gross</span>
									{/if}
								</span>
								<span class="col-employer">
									{#if deduction.isEmployerContribution && deduction.employerAmount}
										{deduction.calculationType === 'percentage'
											? `${deduction.employerAmount}%`
											: formatCurrency(deduction.employerAmount)}
									{:else}
										—
									{/if}
								</span>
								<span class="col-default">
									{#if deduction.isDefaultEnabled}
										<i class="fas fa-check-circle status-yes"></i>
									{:else}
										<i class="fas fa-minus-circle status-no"></i>
									{/if}
								</span>
								<span class="col-actions">
									<button class="btn-icon" onclick={() => openEditModal(index)} title="Edit">
										<i class="fas fa-pen"></i>
									</button>
									<button
										class="btn-icon btn-delete"
										onclick={() => deleteDeduction(index)}
										title="Delete"
									>
										<i class="fas fa-trash"></i>
									</button>
								</span>
							</div>
						{/each}
					</div>
				{:else}
					<div class="empty-state">
						<i class="fas fa-receipt"></i>
						<p>No custom deductions defined</p>
					</div>
				{/if}

				<button class="btn-add" onclick={openAddModal}>
					<i class="fas fa-plus"></i>
					Add Deduction
				</button>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="deductions-view" title="Double-click to edit">
				{#if payGroup.customDeductions.length > 0}
					<div class="deductions-list">
						{#each payGroup.customDeductions as deduction}
							<div class="deduction-card">
								<div class="deduction-header">
									<span class="deduction-name">{deduction.name}</span>
									<span class="type-badge" class:pre-tax={deduction.type === 'pre_tax'}>
										{formatType(deduction.type)}
									</span>
								</div>
								{#if deduction.description}
									<p class="deduction-description">{deduction.description}</p>
								{/if}
								<div class="deduction-details">
									<div class="detail-row">
										<span class="detail-label">Amount</span>
										<span class="detail-value">
											{formatCalculation(deduction.calculationType, deduction.amount)}
											{#if deduction.calculationType === 'percentage'}
												<span class="calc-note">of gross pay</span>
											{/if}
										</span>
									</div>
									{#if deduction.isEmployerContribution && deduction.employerAmount}
										<div class="detail-row">
											<span class="detail-label">Employer Match</span>
											<span class="detail-value employer">
												{deduction.calculationType === 'percentage'
													? `${deduction.employerAmount}%`
													: formatCurrency(deduction.employerAmount)}
											</span>
										</div>
									{/if}
									<div class="detail-row">
										<span class="detail-label">Default Enabled</span>
										<span class="detail-value">
											{#if deduction.isDefaultEnabled}
												<span class="badge-yes">Yes</span>
											{:else}
												<span class="badge-no">No (opt-in)</span>
											{/if}
										</span>
									</div>
								</div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="empty-state">
						<i class="fas fa-receipt"></i>
						<p>No custom deductions defined for this pay group</p>
						<span class="empty-hint">
							Custom deductions can include RRSP contributions, parking fees, charitable donations,
							and more.
						</span>
					</div>
				{/if}
			</div>

			<p class="edit-hint">
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
	<div class="modal-overlay" onclick={closeModal}>
		<div class="modal" onclick={(e) => e.stopPropagation()}>
			<div class="modal-header">
				<h3>{editingDeductionIndex !== null ? 'Edit' : 'Add'} Deduction</h3>
				<button class="btn-close" onclick={closeModal}>
					<i class="fas fa-times"></i>
				</button>
			</div>

			<div class="modal-body">
				<div class="form-group">
					<label for="deduction-name">Name *</label>
					<input
						type="text"
						id="deduction-name"
						bind:value={modalDeduction.name}
						placeholder="e.g., RRSP Contribution"
					/>
				</div>

				<div class="form-group">
					<label for="deduction-description">Description</label>
					<input
						type="text"
						id="deduction-description"
						bind:value={modalDeduction.description}
						placeholder="Optional description"
					/>
				</div>

				<div class="form-row">
					<div class="form-group">
						<label for="deduction-type">Deduction Type</label>
						<select id="deduction-type" bind:value={modalDeduction.type}>
							<option value="pre_tax">Pre-Tax</option>
							<option value="post_tax">Post-Tax</option>
						</select>
						<p class="field-hint">
							{modalDeduction.type === 'pre_tax'
								? 'Deducted before tax calculations (reduces taxable income)'
								: 'Deducted after tax calculations'}
						</p>
					</div>

					<div class="form-group">
						<label for="calc-type">Calculation Type</label>
						<select id="calc-type" bind:value={modalDeduction.calculationType}>
							<option value="fixed">Fixed Amount</option>
							<option value="percentage">Percentage of Gross</option>
						</select>
					</div>
				</div>

				<div class="form-group">
					<label for="amount">
						Amount *
						{#if modalDeduction.calculationType === 'percentage'}
							(%)
						{/if}
					</label>
					<div class="input-with-prefix">
						<span class="prefix">
							{modalDeduction.calculationType === 'percentage' ? '%' : '$'}
						</span>
						<input
							type="number"
							id="amount"
							bind:value={modalDeduction.amount}
							min="0"
							step={modalDeduction.calculationType === 'percentage' ? '0.5' : '1'}
						/>
					</div>
				</div>

				<div class="form-group">
					<label class="checkbox-label">
						<input type="checkbox" bind:checked={modalDeduction.isEmployerContribution} />
						<span>Employer contributes to this deduction</span>
					</label>
				</div>

				{#if modalDeduction.isEmployerContribution}
					<div class="form-group indented">
						<label for="employer-amount">Employer Contribution Amount</label>
						<div class="input-with-prefix">
							<span class="prefix">
								{modalDeduction.calculationType === 'percentage' ? '%' : '$'}
							</span>
							<input
								type="number"
								id="employer-amount"
								bind:value={modalDeduction.employerAmount}
								min="0"
								step={modalDeduction.calculationType === 'percentage' ? '0.5' : '1'}
							/>
						</div>
					</div>
				{/if}

				<div class="form-group">
					<label class="checkbox-label">
						<input type="checkbox" bind:checked={modalDeduction.isDefaultEnabled} />
						<span>Enabled by default for new employees</span>
					</label>
					<p class="field-hint">
						{modalDeduction.isDefaultEnabled
							? 'New employees will have this deduction applied automatically'
							: 'Employees must opt-in to this deduction'}
					</p>
				</div>
			</div>

			<div class="modal-footer">
				<button class="btn-cancel" onclick={closeModal}>Cancel</button>
				<button class="btn-primary" onclick={saveDeduction} disabled={!isModalValid}>
					{editingDeductionIndex !== null ? 'Save Changes' : 'Add Deduction'}
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.info-section {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		overflow: hidden;
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-surface-50);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.section-title {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.section-title i {
		color: var(--color-info-500);
	}

	.header-actions {
		display: flex;
		gap: var(--spacing-2);
	}

	.btn-edit,
	.btn-cancel,
	.btn-save {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-edit {
		background: transparent;
		color: var(--color-primary-600);
		border: 1px solid var(--color-primary-200);
	}

	.btn-edit:hover {
		background: var(--color-primary-50);
		border-color: var(--color-primary-300);
	}

	.btn-cancel {
		background: transparent;
		color: var(--color-surface-600);
		border: 1px solid var(--color-surface-200);
	}

	.btn-cancel:hover {
		background: var(--color-surface-100);
	}

	.btn-save {
		background: var(--color-primary-500);
		color: white;
		border: none;
	}

	.btn-save:hover {
		background: var(--color-primary-600);
	}

	.section-content {
		padding: var(--spacing-5);
	}

	.section-description {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		margin-bottom: var(--spacing-4);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.section-description i {
		color: var(--color-primary-500);
		margin-top: 2px;
	}

	/* Edit Mode Table */
	.deductions-editor {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.deductions-table {
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		overflow: hidden;
	}

	.table-header {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr 80px 100px;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-100);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-600);
		text-transform: uppercase;
	}

	.table-row {
		display: grid;
		grid-template-columns: 2fr 1fr 1fr 1fr 80px 100px;
		gap: var(--spacing-3);
		padding: var(--spacing-3) var(--spacing-4);
		border-top: 1px solid var(--color-surface-100);
		align-items: center;
	}

	.table-row:hover {
		background: var(--color-surface-50);
	}

	.col-name .deduction-name {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		display: block;
	}

	.col-name .deduction-desc {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.type-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.type-badge.pre-tax {
		background: var(--color-primary-50);
		color: var(--color-primary-700);
	}

	.col-amount .calc-type {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-left: var(--spacing-1);
	}

	.col-employer {
		color: var(--color-success-600);
		font-weight: var(--font-weight-medium);
	}

	.status-yes {
		color: var(--color-success-500);
	}

	.status-no {
		color: var(--color-surface-400);
	}

	.col-actions {
		display: flex;
		gap: var(--spacing-1);
	}

	.btn-icon {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		border: none;
		background: transparent;
		color: var(--color-surface-500);
		border-radius: var(--radius-md);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-icon:hover {
		background: var(--color-surface-100);
		color: var(--color-primary-600);
	}

	.btn-icon.btn-delete:hover {
		background: var(--color-error-50);
		color: var(--color-error-600);
	}

	.btn-add {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-primary-50);
		color: var(--color-primary-600);
		border: 1px dashed var(--color-primary-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add:hover {
		background: var(--color-primary-100);
		border-style: solid;
	}

	/* View Mode */
	.deductions-view {
		cursor: pointer;
	}

	.deductions-list {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
	}

	.deduction-card {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-100);
	}

	.deduction-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		margin-bottom: var(--spacing-2);
	}

	.deduction-card .deduction-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.deduction-description {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: 0 0 var(--spacing-3);
	}

	.deduction-details {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.detail-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.detail-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.detail-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.detail-value.employer {
		color: var(--color-success-600);
	}

	.detail-value .calc-note {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		font-weight: normal;
	}

	.badge-yes {
		color: var(--color-success-600);
	}

	.badge-no {
		color: var(--color-surface-500);
	}

	/* Empty State */
	.empty-state {
		text-align: center;
		padding: var(--spacing-8) var(--spacing-4);
		color: var(--color-surface-500);
	}

	.empty-state i {
		font-size: 32px;
		margin-bottom: var(--spacing-3);
		color: var(--color-surface-300);
	}

	.empty-state p {
		font-size: var(--font-size-body-content);
		margin: 0 0 var(--spacing-2);
	}

	.empty-hint {
		font-size: var(--font-size-auxiliary-text);
	}

	.edit-hint {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-top: var(--spacing-4);
		padding-top: var(--spacing-4);
		border-top: 1px dashed var(--color-surface-200);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-400);
	}

	/* Modal */
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.modal {
		background: white;
		border-radius: var(--radius-xl);
		width: 100%;
		max-width: 500px;
		max-height: 90vh;
		overflow-y: auto;
		box-shadow: var(--shadow-md3-3);
	}

	.modal-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: var(--spacing-4) var(--spacing-5);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-header h3 {
		margin: 0;
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.btn-close {
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		border: none;
		background: transparent;
		color: var(--color-surface-500);
		border-radius: var(--radius-md);
		cursor: pointer;
	}

	.btn-close:hover {
		background: var(--color-surface-100);
	}

	.modal-body {
		padding: var(--spacing-5);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.modal-footer {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-5);
		border-top: 1px solid var(--color-surface-100);
	}

	.btn-primary {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		background: var(--color-primary-500);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-primary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Modal Form */
	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.form-group.indented {
		margin-left: var(--spacing-6);
		padding-left: var(--spacing-4);
		border-left: 2px solid var(--color-primary-100);
	}

	.form-group label:not(.checkbox-label) {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
	}

	.form-group input[type='text'],
	.form-group input[type='number'],
	.form-group select {
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		background: white;
	}

	.form-group input:focus,
	.form-group select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-row {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
	}

	.input-with-prefix {
		display: flex;
		align-items: stretch;
	}

	.input-with-prefix .prefix {
		display: flex;
		align-items: center;
		padding: 0 var(--spacing-3);
		background: var(--color-surface-100);
		border: 1px solid var(--color-surface-200);
		border-right: none;
		border-radius: var(--radius-md) 0 0 var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-500);
	}

	.input-with-prefix input {
		border-radius: 0 var(--radius-md) var(--radius-md) 0;
		flex: 1;
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		cursor: pointer;
	}

	.checkbox-label input[type='checkbox'] {
		width: 18px;
		height: 18px;
		accent-color: var(--color-primary-500);
	}

	.field-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: var(--spacing-1) 0 0;
	}

	@media (max-width: 768px) {
		.table-header,
		.table-row {
			grid-template-columns: 1fr;
			gap: var(--spacing-2);
		}

		.table-header {
			display: none;
		}

		.table-row {
			padding: var(--spacing-4);
		}

		.table-row span::before {
			content: attr(data-label);
			font-weight: var(--font-weight-medium);
			color: var(--color-surface-500);
			margin-right: var(--spacing-2);
		}

		.deductions-list {
			grid-template-columns: 1fr;
		}

		.form-row {
			grid-template-columns: 1fr;
		}

		.section-header {
			flex-direction: column;
			gap: var(--spacing-3);
			align-items: flex-start;
		}

		.header-actions {
			width: 100%;
		}

		.btn-cancel,
		.btn-save {
			flex: 1;
		}
	}
</style>
