# Privacy Policy Draft

This draft is for review before any public release. Do not publish it unchanged without confirming hosting, provider retention, and local legal requirements.

## What The App Does

The app helps blind or low-vision users ask spoken questions about the camera view. It can describe scenes, read visible text, recognize Egyptian banknotes, and compare faces against locally saved references.

## Data Processed

The app may process:

- Voice commands.
- Camera frames.
- Saved face reference images.
- Language and voice settings.
- Cloud AI consent state.
- API keys entered by the user.
- Currency model predictions.

## Cloud AI Processing

When the user grants consent, the app may send compressed camera images, audio commands, and prompt metadata to the configured AI provider or local/private backend. OpenRouter requests ask for privacy-conscious routing options where supported.

## Local Storage

User API keys and Cloud AI consent are stored with `expo-secure-store`. Some app preferences and saved face references are stored locally on the device.

## Logs

The app and backend should not log API keys, bearer tokens, base64 camera frames, saved face images, or raw provider error bodies.

## Production Requirements

- Move provider keys to a backend proxy.
- Review OpenRouter/Gemini provider retention terms.
- Add face/PII redaction if images are sent to cloud AI.
- Define retention and deletion rules.
- Add support/security contact.
- Run penetration testing before public release.
