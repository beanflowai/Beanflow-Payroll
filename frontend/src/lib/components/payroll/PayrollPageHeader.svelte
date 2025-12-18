<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		payDateFormatted: string;
		payGroupCount: number;
		employeeCount: number;
		onBack: () => void;
		actions: Snippet;
	}

	let { payDateFormatted, payGroupCount, employeeCount, onBack, actions }: Props = $props();
</script>

<header class="mb-6">
	<button
		class="inline-flex items-center gap-2 py-2 bg-transparent border-none text-body-content font-medium text-primary-600 cursor-pointer mb-4 transition-all duration-150 hover:text-primary-700"
		onclick={onBack}
	>
		<i class="fas fa-arrow-left text-xs"></i>
		<span>Back to Payroll</span>
	</button>

	<div class="flex items-start justify-between flex-wrap gap-4 max-md:flex-col">
		<div>
			<h1 class="text-headline-minimum font-semibold text-surface-800 m-0 mb-1">Pay Date: {payDateFormatted}</h1>
			<p class="text-body-content text-surface-600 m-0">
				{payGroupCount} Pay Group{payGroupCount > 1 ? 's' : ''}
				&middot;
				{employeeCount} Employee{employeeCount > 1 ? 's' : ''}
			</p>
		</div>
		<div class="flex items-center gap-3 flex-wrap max-md:w-full">
			{@render actions()}
		</div>
	</div>
</header>
