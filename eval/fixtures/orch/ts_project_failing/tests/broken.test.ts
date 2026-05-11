import { describe, it, expect } from 'vitest';
describe('forced failure', () => {
  it('always fails', () => { expect(1).toBe(2); });
});
