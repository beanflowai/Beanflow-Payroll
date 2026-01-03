<script lang="ts">
	import type { Province, PayFrequency, EmploymentType } from '$lib/types/employee';
	import {
		PROVINCE_LABELS,
		PAY_FREQUENCY_LABELS,
		EMPLOYMENT_TYPE_LABELS
	} from '$lib/types/employee';
	import type { ProvinceStandards } from '$lib/services/configService';

	interface Props {
		province: Province;
		payFrequency: PayFrequency;
		employmentType: EmploymentType;
		hireDate: string;
		occupation: string;
		tags: string[];
		provinceStandards: ProvinceStandards | null;
		provinceStandardsLoading: boolean;
		yearsOfService: number;
		errors: Record<string, string>;
		onProvinceChange: (province: Province) => void;
		onPayFrequencyChange: (value: PayFrequency) => void;
		onEmploymentTypeChange: (value: EmploymentType) => void;
		onHireDateChange: (value: string) => void;
		onOccupationChange: (value: string) => void;
		onTagsChange: (tags: string[]) => void;
	}

	let {
		province,
		payFrequency,
		employmentType,
		hireDate,
		occupation,
		tags,
		provinceStandards,
		provinceStandardsLoading,
		yearsOfService,
		errors,
		onProvinceChange,
		onPayFrequencyChange,
		onEmploymentTypeChange,
		onHireDateChange,
		onOccupationChange,
		onTagsChange
	}: Props = $props();

	// Local state for new tag input
	let newTag = $state('');

	// Tag management
	function addTag() {
		const trimmed = newTag.trim();
		if (trimmed && !tags.includes(trimmed)) {
			onTagsChange([...tags, trimmed]);
		}
		newTag = '';
	}

	function removeTag(tag: string) {
		onTagsChange(tags.filter(t => t !== tag));
	}

	function handleTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTag();
		}
	}
</script>

