import { supabase } from '$lib/api/supabase';
import type { OnboardingStepConfig } from '$lib/types/onboarding';

export const ONBOARDING_STEPS: OnboardingStepConfig[] = [
  {
    id: 'company_profile',
    title: 'Create Company Profile',
    description: 'Set up your company information and CRA remittance details',
    icon: 'fa-building',
    route: '/company?tab=profile',
    checkCompletion: async (companyId: string) => {
      const { data } = await supabase
        .from('companies')
        .select('company_name, business_number, payroll_account_number, province')
        .eq('id', companyId)
        .single();
      return !!data?.company_name && !!data?.business_number &&
             !!data?.payroll_account_number && !!data?.province;
    },
    videoUrl: undefined
  },
  {
    id: 'pay_groups',
    title: 'Design Pay Groups',
    description: 'Create pay groups to organize employees by pay frequency',
    icon: 'fa-clipboard-list',
    route: '/company?tab=pay-groups',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('pay_groups')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId);
      return (count ?? 0) > 0;
    },
    videoUrl: undefined
  },
  {
    id: 'employees',
    title: 'Add Employees',
    description: 'Add your employees to the system',
    icon: 'fa-user-plus',
    route: '/employees/new',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('employees')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId)
        .is('termination_date', null);
      return (count ?? 0) > 0;
    },
    videoUrl: undefined
  },
  {
    id: 'employee_assignment',
    title: 'Assign to Pay Groups',
    description: 'Assign employees to their appropriate pay groups',
    icon: 'fa-users-cog',
    route: '/employees',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('employees')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId)
        .not('pay_group_id', 'is', null)
        .is('termination_date', null);
      return (count ?? 0) > 0;
    },
    videoUrl: undefined
  },
  {
    id: 'payroll_run',
    title: 'Run First Payroll',
    description: 'Complete your first payroll run',
    icon: 'fa-play-circle',
    route: '/payroll',
    checkCompletion: async (companyId: string) => {
      const { count } = await supabase
        .from('payroll_runs')
        .select('*', { count: 'exact', head: true })
        .eq('company_id', companyId)
        .in('status', ['paid', 'approved']);
      return (count ?? 0) > 0;
    },
    videoUrl: undefined
  }
];
