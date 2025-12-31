<script lang="ts">
	import { setContext } from 'svelte';
	import { createEventDispatcher } from 'svelte';
	import type { IconProps, IconComponentType } from './types';
	import { ICON_SIZES, ICON_COLORS } from './types';
	import type { LineIconName, FilledIconName, BrandIconName, IconVariant } from './types';
	import { ICON_REGISTRY } from './index';

	// 使用 ICON_REGISTRY 中的图标注册表
	const lineIcons = ICON_REGISTRY.line;
	const filledIcons = ICON_REGISTRY.filled;
	const brandIcons = ICON_REGISTRY.brand;

	// Props 定义
	let {
		name,
		variant = 'line',
		size = 'md',
		color = 'currentColor',
		class: className = '',
		ariaLabel,
		ariaHidden = false,
		...restProps
	}: IconProps = $props();

	const dispatch = createEventDispatcher();

	// 计算实际尺寸
	const actualSize = $derived(typeof size === 'number' ? size : ICON_SIZES[size]);

	// 计算实际颜色
	const actualColor = $derived(
		color in ICON_COLORS ? ICON_COLORS[color as keyof typeof ICON_COLORS] : color
	);

	// 动态加载图标组件
	let IconComponent: IconComponentType | null = $state(null);
	let loading = $state(true);
	let error = $state(false);

	// 根据名称和变体选择图标
	async function loadIcon() {
		loading = true;
		error = false;
		IconComponent = null;

		try {
			let iconLoader: (() => Promise<IconComponentType>) | undefined;

			if (variant === 'line' && name in lineIcons) {
				iconLoader = lineIcons[name as keyof typeof lineIcons];
			} else if (variant === 'filled' && name in filledIcons) {
				iconLoader = filledIcons[name as keyof typeof filledIcons];
			} else if (variant === 'brand' && name in brandIcons) {
				iconLoader = brandIcons[name as keyof typeof brandIcons];
			}

			if (iconLoader) {
				IconComponent = await iconLoader();
			} else {
				// 回退到现有的图标组件（向后兼容）
				try {
					// 尝试导入现有的图标组件
					const iconModule = await import(
						`./${name.charAt(0).toUpperCase() + name.slice(1)}Icon.svelte`
					);
					IconComponent = iconModule.default;
				} catch (fallbackError) {
					console.warn(`Icon "${name}" not found in variant "${variant}"`);
					error = true;
				}
			}
		} catch (err) {
			console.error(`Failed to load icon "${name}":`, err);
			error = true;
		} finally {
			loading = false;
		}
	}

	// 监听 name 和 variant 变化
	$effect(() => {
		loadIcon();
	});

	// 事件处理
	function handleClick(event: MouseEvent) {
		dispatch('click', { name, variant, event });
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleClick(event as any);
		}
	}

	// CSS 类名
	const cssClasses = $derived(
		['icon', `icon--${variant}`, `icon--${typeof size === 'string' ? size : 'custom'}`, className]
			.filter(Boolean)
			.join(' ')
	);
</script>

<!-- 图标容器 -->
{#if loading}
	<div
		class={cssClasses}
		style="width: {actualSize}px; height: {actualSize}px;"
		aria-hidden="true"
		{...restProps}
	>
		<!-- 加载占位符 -->
		<div class="icon__placeholder"></div>
	</div>
{:else if error}
	<div
		class={cssClasses}
		style="width: {actualSize}px; height: {actualSize}px;"
		aria-label={ariaLabel || `Error loading icon: ${name}`}
		role="img"
		{...restProps}
	>
		<!-- 错误占位符 -->
		<div class="icon__error">?</div>
	</div>
{:else if IconComponent}
	<div
		class={cssClasses}
		style="width: {actualSize}px; height: {actualSize}px;"
		aria-label={ariaLabel}
		aria-hidden={ariaHidden}
		role={ariaLabel ? 'img' : undefined}
		tabindex={ariaLabel ? 0 : undefined}
		onclick={handleClick}
		onkeydown={handleKeydown}
		{...restProps}
	>
		<svelte:component
			this={IconComponent}
			size={actualSize}
			color={actualColor}
			class="icon__svg"
		/>
	</div>
{/if}

<style>
	.icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		transition: color 0.2s ease;
	}

	.icon:focus-visible {
		outline: 2px solid var(--color-primary-500);
		outline-offset: 2px;
		border-radius: 4px;
	}

	.icon__placeholder {
		width: 100%;
		height: 100%;
		background: var(--color-neutral-200);
		border-radius: 50%;
		animation: pulse 1.5s ease-in-out infinite;
	}

	.icon__error {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--color-error-100);
		color: var(--color-error-600);
		border-radius: 50%;
		font-weight: bold;
		font-size: 0.8em;
	}

	.icon__svg {
		width: 100%;
		height: 100%;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.5;
		}
	}

	/* 变体特定样式 */
	.icon--line .icon__svg {
		stroke-width: 1.5;
		fill: none;
		stroke: currentColor;
	}

	.icon--filled .icon__svg {
		fill: currentColor;
	}

	.icon--brand .icon__svg {
		fill: currentColor;
	}

	/* 尺寸特定样式 */
	.icon--xs {
		font-size: 16px;
	}

	.icon--sm {
		font-size: 18px;
	}

	.icon--md {
		font-size: 20px;
	}

	.icon--lg {
		font-size: 24px;
	}

	.icon--xl {
		font-size: 32px;
	}
</style>
