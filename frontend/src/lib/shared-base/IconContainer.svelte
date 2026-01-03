<script lang="ts">
	interface IconContainerProps {
		variant?: 'primary' | 'secondary' | 'tertiary' | 'error' | 'surface';
		size?: 'small' | 'medium' | 'large' | 'xl';
		icon?: string;
		interactive?: boolean;
		class?: string;
		onclick?: (event: MouseEvent) => void;
		children?: any;
	}

	let {
		variant = 'primary',
		size = 'medium',
		icon,
		interactive = false,
		class: className = '',
		onclick,
		children,
		...props
	}: IconContainerProps = $props();

	function handleClick(event: MouseEvent) {
		if (!interactive) return;
		onclick?.(event);
	}

	const baseClasses = 'icon-container';
	const sizeClasses = {
		small: 'small',
		medium: 'medium',
		large: 'large',
		xl: 'w-16 h-16 text-2xl'
	};
	const variantClasses = {
		primary: 'icon-primary',
		secondary: 'icon-secondary',
		tertiary: 'icon-tertiary',
		error: 'icon-error',
		surface: 'bg-surface-100 text-surface-800'
	};
	const interactiveClasses = interactive ? 'interactive cursor-pointer' : '';

	const containerClasses = $derived(
		[baseClasses, sizeClasses[size], variantClasses[variant], interactiveClasses, className]
			.filter(Boolean)
			.join(' ')
	);
</script>

<!-- svelte-ignore a11y_no_noninteractive_tabindex -->
<div
	class={containerClasses}
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
	{#if icon}
		<i class="fas fa-{icon}"></i>
	{:else if children}
		{@render children?.()}
	{/if}
</div>

<style>
	/* Extra large size */
	:global(.icon-container.w-16) {
		width: 4rem;
		height: 4rem;
	}

	/* Interactive states */
	:global(.icon-container.interactive:hover) {
		transform: translateY(-2px);
		box-shadow: var(--shadow-md3-2);
	}

	:global(.icon-container.interactive:focus-visible) {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
	}
</style>
