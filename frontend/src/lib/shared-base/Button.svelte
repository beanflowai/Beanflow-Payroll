<script lang="ts">
	interface ButtonProps {
		variant?: 'fill' | 'border' | 'text' | 'success';
		size?: 'small' | 'medium' | 'large';
		disabled?: boolean;
		loading?: boolean;
		type?: 'button' | 'submit' | 'reset';
		href?: string;
		onclick?: (event: MouseEvent) => void;
		children?: any;
		class?: string;
		ariaLabel?: string;
	}

	let {
		variant = 'fill',
		size = 'medium',
		disabled = false,
		loading = false,
		type = 'button',
		href,
		onclick,
		children,
		class: className = '',
		ariaLabel,
		...props
	}: ButtonProps = $props();

	const isDisabled = $derived(disabled || loading);

	function handleClick(event: MouseEvent) {
		if (isDisabled) return;
		onclick?.(event);
	}

	const baseClasses = 'btn transition-fast focus-visible:focus-visible';
	const sizeClasses = {
		small: 'btn-small',
		medium: 'btn-medium',
		large: 'btn-large'
	};
	const variantClasses: Record<string, string> = {
		fill: 'btn-fill',
		border: 'btn-border',
		text: 'btn-text',
		success: 'btn-success'
	};

	const buttonClasses = $derived(
		[baseClasses, sizeClasses[size], variantClasses[variant], className].filter(Boolean).join(' ')
	);
</script>

{#if href && !disabled}
	<a {href} class={buttonClasses} role="button" aria-label={ariaLabel} {...props}>
		{#if loading}
			<div class="btn-spinner"></div>
		{/if}
		{@render children?.()}
	</a>
{:else}
	<button
		{type}
		class={buttonClasses}
		disabled={isDisabled}
		onclick={handleClick}
		aria-label={ariaLabel}
		{...props}
	>
		{#if loading}
			<div class="btn-spinner"></div>
		{/if}
		{@render children?.()}
	</button>
{/if}

<style>
	/* Button spinner styling */
	:global(.btn-spinner) {
		width: 16px;
		height: 16px;
		border: 2px solid currentColor;
		border-top-color: transparent;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	/* Loading state - prevent interaction */
	:global(.btn:has(.btn-spinner)) {
		pointer-events: none;
	}
</style>
