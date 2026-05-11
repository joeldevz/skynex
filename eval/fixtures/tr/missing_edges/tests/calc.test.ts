import { describe, it, expect } from 'vitest';
import { divide } from '../src/calc';
describe('divide', () => {
  it('divides 10 by 2', () => { expect(divide(10, 2)).toBe(5); });
  it('divides 9 by 3', () => { expect(divide(9, 3)).toBe(3); });
});
// Missing: zero division, negative numbers, floating point, large numbers
