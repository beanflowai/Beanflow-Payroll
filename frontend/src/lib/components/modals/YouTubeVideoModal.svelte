<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	interface Props {
		isOpen: boolean;
		videoId: string;
		title?: string;
		onClose: () => void;
	}

	let { isOpen, videoId, title = 'Video Tutorial', onClose }: Props = $props();

	// Handle escape key press
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && isOpen) {
			onClose();
		}
	}

	// Add/remove event listener for escape key
	onMount(() => {
		if (browser) {
			window.addEventListener('keydown', handleKeydown);
		}
	});

	onDestroy(() => {
		if (browser) {
			window.removeEventListener('keydown', handleKeydown);
		}
	});

	function handleBackdropClick(event: MouseEvent) {
		if (event.target === event.currentTarget) {
			onClose();
		}
	}

	// Generate YouTube embed URL with better quality parameters
	const embedUrl = $derived(
		videoId
			? `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0&modestbranding=1&playsinline=0&fs=1`
			: ''
	);
</script>

{#if isOpen && videoId}
	<div class="modal-backdrop" onclick={handleBackdropClick}>
		<div class="modal-content">
			<div class="modal-header">
				<button class="close-button" onclick={onClose} aria-label="Close video">
					<i class="fas fa-times"></i>
				</button>
			</div>
			<div class="video-container">
				<iframe
					src={embedUrl}
					title={title}
					class="video-iframe"
					allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
					allowfullscreen
				></iframe>
			</div>
		</div>
	</div>
{/if}

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.75);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 9999;
		padding: var(--spacing-4);
		animation: fadeIn 0.2s ease-out;
	}

	.modal-content {
		background: white;
		border-radius: var(--radius-xl);
		max-width: 1400px;
		width: 80%;
		box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
		animation: slideUp 0.3s ease-out;
		overflow: hidden;
	}

	.modal-header {
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding: var(--spacing-3);
		position: absolute;
		top: 0;
		right: 0;
		z-index: 10;
	}

	.close-button {
		width: 36px;
		height: 36px;
		border: none;
		background: rgba(0, 0, 0, 0.6);
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		cursor: pointer;
		color: white;
		transition: all 0.2s ease;
		font-size: 18px;
	}

	.close-button:hover {
		background: rgba(0, 0, 0, 0.8);
		transform: scale(1.1);
	}

	.video-container {
		position: relative;
		padding-bottom: 56.25%; /* 16:9 aspect ratio */
		height: 0;
		background: black;
	}

	.video-iframe {
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		border: none;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes slideUp {
		from {
			opacity: 0;
			transform: translateY(20px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}

	@media (max-width: 768px) {
		.modal-content {
			max-width: 100%;
			width: 95%;
			border-radius: var(--radius-lg);
		}

		.modal-header {
			padding: var(--spacing-2);
		}

		.close-button {
			width: 32px;
			height: 32px;
			font-size: 16px;
		}
	}
</style>
