# BeanFlow-LLM 图标系统

基于 Figma 设计标准的现代化图标系统，提供完整的线性（Line）和面性（Filled）图标库。

## 📁 目录结构

```
icons/
├── Icon.svelte              # 统一入口组件
├── types.ts                 # TypeScript 类型定义
├── index.ts                 # 导出入口和图标注册表
├── IconPreview.svelte       # 图标预览工具
├── IconExamples.svelte      # 使用示例
├── README.md               # 说明文档
├── line/                   # 线性图标
│   ├── ArrowLeftIcon.svelte
│   ├── ArrowRightIcon.svelte
│   ├── SearchIcon.svelte
│   ├── AddIcon.svelte
│   ├── SettingsIcon.svelte
│   └── AIIcon.svelte
├── filled/                 # 面性图标
│   ├── HomeIcon.svelte
│   ├── UserIcon.svelte
│   └── AIIcon.svelte
└── brand/                  # 品牌图标
    └── BeanflowIcon.svelte
```

## 🚀 快速开始

### 1. 统一组件方式（推荐）

```svelte
<script>
	import { Icon } from '$lib/components/v2-current/icons';
</script>

<!-- 基础用法 -->
<Icon name="search" />

<!-- 指定变体、尺寸和颜色 -->
<Icon name="home" variant="filled" size="lg" color="primary" />

<!-- 带无障碍标签 -->
<Icon name="settings" ariaLabel="设置" />
```

### 2. 直接导入方式

```svelte
<script>
	import { SearchIcon, HomeIcon, SettingsIcon } from '$lib/components/v2-current/icons';
</script>

<SearchIcon size={20} />
<HomeIcon size={24} color="var(--color-primary-500)" />
<SettingsIcon size={32} />
```

## 📖 API 文档

### Icon 组件属性

| 属性         | 类型                                             | 默认值           | 描述               |
| ------------ | ------------------------------------------------ | ---------------- | ------------------ |
| `name`       | `IconName`                                       | **必需**         | 图标名称           |
| `variant`    | `'line' \| 'filled' \| 'brand'`                  | `'line'`         | 图标变体           |
| `size`       | `'xs' \| 'sm' \| 'md' \| 'lg' \| 'xl' \| number` | `'md'`           | 图标尺寸           |
| `color`      | `string`                                         | `'currentColor'` | 图标颜色           |
| `class`      | `string`                                         | `''`             | 自定义 CSS 类名    |
| `ariaLabel`  | `string`                                         | -                | 无障碍标签         |
| `ariaHidden` | `boolean`                                        | `false`          | 是否隐藏无障碍标签 |

### 尺寸规格

| 尺寸 | 像素值 | 使用场景               |
| ---- | ------ | ---------------------- |
| `xs` | 16px   | 小按钮、列表项         |
| `sm` | 18px   | 表单控件、工具栏       |
| `md` | 20px   | **默认尺寸**、一般用途 |
| `lg` | 24px   | 导航菜单、重要操作     |
| `xl` | 32px   | 标题、特殊场景         |

### 颜色预设

```typescript
// 可用的颜色预设
'current'; // 当前文字颜色
'primary'; // 主色调
'secondary'; // 次要色调
'success'; // 成功状态
'warning'; // 警告状态
'error'; // 错误状态
'info'; // 信息提示
```

## 🎨 设计规范

### 线性图标 (Line Icons)

- **stroke-width**: 1.5px
- **填充**: 无填充 (`fill="none"`)
- **描边**: 使用 stroke 属性
- **风格**: 简洁、现代、适合界面元素

### 面性图标 (Filled Icons)

- **填充**: 实心填充
- **描边**: 可选的细边框 (`stroke-width="0.5"`)
- **风格**: 稳重、醒目、适合重要操作

### 品牌图标 (Brand Icons)

- **特殊处理**: 包含渐变、特殊效果
- **用途**: 品牌标识、Logo 展示
- **限制**: 仅限特定场景使用

