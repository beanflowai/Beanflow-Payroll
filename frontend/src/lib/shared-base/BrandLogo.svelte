<script lang="ts">
	interface BrandLogoProps {
		size?: 'sm' | 'md' | 'lg';
		variant?: 'solid' | 'transparent';
		class?: string;
	}

	let { size = 'md', variant = 'solid', class: className = '' }: BrandLogoProps = $props();

	const sizeClass = {
		sm: 'bf-brand-logo-sm',
		md: 'bf-brand-logo-md',
		lg: 'bf-brand-logo-lg'
	}[size];

	const variantClass =
		variant === 'transparent' ? 'bf-brand-logo-transparent' : 'bf-brand-logo-solid';

	const classes = $derived(
		['bf-brand-logo', sizeClass, variantClass, className].filter(Boolean).join(' ')
	);
</script>

<div class={classes} aria-hidden="true">
	<i class="fas fa-leaf"></i>
</div>

<style>
	.bf-brand-logo {
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-xl);
		color: #fff;
		box-shadow: var(--shadow-sm);
	}

	.bf-brand-logo-solid {
		background: var(--gradient-primary);
	}
	.bf-brand-logo-transparent {
		background: transparent;
	}

	.bf-brand-logo-sm {
		width: 32px;
		height: 32px;
		font-size: var(--font-size-body-content);
	}
	.bf-brand-logo-md {
		width: 40px;
		height: 40px;
		font-size: var(--font-size-title-large);
	}
	.bf-brand-logo-lg {
		width: 48px;
		height: 48px;
		font-size: var(--font-size-title-large);
	}
</style>
