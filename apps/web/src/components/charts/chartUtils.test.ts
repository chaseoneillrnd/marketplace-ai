import { describe, it, expect } from 'vitest';
import { abbreviateCount, formatTick, rollingAverage } from './chartUtils';

describe('abbreviateCount', () => {
  it('returns plain number below 1000', () => {
    expect(abbreviateCount(999)).toBe('999');
  });

  it('abbreviates thousands with k', () => {
    expect(abbreviateCount(1000)).toBe('1.0k');
  });

  it('abbreviates 1500 as 1.5k', () => {
    expect(abbreviateCount(1500)).toBe('1.5k');
  });

  it('abbreviates millions with M', () => {
    expect(abbreviateCount(1000000)).toBe('1.0M');
  });

  it('abbreviates 2500000 as 2.5M', () => {
    expect(abbreviateCount(2500000)).toBe('2.5M');
  });
});

describe('formatTick', () => {
  it('delegates to abbreviateCount', () => {
    expect(formatTick(1500)).toBe('1.5k');
    expect(formatTick(500)).toBe('500');
    expect(formatTick(1000000)).toBe('1.0M');
  });
});

describe('rollingAverage', () => {
  it('computes rolling average with window 3', () => {
    const data = [{ value: 1 }, { value: 2 }, { value: 3 }, { value: 4 }, { value: 5 }];
    const result = rollingAverage(data, 3);
    expect(result).toEqual([
      { value: 1 },       // avg(1)
      { value: 1.5 },     // avg(1,2)
      { value: 2 },       // avg(1,2,3)
      { value: 3 },       // avg(2,3,4)
      { value: 4 },       // avg(3,4,5)
    ]);
  });

  it('handles window of 1 (identity)', () => {
    const data = [{ value: 10 }, { value: 20 }];
    const result = rollingAverage(data, 1);
    expect(result).toEqual([{ value: 10 }, { value: 20 }]);
  });

  it('handles empty array', () => {
    expect(rollingAverage([], 3)).toEqual([]);
  });
});
