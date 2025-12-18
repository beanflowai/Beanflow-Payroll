<script lang="ts">
	import type { Employee, Province, VacationPayoutMethod, VacationRate, EmployeeCreateInput, EmployeeUpdateInput } from '$lib/types/employee';
	import type { PayGroup } from '$lib/types/pay-group';
	import {
		PROVINCE_LABELS,
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS,
		VACATION_RATE_LABELS,
		FEDERAL_BPA_2025,
		PROVINCIAL_BPA_2025,
		calculateYearsOfService,
		suggestVacationRate
	} from '$lib/types/employee';
	import { createEmployee, updateEmployee } from '$lib/services/employeeService';

	interface Props {
		employee?: Employee | null;
		payGroups: PayGroup[];
		mode: 'create' | 'edit';
		onSuccess: (employee: Employee) => void;
		onCancel: () => void;
	}

	let { employee = null, payGroups, mode, onSuccess, onCancel }: Props = $props();

	// Form state
	let firstName = $state(employee?.firstName ?? '');
	let lastName = $state(employee?.lastName ?? '');
	let sin = $state(''); // Only used in create mode
	let email = $state(employee?.email ?? '');
	let payGroupId = $state(employee?.payGroupId ?? '');
	let province = $state<Province>(employee?.provinceOfEmployment ?? 'ON');
	let hireDate = $state(employee?.hireDate ?? '');
	let tags = $state<string[]>(employee?.tags ?? []);
	let newTag = $state('');

	// Compensation
	let compensationType = $state<'salaried' | 'hourly'>(
		employee?.hourlyRate ? 'hourly' : 'salaried'
	);
	let annualSalary = $state(employee?.annualSalary ?? 0);
	let hourlyRate = $state(employee?.hourlyRate ?? 0);

	// Tax
	let federalClaimAmount = $state(employee?.federalClaimAmount ?? FEDERAL_BPA_2025);
	let provincialClaimAmount = $state(employee?.provincialClaimAmount ?? PROVINCIAL_BPA_2025['ON']);
	let isCppExempt = $state(employee?.isCppExempt ?? false);
	let isEiExempt = $state(employee?.isEiExempt ?? false);
	let cpp2Exempt = $state(employee?.cpp2Exempt ?? false);

	// Deductions
	let rrspPerPeriod = $state(employee?.rrspPerPeriod ?? 0);
	let unionDuesPerPeriod = $state(employee?.unionDuesPerPeriod ?? 0);

	// Vacation
	let vacationPayoutMethod = $state<VacationPayoutMethod>(employee?.vacationConfig?.payoutMethod ?? 'accrual');
	let vacationRate = $state<VacationRate>(employee?.vacationConfig?.vacationRate ?? '0.04');
	let vacationBalance = $state(employee?.vacationBalance ?? 0);

	// UI state
	let isSubmitting = $state(false);
	let errors = $state<Record<string, string>>({});
	let submitError = $state<string | null>(null);

	// Derived: Selected pay group details
	const selectedPayGroup = $derived(payGroups.find(pg => pg.id === payGroupId) ?? null);

	// Derived: Years of service for vacation rate suggestion
	const yearsOfService = $derived(calculateYearsOfService(hireDate));
	const suggestedRate = $derived(suggestVacationRate(yearsOfService));

	// Reset form when employee prop changes (for edit mode)
	$effect(() => {
		if (mode === 'edit' && employee) {
			firstName = employee.firstName;
			lastName = employee.lastName;
			email = employee.email ?? '';
			payGroupId = employee.payGroupId ?? '';
			province = employee.provinceOfEmployment;
			hireDate = employee.hireDate;
			tags = employee.tags ?? [];
			compensationType = employee.hourlyRate ? 'hourly' : 'salaried';
			annualSalary = employee.annualSalary ?? 0;
			hourlyRate = employee.hourlyRate ?? 0;
			federalClaimAmount = employee.federalClaimAmount;
			provincialClaimAmount = employee.provincialClaimAmount;
			isCppExempt = employee.isCppExempt;
			isEiExempt = employee.isEiExempt;
			cpp2Exempt = employee.cpp2Exempt;
			rrspPerPeriod = employee.rrspPerPeriod;
			unionDuesPerPeriod = employee.unionDuesPerPeriod;
			vacationPayoutMethod = employee.vacationConfig?.payoutMethod ?? 'accrual';
			vacationRate = employee.vacationConfig?.vacationRate ?? '0.04';
			vacationBalance = employee.vacationBalance ?? 0;
			errors = {};
			submitError = null;
		}
	});

	// Mask SIN for display
	function maskSIN(sin: string): string {
		const digits = sin.replace(/\D/g, '');
		if (digits.length < 9) return sin;
		return `${digits.slice(0, 3)}-${digits.slice(3, 6)}-${digits.slice(6, 9)}`;
	}

	// Province change handler - auto-fill BPA
	function handleProvinceChange(newProvince: Province) {
		province = newProvince;
		federalClaimAmount = FEDERAL_BPA_2025;
		provincialClaimAmount = PROVINCIAL_BPA_2025[newProvince];
	}

	// Tag management
	function addTag() {
		const trimmed = newTag.trim();
		if (trimmed && !tags.includes(trimmed)) {
			tags = [...tags, trimmed];
		}
		newTag = '';
	}

	function removeTag(tag: string) {
		tags = tags.filter(t => t !== tag);
	}

	function handleTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTag();
		}
	}

	// Validation
	function isValidEmail(email: string): boolean {
		return !email || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
	}

	function isValidSIN(sin: string): boolean {
		const digits = sin.replace(/\D/g, '');
		return digits.length === 9;
	}

	function validate(): boolean {
		const newErrors: Record<string, string> = {};

		// Personal
		if (!firstName.trim()) newErrors.firstName = 'First name is required';
		if (!lastName.trim()) newErrors.lastName = 'Last name is required';
		if (email && !isValidEmail(email)) newErrors.email = 'Invalid email format';

		// SIN validation only in create mode
		if (mode === 'create') {
			if (!sin.trim()) newErrors.sin = 'SIN is required';
			else if (!isValidSIN(sin)) newErrors.sin = 'SIN must be 9 digits';
		}

		// Employment
		if (!province) newErrors.province = 'Province is required';
		if (!hireDate) newErrors.hireDate = 'Hire date is required';

		// Compensation
		if (compensationType === 'salaried' && (!annualSalary || annualSalary <= 0)) {
			newErrors.annualSalary = 'Annual salary is required';
		}
		if (compensationType === 'hourly' && (!hourlyRate || hourlyRate <= 0)) {
			newErrors.hourlyRate = 'Hourly rate is required';
		}

		// Tax
		if (federalClaimAmount < 0) newErrors.federalClaimAmount = 'Invalid amount';
		if (provincialClaimAmount < 0) newErrors.provincialClaimAmount = 'Invalid amount';

		errors = newErrors;
		return Object.keys(newErrors).length === 0;
	}

	// Submit handler
	async function handleSubmit() {
		if (!validate()) return;

		isSubmitting = true;
		submitError = null;

		// Get pay frequency from selected pay group
		const payFrequency = selectedPayGroup?.payFrequency ?? 'bi_weekly';
		const employmentType = selectedPayGroup?.employmentType ?? 'full_time';

		if (mode === 'create') {
			// Create new employee
			const createInput: EmployeeCreateInput = {
				first_name: firstName.trim(),
				last_name: lastName.trim(),
				sin: sin.replace(/\D/g, ''), // Strip non-digits
				email: email.trim() || null,
				province_of_employment: province,
				pay_frequency: payFrequency,
				employment_type: employmentType,
				hire_date: hireDate,
				annual_salary: compensationType === 'salaried' ? annualSalary : null,
				hourly_rate: compensationType === 'hourly' ? hourlyRate : null,
				federal_claim_amount: federalClaimAmount,
				provincial_claim_amount: provincialClaimAmount,
				is_cpp_exempt: isCppExempt,
				is_ei_exempt: isEiExempt,
				cpp2_exempt: cpp2Exempt,
				rrsp_per_period: rrspPerPeriod,
				union_dues_per_period: unionDuesPerPeriod,
				vacation_config: {
					payout_method: vacationPayoutMethod,
					vacation_rate: vacationRate
				},
				vacation_balance: vacationBalance
			};

			const result = await createEmployee(createInput);
			isSubmitting = false;

			if (result.error) {
				submitError = result.error;
				return;
			}

			if (result.data) {
				// After create, assign to pay group
				if (payGroupId) {
					const { assignEmployeesToPayGroup } = await import('$lib/services/employeeService');
					await assignEmployeesToPayGroup([result.data.id], payGroupId);
				}
				onSuccess(result.data);
			}
		} else {
			// Update existing employee
			if (!employee) return;

			const updateInput: EmployeeUpdateInput = {
				first_name: firstName.trim(),
				last_name: lastName.trim(),
				email: email.trim() || null,
				province_of_employment: province,
				pay_frequency: payFrequency,
				employment_type: employmentType,
				hire_date: hireDate,
				annual_salary: compensationType === 'salaried' ? annualSalary : null,
				hourly_rate: compensationType === 'hourly' ? hourlyRate : null,
				federal_claim_amount: federalClaimAmount,
				provincial_claim_amount: provincialClaimAmount,
				is_cpp_exempt: isCppExempt,
				is_ei_exempt: isEiExempt,
				cpp2_exempt: cpp2Exempt,
				rrsp_per_period: rrspPerPeriod,
				union_dues_per_period: unionDuesPerPeriod,
				vacation_config: {
					payout_method: vacationPayoutMethod,
					vacation_rate: vacationRate
				}
			};

			const result = await updateEmployee(employee.id, updateInput);
			isSubmitting = false;

			if (result.error) {
				submitError = result.error;
				return;
			}

			if (result.data) {
				// Handle pay group change
				if (payGroupId !== employee.payGroupId) {
					const { assignEmployeesToPayGroup, removeEmployeeFromPayGroup } = await import('$lib/services/employeeService');
					if (payGroupId) {
						await assignEmployeesToPayGroup([employee.id], payGroupId);
					} else {
						await removeEmployeeFromPayGroup(employee.id);
					}
				}
				onSuccess(result.data);
			}
		}
	}

	// Format currency for display
	function formatCurrency(amount: number): string {
		return new Intl.NumberFormat('en-CA', {
			style: 'currency',
			currency: 'CAD',
			maximumFractionDigits: 0
		}).format(amount);
	}
