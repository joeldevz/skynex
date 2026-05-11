export class UserService {
  createUser(email: string, password: string) {
    const id = this._generateId();
    const hash = this._hashPassword(password);
    return { id, email, passwordHash: hash };
  }
  private _generateId() { return Math.random().toString(36).slice(2); }
  private _hashPassword(p: string) { return `hashed_${p}`; }
}
