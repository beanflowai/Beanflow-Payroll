<script lang="ts">
	import type { UpcomingPeriod, PayGroupSummary } from '$lib/types/payroll';
	import { PAYROLL_STATUS_LABELS } from '$lib/types/payroll';
	import { goto } from '$app/navigation';
	import { formatShortDate } from '$lib/utils/dateUtils';
	import { formatCurrency } from '$lib/utils/formatUtils';

	interface Props {
		periodData: UpcomingPeriod;
		onPayGroupClick?: (payGroup: PayGroupSummary) => void;
	}

	let { periodData, onPayGroupClick }: Props = $props();

	// Format currency with no decimals for cleaner display
	function formatCurrencyNoDecimals(amount: number): string {
		return formatCurrency(amount, { maximumFractionDigits: 0 });
	}

	function getDaysUntil(dateStr: string): string {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const targetDate = new Date(dateStr);
		targetDate.setHours(0, 0, 0, 0);
		const diffTime = targetDate.getTime() - today.getTime();
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		if (diffDays < 0) return `${Math.abs(diffDays)} days overdue`;
		if (diffDays === 0) return 'Today';
		if (diffDays === 1) return 'Tomorrow';
		return `in ${diffDays} days`;
	}

	function getDaysUntilClass(dateStr: string): string {
		const today = new Date();
		today.setHours(0, 0, 0, 0);
		const targetDate = new Date(dateStr);
		targetDate.setHours(0, 0, 0, 0);
		const diffTime = targetDate.getTime() - today.getTime();
		const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

		if (diffDays < 0) return 'bg-error-100 text-error-700';
		if (diffDays <= 3) return 'bg-warning-100 text-warning-700';
		if (diffDays <= 7) return 'bg-info-100 text-info-700';
		return 'bg-surface-100 text-surface-600';
	}

	function getStatusClass(status?: string): string {
		if (!status) return '';
		switch (status) {
			case 'paid':
				return 'bg-success-100 text-success-700';
			case 'approved':
				return 'bg-info-100 text-info-700';
			case 'pending_approval':
				return 'bg-warning-100 text-warning-700';
			case 'draft':
				return 'bg-surface-100 text-surface-600';
			default:
				return '';
		}
	}

	function handleRunPayroll() {
		goto(`/payroll/run/${periodData.periodEnd}`);
	}

	function getButtonLabel(): string {
		if (!periodData.runStatus) return 'Start Payroll';
		switch (periodData.runStatus) {
			case 'draft':
				return 'Continue';
			case 'pending_approval':
				return 'Review & Approve';
			case 'approved':
			case 'paid':
				return 'View Details';
			default:
				return 'Run Payroll';
		}
	}

	const daysUntilClass = $derived(getDaysUntilClass(periodData.periodEnd));
</script>

