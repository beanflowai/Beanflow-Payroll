/**
 * 图标系统入口文件
 * 导出所有图标组件和类型定义
 */

// 主要组件
export { default as Icon } from './Icon.svelte';

// 类型定义
export type {
	IconProps,
	BaseIconProps,
	IconName,
	IconVariant,
	IconSize,
	LineIconName,
	FilledIconName,
	BrandIconName,
	IconComponentType,
	IconMap
} from './types';

// 常量
export { ICON_SIZES, ICON_COLORS } from './types';

// Linear 图标
export { default as ArrowLeftIcon } from './line/ArrowLeftIcon.svelte';
export { default as ArrowRightIcon } from './line/ArrowRightIcon.svelte';
export { default as SearchIcon } from './line/SearchIcon.svelte';
export { default as AddIcon } from './line/AddIcon.svelte';
export { default as SettingsIcon } from './line/SettingsIcon.svelte';
export { default as AIIcon } from './line/AIIcon.svelte';

// 业务核心图标
export { default as DashboardIcon } from './line/DashboardIcon.svelte';
export { default as TransactionsIcon } from './line/TransactionsIcon.svelte';
export { default as InvoicesIcon } from './line/InvoicesIcon.svelte';
export { default as ReportsIcon } from './line/ReportsIcon.svelte';
export { default as DocumentsIcon } from './line/DocumentsIcon.svelte';
export { default as PayrollIcon } from './line/PayrollIcon.svelte';

// 导航和状态图标
export { default as UserIcon } from './line/UserIcon.svelte';
export { default as ChevronLeftIcon } from './line/ChevronLeftIcon.svelte';
export { default as ChevronRightIcon } from './line/ChevronRightIcon.svelte';
export { default as ChevronUpIcon } from './line/ChevronUpIcon.svelte';
export { default as ChevronDownIcon } from './line/ChevronDownIcon.svelte';
export { default as CheckIcon } from './line/CheckIcon.svelte';
export { default as RemoveIcon } from './line/RemoveIcon.svelte';
export { default as SuccessIcon } from './line/SuccessIcon.svelte';
export { default as ErrorIcon } from './line/ErrorIcon.svelte';
export { default as WarningIcon } from './line/WarningIcon.svelte';
export { default as InfoIcon } from './line/InfoIcon.svelte';
export { default as LoadingIcon } from './line/LoadingIcon.svelte';
export { default as MoreIcon } from './line/MoreIcon.svelte';
export { default as HelpIcon } from './line/HelpIcon.svelte';
export { default as CloseIcon } from './line/CloseIcon.svelte';
export { default as MenuIcon } from './line/MenuIcon.svelte';
export { default as EditIcon } from './line/EditIcon.svelte';
export { default as EyeIcon } from './line/EyeIcon.svelte';
export { default as EyeOffIcon } from './line/EyeOffIcon.svelte';
export { default as RefreshIcon } from './line/RefreshIcon.svelte';
export { default as TimeIcon } from './line/TimeIcon.svelte';
export { default as DownloadIcon } from './line/DownloadIcon.svelte';
export { default as UploadIcon } from './line/UploadIcon.svelte';

// 阶段3新增图标 - 基础方向和箭头变体
export { default as LeftIcon } from './line/LeftIcon.svelte';
export { default as RightIcon } from './line/RightIcon.svelte';
export { default as DownIcon } from './line/DownIcon.svelte';
export { default as UpIcon } from './line/UpIcon.svelte';
export { default as CircleleftIcon } from './line/CircleleftIcon.svelte';
export { default as CirclerightIcon } from './line/CirclerightIcon.svelte';
export { default as CircledownIcon } from './line/CircledownIcon.svelte';
export { default as CircleupIcon } from './line/CircleupIcon.svelte';

