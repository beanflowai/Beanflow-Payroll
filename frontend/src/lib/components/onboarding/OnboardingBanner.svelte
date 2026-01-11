<script lang="ts">
  import type { OnboardingProgress } from '$lib/types/onboarding';
  import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';

  interface Props {
    progress: OnboardingProgress;
    onDismiss: () => void;
    onContinue: () => void;
  }

  let { progress, onDismiss, onContinue }: Props = $props();

  const completedCount = $derived(progress.completedSteps.length);
  const nextStep = $derived(ONBOARDING_STEPS.find(s => !progress.completedSteps.includes(s.id)));
</script>

<div class="onboarding-banner">
  <div class="banner-content">
    <i class="fas fa-rocket banner-icon"></i>
    <div class="banner-text">
      <span class="banner-title">
        Setup in Progress: {completedCount} of 5 steps completed
      </span>
      <span class="banner-description">
        {nextStep ? `Next: ${nextStep.title}` : 'Almost done!'}
      </span>
    </div>
  </div>
  <div class="banner-actions">
    <button class="btn-continue" onclick={onContinue}>
      Continue Setup
    </button>
    <button class="btn-dismiss" onclick={onDismiss} aria-label="Dismiss">
      <i class="fas fa-times"></i>
    </button>
  </div>
</div>

<style>
  .onboarding-banner {
    display: flex;
    align-items: center;
    justify-content: space-between;
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
  .banner-icon {
    font-size: 24px;
    color: var(--color-primary-600);
  }
  .banner-text {
    display: flex;
    flex-direction: column;
  }
  .banner-title {
    font-weight: var(--font-weight-semibold);
    color: var(--color-surface-800);
  }
  .banner-description {
    font-size: var(--font-size-small);
    color: var(--color-surface-600);
  }
  .banner-actions {
    display: flex;
    gap: var(--spacing-3);
  }
  .btn-continue {
    padding: var(--spacing-2) var(--spacing-4);
    background: var(--color-primary-600);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: background-color 0.2s;
  }
  .btn-continue:hover {
    background: var(--color-primary-700);
  }
  .btn-dismiss {
    padding: var(--spacing-2);
    background: transparent;
    color: var(--color-surface-500);
    border: none;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: color 0.2s;
  }
  .btn-dismiss:hover {
    color: var(--color-surface-700);
  }
</style>
