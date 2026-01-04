<script lang="ts">
	// PayGroupBasicInfoSection - Basic info display/edit with section-level edit mode
	import { untrack } from 'svelte';
	import type {
		PayGroup,
		PayFrequency,
		EmploymentType,
		PeriodStartDay,
		TaxCalculationMethod
	} from '$lib/types/pay-group';
	import {
		PAY_FREQUENCY_INFO,
		EMPLOYMENT_TYPE_INFO,
		PERIOD_START_DAY_OPTIONS,
		TAX_CALCULATION_METHOD_INFO,
		calculatePayDate
	} from '$lib/types/pay-group';
	import { formatLongDate } from '$lib/utils/dateUtils';

	interface Props {
		payGroup: PayGroup;
		companyProvince?: string;
		onUpdate: (payGroup: PayGroup) => void;
		startInEditMode?: boolean;
	}

	let { payGroup, companyProvince = 'SK', onUpdate, startInEditMode = false }: Props = $props();

	// Extract initial values for edit mode (form snapshot pattern)
	const initialEditValues = (() => {
		const pg = payGroup;
		const editMode = startInEditMode;
		return {
			isEditing: editMode,
			name: editMode ? pg.name : '',
			description: editMode ? (pg.description ?? '') : '',
			payFrequency: (editMode ? pg.payFrequency : 'bi_weekly') as PayFrequency,
			employmentType: (editMode ? pg.employmentType : 'full_time') as EmploymentType,
			nextPeriodEnd: editMode ? pg.nextPeriodEnd : '',
			periodStartDay: (editMode ? pg.periodStartDay : 'monday') as PeriodStartDay,
			leaveEnabled: editMode ? pg.leaveEnabled : true,
			taxCalculationMethod: (editMode
				? pg.taxCalculationMethod
				: 'annualization') as TaxCalculationMethod
		};
	})();

	// Edit mode state - start in edit mode if requested
	let isEditing = $state(initialEditValues.isEditing);

	// Form state (only used during editing)
	let editName = $state(initialEditValues.name);
	let editDescription = $state(initialEditValues.description);
	let editPayFrequency = $state<PayFrequency>(initialEditValues.payFrequency);
	let editEmploymentType = $state<EmploymentType>(initialEditValues.employmentType);
	let editNextPeriodEnd = $state(initialEditValues.nextPeriodEnd);
	let editPeriodStartDay = $state<PeriodStartDay>(initialEditValues.periodStartDay);
	let editLeaveEnabled = $state(initialEditValues.leaveEnabled);
	let editTaxCalculationMethod = $state<TaxCalculationMethod>(
		initialEditValues.taxCalculationMethod
	);

	// Enter edit mode
	function enterEditMode() {
		editName = payGroup.name;
		editDescription = payGroup.description ?? '';
		editPayFrequency = payGroup.payFrequency;
		editEmploymentType = payGroup.employmentType;
		editNextPeriodEnd = payGroup.nextPeriodEnd;
		editPeriodStartDay = payGroup.periodStartDay;
		editLeaveEnabled = payGroup.leaveEnabled;
		editTaxCalculationMethod = payGroup.taxCalculationMethod;
		isEditing = true;
	}

	// Computed pay date (auto-calculated from period end based on company province)
	const computedPayDate = $derived(
		editNextPeriodEnd ? calculatePayDate(editNextPeriodEnd, companyProvince) : ''
	);

	// Display pay date for view mode
	const displayPayDate = $derived(
		payGroup.nextPeriodEnd ? calculatePayDate(payGroup.nextPeriodEnd, companyProvince) : ''
	);

	// Cancel edit mode
	function cancelEdit() {
		isEditing = false;
	}

	// Save changes
	function saveChanges() {
		const updated: PayGroup = {
			...payGroup,
			name: editName.trim(),
			description: editDescription.trim() || undefined,
			payFrequency: editPayFrequency,
			employmentType: editEmploymentType,
			nextPeriodEnd: editNextPeriodEnd,
			periodStartDay: editPeriodStartDay,
			leaveEnabled: editLeaveEnabled,
			taxCalculationMethod: editTaxCalculationMethod,
			updatedAt: new Date().toISOString()
		};
		onUpdate(updated);
		isEditing = false;
	}

	// Handle double-click on field to enter edit mode
	function handleDoubleClick() {
		if (!isEditing) {
			enterEditMode();
		}
	}

	// Validation
	const isValid = $derived(editName.trim().length > 0 && editNextPeriodEnd.length > 0);

	// When startInEditMode is true, sync changes back to parent in real-time
	// This is needed for the "new" page where the parent has a separate save button
	// Use untrack to read payGroup without creating a dependency loop
	$effect(() => {
		if (startInEditMode && isEditing) {
			// Track these edit fields
			const name = editName;
			const desc = editDescription;
			const freq = editPayFrequency;
			const empType = editEmploymentType;
			const nextPeriodEnd = editNextPeriodEnd;
			const startDay = editPeriodStartDay;
			const leave = editLeaveEnabled;
			const taxMethod = editTaxCalculationMethod;

			// Read payGroup without tracking to avoid loop
			untrack(() => {
				const updated: PayGroup = {
					...payGroup,
					name: name.trim(),
					description: desc.trim() || undefined,
					payFrequency: freq,
					employmentType: empType,
					nextPeriodEnd: nextPeriodEnd,
					periodStartDay: startDay,
					leaveEnabled: leave,
					taxCalculationMethod: taxMethod
				};
				onUpdate(updated);
			});
		}
	});