## 🛠️ 开发指南

### 添加新图标

1. **创建 SVG 文件**

   ```bash
   # 在对应目录下创建新图标
   touch icons/line/NewIcon.svelte
   ```

2. **实现图标组件**

   ```svelte
   <script lang="ts">
   	import type { BaseIconProps } from '../types';

   	let {
   		size = 20,
   		color = 'currentColor',
   		class: className = '',
   		ariaLabel,
   		ariaHidden = false,
   		...restProps
   	}: BaseIconProps = $props();
   </script>

   <div
   	class="icon-new {className}"
   	style="width: {size}px; height: {size}px;"
   	aria-label={ariaLabel || 'New'}
   	aria-hidden={ariaHidden}
   	role="img"
   	{...restProps}
   >
   	<svg
   		width={size}
   		height={size}
   		viewBox="0 0 20 20"
   		fill="none"
   		xmlns="http://www.w3.org/2000/svg"
   	>
   		<!-- SVG 路径 -->
   	</svg>
   </div>

   <style>
   	.icon-new {
   		display: inline-flex;
   		align-items: center;
   		justify-content: center;
   	}
   </style>
   ```

3. **更新类型定义**

   ```typescript
   // types.ts
   export type LineIconName =
   	// ... 现有图标
   	'new-icon';
   ```

4. **注册图标**

   ```typescript
   // index.ts
   export { default as NewIcon } from './line/NewIcon.svelte';

   export const ICON_REGISTRY = {
   	line: {
   		// ... 现有图标
   		'new-icon': () => import('./line/NewIcon.svelte').then((m) => m.default)
   	}
   	// ...
   };
   ```

### 设计规范检查

- ✅ **尺寸**: 20px 标准尺寸，基于 20x20 网格
- ✅ **描边**: 线性图标使用 1.5px stroke-width
- ✅ **对齐**: SVG viewBox 对齐到像素网格
- ✅ **颜色**: 使用 CSS 变量或 currentColor
- ✅ **无障碍**: 提供有意义的 ariaLabel

## 🧪 工具和资源

### 图标预览工具

使用 `IconPreview.svelte` 浏览和搜索所有可用图标：

```svelte
<script>
	import IconPreview from '$lib/components/v2-current/icons/IconPreview.svelte';
</script>

<IconPreview />
```

### 使用示例

查看 `IconExamples.svelte` 了解各种使用场景：

```svelte
<script>
	import IconExamples from '$lib/components/v2-current/icons/IconExamples.svelte';
</script>

<IconExamples />
```

## 🔄 迁移指南

### 从旧系统迁移

1. **替换导入**

   ```typescript
   // 旧方式
   import AIIcon from './AIIcon.svelte';

   // 新方式
   import { Icon, AIIcon } from '$lib/components/v2-current/icons';
   ```

2. **更新使用方式**

   ```svelte
   <!-- 旧方式 -->
   <AIIcon size={18} color="#612AE1" />

   <!-- 新方式 - 统一组件 -->
   <Icon name="ai" size="md" color="primary" />

   <!-- 新方式 - 直接导入 -->
   <AIIcon size={20} color="var(--color-primary-500)" />
   ```

3. **移除硬编码颜色**

   ```svelte
   <!-- 避免硬编码 -->
   <Icon name="settings" color="#612AE1" />

   <!-- 使用设计变量 -->
   <Icon name="settings" color="primary" />
   <Icon name="settings" color="var(--color-primary-500)" />
   ```

## 🚧 待办事项

- [ ] 完整的 Figma 图标库同步
- [ ] 图标动画支持
- [ ] 更多颜色预设
- [ ] 图标组合使用示例
- [ ] 自动化图标生成工具
- [ ] 图标使用统计和分析

## 📄 许可证

本图标系统遵循项目的整体许可证。所有图标基于 Figma 设计标准开发，仅供 BeanFlow-LLM 项目使用。
