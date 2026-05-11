import { describe, it, expect } from 'vitest';
import { add, subtract } from '../src/math';
describe('add', () => {
  it('returns sum of two positive numbers', () => { expect(add(2, 3)).toBe(5); });
  it('handles negative numbers', () => { expect(add(-1, -2)).toBe(-3); });
  it('handles zero', () => { expect(add(0, 5)).toBe(5); });
});
describe('subtract', () => {
  it('returns difference', () => { expect(subtract(5, 3)).toBe(2); });
  it('handles negative result', () => { expect(subtract(3, 5)).toBe(-2); });
});
