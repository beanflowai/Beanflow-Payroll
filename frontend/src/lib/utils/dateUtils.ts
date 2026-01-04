/**
 * Date Utility Functions (TypeScript version)
 * Based on beancount-LLM/frontend/src/lib/utils/dateUtils.js
 */

// ============ 类型定义 ============

export type DateRangePeriod =
	| 'today'
	| 'yesterday'
	| 'thisWeek'
	| 'thisMonth'
	| 'lastMonth'
	| 'thisYear'
	| 'lastYear'
	| 'last30Days'
	| 'last90Days';

export interface DateRange {
	from: string;
	to: string;
}

// ============ 基础函数 ============

/**
 * Get current date in YYYY-MM-DD format
 */
export function getCurrentDate(): string {
	return new Date().toISOString().split('T')[0];
}

/**
 * Get first day of current month in YYYY-MM-DD format
 */
export function getCurrentMonthStart(): string {
	const now = new Date();
	const year = now.getFullYear();
	const month = String(now.getMonth() + 1).padStart(2, '0');
	return `${year}-${month}-01`;
}

/**
 * Get last day of current month in YYYY-MM-DD format
 */
export function getCurrentMonthEnd(): string {
	const now = new Date();
	const year = now.getFullYear();
	const month = now.getMonth() + 1;
	const lastDay = new Date(year, month, 0).getDate();
	return `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
}

/**
 * Get date range for common periods
 */
export function getDateRange(period: DateRangePeriod): DateRange {
	const now = new Date();
	const year = now.getFullYear();
	const month = now.getMonth();

	switch (period) {
		case 'today': {
			const today = getCurrentDate();
			return { from: today, to: today };
		}

		case 'yesterday': {
			const yesterday = new Date(now);
			yesterday.setDate(yesterday.getDate() - 1);
			const yesterdayStr = yesterday.toISOString().split('T')[0];
			return { from: yesterdayStr, to: yesterdayStr };
		}

		case 'thisWeek': {
			const startOfWeek = new Date(now);
			startOfWeek.setDate(now.getDate() - now.getDay());
			const endOfWeek = new Date(startOfWeek);
			endOfWeek.setDate(startOfWeek.getDate() + 6);
			return {
				from: startOfWeek.toISOString().split('T')[0],
				to: endOfWeek.toISOString().split('T')[0]
			};
		}

		case 'thisMonth':
			return {
				from: getCurrentMonthStart(),
				to: getCurrentMonthEnd()
			};

		case 'lastMonth': {
			const lastMonth = new Date(year, month - 1);
			const lastMonthStart = new Date(lastMonth.getFullYear(), lastMonth.getMonth(), 1);
			const lastMonthEnd = new Date(lastMonth.getFullYear(), lastMonth.getMonth() + 1, 0);
			return {
				from: lastMonthStart.toISOString().split('T')[0],
				to: lastMonthEnd.toISOString().split('T')[0]
			};
		}

		case 'thisYear':
			return {
				from: `${year}-01-01`,
				to: `${year}-12-31`
			};

		case 'lastYear':
			return {
				from: `${year - 1}-01-01`,
				to: `${year - 1}-12-31`
			};

		case 'last30Days': {
			const thirtyDaysAgo = new Date(now);
			thirtyDaysAgo.setDate(now.getDate() - 30);
			return {
				from: thirtyDaysAgo.toISOString().split('T')[0],
				to: getCurrentDate()
			};
		}

		case 'last90Days': {
			const ninetyDaysAgo = new Date(now);
			ninetyDaysAgo.setDate(now.getDate() - 90);
			return {
				from: ninetyDaysAgo.toISOString().split('T')[0],
				to: getCurrentDate()
			};
		}

		default:
			return { from: '', to: '' };
	}
}

/**
 * Validate date string format (YYYY-MM-DD)
 */
export function isValidDate(dateString: string): boolean {
	if (!dateString) return false;
	const regex = /^\d{4}-\d{2}-\d{2}$/;
	if (!regex.test(dateString)) return false;

	const date = new Date(dateString + 'T00:00:00');
	return date instanceof Date && !isNaN(date.getTime());
}

/**
 * Compare two date strings
 */
export function compareDates(date1: string, date2: string): number {
	if (!date1 || !date2) return 0;
	return date1.localeCompare(date2);
}

/**
 * Check if date is in range
 */
export function isDateInRange(date: string, fromDate?: string, toDate?: string): boolean {
	if (!date) return false;
	if (fromDate && date < fromDate) return false;
	if (toDate && date > toDate) return false;
	return true;
}

/**
 * Get relative date description
 */
export function getRelativeDateDescription(dateString: string): string {
	if (!dateString) return '';

	const date = new Date(dateString + 'T00:00:00');
	const now = new Date();
	const diffTime = now.getTime() - date.getTime();
	const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

	if (diffDays === 0) return 'Today';
	if (diffDays === 1) return 'Yesterday';
	if (diffDays === -1) return 'Tomorrow';
	if (diffDays > 1 && diffDays <= 7) return `${diffDays} days ago`;
	if (diffDays < -1 && diffDays >= -7) return `In ${Math.abs(diffDays)} days`;
	if (diffDays > 7 && diffDays <= 30) return `${Math.floor(diffDays / 7)} weeks ago`;
	if (diffDays < -7 && diffDays >= -30) return `In ${Math.floor(Math.abs(diffDays) / 7)} weeks`;

	return date.toLocaleDateString('en-CA');
}

/**
 * Formats a Date object for HTML date input (YYYY-MM-DD format)
 */
export function formatDateForInput(date: Date): string {
	if (!date || !(date instanceof Date) || isNaN(date.getTime())) {
		return '';
	}
	return date.toISOString().split('T')[0];
}

/**
 * Parses a date string from HTML date input into a Date object
 */
export function parseInputDate(dateString: string): Date | null {
	if (!dateString || typeof dateString !== 'string') {
		return null;
	}

	if (!isValidDate(dateString)) {
		return null;
	}

	const date = new Date(dateString + 'T00:00:00');
	return isNaN(date.getTime()) ? null : date;
}

// ============ UI 显示函数 (修复时区问题) ============

/**
 * 安全解析 ISO 日期字符串，避免时区偏移
 * 使用 T12:00:00 确保任何时区都显示正确日期
 */
export function parseDateString(dateStr: string): Date {
	return new Date(dateStr + 'T12:00:00');
}

/**
 * 格式化月份字符串 (YYYY-MM) 为可读格式
 */
export function formatMonth(monthString: string): string {
	const [year, month] = monthString.split('-');
	const date = new Date(parseInt(year), parseInt(month) - 1);
	return date.toLocaleDateString('en-CA', {
		year: 'numeric',
		month: 'long'
	});
}

/**
 * 格式化完整日期（含星期）- 用于 UI 显示
 * @param dateStr - ISO 日期字符串 (YYYY-MM-DD)
 * @returns 格式化的日期字符串，如 "Saturday, December 28, 2025"
 */
export function formatFullDate(dateStr: string): string {
	const date = parseDateString(dateStr);
	return date.toLocaleDateString('en-CA', {
		weekday: 'long',
		year: 'numeric',
		month: 'long',
		day: 'numeric'
	});
}

/**
 * 格式化短日期 - 用于 UI 显示
 * @param dateStr - ISO 日期字符串 (YYYY-MM-DD)
 * @returns 格式化的日期字符串，如 "Dec 28, 2025"
 */
export function formatShortDate(dateStr: string): string {
	const date = parseDateString(dateStr);
	return date.toLocaleDateString('en-CA', {
		year: 'numeric',
		month: 'short',
		day: 'numeric'
	});
}

/**
 * 格式化日期范围 - 用于 UI 显示
 * @param startDate - 开始日期 (YYYY-MM-DD)
 * @param endDate - 结束日期 (YYYY-MM-DD)
 * @returns 格式化的日期范围，如 "Dec 8 - Dec 21"
 */
export function formatDateRange(startDate: string, endDate: string): string {
	const start = parseDateString(startDate);
	const end = parseDateString(endDate);

	const startMonth = start.toLocaleDateString('en-CA', { month: 'short' });
	const endMonth = end.toLocaleDateString('en-CA', { month: 'short' });
	const startDay = start.getDate();
	const endDay = end.getDate();

	if (startMonth === endMonth) {
		return `${startMonth} ${startDay} - ${endDay}`;
	}
	return `${startMonth} ${startDay} - ${endMonth} ${endDay}`;
}

/**
 * 格式化日期时间 - 用于时间戳显示
 * @param dateTimeStr - ISO 日期时间字符串 (包含时间部分)
 * @returns 格式化的日期时间字符串，如 "Dec 24, 2025, 3:45 PM"
 */
export function formatDateTime(dateTimeStr: string): string {
	const date = new Date(dateTimeStr);
	return date.toLocaleDateString('en-CA', {
		month: 'short',
		day: 'numeric',
		year: 'numeric',
		hour: 'numeric',
		minute: '2-digit'
	});
}

/**
 * 格式化长日期 (完整月份名称) - 用于 UI 显示
 * @param dateStr - ISO 日期字符串 (YYYY-MM-DD)
 * @returns 格式化的日期字符串，如 "December 28, 2025"
 */
export function formatLongDate(dateStr: string): string {
	const date = parseDateString(dateStr);
	return date.toLocaleDateString('en-CA', {
		month: 'long',
		day: 'numeric',
		year: 'numeric'
	});
}

/**
 * 格式化短日期 (无年份) - 用于日期范围内的显示
 * @param dateStr - ISO 日期字符串 (YYYY-MM-DD)
 * @returns 格式化的日期字符串，如 "Dec 28"
 */
export function formatDateNoYear(dateStr: string): string {
	const date = parseDateString(dateStr);
	return date.toLocaleDateString('en-CA', {
		month: 'short',
		day: 'numeric'
	});
}

/**
 * 通用日期格式化函数 - 支持 null 值处理
 * 等同于 formatShortDate，但支持 null/undefined 输入
 * @param dateStr - ISO 日期字符串 (YYYY-MM-DD) 或 null/undefined
 * @param fallback - 当日期为空时返回的默认值 (默认 '-')
 * @returns 格式化的日期字符串，如 "Dec 28, 2025" 或 fallback
 */
export function formatDate(dateStr: string | null | undefined, fallback = '-'): string {
	if (!dateStr) return fallback;
	return formatShortDate(dateStr);
}

/**
 * 相对时间显示 - 用于显示 "刚刚", "5分钟前", "2小时前" 等
 * @param dateStr - ISO 日期时间字符串
 * @returns 相对时间字符串
 */
export function timeAgo(dateStr: string): string {
	const date = new Date(dateStr);
	const now = new Date();
	const diffMs = now.getTime() - date.getTime();
	const diffMins = Math.floor(diffMs / 60000);
	const diffHours = Math.floor(diffMs / 3600000);
	const diffDays = Math.floor(diffMs / 86400000);

	if (diffMins < 1) return 'Just now';
	if (diffMins < 60) return `${diffMins}m ago`;
	if (diffHours < 24) return `${diffHours}h ago`;
	if (diffDays < 7) return `${diffDays}d ago`;
	return formatShortDate(dateStr.split('T')[0]);
}