</script>

<form class="flex flex-col gap-6" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
	{#if submitError}
		<div class="flex items-center gap-3 p-4 bg-error-50 border border-error-200 rounded-lg text-error-700">
			<i class="fas fa-exclamation-circle"></i>
			<span class="flex-1">{submitError}</span>
			<button type="button" class="bg-transparent border-none text-error-500 cursor-pointer p-1 opacity-70 hover:opacity-100" onclick={() => submitError = null}>
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	<!-- Section 1: Personal Information -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Personal Information</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="firstName" class="text-body-small font-medium text-surface-700">First Name *</label>
				<input
					id="firstName"
					type="text"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.firstName ? 'border-error-500' : 'border-surface-300'}"
					bind:value={firstName}
				/>
				{#if errors.firstName}
					<span class="text-auxiliary-text text-error-600">{errors.firstName}</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="lastName" class="text-body-small font-medium text-surface-700">Last Name *</label>
				<input
					id="lastName"
					type="text"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.lastName ? 'border-error-500' : 'border-surface-300'}"
					bind:value={lastName}
				/>
				{#if errors.lastName}
					<span class="text-auxiliary-text text-error-600">{errors.lastName}</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="sin" class="text-body-small font-medium text-surface-700">SIN {mode === 'create' ? '*' : ''}</label>
				{#if mode === 'create'}
					<input
						id="sin"
						type="text"
						class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.sin ? 'border-error-500' : 'border-surface-300'}"
						bind:value={sin}
						placeholder="123-456-789"
						maxlength="11"
					/>
					{#if errors.sin}
						<span class="text-auxiliary-text text-error-600">{errors.sin}</span>
					{/if}
				{:else}
					<input
						id="sin"
						type="text"
						class="p-3 border border-surface-300 rounded-md text-body-content bg-surface-100 text-surface-500 cursor-not-allowed"
						value={employee?.sin ?? '***-***-***'}
						readonly
						disabled
					/>
					<span class="text-auxiliary-text text-surface-500">SIN cannot be changed after creation</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2">
				<label for="email" class="text-body-small font-medium text-surface-700">Email</label>
				<input
					id="email"
					type="email"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.email ? 'border-error-500' : 'border-surface-300'}"
					bind:value={email}
					placeholder="employee@company.com"
				/>
				{#if errors.email}
					<span class="text-auxiliary-text text-error-600">{errors.email}</span>
				{/if}
			</div>
		</div>
	</section>

	<!-- Section 2: Employment Details -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Employment Details</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="payGroup" class="text-body-small font-medium text-surface-700">Pay Group</label>
				<select
					id="payGroup"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={payGroupId}
				>
					<option value="">No pay group (unassigned)</option>
					{#each payGroups as pg}
						<option value={pg.id}>{pg.name}</option>
					{/each}
				</select>
			</div>

			<div class="flex flex-col gap-2">
				<label for="province" class="text-body-small font-medium text-surface-700">Province of Employment *</label>
				<select
					id="province"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.province ? 'border-error-500' : 'border-surface-300'}"
					value={province}
					onchange={(e) => handleProvinceChange(e.currentTarget.value as Province)}
				>
					{#each Object.entries(PROVINCE_LABELS) as [code, label]}
						<option value={code}>{label}</option>
					{/each}
				</select>
				{#if errors.province}
					<span class="text-auxiliary-text text-error-600">{errors.province}</span>
				{/if}
			</div>

			<!-- Inherited from Pay Group (read-only) -->
			{#if selectedPayGroup}
				<div class="flex flex-col gap-2">
					<label class="text-body-small font-medium text-surface-700">Pay Frequency</label>
					<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
						{PAY_FREQUENCY_LABELS[selectedPayGroup.payFrequency]}
						<span class="text-auxiliary-text text-surface-400 ml-2">(from Pay Group)</span>
					</div>
				</div>

				<div class="flex flex-col gap-2">
					<label class="text-body-small font-medium text-surface-700">Employment Type</label>
					<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
						{EMPLOYMENT_TYPE_LABELS[selectedPayGroup.employmentType]}
						<span class="text-auxiliary-text text-surface-400 ml-2">(from Pay Group)</span>
					</div>
				</div>
			{/if}

			<div class="flex flex-col gap-2">
				<label for="hireDate" class="text-body-small font-medium text-surface-700">Hire Date *</label>
				<input
					id="hireDate"
					type="date"
					class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.hireDate ? 'border-error-500' : 'border-surface-300'}"
					bind:value={hireDate}
				/>
				{#if errors.hireDate}
					<span class="text-auxiliary-text text-error-600">{errors.hireDate}</span>
				{/if}
				{#if hireDate}
					<span class="text-auxiliary-text text-surface-500">Years of service: {yearsOfService.toFixed(1)} years</span>
				{/if}
			</div>

			<div class="flex flex-col gap-2 col-span-full">
				<label for="tags" class="text-body-small font-medium text-surface-700">Tags</label>
				<div class="flex flex-col gap-2">
					<div class="flex flex-wrap gap-2">
						{#each tags as tag}
							<span class="inline-flex items-center gap-1 py-1 px-3 bg-primary-100 text-primary-700 rounded-full text-body-small">
								{tag}
								<button type="button" class="flex items-center justify-center w-4 h-4 p-0 border-none bg-transparent text-primary-500 cursor-pointer rounded-full hover:bg-primary-200 hover:text-primary-700" onclick={() => removeTag(tag)}>
									<i class="fas fa-times text-xs"></i>
								</button>
							</span>
						{/each}
					</div>
					<div class="flex gap-2">
						<input
							id="tags"
							type="text"
							class="flex-1 p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
							bind:value={newTag}
							onkeydown={handleTagKeydown}
							placeholder="Add a tag..."
						/>
						<button type="button" class="py-2 px-4 border border-surface-300 rounded-md bg-white text-surface-700 text-body-small cursor-pointer transition-[150ms] hover:bg-surface-100 hover:border-surface-400 disabled:opacity-50 disabled:cursor-not-allowed" onclick={addTag} disabled={!newTag.trim()}>
							Add
						</button>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 3: Compensation -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Compensation</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2 col-span-full">
				<label class="text-body-small font-medium text-surface-700">Compensation Type *</label>
				<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input
							type="radio"
							name="compensationType"
							value="salaried"
							bind:group={compensationType}
						/>
						<span>Annual Salary</span>
					</label>
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input
							type="radio"
							name="compensationType"
							value="hourly"
							bind:group={compensationType}
						/>
						<span>Hourly Rate</span>
					</label>
				</div>
			</div>

			{#if compensationType === 'salaried'}
				<div class="flex flex-col gap-2">
					<label for="annualSalary" class="text-body-small font-medium text-surface-700">Annual Salary *</label>
					<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
						<input
							id="annualSalary"
							type="number"
							class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
							bind:value={annualSalary}
							min="0"
							step="100"
						/>
					</div>
					{#if errors.annualSalary}
						<span class="text-auxiliary-text text-error-600">{errors.annualSalary}</span>
					{/if}
				</div>
			{:else}
				<div class="flex flex-col gap-2">
					<label for="hourlyRate" class="text-body-small font-medium text-surface-700">Hourly Rate *</label>
					<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
						<input
							id="hourlyRate"
							type="number"
							class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
							bind:value={hourlyRate}
							min="0"
							step="0.01"
						/>
						<span class="p-3 bg-surface-100 text-surface-500 text-body-content">/hr</span>
					</div>
					{#if errors.hourlyRate}
						<span class="text-auxiliary-text text-error-600">{errors.hourlyRate}</span>
					{/if}
				</div>
			{/if}
		</div>
	</section>

	<!-- Section 4: Tax Information -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Tax Information (TD1)</h3>
		<p class="text-body-small text-surface-500 m-0 mb-4 flex items-center gap-2">
			<i class="fas fa-info-circle text-primary-500"></i>
			Claim amounts are auto-filled with 2025 Basic Personal Amounts when province changes
		</p>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="federalClaim" class="text-body-small font-medium text-surface-700">Federal Claim Amount *</label>
				<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
					<input
						id="federalClaim"
						type="number"
						class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
						bind:value={federalClaimAmount}
						min="0"
						step="1"
					/>
				</div>
				{#if errors.federalClaimAmount}
					<span class="text-auxiliary-text text-error-600">{errors.federalClaimAmount}</span>
				{/if}
				<span class="text-auxiliary-text text-surface-500">2025 BPA: {formatCurrency(FEDERAL_BPA_2025)}</span>
			</div>

			<div class="flex flex-col gap-2">
				<label for="provincialClaim" class="text-body-small font-medium text-surface-700">Provincial Claim Amount *</label>
				<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
					<input
						id="provincialClaim"
						type="number"
						class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
						bind:value={provincialClaimAmount}
						min="0"
						step="1"
					/>
				</div>
				{#if errors.provincialClaimAmount}
					<span class="text-auxiliary-text text-error-600">{errors.provincialClaimAmount}</span>
				{/if}
				<span class="text-auxiliary-text text-surface-500">{PROVINCE_LABELS[province]} BPA: {formatCurrency(PROVINCIAL_BPA_2025[province])}</span>
			</div>

			<div class="flex flex-col gap-2 col-span-full">
				<label class="text-body-small font-medium text-surface-700">Exemptions</label>
				<div class="flex gap-6 flex-wrap max-sm:flex-col max-sm:gap-3">
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" bind:checked={isCppExempt} />
						<span>CPP Exempt</span>
					</label>
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" bind:checked={isEiExempt} />
						<span>EI Exempt</span>
					</label>
					<label class="flex items-center gap-2 text-body-content text-surface-700 cursor-pointer">
						<input type="checkbox" bind:checked={cpp2Exempt} />
						<span>CPP2 Exempt</span>
						<span class="text-surface-400 cursor-help" title="CPT30 form on file - exempt from additional CPP contributions">
							<i class="fas fa-info-circle"></i>
						</span>
					</label>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 5: Optional Deductions -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Optional Deductions</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="rrsp" class="text-body-small font-medium text-surface-700">RRSP Per Period</label>
				<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
					<input
						id="rrsp"
						type="number"
						class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
						bind:value={rrspPerPeriod}
						min="0"
						step="0.01"
					/>
				</div>
			</div>

			<div class="flex flex-col gap-2">
				<label for="unionDues" class="text-body-small font-medium text-surface-700">Union Dues Per Period</label>
				<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
					<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
					<input
						id="unionDues"
						type="number"
						class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
						bind:value={unionDuesPerPeriod}
						min="0"
						step="0.01"
					/>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 6: Vacation Settings -->
	<section class="bg-white rounded-xl p-6 shadow-md3-1">
		<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Vacation Settings</h3>
		<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
			<div class="flex flex-col gap-2">
				<label for="vacationRate" class="text-body-small font-medium text-surface-700">Vacation Rate</label>
				<select
					id="vacationRate"
					class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
					bind:value={vacationRate}
				>
					{#each Object.entries(VACATION_RATE_LABELS) as [rate, label]}
						<option value={rate}>{label}</option>
					{/each}
				</select>
				{#if vacationRate !== '0' && vacationRate !== suggestedRate && hireDate}
					<span class="text-auxiliary-text text-primary-600 flex items-center gap-1">
						<i class="fas fa-lightbulb"></i>
						Suggested: {VACATION_RATE_LABELS[suggestedRate]} based on {yearsOfService.toFixed(1)} years of service
					</span>
				{/if}
			</div>

			{#if vacationRate !== '0'}
				<div class="flex flex-col gap-2">
					<label for="vacationMethod" class="text-body-small font-medium text-surface-700">Payout Method</label>
					<select
						id="vacationMethod"
						class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
						bind:value={vacationPayoutMethod}
					>
						<option value="accrual">Accrual (pay when vacation taken)</option>
						<option value="pay_as_you_go">Pay as you go (add to each paycheck)</option>
					</select>
				</div>

				{#if vacationPayoutMethod === 'accrual'}
					{#if mode === 'create'}
						<div class="flex flex-col gap-2">
							<label for="vacationBalance" class="text-body-small font-medium text-surface-700">Initial Vacation Balance</label>
							<div class="flex items-center border border-surface-300 rounded-md overflow-hidden transition-[150ms] focus-within:border-primary-500 focus-within:ring-[3px] focus-within:ring-primary-500/10">
								<span class="p-3 bg-surface-100 text-surface-500 text-body-content">$</span>
								<input
									id="vacationBalance"
									type="number"
									class="flex-1 p-3 border-none rounded-none text-body-content focus:outline-none focus:ring-0"
									bind:value={vacationBalance}
									min="0"
									step="0.01"
								/>
							</div>
							<span class="text-auxiliary-text text-surface-500">Opening balance for vacation pay accrual</span>
						</div>
					{:else}
						<div class="flex flex-col gap-2">
							<label class="text-body-small font-medium text-surface-700">Current Balance</label>
							<div class="p-3 bg-surface-100 rounded-md text-body-content text-surface-600">
								{formatCurrency(employee?.vacationBalance ?? 0)}
								<span class="text-auxiliary-text text-surface-400 ml-2">(managed by payroll)</span>
							</div>
						</div>
					{/if}
				{/if}
			{/if}
		</div>
	</section>

	<!-- Form Actions - Hidden, controlled by parent page -->
	<input type="submit" hidden />
</form>

<!-- Expose submit function to parent -->
<svelte:options accessors={true} />
