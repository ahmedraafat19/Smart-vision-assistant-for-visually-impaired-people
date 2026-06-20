# Data Flow and Privacy

## Secure Flow

1. User taps the voice button and speaks a command.
2. App records a short audio command.
3. App asks for camera/microphone permission only for the assistant flow.
4. App captures a camera frame.
5. App compresses the frame before cloud analysis.
6. Smart voice prompt classifies intent and language.
7. If the user asks for banknote value, currency recognition is routed through the local model/backend/currency-only verifier.
8. If the user asks a normal scene question, any guessed banknote value is removed.
9. Backend URL is checked so local/private HTTP works for Expo Go, while unsafe public cleartext backend URLs are blocked.
10. Backend validates request size for `/tts` and `/currency`.
11. Backend returns generic JSON errors and request IDs.
12. App speaks the response.
13. Generated TTS cache files are overwritten/deleted before reuse.

## Data Processed Locally

- Spoken command audio before upload.
- Camera frame and compressed image.
- Language and voice settings.
- Saved face reference images.
- Cloud consent state.
- User-provided OpenRouter/Gemini API key in secure storage.
- Local currency model predictions.

## Data That May Be Sent to Cloud or Backend

- Compressed camera image.
- Short voice-command audio.
- Saved face reference samples when face matching is requested.
- Text prompt and intent instructions.
- Text for TTS generation.
- Currency image for `/currency` backend recognition.

## Data That Should Not Be Logged

- API keys.
- Bearer tokens.
- Base64 camera frames.
- Base64 audio payloads.
- Saved face images.
- Full raw provider error bodies.
- Private documents visible in camera frames.

## Current Limitations

- Direct OpenRouter/Gemini calls are still available for Expo Go demo use.
- Full backend proxying for every cloud AI call is pending.
- Real face/PII redaction before cloud upload is pending.
- Certificate pinning is pending.
- Full temporary camera/audio cleanup verification is pending.
- A full penetration test has not yet been executed.

## Pending Before Public Production

- Move all cloud AI calls behind a production backend proxy.
- Require HTTPS backend URLs only.
- Add real user/device authentication or attestation.
- Add face/PII redaction if images continue going to cloud AI.
- Add retention policy for logs and saved face references.
- Publish reviewed privacy policy and support/security contact.
- Run the pentest checklist and close findings.
