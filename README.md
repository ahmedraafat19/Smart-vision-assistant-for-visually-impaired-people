# Smart Vision Assistant Expo

Expo Go version of Smart Vision Assistant / بصيرة for quick iPhone testing without Xcode.

AI-powered mobile assistant for visually impaired users, combining scene understanding, text reading, Egyptian currency recognition, saved face references, voice interaction, and spoken responses in one accessible app.

## What it does

- Opens a live iPhone camera preview.
- Supports one-button voice commands.
- Sends the current camera frame and spoken command to OpenRouter/Gemini when cloud consent is granted.
- Speaks the answer aloud.
- Uses the local/backend Egyptian currency model for banknote value questions.
- Keeps normal scene descriptions from guessing banknote values.
- Supports saved face references for user-controlled recognition.

## Run

```bash
cd "/Users/mac/Downloads/Smart Ai Vision assistant"

screen -dmS smart_ai_vision_backend zsh -lc 'cd "/Users/mac/Downloads/Smart Ai Vision assistant" && python3 edge_tts_server.py'

EXPO_PUBLIC_GEMINI_BACKEND_URL="http://192.168.8.225:5055" \
GEMINI_BACKEND_URL="http://192.168.8.225:5055" \
EXPO_NO_TELEMETRY=1 \
./node_modules/.bin/expo start --port 8082 --host lan --clear
```

Then scan the QR code with the Expo Go app on your iPhone.

## First use

1. Install Expo Go on your iPhone.
2. Keep the Mac and iPhone on the same Wi-Fi.
3. Start the app.
4. Scan the QR code from Expo Go.
5. Allow camera and microphone access.
6. Tap `Key`, paste your OpenRouter or Gemini API key, and tap `Save Key`.
7. Tap `Voice Command`, speak, and wait for the answer.

## Security and Privacy

- User API keys and cloud consent are stored with `expo-secure-store`.
- The app asks for Cloud AI consent before cloud analysis.
- Prompt rules treat text inside images as untrusted visual content.
- Currency values are not guessed in normal scene descriptions.
- Backend responses include request IDs.
- Backend logs redact API keys, bearer tokens, and base64 payloads.
- Local/private HTTP backend URLs are allowed for Expo Go testing; unsafe public cleartext backend URLs are blocked.

## Where to find security docs

- [Security Pipeline](SECURITY_PIPELINE.md)
- [Security Checklist](SECURITY_CHECKLIST.md)
- [Security Documentation Index](docs/security/README.md)

## Security Checks

```bash
npm run test:security
python3 -m py_compile edge_tts_server.py
npx expo config --type public
```

## Notes

- This avoids Xcode for testing.
- Expo Go does not provide always-on wake-word listening.
- Voice commands require an OpenRouter key that starts with `sk-or-` or a Gemini key.
- Public production still needs a full backend proxy for all cloud AI calls, real HTTPS-only deployment, and face/PII redaction before cloud upload.
