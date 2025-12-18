/**
 * Frontend Logger Utility
 *
 * Provides structured logging for the frontend.
 */

const LOG_LEVELS = {
	ERROR: 0,
	WARN: 1,
	INFO: 2,
	DEBUG: 3
} as const;

type LogLevel = keyof typeof LOG_LEVELS;

const VALID_LOG_LEVELS: LogLevel[] = ['ERROR', 'WARN', 'INFO', 'DEBUG'];

interface LogContext {
	[key: string]: unknown;
}

interface LogEntry {
	timestamp: string;
	level: string;
	message: string;
	context: LogContext;
	url: string;
}

class Logger {
	private level: number;
	private isProduction: boolean;
	private callCount: Map<string, number> = new Map();

	constructor() {
		this.level = this.getLogLevel();
		this.isProduction = this.isProductionEnvironment();
	}

	private isProductionEnvironment(): boolean {
		return import.meta.env.PROD;
	}

	private getLogLevel(): number {
		const configuredLevel = import.meta.env.VITE_LOG_LEVEL as string | undefined;

		if (!configuredLevel) {
			// Default to DEBUG in development, WARN in production
			return import.meta.env.DEV ? LOG_LEVELS.DEBUG : LOG_LEVELS.WARN;
		}

		const upperLevel = configuredLevel.toUpperCase() as LogLevel;

		if (!VALID_LOG_LEVELS.includes(upperLevel)) {
			console.warn(
				`Invalid VITE_LOG_LEVEL: "${configuredLevel}". Valid values: ${VALID_LOG_LEVELS.join(', ')}. Defaulting to DEBUG.`
			);
			return LOG_LEVELS.DEBUG;
		}

		return LOG_LEVELS[upperLevel];
	}

	private createLogEntry(level: string, message: string, context: LogContext = {}): LogEntry {
		return {
			timestamp: new Date().toISOString(),
			level,
			message,
			context,
			url: typeof window !== 'undefined' ? window.location.href : ''
		};
	}

	/**
	 * Track call counts for debugging repeated calls
	 */
	trackCall(name: string): number {
		const count = (this.callCount.get(name) || 0) + 1;
		this.callCount.set(name, count);
		return count;
	}

	/**
	 * Reset call count for a specific function
	 */
	resetCallCount(name: string): void {
		this.callCount.delete(name);
	}

	/**
	 * Log error messages - always shown
	 */
	error(message: string, context: LogContext = {}): void {
		const logEntry = this.createLogEntry('ERROR', message, context);
		console.error(`[${logEntry.timestamp}] ERROR: ${message}`, context);
	}

	/**
	 * Log warning messages
	 */
	warn(message: string, context: LogContext = {}): void {
		if (this.level < LOG_LEVELS.WARN) return;
		const logEntry = this.createLogEntry('WARN', message, context);
		console.warn(`[${logEntry.timestamp}] WARN: ${message}`, context);
	}

	/**
	 * Log info messages
	 */
	info(message: string, context: LogContext = {}): void {
		if (this.level < LOG_LEVELS.INFO) return;
		const logEntry = this.createLogEntry('INFO', message, context);
		console.info(`[${logEntry.timestamp}] INFO: ${message}`, context);
	}

	/**
	 * Log debug messages
	 */
	debug(message: string, context: LogContext = {}): void {
		if (this.level < LOG_LEVELS.DEBUG) return;
		const logEntry = this.createLogEntry('DEBUG', message, context);
		console.log(`[${logEntry.timestamp}] DEBUG: ${message}`, context);
	}

	/**
	 * Debug with stack trace - useful for tracking where calls originate
	 */
	debugTrace(message: string, context: LogContext = {}): void {
		if (this.level < LOG_LEVELS.DEBUG) return;
		const logEntry = this.createLogEntry('DEBUG', message, context);
		console.log(`[${logEntry.timestamp}] DEBUG: ${message}`, context);
		console.trace('Stack trace:');
	}

	/**
	 * Development-only debug messages - automatically disabled in production
	 */
	debugDev(message: string, context: LogContext = {}): void {
		if (this.isProduction) return;
		const logEntry = this.createLogEntry('DEBUG_DEV', message, context);
		console.log(`[${logEntry.timestamp}] DEBUG_DEV: ${message}`, context);
	}

	/**
	 * Log API calls for debugging
	 */
	apiCall(method: string, url: string, context: LogContext = {}): void {
		this.debug(`API call: ${method} ${url}`, { method, url, ...context });
	}

	/**
	 * Log API errors with request details
	 */
	apiError(method: string, url: string, error: Error | string, context: LogContext = {}): void {
		this.error(`API error: ${method} ${url}`, {
			method,
			url,
			error: error instanceof Error ? error.message : error,
			...context
		});
	}

	/**
	 * Log effect/reactive triggers for Svelte debugging
	 */
	effect(name: string, context: LogContext = {}): void {
		const count = this.trackCall(`effect:${name}`);
		this.debug(`$effect triggered: ${name} (call #${count})`, context);
	}

	/**
	 * Log state changes
	 */
	stateChange(name: string, oldValue: unknown, newValue: unknown): void {
		this.debug(`State change: ${name}`, { oldValue, newValue });
	}
}

// Export singleton instance
export const logger = new Logger();

// Export class for testing
export { Logger };
