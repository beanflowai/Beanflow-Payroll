<script lang="ts">
	import { Icon } from './index';
	import { ArrowLeftIcon, SearchIcon, AIIcon, SettingsIcon } from './index';
	import { BeanflowIcon } from './index';
	import type { IconName } from './types';

	// Helper to cast string literals to IconName for type safety
	const icon = (name: string) => name as IconName;
</script>

<div class="icon-examples">
	<h1>图标系统使用示例</h1>

	<!-- 基础用法 -->
	<section class="example-section">
		<h2>基础用法</h2>
		<div class="example-grid">
			<div class="example-item">
				<h3>统一组件方式</h3>
				<div class="demo-row">
					<Icon name={icon("search")} size="md" />
					<Icon name={icon("settings")} size="lg" />
					<Icon name={icon("ai")} size="xl" />
				</div>
				<pre><code
						>&lt;Icon name="search" size="md" /&gt;
&lt;Icon name="settings" size="lg" /&gt;
&lt;Icon name="ai" size="xl" /&gt;</code
					></pre>
			</div>

			<div class="example-item">
				<h3>直接导入方式</h3>
				<div class="demo-row">
					<SearchIcon size={20} />
					<SettingsIcon size={24} />
					<AIIcon size={32} />
				</div>
				<pre><code
						>&lt;SearchIcon size=&#123;20&#125; /&gt;
&lt;SettingsIcon size=&#123;24&#125; /&gt;
&lt;AIIcon size=&#123;32&#125; /&gt;</code
					></pre>
			</div>
		</div>
	</section>

	<!-- 变体展示 -->
	<section class="example-section">
		<h2>不同变体</h2>
		<div class="variant-grid">
			<div class="variant-group">
				<h3>Linear 图标</h3>
				<div class="demo-row">
					<Icon name={icon("arrow-left")} variant="line" />
					<Icon name={icon("search")} variant="line" />
					<Icon name={icon("settings")} variant="line" />
					<Icon name={icon("ai")} variant="line" />
				</div>
			</div>

			<div class="variant-group">
				<h3>Filled 图标</h3>
				<div class="demo-row">
					<Icon name={icon("home")} variant="filled" />
					<Icon name={icon("user")} variant="filled" />
					<Icon name={icon("ai")} variant="filled" />
				</div>
			</div>

			<div class="variant-group">
				<h3>Brand 图标</h3>
				<div class="demo-row">
					<Icon name={icon("beanflow")} variant="brand" />
					<BeanflowIcon size={32} />
				</div>
			</div>
		</div>
	</section>

	<!-- 尺寸展示 -->
	<section class="example-section">
		<h2>不同尺寸</h2>
		<div class="size-grid">
			<div class="size-item">
				<Icon name={icon("search")} size="xs" />
				<span>XS (16px)</span>
			</div>
			<div class="size-item">
				<Icon name={icon("search")} size="sm" />
				<span>SM (18px)</span>
			</div>
			<div class="size-item">
				<Icon name={icon("search")} size="md" />
				<span>MD (20px)</span>
			</div>
			<div class="size-item">
				<Icon name={icon("search")} size="lg" />
				<span>LG (24px)</span>
			</div>
			<div class="size-item">
				<Icon name={icon("search")} size="xl" />
				<span>XL (32px)</span>
			</div>
			<div class="size-item">
				<Icon name={icon("search")} size={40} />
				<span>Custom (40px)</span>
			</div>
		</div>
	</section>

	<!-- 颜色展示 -->
	<section class="example-section">
		<h2>不同颜色</h2>
		<div class="color-grid">
			<div class="color-item">
				<Icon name={icon("search")} color="current" />
				<span>Current</span>
			</div>
			<div class="color-item">
				<Icon name={icon("search")} color="primary" />
				<span>Primary</span>
			</div>
			<div class="color-item">
				<Icon name={icon("search")} color="secondary" />
				<span>Secondary</span>
			</div>
			<div class="color-item">
				<Icon name={icon("search")} color="success" />
				<span>Success</span>
			</div>
			<div class="color-item">
				<Icon name={icon("search")} color="warning" />
				<span>Warning</span>
			</div>
			<div class="color-item">
				<Icon name={icon("search")} color="error" />
				<span>Error</span>
			</div>
			<div class="color-item">
				<Icon name={icon("search")} color="#9810fa" />
				<span>Custom</span>
			</div>
		</div>
	</section>

	<!-- 交互状态 -->
	<section class="example-section">
		<h2>交互状态</h2>
		<div class="interaction-grid">
			<div class="interaction-item">
				<h3>按钮中的图标</h3>
				<div class="demo-row">
					<button class="btn btn-primary">
						<Icon name={icon("search")} />
						搜索
					</button>
					<button class="btn btn-secondary">
						<Icon name={icon("settings")} />
						设置
					</button>
					<button class="btn btn-ghost">
						<Icon name={icon("ai")} />
						AI 助手
					</button>
				</div>
			</div>

			<div class="interaction-item">
				<h3>链接中的图标</h3>
				<div class="demo-row">
					<a href="#" class="link">
						<Icon name={icon("arrow-left")} />
						返回
					</a>
					<a href="#" class="link">
						查看详情
						<Icon name="arrow-right" />
					</a>
				</div>
			</div>

			<div class="interaction-item">
				<h3>状态指示</h3>
				<div class="demo-row">
					<div class="status-item">
						<Icon name="check" color="success" />
						<span>成功</span>
					</div>
					<div class="status-item">
						<Icon name="warning" color="warning" />
						<span>警告</span>
					</div>
					<div class="status-item">
						<Icon name="error" color="error" />
						<span>错误</span>
					</div>
				</div>
			</div>
		</div>
	</section>
