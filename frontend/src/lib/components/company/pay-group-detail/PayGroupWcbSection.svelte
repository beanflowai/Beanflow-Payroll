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

<section class="info-section">
	<div class="section-header">
		<h2 class="section-title">
			<i class="fas fa-hard-hat"></i>
			Workers' Compensation (WCB)
		</h2>
		{#if isEditing}
			<div class="header-actions">
				<button class="btn-cancel" onclick={cancelEdit}>Cancel</button>
				<button class="btn-save" onclick={saveChanges} disabled={!isValid}>Save</button>
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
				Workers' Compensation Board (WCB) coverage provides insurance for workplace injuries.
				Employers pay premiums based on their industry classification code and assessment rate.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="wcb-form">
				<div class="toggle-card main-toggle">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={editEnabled} />
						<span class="toggle-content">
							<span class="toggle-title">Enable WCB for this Pay Group</span>
							<span class="toggle-description">
								Calculate and remit WCB premiums for employees in this group
							</span>
						</span>
					</label>
				</div>

				{#if editEnabled}
					<div class="sub-settings">
						<div class="form-row">
							<div class="form-group">
								<label for="industryClassCode">Industry Class Code *</label>
								<input
									type="text"
									id="industryClassCode"
									bind:value={editIndustryClassCode}
									placeholder="e.g., 72300"
									class:error={editIndustryClassCode.length === 0}
								/>
								<p class="field-hint">
									Your WCB industry classification code (contact your provincial WCB)
								</p>
							</div>

							<div class="form-group">
								<label for="industryName">Industry Name</label>
								<input
									type="text"
									id="industryName"
									bind:value={editIndustryName}
									placeholder="e.g., Office Administrative Services"
								/>
								<p class="field-hint">Description of your industry classification</p>
							</div>
						</div>

						<div class="form-row">
							<div class="form-group">
								<label for="assessmentRate">Assessment Rate (per $100) *</label>
								<div class="input-with-prefix">
									<span class="prefix">$</span>
									<input
										type="number"
										id="assessmentRate"
										bind:value={editAssessmentRate}
										min="0"
										step="0.01"
										placeholder="0.00"
										class:error={editAssessmentRate <= 0}
									/>
								</div>
								<p class="field-hint">
									Premium rate per $100 of assessable earnings (check your WCB rate sheet)
								</p>
							</div>

							<div class="form-group">
								<label for="maxEarnings">Maximum Assessable Earnings</label>
								<div class="input-with-prefix">
									<span class="prefix">$</span>
									<input
										type="number"
										id="maxEarnings"
										bind:value={editMaxAssessableEarnings}
										min="0"
										step="1"
										placeholder="Optional"
									/>
								</div>
								<p class="field-hint">
									Annual cap on assessable earnings (set by your province)
								</p>
							</div>
						</div>
					</div>
				{/if}
			</div>

			<div class="info-note">
				<i class="fas fa-map-marker-alt"></i>
				<span>
					<strong>Provincial Variations:</strong> WCB is administered provincially. In Ontario it's
					called WSIB, in BC it's WorkSafeBC, etc. Rates and maximum assessable earnings vary by
					province.
				</span>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="wcb-status" title="Double-click to edit">
				<div class="status-card" class:enabled={payGroup.wcbConfig.enabled}>
					<div class="status-icon">
						{#if payGroup.wcbConfig.enabled}
							<i class="fas fa-shield-alt"></i>
						{:else}
							<i class="fas fa-shield-virus"></i>
						{/if}
					</div>
					<div class="status-content">
						<span class="status-title">WCB Coverage</span>
						<span class="status-value">
							{payGroup.wcbConfig.enabled ? 'Enabled' : 'Not Enabled'}
						</span>
					</div>
				</div>

				{#if payGroup.wcbConfig.enabled}
					<div class="config-details">
						<div class="detail-card industry">
							<div class="detail-header">
								<span class="detail-label">Industry Classification</span>
							</div>
							<div class="detail-body">
								<span class="detail-code">{payGroup.wcbConfig.industryClassCode ?? '—'}</span>
								{#if payGroup.wcbConfig.industryName}
									<span class="detail-name">{payGroup.wcbConfig.industryName}</span>
								{/if}
							</div>
						</div>

						<div class="rate-cards">
							<div class="detail-card">
								<span class="detail-label">Assessment Rate</span>
								<span class="detail-value highlight">
									{formatRate(payGroup.wcbConfig.assessmentRate)}
								</span>
							</div>

							<div class="detail-card">
								<span class="detail-label">Max Assessable Earnings</span>
								<span class="detail-value">
									{payGroup.wcbConfig.maxAssessableEarnings
										? formatCurrency(payGroup.wcbConfig.maxAssessableEarnings)
										: 'Not Set'}
								</span>
							</div>
						</div>

						<div class="estimate-note">
							<i class="fas fa-calculator"></i>
							<span>
								Estimated annual premium for an employee earning $50,000:
								<strong>
									{formatCurrency((50000 / 100) * payGroup.wcbConfig.assessmentRate)}
								</strong>
							</span>
						</div>
					</div>
				{:else}
					<div class="disabled-note">
						<i class="fas fa-exclamation-triangle"></i>
						<div>
							<p>
								WCB coverage is not enabled for this pay group. Employees will not have WCB
								premiums calculated.
							</p>
							<p class="note-secondary">
								Note: Most employers are required by law to register with their provincial WCB.
								Exemptions may apply to certain industries or ownership structures.
							</p>
						</div>
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
		color: var(--color-warning-500);
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

	.btn-save:hover:not(:disabled) {
		background: var(--color-primary-600);
	}

	.btn-save:disabled {
		opacity: 0.5;
		cursor: not-allowed;
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
	.wcb-form {
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
		background: var(--color-warning-50);
		border-color: var(--color-warning-100);
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

	.sub-settings {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
		padding-left: var(--spacing-4);
		border-left: 3px solid var(--color-warning-200);
	}

	.form-row {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.form-group label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
	}

	.form-group input {
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		background: white;
		transition: var(--transition-fast);
	}

	.form-group input:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-group input.error {
		border-color: var(--color-error-400);
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

	.field-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: var(--spacing-1) 0 0;
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
	.wcb-status {
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
		background: var(--color-warning-50);
		border-color: var(--color-warning-100);
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
		background: var(--color-warning-100);
	}

	.status-icon i {
		font-size: 24px;
		color: var(--color-surface-400);
	}

	.status-card.enabled .status-icon i {
		color: var(--color-warning-600);
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

	.config-details {
		margin-top: var(--spacing-4);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.detail-card {
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.detail-card.industry {
		background: var(--color-primary-50);
	}

	.detail-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
	}

	.detail-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.detail-body {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.detail-code {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-bold);
		color: var(--color-primary-700);
		font-family: monospace;
	}

	.detail-name {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.rate-cards {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
	}

	.detail-value {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.detail-value.highlight {
		color: var(--color-warning-700);
	}

	.estimate-note {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.estimate-note i {
		color: var(--color-primary-500);
	}

	.disabled-note {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
		margin-top: var(--spacing-4);
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
		border: 1px dashed var(--color-surface-200);
	}

	.disabled-note i {
		color: var(--color-warning-500);
		font-size: 20px;
	}

	.disabled-note p {
		margin: 0;
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.disabled-note .note-secondary {
		margin-top: var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
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
		.form-row,
		.rate-cards {
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
