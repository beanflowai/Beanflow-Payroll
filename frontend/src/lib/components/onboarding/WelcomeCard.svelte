<script lang="ts">
  import type { OnboardingProgress } from '$lib/types/onboarding';
  import { ONBOARDING_STEPS } from '$lib/config/onboardingSteps';

  interface Props {
    progress: OnboardingProgress;
    onContinue: () => void;
  }

  let { progress, onContinue }: Props = $props();

  const remainingSteps = $derived(
    ONBOARDING_STEPS.length - progress.completedSteps.length
  );

  const features = [
    { icon: 'fa-calculator', text: 'Automatic tax calculations (CPP, EI, Tax)' },
    { icon: 'fa-play-circle', text: 'One-click payroll runs' },
    { icon: 'fa-file-alt', text: 'T4 year-end reporting' },
    { icon: 'fa-landmark', text: 'CRA remittance tracking' }
  ];
</script>

<div class="welcome-card">
  <div class="welcome-header">
    <div class="welcome-icon">
      <i class="fas fa-rocket"></i>
    </div>
    <h2 class="welcome-title">Your Payroll Journey Starts Here</h2>
    <p class="welcome-subtitle">
      Complete the setup to unlock all features of BeanFlow Payroll
    </p>
  </div>

  <div class="features-list">
    <p class="features-label">What you'll unlock:</p>
    {#each features as feature}
      <div class="feature-item">
        <i class="fas {feature.icon} feature-icon"></i>
        <span class="feature-text">{feature.text}</span>
      </div>
    {/each}
  </div>

  <div class="welcome-footer">
    <button class="continue-btn" onclick={onContinue} type="button">
      <span>Continue Setup</span>
      {#if remainingSteps > 0}
        <span class="steps-badge">{remainingSteps} steps remaining</span>
      {/if}
      <i class="fas fa-arrow-right"></i>
    </button>
  </div>
</div>

<style>
  .welcome-card {
    background: linear-gradient(135deg, var(--color-primary-50) 0%, white 50%, var(--color-secondary-50) 100%);
    border: 1px solid var(--color-primary-200);
    border-radius: var(--radius-xl);
    padding: var(--spacing-6);
    text-align: center;
  }

  .welcome-header {
    margin-bottom: var(--spacing-5);
  }

  .welcome-icon {
    width: 64px;
    height: 64px;
    margin: 0 auto var(--spacing-4);
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-primary-100);
    border-radius: var(--radius-xl);
    font-size: 28px;
    color: var(--color-primary-600);
  }

  .welcome-title {
    font-size: var(--font-size-title-large);
    font-weight: var(--font-weight-semibold);
    color: var(--color-surface-900);
    margin: 0 0 var(--spacing-2);
  }

  .welcome-subtitle {
    font-size: var(--font-size-body-content);
    color: var(--color-surface-600);
    margin: 0;
  }

  .features-list {
    background: white;
    border-radius: var(--radius-lg);
    padding: var(--spacing-4);
    margin-bottom: var(--spacing-5);
    text-align: left;
  }

  .features-label {
    font-size: var(--font-size-small);
    font-weight: var(--font-weight-medium);
    color: var(--color-surface-700);
    margin: 0 0 var(--spacing-3);
  }

  .feature-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-3);
    padding: var(--spacing-2) 0;
  }

  .feature-item:not(:last-child) {
    border-bottom: 1px solid var(--color-surface-100);
  }

  .feature-icon {
    width: 20px;
    color: var(--color-success-500);
    font-size: 14px;
    text-align: center;
  }

  .feature-text {
    font-size: var(--font-size-small);
    color: var(--color-surface-700);
  }

  .welcome-footer {
    display: flex;
    justify-content: center;
  }

  .continue-btn {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-3);
    padding: var(--spacing-3) var(--spacing-5);
    background: var(--color-primary-600);
    color: white;
    border: none;
    border-radius: var(--radius-lg);
    font-size: var(--font-size-body-content);
    font-weight: var(--font-weight-medium);
    cursor: pointer;
    transition: all 0.2s;
  }

  .continue-btn:hover {
    background: var(--color-primary-700);
    transform: translateY(-1px);
  }

  .steps-badge {
    padding: 2px 8px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: var(--radius-full);
    font-size: var(--font-size-small);
  }
</style>
