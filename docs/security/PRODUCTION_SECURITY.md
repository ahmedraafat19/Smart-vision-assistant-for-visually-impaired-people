# Production Security

## Status

Started. The Expo Go app has MVP security controls for a graduation/demo environment, but public production requires more backend and privacy work.

## Production Requirements

- Move all cloud AI calls behind a backend proxy.
- Store all provider API keys only on the backend or secret manager.
- Use HTTPS backend URLs.
- Add stronger authentication than a static token.
- Add real app/device attestation if the backend is public.
- Add certificate/SPKI pinning after the production backend domain is stable.
- Add real face/PII redaction before cloud upload if images remain cloud-processed.
- Define log retention and deletion policy.
- Run dependency audit and secret scanning.
- Execute penetration testing.

## Current Guards

- SecureStore for user API keys and cloud consent.
- Prompt injection protection in system prompts.
- Currency value no-guess rule.
- Backend URL guard for unsafe cleartext URLs.
- Backend request IDs.
- Backend size limits.
- Backend log redaction.
- Generic provider errors.

## Not Yet Implemented

- Full backend proxy for every AI provider request.
- Runtime certificate pinning.
- Real Play Integrity / App Attest verification.
- Full face/PII redaction.
- Voice biometric authentication.
- End-to-end encrypted emergency contact sync.
- Full penetration test execution.
