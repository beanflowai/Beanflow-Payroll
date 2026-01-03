<script lang="ts">
	// PayGroupDeleteModal - Delete confirmation modal
	import type { PayGroup } from '$lib/types/pay-group';

	interface Props {
		payGroup: PayGroup;
		onClose: () => void;
		onConfirm: () => void;
	}

	let { payGroup, onClose, onConfirm }: Props = $props();

	let isDeleting = $state(false);

	function handleDelete() {
		isDeleting = true;
		// Simulate delete delay
		setTimeout(() => {
			isDeleting = false;
			onConfirm();
		}, 300);
	}

	function handleOverlayClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			onClose();
		}
	}
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-overlay" onclick={handleOverlayClick} role="presentation">
	<div class="modal" role="dialog" aria-modal="true" aria-labelledby="modal-title" tabindex="-1">
		<div class="modal-header">
			<h2 id="modal-title" class="modal-title">Delete Pay Group</h2>
			<button class="close-button" onclick={onClose} aria-label="Close">
				<i class="fas fa-times"></i>
			</button>
		</div>

		<div class="modal-body">
			<div class="icon-container">
				<i class="fas fa-trash"></i>
			</div>

			<h3 class="confirm-title">Delete "{payGroup.name}"?</h3>

			<p class="confirm-text">
				This will permanently delete this pay group and all its policy configurations.
			</p>

			<div class="warning-box">
				<i class="fas fa-exclamation-triangle"></i>
				<div class="warning-content">
					<strong>Important</strong>
					<p>Before deleting this pay group:</p>
					<ul>
						<li>Ensure no employees are assigned to this group</li>
						<li>Employees in this group will need to be reassigned first</li>
					</ul>
					<p>
						This action cannot be undone.
					</p>
				</div>
			</div>
		</div>

		<div class="modal-footer">
			<button class="btn-secondary" onclick={onClose} disabled={isDeleting}>Cancel</button>
			<button class="btn-destructive" onclick={handleDelete} disabled={isDeleting}>
				{#if isDeleting}
					<i class="fas fa-spinner fa-spin"></i>
					<span>Deleting...</span>
				{:else}
					<span>Delete Group</span>
				{/if}
			</button>
		</div>
	</div>
</div>

<style>
	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		padding: var(--spacing-4);
	}

	.modal {
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-3);
		width: 100%;
		max-width: 450px;
		overflow: hidden;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-5) var(--spacing-6);
		border-bottom: 1px solid var(--color-surface-100);
	}

	.modal-title {
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0;
	}

	.close-button {
		width: 32px;
		height: 32px;
		border: none;
		background: none;
		color: var(--color-surface-500);
		border-radius: var(--radius-md);
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: var(--transition-fast);
	}

	.close-button:hover {
		background: var(--color-surface-100);
		color: var(--color-surface-700);
	}

	.modal-body {
		padding: var(--spacing-6);
		text-align: center;
	}

	.icon-container {
		width: 64px;
		height: 64px;
		border-radius: var(--radius-full);
		background: var(--color-error-100);
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 28px;
		color: var(--color-error-500);
		margin: 0 auto var(--spacing-4);
	}

	.confirm-title {
		font-size: var(--font-size-title-medium);
		font-weight: var(--font-weight-semibold);
		color: var(--color-surface-800);
		margin: 0 0 var(--spacing-3);
	}

	.confirm-text {
		font-size: var(--font-size-body-content);
		color: var(--color-surface-600);
		margin: 0 0 var(--spacing-4);
	}

	.warning-box {
		display: flex;
		gap: var(--spacing-3);
		padding: var(--spacing-4);
		background: var(--color-warning-50);
		border: 1px solid var(--color-warning-200);
		border-radius: var(--radius-lg);
		text-align: left;
	}

	.warning-box > i {
		color: var(--color-warning-500);
		font-size: 18px;
		margin-top: 2px;
		flex-shrink: 0;
	}

	.warning-content {
		flex: 1;
	}

	.warning-content strong {
		display: block;
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-semibold);
		color: var(--color-warning-700);
		margin-bottom: var(--spacing-2);
	}

	.warning-content p {
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
		margin: 0 0 var(--spacing-2);
	}

	.warning-content ul {
		margin: 0 0 var(--spacing-2);
		padding-left: var(--spacing-4);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-700);
	}

	.warning-content ul li {
		margin-bottom: var(--spacing-1);
	}

	.modal-footer {
		display: flex;
		justify-content: center;
		gap: var(--spacing-3);
		padding: var(--spacing-4) var(--spacing-6);
		border-top: 1px solid var(--color-surface-100);
		background: var(--color-surface-50);
	}

	/* Buttons */
	.btn-secondary,
	.btn-destructive {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: var(--spacing-2);
		padding: var(--spacing-3) var(--spacing-5);
		border: none;
		border-radius: var(--radius-lg);
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		cursor: pointer;
		transition: var(--transition-fast);
	}

	.btn-secondary {
		background: white;
		color: var(--color-surface-700);
		border: 1px solid var(--color-surface-200);
	}

	.btn-secondary:hover:not(:disabled) {
		background: var(--color-surface-50);
		border-color: var(--color-surface-300);
	}

	.btn-secondary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-destructive {
		background: var(--color-error-500);
		color: white;
		box-shadow: var(--shadow-md3-1);
	}

	.btn-destructive:hover:not(:disabled) {
		background: var(--color-error-600);
	}

	.btn-destructive:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	@media (max-width: 640px) {
		.modal-footer {
			flex-direction: column;
		}

		.modal-footer button {
			width: 100%;
		}
	}
</style>
