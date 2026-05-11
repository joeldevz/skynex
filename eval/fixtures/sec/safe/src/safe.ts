import { Pool } from 'pg';
const pool = new Pool();

export async function getUserById(id: string) {
  // SAFE: parameterized query
  const result = await pool.query('SELECT * FROM users WHERE id = $1', [id]);
  return result.rows[0];
}

export function renderText(text: string): string {
  // SAFE: using textContent equivalent
  return text.replace(/[<>&"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