</script>

<section class="info-section">
	<div class="section-header">
		<h2 class="section-title">
			<i class="fas fa-info-circle"></i>
			Basic Information
		</h2>
		{#if !startInEditMode}
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
		{/if}
	</div>

	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="section-content" ondblclick={handleDoubleClick}>
		{#if isEditing}
			<!-- Edit Mode -->
			<div class="form-grid">
				<div class="form-group">
					<label for="name">Name *</label>
					<input
						type="text"
						id="name"
						bind:value={editName}
						placeholder="Pay group name"
						class:error={editName.trim().length === 0}
					/>
				</div>

				<div class="form-group">
					<label for="description">Description</label>
					<input
						type="text"
						id="description"
						bind:value={editDescription}
						placeholder="Optional description"
					/>
				</div>

				<div class="form-group">
					<label for="payFrequency">Pay Frequency *</label>
					<select id="payFrequency" bind:value={editPayFrequency}>
						{#each Object.entries(PAY_FREQUENCY_INFO) as [value, info] (value)}
							<option {value}>{info.label}</option>
						{/each}
					</select>
				</div>

				<div class="form-group">
					<label for="employmentType">Employment Type *</label>
					<select id="employmentType" bind:value={editEmploymentType}>
						{#each Object.entries(EMPLOYMENT_TYPE_INFO) as [value, info] (value)}
							<option {value}>{info.label}</option>
						{/each}
					</select>
				</div>

				<div class="form-group">
					<label for="nextPeriodEnd">Next Period End *</label>
					<input type="date" id="nextPeriodEnd" bind:value={editNextPeriodEnd} />
				</div>

				<div class="form-group">
					<label for="payDate">Pay Date (auto-calculated)</label>
					<input
						type="text"
						id="payDate"
						value={computedPayDate ? formatLongDate(computedPayDate) : '—'}
						readonly
						class="readonly-field"
					/>
					<p class="field-hint">Saskatchewan law: pay within 6 days of period end</p>
				</div>

				<div class="form-group">
					<label for="periodStartDay">Period Start *</label>
					<select id="periodStartDay" bind:value={editPeriodStartDay}>
						{#each PERIOD_START_DAY_OPTIONS[editPayFrequency] as option (option.value)}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
				</div>

				<div class="form-group checkbox-group">
					<label class="checkbox-label">
						<input type="checkbox" bind:checked={editLeaveEnabled} />
						<span class="checkbox-text">Leave Tracking Enabled</span>
					</label>
					<p class="field-hint">Track vacation and sick leave for employees in this group</p>
				</div>

				<!-- Tax Calculation Method -->
				<div class="form-group tax-method-group">
					<span class="form-label">Tax Calculation Method</span>
					<div class="tax-method-options">
						{#each Object.entries(TAX_CALCULATION_METHOD_INFO) as [value, info] (value)}
							<label
								class="tax-method-option"
								class:selected={editTaxCalculationMethod === value}
								class:disabled={info.disabled}
							>
								<input
									type="radio"
									name="taxCalculationMethod"
									{value}
									checked={editTaxCalculationMethod === value}
									disabled={info.disabled}
									onchange={() => {
										if (!info.disabled) {
											editTaxCalculationMethod = value as TaxCalculationMethod;
										}
									}}
								/>
								<div class="tax-method-content">
									<div class="tax-method-header">
										<span class="tax-method-label">{info.label}</span>
										{#if info.badge}
											<span class="tax-method-badge">{info.badge}</span>
										{/if}
									</div>
									<p class="tax-method-description">{info.description}</p>
								</div>
							</label>
						{/each}
					</div>
				</div>
			</div>
		{:else}
			<!-- View Mode -->
			<div class="info-grid" title="Double-click to edit">
				<div class="info-item">
					<span class="info-label">Name</span>
					<span class="info-value">{payGroup.name}</span>
				</div>

				<div class="info-item">
					<span class="info-label">Description</span>
					<span class="info-value">{payGroup.description || '—'}</span>
				</div>

				<div class="info-item">
					<span class="info-label">Pay Frequency</span>
					<span class="info-value">{PAY_FREQUENCY_INFO[payGroup.payFrequency].label}</span>
				</div>

				<div class="info-item">
					<span class="info-label">Employment Type</span>
					<span class="info-value">{EMPLOYMENT_TYPE_INFO[payGroup.employmentType].label}</span>
				</div>

				<div class="info-item">
					<span class="info-label">Next Period End</span>
					<span class="info-value">{formatLongDate(payGroup.nextPeriodEnd)}</span>
				</div>

				<div class="info-item">
					<span class="info-label">Pay Date</span>
					<span class="info-value auto-calculated">
						{displayPayDate ? formatLongDate(displayPayDate) : '—'}
						<span class="auto-badge">auto</span>
					</span>
				</div>

				<div class="info-item">
					<span class="info-label">Period Start</span>
					<span class="info-value">
						{PERIOD_START_DAY_OPTIONS[payGroup.payFrequency].find(
							(o) => o.value === payGroup.periodStartDay
						)?.label ?? payGroup.periodStartDay}
					</span>
				</div>

				<div class="info-item">
					<span class="info-label">Leave Tracking</span>
					<span class="info-value">
						{#if payGroup.leaveEnabled}
							<span class="badge enabled">
								<i class="fas fa-check"></i>
								Enabled
							</span>
						{:else}
							<span class="badge disabled">
								<i class="fas fa-times"></i>
								Disabled
							</span>
						{/if}
					</span>
				</div>

				<div class="info-item tax-method-view">
					<span class="info-label">Tax Calculation Method</span>
					<span class="info-value">
						{#if TAX_CALCULATION_METHOD_INFO[payGroup.taxCalculationMethod]}
							{TAX_CALCULATION_METHOD_INFO[payGroup.taxCalculationMethod].label}
						{:else}
							Annualization (Option 1)
						{/if}
					</span>
				</div>
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

	/* View Mode Grid */
	.info-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
		cursor: pointer;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.info-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.info-value {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
	}

	.badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
	}

	.badge.enabled {
		background: var(--color-success-50);
		color: var(--color-success-700);
	}

	.badge.disabled {
		background: var(--color-surface-100);
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

	/* Edit Mode Form */
	.form-grid {
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

	.form-group input[type='text'],
	.form-group input[type='date'],
	.form-group select {
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		background: white;
		transition: var(--transition-fast);
	}

	.form-group input:focus,
	.form-group select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-group input.error {
		border-color: var(--color-error-400);
	}

	.form-group input.readonly-field {
		background: var(--color-surface-50);
		color: var(--color-surface-600);
		cursor: not-allowed;
	}

	.auto-calculated {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.auto-badge {
		padding: 2px 6px;
		background: var(--color-primary-100);
		color: var(--color-primary-700);
		font-size: 10px;
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-full);
		text-transform: uppercase;
	}

	.checkbox-group {
		grid-column: span 2;
	}

	.checkbox-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		cursor: pointer;
	}

	.checkbox-label input[type='checkbox'] {
		width: 18px;
		height: 18px;
		accent-color: var(--color-primary-500);
	}

	.checkbox-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
	}

	.field-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin: var(--spacing-1) 0 0;
	}

	/* Tax Calculation Method Styles */
	.tax-method-group {
		grid-column: span 2;
	}

	.form-label {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-600);
		margin-bottom: var(--spacing-2);
	}

	.tax-method-options {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-3);
	}

	.tax-method-option {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.tax-method-option:hover:not(.disabled) {
		border-color: var(--color-surface-300);
		background: var(--color-surface-50);
	}

	.tax-method-option.selected {
		border-color: var(--color-primary-500);
		background: var(--color-primary-50);
	}

	.tax-method-option.disabled {
		opacity: 0.6;
		cursor: not-allowed;
		background: var(--color-surface-50);
	}

	.tax-method-option input[type='radio'] {
		margin-top: var(--spacing-1);
		accent-color: var(--color-primary-500);
	}

	.tax-method-content {
		flex: 1;
	}

	.tax-method-header {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-1);
	}

	.tax-method-label {
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.tax-method-badge {
		padding: var(--spacing-1) var(--spacing-2);
		background: var(--color-warning-100);
		color: var(--color-warning-700);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-full);
	}

	.tax-method-description {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
		line-height: 1.4;
	}

	.tax-method-view {
		grid-column: span 2;
	}

	@media (max-width: 640px) {
		.info-grid,
		.form-grid {
			grid-template-columns: 1fr;
		}

		.checkbox-group,
		.tax-method-group,
		.tax-method-view {
			grid-column: span 1;
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
