<script lang="ts">
	import { AVAILABLE_ICONS, ICON_SIZES, ICON_COLORS } from './index';
	import type { IconVariant, IconSize, IconName } from './types';
	import Icon from './Icon.svelte';

	// 预览配置
	let selectedVariant: IconVariant = $state('line');
	let selectedSize: IconSize = $state('md');
	let selectedColor = $state('current');
	let searchText = $state('');

	// 过滤图标列表
	const filteredIcons = $derived(
		AVAILABLE_ICONS[selectedVariant].filter((name) =>
			name.toLowerCase().includes(searchText.toLowerCase())
		)
	);

	// 颜色选项
	const colorOptions = Object.keys(ICON_COLORS);

	// 尺寸选项
	const sizeOptions: IconSize[] = ['xs', 'sm', 'md', 'lg', 'xl'];

	// 复制代码到剪贴板
	async function copyToClipboard(code: string) {
		try {
			await navigator.clipboard.writeText(code);
			// 这里可以添加成功提示
		} catch (err) {
			console.error('Failed to copy code:', err);
		}
	}

	// 生成使用代码
	function generateCode(iconName: string) {
		const sizeAttr = selectedSize !== 'md' ? ` size="${selectedSize}"` : '';
		const colorAttr = selectedColor !== 'current' ? ` color="${selectedColor}"` : '';
		const variantAttr = selectedVariant !== 'line' ? ` variant="${selectedVariant}"` : '';

		const attrs = [variantAttr, sizeAttr, colorAttr].filter(Boolean).join(' ');

		return `<Icon name="${iconName}"${attrs ? ' ' + attrs : ''} />`;
	}
</script>