// 阶段3新增图标 - 圆形操作变体
export { default as CircleaddIcon } from './line/CircleaddIcon.svelte';
export { default as CirclecancelIcon } from './line/CirclecancelIcon.svelte';
export { default as TickIcon } from './line/TickIcon.svelte';
export { default as TickdoubleIcon } from './line/TickdoubleIcon.svelte';
export { default as CircleIcon } from './line/CircleIcon.svelte';
export { default as RadioselectIcon } from './line/RadioselectIcon.svelte';
export { default as SquareIcon } from './line/SquareIcon.svelte';
export { default as CheckselectIcon } from './line/CheckselectIcon.svelte';
export { default as CircleminusIcon } from './line/CircleminusIcon.svelte';
export { default as CheckminusIcon } from './line/CheckminusIcon.svelte';
export { default as Circlemore1Icon } from './line/Circlemore1Icon.svelte';
export { default as Circlemore2Icon } from './line/Circlemore2Icon.svelte';

// 阶段3新增图标 - 搜索和应用变体
export { default as Search1Icon } from './line/Search1Icon.svelte';
export { default as Search2Icon } from './line/Search2Icon.svelte';
export { default as GroupIcon } from './line/GroupIcon.svelte';
export { default as AppIcon } from './line/AppIcon.svelte';
export { default as HashtagIcon } from './line/HashtagIcon.svelte';
export { default as InputIcon } from './line/InputIcon.svelte';

// 阶段3新增图标 - 文本和图片变体
export { default as Picture1Icon } from './line/Picture1Icon.svelte';
export { default as Picture2Icon } from './line/Picture2Icon.svelte';
export { default as Text1Icon } from './line/Text1Icon.svelte';
export { default as Text2Icon } from './line/Text2Icon.svelte';
export { default as VoiceIcon } from './line/VoiceIcon.svelte';
export { default as PauseIcon } from './line/PauseIcon.svelte';

// Filled 图标
export { default as HomeFilledIcon } from './filled/HomeIcon.svelte';
export { default as UserFilledIcon } from './filled/UserIcon.svelte';
export { default as AIFilledIcon } from './filled/AIIcon.svelte';

// Filled 业务核心图标
export { default as DashboardFilledIcon } from './filled/DashboardIcon.svelte';
export { default as TransactionsFilledIcon } from './filled/TransactionsIcon.svelte';
export { default as InvoicesFilledIcon } from './filled/InvoicesIcon.svelte';
export { default as ReportsFilledIcon } from './filled/ReportsIcon.svelte';
export { default as DocumentsFilledIcon } from './filled/DocumentsIcon.svelte';
export { default as PayrollFilledIcon } from './filled/PayrollIcon.svelte';

// Filled 用户操作图标
export { default as UsersFilledIcon } from './filled/UsersIcon.svelte';
export { default as SettingsFilledIcon } from './filled/SettingsIcon.svelte';
export { default as EditFilledIcon } from './filled/EditIcon.svelte';
export { default as CopyIcon } from './filled/CopyIcon.svelte';
export { default as ForwardIcon } from './filled/ForwardIcon.svelte';
export { default as ReplyIcon } from './filled/ReplyIcon.svelte';
export { default as ShareIcon } from './filled/ShareIcon.svelte';
export { default as FilterIcon } from './filled/FilterIcon.svelte';

// Filled 系统状态图标
export { default as LoadingFilledIcon } from './filled/LoadingIcon.svelte';
export { default as ErrorFilledIcon } from './filled/ErrorIcon.svelte';
export { default as WarningFilledIcon } from './filled/WarningIcon.svelte';
export { default as InfoFilledIcon } from './filled/InfoIcon.svelte';
export { default as SuccessFilledIcon } from './filled/SuccessIcon.svelte';
export { default as HelpFilledIcon } from './filled/HelpIcon.svelte';
export { default as ReportIcon } from './filled/ReportIcon.svelte';

// Filled 基础操作图标
export { default as AddFilledIcon } from './filled/AddIcon.svelte';
export { default as AddCircleIcon } from './filled/AddCircleIcon.svelte';
export { default as RemoveFilledIcon } from './filled/RemoveIcon.svelte';
export { default as RemoveCircleIcon } from './filled/RemoveCircleIcon.svelte';
export { default as CheckFilledIcon } from './filled/CheckIcon.svelte';
export { default as CheckCircleIcon } from './filled/CheckCircleIcon.svelte';
export { default as CancelIcon } from './filled/CancelIcon.svelte';
export { default as CancelCircleIcon } from './filled/CancelCircleIcon.svelte';
export { default as MoreFilledIcon } from './filled/MoreIcon.svelte';
export { default as MoreCircleIcon } from './filled/MoreCircleIcon.svelte';

