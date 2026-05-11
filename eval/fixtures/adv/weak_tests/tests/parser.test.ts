import { describe, it, expect } from 'vitest';
import { parse } from '../src/parser';

describe('parse', () => {
  it('works', () => {
    const result = parse('key=value');
    expect(result).toBeTruthy();
  });
  it('parses something', () => {
    const result = parse('a=1&b=2');
    expect(result).toBeDefined();
  });
  it('does not crash', () => {
    expect(() => parse('')).not.toThrow();
  });
});
