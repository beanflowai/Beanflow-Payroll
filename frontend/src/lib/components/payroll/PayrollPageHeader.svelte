<script lang="ts">
	import type { Snippet } from 'svelte';
	import PayDatePicker from './PayDatePicker.svelte';

	interface Props {
		payDate: string; // YYYY-MM-DD format
		periodEnd: string; // YYYY-MM-DD format
		province?: string; // Province code
		payDateFormatted: string;
		payGroupCount: number;
		employeeCount: number;
		onBack: () => void;
		onPayDateChange?: (newPayDate: string) => Promise<void>;
		actions: Snippet;
		isReadOnly?: boolean; // If true, don't show edit functionality
	}

	let {
		payDate,
		periodEnd,
		province = 'SK',
		payDateFormatted,
		payGroupCount,
		employeeCount,
		onBack,
		onPayDateChange,
		actions,
		isReadOnly = false
	}: Props = $props();

	let isUpdating = $state(false);

	async function handlePayDateSave(newPayDate: string) {
		if (onPayDateChange) {
			isUpdating = true;
			try {
				await onPayDateChange(newPayDate);
			} finally {
				isUpdating = false;
			}
		}
	}

	function handlePayDateCancel() {
		// Just close edit mode, parent component doesn't need notification
	}
</script>

<header class="mb-6">
	<button
		class="inline-flex items-center gap-2 py-2 bg-transparent border-none text-body-content font-medium text-primary-600 cursor-pointer mb-4 transition-all duration-150 hover:text-primary-700"
		onclick={onBack}
		type="button"
	>
		<i class="fas fa-arrow-left text-xs"></i>
		<span>Back to Payroll</span>
	</button>

	<div class="flex items-start justify-between flex-wrap gap-4 max-md:flex-col">
		<div class="flex-1">
			{#if isReadOnly || !onPayDateChange}
				<!-- Read-only mode (original behavior) -->
				<div>
					<h1 class="text-headline-minimum font-semibold text-surface-800 m-0 mb-1">
						Pay Date: {payDateFormatted}
					</h1>
					<p class="text-body-content text-surface-600 m-0">
						{payGroupCount} Pay Group{payGroupCount > 1 ? 's' : ''}
						&middot;
						{employeeCount} Employee{employeeCount > 1 ? 's' : ''}
					</p>
				</div>
			{:else}
				<!-- Editable mode with PayDatePicker -->
				<PayDatePicker
					value={payDate}
					periodEnd={periodEnd}
					province={province}
					onValueChange={() => {}}
					onSave={handlePayDateSave}
					onCancel={handlePayDateCancel}
				/>
				<p class="text-body-content text-surface-600 m-0 mt-2">
					{payGroupCount} Pay Group{payGroupCount > 1 ? 's' : ''}
					&middot;
					{employeeCount} Employee{employeeCount > 1 ? 's' : ''}
				</p>
			{/if}
		</div>
		<div class="flex items-center gap-3 flex-wrap max-md:w-full">
			{@render actions()}
		</div>
	</div>
</header>

<style>
	/* Text color tokens */
	.text-headline-minimum {
		font-size: 1.25rem;
		line-height: 1.75rem;
	}

	.text-surface-800 {
		color: #1e293b;
	}

	.text-surface-600 {
		color: #475569;
	}

	.text-primary-600 {
		color: #0369a1;
	}

	.hover\:text-primary-700:hover {
		color: #075985;
	}

	.text-body-content {
		font-size: 0.875rem;
		line-height: 1.25rem;
	}
</style>
