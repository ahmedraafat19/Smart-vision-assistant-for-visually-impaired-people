# VisionClaw Expo

Expo Go version of VisionClaw for quick iPhone testing without Xcode.

## What it does

- Opens a live iPhone camera preview
- Sends a captured frame to Gemini 2.5 Flash
- Speaks the answer aloud with Expo Speech
- Supports one-button voice commands with OpenRouter Gemini 2.5 Flash
- Stops recording automatically after the user stops speaking

## Run

```bash
cd /Users/mac/Downloads/testing/visionclaw-expo
npm start
```

Then scan the QR code with the Expo Go app on your iPhone.

## First use

1. Install Expo Go on your iPhone.
2. Keep the Mac and iPhone on the same Wi-Fi.
3. Start the app with `npm start`.
4. Scan the QR code from Expo Go.
5. Allow camera access.
6. Tap `Key`, paste your Gemini API key, and tap `Save Key`.
7. Tap `Voice Command`, speak, and wait for the answer.

## Voice commands

1. Tap `Voice Command`.
2. Speak your question.
3. Stop speaking.
4. The app automatically stops recording, sends your voice command and the current camera image to OpenRouter, then speaks the answer.

## Notes

- This avoids Xcode for testing.
- Expo Go does not provide always-on wake-word listening.
- Voice commands require an OpenRouter key that starts with `sk-or-`.
