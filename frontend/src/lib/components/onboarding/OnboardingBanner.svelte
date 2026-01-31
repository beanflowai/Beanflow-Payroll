<script lang="ts">
  import type { OnboardingProgress } from '$lib/types/onboarding';
  import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';

  interface Props {
    progress: OnboardingProgress;
    onDismiss: () => void;
    onContinue: () => void;
    onWatchVideo?: (videoId: string, title: string) => void;
  }

  let { progress, onDismiss, onContinue, onWatchVideo }: Props = $props();

  const totalSteps = ONBOARDING_STEPS.length;
  const completedCount = $derived(progress.completedSteps.length);
  const progressPercent = $derived(Math.round((completedCount / totalSteps) * 100));
  const nextStep = $derived(ONBOARDING_STEPS.find(s => !progress.completedSteps.includes(s.id)));
</script>

<div class="onboarding-banner">
  <div class="banner-content">
    <div class="banner-icon-wrapper">
      <i class="fas fa-rocket banner-icon"></i>
    </div>
    <div class="banner-text">
      <div class="banner-title">
        <span class="setup-label">Setup:</span>
        <span class="progress-badge">{progressPercent}% Complete</span>
      </div>
      <span class="banner-description">
        {#if nextStep}
          Next: {nextStep.title} (~{nextStep.estimatedMinutes} min)
        {:else}
          Almost done!
        {/if}
      </span>
    </div>
  </div>

  <div class="banner-actions">
    {#if nextStep?.youtubeVideoId && onWatchVideo}
      <button
        class="btn-video"
        onclick={() => onWatchVideo(nextStep.youtubeVideoId!, nextStep.title)}
        type="button"
      >
        <i class="fas fa-play"></i>
        Watch Tutorial
      </button>
    {/if}
    <button class="btn-continue" onclick={onContinue} type="button">
      <span>Continue Setup</span>
      <i class="fas fa-arrow-right"></i>
    </button>
    <button class="btn-dismiss" onclick={onDismiss} aria-label="Dismiss" type="button">
      <i class="fas fa-times"></i>
    </button>
  </div>
</div>

<style>
  .onboarding-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-4);
    padding: var(--spacing-4) var(--spacing-5);
    background: linear-gradient(135deg, var(--color-primary-50), var(--color-secondary-50));
    border: 1px solid var(--color-primary-200);
    border-radius: var(--radius-lg);
    margin-bottom: var(--spacing-6);
  }

  .banner-content {
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
  }

  .banner-icon-wrapper {
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-primary-100);
    border-radius: var(--radius-lg);
  }

  .banner-icon {
    font-size: 20px;
    color: var(--color-primary-600);
  }

  .banner-text {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-1);
  }

  .banner-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .setup-label {
    font-weight: var(--font-weight-semibold);
    color: var(--color-surface-800);
  }

  .progress-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    background: var(--color-primary-500);
    color: white;
    border-radius: var(--radius-full);
    font-size: var(--font-size-auxiliary-text);
    font-weight: var(--font-weight-medium);
  }

  .banner-description {
    font-size: var(--font-size-small);
    color: var(--color-surface-600);
  }

  .banner-actions {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    flex-shrink: 0;
  }

  .btn-video {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    padding: var(--spacing-2) var(--spacing-3);
    background: white;
    color: var(--color-primary-600);
    border: 1px solid var(--color-primary-200);
    border-radius: var(--radius-md);
    font-size: var(--font-size-small);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-video:hover {
    background: var(--color-primary-50);
    border-color: var(--color-primary-300);
  }

  .btn-video i {
    font-size: 12px;
  }

  .btn-continue {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    padding: var(--spacing-2) var(--spacing-4);
    background: var(--color-primary-600);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    font-size: var(--font-size-small);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .btn-continue:hover {
    background: var(--color-primary-700);
  }

  .btn-continue i {
    font-size: 12px;
  }

  .btn-dismiss {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    background: transparent;
    color: var(--color-surface-500);
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s;
  }

  .btn-dismiss:hover {
    background: var(--color-surface-100);
    color: var(--color-surface-700);
  }

  /* Responsive - stack on mobile */
  @media (max-width: 640px) {
    .onboarding-banner {
      flex-direction: column;
      align-items: stretch;
      gap: var(--spacing-4);
    }

    .banner-actions {
      justify-content: flex-end;
    }

    .btn-video {
      flex: 1;
      justify-content: center;
    }

    .btn-continue {
      flex: 1;
      justify-content: center;
    }
  }
</style>
