<script lang="ts">
	// PayGroupStatutorySection - CPP/EI statutory defaults with section-level edit mode
	import type { PayGroup } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
		onUpdate: (payGroup: PayGroup) => void;
	}

	let { payGroup, onUpdate }: Props = $props();

	// Edit mode state
	let isEditing = $state(false);

	// Form state
	let editCppExempt = $state(false);
	let editCpp2Exempt = $state(false);
	let editEiExempt = $state(false);

	// Enter edit mode
	function enterEditMode() {
		editCppExempt = payGroup.statutoryDefaults.cppExemptByDefault;
		editCpp2Exempt = payGroup.statutoryDefaults.cpp2ExemptByDefault;
		editEiExempt = payGroup.statutoryDefaults.eiExemptByDefault;
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
			statutoryDefaults: {
				cppExemptByDefault: editCppExempt,
				cpp2ExemptByDefault: editCpp2Exempt,
				eiExemptByDefault: editEiExempt
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

	// Determine if any exemption is set
	const hasExemptions = $derived(
		payGroup.statutoryDefaults.cppExemptByDefault ||
			payGroup.statutoryDefaults.cpp2ExemptByDefault ||
			payGroup.statutoryDefaults.eiExemptByDefault
	);
</script>

<section class="info-section">
	<div class="section-header">
		<h2 class="section-title">
			<i class="fas fa-landmark"></i>
			Statutory Defaults
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
				These settings define the default statutory deduction behavior for new employees added to
				this pay group. Individual employees can override these defaults.
			</span>
		</div>

		{#if isEditing}
			<!-- Edit Mode -->
			<div class="statutory-grid">
				<div class="statutory-item">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={editCppExempt} />
						<span class="toggle-content">
							<span class="toggle-title">CPP Exempt by Default</span>
							<span class="toggle-description">
								New employees in this group will be exempt from Canada Pension Plan contributions
							</span>
						</span>
					</label>
				</div>

				<div class="statutory-item">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={editCpp2Exempt} />
						<span class="toggle-content">
							<span class="toggle-title">CPP2 Exempt by Default</span>
							<span class="toggle-description">
								New employees will be exempt from enhanced CPP (CPP2) contributions
							</span>
						</span>
					</label>
				</div>

				<div class="statutory-item">
					<label class="toggle-label">
						<input type="checkbox" bind:checked={editEiExempt} />
						<span class="toggle-content">
							<span class="toggle-title">EI Exempt by Default</span>
							<span class="toggle-description">
								New employees will be exempt from Employment Insurance premiums
							</span>
						</span>
					</label>
				</div>
			</div>

			<div class="warning-note">
				<i class="fas fa-exclamation-triangle"></i>
				<span>
					<strong>Important:</strong> Exemptions should only be applied when legally appropriate
					(e.g., controlling shareholders, certain family members). Incorrect exemptions may result
					in CRA penalties.
				</span>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="statutory-grid view-mode" title="Double-click to edit">
				<div class="statutory-card">
					<div class="card-header">
						<span class="card-title">CPP</span>
						<span class="status-badge" class:exempt={payGroup.statutoryDefaults.cppExemptByDefault}>
							{payGroup.statutoryDefaults.cppExemptByDefault ? 'Exempt' : 'Standard'}
						</span>
					</div>
					<p class="card-description">Canada Pension Plan contributions</p>
				</div>

				<div class="statutory-card">
					<div class="card-header">
						<span class="card-title">CPP2</span>
						<span
							class="status-badge"
							class:exempt={payGroup.statutoryDefaults.cpp2ExemptByDefault}
						>
							{payGroup.statutoryDefaults.cpp2ExemptByDefault ? 'Exempt' : 'Standard'}
						</span>
					</div>
					<p class="card-description">Enhanced CPP (second tier) contributions</p>
				</div>

				<div class="statutory-card">
					<div class="card-header">
						<span class="card-title">EI</span>
						<span class="status-badge" class:exempt={payGroup.statutoryDefaults.eiExemptByDefault}>
							{payGroup.statutoryDefaults.eiExemptByDefault ? 'Exempt' : 'Standard'}
						</span>
					</div>
					<p class="card-description">Employment Insurance premiums</p>
				</div>
			</div>

			{#if hasExemptions}
				<div class="info-note">
					<i class="fas fa-info-circle"></i>
					<span>
						Employees added to this group will have the above exemptions applied by default.
						Individual overrides can be set on each employee's profile.
					</span>
				</div>
			{/if}

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

	/* View Mode Cards */
	.statutory-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: var(--spacing-4);
	}

	.statutory-grid.view-mode {
		cursor: pointer;
	}

	.statutory-card {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-100);
	}

	.card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-2);
	}

	.card-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.status-badge {
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		background: var(--color-success-50);
		color: var(--color-success-700);
	}

	.status-badge.exempt {
		background: var(--color-warning-50);
		color: var(--color-warning-700);
	}

	.card-description {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: 0;
	}

	/* Edit Mode */
	.statutory-item {
		padding: var(--spacing-4);
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		border: 1px solid var(--color-surface-100);
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

	.warning-note {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		margin-top: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-warning-800);
	}

	.warning-note i {
		color: var(--color-warning-500);
		margin-top: 2px;
	}

	.info-note {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		margin-top: var(--spacing-4);
		padding: var(--spacing-3) var(--spacing-4);
		background: var(--color-primary-50);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-primary-800);
	}

	.info-note i {
		color: var(--color-primary-500);
		margin-top: 2px;
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
		.statutory-grid {
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
