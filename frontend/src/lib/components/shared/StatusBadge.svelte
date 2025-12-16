<script lang="ts">
	interface Props {
		status: string;
		variant?: 'default' | 'pill';
	}

	let { status, variant = 'default' }: Props = $props();

	function getStatusColor(status: string): string {
		switch (status.toLowerCase()) {
			case 'active':
			case 'paid':
				return 'green';
			case 'draft':
			case 'terminated':
				return 'gray';
			case 'calculating':
			case 'approved':
				return 'blue';
			case 'pending_approval':
			case 'pending':
				return 'yellow';
			case 'cancelled':
			case 'error':
				return 'red';
			default:
				return 'gray';
		}
	}

	const color = $derived(getStatusColor(status));
</script>

<span class="status-badge {color}" class:pill={variant === 'pill'}>
	{status.replace(/_/g, ' ')}
</span>

<style>
	.status-badge {
		display: inline-block;
		padding: var(--spacing-1) var(--spacing-3);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
		text-transform: capitalize;
	}

	.status-badge.pill {
		border-radius: var(--radius-full);
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.status-badge.gray {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.status-badge.blue {
		background: var(--color-primary-100);
		color: var(--color-primary-700);
	}

	.status-badge.yellow {
		background: var(--color-warning-100);
		color: var(--color-warning-700);
	}

	.status-badge.green {
		background: var(--color-success-100);
		color: var(--color-success-700);
	}

	.status-badge.red {
		background: var(--color-error-100);
		color: var(--color-error-700);
	}
</style>
