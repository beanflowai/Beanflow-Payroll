<script lang="ts">
	import type { LeaveType } from '$lib/types/payroll';
	import { LEAVE_TYPE_LABELS } from '$lib/types/payroll';

	interface Props {
		type: LeaveType;
		hours: number;
		compact?: boolean; // true = "8h VAC", false = "8 hours Vacation"
	}

	let { type, hours, compact = false }: Props = $props();

	const label = $derived(LEAVE_TYPE_LABELS[type]);
	const displayText = $derived(
		compact ? `${hours}h ${label.short}` : `${hours} hours ${label.full}`
	);
</script>

<span class="leave-badge" class:vacation={type === 'vacation'} class:sick={type === 'sick'}>
	{#if !compact}
		<span class="icon">{label.icon}</span>
	{/if}
	<span class="text">{displayText}</span>
</span>

<style>
	.leave-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		white-space: nowrap;
	}

	.leave-badge.vacation {
		background: var(--color-info-50, #eff6ff);
		color: var(--color-info-700, #1d4ed8);
	}

	.leave-badge.sick {
		background: var(--color-warning-50, #fff7ed);
		color: var(--color-warning-700, #c2410c);
	}

	.icon {
		font-size: var(--font-size-body-content);
	}

	.text {
		line-height: 1;
	}
</style>
