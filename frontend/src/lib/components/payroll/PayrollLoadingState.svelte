<script lang="ts">
	interface Props {
		message?: string;
	}

	let { message = 'Loading payroll run...' }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center min-h-[400px] text-center">
	<div class="w-12 h-12 border-4 border-surface-200 border-t-primary-500 rounded-full animate-spin mb-4"></div>
	<p class="text-body-content text-surface-600">{message}</p>
</div>
