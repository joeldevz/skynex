import { describe, it, expect, vi } from 'vitest';
import { UserService } from '../src/service';
describe('UserService', () => {
  it('calls _hashPassword internally', () => {
    const svc = new UserService();
    const spy = vi.spyOn(svc as any, '_hashPassword');
    svc.createUser('test@test.com', 'pass123');
    expect(spy).toHaveBeenCalledWith('pass123');
  });
  it('uses _generateId', () => {
    const svc = new UserService();
    const spy = vi.spyOn(svc as any, '_generateId');
    svc.createUser('a@b.com', 'x');
    expect(spy).toHaveBeenCalled();
  });
});
