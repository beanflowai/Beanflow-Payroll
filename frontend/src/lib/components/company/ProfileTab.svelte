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
		createCompany,
		updateCompany,
		uploadCompanyLogo,
		type CompanyCreateInput
	} from '$lib/services/companyService';
	import { companyState, refreshCompanies } from '$lib/stores/company.svelte';

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
	let logoUrl = $state<string | null>(null);

	// UI state
	let showRemitterInfo = $state(false);
	let isSaving = $state(false);
	let isUploadingLogo = $state(false);
	let error = $state<string | null>(null);
	let logoInputRef = $state<HTMLInputElement | null>(null);

	// Derive isLoading from companyState
	const isLoading = $derived(companyState.isLoading);

	// Load company data when current company changes
	$effect(() => {
		const company = companyState.currentCompany;
		if (company) {
			// Existing company - populate form
			populateForm(company);
			companyId = company.id;
			isNewCompany = false;
		} else {
			// No company yet - show empty form for creation
			isNewCompany = true;
		}
	});

	function populateForm(company: CompanyProfile) {
		companyName = company.companyName;
		businessNumber = company.businessNumber;
		payrollAccountNumber = company.payrollAccountNumber;
		province = company.province;
		remitterType = company.remitterType;
		autoCalculate = company.autoCalculateDeductions;
		sendPaystubs = company.sendPaystubEmails;
		logoUrl = company.logoUrl ?? null;
	}

	// Logo upload handler
	async function handleLogoUpload(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		isUploadingLogo = true;
		error = null;

		const result = await uploadCompanyLogo(file, companyId);

		if (result.error) {
			error = result.error;
		} else if (result.publicUrl) {
			logoUrl = result.publicUrl;
		}

		isUploadingLogo = false;
	}

	function removeLogo() {
		logoUrl = null;
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
					send_paystub_emails: sendPaystubs,
					logo_url: logoUrl
				});
				if (result.error) {
					error = result.error;
					return;
				}
			}
			// Refresh companies list to update CompanySwitcher
			await refreshCompanies();
			onSave?.();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save company';
		} finally {
			isSaving = false;
		}
	}
</script>

