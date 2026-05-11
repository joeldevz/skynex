import { describe, it, expect } from 'vitest';
import { parse } from '../src/parser';
describe('parse', () => {
  it('works', () => { expect(parse('a=1')).toBeTruthy(); });
  it('returns something', () => { expect(parse('x=y')).toBeDefined(); });
  it('handles input', () => { const r = parse('k=v'); expect(r).not.toBeNull(); });
});
