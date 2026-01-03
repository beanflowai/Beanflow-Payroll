<script lang="ts">
	interface CardProps {
		variant?: 'default' | 'elevated' | 'outlined' | 'stat';
		padding?: 'none' | 'small' | 'medium' | 'large';
		hover?: boolean;
		interactive?: boolean;
		class?: string;
		onclick?: (event: MouseEvent) => void;
		children?: any;
	}

	let {
		variant = 'default',
		padding = 'medium',
		hover = false,
		interactive = false,
		class: className = '',
		onclick,
		children,
		...props
	}: CardProps = $props();

	function handleClick(event: MouseEvent) {
		if (!interactive) return;
		onclick?.(event);
	}

	const baseClasses = 'card';
	const variantClasses = {
		default: 'bg-white border-0',
		elevated: 'card-elevated',
		outlined: 'bg-white border border-surface-300',
		stat: 'stat-card'
	};
	const paddingClasses = {
		none: 'p-0',
		small: 'p-4',
		medium: 'p-6',
		large: 'p-8'
	};
	const cardClasses = $derived(
		[
			baseClasses,
			variantClasses[variant],
			paddingClasses[padding],
			interactive ? 'interactive cursor-pointer' : '',
			hover ? 'hover-lift' : '',
			className
		]
			.filter(Boolean)
			.join(' ')
	);
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
	class={cardClasses}
	role={interactive ? 'button' : undefined}
	tabindex={interactive ? 0 : undefined}
	onclick={interactive ? handleClick : undefined}
	onkeydown={interactive
		? (e) => {
				if (e.key === 'Enter' || e.key === ' ') {
					e.preventDefault();
					handleClick(e as any);
				}
			}
		: undefined}
	{...props}
>
	{@render children?.()}
</div>

<style>
	/* Stat Card Specific Styling */
	:global(.stat-card) {
		background: white;
		border-radius: var(--radius-xl);
		padding: var(--spacing-6);
		box-shadow: var(--shadow-md3-1);
		transition: all var(--transition-standard);
		border: 1px solid var(--color-surface-200);
	}

	:global(.stat-card:hover) {
		box-shadow: var(--shadow-md3-2);
		border-color: var(--color-primary-200);
		transform: translateY(-2px);
	}

	/* Focus states for interactive cards */
	:global(.interactive:focus-visible) {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
	}
</style>
