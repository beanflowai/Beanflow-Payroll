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
			minimumFractionDigits: 0,
			maximumFractionDigits: 0
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

<section class="info-section">
	<div class="section-header">
		<h2 class="section-title">
			<i class="fas fa-heartbeat"></i>
			Group Benefits
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
				Configure default benefit deductions and employer contributions for employees in this pay
				group. Individual employees can have benefits adjusted on their profiles.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="benefits-form">
				<div class="toggle-card main-toggle">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={editEnabled} />
						<span class="toggle-content">
							<span class="toggle-title">Enable Group Benefits</span>
							<span class="toggle-description">
								Apply benefit deductions to employees in this pay group
							</span>
						</span>
					</label>
				</div>

				{#if editEnabled}
					<div class="benefits-list">
						<!-- Health -->
						<div class="benefit-card" class:disabled={!editHealth.enabled}>
							<div class="benefit-header">
								<label class="benefit-toggle">
									<input type="checkbox" bind:checked={editHealth.enabled} />
									<i class="fas fa-heart"></i>
									<span>Health</span>
								</label>
							</div>
							{#if editHealth.enabled}
								<div class="benefit-fields">
									<div class="field-row">
										<div class="form-field">
											<label>Employee Deduction</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editHealth.employeeDeduction} min="0" step="1" />
											</div>
										</div>
										<div class="form-field">
											<label>Employer Contribution</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editHealth.employerContribution} min="0" step="1" />
											</div>
										</div>
									</div>
									<label class="taxable-toggle">
										<input type="checkbox" bind:checked={editHealth.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Dental -->
						<div class="benefit-card" class:disabled={!editDental.enabled}>
							<div class="benefit-header">
								<label class="benefit-toggle">
									<input type="checkbox" bind:checked={editDental.enabled} />
									<i class="fas fa-tooth"></i>
									<span>Dental</span>
								</label>
							</div>
							{#if editDental.enabled}
								<div class="benefit-fields">
									<div class="field-row">
										<div class="form-field">
											<label>Employee Deduction</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editDental.employeeDeduction} min="0" step="1" />
											</div>
										</div>
										<div class="form-field">
											<label>Employer Contribution</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editDental.employerContribution} min="0" step="1" />
											</div>
										</div>
									</div>
									<label class="taxable-toggle">
										<input type="checkbox" bind:checked={editDental.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Vision -->
						<div class="benefit-card" class:disabled={!editVision.enabled}>
							<div class="benefit-header">
								<label class="benefit-toggle">
									<input type="checkbox" bind:checked={editVision.enabled} />
									<i class="fas fa-eye"></i>
									<span>Vision</span>
								</label>
							</div>
							{#if editVision.enabled}
								<div class="benefit-fields">
									<div class="field-row">
										<div class="form-field">
											<label>Employee Deduction</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editVision.employeeDeduction} min="0" step="1" />
											</div>
										</div>
										<div class="form-field">
											<label>Employer Contribution</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editVision.employerContribution} min="0" step="1" />
											</div>
										</div>
									</div>
									<label class="taxable-toggle">
										<input type="checkbox" bind:checked={editVision.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Life Insurance -->
						<div class="benefit-card" class:disabled={!editLifeInsurance.enabled}>
							<div class="benefit-header">
								<label class="benefit-toggle">
									<input type="checkbox" bind:checked={editLifeInsurance.enabled} />
									<i class="fas fa-shield-alt"></i>
									<span>Life Insurance</span>
								</label>
							</div>
							{#if editLifeInsurance.enabled}
								<div class="benefit-fields">
									<div class="field-row">
										<div class="form-field">
											<label>Employee Deduction</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editLifeInsurance.employeeDeduction} min="0" step="1" />
											</div>
										</div>
										<div class="form-field">
											<label>Employer Contribution</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editLifeInsurance.employerContribution} min="0" step="1" />
											</div>
										</div>
									</div>
									<div class="field-row">
										<div class="form-field">
											<label>Coverage Amount</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editLifeInsurance.coverageAmount} min="0" step="1000" />
											</div>
										</div>
										<div class="form-field">
											<label>Coverage Multiplier</label>
											<select bind:value={editLifeInsurance.coverageMultiplier}>
												<option value={undefined}>Fixed Amount</option>
												<option value={1}>1x Salary</option>
												<option value={2}>2x Salary</option>
												<option value={3}>3x Salary</option>
											</select>
										</div>
									</div>
									<label class="taxable-toggle">
										<input type="checkbox" bind:checked={editLifeInsurance.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>

						<!-- Disability -->
						<div class="benefit-card" class:disabled={!editDisability.enabled}>
							<div class="benefit-header">
								<label class="benefit-toggle">
									<input type="checkbox" bind:checked={editDisability.enabled} />
									<i class="fas fa-wheelchair"></i>
									<span>Disability</span>
								</label>
							</div>
							{#if editDisability.enabled}
								<div class="benefit-fields">
									<div class="field-row">
										<div class="form-field">
											<label>Employee Deduction</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editDisability.employeeDeduction} min="0" step="1" />
											</div>
										</div>
										<div class="form-field">
											<label>Employer Contribution</label>
											<div class="input-with-prefix">
												<span class="prefix">$</span>
												<input type="number" bind:value={editDisability.employerContribution} min="0" step="1" />
											</div>
										</div>
									</div>
									<label class="taxable-toggle">
										<input type="checkbox" bind:checked={editDisability.isTaxable} />
										<span>Employer portion is taxable benefit</span>
									</label>
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>

			<div class="info-note">
				<i class="fas fa-calculator"></i>
				<span>
					<strong>Taxable Benefits:</strong> Employer-paid portions of certain benefits (e.g., group
					life insurance over $10,000) are taxable benefits that must be reported on T4s.
				</span>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="benefits-status" title="Double-click to edit">
				<div class="status-card" class:enabled={payGroup.groupBenefits.enabled}>
					<div class="status-icon">
						{#if payGroup.groupBenefits.enabled}
							<i class="fas fa-heartbeat"></i>
						{:else}
							<i class="fas fa-heart-broken"></i>
						{/if}
					</div>
					<div class="status-content">
						<span class="status-title">Group Benefits</span>
						<span class="status-value">
							{payGroup.groupBenefits.enabled ? `${enabledBenefitsCount()} Active` : 'Not Enabled'}
						</span>
					</div>
				</div>

				{#if payGroup.groupBenefits.enabled}
					<div class="benefits-grid">
						{#each benefitTypes as benefit}
							{@const config = benefit.key === 'lifeInsurance'
								? payGroup.groupBenefits.lifeInsurance
								: payGroup.groupBenefits[benefit.key]}
							<div class="benefit-view-card" class:enabled={config.enabled}>
								<div class="benefit-view-header">
									<i class="fas {benefit.icon}"></i>
									<span class="benefit-name">{benefit.label}</span>
									<span class="benefit-status-badge" class:active={config.enabled}>
										{config.enabled ? 'Active' : 'Inactive'}
									</span>
								</div>
								{#if config.enabled}
									<div class="benefit-amounts">
										<div class="amount-item">
											<span class="amount-label">Employee</span>
											<span class="amount-value">{formatCurrency(config.employeeDeduction)}/pay</span>
										</div>
										<div class="amount-item">
											<span class="amount-label">Employer</span>
											<span class="amount-value">{formatCurrency(config.employerContribution)}/pay</span>
										</div>
									</div>
									{#if config.isTaxable}
										<span class="taxable-badge">Taxable Benefit</span>
									{/if}
								{/if}
							</div>
						{/each}
					</div>

					<div class="totals-row">
						<div class="total-item">
							<span class="total-label">Total Employee Deduction</span>
							<span class="total-value">{formatCurrency(totalEmployeeDeduction())}/pay period</span>
						</div>
						<div class="total-item">
							<span class="total-label">Total Employer Contribution</span>
							<span class="total-value">{formatCurrency(totalEmployerContribution())}/pay period</span>
						</div>
					</div>
				{:else}
					<div class="disabled-note">
						<p>
							Group benefits are not enabled for this pay group. Employees will not have benefit
							deductions applied.
						</p>
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
		color: var(--color-success-500);
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

	/* Edit Mode */
	.benefits-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.toggle-card {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-100);
	}

	.toggle-card.main-toggle {
		background: var(--color-success-50);
		border-color: var(--color-success-100);
	}

	.toggle-label {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
		cursor: pointer;
	}

	.toggle-label input[type='checkbox'] {
		width: 20px;
		height: 20px;
		margin-top: 2px;
		accent-color: var(--color-primary-500);
		flex-shrink: 0;
	}

	.toggle-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.toggle-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.toggle-description {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.benefits-list {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.benefit-card {
		padding: var(--spacing-4);
		background: white;
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-200);
		transition: var(--transition-fast);
	}

	.benefit-card.disabled {
		background: var(--color-surface-50);
	}

	.benefit-header {
		margin-bottom: var(--spacing-3);
	}

	.benefit-toggle {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		cursor: pointer;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.benefit-toggle input[type='checkbox'] {
		width: 18px;
		height: 18px;
		accent-color: var(--color-primary-500);
	}

	.benefit-toggle i {
		color: var(--color-primary-500);
	}

	.benefit-fields {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
		padding-left: var(--spacing-6);
		border-left: 2px solid var(--color-primary-100);
	}

	.field-row {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-3);
	}

	.form-field {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.form-field label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.input-with-prefix {
		display: flex;
		align-items: stretch;
	}

	.input-with-prefix .prefix {
		display: flex;
		align-items: center;
		padding: 0 var(--spacing-2);
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
		min-width: 0;
	}

	.form-field input,
	.form-field select {
		padding: var(--spacing-2) var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		background: white;
	}

	.form-field input:focus,
	.form-field select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 2px var(--color-primary-100);
	}

	.taxable-toggle {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		cursor: pointer;
	}

	.taxable-toggle input[type='checkbox'] {
		width: 16px;
		height: 16px;
		accent-color: var(--color-warning-500);
	}

	.info-note {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		margin-top: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-info-50);
		border: 1px solid var(--color-info-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-info-800);
	}

	.info-note i {
		color: var(--color-info-500);
		margin-top: 2px;
	}

	/* View Mode */
	.benefits-status {
		cursor: pointer;
	}

	.status-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-100);
	}

	.status-card.enabled {
		background: var(--color-success-50);
		border-color: var(--color-success-100);
	}

	.status-icon {
		width: 48px;
		height: 48px;
		border-radius: var(--radius-full);
		background: var(--color-surface-200);
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.status-card.enabled .status-icon {
		background: var(--color-success-100);
	}

	.status-icon i {
		font-size: 24px;
		color: var(--color-surface-400);
	}

	.status-card.enabled .status-icon i {
		color: var(--color-success-600);
	}

	.status-content {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.status-title {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.status-value {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.benefits-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-3);
		margin-top: var(--spacing-4);
	}

	.benefit-view-card {
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		border: 1px solid var(--color-surface-100);
	}

	.benefit-view-card.enabled {
		background: white;
		border-color: var(--color-success-200);
	}

	.benefit-view-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-2);
	}

	.benefit-view-header i {
		color: var(--color-surface-400);
	}

	.benefit-view-card.enabled .benefit-view-header i {
		color: var(--color-success-500);
	}

	.benefit-name {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		flex: 1;
	}

	.benefit-status-badge {
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: 10px;
		text-transform: uppercase;
		font-weight: var(--font-weight-semibold);
		background: var(--color-surface-200);
		color: var(--color-surface-500);
	}

	.benefit-status-badge.active {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.benefit-amounts {
		display: flex;
		gap: var(--spacing-4);
		margin-bottom: var(--spacing-2);
	}

	.amount-item {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.amount-label {
		font-size: 10px;
		text-transform: uppercase;
		color: var(--color-surface-400);
	}

	.amount-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.taxable-badge {
		display: inline-block;
		padding: 2px var(--spacing-2);
		background: var(--color-warning-100);
		color: var(--color-warning-700);
		border-radius: var(--radius-sm);
		font-size: 10px;
		font-weight: var(--font-weight-medium);
	}

	.totals-row {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
		margin-top: var(--spacing-4);
		padding-top: var(--spacing-4);
		border-top: 1px solid var(--color-surface-200);
	}

	.total-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		padding: var(--spacing-3);
		background: var(--color-primary-50);
		border-radius: var(--radius-md);
	}

	.total-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.total-value {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-bold);
		color: var(--color-primary-700);
	}

	.disabled-note {
		margin-top: var(--spacing-4);
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		border: 1px dashed var(--color-surface-200);
	}

	.disabled-note p {
		margin: 0;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
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

	@media (max-width: 768px) {
		.field-row,
		.benefits-grid,
		.totals-row {
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