<div class="bg-white rounded-xl shadow-md3-1 p-5 transition-shadow duration-150 hover:shadow-md3-2">
	<!-- Header -->
	<div class="flex items-start justify-between mb-4 gap-4 max-md:flex-col">
		<div class="flex items-center gap-3">
			<div
				class="w-11 h-11 rounded-lg bg-primary-100 text-primary-600 flex items-center justify-center text-lg"
			>
				<i class="fas fa-calendar-alt"></i>
			</div>
			<div class="flex flex-col gap-1">
				<h3 class="text-title-small font-semibold text-surface-800 m-0">
					Period End: {formatShortDate(periodData.periodEnd)}
				</h3>
				<div class="flex items-center gap-3 max-md:flex-col max-md:items-start max-md:gap-1">
					<span class="text-auxiliary-text text-surface-500">
						Pay Date: {formatShortDate(periodData.payDate)}
					</span>
					<span class="text-auxiliary-text font-medium px-2 py-1 rounded-sm {daysUntilClass}">
						{getDaysUntil(periodData.periodEnd)}
					</span>
				</div>
			</div>
		</div>
		<div class="flex items-center gap-3 max-md:w-full max-md:justify-between">
			{#if periodData.runStatus}
				<span
					class="inline-flex items-center px-3 py-1 rounded-full text-auxiliary-text font-medium {getStatusClass(
						periodData.runStatus
					)}"
				>
					{PAYROLL_STATUS_LABELS[periodData.runStatus]}
				</span>
			{/if}
			{#if periodData.totalEmployees > 0}
				<button
					class="flex items-center gap-2 px-4 py-2 bg-gradient-to-br from-primary-500 to-secondary-500 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:opacity-90 hover:-translate-y-px"
					onclick={handleRunPayroll}
				>
					{getButtonLabel()}
					<i class="fas fa-arrow-right text-xs"></i>
				</button>
			{/if}
		</div>
	</div>

	<!-- Summary Bar -->
	<div class="flex items-center gap-3 px-4 py-3 bg-surface-50 rounded-lg mb-4 max-md:flex-wrap">
		<span class="flex items-center gap-2 text-body-content text-surface-700">
			<i class="fas fa-layer-group text-surface-500 text-sm"></i>
			{periodData.payGroups.length} Pay Group{periodData.payGroups.length > 1 ? 's' : ''}
		</span>
		<span class="w-px h-4 bg-surface-200"></span>
		<span class="flex items-center gap-2 text-body-content text-surface-700">
			<i class="fas fa-users text-surface-500 text-sm"></i>
			{periodData.totalEmployees} Employee{periodData.totalEmployees > 1 ? 's' : ''}
		</span>
		<span class="w-px h-4 bg-surface-200"></span>
		<span class="flex items-center gap-2 text-body-content font-semibold text-surface-800">
			<i class="fas fa-dollar-sign text-surface-500 text-sm"></i>
			Est. {formatCurrencyNoDecimals(periodData.totalEstimatedGross)}
		</span>
	</div>

	<!-- Pay Groups List -->
	<div class="flex flex-wrap gap-3">
		{#each periodData.payGroups as group (group.id)}
			<div
				class="flex-1 min-w-[200px] max-w-[280px] max-md:max-w-none p-4 rounded-lg border transition-all duration-150 flex flex-col gap-3 hover:shadow-sm
					{group.employeeCount === 0
					? 'border-warning-200 bg-warning-50 hover:border-warning-300'
					: 'border-surface-200 bg-surface-50 hover:border-surface-300'}"
			>
				<!-- Pay Group Name -->
				<div class="flex items-center justify-between">
					<span class="text-body-content font-semibold text-surface-800">{group.name}</span>
				</div>

				<!-- Stats -->
				<div class="flex flex-col gap-2">
					{#if group.employeeCount === 0}
						<span class="flex items-center gap-2 text-auxiliary-text text-warning-700">
							<i class="fas fa-user-slash w-3.5 text-warning-600 text-xs"></i>
							No employees
						</span>
					{:else}
						<span class="flex items-center gap-2 text-auxiliary-text text-surface-600">
							<i class="fas fa-users w-3.5 text-surface-500 text-xs"></i>
							{group.employeeCount} employee{group.employeeCount > 1 ? 's' : ''}
						</span>
						<span class="flex items-center gap-2 text-auxiliary-text text-surface-600">
							<i class="fas fa-dollar-sign w-3.5 text-surface-500 text-xs"></i>
							Est. {formatCurrencyNoDecimals(group.estimatedGross)}
						</span>
					{/if}
				</div>

				<!-- Action Button -->
				{#if onPayGroupClick}
					<button
						class="flex items-center justify-center gap-2 px-3 py-2 rounded-md text-auxiliary-text font-medium cursor-pointer transition-all duration-150 mt-auto
							{group.employeeCount === 0
							? 'bg-warning-100 text-warning-800 border border-warning-300 hover:bg-warning-200'
							: 'bg-primary-50 text-primary-700 border border-primary-200 hover:bg-primary-100 hover:border-primary-300'}"
						onclick={() => onPayGroupClick?.(group)}
						aria-label="Add employees to {group.name}"
					>
						<i class="fas fa-user-plus text-xs"></i>
						Add Employees
					</button>
				{/if}
			</div>
		{/each}
	</div>
</div>
