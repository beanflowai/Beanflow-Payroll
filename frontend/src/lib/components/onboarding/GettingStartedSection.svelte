<script lang="ts">
	import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';
	import type { OnboardingProgress } from '$lib/types/onboarding';
	import YouTubeVideoModal from '$lib/components/modals/YouTubeVideoModal.svelte';

	interface Props {
		progress: OnboardingProgress;
	}

	let { progress }: Props = $props();

	// Video modal state
	let isModalOpen = $state(false);
	let selectedVideoId = $state('');
	let selectedVideoTitle = $state('');

	// Filter steps that have a video
	const availableSteps = $derived(
		ONBOARDING_STEPS.filter((step) => step.youtubeVideoId)
	);

	// Find the first incomplete step (recommended)
	const recommendedStepId = $derived(
		ONBOARDING_STEPS.find(s => !progress.completedSteps.includes(s.id))?.id ?? null
	);

	function handleVideoClick(step: (typeof ONBOARDING_STEPS)[0]) {
		if (step.youtubeVideoId) {
			selectedVideoId = step.youtubeVideoId;
			selectedVideoTitle = step.title;
			isModalOpen = true;
		}
	}

	function handleCloseModal() {
		isModalOpen = false;
		selectedVideoId = '';
		selectedVideoTitle = '';
	}
</script>

<section class="section getting-started-section">
	<h2 class="section-title">Getting Started</h2>
	<p class="section-subtitle">Watch these tutorials to learn how to use BeanFlow Payroll</p>
	<div class="video-grid">
		{#each availableSteps as step}
			{@const isCompleted = progress.completedSteps.includes(step.id)}
			{@const isRecommended = step.id === recommendedStepId}
			<button
				class="video-card"
				class:completed={isCompleted}
				class:recommended={isRecommended}
				onclick={() => handleVideoClick(step)}
				type="button"
			>
				{#if isRecommended}
					<div class="recommended-badge">
						<i class="fas fa-star"></i>
						<span>Recommended</span>
					</div>
				{/if}
				<div class="video-thumbnail">
					<i class="fas fa-play-circle thumbnail-icon"></i>
					{#if isCompleted}
						<div class="completion-badge">
							<i class="fas fa-check"></i>
						</div>
					{/if}
				</div>
				<div class="video-info">
					<span class="video-title">{step.title}</span>
					<span class="video-description">{step.description}</span>
					<span class="video-duration">
						<i class="fas fa-clock"></i>
						~{step.estimatedMinutes} min
					</span>
				</div>
			</button>
		{/each}
	</div>

	<!-- YouTube Video Modal -->
	<YouTubeVideoModal
		isOpen={isModalOpen}
		videoId={selectedVideoId}
		title={selectedVideoTitle}
		onClose={handleCloseModal}
	/>
</section>

<style>
	.getting-started-section {
		margin-bottom: var(--spacing-8);
	}

	.section-subtitle {
		font-size: var(--font-size-small);
		color: var(--color-surface-600);
		margin: calc(-1 * var(--spacing-2)) 0 var(--spacing-4) 0;
	}

	.video-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: var(--spacing-4);
	}

	.video-card {
		display: flex;
		align-items: center;
		gap: var(--spacing-4);
		padding: var(--spacing-4);
		background: white;
		border-radius: var(--radius-xl);
		box-shadow: var(--shadow-md3-1);
		transition: var(--transition-fast);
		cursor: pointer;
		border: 2px solid transparent;
		text-align: left;
		position: relative;
	}

	.video-card:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-md3-2);
	}

	.video-card.completed {
		border-color: var(--color-success-200);
	}

	.video-card.recommended {
		border-color: var(--color-primary-300);
		background: linear-gradient(135deg, white 0%, var(--color-primary-50) 100%);
	}

	.video-card.recommended:hover {
		border-color: var(--color-primary-400);
	}

	.recommended-badge {
		position: absolute;
		top: -10px;
		right: var(--spacing-3);
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		padding: 4px 10px;
		background: var(--color-primary-500);
		color: white;
		border-radius: var(--radius-full);
		font-size: var(--font-size-auxiliary-text);
		font-weight: var(--font-weight-medium);
	}

	.recommended-badge i {
		font-size: 10px;
	}

	.video-thumbnail {
		width: 80px;
		height: 60px;
		background: var(--color-surface-100);
		border-radius: var(--radius-lg);
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
		flex-shrink: 0;
	}

	.video-card.recommended .video-thumbnail {
		background: var(--color-primary-100);
	}

	.thumbnail-icon {
		font-size: 28px;
		color: var(--color-primary-500);
	}

	.completion-badge {
		position: absolute;
		top: -8px;
		right: -8px;
		width: 24px;
		height: 24px;
		background: var(--color-success-500);
		border-radius: var(--radius-full);
		display: flex;
		align-items: center;
		justify-content: center;
		color: white;
		font-size: 12px;
	}

	.video-info {
		display: flex;
		flex-direction: column;
		gap: var(--spacing-1);
		min-width: 0;
	}

	.video-title {
		font-size: var(--font-size-body-content);
		font-weight: var(--font-weight-medium);
		color: var(--color-surface-800);
	}

	.video-description {
		font-size: var(--font-size-small);
		color: var(--color-surface-600);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.video-duration {
		display: flex;
		align-items: center;
		gap: var(--spacing-1);
		font-size: var(--font-size-auxiliary-text);
		color: var(--color-surface-500);
		margin-top: var(--spacing-1);
	}

	.video-duration i {
		font-size: 10px;
	}
</style>
