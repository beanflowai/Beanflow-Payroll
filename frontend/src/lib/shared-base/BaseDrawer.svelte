<script lang="ts">
	import { Portal } from '@jsrob/svelte-portal';
	import type { Snippet } from 'svelte';
	import IconContainer from './IconContainer.svelte';

	/**
	 * BaseDrawer - Right-Side Drawer Modal Component
	 *
	 * A Portal-based drawer component that slides in from the right side of the screen.
	 * Uses @jsrob/svelte-portal to render directly to <body>, avoiding containing block issues.
	 *
	 * Features:
	 * - Portal rendering (escapes parent overflow/transform constraints)
	 * - Slide-in animation from right
	 * - Configurable width (default: 800px)
	 * - Click-outside-to-close and ESC key support
	 * - Full-height drawer (100vh)
	 * - Accessibility: ARIA attributes, focus management
	 * - Body scroll locking when drawer is open
	 *
	 * @example
	 * ```svelte
	 * <BaseDrawer
	 *   visible={isDrawerOpen}
	 *   onclose={() => isDrawerOpen = false}
	 *   title="New Transaction"
	 *   width="900px"
	 * >
	 *   <YourContent />
	 * </BaseDrawer>
	 * ```
	 */

	interface Props {
		/** Whether the drawer is visible */
		visible: boolean;
		/** Callback when drawer should close (backdrop click, ESC key) */
		onclose: () => void;
		/** Drawer width (CSS value, e.g., "800px", "40%") */
		width?: string;
		/** Optional title for the drawer header */
		title?: string;
		/** Show close button in header */
		showCloseButton?: boolean;
		/** Disable click-outside-to-close */
		disableBackdropClose?: boolean;
		/** Disable ESC key to close */
		disableEscapeClose?: boolean;
		/** Side to slide in from ("left" or "right") */
		side?: 'left' | 'right';
		/** Content to render inside drawer */
		children?: Snippet;
	}

	let {
		visible = $bindable(false),
		onclose,
		width = '800px',
		title,
		showCloseButton = true,
		disableBackdropClose = false,
		disableEscapeClose = false,
		side = 'right',
		children
	}: Props = $props();

	let drawerElement: HTMLElement | null = $state(null);

	// Handle backdrop click
	function handleBackdropClick() {
		if (!disableBackdropClose) {
			onclose();
		}
	}

	// Handle ESC key and Focus Trap
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && !disableEscapeClose) {
			event.preventDefault();
			onclose();
			return;
		}

		// Focus trap: keep Tab/Shift+Tab within drawer
		if (event.key === 'Tab' && visible && drawerElement) {
			const focusableElements = drawerElement.querySelectorAll<HTMLElement>(
				'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
			);

			if (focusableElements.length === 0) return;

			const firstElement = focusableElements[0];
			const lastElement = focusableElements[focusableElements.length - 1];

			if (event.shiftKey) {
				// Shift+Tab at first element → focus last element
				if (document.activeElement === firstElement) {
					event.preventDefault();
					lastElement.focus();
				}
			} else {
				// Tab at last element → focus first element
				if (document.activeElement === lastElement) {
					event.preventDefault();
					firstElement.focus();
				}
			}
		}
	}

	// Prevent content click from bubbling to backdrop
	function handleContentClick(event: MouseEvent) {
		event.stopPropagation();
	}

	// Body scroll locking, keyboard listener, and auto-focus
	$effect(() => {
		if (visible) {
			// Set up keyboard listener
			window.addEventListener('keydown', handleKeydown);

			// Lock body scroll when drawer is open
			document.body.style.overflow = 'hidden';

			// Auto-focus first focusable element when drawer opens
			setTimeout(() => {
				if (drawerElement) {
					const firstFocusable = drawerElement.querySelector<HTMLElement>(
						'input:not([disabled]):not([type="hidden"]), textarea:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"]):not([disabled])'
					);
					if (firstFocusable) {
						firstFocusable.focus();
					}
				}
			}, 150); // Wait for slide animation

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
			class="drawer-backdrop"
			onclick={handleBackdropClick}
			role="presentation"
			aria-hidden={!visible}
		>
			<div
				bind:this={drawerElement}
				class="drawer-content drawer-{side}"
				style="width: {width}; max-width: 90vw;"
				onclick={handleContentClick}
				role="dialog"
				aria-modal="true"
				aria-labelledby={title ? 'drawer-title' : undefined}
				tabindex="-1"
			>
				{#if title || showCloseButton}
					<div class="drawer-header">
						{#if title}
							<h2 id="drawer-title" class="drawer-title">{title}</h2>
						{/if}
						{#if showCloseButton}
							<button
								type="button"
								class="drawer-close-button"
								onclick={onclose}
								aria-label="Close drawer"
							>
								<IconContainer icon="x" size="small" />
							</button>
						{/if}
					</div>
				{/if}

				<div class="drawer-body">
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
	.drawer-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(4px);
		z-index: var(--z-modal-backdrop);

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

	/* Drawer Content Container */
	.drawer-content {
		position: fixed;
		top: 0;
		bottom: 0;
		background: white;
		box-shadow: var(--shadow-md3-5);
		z-index: var(--z-modal);
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	/* Right-side drawer */
	.drawer-right {
		right: 0;
		/* Smooth slide-in animation from right */
		animation:
			fadeIn 200ms var(--easing-standard),
			slideInRight 300ms var(--easing-standard);
	}

	@keyframes slideInRight {
		from {
			transform: translateX(100%);
		}
		to {
			transform: translateX(0);
		}
	}

	/* Left-side drawer */
	.drawer-left {
		left: 0;
		/* Smooth slide-in animation from left */
		animation:
			fadeIn 200ms var(--easing-standard),
			slideInLeft 300ms var(--easing-standard);
	}

	@keyframes slideInLeft {
		from {
			transform: translateX(-100%);
		}
		to {
			transform: translateX(0);
		}
	}

	/* Drawer Header */
	.drawer-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: var(--spacing-6);
		border-bottom: 1px solid var(--color-surface-300);
		flex-shrink: 0;
		background: white;
	}

	.drawer-title {
		margin: 0;
		font-size: var(--font-size-title-large);
		font-weight: var(--font-weight-title-large);
		color: var(--color-surface-900);
	}

	.drawer-close-button {
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

	.drawer-close-button:hover {
		background: var(--color-surface-200);
		color: var(--color-surface-900);
	}

	.drawer-close-button:focus-visible {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
	}

	/* Drawer Body */
	.drawer-body {
		padding: var(--spacing-6);
		overflow-y: scroll; /* Always show scrollbar to prevent layout shift */
		scrollbar-gutter: stable; /* Reserve space for scrollbar, avoid width changes */
		flex: 1;
		min-height: 0; /* Allow flex child to shrink below content size */
	}

	/* Scrollbar Styling */
	.drawer-body::-webkit-scrollbar {
		width: 8px;
	}

	.drawer-body::-webkit-scrollbar-track {
		background: var(--color-surface-100);
		border-radius: var(--radius-full);
	}

	.drawer-body::-webkit-scrollbar-thumb {
		background: var(--color-surface-400);
		border-radius: var(--radius-full);
	}

	.drawer-body::-webkit-scrollbar-thumb:hover {
		background: var(--color-surface-500);
	}

	/* Responsive Design */
	@media (max-width: 1024px) {
		.drawer-content {
			width: 60% !important;
			max-width: none !important;
		}
	}

	@media (max-width: 768px) {
		.drawer-content {
			width: 80% !important;
			max-width: none !important;
		}
	}

	@media (max-width: 640px) {
		.drawer-content {
			width: 100% !important;
			max-width: none !important;
		}

		.drawer-header,
		.drawer-body {
			padding: var(--spacing-4);
		}
	}
</style>
