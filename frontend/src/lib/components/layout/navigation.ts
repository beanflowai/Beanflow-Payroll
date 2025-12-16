/**
 * Payroll Navigation Configuration
 */

export interface NavigationItem {
	label: string;
	href: string;
	icon: string;
}

export const navigationItems: NavigationItem[] = [
	{
		label: 'Dashboard',
		href: '/dashboard',
		icon: 'fa-chart-pie'
	},
	{
		label: 'Employees',
		href: '/employees',
		icon: 'fa-users'
	},
	{
		label: 'Run Payroll',
		href: '/payroll',
		icon: 'fa-calculator'
	},
	{
		label: 'History',
		href: '/payroll/history',
		icon: 'fa-history'
	},
	{
		label: 'Remittance',
		href: '/remittance',
		icon: 'fa-landmark'
	},
	{
		label: 'Reports',
		href: '/reports',
		icon: 'fa-chart-bar'
	},
	{
		label: 'Company',
		href: '/company',
		icon: 'fa-building'
	}
];
