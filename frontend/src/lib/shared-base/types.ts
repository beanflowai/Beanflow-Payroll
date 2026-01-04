// Type definitions for Beanflow Design System Base Components
import type { Snippet } from 'svelte';

export interface ButtonProps {
	variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
	size?: 'small' | 'medium' | 'large';
	disabled?: boolean;
	loading?: boolean;
	type?: 'button' | 'submit' | 'reset';
	href?: string;
	onclick?: (event: MouseEvent) => void;
	children?: Snippet;
	class?: string;
	ariaLabel?: string;
}

export interface CardProps {
	variant?: 'default' | 'elevated' | 'outlined' | 'stat';
	padding?: 'none' | 'small' | 'medium' | 'large';
	hover?: boolean;
	interactive?: boolean;
	class?: string;
	onclick?: (event: MouseEvent) => void;
	children?: Snippet;
}

export interface IconContainerProps {
	variant?: 'primary' | 'secondary' | 'tertiary' | 'error' | 'surface';
	size?: 'small' | 'medium' | 'large' | 'xl';
	icon?: string;
	interactive?: boolean;
	class?: string;
	onclick?: (event: MouseEvent) => void;
	children?: Snippet;
}
