<script lang="ts">
	import type { PaystubStatus } from '$lib/types/payroll';

	interface Props {
		status: PaystubStatus;
		sentAt?: string;
		onRetry?: () => void;
	}

	let { status, sentAt, onRetry }: Props = $props();

	const statusConfig: Record<
		PaystubStatus,
		{ icon: string; label: string; subtext: string; colorClass: string }
	> = {
		pending: {
			icon: 'fa-clock',
			label: 'Pending',
			subtext: 'Not generated',
			colorClass: 'status-pending'
		},
		sending: {
			icon: 'fa-spinner fa-spin',
			label: 'Sending',
			subtext: 'Sending...',
			colorClass: 'status-sending'
		},
		sent: {
			icon: 'fa-check-circle',
			label: 'Sent',
			subtext: '',
			colorClass: 'status-sent'
		},
		failed: {
			icon: 'fa-exclamation-triangle',
			label: 'Failed',
			subtext: 'Click to retry',
			colorClass: 'status-failed'
		}
	};

	const config = $derived(statusConfig[status]);

	function formatSentTime(isoDate: string): string {
		const date = new Date(isoDate);
		return date.toLocaleDateString('en-CA', {
			month: 'short',
			day: 'numeric',
			hour: 'numeric',
			minute: '2-digit'
		});
	}

	function handleClick() {
		if (status === 'failed' && onRetry) {
			onRetry();
		}
	}
</script>

<div
	class="paystub-status {config.colorClass}"
	class:clickable={status === 'failed' && onRetry}
	onclick={handleClick}
	onkeydown={(e) => e.key === 'Enter' && handleClick()}
	role={status === 'failed' ? 'button' : undefined}
	tabindex={status === 'failed' ? 0 : undefined}
>
	<div class="status-main">
		<i class="fas {config.icon}"></i>
		<span class="status-label">{config.label}</span>
	</div>
	<div class="status-subtext">
		{#if status === 'sent' && sentAt}
			{formatSentTime(sentAt)}
		{:else}
			{config.subtext}
		{/if}
	</div>
</div>

<style>
	.paystub-status {
		display: flex;
		flex-direction: column;
		gap: 2px;
		padding: var(--spacing-1) var(--spacing-2);
		border-radius: var(--radius-md);
		font-size: var(--font-size-auxiliary-text);
		min-width: 90px;
	}

	.paystub-status.clickable {
		cursor: pointer;
	}

	.paystub-status.clickable:hover {
		filter: brightness(0.95);
	}

	.status-main {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		font-weight: var(--font-weight-medium);
	}

	.status-main i {
		font-size: 12px;
	}

	.status-subtext {
		font-size: 11px;
		opacity: 0.8;
		padding-left: 18px;
	}

	/* Status Colors */
	.status-pending {
		background: var(--color-surface-100);
		color: var(--color-surface-600);
	}

	.status-sending {
		background: var(--color-info-50);
		color: var(--color-info-700);
	}

	.status-sent {
		background: var(--color-success-50);
		color: var(--color-success-700);
	}

	.status-failed {
		background: var(--color-danger-50);
		color: var(--color-danger-700);
	}
</style>
