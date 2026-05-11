// Starter file for JWT verification middleware
import { Request, Response, NextFunction } from 'express';

export function authMiddleware(req: Request, res: Response, next: NextFunction) {
  // TODO: implement JWT verification
  next();
}
