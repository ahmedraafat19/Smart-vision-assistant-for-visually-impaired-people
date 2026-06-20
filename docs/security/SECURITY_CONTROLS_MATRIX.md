# Security Controls Matrix

| Security Control | Purpose | Location in Repository | Status | Notes / Production Requirement |
| --- | --- | --- | --- | --- |
| Secure key storage | Store user cloud API keys outside plain AsyncStorage | `App.js` | Implemented MVP | Uses `expo-secure-store`. |
| Environment-based demo key | Allow optional demo key injection without hardcoding in source | `app.config.js` | Implemented MVP | Do not commit `.env` with real keys. |
| Cloud AI consent | Ask before sending camera/audio-derived data to cloud AI | `App.js` | Implemented MVP | Review consent wording before public release. |
| Backend URL guard | Block unsafe public cleartext backend URLs | `security/security_utils.js`, `App.js` | Implemented MVP | Local/private HTTP remains allowed for Expo Go testing. |
| Prompt injection protection | Treat image text as visual content only | `App.js` | Implemented MVP | Add more malicious-image tests. |
| Currency no-guess rule | Prevent VLM scene flow from naming banknote values | `App.js` | Implemented MVP | Currency value must come from model/backend/currency-only verifier. |
| Local currency model | Identify Egyptian banknote denominations locally when possible | `assets/models/egyptian_currency_classifier.onnx`, `App.js` | Implemented MVP | Continue collecting difficult real camera examples. |
| Backend currency endpoint | Server-side currency fallback for local model gaps | `edge_tts_server.py` | Implemented MVP | Keep model path configurable through environment. |
| Backend TTS endpoint | Generate speech without exposing provider errors | `edge_tts_server.py` | Implemented MVP | Requires backend `GEMINI_API_KEY`. |
| Request IDs | Correlate failures without logging payloads | `edge_tts_server.py` | Implemented MVP | Returned as `requestId`. |
| Request size limits | Reduce abuse and accidental huge uploads | `edge_tts_server.py` | Implemented MVP | Controlled by `MAX_JSON_BODY_BYTES` and `MAX_IMAGE_BYTES`. |
| No raw image logging | Avoid base64 camera payloads in logs | `security/security_utils.js`, `edge_tts_server.py` | Implemented MVP | Verify during pentest. |
| Log redaction | Redact keys, bearer tokens, and base64 payloads | `security/security_utils.js`, `edge_tts_server.py` | Implemented MVP | Covered by `npm run test:security`. |
| CORS allowlist | Restrict browser origins when configured | `edge_tts_server.py` | Started | Set `CORS_ALLOWED_ORIGINS` for hosted deployments. |
| Face reference caution | Avoid invented identity claims | `App.js` | Implemented MVP | Saved references are local app data. |
| Secure docs index | Make cybersecurity work easy to find | `docs/security/README.md` | Implemented | Keep docs updated with code changes. |
| Automated security checks | Run basic tests and audit reminders | `.github/workflows/security-checks.yml` | Started | Add secret scanning integration later. |
| Backend proxy for all AI calls | Hide all provider keys from the app | Not fully present | Pending | Needed before public production. |
| Certificate pinning | Protect production backend transport | Not present | Pending | Requires stable HTTPS domain/certificate lifecycle. |
| Face/PII redaction | Blur sensitive data before cloud upload | Not present | Pending | Do not claim implemented. |
| Penetration testing | Validate controls manually | `docs/security/PENTEST_REPORT.md` | Started | Execution pending. |
