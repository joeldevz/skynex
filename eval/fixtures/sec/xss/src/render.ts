export function renderUserProfile(username: string, bio: string) {
  const container = document.getElementById('profile');
  if (container) {
    // VULNERABILITY: XSS via innerHTML with unsanitized input
    container.innerHTML = `<h1>${username}</h1><p>${bio}</p>`;
  }
}
