# Security Documentation Index

This folder collects the cybersecurity and privacy documentation for the Expo Go version of بصيرة / Smart AI Vision Assistant.

## Main Security Documents

- [Security Pipeline](../../SECURITY_PIPELINE.md) - phase-based security roadmap.
- [Security Checklist](../../SECURITY_CHECKLIST.md) - demo/release verification checklist.
- [Security Controls Matrix](SECURITY_CONTROLS_MATRIX.md) - control-by-control implementation map.
- [Data Flow and Privacy](DATA_FLOW_AND_PRIVACY.md) - camera, voice, backend, and cloud data flow.
- [Production Security](PRODUCTION_SECURITY.md) - production hardening requirements.
- [Threat Model](THREAT_MODEL.md) - main assets, trust boundaries, threats, and remaining work.
- [Penetration Testing Report](PENTEST_REPORT.md) - pentest template and checklist.
- [Privacy Policy Draft](PRIVACY_POLICY_DRAFT.md) - draft privacy policy wording.

## Implementation Locations

- `App.js` - Expo app flow, cloud consent, secure key storage, prompt-injection guidance, backend URL guard.
- `security/security_utils.js` - redaction and backend URL safety helpers.
- `edge_tts_server.py` - local backend for Gemini TTS and currency recognition.
- `assets/models/egyptian_currency_classifier.onnx` - local Egyptian banknote classifier.
- `tests/security_utils.test.js` - security utility tests.
- `.github/workflows/security-checks.yml` - basic automated security checks.

## Status Summary

- Secure key storage: Implemented MVP.
- Cloud consent: Implemented MVP.
- Prompt injection protection: Implemented MVP.
- Currency safety routing: Implemented MVP.
- Backend request/log hardening: Implemented MVP.
- Production backend proxy for all AI calls: Pending.
- Face/PII redaction: Pending.
- Full penetration test: Pending.
