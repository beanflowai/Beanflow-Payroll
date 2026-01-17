<script lang="ts">
	import { formatFullDate, formatDateNoYear, parseDateString } from '$lib/utils/dateUtils';

	/**
	 * Props for the PayDatePicker component
	 */
	interface Props {
		/** Current pay date value (YYYY-MM-DD format) */
		value: string;
		/** Pay period end date (YYYY-MM-DD format) */
		periodEnd: string;
		/** Province code (default: SK) */
		province?: string;
		/** Callback when value changes */
		onValueChange: (newValue: string) => void;
		/** Callback to save changes */
		onSave: (newValue: string) => Promise<void>;
		/** Callback to cancel editing */
		onCancel: () => void;
		/** Additional CSS classes */
		class?: string;
	}

	let {
		value,
		periodEnd,
		province = 'SK',
		onValueChange,
		onSave,
		onCancel,
		class: className = ''
	}: Props = $props();

	// Component state
	let isEditing = $state(false);
	let editedValue = $state(value);
	let isSaving = $state(false);
	let validationMessage = $state<{
		type: 'success' | 'warning' | 'error';
		text: string;
	} | null>(null);

	// Pay date delay configuration for each province
	const PAY_DATE_DELAY_DAYS: Record<string, number> = {
		SK: 6,
		ON: 7,
		BC: 8,
		AB: 10,
		MB: 10,
		QC: 16,
		NB: 5,
		NS: 5,
		PE: 7,
		NL: 7,
		NT: 10,
		NU: 10,
		YT: 10
	};

	const DEFAULT_DELAY_DAYS = 7;
	const EARLIEST_PAYMENT_DAYS_BEFORE = 10; // Allow paying up to 10 days before period end

	// Calculate date range
	function calculateDateRange() {
		const periodEndDate = parseDateString(periodEnd);
		const delayDays = PAY_DATE_DELAY_DAYS[province] ?? DEFAULT_DELAY_DAYS;
		const recommendedDate = new Date(periodEndDate);
		recommendedDate.setDate(periodEndDate.getDate() + delayDays);
		const latestDate = recommendedDate;

		// Earliest date: 10 days before period end (for early payment)
		const earliestDate = new Date(periodEndDate);
		earliestDate.setDate(periodEndDate.getDate() - EARLIEST_PAYMENT_DAYS_BEFORE);

		return {
			minDate: earliestDate.toISOString().split('T')[0],
			recommendedDate: recommendedDate.toISOString().split('T')[0],
			latestDate: latestDate.toISOString().split('T')[0]
		};
	}

	// Validation function
	function validate(): boolean {
		const { minDate, latestDate } = calculateDateRange();
		const editedDate = new Date(editedValue + 'T12:00:00');
		const min = new Date(minDate + 'T12:00:00');
		const max = new Date(latestDate + 'T12:00:00');

		if (editedDate > max) {
			validationMessage = {
				type: 'error',
				text: `Cannot be after ${formatFullDate(latestDate)} (legal deadline)`
			};
			return false;
		} else if (editedDate < min) {
			validationMessage = {
				type: 'error',
				text: `Cannot be earlier than 10 days before period end (earliest: ${formatFullDate(minDate)})`
			};
			return false;
		} else {
			const { recommendedDate } = calculateDateRange();
			const recommended = new Date(recommendedDate + 'T12:00:00');
			if (editedDate < recommended) {
				validationMessage = {
					type: 'warning',
					text: `Earlier than recommended (${formatFullDate(recommendedDate)})`
				};
			} else {
				validationMessage = {
					type: 'success',
					text: `Compliant: Before ${formatFullDate(latestDate)}`
				};
			}
			return true;
		}
	}

	// Check if December pay date (for tax year warning)
	function showTaxYearWarning(): boolean {
		const periodEndDate = parseDateString(periodEnd);
		const currentValue = new Date(value + 'T12:00:00');
		const edited = new Date(editedValue + 'T12:00:00');

		// Check if December and crossing year boundary
		return (
			periodEndDate.getMonth() === 11 && // December
			currentValue.getFullYear() !== edited.getFullYear()
		);
	}

	// Province name helper
	function getProvinceName(code: string): string {
		const names: Record<string, string> = {
			SK: 'Saskatchewan',
			ON: 'Ontario',
			BC: 'British Columbia',
			AB: 'Alberta',
			MB: 'Manitoba',
			QC: 'Quebec',
			NB: 'New Brunswick',
			NS: 'Nova Scotia',
			PE: 'Prince Edward Island',
			NL: 'Newfoundland and Labrador',
			NT: 'Northwest Territories',
			NU: 'Nunavut',
			YT: 'Yukon'
		};
		return names[code] ?? code;
	}

	// Event handlers
	async function handleSave() {
		if (validate()) {
			isSaving = true;
			try {
				await onSave(editedValue);
				onValueChange(editedValue);
				isEditing = false;
			} finally {
				isSaving = false;
			}
		}
	}

	function handleCancel() {
		editedValue = value;
		validationMessage = null;
		isEditing = false;
		onCancel();
	}

	function startEditing() {
		editedValue = value;
		validationMessage = null;
		isEditing = true;
	}

	// Get province delay info for display
	const provinceDelayInfo = $derived(() => {
		const delay = PAY_DATE_DELAY_DAYS[province] ?? DEFAULT_DELAY_DAYS;
		return {
			days: delay,
			name: getProvinceName(province)
		};
	});
