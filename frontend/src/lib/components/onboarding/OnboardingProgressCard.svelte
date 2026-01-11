<script lang="ts">
  import type { OnboardingProgress, OnboardingStep } from '$lib/types/onboarding';
  import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';

  interface Props {
    progress: OnboardingProgress;
    onStepClick?: (stepId: OnboardingStep) => void;
  }

  let { progress, onStepClick }: Props = $props();

  function getStatus(stepId: string): 'completed' | 'pending' {
    return progress.completedSteps.includes(stepId as OnboardingStep) ? 'completed' : 'pending';
  }
</script>

<div class="stat-card onboarding-card">
  <div class="card-header">
    <div class="stat-icon onboarding">
      <i class="fas fa-tasks"></i>
    </div>
    <div class="card-title">
      <span class="stat-label">Setup Progress</span>
      <span class="stat-value">{progress.completedSteps.length}/5</span>
    </div>
  </div>
  <div class="steps-list">
    {#each ONBOARDING_STEPS as step}
      {@const status = getStatus(step.id)}
      <button
        class="step-item {status}"
        onclick={() => onStepClick?.(step.id)}
        type="button"
      >
        <i class="fas {status === 'completed' ? 'fa-check-circle' : 'fa-circle'} step-icon"></i>
        <span class="step-text">{step.title}</span>
      </button>
    {/each}
  </div>
</div>

<style>
  .onboarding-card {
    cursor: default;
  }
  .card-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-4);
  }
  .stat-icon.onboarding {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-primary-100);
    color: var(--color-primary-600);
    border-radius: var(--radius-lg);
    font-size: 20px;
  }
  .card-title {
    display: flex;
    flex-direction: column;
  }
  .stat-label {
    font-size: var(--font-size-small);
    color: var(--color-surface-600);
  }
  .stat-value {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-surface-900);
  }
  .steps-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-2);
    margin-top: var(--spacing-4);
  }
  .step-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
    padding: var(--spacing-2);
    border-radius: var(--radius-md);
    transition: background-color 0.15s;
    cursor: pointer;
    background: transparent;
    border: none;
    text-align: left;
    width: 100%;
  }
  .step-item:hover {
    background: var(--color-surface-50);
  }
  .step-item.completed .step-icon {
    color: var(--color-success-500);
  }
  .step-item.pending .step-icon {
    color: var(--color-surface-300);
  }
  .step-text {
    font-size: var(--font-size-small);
    color: var(--color-surface-700);
  }
</style>
