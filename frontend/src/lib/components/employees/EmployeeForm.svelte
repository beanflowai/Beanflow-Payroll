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

<form class="employee-form" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
	{#if submitError}
		<div class="error-banner">
			<i class="fas fa-exclamation-circle"></i>
			<span>{submitError}</span>
			<button type="button" class="error-dismiss" onclick={() => submitError = null}>
				<i class="fas fa-times"></i>
			</button>
		</div>
	{/if}

	<!-- Section 1: Personal Information -->
	<section class="form-section">
		<h3 class="section-title">Personal Information</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="firstName" class="form-label">First Name *</label>
				<input
					id="firstName"
					type="text"
					class="form-input"
					class:error={errors.firstName}
					bind:value={firstName}
				/>
				{#if errors.firstName}
					<span class="error-message">{errors.firstName}</span>
				{/if}
			</div>

			<div class="form-group">
				<label for="lastName" class="form-label">Last Name *</label>
				<input
					id="lastName"
					type="text"
					class="form-input"
					class:error={errors.lastName}
					bind:value={lastName}
				/>
				{#if errors.lastName}
					<span class="error-message">{errors.lastName}</span>
				{/if}
			</div>

			<div class="form-group">
				<label for="sin" class="form-label">SIN {mode === 'create' ? '*' : ''}</label>
				{#if mode === 'create'}
					<input
						id="sin"
						type="text"
						class="form-input"
						class:error={errors.sin}
						bind:value={sin}
						placeholder="123-456-789"
						maxlength="11"
					/>
					{#if errors.sin}
						<span class="error-message">{errors.sin}</span>
					{/if}
				{:else}
					<input
						id="sin"
						type="text"
						class="form-input readonly"
						value={employee?.sin ?? '***-***-***'}
						readonly
						disabled
					/>
					<span class="field-hint">SIN cannot be changed after creation</span>
				{/if}
			</div>

			<div class="form-group">
				<label for="email" class="form-label">Email</label>
				<input
					id="email"
					type="email"
					class="form-input"
					class:error={errors.email}
					bind:value={email}
					placeholder="employee@company.com"
				/>
				{#if errors.email}
					<span class="error-message">{errors.email}</span>
				{/if}
			</div>
		</div>
	</section>

	<!-- Section 2: Employment Details -->
	<section class="form-section">
		<h3 class="section-title">Employment Details</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="payGroup" class="form-label">Pay Group</label>
				<select
					id="payGroup"
					class="form-select"
					bind:value={payGroupId}
				>
					<option value="">No pay group (unassigned)</option>
					{#each payGroups as pg}
						<option value={pg.id}>{pg.name}</option>
					{/each}
				</select>
			</div>

			<div class="form-group">
				<label for="province" class="form-label">Province of Employment *</label>
				<select
					id="province"
					class="form-select"
					class:error={errors.province}
					value={province}
					onchange={(e) => handleProvinceChange(e.currentTarget.value as Province)}
				>
					{#each Object.entries(PROVINCE_LABELS) as [code, label]}
						<option value={code}>{label}</option>
					{/each}
				</select>
				{#if errors.province}
					<span class="error-message">{errors.province}</span>
				{/if}
			</div>

			<!-- Inherited from Pay Group (read-only) -->
			{#if selectedPayGroup}
				<div class="form-group">
					<label class="form-label">Pay Frequency</label>
					<div class="readonly-value">
						{PAY_FREQUENCY_LABELS[selectedPayGroup.payFrequency]}
						<span class="readonly-hint">(from Pay Group)</span>
					</div>
				</div>

				<div class="form-group">
					<label class="form-label">Employment Type</label>
					<div class="readonly-value">
						{EMPLOYMENT_TYPE_LABELS[selectedPayGroup.employmentType]}
						<span class="readonly-hint">(from Pay Group)</span>
					</div>
				</div>
			{/if}

			<div class="form-group">
				<label for="hireDate" class="form-label">Hire Date *</label>
				<input
					id="hireDate"
					type="date"
					class="form-input"
					class:error={errors.hireDate}
					bind:value={hireDate}
				/>
				{#if errors.hireDate}
					<span class="error-message">{errors.hireDate}</span>
				{/if}
				{#if hireDate}
					<span class="field-hint">Years of service: {yearsOfService.toFixed(1)} years</span>
				{/if}
			</div>

			<div class="form-group full-width">
				<label for="tags" class="form-label">Tags</label>
				<div class="tags-input-container">
					<div class="tags-list">
						{#each tags as tag}
							<span class="tag-chip">
								{tag}
								<button type="button" class="tag-remove" onclick={() => removeTag(tag)}>
									<i class="fas fa-times"></i>
								</button>
							</span>
						{/each}
					</div>
					<div class="tag-input-wrapper">
						<input
							id="tags"
							type="text"
							class="form-input"
							bind:value={newTag}
							onkeydown={handleTagKeydown}
							placeholder="Add a tag..."
						/>
						<button type="button" class="btn-add-tag" onclick={addTag} disabled={!newTag.trim()}>
							Add
						</button>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 3: Compensation -->
	<section class="form-section">
		<h3 class="section-title">Compensation</h3>
		<div class="form-grid">
			<div class="form-group full-width">
				<label class="form-label">Compensation Type *</label>
				<div class="radio-group">
					<label class="radio-label">
						<input
							type="radio"
							name="compensationType"
							value="salaried"
							bind:group={compensationType}
						/>
						<span>Annual Salary</span>
					</label>
					<label class="radio-label">
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
				<div class="form-group">
					<label for="annualSalary" class="form-label">Annual Salary *</label>
					<div class="input-with-prefix">
						<span class="input-prefix">$</span>
						<input
							id="annualSalary"
							type="number"
							class="form-input"
							class:error={errors.annualSalary}
							bind:value={annualSalary}
							min="0"
							step="100"
						/>
					</div>
					{#if errors.annualSalary}
						<span class="error-message">{errors.annualSalary}</span>
					{/if}
				</div>
			{:else}
				<div class="form-group">
					<label for="hourlyRate" class="form-label">Hourly Rate *</label>
					<div class="input-with-prefix">
						<span class="input-prefix">$</span>
						<input
							id="hourlyRate"
							type="number"
							class="form-input"
							class:error={errors.hourlyRate}
							bind:value={hourlyRate}
							min="0"
							step="0.01"
						/>
						<span class="input-suffix">/hr</span>
					</div>
					{#if errors.hourlyRate}
						<span class="error-message">{errors.hourlyRate}</span>
					{/if}
				</div>
			{/if}
		</div>
	</section>

	<!-- Section 4: Tax Information -->
	<section class="form-section">
		<h3 class="section-title">Tax Information (TD1)</h3>
		<p class="section-description">
			<i class="fas fa-info-circle"></i>
			Claim amounts are auto-filled with 2025 Basic Personal Amounts when province changes
		</p>
		<div class="form-grid">
			<div class="form-group">
				<label for="federalClaim" class="form-label">Federal Claim Amount *</label>
				<div class="input-with-prefix">
					<span class="input-prefix">$</span>
					<input
						id="federalClaim"
						type="number"
						class="form-input"
						class:error={errors.federalClaimAmount}
						bind:value={federalClaimAmount}
						min="0"
						step="1"
					/>
				</div>
				{#if errors.federalClaimAmount}
					<span class="error-message">{errors.federalClaimAmount}</span>
				{/if}
				<span class="field-hint">2025 BPA: {formatCurrency(FEDERAL_BPA_2025)}</span>
			</div>

			<div class="form-group">
				<label for="provincialClaim" class="form-label">Provincial Claim Amount *</label>
				<div class="input-with-prefix">
					<span class="input-prefix">$</span>
					<input
						id="provincialClaim"
						type="number"
						class="form-input"
						class:error={errors.provincialClaimAmount}
						bind:value={provincialClaimAmount}
						min="0"
						step="1"
					/>
				</div>
				{#if errors.provincialClaimAmount}
					<span class="error-message">{errors.provincialClaimAmount}</span>
				{/if}
				<span class="field-hint">{PROVINCE_LABELS[province]} BPA: {formatCurrency(PROVINCIAL_BPA_2025[province])}</span>
			</div>

			<div class="form-group full-width">
				<label class="form-label">Exemptions</label>
				<div class="checkbox-group">
					<label class="checkbox-label">
						<input type="checkbox" bind:checked={isCppExempt} />
						<span>CPP Exempt</span>
					</label>
					<label class="checkbox-label">
						<input type="checkbox" bind:checked={isEiExempt} />
						<span>EI Exempt</span>
					</label>
					<label class="checkbox-label">
						<input type="checkbox" bind:checked={cpp2Exempt} />
						<span>CPP2 Exempt</span>
						<span class="checkbox-hint" title="CPT30 form on file - exempt from additional CPP contributions">
							<i class="fas fa-info-circle"></i>
						</span>
					</label>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 5: Optional Deductions -->
	<section class="form-section">
		<h3 class="section-title">Optional Deductions</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="rrsp" class="form-label">RRSP Per Period</label>
				<div class="input-with-prefix">
					<span class="input-prefix">$</span>
					<input
						id="rrsp"
						type="number"
						class="form-input"
						bind:value={rrspPerPeriod}
						min="0"
						step="0.01"
					/>
				</div>
			</div>

			<div class="form-group">
				<label for="unionDues" class="form-label">Union Dues Per Period</label>
				<div class="input-with-prefix">
					<span class="input-prefix">$</span>
					<input
						id="unionDues"
						type="number"
						class="form-input"
						bind:value={unionDuesPerPeriod}
						min="0"
						step="0.01"
					/>
				</div>
			</div>
		</div>
	</section>

	<!-- Section 6: Vacation Settings -->
	<section class="form-section">
		<h3 class="section-title">Vacation Settings</h3>
		<div class="form-grid">
			<div class="form-group">
				<label for="vacationRate" class="form-label">Vacation Rate</label>
				<select
					id="vacationRate"
					class="form-select"
					bind:value={vacationRate}
				>
					{#each Object.entries(VACATION_RATE_LABELS) as [rate, label]}
						<option value={rate}>{label}</option>
					{/each}
				</select>
				{#if vacationRate !== '0' && vacationRate !== suggestedRate && hireDate}
					<span class="field-hint suggestion">
						<i class="fas fa-lightbulb"></i>
						Suggested: {VACATION_RATE_LABELS[suggestedRate]} based on {yearsOfService.toFixed(1)} years of service
					</span>
				{/if}
			</div>

			{#if vacationRate !== '0'}
				<div class="form-group">
					<label for="vacationMethod" class="form-label">Payout Method</label>
					<select
						id="vacationMethod"
						class="form-select"
						bind:value={vacationPayoutMethod}
					>
						<option value="accrual">Accrual (pay when vacation taken)</option>
						<option value="pay_as_you_go">Pay as you go (add to each paycheck)</option>
					</select>
				</div>

				{#if vacationPayoutMethod === 'accrual'}
					{#if mode === 'create'}
						<div class="form-group">
							<label for="vacationBalance" class="form-label">Initial Vacation Balance</label>
							<div class="input-with-prefix">
								<span class="input-prefix">$</span>
								<input
									id="vacationBalance"
									type="number"
									class="form-input"
									bind:value={vacationBalance}
									min="0"
									step="0.01"
								/>
							</div>
							<span class="field-hint">Opening balance for vacation pay accrual</span>
						</div>
					{:else}
						<div class="form-group">
							<label class="form-label">Current Balance</label>
							<div class="readonly-value">
								{formatCurrency(employee?.vacationBalance ?? 0)}
								<span class="readonly-hint">(managed by payroll)</span>
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

<style>
	.employee-form {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-6);
	}

	.error-banner {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-error-50, #fef2f2);
		border: 1px solid var(--color-error-200, #fecaca);
		border-radius: var(--radius-lg);
		color: var(--color-error-700, #b91c1c);
	}

	.error-banner span {
		flex: 1;
	}

	.error-dismiss {
		background: none;
		border: none;
		color: var(--color-error-500, #ef4444);
		cursor: pointer;
		padding: var(--spacing-1);
		opacity: 0.7;
	}

	.error-dismiss:hover {
		opacity: 1;
	}

	.form-section {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-6);
		box-shadow: var(--shadow-md3-1);
	}

	.section-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-4);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.section-description {
		font-size: var(--font-size-body-small);
		color: var(--color-surface-500);
		margin: 0 0 var(--spacing-4);
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
	}

	.section-description i {
		color: var(--color-primary-500);
	}

	.form-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: var(--spacing-4);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.form-group.full-width {
		grid-column: 1 / -1;
	}

	.form-label {
		font-size: var(--font-size-body-small);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-700);
	}

	.form-input,
	.form-select {
		padding: var(--spacing-3);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		transition: var(--transition-fast);
	}

	.form-input:focus,
	.form-select:focus {
		outline: none;
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.form-input.error,
	.form-select.error {
		border-color: var(--color-error-500, #ef4444);
	}

	.form-input.readonly {
		background: var(--color-surface-100);
		color: var(--color-surface-500);
		cursor: not-allowed;
	}

	.error-message {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-error-600, #dc2626);
	}

	.field-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.field-hint.suggestion {
		color: var(--color-primary-600);
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
	}

	.readonly-value {
		padding: var(--spacing-3);
		background: var(--color-surface-100);
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
	}

	.readonly-hint {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-400);
		margin-left: var(--spacing-2);
	}

	/* Input with prefix/suffix */
	.input-with-prefix {
		display: flex;
		align-items: center;
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		overflow: hidden;
		transition: var(--transition-fast);
	}

	.input-with-prefix:focus-within {
		border-color: var(--color-primary-500);
		box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
	}

	.input-prefix,
	.input-suffix {
		padding: var(--spacing-3);
		background: var(--color-surface-100);
		color: var(--color-surface-500);
		font-size: var(--font-size-body-content);
	}

	.input-with-prefix .form-input {
		border: none;
		border-radius: 0;
		flex: 1;
	}

	.input-with-prefix .form-input:focus {
		box-shadow: none;
	}

	/* Radio and Checkbox groups */
	.radio-group,
	.checkbox-group {
		display: flex;
		gap: var(--spacing-6);
		flex-wrap: wrap;
	}

	.radio-label,
	.checkbox-label {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
		cursor: pointer;
	}

	.checkbox-hint {
		color: var(--color-surface-400);
		cursor: help;
	}

	/* Tags */
	.tags-input-container {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-2);
	}

	.tags-list {
		display: flex;
		flex-wrap: wrap;
		gap: var(--spacing-2);
	}

	.tag-chip {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-3);
		background: var(--color-primary-100);
		color: var(--color-primary-700);
		border-radius: var(--radius-full);
		font-size: var(--font-size-body-small);
	}

	.tag-remove {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 16px;
		height: 16px;
		padding: 0;
		border: none;
		background: transparent;
		color: var(--color-primary-500);
		cursor: pointer;
		border-radius: var(--radius-full);
	}

	.tag-remove:hover {
		background: var(--color-primary-200);
		color: var(--color-primary-700);
	}

	.tag-input-wrapper {
		display: flex;
		gap: var(--spacing-2);
	}

	.tag-input-wrapper .form-input {
		flex: 1;
	}

	.btn-add-tag {
		padding: var(--spacing-2) var(--spacing-4);
		border: 1px solid var(--color-surface-300);
		border-radius: var(--radius-md);
		background: white;
		color: var(--color-surface-700);
		font-size: var(--font-size-body-small);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-add-tag:hover:not(:disabled) {
		background: var(--color-surface-100);
		border-color: var(--color-surface-400);
	}

	.btn-add-tag:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Responsive */
	@media (max-width: 640px) {
		.form-grid {
			grid-template-columns: 1fr;
		}

		.radio-group,
		.checkbox-group {
			flex-direction: column;
			gap: var(--spacing-3);
		}
	}
</style>