</script>

<div class="pay-date-picker {className}">
	{#if !isEditing}
		<!-- Display mode -->
		<div class="flex items-center gap-2 group">
			<span class="text-headline-minimum font-semibold text-surface-800">
				Pay Date: {formatFullDate(value)}
			</span>
			<button
				onclick={startEditing}
				class="p-1.5 text-surface-400 hover:text-surface-600 hover:bg-surface-100 rounded-lg cursor-pointer transition-all duration-200"
				aria-label="Edit pay date"
				type="button"
			>
				<i class="fas fa-pen text-surface-600 text-xs"></i>
			</button>
		</div>

		<!-- Province compliance hint -->
		<p class="text-xs text-surface-500 mt-1">
			{provinceDelayInfo().name}: {formatDateNoYear(calculateDateRange().minDate)} to {formatDateNoYear(calculateDateRange().latestDate)} (legal deadline)
		</p>

	{:else}
		<!-- Edit mode -->
		<div class="space-y-3">
			<div class="flex items-center gap-3 flex-wrap">
				<label for="pay-date-input" class="text-sm font-medium text-surface-700">
					Pay Date:
				</label>
				<input
					id="pay-date-input"
					type="date"
					bind:value={editedValue}
					min={calculateDateRange().minDate}
					max={calculateDateRange().latestDate}
					onblur={() => validate()}
					class="px-3 py-2 border border-surface-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 cursor-pointer"
					aria-describedby="pay-date-validation"
				/>
				<button
					onclick={handleSave}
					disabled={!validationMessage || validationMessage.type === 'error' || isSaving}
					class="px-4 py-2 bg-primary-700 text-white rounded-lg hover:bg-primary-800 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-200"
					type="button"
				>
					{isSaving ? 'Saving...' : 'Save'}
				</button>
				<button
					onclick={handleCancel}
					disabled={isSaving}
					class="px-4 py-2 bg-surface-200 text-surface-700 rounded-lg hover:bg-surface-300 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer transition-colors duration-200"
					type="button"
				>
					Cancel
				</button>
			</div>

			{#if validationMessage}
				<div id="pay-date-validation" class="flex items-center gap-2 text-sm">
					{#if validationMessage.type === 'success'}
						<i class="fas fa-check-circle text-success-600"></i>
						<span class="text-success-700">{validationMessage.text}</span>
					{:else if validationMessage.type === 'warning'}
						<i class="fas fa-exclamation-triangle text-warning-600"></i>
						<span class="text-warning-700">{validationMessage.text}</span>
					{:else}
						<i class="fas fa-times-circle text-error-600"></i>
						<span class="text-error-700">{validationMessage.text}</span>
					{/if}
				</div>
			{/if}

			<!-- Province legal hint -->
			<p class="text-xs text-surface-600">
				{provinceDelayInfo().name}: {formatFullDate(calculateDateRange().minDate)} to {formatFullDate(calculateDateRange().latestDate)} (legal deadline)
			</p>

			<!-- Tax year warning for December -->
			{#if showTaxYearWarning()}
				<div class="mt-3 p-3 bg-warning-50 border border-warning-200 rounded-lg">
					<div class="flex gap-2 text-warning-800 text-sm">
						<i class="fas fa-info-circle flex-shrink-0 mt-0.5"></i>
						<div>
							<p class="font-medium">Tax Year Notice</p>
							<p class="mt-1">
								Changing pay date from {formatFullDate(value)} to {formatFullDate(editedValue)}
								will change the tax year for reporting.
							</p>
						</div>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	/* Text color tokens (using Tailwind classes) */
	.text-headline-minimum {
		font-size: 1.25rem;
		line-height: 1.75rem;
	}

	.text-surface-800 {
		color: #1e293b;
	}

	.text-surface-700 {
		color: #334155;
	}

	.text-surface-600 {
		color: #475569;
	}

	.text-surface-500 {
		color: #64748b;
	}

	.text-surface-300 {
		border-color: #cbd5e1;
		color: #cbd5e1;
	}

	.text-surface-100 {
		background-color: #f1f5f9;
	}

	.text-primary-700 {
		color: #0369a1;
	}

	.text-primary-800 {
		background-color: #075985;
	}

	.text-success-700 {
		color: #16a34a;
	}

	.text-success-600 {
		color: #16a34a;
	}

	.text-warning-800 {
		color: #b45309;
	}

	.text-warning-700 {
		color: #ca8a04;
	}

	.text-warning-600 {
		color: #d97706;
	}

	.text-warning-200 {
		border-color: #fde047;
		background-color: #fef9c3;
	}

	.text-warning-50 {
		background-color: #fffbeb;
	}

	.text-error-700 {
		color: #dc2626;
	}

	.text-error-600 {
		color: #dc2626;
	}

	.bg-primary-700 {
		background-color: #0369a1;
	}

	.hover\:bg-primary-800:hover {
		background-color: #075985;
	}

	.bg-surface-200 {
		background-color: #e2e8f0;
	}

	.hover\:bg-surface-300:hover {
		background-color: #cbd5e1;
	}
</style>