</div>

<style>
	.icon-examples {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
		font-family: var(--font-sans);
	}

	h1 {
		font-size: 2rem;
		font-weight: 600;
		margin-bottom: 2rem;
		text-align: center;
		color: var(--color-neutral-900);
	}

	.example-section {
		margin-bottom: 3rem;
	}

	h2 {
		font-size: 1.5rem;
		font-weight: 600;
		margin-bottom: 1.5rem;
		color: var(--color-neutral-800);
	}

	h3 {
		font-size: 1.1rem;
		font-weight: 500;
		margin-bottom: 1rem;
		color: var(--color-neutral-700);
	}

	.example-grid,
	.variant-grid,
	.size-grid,
	.color-grid,
	.interaction-grid {
		display: grid;
		gap: 2rem;
	}

	.example-item,
	.variant-group,
	.size-item,
	.color-item,
	.interaction-item {
		padding: 1.5rem;
		background: var(--color-surface-50);
		border: 1px solid var(--color-neutral-200);
		border-radius: 8px;
	}

	.demo-row {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 1rem;
		flex-wrap: wrap;
	}

	pre {
		background: var(--color-neutral-900);
		color: var(--color-neutral-100);
		padding: 1rem;
		border-radius: 4px;
		overflow-x: auto;
		font-size: 0.85rem;
		line-height: 1.5;
	}

	code {
		font-family: var(--font-mono);
	}

	/* 尺寸展示样式 */
	.size-grid {
		grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
	}

	.size-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		text-align: center;
	}

	.size-item span {
		font-size: 0.85rem;
		color: var(--color-neutral-600);
	}

	/* 颜色展示样式 */
	.color-grid {
		grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
	}

	.color-item {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 0.5rem;
		text-align: center;
	}

	.color-item span {
		font-size: 0.85rem;
		color: var(--color-neutral-600);
	}

	/* 交互状态样式 */
	.btn {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 1rem;
		border: none;
		border-radius: 6px;
		font-size: 0.9rem;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.btn-primary {
		background: var(--color-primary-500);
		color: white;
	}

	.btn-primary:hover {
		background: var(--color-primary-600);
	}

	.btn-secondary {
		background: var(--color-neutral-200);
		color: var(--color-neutral-800);
	}

	.btn-secondary:hover {
		background: var(--color-neutral-300);
	}

	.btn-ghost {
		background: transparent;
		color: var(--color-neutral-600);
		border: 1px solid var(--color-neutral-300);
	}

	.btn-ghost:hover {
		background: var(--color-neutral-100);
	}

	.link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		color: var(--color-primary-600);
		text-decoration: none;
		font-weight: 500;
	}

	.link:hover {
		color: var(--color-primary-700);
		text-decoration: underline;
	}

	.status-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-weight: 500;
	}

	@media (max-width: 768px) {
		.icon-examples {
			padding: 1rem;
		}

		.example-grid,
		.variant-grid,
		.interaction-grid {
			grid-template-columns: 1fr;
		}

		.size-grid,
		.color-grid {
			grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
		}
	}
</style>