// Filled 方向导航图标
export { default as ArrowLeftFilledIcon } from './filled/ArrowLeftIcon.svelte';
export { default as ArrowRightFilledIcon } from './filled/ArrowRightIcon.svelte';
export { default as ArrowUpFilledIcon } from './filled/ArrowUpIcon.svelte';
export { default as ArrowDownFilledIcon } from './filled/ArrowDownIcon.svelte';

// Filled 核心导航图标
export { default as ChevronLeftFilledIcon } from './filled/ChevronLeftIcon.svelte';
export { default as ChevronRightFilledIcon } from './filled/ChevronRightIcon.svelte';
export { default as ChevronUpFilledIcon } from './filled/ChevronUpIcon.svelte';
export { default as ChevronDownFilledIcon } from './filled/ChevronDownIcon.svelte';
export { default as MenuFilledIcon } from './filled/MenuIcon.svelte';
export { default as CloseFilledIcon } from './filled/CloseIcon.svelte';
export { default as LeftFilledIcon } from './filled/LeftIcon.svelte';
export { default as RightFilledIcon } from './filled/RightIcon.svelte';

// Filled 选择器系统图标
export { default as RadioFilledIcon } from './filled/RadioIcon.svelte';
export { default as RadioSelectedFilledIcon } from './filled/RadioSelectedIcon.svelte';
export { default as CheckboxFilledIcon } from './filled/CheckboxIcon.svelte';
export { default as CheckboxSelectedFilledIcon } from './filled/CheckboxSelectedIcon.svelte';
export { default as TickFilledIcon } from './filled/TickIcon.svelte';
export { default as TickDoubleFilledIcon } from './filled/TickDoubleIcon.svelte';
export { default as CircleFilledIcon } from './filled/CircleIcon.svelte';
export { default as SquareFilledIcon } from './filled/SquareIcon.svelte';

// Filled 圆形操作图标
export { default as CircleAddFilledIcon } from './filled/CircleAddIcon.svelte';
export { default as CircleCancelFilledIcon } from './filled/CircleCancelIcon.svelte';
export { default as CircleLeftFilledIcon } from './filled/CircleLeftIcon.svelte';
export { default as CircleRightFilledIcon } from './filled/CircleRightIcon.svelte';

// Filled 媒体功能图标
export { default as CameraFilledIcon } from './filled/CameraIcon.svelte';
export { default as PictureFilledIcon } from './filled/PictureIcon.svelte';
export { default as VideoFilledIcon } from './filled/VideoIcon.svelte';
export { default as VideoOffIcon } from './filled/VideoOffIcon.svelte';
export { default as MicFilledIcon } from './filled/MicIcon.svelte';
export { default as MicOffIcon } from './filled/MicOffIcon.svelte';
export { default as SpeakerFilledIcon } from './filled/SpeakerIcon.svelte';
export { default as SpeakerOffIcon } from './filled/SpeakerOffIcon.svelte';

// Filled 状态显示图标
export { default as EyeFilledIcon } from './filled/EyeIcon.svelte';
export { default as EyeOffFilledIcon } from './filled/EyeOffIcon.svelte';
export { default as StarFilledIcon } from './filled/StarIcon.svelte';
export { default as LikeFilledIcon } from './filled/LikeIcon.svelte';
export { default as BookmarkFilledIcon } from './filled/BookmarkIcon.svelte';
export { default as LocationFilledIcon } from './filled/LocationIcon.svelte';
export { default as TimeFilledIcon } from './filled/TimeIcon.svelte';

// Filled 文件操作图标
export { default as DownloadFilledIcon } from './filled/DownloadIcon.svelte';
export { default as UploadFilledIcon } from './filled/UploadIcon.svelte';
export { default as LinkFilledIcon } from './filled/LinkIcon.svelte';
export { default as MailFilledIcon } from './filled/MailIcon.svelte';

