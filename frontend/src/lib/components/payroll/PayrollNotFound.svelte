<script lang="ts">
	interface Props {
		payDateFormatted: string;
		onBack: () => void;
	}

	let { payDateFormatted, onBack }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center min-h-[400px] text-center">
	<div class="w-20 h-20 rounded-full bg-surface-100 text-surface-400 flex items-center justify-center text-[32px] mb-4">
		<i class="fas fa-calendar-times"></i>
	</div>
	<h2 class="text-title-small font-semibold text-surface-800 m-0 mb-2">Payroll Run Not Found</h2>
	<p class="text-body-content text-surface-600 m-0 mb-6">No payroll run exists for {payDateFormatted}.</p>
	<button
		class="flex items-center gap-2 py-2 px-4 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:opacity-90 hover:-translate-y-px"
		onclick={onBack}
	>
		<i class="fas fa-arrow-left"></i>
		<span>Back to Payroll</span>
	</button>
</div>
