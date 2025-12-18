<script lang="ts">
	interface Props {
		variant: 'info' | 'warning';
		message: string;
	}

	let { variant, message }: Props = $props();
</script>

{#if variant === 'warning'}
	<div class="flex items-center gap-3 p-4 bg-warning-50 rounded-lg text-warning-700 text-body-content mt-6 border border-warning-200">
		<i class="fas fa-exclamation-triangle text-lg text-warning-500"></i>
		<span>{message}</span>
	</div>
{:else}
	<div class="flex items-center gap-3 p-4 bg-primary-50 rounded-lg text-primary-700 text-body-content mt-6">
		<i class="fas fa-info-circle text-lg"></i>
		<span>{message}</span>
	</div>
{/if}