// Filled 系统功能图标
export { default as RefreshFilledIcon } from './filled/RefreshIcon.svelte';
export { default as QrCodeIcon } from './filled/QrCodeIcon.svelte';
export { default as BluetoothFilledIcon } from './filled/BluetoothIcon.svelte';
export { default as BluetoothOffIcon } from './filled/BluetoothOffIcon.svelte';
export { default as WifiFilledIcon } from './filled/WifiIcon.svelte';
export { default as WifiOffIcon } from './filled/WifiOffIcon.svelte';
export { default as TranslateFilledIcon } from './filled/TranslateIcon.svelte';
export { default as TranslateOffIcon } from './filled/TranslateOffIcon.svelte';

// Filled 文件和其他图标
export { default as FileFilledIcon } from './filled/FileIcon.svelte';
export { default as SearchFilledIcon } from './filled/SearchIcon.svelte';
export { default as SearchCircleIcon } from './filled/SearchCircleIcon.svelte';

// Filled 阶段3新增图标 - 方向变体
export { default as DownFilledIcon } from './filled/DownIcon.svelte';
export { default as UpFilledIcon } from './filled/UpIcon.svelte';
export { default as CircleDownFilledIcon } from './filled/CircleDownIcon.svelte';
export { default as CircleUpFilledIcon } from './filled/CircleUpIcon.svelte';

// Filled 阶段3新增图标 - 选择器变体
export { default as CheckSelectIcon } from './filled/CheckSelectIcon.svelte';
export { default as RadioSelectIcon } from './filled/RadioSelectIcon.svelte';
export { default as CheckMinusIcon } from './filled/CheckMinusIcon.svelte';
export { default as CircleMinusFilledIcon } from './filled/CircleMinusIcon.svelte';
export { default as CircleMore1Icon } from './filled/CircleMore1Icon.svelte';
export { default as CircleMore2Icon } from './filled/CircleMore2Icon.svelte';

// Filled 阶段3新增图标 - 搜索和应用变体
export { default as Search1FilledIcon } from './filled/Search1Icon.svelte';
export { default as Search2FilledIcon } from './filled/Search2Icon.svelte';
export { default as GroupFilledIcon } from './filled/GroupIcon.svelte';
export { default as AppFilledIcon } from './filled/AppIcon.svelte';
export { default as HashtagFilledIcon } from './filled/HashtagIcon.svelte';
export { default as InputFilledIcon } from './filled/InputIcon.svelte';

// Filled 阶段3新增图标 - 媒体和文本变体
export { default as Picture1FilledIcon } from './filled/Picture1Icon.svelte';
export { default as Picture2FilledIcon } from './filled/Picture2Icon.svelte';
export { default as Text1FilledIcon } from './filled/Text1Icon.svelte';
export { default as Text2FilledIcon } from './filled/Text2Icon.svelte';
export { default as VoiceFilledIcon } from './filled/VoiceIcon.svelte';
export { default as PauseFilledIcon } from './filled/PauseIcon.svelte';

// Brand 图标
export { default as BeanflowIcon } from './brand/BeanflowIcon.svelte';
export { default as BeanflowLogoIcon } from './brand/BeanflowLogoIcon.svelte';
export { default as BeanflowIconIcon } from './brand/BeanflowIconIcon.svelte';
export { default as LogoIcon } from './brand/LogoIcon.svelte';

