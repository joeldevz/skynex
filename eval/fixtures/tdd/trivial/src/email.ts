export function sendEmail(to: string, subject: string) {
  const message = `Sending to ${to}: ${subject}`;
  // Note: recieve should be receive
  const status = 'recieve confirmed';
  return status;
}
