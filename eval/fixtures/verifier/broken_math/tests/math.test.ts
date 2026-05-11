import { describe, it, expect } from 'vitest';
import { add } from '../src/math';
describe('add', () => {
  it('adds correctly', () => { expect(add(2, 3)).toBe(5); });
});
