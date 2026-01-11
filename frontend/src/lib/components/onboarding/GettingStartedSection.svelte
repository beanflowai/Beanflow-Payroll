<script lang="ts">
	import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';
	import type { OnboardingProgress } from '$lib/types/onboarding';

	interface Props {
		progress: OnboardingProgress;
	}

	let { progress }: Props = $props();

	// Show all steps for now (when videos are added, filter by videoUrl)
	const availableSteps = ONBOARDING_STEPS;
</script>

<section class="section getting-started-section">
	<h2 class="section-title">Getting Started</h2>
	<div class="video-grid">
		{#each availableSteps as step}
			{@const isCompleted = progress.completedSteps.includes(step.id)}
			<div class="video-card" class:completed={isCompleted}>
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
				</div>
			</div>
		{/each}
	</div>
</section>

<style>
	.getting-started-section {
		margin-bottom: var(--spacing-8);
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
	}

	.video-card:hover {
		transform: translateY(-2px);
		box-shadow: var(--shadow-md3-2);
	}

	.video-card.completed {
		border: 2px solid var(--color-success-200);
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
</style>
