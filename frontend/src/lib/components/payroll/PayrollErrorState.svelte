<script lang="ts">
	interface Props {
		error: string;
		onRetry: () => void;
	}

	let { error, onRetry }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center min-h-[400px] text-center">
	<div class="w-20 h-20 rounded-full bg-error-100 text-error-600 flex items-center justify-center text-[32px] mb-4">
		<i class="fas fa-exclamation-triangle"></i>
	</div>
	<h2 class="text-title-small font-semibold text-surface-800 m-0 mb-2">Error Loading Payroll Run</h2>
	<p class="text-body-content text-surface-600 m-0 mb-6">{error}</p>
	<button
		class="flex items-center gap-2 py-2 px-4 bg-gradient-to-br from-primary-600 to-secondary-600 text-white border-none rounded-lg text-body-content font-medium cursor-pointer transition-all duration-150 hover:opacity-90 hover:-translate-y-px"
		onclick={onRetry}
	>
		<i class="fas fa-redo"></i>
		<span>Try Again</span>
	</button>
</div>
