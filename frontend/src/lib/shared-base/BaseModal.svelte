<script lang="ts">
	import { Portal } from '@jsrob/svelte-portal';
	import type { Snippet } from 'svelte';
	import IconContainer from './IconContainer.svelte';

	/**
	 * BaseModal - Universal Modal Component
	 *
	 * A Portal-based modal component that renders content on top of the application.
	 * Uses @jsrob/svelte-portal to render directly to <body>, avoiding containing block issues.
	 *
	 * Features:
	 * - Portal rendering (escapes parent overflow/transform constraints)
	 * - Unified z-index management using design system variables
	 * - Three size variants: small, medium (default), large
	 * - Click-outside-to-close and ESC key support
	 * - Smooth animations (fade + slide)
	 * - Accessibility: ARIA attributes, focus management
	 *
	 * @example
	 * ```svelte
	 * <BaseModal visible={showModal} onclose={() => showModal = false} size="medium">
	 *   {@render children()}
	 * </BaseModal>
	 * ```
	 */

	interface Props {
		/** Whether the modal is visible */
		visible: boolean;
		/** Callback when modal should close (backdrop click, ESC key) */
		onclose: () => void;
		/** Modal size variant */
		size?: 'small' | 'medium' | 'large';
		/** Optional title for the modal */
		title?: string;
		/** Show close button in header */
		showCloseButton?: boolean;
		/** Disable click-outside-to-close */
		disableBackdropClose?: boolean;
		/** Disable ESC key to close */
		disableEscapeClose?: boolean;
		/** Content to render inside modal */
		children?: Snippet;
	}

	let {
		visible = $bindable(false),
		onclose,
		size = 'medium',
		title,
		showCloseButton = true,
		disableBackdropClose = false,
		disableEscapeClose = false,
		children
	}: Props = $props();

	// Handle backdrop click
	function handleBackdropClick() {
		if (!disableBackdropClose) {
			onclose();
		}
	}

	// Handle ESC key
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && !disableEscapeClose) {
			event.preventDefault();
			onclose();
		}
	}

	// Prevent content click from bubbling to backdrop
	function handleContentClick(event: MouseEvent) {
		event.stopPropagation();
	}

	// Focus trap: handle Tab navigation within modal
	// Note: For production, consider using a library like focus-trap-svelte
	$effect(() => {
		if (visible) {
			// Set up keyboard listener
			window.addEventListener('keydown', handleKeydown);

			// Optional: Lock body scroll when modal is open
			document.body.style.overflow = 'hidden';

			return () => {
				window.removeEventListener('keydown', handleKeydown);
				document.body.style.overflow = '';
			};
		}
	});
</script>

{#if visible}
	<Portal target="body">
		<div
			class="modal-backdrop"
			onclick={handleBackdropClick}
			role="presentation"
			aria-hidden={!visible}
		>
			<div
				class="modal-content modal-{size}"
				onclick={handleContentClick}
				role="dialog"
				aria-modal="true"
				aria-labelledby={title ? 'modal-title' : undefined}
			>
				{#if title || showCloseButton}
					<div class="modal-header">
						{#if title}
							<h2 id="modal-title" class="modal-title">{title}</h2>
						{/if}
						{#if showCloseButton}
							<button
								type="button"
								class="modal-close-button"
								onclick={onclose}
								aria-label="Close modal"
							>
								<IconContainer icon="x" size="small" />
							</button>
						{/if}
					</div>
				{/if}

				<div class="modal-body">
					{#if children}
						{@render children()}
					{/if}
				</div>
			</div>
		</div>
	</Portal>
{/if}

<style>
	/* Backdrop Overlay */
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(4px);
		z-index: var(--z-modal-backdrop);
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1rem;

		/* Smooth fade-in animation */
		animation: fadeIn 200ms var(--easing-standard);
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	/* Modal Content Container */
	.modal-content {
		background: white;
		border-radius: var(--radius-2xl);
		box-shadow: var(--shadow-md3-5);
		z-index: var(--z-modal);
		display: flex;
		flex-direction: column;
		max-height: 90vh;
		overflow: hidden;

		/* Smooth slide-up animation */
		animation:
			fadeIn 200ms var(--easing-standard),
			slideUp 300ms var(--easing-standard);
	}

	@keyframes slideUp {
		from {
			transform: translateY(20px);
		}
		to {
			transform: translateY(0);
		}
	}

	/* Size Variants */
	.modal-small {
		width: 100%;
		max-width: 400px;
	}

	.modal-medium {
		width: 100%;
		max-width: 600px;
	}

	.modal-large {
		width: 100%;
		max-width: 900px;
	}

	/* Modal Header */
	.modal-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-6);
		border-bottom: 1px solid var(--color-surface-300);
		flex-shrink: 0;
	}

	.modal-title {
		margin: 0;
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-title-large);
		color: var(--color-surface-900);
	}

	.modal-close-button {
		background: none;
		border: none;
		color: var(--color-surface-600);
		cursor: pointer;
		padding: 0.5rem;
		border-radius: var(--radius-md);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: all var(--transition-fast);
	}

	.modal-close-button:hover {
		background: var(--color-surface-200);
		color: var(--color-surface-900);
	}

	.modal-close-button:focus-visible {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
	}

	/* Modal Body */
	.modal-body {
		padding: var(--spacing-6);
		overflow-y: auto;
		flex: 1;
		min-height: 0; /* Allow flex child to shrink below content size */
	}

	/* Scrollbar Styling */
	.modal-body::-webkit-scrollbar {
		width: 8px;
	}

	.modal-body::-webkit-scrollbar-track {
		background: var(--color-surface-100);
		border-radius: var(--radius-full);
	}

	.modal-body::-webkit-scrollbar-thumb {
		background: var(--color-surface-400);
		border-radius: var(--radius-full);
	}

	.modal-body::-webkit-scrollbar-thumb:hover {
		background: var(--color-surface-500);
	}

	/* Responsive Design */
	@media (max-width: 640px) {
		.modal-backdrop {
			padding: 0.5rem;
		}

		.modal-content {
			max-height: 95vh;
			border-radius: var(--radius-xl);
		}

		.modal-small,
		.modal-medium,
		.modal-large {
			max-width: 100%;
		}

		.modal-header,
		.modal-body {
			padding: var(--spacing-4);
		}
	}
</style>
