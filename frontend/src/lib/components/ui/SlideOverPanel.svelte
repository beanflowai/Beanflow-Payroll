<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		isOpen: boolean;
		title: string;
		width?: 'sm' | 'md' | 'lg';
		onClose: () => void;
		children: Snippet;
		footer?: Snippet;
	}

	let { isOpen, title, width = 'md', onClose, children, footer }: Props = $props();

	// Width classes
	const widthClasses = {
		sm: 'w-80', // 320px
		md: 'w-[400px]',
		lg: 'w-[500px]'
	};

	// Handle escape key
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && isOpen) {
			onClose();
		}
	}

	// Handle backdrop click
	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			onClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isOpen}
	<!-- Backdrop -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<div
		class="fixed inset-0 bg-black/50 z-[1000] transition-opacity duration-300"
		onclick={handleBackdropClick}
	>
		<!-- Panel -->
		<div
			class="fixed top-0 right-0 h-full bg-white shadow-xl flex flex-col transition-transform duration-300 ease-out
				{widthClasses[width]}
				max-sm:w-full"
		>
			<!-- Header -->
			<div class="flex items-center justify-between px-5 py-4 border-b border-surface-100 shrink-0">
				<h2 class="text-title-small font-semibold text-surface-800 m-0">{title}</h2>
				<button
					type="button"
					class="w-8 h-8 flex items-center justify-center rounded-md text-surface-500 hover:bg-surface-100 hover:text-surface-700 transition-colors cursor-pointer border-none bg-transparent"
					onclick={onClose}
					aria-label="Close panel"
				>
					<i class="fas fa-times"></i>
				</button>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto px-5 py-4">
				{@render children()}
			</div>

			<!-- Footer (optional) -->
			{#if footer}
				<div class="shrink-0 px-5 py-4 border-t border-surface-100 bg-surface-50">
					{@render footer()}
				</div>
			{/if}
		</div>
	</div>
{/if}