<section class="bg-white rounded-xl p-6 shadow-md3-1">
	<h3 class="text-body-content font-semibold text-surface-700 m-0 mb-4 uppercase tracking-wide">Employment Details</h3>
	<div class="grid grid-cols-2 gap-4 max-sm:grid-cols-1">
		<div class="flex flex-col gap-2">
			<label for="province" class="text-body-small font-medium text-surface-700">Province of Employment *</label>
			<select
				id="province"
				class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.province ? 'border-error-500' : 'border-surface-300'}"
				value={province}
				onchange={(e) => onProvinceChange(e.currentTarget.value as Province)}
			>
				{#each Object.entries(PROVINCE_LABELS) as [code, label]}
					<option value={code}>{label}</option>
				{/each}
			</select>
			{#if errors.province}
				<span class="text-auxiliary-text text-error-600">{errors.province}</span>
			{/if}
		</div>

		<!-- Province Employment Standards Info Card -->
		{#if provinceStandardsLoading}
			<div class="col-span-full p-4 bg-surface-50 border border-surface-200 rounded-lg">
				<div class="flex items-center gap-2 text-surface-500 text-body-small">
					<i class="fas fa-spinner fa-spin"></i>
					<span>Loading employment standards...</span>
				</div>
			</div>
		{:else if provinceStandards}
			<div class="col-span-full p-4 bg-primary-50 border border-primary-200 rounded-lg">
				<div class="flex items-center justify-between mb-3">
					<div class="flex items-center gap-2">
						<i class="fas fa-info-circle text-primary-500"></i>
						<h4 class="text-body-small font-semibold text-primary-700 m-0">{provinceStandards.provinceName} Employment Standards</h4>
					</div>
					<a
						href="https://beanflow.ai/resources/employment-standards?province={province}"
						target="_blank"
						rel="noopener noreferrer"
						class="text-auxiliary-text text-primary-600 hover:text-primary-700 hover:underline flex items-center gap-1"
					>
						See More
						<i class="fas fa-external-link-alt text-xs"></i>
					</a>
				</div>
				<div class="grid grid-cols-4 gap-4 max-sm:grid-cols-2">
					<!-- Vacation -->
					<div class="flex flex-col gap-1">
						<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Vacation</span>
						<span class="text-body-small text-primary-700">
							{provinceStandards.vacation.minimumWeeks} weeks ({provinceStandards.vacation.rateDisplay})
						</span>
						{#if provinceStandards.vacation.upgradeYears}
							<span class="text-auxiliary-text text-primary-500">
								{provinceStandards.vacation.upgradeWeeks} weeks after {provinceStandards.vacation.upgradeYears} years
							</span>
						{/if}
					</div>

					<!-- Sick Leave -->
					<div class="flex flex-col gap-1">
						<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Sick Leave</span>
						{#if provinceStandards.sickLeave.paidDays > 0 || provinceStandards.sickLeave.unpaidDays > 0}
							<span class="text-body-small text-primary-700">
								{#if provinceStandards.sickLeave.paidDays > 0}
									{provinceStandards.sickLeave.paidDays} paid
								{/if}
								{#if provinceStandards.sickLeave.paidDays > 0 && provinceStandards.sickLeave.unpaidDays > 0}
									+
								{/if}
								{#if provinceStandards.sickLeave.unpaidDays > 0}
									{provinceStandards.sickLeave.unpaidDays} unpaid
								{/if}
								days/year
							</span>
							{#if provinceStandards.sickLeave.waitingPeriodDays > 0}
								<span class="text-auxiliary-text text-primary-500">
									After {provinceStandards.sickLeave.waitingPeriodDays} days
								</span>
							{/if}
						{:else}
							<span class="text-body-small text-primary-500 italic">No statutory sick leave</span>
						{/if}
					</div>

					<!-- Overtime -->
					<div class="flex flex-col gap-1">
						<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Overtime</span>
						<span class="text-body-small text-primary-700">
							{#if provinceStandards.overtime.dailyThreshold}
								After {provinceStandards.overtime.dailyThreshold} hrs/day
							{:else}
								After {provinceStandards.overtime.weeklyThreshold} hrs/week
							{/if}
						</span>
						<span class="text-auxiliary-text text-primary-500">
							{provinceStandards.overtime.overtimeRate}x rate
							{#if provinceStandards.overtime.doubleTimeDaily}
								(2x after {provinceStandards.overtime.doubleTimeDaily} hrs)
							{/if}
						</span>
					</div>

					<!-- Statutory Holidays -->
					<div class="flex flex-col gap-1">
						<span class="text-auxiliary-text text-primary-600 font-medium uppercase tracking-wide">Stat Holidays</span>
						<span class="text-body-small text-primary-700">
							{provinceStandards.statutoryHolidaysCount} per year
						</span>
					</div>
				</div>
			</div>
		{/if}

		<div class="flex flex-col gap-2">
			<label for="payFrequency" class="text-body-small font-medium text-surface-700">Pay Frequency *</label>
			<select
				id="payFrequency"
				class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
				value={payFrequency}
				onchange={(e) => onPayFrequencyChange(e.currentTarget.value as PayFrequency)}
			>
				{#each Object.entries(PAY_FREQUENCY_LABELS) as [code, label]}
					<option value={code}>{label}</option>
				{/each}
			</select>
		</div>

		<div class="flex flex-col gap-2">
			<label for="employmentType" class="text-body-small font-medium text-surface-700">Employment Type *</label>
			<select
				id="employmentType"
				class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
				value={employmentType}
				onchange={(e) => onEmploymentTypeChange(e.currentTarget.value as EmploymentType)}
			>
				{#each Object.entries(EMPLOYMENT_TYPE_LABELS) as [code, label]}
					<option value={code}>{label}</option>
				{/each}
			</select>
		</div>

		<div class="flex flex-col gap-2">
			<label for="hireDate" class="text-body-small font-medium text-surface-700">Hire Date *</label>
			<input
				id="hireDate"
				type="date"
				class="p-3 border rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10 {errors.hireDate ? 'border-error-500' : 'border-surface-300'}"
				value={hireDate}
				oninput={(e) => onHireDateChange(e.currentTarget.value)}
			/>
			{#if errors.hireDate}
				<span class="text-auxiliary-text text-error-600">{errors.hireDate}</span>
			{/if}
			{#if hireDate}
				<span class="text-auxiliary-text text-surface-500">Years of service: {yearsOfService.toFixed(1)} years</span>
			{/if}
		</div>

		<div class="flex flex-col gap-2">
			<label for="occupation" class="text-body-small font-medium text-surface-700">Job Title / Occupation</label>
			<input
				id="occupation"
				type="text"
				class="p-3 border border-surface-300 rounded-md text-body-content transition-[150ms] focus:outline-none focus:border-primary-500 focus:ring-[3px] focus:ring-primary-500/10"
				value={occupation}
				oninput={(e) => onOccupationChange(e.currentTarget.value)}
				placeholder="e.g., Software Developer"
			/>
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
