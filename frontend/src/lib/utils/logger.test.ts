/**
 * Tests for logger utility
 */

import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { Logger, logger } from './logger';

describe('Logger', () => {
	let consoleSpy: {
		error: ReturnType<typeof vi.spyOn>;
		warn: ReturnType<typeof vi.spyOn>;
		info: ReturnType<typeof vi.spyOn>;
		log: ReturnType<typeof vi.spyOn>;
		trace: ReturnType<typeof vi.spyOn>;
	};

	beforeEach(() => {
		consoleSpy = {
			error: vi.spyOn(console, 'error').mockImplementation(() => {}),
			warn: vi.spyOn(console, 'warn').mockImplementation(() => {}),
			info: vi.spyOn(console, 'info').mockImplementation(() => {}),
			log: vi.spyOn(console, 'log').mockImplementation(() => {}),
			trace: vi.spyOn(console, 'trace').mockImplementation(() => {})
		};
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('logger singleton', () => {
		it('exports a Logger instance', () => {
			expect(logger).toBeInstanceOf(Logger);
		});
	});

	describe('error', () => {
		it('logs error messages with timestamp', () => {
			const testLogger = new Logger();
			testLogger.error('Test error message');

			expect(consoleSpy.error).toHaveBeenCalled();
			const call = consoleSpy.error.mock.calls[0][0];
			expect(call).toContain('ERROR');
			expect(call).toContain('Test error message');
		});

		it('includes context in error log', () => {
			const testLogger = new Logger();
			testLogger.error('Error with context', { userId: '123', action: 'save' });

			expect(consoleSpy.error).toHaveBeenCalled();
			const context = consoleSpy.error.mock.calls[0][1];
			expect(context).toEqual({ userId: '123', action: 'save' });
		});
	});

	describe('warn', () => {
		it('logs warning messages with timestamp', () => {
			const testLogger = new Logger();
			testLogger.warn('Test warning message');

			expect(consoleSpy.warn).toHaveBeenCalled();
			const call = consoleSpy.warn.mock.calls[0][0];
			expect(call).toContain('WARN');
			expect(call).toContain('Test warning message');
		});

		it('includes context in warning log', () => {
			const testLogger = new Logger();
			testLogger.warn('Warning with context', { field: 'email' });

			const context = consoleSpy.warn.mock.calls[0][1];
			expect(context).toEqual({ field: 'email' });
		});
	});

	describe('info', () => {
		it('logs info messages with timestamp', () => {
			const testLogger = new Logger();
			testLogger.info('Test info message');

			expect(consoleSpy.info).toHaveBeenCalled();
			const call = consoleSpy.info.mock.calls[0][0];
			expect(call).toContain('INFO');
			expect(call).toContain('Test info message');
		});

		it('includes context in info log', () => {
			const testLogger = new Logger();
			testLogger.info('Info with context', { operation: 'create' });

			const context = consoleSpy.info.mock.calls[0][1];
			expect(context).toEqual({ operation: 'create' });
		});
	});

	describe('debug', () => {
		it('logs debug messages with timestamp', () => {
			const testLogger = new Logger();
			testLogger.debug('Test debug message');

			expect(consoleSpy.log).toHaveBeenCalled();
			const call = consoleSpy.log.mock.calls[0][0];
			expect(call).toContain('DEBUG');
			expect(call).toContain('Test debug message');
		});

		it('includes context in debug log', () => {
			const testLogger = new Logger();
			testLogger.debug('Debug with context', { data: [1, 2, 3] });

			const context = consoleSpy.log.mock.calls[0][1];
			expect(context).toEqual({ data: [1, 2, 3] });
		});
	});

	describe('debugTrace', () => {
		it('logs debug message and stack trace', () => {
			const testLogger = new Logger();
			testLogger.debugTrace('Trace message');

			expect(consoleSpy.log).toHaveBeenCalled();
			expect(consoleSpy.trace).toHaveBeenCalledWith('Stack trace:');
		});
	});

	describe('debugDev', () => {
		it('logs debug message in development mode', () => {
			const testLogger = new Logger();
			testLogger.debugDev('Dev debug message');

			expect(consoleSpy.log).toHaveBeenCalled();
			const call = consoleSpy.log.mock.calls[0][0];
			expect(call).toContain('DEBUG_DEV');
			expect(call).toContain('Dev debug message');
		});
	});

	describe('apiCall', () => {
		it('logs API calls with method and URL', () => {
			const testLogger = new Logger();
			testLogger.apiCall('GET', '/api/users');

			expect(consoleSpy.log).toHaveBeenCalled();
			const call = consoleSpy.log.mock.calls[0][0];
			expect(call).toContain('API call: GET /api/users');
		});

		it('includes additional context', () => {
			const testLogger = new Logger();
			testLogger.apiCall('POST', '/api/data', { body: { name: 'test' } });

			const context = consoleSpy.log.mock.calls[0][1];
			expect(context).toMatchObject({
				method: 'POST',
				url: '/api/data',
				body: { name: 'test' }
			});
		});
	});

	describe('apiError', () => {
		it('logs API errors with method and URL', () => {
			const testLogger = new Logger();
			testLogger.apiError('POST', '/api/save', 'Network error');

			expect(consoleSpy.error).toHaveBeenCalled();
			const call = consoleSpy.error.mock.calls[0][0];
			expect(call).toContain('API error: POST /api/save');
		});

		it('handles Error objects', () => {
			const testLogger = new Logger();
			const error = new Error('Something went wrong');
			testLogger.apiError('GET', '/api/data', error);

			const context = consoleSpy.error.mock.calls[0][1];
			expect(context.error).toBe('Something went wrong');
		});

		it('handles string errors', () => {
			const testLogger = new Logger();
			testLogger.apiError('PUT', '/api/update', 'Failed to update');

			const context = consoleSpy.error.mock.calls[0][1];
			expect(context.error).toBe('Failed to update');
		});
	});

	describe('effect', () => {
		it('logs effect triggers with call count', () => {
			const testLogger = new Logger();
			testLogger.effect('fetchData');

			expect(consoleSpy.log).toHaveBeenCalled();
			const call = consoleSpy.log.mock.calls[0][0];
			expect(call).toContain('$effect triggered: fetchData (call #1)');
		});

		it('increments call count on repeated calls', () => {
			const testLogger = new Logger();
			testLogger.effect('loadUsers');
			testLogger.effect('loadUsers');
			testLogger.effect('loadUsers');

			expect(consoleSpy.log).toHaveBeenCalledTimes(3);
			const lastCall = consoleSpy.log.mock.calls[2][0];
			expect(lastCall).toContain('(call #3)');
		});
	});

	describe('stateChange', () => {
		it('logs state changes with old and new values', () => {
			const testLogger = new Logger();
			testLogger.stateChange('selectedUser', null, { id: 1, name: 'John' });

			expect(consoleSpy.log).toHaveBeenCalled();
			const call = consoleSpy.log.mock.calls[0][0];
			expect(call).toContain('State change: selectedUser');

			const context = consoleSpy.log.mock.calls[0][1];
			expect(context).toEqual({
				oldValue: null,
				newValue: { id: 1, name: 'John' }
			});
		});
	});

	describe('trackCall', () => {
		it('tracks call counts', () => {
			const testLogger = new Logger();
			expect(testLogger.trackCall('testFn')).toBe(1);
			expect(testLogger.trackCall('testFn')).toBe(2);
			expect(testLogger.trackCall('testFn')).toBe(3);
		});

		it('tracks different functions separately', () => {
			const testLogger = new Logger();
			expect(testLogger.trackCall('fn1')).toBe(1);
			expect(testLogger.trackCall('fn2')).toBe(1);
			expect(testLogger.trackCall('fn1')).toBe(2);
		});
	});

	describe('resetCallCount', () => {
		it('resets call count for a specific function', () => {
			const testLogger = new Logger();
			testLogger.trackCall('fn');
			testLogger.trackCall('fn');
			expect(testLogger.trackCall('fn')).toBe(3);

			testLogger.resetCallCount('fn');
			expect(testLogger.trackCall('fn')).toBe(1);
		});

		it('does not affect other function counts', () => {
			const testLogger = new Logger();
			testLogger.trackCall('fn1');
			testLogger.trackCall('fn2');

			testLogger.resetCallCount('fn1');

			expect(testLogger.trackCall('fn1')).toBe(1);
			expect(testLogger.trackCall('fn2')).toBe(2);
		});
	});
});
