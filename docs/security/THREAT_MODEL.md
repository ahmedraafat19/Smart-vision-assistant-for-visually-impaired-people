# Threat Model

## Scope

This threat model covers the Expo Go app, camera frames, voice commands, saved face references, local currency model, local Python backend, and cloud AI calls.

## Primary Assets

- User API keys saved in secure storage.
- Camera frames.
- Voice command audio.
- Saved face references.
- Cloud consent state.
- Egyptian banknote recognition result.
- Backend Gemini TTS key when configured.

## Trust Boundaries

1. User device and Expo app.
2. App to OpenRouter/Gemini cloud API.
3. App to local/private backend.
4. Backend to Gemini TTS service.
5. Backend to local currency model process.
6. Secure storage boundary for keys and consent.

## Implemented Controls

- `expo-secure-store` for user API keys and cloud consent.
- Prompt rules that reject image prompt injection.
- Currency value no-guess rule.
- Backend URL guard.
- Backend request IDs and generic JSON errors.
- Backend body/image size limits.
- Backend log redaction.
- OpenRouter privacy routing options where supported.

## Key Threats and Status

| Threat | Current Control | Remaining Work |
| --- | --- | --- |
| API key exposure from logs | Redaction helpers | Verify with pentest and secret scanning |
| API key extraction from app | SecureStore for user key | Move production keys to backend only |
| Image prompt injection | System prompt rules | Add malicious image tests |
| Sensitive image upload | Cloud consent | Add face/PII redaction before production |
| Public cleartext backend URL | Backend URL guard | Require HTTPS in production |
| Backend abuse | Size limits | Add auth, rate limiting, and quotas if hosted |
| Raw provider error leakage | Generic errors | Monitor logs and error reporting |
| Face identity mistakes | Saved-name-only prompt rules | Add stronger local face matching and confidence thresholds |

## Non-Goals for Current MVP

- True voice biometric authentication.
- Full face/PII redaction.
- Runtime certificate pinning.
- Production app attestation.
- End-to-end encrypted emergency contact sync.
