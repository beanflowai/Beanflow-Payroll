/**
 * 图标系统类型定义
 * 基于 Figma 设计标准
 */

export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

export type IconVariant = 'line' | 'filled' | 'brand';

// Linear 图标名称（来自 Figma）
export type LineIconName =
	// 方向箭头
	| 'arrow-left'
	| 'arrow-right'
	| 'arrow-up'
	| 'arrow-down'
	| 'chevron-left'
	| 'chevron-right'
	| 'chevron-up'
	| 'chevron-down'

	// 圆形操作
	| 'add'
	| 'add-circle'
	| 'remove'
	| 'remove-circle'
	| 'check'
	| 'check-circle'
	| 'cancel'
	| 'cancel-circle'
	| 'more'
	| 'more-circle'

	// 选择器
	| 'radio'
	| 'radio-selected'
	| 'checkbox'
	| 'checkbox-selected'

	// 搜索和导航
	| 'search'
	| 'search-circle'
	| 'menu'
	| 'close'

	// 用户和操作
	| 'user'
	| 'users'
	| 'settings'
	| 'edit'
	| 'copy'
	| 'forward'
	| 'reply'
	| 'share'

	// 业务核心图标
	| 'dashboard'
	| 'transactions'
	| 'invoices'
	| 'reports'
	| 'documents'
	| 'payroll'

	// 媒体
	| 'camera'
	| 'picture'
	| 'video'
	| 'video-off'
	| 'mic'
	| 'mic-off'
	| 'speaker'
	| 'speaker-off'

	// 状态
	| 'eye'
	| 'eye-off'
	| 'star'
	| 'like'
	| 'bookmark'
	| 'location'
	| 'time'

	// 文件和操作
	| 'file'
	| 'download'
	| 'upload'
	| 'link'
	| 'mail'

	// AI 和智能
	| 'ai'
	| 'translate'
	| 'translate-off'

	// 系统状态
	| 'loading'
	| 'error'
	| 'warning'
	| 'info'
	| 'success'
	| 'help'
	| 'report'

	// 其他
	| 'refresh'
	| 'filter'
	| 'qr-code'
	| 'bluetooth'
	| 'bluetooth-off'
	| 'wifi'
	| 'wifi-off'

	// 阶段3新增图标 - 特殊功能和变体
	| 'left'
	| 'right'
	| 'down'
	| 'up'
	| 'circleleft'
	| 'circleright'
	| 'circledown'
	| 'circleup'
	| 'circleadd'
	| 'circlecancel'
	| 'tick'
	| 'tickdouble'
	| 'circle'
	| 'radioselect'
	| 'square'
	| 'checkselect'
	| 'circleminus'
	| 'checkminus'
	| 'circlemore1'
	| 'circlemore2'
	| 'search1'
	| 'search2'
	| 'group'
	| 'app'
	| 'hashtag'
	| 'input'
	| 'picture1'
	| 'picture2'
	| 'text1'
	| 'text2'
	| 'voice'
	| 'pause';

// Filled 图标名称（来自 Figma）
export type FilledIconName =
	// 方向箭头
	| 'arrow-left'
	| 'arrow-right'
	| 'arrow-up'
	| 'arrow-down'
	| 'chevron-left'
	| 'chevron-right'
	| 'chevron-up'
	| 'chevron-down'

	// 圆形操作
	| 'add'
	| 'add-circle'
	| 'remove'
	| 'remove-circle'
	| 'check'
	| 'check-circle'
	| 'cancel'
	| 'cancel-circle'
	| 'more'
	| 'more-circle'

	// 选择器
	| 'radio'
	| 'radio-selected'
	| 'checkbox'
	| 'checkbox-selected'

	// 用户和操作
	| 'user'
	| 'users'
	| 'settings'
	| 'edit'
	| 'copy'
	| 'forward'
	| 'reply'
	| 'share'

	// 业务核心图标
	| 'dashboard'
	| 'transactions'
	| 'invoices'
	| 'reports'
	| 'documents'
	| 'payroll'

	// 媒体
	| 'camera'
	| 'picture'
	| 'video'
	| 'video-off'
	| 'mic'
	| 'mic-off'
	| 'speaker'
	| 'speaker-off'

	// 状态
	| 'eye'
	| 'eye-off'
	| 'star'
	| 'like'
	| 'bookmark'
	| 'location'
	| 'time'

	// 文件和操作
	| 'file'
	| 'download'
	| 'upload'
	| 'link'
	| 'mail'

	// AI 和智能
	| 'ai'
	| 'translate'
	| 'translate-off'

	// 系统状态
	| 'loading'
	| 'error'
	| 'warning'
	| 'info'
	| 'success'
	| 'help'
	| 'report'

	// 其他
	| 'refresh'
	| 'filter'
	| 'qr-code'
	| 'bluetooth'
	| 'bluetooth-off'
	| 'wifi'
	| 'wifi-off'

	// 阶段3新增图标 - 特殊功能和变体
	| 'left'
	| 'right'
	| 'down'
	| 'up'
	| 'circleleft'
	| 'circleright'
	| 'circledown'
	| 'circleup'
	| 'circleadd'
	| 'circlecancel'
	| 'tick'
	| 'tickdouble'
	| 'circle'
	| 'radioselect'
	| 'square'
	| 'checkselect'
	| 'circleminus'
	| 'checkminus'
	| 'circlemore1'
	| 'circlemore2'
	| 'search1'
	| 'search2'
	| 'group'
	| 'app'
	| 'hashtag'
	| 'input'
	| 'picture1'
	| 'picture2'
	| 'text1'
	| 'text2'
	| 'voice'
	| 'pause';

// 品牌图标名称
export type BrandIconName = 'beanflow' | 'beanflow-logo' | 'beanflow-icon' | 'logo';

// 所有图标名称的联合类型
export type IconName = LineIconName | FilledIconName | BrandIconName;

// 图标组件基础属性
export interface BaseIconProps {
	size?: IconSize | number;
	color?: string;
	class?: string;
	ariaLabel?: string;
	ariaHidden?: boolean;
}

// 统一 Icon 组件属性
export interface IconProps extends BaseIconProps {
	name: IconName;
	variant?: IconVariant;
}

// 图标尺寸映射（基于 Figma 标准）
export const ICON_SIZES = {
	xs: 16,
	sm: 18,
	md: 20, // Figma 基准尺寸
	lg: 24,
	xl: 32
} as const;

// 默认颜色映射（基于 Figma 设计系统）
export const ICON_COLORS = {
	primary: 'var(--color-primary-700)',
	secondary: 'var(--color-neutral-600)',
	surface: 'var(--color-surface-700)',
	success: 'var(--color-success-600)',
	warning: 'var(--color-warning-600)',
	error: 'var(--color-error-600)',
	info: 'var(--color-info-600)',
	current: 'currentColor'
} as const;

// 图标组件类型 (Svelte 5 uses Component instead of SvelteComponent)
export type IconComponentType = import('svelte').Component<BaseIconProps>;

// 图标映射表类型
export interface IconMap {
	line: Record<LineIconName, IconComponentType>;
	filled: Record<FilledIconName, IconComponentType>;
	brand: Record<BrandIconName, IconComponentType>;
}
