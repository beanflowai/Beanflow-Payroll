<script lang="ts">
	// PayGroupOvertimeSection - Overtime & Bank Time policy with section-level edit mode
	import type { PayGroup, BankTimeRate, BankTimeExpiryMonths } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
		onUpdate: (payGroup: PayGroup) => void;
	}

	let { payGroup, onUpdate }: Props = $props();

	// Edit mode state
	let isEditing = $state(false);

	// Form state
	let editBankTimeEnabled = $state(false);
	let editBankTimeRate = $state<BankTimeRate>(1.5);
	let editBankTimeExpiryMonths = $state<BankTimeExpiryMonths>(3);
	let editRequireWrittenAgreement = $state(true);

	// Enter edit mode
	function enterEditMode() {
		editBankTimeEnabled = payGroup.overtimePolicy.bankTimeEnabled;
		editBankTimeRate = payGroup.overtimePolicy.bankTimeRate;
		editBankTimeExpiryMonths = payGroup.overtimePolicy.bankTimeExpiryMonths;
		editRequireWrittenAgreement = payGroup.overtimePolicy.requireWrittenAgreement;
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
			overtimePolicy: {
				bankTimeEnabled: editBankTimeEnabled,
				bankTimeRate: editBankTimeRate,
				bankTimeExpiryMonths: editBankTimeExpiryMonths,
				requireWrittenAgreement: editRequireWrittenAgreement
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

	// Format rate for display
	function formatRate(rate: BankTimeRate): string {
		return rate === 1.0 ? 'Straight Time (1:1)' : 'Time and a Half (1.5:1)';
	}

	// Format expiry for display
	function formatExpiry(months: BankTimeExpiryMonths): string {
		return `${months} Month${months > 1 ? 's' : ''}`;
	}
</script>

<section class="info-section">
	<div class="section-header">
		<h2 class="section-title">
			<i class="fas fa-clock"></i>
			Overtime & Bank Time
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
				Bank Time (Time Off In Lieu / TOIL) allows employees to bank overtime hours instead of
				receiving immediate overtime pay. Banked time can be used later as paid time off.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="overtime-form">
				<div class="toggle-card main-toggle">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={editBankTimeEnabled} />
						<span class="toggle-content">
							<span class="toggle-title">Enable Bank Time</span>
							<span class="toggle-description">
								Allow employees to bank overtime hours as time off instead of pay
							</span>
						</span>
					</label>
				</div>

				{#if editBankTimeEnabled}
					<div class="sub-settings">
						<div class="form-group">
							<label for="bankTimeRate">Bank Time Rate</label>
							<select id="bankTimeRate" bind:value={editBankTimeRate}>
								<option value={1.0}>Straight Time (1:1)</option>
								<option value={1.5}>Time and a Half (1.5:1)</option>
							</select>
							<p class="field-hint">
								{editBankTimeRate === 1.5
									? 'Each overtime hour worked earns 1.5 hours of banked time'
									: 'Each overtime hour worked earns 1 hour of banked time'}
							</p>
						</div>

						<div class="form-group">
							<label for="expiryMonths">Bank Time Expiry</label>
							<select id="expiryMonths" bind:value={editBankTimeExpiryMonths}>
								<option value={3}>3 Months</option>
								<option value={6}>6 Months</option>
								<option value={12}>12 Months</option>
							</select>
							<p class="field-hint">
								Banked time must be used within this period or it will be paid out
							</p>
						</div>

						<div class="toggle-card">
							<label class="toggle-label">
								<input type="checkbox" bind:checked={editRequireWrittenAgreement} />
								<span class="toggle-content">
									<span class="toggle-title">Require Written Agreement</span>
									<span class="toggle-description">
										Employee must sign a bank time agreement before banking overtime
									</span>
								</span>
							</label>
						</div>
					</div>
				{/if}
			</div>

			<div class="info-note">
				<i class="fas fa-balance-scale"></i>
				<span>
					<strong>Provincial Compliance:</strong> Bank time rules vary by province. In Ontario,
					employees must agree in writing to bank overtime, and time must be taken within 3 months
					unless a longer period is agreed upon.
				</span>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="overtime-status" title="Double-click to edit">
				<div class="status-card" class:enabled={payGroup.overtimePolicy.bankTimeEnabled}>
					<div class="status-icon">
						{#if payGroup.overtimePolicy.bankTimeEnabled}
							<i class="fas fa-check-circle"></i>
						{:else}
							<i class="fas fa-times-circle"></i>
						{/if}
					</div>
					<div class="status-content">
						<span class="status-title">Bank Time</span>
						<span class="status-value">
							{payGroup.overtimePolicy.bankTimeEnabled ? 'Enabled' : 'Disabled'}
						</span>
					</div>
				</div>

				{#if payGroup.overtimePolicy.bankTimeEnabled}
					<div class="policy-details">
						<div class="detail-item">
							<span class="detail-label">Rate</span>
							<span class="detail-value">{formatRate(payGroup.overtimePolicy.bankTimeRate)}</span>
						</div>
						<div class="detail-item">
							<span class="detail-label">Expiry Period</span>
							<span class="detail-value"
								>{formatExpiry(payGroup.overtimePolicy.bankTimeExpiryMonths)}</span
							>
						</div>
						<div class="detail-item">
							<span class="detail-label">Written Agreement</span>
							<span class="detail-value">
								{#if payGroup.overtimePolicy.requireWrittenAgreement}
									<span class="badge required">Required</span>
								{:else}
									<span class="badge optional">Not Required</span>
								{/if}
							</span>
						</div>
					</div>
				{:else}
					<div class="disabled-note">
						<p>
							Employees will receive overtime pay for all overtime hours worked. Bank time is not
							available as an option.
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
		color: var(--color-primary-500);
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
	.overtime-form {
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
		background: var(--color-primary-50);
		border-color: var(--color-primary-100);
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
		border-left: 3px solid var(--color-primary-200);
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

	.form-group select {
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		background: white;
		transition: var(--transition-fast);
	}

	.form-group select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
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
	.overtime-status {
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

	.policy-details {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-4);
		margin-top: var(--spacing-4);
	}

	.detail-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		padding: var(--spacing-3);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
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

	.badge {
		display: inline-flex;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
	}

	.badge.required {
		background: var(--color-primary-50);
		color: var(--color-primary-700);
	}

	.badge.optional {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.disabled-note {
		margin-top: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-md);
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
		.policy-details {
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
