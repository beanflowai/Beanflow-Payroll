<script lang="ts">
	/**
	 * PortalStatusBadge - Shows employee portal access status
	 * Used in employee list table
	 */
	import type { PortalStatus } from '$lib/types/employee-portal';

	interface Props {
		status: PortalStatus;
	}

	let { status }: Props = $props();

	const statusConfig = {
		not_set: { icon: '➖', label: 'Not set', class: 'not-set' },
		invited: { icon: '⏳', label: 'Invited', class: 'invited' },
		active: { icon: '✅', label: 'Active', class: 'active' },
		disabled: { icon: '🚫', label: 'Disabled', class: 'disabled' }
	};

	const config = $derived(statusConfig[status]);
</script>

<span class="portal-status-badge {config.class}">
	<span class="status-icon">{config.icon}</span>
	<span class="status-label">{config.label}</span>
</span>

<style>
	.portal-status-badge {
		display: inline-flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: var(--spacing-1) var(--spacing-2);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		border-radius: var(--radius-sm);
	}

	.status-icon {
		font-size: 12px;
	}

	.portal-status-badge.not-set {
		background: var(--color-surface-100);
		color: var(--color-surface-500);
	}

	.portal-status-badge.invited {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.portal-status-badge.active {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.portal-status-badge.disabled {
		background: var(--color-error-100);
		color: var(--color-error-700);
	}
</style>
