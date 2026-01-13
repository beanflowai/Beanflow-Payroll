import { browser } from '$app/environment';
import { supabase } from '$lib/api/supabase';
import { companyState } from './company.svelte';
import type { OnboardingProgress, OnboardingStep } from '$lib/types/onboarding';

let _progress = $state<OnboardingProgress | null>(null);
let _isLoading = $state(false);
let _error = $state<string | null>(null);
let _isDismissed = $state(false);

const EMPTY_PROGRESS: OnboardingProgress = {
  completedSteps: [],
  dismissedAt: null,
  lastUpdated: null
};

function normalizeProgress(progress?: Partial<OnboardingProgress> | null): OnboardingProgress {
  return {
    completedSteps: Array.isArray(progress?.completedSteps)
      ? (progress?.completedSteps as OnboardingStep[])
      : [],
    dismissedAt: null,
    lastUpdated: progress?.lastUpdated ?? null
  };
}

function getCompanyIdSafe(): string | null {
  return companyState.currentCompany?.id ?? null;
}

export async function loadOnboardingProgress(): Promise<void> {
  if (!browser) return;
  _isLoading = true;
  _error = null;
  _isDismissed = false;

  try {
    const companyId = getCompanyIdSafe();
    if (!companyId) {
      // No company yet - set default empty progress
      _progress = { ...EMPTY_PROGRESS };
      return;
    }
    const { data, error } = await supabase
      .from('companies')
      .select('onboarding_progress')
      .eq('id', companyId)
      .single();

    if (error) throw error;
    _progress = normalizeProgress(data?.onboarding_progress);

    // Auto-dismiss if all 5 steps are complete
    if (_progress.completedSteps.length === 5) {
      _isDismissed = true;
    }
  } catch (err) {
    _error = err instanceof Error ? err.message : 'Failed to load onboarding progress';
    _progress = _progress ?? { ...EMPTY_PROGRESS };
  } finally {
    _isLoading = false;
  }
}

export async function markStepComplete(stepId: OnboardingStep): Promise<void> {
  if (!browser) return;
  const companyId = getCompanyIdSafe();
  if (!companyId) return; // No company, can't mark progress

  if (!_progress) await loadOnboardingProgress();
  if (_progress?.completedSteps.includes(stepId)) return;

  const updatedProgress: OnboardingProgress = {
    completedSteps: [...(_progress?.completedSteps || []), stepId],
    dismissedAt: null,
    lastUpdated: new Date().toISOString()
  };

  try {
    const { error } = await supabase
      .from('companies')
      .update({ onboarding_progress: updatedProgress })
      .eq('id', companyId);

    if (error) throw error;
    _progress = updatedProgress;

    // If all 5 steps are complete, auto-dismiss the banner
    if (updatedProgress.completedSteps.length === 5) {
      _isDismissed = true;
    }
  } catch (err) {
    _error = err instanceof Error ? err.message : 'Failed to update onboarding progress';
  }
}

export async function dismissOnboarding(): Promise<void> {
  if (!browser) return;
  _isDismissed = true;
}

export async function refreshOnboardingStatus(): Promise<void> {
  if (!browser) return;
  const companyId = getCompanyIdSafe();
  _isDismissed = false;
  if (!companyId) {
    // No company yet - set default empty progress
    _progress = { ...EMPTY_PROGRESS };
    return;
  }
  try {
    const { ONBOARDING_STEPS } = await import('$lib/config/onboardingSteps');

    const { data: currentProgress, error: loadError } = await supabase
      .from('companies')
      .select('onboarding_progress')
      .eq('id', companyId)
      .single();

    if (loadError) throw loadError;

    const completedSteps = Array.isArray(currentProgress?.onboarding_progress?.completedSteps)
      ? [...(currentProgress?.onboarding_progress?.completedSteps as OnboardingStep[])]
      : [];

    for (const step of ONBOARDING_STEPS) {
      if (!completedSteps.includes(step.id)) {
        const isComplete = await step.checkCompletion(companyId);
        if (isComplete) completedSteps.push(step.id);
      }
    }

    const newProgress: OnboardingProgress = {
      completedSteps,
      dismissedAt: null,
      lastUpdated: new Date().toISOString()
    };

    const { error: updateError } = await supabase
      .from('companies')
      .update({ onboarding_progress: newProgress })
      .eq('id', companyId);

    if (updateError) throw updateError;
    _progress = newProgress;

    // Auto-dismiss if all 5 steps are complete
    if (newProgress.completedSteps.length === 5) {
      _isDismissed = true;
    }
  } catch (err) {
    _error = err instanceof Error ? err.message : 'Failed to refresh onboarding status';
  }
}

export function clearOnboardingState(): void {
  _progress = null;
  _isLoading = false;
  _error = null;
  _isDismissed = false;
}

export const onboardingState = {
  get progress() { return _progress; },
  get isLoading() { return _isLoading; },
  get error() { return _error; },
  get isCompleted() { return _progress?.completedSteps.length === 5; },
  get completionPercentage() {
    if (!_progress) return 0;
    return (_progress.completedSteps.length / 5) * 100;
  },
  get isDismissed() { return _isDismissed; }
};
