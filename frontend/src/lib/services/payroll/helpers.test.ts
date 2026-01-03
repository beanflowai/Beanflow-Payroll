import { describe, it, expect } from 'vitest';
import { getProvincialBpa } from './helpers';

describe('getProvincialBpa', () => {
	it('returns correct BPA for Alberta', () => {
		expect(getProvincialBpa('AB')).toBe('22323.00');
	});

	it('returns correct BPA for Ontario', () => {
		expect(getProvincialBpa('ON')).toBe('12747.00');
	});

	it('returns correct BPA for British Columbia', () => {
		expect(getProvincialBpa('BC')).toBe('12932.00');
	});

	it('returns Ontario BPA as default for unknown province', () => {
		expect(getProvincialBpa('XX')).toBe('12747.00');
	});

	it('returns Ontario BPA for Quebec (falls back to default)', () => {
		expect(getProvincialBpa('QC')).toBe('12747.00');
	});
});