<div class="flex flex-col gap-8">
	<!-- Error Message -->
	{#if error}
		<div class="flex items-center gap-3 p-4 bg-error-50 border border-error-200 rounded-lg text-error-700">
			<i class="fas fa-exclamation-circle text-xl"></i>
			<span class="flex-1">{error}</span>
			<button class="bg-transparent border-none text-error-500 cursor-pointer p-1 opacity-70 hover:opacity-100" onclick={() => error = null} aria-label="Dismiss error">
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	<!-- Loading State -->
	{#if isLoading}
		<div class="flex flex-col items-center justify-center py-12 px-6 gap-4">
			<div class="w-10 h-10 border-[3px] border-surface-200 border-t-primary-500 rounded-full animate-spin"></div>
			<p class="text-surface-500 m-0">Loading company profile...</p>
		</div>
	{:else}
		<!-- New Company Notice -->
		{#if isNewCompany}
			<div class="flex items-center gap-3 p-4 bg-primary-50 border border-primary-200 rounded-lg text-primary-700">
				<i class="fas fa-info-circle text-xl"></i>
				<span>No company profile found. Fill in the details below to create your company.</span>
			</div>
		{/if}

		<!-- Company Information -->
		<section class="flex flex-col gap-4">
			<div class="flex items-start gap-4">
				<div class="w-10 h-10 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-lg shrink-0">
					<i class="fas fa-building"></i>
				</div>
				<div class="flex-1">
					<h2 class="text-title-medium font-semibold text-surface-800 m-0 mb-1">Company Information</h2>
					<p class="text-body-content text-surface-600 m-0">Basic company details for payroll processing</p>
				</div>
			</div>

			<div class="bg-white rounded-xl shadow-md3-1 p-6">
				<!-- Company Logo -->
				<div class="flex flex-col gap-3 mb-6 pb-6 border-b border-surface-100">
					<span class="text-body-content font-medium text-surface-700">Company Logo</span>
					<div class="flex items-start gap-4">
						<!-- Logo Preview -->
						<div class="w-24 h-24 rounded-lg border-2 border-dashed border-surface-200 bg-surface-50 flex items-center justify-center overflow-hidden shrink-0">
							{#if logoUrl}
								<img src={logoUrl} alt="Company logo" class="w-full h-full object-contain" />
							{:else}
								<i class="fas fa-building text-3xl text-surface-300"></i>
							{/if}
						</div>
						<!-- Upload Controls -->
						<div class="flex flex-col gap-2">
							<p class="text-auxiliary-text text-surface-600 m-0">
								Upload your company logo for paystubs. Recommended: PNG or JPG, max 2MB.
							</p>
							<div class="flex items-center gap-2">
								<input
									type="file"
									accept="image/*"
									class="hidden"
									onchange={handleLogoUpload}
									bind:this={logoInputRef}
								/>
								<button
									type="button"
									class="inline-flex items-center gap-2 py-2 px-4 border border-surface-200 rounded-lg text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-60 disabled:cursor-not-allowed"
									onclick={() => logoInputRef?.click()}
									disabled={isUploadingLogo}
								>
									{#if isUploadingLogo}
										<i class="fas fa-spinner fa-spin"></i>
										<span>Uploading...</span>
									{:else}
										<i class="fas fa-upload"></i>
										<span>{logoUrl ? 'Change Logo' : 'Upload Logo'}</span>
									{/if}
								</button>
								{#if logoUrl}
									<button
										type="button"
										class="inline-flex items-center gap-2 py-2 px-4 border border-error-200 rounded-lg text-auxiliary-text font-medium cursor-pointer transition-[150ms] bg-white text-error-600 hover:bg-error-50"
										onclick={removeLogo}
									>
										<i class="fas fa-trash"></i>
										<span>Remove</span>
									</button>
								{/if}
							</div>
						</div>
					</div>
				</div>

				<div class="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-5">
					<div class="flex flex-col gap-2">
						<label class="text-body-content font-medium text-surface-700" for="company-name">Company Name *</label>
						<input
							type="text"
							id="company-name"
							class="py-3 px-4 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
							bind:value={companyName}
							placeholder="Enter company name"
						/>
						<span class="text-auxiliary-text text-surface-500">Legal name of your business</span>
					</div>

					<div class="flex flex-col gap-2">
						<label class="text-body-content font-medium text-surface-700" for="business-number">Business Number (BN) *</label>
						<input
							type="text"
							id="business-number"
							class="py-3 px-4 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
							bind:value={businessNumber}
							placeholder="9 digits"
						/>
						<span class="text-auxiliary-text text-surface-500">Your 9-digit CRA business number</span>
					</div>

					<div class="flex flex-col gap-2">
						<label class="text-body-content font-medium text-surface-700" for="payroll-account">Payroll Account Number *</label>
						<input
							type="text"
							id="payroll-account"
							class="py-3 px-4 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100"
							bind:value={payrollAccountNumber}
							placeholder="123456789RP0001"
						/>
						<span class="text-auxiliary-text text-surface-500">15-character CRA payroll account (e.g., 123456789RP0001)</span>
					</div>

					<div class="flex flex-col gap-2">
						<label class="text-body-content font-medium text-surface-700" for="province">Province/Territory *</label>
						<select id="province" class="py-3 px-4 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100" bind:value={province}>
							{#each PROVINCES as prov (prov.code)}
								<option value={prov.code}>{prov.name}</option>
							{/each}
						</select>
						<span class="text-auxiliary-text text-surface-500">Company's primary location</span>
					</div>
				</div>
			</div>
		</section>

		<!-- CRA Remittance Configuration -->
		<section class="flex flex-col gap-4">
			<div class="flex items-start gap-4">
				<div class="w-10 h-10 rounded-lg bg-secondary-100 text-secondary-600 flex items-center justify-center text-lg shrink-0">
					<i class="fas fa-landmark"></i>
				</div>
				<div class="flex-1">
					<h2 class="text-title-medium font-semibold text-surface-800 m-0 mb-1">CRA Remittance</h2>
					<p class="text-body-content text-surface-600 m-0">Configure how you remit payroll deductions to CRA</p>
				</div>
			</div>

			<div class="bg-white rounded-xl shadow-md3-1 p-6">
				<div class="flex flex-col gap-2 mb-4">
					<label class="text-body-content font-medium text-surface-700" for="remitter-type">Remitter Type *</label>
					<select id="remitter-type" class="py-3 px-4 bg-white border border-surface-200 rounded-lg text-body-content text-surface-800 transition-[150ms] focus:outline-none focus:border-primary-400 focus:ring-[3px] focus:ring-primary-100 max-w-[400px]" bind:value={remitterType}>
						{#each Object.entries(REMITTER_TYPE_INFO) as [value, info] (value)}
							<option {value}>{info.label}</option>
						{/each}
					</select>
					<span class="text-auxiliary-text text-surface-500">Based on your Average Monthly Withholding Amount (AMWA)</span>
				</div>

				<!-- Remitter Type Info Box -->
				<button
					type="button"
					class="flex items-center gap-2 py-3 bg-transparent border-none text-primary-600 text-auxiliary-text cursor-pointer transition-[150ms] hover:text-primary-700"
					onclick={() => (showRemitterInfo = !showRemitterInfo)}
				>
					<i class="fas fa-info-circle"></i>
					<span>What is Remitter Type?</span>
					<i class="fas fa-chevron-{showRemitterInfo ? 'up' : 'down'} ml-auto text-xs"></i>
				</button>

				{#if showRemitterInfo}
					<div class="bg-surface-50 rounded-lg p-4 mb-4">
						<p class="text-body-content text-surface-700 m-0 mb-4">
							Your remitter type determines how often you must send payroll deductions (CPP, EI,
							Income Tax) to the CRA.
						</p>
						<div class="flex flex-col gap-2 mb-4">
							{#each Object.entries(REMITTER_TYPE_INFO) as [value, info] (value)}
								<div class="bg-white border rounded-md p-3 transition-[150ms] {remitterType === value ? 'border-primary-400 bg-primary-50' : 'border-surface-200'}">
									<div class="flex justify-between items-center mb-1">
										<span class="text-body-content font-medium text-surface-800">{info.label}</span>
										<span class="text-auxiliary-text text-surface-500">{info.amwaRange}</span>
									</div>
									<p class="text-auxiliary-text text-surface-600 m-0">{info.description}</p>
								</div>
							{/each}
						</div>
						<p class="flex items-start gap-2 text-auxiliary-text text-surface-600 m-0">
							<i class="fas fa-clipboard-list mt-0.5 text-primary-500"></i>
							Check your CRA My Business Account or the letter CRA sent you to confirm your remitter
							type.
						</p>
					</div>
				{/if}

				<!-- Current Status -->
				<div class="border-t border-surface-100 pt-4 mt-4">
					<h3 class="text-auxiliary-text font-medium text-surface-500 uppercase tracking-wider m-0 mb-3">Current Status</h3>
					<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
						<div class="bg-surface-50 rounded-lg p-4 flex flex-col gap-1">
							<span class="text-auxiliary-text text-surface-500">Frequency</span>
							<span class="text-title-medium font-semibold text-surface-800">{REMITTER_TYPE_INFO[remitterType].frequency}</span>
							<span class="text-auxiliary-text text-surface-600">
								{REMITTER_TYPE_INFO[remitterType].periodsPerYear} times/year
							</span>
						</div>
						<div class="bg-surface-50 rounded-lg p-4 flex flex-col gap-1">
							<span class="text-auxiliary-text text-surface-500">Next Due Date</span>
							<span class="text-title-medium font-semibold text-surface-800">{dueDateInfo().formatted}</span>
							<span class="text-auxiliary-text flex items-center gap-1 {dueDateInfo().daysRemaining <= 7 ? 'text-warning-600' : 'text-surface-600'}">
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
		<section class="flex flex-col gap-4">
			<div class="flex items-start gap-4">
				<div class="w-10 h-10 rounded-lg bg-tertiary-100 text-tertiary-600 flex items-center justify-center text-lg shrink-0">
					<i class="fas fa-cog"></i>
				</div>
				<div class="flex-1">
					<h2 class="text-title-medium font-semibold text-surface-800 m-0 mb-1">Preferences</h2>
					<p class="text-body-content text-surface-600 m-0">Payroll processing preferences</p>
				</div>
			</div>

			<div class="bg-white rounded-xl shadow-md3-1 p-6">
				<div class="flex items-center justify-between py-4 border-b border-surface-100">
					<div class="flex-1">
						<span id="auto-calc-label" class="block text-body-content font-medium text-surface-800 mb-1">Auto-calculate deductions</span>
						<span class="text-auxiliary-text text-surface-600">
							Automatically calculate CPP, EI, and income tax based on current CRA tables
						</span>
					</div>
					<span class="relative inline-block w-12 h-7 shrink-0">
						<input type="checkbox" class="opacity-0 w-0 h-0" bind:checked={autoCalculate} aria-labelledby="auto-calc-label" />
						<span class="absolute cursor-pointer inset-0 bg-surface-300 transition-[150ms] rounded-full before:absolute before:content-[''] before:h-5 before:w-5 before:left-1 before:bottom-1 before:bg-white before:transition-[150ms] before:rounded-full {autoCalculate ? 'bg-primary-500 before:translate-x-5' : ''}"></span>
					</span>
				</div>

				<div class="flex items-center justify-between py-4">
					<div class="flex-1">
						<span id="paystub-label" class="block text-body-content font-medium text-surface-800 mb-1">Send paystub emails</span>
						<span class="text-auxiliary-text text-surface-600">
							Automatically email digital paystubs to employees after each payroll run is approved
						</span>
					</div>
					<span class="relative inline-block w-12 h-7 shrink-0">
						<input type="checkbox" class="opacity-0 w-0 h-0" bind:checked={sendPaystubs} aria-labelledby="paystub-label" />
						<span class="absolute cursor-pointer inset-0 bg-surface-300 transition-[150ms] rounded-full before:absolute before:content-[''] before:h-5 before:w-5 before:left-1 before:bottom-1 before:bg-white before:transition-[150ms] before:rounded-full {sendPaystubs ? 'bg-primary-500 before:translate-x-5' : ''}"></span>
					</span>
				</div>
			</div>
		</section>

		<!-- Save Button -->
		<div class="flex justify-end gap-3 pt-6 border-t border-surface-200 max-sm:flex-col">
			<button class="inline-flex items-center justify-center gap-2 py-3 px-5 border border-surface-200 rounded-lg text-body-content font-medium cursor-pointer transition-[150ms] bg-white text-surface-700 hover:bg-surface-50 hover:border-surface-300 disabled:opacity-60 disabled:cursor-not-allowed max-sm:w-full" onclick={onCancel} disabled={isSaving}>Cancel</button>
			<button class="inline-flex items-center justify-center gap-2 py-3 px-5 border-none rounded-lg text-body-content font-medium cursor-pointer transition-[150ms] bg-gradient-to-br from-primary-600 to-secondary-600 text-white shadow-md3-1 hover:opacity-90 hover:-translate-y-px disabled:opacity-60 disabled:cursor-not-allowed max-sm:w-full" onclick={handleSave} disabled={isSaving}>
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
