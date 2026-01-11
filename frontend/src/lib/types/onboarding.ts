export type OnboardingStep =
  | 'company_profile'
  | 'pay_groups'
  | 'employees'
  | 'employee_assignment'
  | 'payroll_run';

export interface OnboardingProgress {
  completedSteps: OnboardingStep[];
  dismissedAt: string | null;
  lastUpdated: string | null;
}

export interface OnboardingStepConfig {
  id: OnboardingStep;
  title: string;
  description: string;
  icon: string;
  route: string;
  checkCompletion: (companyId: string) => Promise<boolean>;
  videoUrl?: string;
}
