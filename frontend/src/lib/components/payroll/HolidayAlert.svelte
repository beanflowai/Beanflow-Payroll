<script lang="ts">
	import type { Holiday } from '$lib/types/payroll';
	import { formatShortDate } from '$lib/utils/dateUtils';

	interface Props {
		holidays: Holiday[];
		onManageHolidayHours?: () => void;
	}

	let { holidays, onManageHolidayHours }: Props = $props();

	const holidayText = $derived(
		holidays.map((h) => `${h.name} (${formatShortDate(h.date)})`).join(', ')
	);
</script>

{#if holidays.length > 0}
	<div class="holiday-alert">
		<div class="alert-content">
			<i class="fas fa-gift"></i>
			<div class="alert-text">
				<strong>Holidays in this period:</strong>
				{holidayText}
			</div>
		</div>
		{#if onManageHolidayHours}
			<button class="alert-action" onclick={onManageHolidayHours}>
				Manage Holiday Hours
				<i class="fas fa-arrow-right"></i>
			</button>
		{/if}
	</div>
{/if}

<style>
	.holiday-alert {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-xl);
		margin-bottom: var(--spacing-6);
		flex-wrap: wrap;
		gap: var(--spacing-3);
	}

	.alert-content {
		display: flex;
		align-items: center;
		gap: var(--spacing-3);
	}

	.alert-content i {
		font-size: var(--font-size-title-medium);
		color: var(--color-warning-600);
	}

	.alert-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.alert-action {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-warning-600);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.alert-action:hover {
		background: var(--color-warning-700);
	}
</style>
