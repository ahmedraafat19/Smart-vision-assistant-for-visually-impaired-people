# Security Checklist

Use this checklist before demo builds, APK builds, or public release of the Expo app.

## Mobile App Security

- [x] Store user API keys with `expo-secure-store`.
- [x] Ask for Cloud AI consent before cloud analysis.
- [x] Request camera and microphone only for the assistant flow.
- [x] Treat image text as untrusted visual content in prompts.
- [x] Keep currency value answers out of normal scene descriptions.
- [~] Allow local/private HTTP backend URLs for Expo Go development.
- [ ] Require HTTPS backend URLs for production builds.
- [ ] Move all direct cloud AI calls behind a backend proxy before public release.

## Backend Security

- [x] Add request IDs to backend JSON responses.
- [x] Keep `/health` free of API keys.
- [x] Add request body and image payload size limits.
- [x] Return generic JSON errors for TTS/currency failures.
- [x] Redact keys, bearer tokens, and base64 payloads from logs.
- [~] Support CORS allowlist through `CORS_ALLOWED_ORIGINS`.
- [ ] Add backend client token enforcement if the backend becomes public.
- [ ] Put production secrets in environment variables or a secret manager only.

## Privacy and Data Protection

- [x] Do not log raw base64 images from the app security utility.
- [x] Do not log raw provider error bodies from the backend.
- [x] Store cloud consent securely.
- [x] Keep saved face matching limited to registered local references.
- [~] Keep temporary generated TTS files in cache and overwrite/delete old generated TTS file names.
- [ ] Add a full temporary camera/audio cleanup audit before production.
- [ ] Add real face/PII redaction before public production if cloud image upload remains enabled.

## AI Safety and Prompt Injection

- [x] System prompt rejects instructions written inside images.
- [x] Navigation/obstacle answers must avoid safety guarantees.
- [x] Currency values must come from currency model/backend or explicit currency verifier flow.
- [ ] Add malicious-image prompt injection tests.
- [ ] Add broader AI safety evaluation prompts.

## Build and Release Security

- [x] Keep OpenRouter/Gemini keys out of committed files.
- [x] Add security utility tests.
- [ ] Run `npm audit` before release.
- [ ] Run secret scanning before release.
- [ ] Build production APK with no manual hardcoded key.
- [ ] Document incident response and key rotation process.

## Testing and Verification

- [x] Run `npm run test:security`.
- [x] Run `python3 -m py_compile edge_tts_server.py`.
- [ ] Run `npx expo config --type public`.
- [ ] Test `/health`, `/currency`, and `/tts` against the local backend.
- [ ] Execute `docs/security/PENTEST_REPORT.md` before public release.
