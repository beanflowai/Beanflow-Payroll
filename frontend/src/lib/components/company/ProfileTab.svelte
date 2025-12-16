<script lang="ts">
	// ProfileTab - Company profile settings (Tab 1)
	import {
		REMITTER_TYPE_INFO,
		PROVINCES,
		calculateNextDueDate,
		formatDueDateWithDays
	} from '$lib/types/company';
	import type { RemitterType, CompanyProfile } from '$lib/types/company';
	import type { Province } from '$lib/types/employee';
	import {
		getOrCreateDefaultCompany,
		createCompany,
		updateCompany,
		type CompanyCreateInput
	} from '$lib/services/companyService';

	interface Props {
		onSave?: () => void;
		onCancel?: () => void;
	}

	let { onSave, onCancel }: Props = $props();

	// Company state
	let companyId = $state<string | null>(null);
	let isNewCompany = $state(false);

	// Form state
	let companyName = $state('');
	let businessNumber = $state('');
	let payrollAccountNumber = $state('');
	let province = $state<Province>('ON');
	let remitterType = $state<RemitterType>('regular');
	let autoCalculate = $state(true);
	let sendPaystubs = $state(false);

	// UI state
	let showRemitterInfo = $state(false);
	let isSaving = $state(false);
	let isLoading = $state(true);
	let error = $state<string | null>(null);

	// Load company data on mount
	$effect(() => {
		loadCompany();
	});

	async function loadCompany() {
		isLoading = true;
		error = null;
		try {
			const result = await getOrCreateDefaultCompany();
			if (result.error) {
				error = result.error;
				return;
			}
			if (result.data) {
				// Existing company - populate form
				populateForm(result.data);
				companyId = result.data.id;
				isNewCompany = false;
			} else {
				// No company yet - show empty form for creation
				isNewCompany = true;
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to load company';
		} finally {
			isLoading = false;
		}
	}

	function populateForm(company: CompanyProfile) {
		companyName = company.companyName;
		businessNumber = company.businessNumber;
		payrollAccountNumber = company.payrollAccountNumber;
		province = company.province;
		remitterType = company.remitterType;
		autoCalculate = company.autoCalculateDeductions;
		sendPaystubs = company.sendPaystubEmails;
	}

	// Computed due date info
	let dueDateInfo = $derived(() => {
		const nextDue = calculateNextDueDate(remitterType);
		return formatDueDateWithDays(nextDue);
	});

	async function handleSave() {
		// Validation
		if (!companyName.trim()) {
			error = 'Company name is required';
			return;
		}
		if (!businessNumber.trim() || businessNumber.length !== 9) {
			error = 'Business number must be 9 digits';
			return;
		}
		if (!payrollAccountNumber.trim() || payrollAccountNumber.length !== 15) {
			error = 'Payroll account number must be 15 characters';
			return;
		}

		isSaving = true;
		error = null;

		try {
			if (isNewCompany) {
				// Create new company
				const input: CompanyCreateInput = {
					company_name: companyName.trim(),
					business_number: businessNumber.trim(),
					payroll_account_number: payrollAccountNumber.trim(),
					province,
					remitter_type: remitterType,
					auto_calculate_deductions: autoCalculate,
					send_paystub_emails: sendPaystubs
				};
				const result = await createCompany(input);
				if (result.error) {
					error = result.error;
					return;
				}
				if (result.data) {
					companyId = result.data.id;
					isNewCompany = false;
				}
			} else if (companyId) {
				// Update existing company
				const result = await updateCompany(companyId, {
					company_name: companyName.trim(),
					business_number: businessNumber.trim(),
					payroll_account_number: payrollAccountNumber.trim(),
					province,
					remitter_type: remitterType,
					auto_calculate_deductions: autoCalculate,
					send_paystub_emails: sendPaystubs
				});
				if (result.error) {
					error = result.error;
					return;
				}
			}
			onSave?.();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save company';
		} finally {
			isSaving = false;
		}
	}
</script>

<div class="profile-tab">
	<!-- Error Message -->
	{#if error}
		<div class="error-banner">
			<i class="fas fa-exclamation-circle"></i>
			<span>{error}</span>
			<button class="error-dismiss" onclick={() => error = null}>
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	<!-- Loading State -->
	{#if isLoading}
		<div class="loading-container">
			<div class="loading-spinner"></div>
			<p>Loading company profile...</p>
		</div>
	{:else}
		<!-- New Company Notice -->
		{#if isNewCompany}
			<div class="info-banner">
				<i class="fas fa-info-circle"></i>
				<span>No company profile found. Fill in the details below to create your company.</span>
			</div>
		{/if}

		<!-- Company Information -->
		<section class="settings-section">
		<div class="section-header">
			<div class="section-icon">
				<i class="fas fa-building"></i>
			</div>
			<div class="section-info">
				<h2 class="section-title">Company Information</h2>
				<p class="section-description">Basic company details for payroll processing</p>
			</div>
		</div>

		<div class="settings-card">
			<div class="form-grid">
				<div class="form-group">
					<label class="form-label" for="company-name">Company Name *</label>
					<input
						type="text"
						id="company-name"
						class="form-input"
						bind:value={companyName}
						placeholder="Enter company name"
					/>
					<span class="form-hint">Legal name of your business</span>
				</div>

				<div class="form-group">
					<label class="form-label" for="business-number">Business Number (BN) *</label>
					<input
						type="text"
						id="business-number"
						class="form-input"
						bind:value={businessNumber}
						placeholder="9 digits"
					/>
					<span class="form-hint">Your 9-digit CRA business number</span>
				</div>

				<div class="form-group">
					<label class="form-label" for="payroll-account">Payroll Account Number *</label>
					<input
						type="text"
						id="payroll-account"
						class="form-input"
						bind:value={payrollAccountNumber}
						placeholder="123456789RP0001"
					/>
					<span class="form-hint">15-character CRA payroll account (e.g., 123456789RP0001)</span>
				</div>

				<div class="form-group">
					<label class="form-label" for="province">Province/Territory *</label>
					<select id="province" class="form-select" bind:value={province}>
						{#each PROVINCES as prov (prov.code)}
							<option value={prov.code}>{prov.name}</option>
						{/each}
					</select>
					<span class="form-hint">Company's primary location</span>
				</div>
			</div>
		</div>
	</section>

	<!-- CRA Remittance Configuration -->
	<section class="settings-section">
		<div class="section-header">
			<div class="section-icon remittance">
				<i class="fas fa-landmark"></i>
			</div>
			<div class="section-info">
				<h2 class="section-title">CRA Remittance</h2>
				<p class="section-description">Configure how you remit payroll deductions to CRA</p>
			</div>
		</div>

		<div class="settings-card">
			<div class="form-group" style="margin-bottom: var(--spacing-4);">
				<label class="form-label" for="remitter-type">Remitter Type *</label>
				<select id="remitter-type" class="form-select remitter-select" bind:value={remitterType}>
					{#each Object.entries(REMITTER_TYPE_INFO) as [value, info] (value)}
						<option {value}>{info.label}</option>
					{/each}
				</select>
				<span class="form-hint">Based on your Average Monthly Withholding Amount (AMWA)</span>
			</div>

			<!-- Remitter Type Info Box -->
			<button
				type="button"
				class="info-toggle"
				onclick={() => (showRemitterInfo = !showRemitterInfo)}
			>
				<i class="fas fa-info-circle"></i>
				<span>What is Remitter Type?</span>
				<i class="fas fa-chevron-{showRemitterInfo ? 'up' : 'down'} chevron"></i>
			</button>

			{#if showRemitterInfo}
				<div class="info-box">
					<p class="info-intro">
						Your remitter type determines how often you must send payroll deductions (CPP, EI,
						Income Tax) to the CRA.
					</p>
					<div class="remitter-options">
						{#each Object.entries(REMITTER_TYPE_INFO) as [value, info] (value)}
							<div class="remitter-option" class:active={remitterType === value}>
								<div class="option-header">
									<span class="option-label">{info.label}</span>
									<span class="option-amwa">{info.amwaRange}</span>
								</div>
								<p class="option-desc">{info.description}</p>
							</div>
						{/each}
					</div>
					<p class="info-note">
						<i class="fas fa-clipboard-list"></i>
						Check your CRA My Business Account or the letter CRA sent you to confirm your remitter
						type.
					</p>
				</div>
			{/if}

			<!-- Current Status -->
			<div class="status-section">
				<h3 class="status-title">Current Status</h3>
				<div class="status-cards">
					<div class="status-card">
						<span class="status-label">Frequency</span>
						<span class="status-value">{REMITTER_TYPE_INFO[remitterType].frequency}</span>
						<span class="status-subtext">
							{REMITTER_TYPE_INFO[remitterType].periodsPerYear} times/year
						</span>
					</div>
					<div class="status-card">
						<span class="status-label">Next Due Date</span>
						<span class="status-value">{dueDateInfo().formatted}</span>
						<span class="status-subtext" class:warning={dueDateInfo().daysRemaining <= 7}>
							{#if dueDateInfo().isOverdue}
								<i class="fas fa-exclamation-circle"></i>
								{Math.abs(dueDateInfo().daysRemaining)} days overdue
							{:else}
								<i class="fas fa-clock"></i>
								in {dueDateInfo().daysRemaining} days
							{/if}
						</span>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Preferences -->
	<section class="settings-section">
		<div class="section-header">
			<div class="section-icon preferences">
				<i class="fas fa-cog"></i>
			</div>
			<div class="section-info">
				<h2 class="section-title">Preferences</h2>
				<p class="section-description">Payroll processing preferences</p>
			</div>
		</div>

		<div class="settings-card">
			<div class="setting-toggle">
				<div class="toggle-info">
					<span class="toggle-label">Auto-calculate deductions</span>
					<span class="toggle-description">
						Automatically calculate CPP, EI, and income tax based on current CRA tables
					</span>
				</div>
				<label class="toggle-switch">
					<input type="checkbox" bind:checked={autoCalculate} />
					<span class="toggle-slider"></span>
				</label>
			</div>

			<div class="setting-toggle">
				<div class="toggle-info">
					<span class="toggle-label">Send paystub emails</span>
					<span class="toggle-description">
						Automatically email digital paystubs to employees after each payroll run is approved
					</span>
				</div>
				<label class="toggle-switch">
					<input type="checkbox" bind:checked={sendPaystubs} />
					<span class="toggle-slider"></span>
				</label>
			</div>
		</div>
	</section>

	<!-- Save Button -->
	<div class="actions-bar">
		<button class="btn-secondary" onclick={onCancel} disabled={isSaving}>Cancel</button>
		<button class="btn-primary" onclick={handleSave} disabled={isSaving}>
			{#if isSaving}
				<i class="fas fa-spinner fa-spin"></i>
				<span>Saving...</span>
			{:else}
				<i class="fas fa-save"></i>
				<span>Save Changes</span>
			{/if}
		</button>
	</div>
	{/if}
</div>

<style>
	.profile-tab {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-8);
	}

	/* Error Banner */
	.error-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-danger-50, #fef2f2);
		border: 1px solid var(--color-danger-200, #fecaca);
		border-radius: var(--radius-lg);
		color: var(--color-danger-700, #b91c1c);
	}

	.error-banner i:first-child {
		font-size: 1.25rem;
	}

	.error-banner span {
		flex: 1;
	}

	.error-dismiss {
		background: none;
		border: none;
		color: var(--color-danger-500, #ef4444);
		cursor: pointer;
		padding: var(--spacing-1);
		opacity: 0.7;
	}

	.error-dismiss:hover {
		opacity: 1;
	}

	/* Info Banner */
	.info-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-primary-50, #eff6ff);
		border: 1px solid var(--color-primary-200, #bfdbfe);
		border-radius: var(--radius-lg);
		color: var(--color-primary-700, #1d4ed8);
	}

	.info-banner i {
		font-size: 1.25rem;
	}

	/* Loading State */
	.loading-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--spacing-12) var(--spacing-6);
		gap: var(--spacing-4);
	}

	.loading-spinner {
		width: 40px;
		height: 40px;
		border: 3px solid var(--color-surface-200);
		border-top-color: var(--color-primary-500, #3b82f6);
		border-radius: 50%;
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.loading-container p {
		color: var(--color-surface-500);
		margin: 0;
	}

	/* Section */
	.settings-section {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-4);
	}

	.section-header {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-4);
	}

	.section-icon {
		width: 40px;
		height: 40px;
		border-radius: var(--radius-lg);
		background: var(--color-primary-100);
		color: var(--color-primary-600);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 18px;
		flex-shrink: 0;
	}

	.section-icon.remittance {
		background: var(--color-secondary-100);
		color: var(--color-secondary-600);
	}

	.section-icon.preferences {
		background: var(--color-tertiary-100);
		color: var(--color-tertiary-600);
	}

	.section-info {
		flex: 1;
	}

	.section-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-1);
	}

	.section-description {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0;
	}

	/* Settings Card */
	.settings-card {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		padding: var(--spacing-6);
	}

	/* Form */
	.form-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
		gap: var(--spacing-5);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.form-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.form-input,
	.form-select {
		padding: var(--spacing-3) var(--spacing-4);
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-800);
		transition: var(--transition-fast);
	}

	.form-input:focus,
	.form-select:focus {
		outline: none;
		border-color: var(--color-primary-400);
		box-shadow: 0 0 0 3px var(--color-primary-100);
	}

	.form-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	/* Remitter Type Section */
	.remitter-select {
		max-width: 400px;
	}

	.info-toggle {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) 0;
		background: none;
		border: none;
		color: var(--color-primary-600);
		font-size: var(--font-size-auxiliary-text);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.info-toggle:hover {
		color: var(--color-primary-700);
	}

	.info-toggle .chevron {
		margin-left: auto;
		font-size: 12px;
	}

	.info-box {
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		margin-bottom: var(--spacing-4);
	}

	.info-intro {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-4);
	}

	.remitter-options {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
		margin-bottom: var(--spacing-4);
	}

	.remitter-option {
		background: white;
		border: 1px solid var(--color-surface-200);
		border-radius: var(--radius-md);
		padding: var(--spacing-3);
		transition: var(--transition-fast);
	}

	.remitter-option.active {
		border-color: var(--color-primary-400);
		background: var(--color-primary-50);
	}

	.option-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--spacing-1);
	}

	.option-label {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.option-amwa {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.option-desc {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
	}

	.info-note {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		margin: 0;
	}

	.info-note i {
		margin-top: 2px;
		color: var(--color-primary-500);
	}

	/* Status Section */
	.status-section {
		border-top: 1px solid var(--color-surface-100);
		padding-top: var(--spacing-4);
		margin-top: var(--spacing-4);
	}

	.status-title {
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-500);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 var(--spacing-3);
	}

	.status-cards {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
	}

	.status-card {
		background: var(--color-surface-50);
		border-radius: var(--radius-lg);
		padding: var(--spacing-4);
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
	}

	.status-label {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.status-value {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
	}

	.status-subtext {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	.status-subtext.warning {
		color: var(--color-warning-600);
	}

	/* Toggle */
	.setting-toggle {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) 0;
		border-bottom: 1px solid var(--color-surface-100);
	}

	.setting-toggle:last-child {
		border-bottom: none;
	}

	.toggle-info {
		flex: 1;
	}

	.toggle-label {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
		margin-bottom: var(--spacing-1);
	}

	.toggle-description {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-600);
	}

	.toggle-switch {
		position: relative;
		display: inline-block;
		width: 48px;
		height: 28px;
		flex-shrink: 0;
	}

	.toggle-switch input {
		opacity: 0;
		width: 0;
		height: 0;
	}

	.toggle-slider {
		position: absolute;
		cursor: pointer;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: var(--color-surface-300);
		transition: var(--transition-fast);
		border-radius: var(--radius-full);
	}

	.toggle-slider:before {
		position: absolute;
		content: '';
		height: 20px;
		width: 20px;
		left: 4px;
		bottom: 4px;
		background-color: white;
		transition: var(--transition-fast);
		border-radius: 50%;
	}

	.toggle-switch input:checked + .toggle-slider {
		background-color: var(--color-primary-500);
	}

	.toggle-switch input:checked + .toggle-slider:before {
		transform: translateX(20px);
	}

	/* Buttons */
	.btn-primary,
	.btn-secondary {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-primary {
		background: var(--gradient-primary);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-primary:hover:not(:disabled) {
		opacity: 0.9;
		transform: translateY(-1px);
	}

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	.btn-secondary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Actions Bar */
	.actions-bar {
		display: flex;
		justify-content: flex-end;
		gap: var(--spacing-3);
		padding-top: var(--spacing-6);
		border-top: 1px solid var(--color-surface-200);
	}

	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}

		.status-cards {
			grid-template-columns: 1fr;
		}

		.actions-bar {
			flex-direction: column;
		}

		.actions-bar button {
			width: 100%;
		}
	}
</style>
