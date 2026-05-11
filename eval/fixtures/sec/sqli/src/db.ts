import { Pool } from 'pg';
const pool = new Pool();

export async function getUserById(id: string) {
  // VULNERABILITY: SQL injection via string concatenation
  const query = "SELECT * FROM users WHERE id = '" + id + "'";
  const result = await pool.query(query);
  return result.rows[0];
}
