<script lang="ts">
	import type { LeaveEntry } from '$lib/types/payroll';
	import { LEAVE_TYPE_LABELS } from '$lib/types/payroll';

	interface Props {
		leaveEntries: LeaveEntry[];
		onManageLeaveHours: () => void;
	}

	let { leaveEntries, onManageLeaveHours }: Props = $props();

	// Group entries by employee
	const employeeSummaries = $derived(() => {
		const byEmployee = new Map<string, { name: string; entries: LeaveEntry[] }>();

		for (const entry of leaveEntries) {
			if (!byEmployee.has(entry.employeeId)) {
				byEmployee.set(entry.employeeId, { name: entry.employeeName, entries: [] });
			}
			byEmployee.get(entry.employeeId)!.entries.push(entry);
		}

		return Array.from(byEmployee.values()).map(({ name, entries }) => {
			const parts = entries.map(
				(e) => `${e.hours}h ${LEAVE_TYPE_LABELS[e.leaveType].short.toLowerCase()}`
			);
			return `${name} (${parts.join(', ')})`;
		});
	});

	const summaryText = $derived(employeeSummaries().join(', '));
	const employeeCount = $derived(new Set(leaveEntries.map((e) => e.employeeId)).size);
</script>

{#if leaveEntries.length > 0}
	<div class="leave-alert">
		<div class="alert-content">
			<span class="alert-icon">🏖️</span>
			<div class="alert-text">
				<strong>{employeeCount} employee{employeeCount > 1 ? 's have' : ' has'} leave recorded</strong>
				<span class="alert-details">{summaryText}</span>
			</div>
		</div>
		<button class="alert-action" onclick={onManageLeaveHours}>
			Manage Leave Hours
			<i class="fas fa-arrow-right"></i>
		</button>
	</div>
{/if}

<style>
	.leave-alert {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-4) var(--spacing-5);
		background: var(--color-info-50, #eff6ff);
		border: 1px solid var(--color-info-200, #bfdbfe);
		border-radius: var(--radius-xl);
		margin-bottom: var(--spacing-6);
		flex-wrap: wrap;
		gap: var(--spacing-3);
	}

	.alert-content {
		display: flex;
		align-items: flex-start;
		gap: var(--spacing-3);
	}

	.alert-icon {
		font-size: var(--font-size-title-medium);
	}

	.alert-text {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		font-size: var(--font-size-body-content);
		color: var(--color-surface-700);
	}

	.alert-details {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
	}

	.alert-action {
		display: flex;
		align-items: center;
		gap: var(--spacing-2);
		padding: var(--spacing-2) var(--spacing-4);
		background: var(--color-info-600, #2563eb);
		color: white;
		border: none;
		border-radius: var(--radius-md);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.alert-action:hover {
		background: var(--color-info-700, #1d4ed8);
	}
</style>
