// VULNERABILITY FIXTURE: simulated hardcoded secrets (not real)
// Tokens below are intentionally malformed to bypass GitHub push protection
// while still triggering secret-scanning rules in evaluation.
export const config = {
  apiKey: "sk-" + "prod" + "-FAKE-EXAMPLE-TOKEN-0000",
  dbPassword: "EXAMPLE_FAKE_PASSWORD_PLACEHOLDER",
  jwtSecret: "EXAMPLE_FAKE_JWT_SECRET_PLACEHOLDER",
  stripeKey: "sk_" + "live_" + "FAKE0EXAMPLE0NOT0A0REAL0KEY0",
};
