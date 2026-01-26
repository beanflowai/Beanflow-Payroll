<script lang="ts">
  import type { OnboardingProgress, OnboardingStep } from '$lib/types/onboarding';
  import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';

  interface Props {
    progress: OnboardingProgress;
    onStepClick?: (stepId: OnboardingStep) => void;
    onSkip?: () => void;
  }

  let { progress, onStepClick, onSkip }: Props = $props();

  const totalSteps = ONBOARDING_STEPS.length;
  const completedCount = $derived(progress.completedSteps.length);
  const progressPercent = $derived(Math.round((completedCount / totalSteps) * 100));

  // Find the first incomplete step (current step)
  const currentStepId = $derived(
    ONBOARDING_STEPS.find(s => !progress.completedSteps.includes(s.id))?.id ?? null
  );

  // Calculate remaining time (sum of incomplete steps)
  const remainingMinutes = $derived(
    ONBOARDING_STEPS
      .filter(s => !progress.completedSteps.includes(s.id))
      .reduce((sum, s) => sum + s.estimatedMinutes, 0)
  );

  function getStatus(stepId: OnboardingStep): 'completed' | 'current' | 'pending' {
    if (progress.completedSteps.includes(stepId)) return 'completed';
    if (stepId === currentStepId) return 'current';
    return 'pending';
  }
</script>

<div class="progress-card">
  <!-- Header with progress bar -->
  <div class="card-header">
    <div class="header-top">
      <div class="header-title">
        <i class="fas fa-tasks header-icon"></i>
        <span class="title-text">Setup Progress</span>
      </div>
      <span class="progress-fraction">{completedCount}/{totalSteps}</span>
    </div>

    <div class="progress-bar-container">
      <div class="progress-bar" style="width: {progressPercent}%"></div>
    </div>

    <div class="progress-meta">
      <span class="progress-percent">{progressPercent}% complete</span>
      {#if remainingMinutes > 0}
        <span class="time-remaining">~{remainingMinutes} min remaining</span>
      {/if}
    </div>
  </div>

  <!-- Steps list -->
  <div class="steps-list">
    {#each ONBOARDING_STEPS as step}
      {@const status = getStatus(step.id)}
      <button
        class="step-item {status}"
        onclick={() => onStepClick?.(step.id)}
        type="button"
      >
        <div class="step-indicator">
          {#if status === 'completed'}
            <i class="fas fa-check-circle"></i>
          {:else if status === 'current'}
            <div class="current-dot"></div>
          {:else}
            <div class="pending-dot"></div>
          {/if}
        </div>
        <div class="step-content">
          <span class="step-title">{step.title}</span>
          {#if status === 'current' && step.tip}
            <span class="step-tip">{step.tip}</span>
          {/if}
        </div>
        <span class="step-time">
          {#if status === 'completed'}
            Done
          {:else}
            ~{step.estimatedMinutes} min
          {/if}
        </span>
      </button>
    {/each}
  </div>

  <!-- Skip button -->
  {#if onSkip}
    <div class="card-footer">
      <button class="skip-btn" onclick={onSkip} type="button">
        Skip Setup for Now
      </button>
    </div>
  {/if}
</div>

<style>
  .progress-card {
    background: white;
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-md3-1);
    overflow: hidden;
  }

  .card-header {
    padding: var(--spacing-5);
    border-bottom: 1px solid var(--color-surface-100);
  }

  .header-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-3);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-2);
  }

  .header-icon {
    font-size: 18px;
    color: var(--color-primary-500);
  }

  .title-text {
    font-size: var(--font-size-body-content);
    font-weight: var(--font-weight-semibold);
    color: var(--color-surface-800);
  }

  .progress-fraction {
    font-size: var(--font-size-2xl);
    font-weight: var(--font-weight-bold);
    color: var(--color-surface-900);
  }

  .progress-bar-container {
    height: 8px;
    background: var(--color-surface-100);
    border-radius: var(--radius-full);
    overflow: hidden;
    margin-bottom: var(--spacing-2);
  }

  .progress-bar {
    height: 100%;
    background: var(--color-primary-500);
    border-radius: var(--radius-full);
    transition: width 0.3s ease;
  }

  .progress-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .progress-percent {
    font-size: var(--font-size-small);
    font-weight: var(--font-weight-medium);
    color: var(--color-primary-600);
  }

  .time-remaining {
    font-size: var(--font-size-small);
    color: var(--color-surface-500);
  }

  .steps-list {
    display: flex;
    flex-direction: column;
  }

  .step-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    padding: var(--spacing-3) var(--spacing-5);
    background: transparent;
    border: none;
    border-bottom: 1px solid var(--color-surface-50);
    cursor: pointer;
    text-align: left;
    width: 100%;
    transition: background-color 0.15s;
  }

  .step-item:last-child {
    border-bottom: none;
  }

  .step-item:hover {
    background: var(--color-surface-50);
  }

  .step-item.current {
    background: var(--color-primary-50);
  }

  .step-item.current:hover {
    background: var(--color-primary-100);
  }

  .step-indicator {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .step-item.completed .step-indicator {
    color: var(--color-success-500);
    font-size: 20px;
  }

  .current-dot {
    width: 12px;
    height: 12px;
    background: var(--color-primary-500);
    border-radius: var(--radius-full);
    animation: pulse 2s infinite;
  }

  .pending-dot {
    width: 10px;
    height: 10px;
    border: 2px solid var(--color-surface-300);
    border-radius: var(--radius-full);
  }

  @keyframes pulse {
    0%, 100% {
      box-shadow: 0 0 0 0 rgba(152, 16, 250, 0.4);
    }
    50% {
      box-shadow: 0 0 0 8px rgba(152, 16, 250, 0);
    }
  }

  .step-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .step-title {
    font-size: var(--font-size-small);
    color: var(--color-surface-700);
  }

  .step-item.completed .step-title {
    color: var(--color-surface-500);
  }

  .step-item.current .step-title {
    font-weight: var(--font-weight-medium);
    color: var(--color-surface-800);
  }

  .step-tip {
    font-size: var(--font-size-auxiliary-text);
    color: var(--color-primary-600);
    margin-top: 2px;
  }

  .step-time {
    font-size: var(--font-size-auxiliary-text);
    color: var(--color-surface-500);
    flex-shrink: 0;
  }

  .step-item.completed .step-time {
    color: var(--color-success-500);
    font-weight: var(--font-weight-medium);
  }

  .card-footer {
    padding: var(--spacing-4) var(--spacing-5);
    border-top: 1px solid var(--color-surface-100);
  }

  .skip-btn {
    width: 100%;
    padding: var(--spacing-2) var(--spacing-4);
    background: transparent;
    color: var(--color-surface-600);
    border: 1px solid var(--color-surface-200);
    border-radius: var(--radius-md);
    font-size: var(--font-size-small);
    cursor: pointer;
    transition: all 0.15s;
  }

  .skip-btn:hover {
    background: var(--color-surface-50);
    color: var(--color-surface-700);
    border-color: var(--color-surface-300);
  }
</style>
