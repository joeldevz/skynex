import { describe, it, expect } from 'vitest';
import { add } from '../src/math';

describe('add', () => {
  it('adds two positive numbers', () => {
    expect(add(2, 3)).toBe(5);
  });
  it('handles zero', () => {
    expect(add(0, 5)).toBe(5);
  });
  it('handles negatives', () => {
    expect(add(-1, -2)).toBe(-3);
  });
});