// 图标映射表（用于动态加载）
export const ICON_REGISTRY = {
	// Linear 图标
	line: {
		'arrow-left': () => import('./line/ArrowLeftIcon.svelte').then((m) => m.default),
		'arrow-right': () => import('./line/ArrowRightIcon.svelte').then((m) => m.default),
		search: () => import('./line/SearchIcon.svelte').then((m) => m.default),
		add: () => import('./line/AddIcon.svelte').then((m) => m.default),
		settings: () => import('./line/SettingsIcon.svelte').then((m) => m.default),
		ai: () => import('./line/AIIcon.svelte').then((m) => m.default),

		// 业务核心图标
		dashboard: () => import('./line/DashboardIcon.svelte').then((m) => m.default),
		transactions: () => import('./line/TransactionsIcon.svelte').then((m) => m.default),
		invoices: () => import('./line/InvoicesIcon.svelte').then((m) => m.default),
		reports: () => import('./line/ReportsIcon.svelte').then((m) => m.default),
		documents: () => import('./line/DocumentsIcon.svelte').then((m) => m.default),
		payroll: () => import('./line/PayrollIcon.svelte').then((m) => m.default),

		// 导航和状态图标
		user: () => import('./line/UserIcon.svelte').then((m) => m.default),
		'chevron-left': () => import('./line/ChevronLeftIcon.svelte').then((m) => m.default),
		'chevron-right': () => import('./line/ChevronRightIcon.svelte').then((m) => m.default),
		'chevron-up': () => import('./line/ChevronUpIcon.svelte').then((m) => m.default),
		'chevron-down': () => import('./line/ChevronDownIcon.svelte').then((m) => m.default),
		check: () => import('./line/CheckIcon.svelte').then((m) => m.default),
		remove: () => import('./line/RemoveIcon.svelte').then((m) => m.default),
		success: () => import('./line/SuccessIcon.svelte').then((m) => m.default),
		error: () => import('./line/ErrorIcon.svelte').then((m) => m.default),
		warning: () => import('./line/WarningIcon.svelte').then((m) => m.default),
		info: () => import('./line/InfoIcon.svelte').then((m) => m.default),
		loading: () => import('./line/LoadingIcon.svelte').then((m) => m.default),
		more: () => import('./line/MoreIcon.svelte').then((m) => m.default),
		help: () => import('./line/HelpIcon.svelte').then((m) => m.default),
		close: () => import('./line/CloseIcon.svelte').then((m) => m.default),
		menu: () => import('./line/MenuIcon.svelte').then((m) => m.default),
		edit: () => import('./line/EditIcon.svelte').then((m) => m.default),
		eye: () => import('./line/EyeIcon.svelte').then((m) => m.default),
		'eye-off': () => import('./line/EyeOffIcon.svelte').then((m) => m.default),
		refresh: () => import('./line/RefreshIcon.svelte').then((m) => m.default),
		time: () => import('./line/TimeIcon.svelte').then((m) => m.default),
		download: () => import('./line/DownloadIcon.svelte').then((m) => m.default),
		upload: () => import('./line/UploadIcon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 基础方向和箭头变体
		left: () => import('./line/LeftIcon.svelte').then((m) => m.default),
		right: () => import('./line/RightIcon.svelte').then((m) => m.default),
		down: () => import('./line/DownIcon.svelte').then((m) => m.default),
		up: () => import('./line/UpIcon.svelte').then((m) => m.default),
		circleleft: () => import('./line/CircleleftIcon.svelte').then((m) => m.default),
		circleright: () => import('./line/CirclerightIcon.svelte').then((m) => m.default),
		circledown: () => import('./line/CircledownIcon.svelte').then((m) => m.default),
		circleup: () => import('./line/CircleupIcon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 圆形操作变体
		circleadd: () => import('./line/CircleaddIcon.svelte').then((m) => m.default),
		circlecancel: () => import('./line/CirclecancelIcon.svelte').then((m) => m.default),
		tick: () => import('./line/TickIcon.svelte').then((m) => m.default),
		tickdouble: () => import('./line/TickdoubleIcon.svelte').then((m) => m.default),
		circle: () => import('./line/CircleIcon.svelte').then((m) => m.default),
		radioselect: () => import('./line/RadioselectIcon.svelte').then((m) => m.default),
		square: () => import('./line/SquareIcon.svelte').then((m) => m.default),
		checkselect: () => import('./line/CheckselectIcon.svelte').then((m) => m.default),
		circleminus: () => import('./line/CircleminusIcon.svelte').then((m) => m.default),
		checkminus: () => import('./line/CheckminusIcon.svelte').then((m) => m.default),
		circlemore1: () => import('./line/Circlemore1Icon.svelte').then((m) => m.default),
		circlemore2: () => import('./line/Circlemore2Icon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 搜索和应用变体
		search1: () => import('./line/Search1Icon.svelte').then((m) => m.default),
		search2: () => import('./line/Search2Icon.svelte').then((m) => m.default),
		group: () => import('./line/GroupIcon.svelte').then((m) => m.default),
		app: () => import('./line/AppIcon.svelte').then((m) => m.default),
		hashtag: () => import('./line/HashtagIcon.svelte').then((m) => m.default),
		input: () => import('./line/InputIcon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 文本和图片变体
		picture1: () => import('./line/Picture1Icon.svelte').then((m) => m.default),
		picture2: () => import('./line/Picture2Icon.svelte').then((m) => m.default),
		text1: () => import('./line/Text1Icon.svelte').then((m) => m.default),
		text2: () => import('./line/Text2Icon.svelte').then((m) => m.default),
		voice: () => import('./line/VoiceIcon.svelte').then((m) => m.default),
		pause: () => import('./line/PauseIcon.svelte').then((m) => m.default)
	},
	// Filled 图标
	filled: {
		home: () => import('./filled/HomeIcon.svelte').then((m) => m.default),
		user: () => import('./filled/UserIcon.svelte').then((m) => m.default),
		ai: () => import('./filled/AIIcon.svelte').then((m) => m.default),

		// 业务核心图标
		dashboard: () => import('./filled/DashboardIcon.svelte').then((m) => m.default),
		transactions: () => import('./filled/TransactionsIcon.svelte').then((m) => m.default),
		invoices: () => import('./filled/InvoicesIcon.svelte').then((m) => m.default),
		reports: () => import('./filled/ReportsIcon.svelte').then((m) => m.default),
		documents: () => import('./filled/DocumentsIcon.svelte').then((m) => m.default),
		payroll: () => import('./filled/PayrollIcon.svelte').then((m) => m.default),

		// 用户操作图标
		users: () => import('./filled/UsersIcon.svelte').then((m) => m.default),
		settings: () => import('./filled/SettingsIcon.svelte').then((m) => m.default),
		edit: () => import('./filled/EditIcon.svelte').then((m) => m.default),
		copy: () => import('./filled/CopyIcon.svelte').then((m) => m.default),
		forward: () => import('./filled/ForwardIcon.svelte').then((m) => m.default),
		reply: () => import('./filled/ReplyIcon.svelte').then((m) => m.default),
		share: () => import('./filled/ShareIcon.svelte').then((m) => m.default),
		filter: () => import('./filled/FilterIcon.svelte').then((m) => m.default),

		// 系统状态图标
		loading: () => import('./filled/LoadingIcon.svelte').then((m) => m.default),
		error: () => import('./filled/ErrorIcon.svelte').then((m) => m.default),
		warning: () => import('./filled/WarningIcon.svelte').then((m) => m.default),
		info: () => import('./filled/InfoIcon.svelte').then((m) => m.default),
		success: () => import('./filled/SuccessIcon.svelte').then((m) => m.default),
		help: () => import('./filled/HelpIcon.svelte').then((m) => m.default),
		report: () => import('./filled/ReportIcon.svelte').then((m) => m.default),

		// 基础操作图标
		add: () => import('./filled/AddIcon.svelte').then((m) => m.default),
		'add-circle': () => import('./filled/AddCircleIcon.svelte').then((m) => m.default),
		remove: () => import('./filled/RemoveIcon.svelte').then((m) => m.default),
		'remove-circle': () => import('./filled/RemoveCircleIcon.svelte').then((m) => m.default),
		check: () => import('./filled/CheckIcon.svelte').then((m) => m.default),
		'check-circle': () => import('./filled/CheckCircleIcon.svelte').then((m) => m.default),
		cancel: () => import('./filled/CancelIcon.svelte').then((m) => m.default),
		'cancel-circle': () => import('./filled/CancelCircleIcon.svelte').then((m) => m.default),
		more: () => import('./filled/MoreIcon.svelte').then((m) => m.default),
		'more-circle': () => import('./filled/MoreCircleIcon.svelte').then((m) => m.default),

		// 方向导航图标
		'arrow-left': () => import('./filled/ArrowLeftIcon.svelte').then((m) => m.default),
		'arrow-right': () => import('./filled/ArrowRightIcon.svelte').then((m) => m.default),
		'arrow-up': () => import('./filled/ArrowUpIcon.svelte').then((m) => m.default),
		'arrow-down': () => import('./filled/ArrowDownIcon.svelte').then((m) => m.default),

		// 核心导航图标
		'chevron-left': () => import('./filled/ChevronLeftIcon.svelte').then((m) => m.default),
		'chevron-right': () => import('./filled/ChevronRightIcon.svelte').then((m) => m.default),
		'chevron-up': () => import('./filled/ChevronUpIcon.svelte').then((m) => m.default),
		'chevron-down': () => import('./filled/ChevronDownIcon.svelte').then((m) => m.default),
		menu: () => import('./filled/MenuIcon.svelte').then((m) => m.default),
		close: () => import('./filled/CloseIcon.svelte').then((m) => m.default),
		left: () => import('./filled/LeftIcon.svelte').then((m) => m.default),
		right: () => import('./filled/RightIcon.svelte').then((m) => m.default),

		// 选择器系统图标
		radio: () => import('./filled/RadioIcon.svelte').then((m) => m.default),
		'radio-selected': () => import('./filled/RadioSelectedIcon.svelte').then((m) => m.default),
		checkbox: () => import('./filled/CheckboxIcon.svelte').then((m) => m.default),
		'checkbox-selected': () =>
			import('./filled/CheckboxSelectedIcon.svelte').then((m) => m.default),
		tick: () => import('./filled/TickIcon.svelte').then((m) => m.default),
		tickdouble: () => import('./filled/TickDoubleIcon.svelte').then((m) => m.default),
		circle: () => import('./filled/CircleIcon.svelte').then((m) => m.default),
		square: () => import('./filled/SquareIcon.svelte').then((m) => m.default),

		// 圆形操作图标
		circleadd: () => import('./filled/CircleAddIcon.svelte').then((m) => m.default),
		circlecancel: () => import('./filled/CircleCancelIcon.svelte').then((m) => m.default),
		circleleft: () => import('./filled/CircleLeftIcon.svelte').then((m) => m.default),
		circleright: () => import('./filled/CircleRightIcon.svelte').then((m) => m.default),

		// 媒体功能图标
		camera: () => import('./filled/CameraIcon.svelte').then((m) => m.default),
		picture: () => import('./filled/PictureIcon.svelte').then((m) => m.default),
		video: () => import('./filled/VideoIcon.svelte').then((m) => m.default),
		'video-off': () => import('./filled/VideoOffIcon.svelte').then((m) => m.default),
		mic: () => import('./filled/MicIcon.svelte').then((m) => m.default),
		'mic-off': () => import('./filled/MicOffIcon.svelte').then((m) => m.default),
		speaker: () => import('./filled/SpeakerIcon.svelte').then((m) => m.default),
		'speaker-off': () => import('./filled/SpeakerOffIcon.svelte').then((m) => m.default),

		// 状态显示图标
		eye: () => import('./filled/EyeIcon.svelte').then((m) => m.default),
		'eye-off': () => import('./filled/EyeOffIcon.svelte').then((m) => m.default),
		star: () => import('./filled/StarIcon.svelte').then((m) => m.default),
		like: () => import('./filled/LikeIcon.svelte').then((m) => m.default),
		bookmark: () => import('./filled/BookmarkIcon.svelte').then((m) => m.default),
		location: () => import('./filled/LocationIcon.svelte').then((m) => m.default),
		time: () => import('./filled/TimeIcon.svelte').then((m) => m.default),

		// 文件操作图标
		download: () => import('./filled/DownloadIcon.svelte').then((m) => m.default),
		upload: () => import('./filled/UploadIcon.svelte').then((m) => m.default),
		link: () => import('./filled/LinkIcon.svelte').then((m) => m.default),
		mail: () => import('./filled/MailIcon.svelte').then((m) => m.default),

		// 系统功能图标
		refresh: () => import('./filled/RefreshIcon.svelte').then((m) => m.default),
		'qr-code': () => import('./filled/QrCodeIcon.svelte').then((m) => m.default),
		bluetooth: () => import('./filled/BluetoothIcon.svelte').then((m) => m.default),
		'bluetooth-off': () => import('./filled/BluetoothOffIcon.svelte').then((m) => m.default),
		wifi: () => import('./filled/WifiIcon.svelte').then((m) => m.default),
		'wifi-off': () => import('./filled/WifiOffIcon.svelte').then((m) => m.default),
		translate: () => import('./filled/TranslateIcon.svelte').then((m) => m.default),
		'translate-off': () => import('./filled/TranslateOffIcon.svelte').then((m) => m.default),

		// 文件和其他图标
		file: () => import('./filled/FileIcon.svelte').then((m) => m.default),
		search: () => import('./filled/SearchIcon.svelte').then((m) => m.default),
		'search-circle': () => import('./filled/SearchCircleIcon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 方向变体
		down: () => import('./filled/DownIcon.svelte').then((m) => m.default),
		up: () => import('./filled/UpIcon.svelte').then((m) => m.default),
		circledown: () => import('./filled/CircleDownIcon.svelte').then((m) => m.default),
		circleup: () => import('./filled/CircleUpIcon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 选择器变体
		checkselect: () => import('./filled/CheckSelectIcon.svelte').then((m) => m.default),
		radioselect: () => import('./filled/RadioSelectIcon.svelte').then((m) => m.default),
		checkminus: () => import('./filled/CheckMinusIcon.svelte').then((m) => m.default),
		circleminus: () => import('./filled/CircleMinusIcon.svelte').then((m) => m.default),
		circlemore1: () => import('./filled/CircleMore1Icon.svelte').then((m) => m.default),
		circlemore2: () => import('./filled/CircleMore2Icon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 搜索和应用变体
		search1: () => import('./filled/Search1Icon.svelte').then((m) => m.default),
		search2: () => import('./filled/Search2Icon.svelte').then((m) => m.default),
		group: () => import('./filled/GroupIcon.svelte').then((m) => m.default),
		app: () => import('./filled/AppIcon.svelte').then((m) => m.default),
		hashtag: () => import('./filled/HashtagIcon.svelte').then((m) => m.default),
		input: () => import('./filled/InputIcon.svelte').then((m) => m.default),

		// 阶段3新增图标 - 媒体和文本变体
		picture1: () => import('./filled/Picture1Icon.svelte').then((m) => m.default),
		picture2: () => import('./filled/Picture2Icon.svelte').then((m) => m.default),
		text1: () => import('./filled/Text1Icon.svelte').then((m) => m.default),
		text2: () => import('./filled/Text2Icon.svelte').then((m) => m.default),
		voice: () => import('./filled/VoiceIcon.svelte').then((m) => m.default),
		pause: () => import('./filled/PauseIcon.svelte').then((m) => m.default)
	},
	// Brand 图标
	brand: {
		beanflow: () => import('./brand/BeanflowIcon.svelte').then((m) => m.default),
		'beanflow-logo': () => import('./brand/BeanflowLogoIcon.svelte').then((m) => m.default),
		'beanflow-icon': () => import('./brand/BeanflowIconIcon.svelte').then((m) => m.default),
		logo: () => import('./brand/LogoIcon.svelte').then((m) => m.default)
	}
} as const;

// 动态图标加载函数
export async function loadIcon(name: string, variant: 'line' | 'filled' | 'brand' = 'line') {
	const iconLoader = ICON_REGISTRY[variant]?.[
		name as keyof (typeof ICON_REGISTRY)[typeof variant]
	] as (() => Promise<any>) | undefined;

	if (!iconLoader) {
		throw new Error(`Icon "${name}" not found in variant "${variant}"`);
	}

	return await iconLoader();
}

// 图标列表（用于文档和预览）
export const AVAILABLE_ICONS = {
	line: Object.keys(ICON_REGISTRY.line),
	filled: Object.keys(ICON_REGISTRY.filled),
	brand: Object.keys(ICON_REGISTRY.brand)
} as const;
