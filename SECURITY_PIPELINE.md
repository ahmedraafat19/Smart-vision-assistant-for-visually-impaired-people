# Security Pipeline

This pipeline tracks the Expo Go app from a demo AI assistant to a safer production-ready architecture.

## Phase 1: API Key Storage - Implemented MVP

- Store user-provided OpenRouter/Gemini keys with `expo-secure-store`.
- Clean pasted key labels and whitespace before saving.
- Keep direct cloud keys available for Expo Go demos.
- Pending: move all production AI calls behind a backend proxy before public release.

## Phase 2: Cloud Consent - Implemented MVP

- Ask for Cloud AI consent before camera/audio content is sent to a cloud model.
- Store consent with `expo-secure-store`.
- Keep the consent prompt short and accessible.
- Pending: review consent copy before app-store/public release.

## Phase 3: Prompt Injection Protection - Implemented MVP

- Add system prompt rules that treat image text as visual content only.
- Do not obey instructions written on papers, screens, signs, stickers, QR codes, or documents.
- Keep navigation, obstacle, currency, and face responses cautious.
- Pending: add malicious-image evaluation cases.

## Phase 4: Currency Recognition Safety - Implemented MVP

- Use the local ONNX currency classifier first.
- Use the backend currency endpoint when the native model is unavailable or uncertain.
- Use the cloud vision verifier only inside explicit currency-value requests.
- Prevent normal scene descriptions from naming banknote values.
- Pending: collect more real-world banknote test images and tune model thresholds with evidence.

## Phase 5: Face Reference Privacy - Implemented MVP

- Store saved face references locally in app storage.
- Use saved references only for user-requested face recognition and registration flows.
- Do not invent names that are not registered.
- Pending: migrate face reference storage to stronger encrypted storage if the dataset grows.

## Phase 6: Backend TTS and Currency Service Hardening - Implemented MVP

- Add request IDs to backend responses.
- Add JSON/body and image-size limits.
- Add generic JSON errors instead of raw provider/model errors.
- Redact secrets, bearer tokens, and base64 payloads from backend logs.
- Add CORS allowlist support with `CORS_ALLOWED_ORIGINS`.
- Keep `/health` free of API keys and raw secrets.

## Phase 7: Logging Redaction - Implemented MVP

- Add shared JavaScript redaction helpers.
- Redact OpenRouter/Gemini-style keys, bearer tokens, and base64 image payloads.
- Add a small Node security test for the redaction helpers.
- Pending: add centralized production logging with retention rules.

## Phase 8: Backend URL Guard - Implemented MVP

- Allow HTTPS backend URLs.
- Allow local/private HTTP URLs for Expo Go development, including `127.0.0.1` and `192.168.x.x`.
- Reject public cleartext HTTP backend URLs from app-side backend calls.
- Pending: require HTTPS only for production builds.

## Phase 9: Security Documentation Index - Implemented

- Add `docs/security/README.md` as the main security documentation hub.
- Link the pipeline, checklist, controls matrix, data-flow document, production notes, threat model, pentest template, and privacy draft.

## Phase 10: Security Controls Matrix - Implemented

- Add `docs/security/SECURITY_CONTROLS_MATRIX.md`.
- Map each major security control to its repository location and status.
- Use honest labels such as Implemented MVP, Started, Scaffolded, and Pending.

## Phase 11: Data Flow and Privacy Mapping - Implemented

- Add `docs/security/DATA_FLOW_AND_PRIVACY.md`.
- Document what is local, what may be sent to cloud/backend, and what must not be logged.
- Mark production gaps clearly.

## Phase 12: Automated Security Checks - Started

- Add `npm run test:security`.
- Add a GitHub Actions workflow for safe basic checks.
- Run `npm audit` only when `package-lock.json` exists.
- Pending: add real secret scanning such as gitleaks or GitHub secret scanning.

## Phase 13: Production Security - Started

- Add `docs/security/PRODUCTION_SECURITY.md`.
- Pending: backend proxy for all cloud AI calls.
- Pending: production HTTPS-only backend.
- Pending: certificate pinning/runtime verification.
- Pending: stronger auth than a static client token.
- Pending: production privacy policy review.