<div class="icon-preview">
	<div class="preview-header">
		<h1>图标预览工具</h1>
		<p>基于 Figma 设计标准的图标系统</p>
	</div>

	<!-- 控制面板 -->
	<div class="control-panel">
		<div class="control-group">
			<label for="variant-select">图标类型：</label>
			<select id="variant-select" bind:value={selectedVariant}>
				<option value="line">线性图标</option>
				<option value="filled">面性图标</option>
				<option value="brand">品牌图标</option>
			</select>
		</div>

		<div class="control-group">
			<label for="size-select">尺寸：</label>
			<select id="size-select" bind:value={selectedSize}>
				{#each sizeOptions as size (size)}
					<option value={size}>{size.toUpperCase()} ({ICON_SIZES[size]}px)</option>
				{/each}
			</select>
		</div>

		<div class="control-group">
			<label for="color-select">颜色：</label>
			<select id="color-select" bind:value={selectedColor}>
				{#each colorOptions as color (color)}
					<option value={color}>{color}</option>
				{/each}
			</select>
		</div>

		<div class="control-group search-group">
			<label for="icon-search">搜索：</label>
			<input id="icon-search" type="text" placeholder="输入图标名称..." bind:value={searchText} />
		</div>
	</div>

	<!-- 图标网格 -->
	<div class="icon-grid">
		{#each filteredIcons as iconName (iconName)}
			<div class="icon-item">
				<div class="icon-display">
					<Icon
						name={iconName as IconName}
						variant={selectedVariant}
						size={selectedSize}
						color={selectedColor}
					/>
				</div>
				<div class="icon-info">
					<div class="icon-name">{iconName}</div>
					<div class="icon-code">
						<code>{generateCode(iconName)}</code>
						<button
							class="copy-button"
							onclick={() => copyToClipboard(generateCode(iconName))}
							title="复制代码"
						>
							📋
						</button>
					</div>
				</div>
			</div>
		{/each}
	</div>

	{#if filteredIcons.length === 0}
		<div class="no-results">
			<p>没有找到匹配的图标</p>
		</div>
	{/if}

	<!-- 使用说明 -->
	<div class="usage-guide">
		<h2>使用说明</h2>
		<div class="usage-section">
			<h3>统一组件方式</h3>
			<pre><code
					>&lt;script&gt;
  import &#123; Icon &#125; from '$lib/components/v2-current/icons';
&lt;/script&gt;

&lt;Icon name="search" size="md" variant="line" /&gt;
&lt;Icon name="home" size="lg" variant="filled" color="primary" /&gt;</code
				></pre>
		</div>

		<div class="usage-section">
			<h3>直接导入方式</h3>
			<pre><code
					>&lt;script&gt;
  import &#123; SearchIcon, HomeIcon &#125; from '$lib/components/v2-current/icons';
&lt;/script&gt;

&lt;SearchIcon size=&#123;20&#125; /&gt;
&lt;HomeIcon size=&#123;24&#125; color="var(--color-primary-500)" /&gt;</code
				></pre>
		</div>

		<div class="usage-section">
			<h3>支持的属性</h3>
			<ul>
				<li><code>name</code>: 图标名称（必需）</li>
				<li><code>variant</code>: 图标类型 ('line' | 'filled' | 'brand')</li>
				<li><code>size</code>: 尺寸 ('xs' | 'sm' | 'md' | 'lg' | 'xl' | number)</li>
				<li><code>color</code>: 颜色（CSS颜色值或预设名称）</li>
				<li><code>class</code>: 自定义CSS类名</li>
				<li><code>ariaLabel</code>: 无障碍标签</li>
			</ul>
		</div>
	</div>
</div>

<style>
	.icon-preview {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		font-family: var(--font-sans);
	}

	.preview-header {
		text-align: center;
		margin-bottom: 2rem;
	}

	.preview-header h1 {
		font-size: 2rem;
		font-weight: 600;
		margin-bottom: 0.5rem;
		color: var(--color-neutral-900);
	}

	.preview-header p {
		color: var(--color-neutral-600);
		font-size: 1.1rem;
	}

	.control-panel {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 2rem;
		padding: 1.5rem;
		background: var(--color-surface-100);
		border-radius: 8px;
		border: 1px solid var(--color-neutral-200);
	}

	.control-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.control-group label {
		font-weight: 500;
		color: var(--color-neutral-700);
		font-size: 0.9rem;
	}

	.control-group select,
	.control-group input {
		padding: 0.5rem;
		border: 1px solid var(--color-neutral-300);
		border-radius: 4px;
		font-size: 0.9rem;
	}

	.search-group {
		grid-column: span 2;
	}

	.icon-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
		gap: 1.5rem;
		margin-bottom: 3rem;
	}

	.icon-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		padding: 1.5rem;
		background: var(--color-surface-50);
		border: 1px solid var(--color-neutral-200);
		border-radius: 8px;
		transition: all 0.2s ease;
	}

	.icon-item:hover {
		border-color: var(--color-primary-300);
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
		transform: translateY(-2px);
	}

	.icon-display {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 60px;
		height: 60px;
		margin-bottom: 1rem;
		background: var(--color-neutral-50);
		border-radius: 8px;
		border: 1px solid var(--color-neutral-200);
	}

	.icon-info {
		text-align: center;
		width: 100%;
	}

	.icon-name {
		font-weight: 500;
		color: var(--color-neutral-800);
		margin-bottom: 0.5rem;
		font-size: 0.9rem;
	}

	.icon-code {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.5rem;
		background: var(--color-neutral-100);
		padding: 0.5rem;
		border-radius: 4px;
		border: 1px solid var(--color-neutral-200);
	}

	.icon-code code {
		font-size: 0.75rem;
		color: var(--color-neutral-700);
		flex: 1;
		text-align: left;
		word-break: break-all;
	}

	.copy-button {
		background: none;
		border: none;
		cursor: pointer;
		padding: 0.25rem;
		border-radius: 4px;
		transition: background-color 0.2s ease;
	}

	.copy-button:hover {
		background: var(--color-neutral-200);
	}

	.no-results {
		text-align: center;
		padding: 3rem;
		color: var(--color-neutral-500);
		font-size: 1.1rem;
	}

	.usage-guide {
		margin-top: 3rem;
		padding: 2rem;
		background: var(--color-surface-100);
		border-radius: 8px;
		border: 1px solid var(--color-neutral-200);
	}

	.usage-guide h2 {
		font-size: 1.5rem;
		font-weight: 600;
		margin-bottom: 1.5rem;
		color: var(--color-neutral-900);
	}

	.usage-section {
		margin-bottom: 1.5rem;
	}

	.usage-section h3 {
		font-size: 1.1rem;
		font-weight: 500;
		margin-bottom: 0.75rem;
		color: var(--color-neutral-800);
	}

	.usage-section pre {
		background: var(--color-neutral-900);
		color: var(--color-neutral-100);
		padding: 1rem;
		border-radius: 4px;
		overflow-x: auto;
		font-size: 0.85rem;
		line-height: 1.5;
	}

	.usage-section code {
		font-family: var(--font-mono);
	}

	.usage-section ul {
		list-style: none;
		padding: 0;
	}

	.usage-section li {
		padding: 0.25rem 0;
		color: var(--color-neutral-700);
	}

	.usage-section li code {
		background: var(--color-neutral-200);
		color: var(--color-neutral-800);
		padding: 0.125rem 0.25rem;
		border-radius: 3px;
		font-size: 0.85rem;
	}

	@media (max-width: 768px) {
		.icon-preview {
			padding: 1rem;
		}

		.control-panel {
			grid-template-columns: 1fr;
		}

		.search-group {
			grid-column: span 1;
		}

		.icon-grid {
			grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
			gap: 1rem;
		}
	}
</style>
