const openRouterApiKey =
  process.env.OPENROUTER_API_KEY || process.env.EXPO_PUBLIC_OPENROUTER_API_KEY || '';
const geminiBackendUrl =
  process.env.GEMINI_BACKEND_URL || process.env.EXPO_PUBLIC_GEMINI_BACKEND_URL || '';

module.exports = {
  name: 'بصيرة',
  slug: 'visionclaw-expo',
  version: '1.0.0',
  orientation: 'portrait',
  icon: './assets/icon.png',
  userInterfaceStyle: 'light',
  newArchEnabled: true,
  splash: {
    image: './assets/splash-icon.png',
    resizeMode: 'contain',
    backgroundColor: '#ffffff',
  },
  ios: {
    supportsTablet: true,
    bundleIdentifier: 'com.visionclaw.voice',
    infoPlist: {
      NSCameraUsageDescription:
        'بصيرة uses the camera to describe surroundings and read visible text.',
      NSMicrophoneUsageDescription:
        'بصيرة records short voice commands so the assistant can answer hands-free questions.',
    },
  },
  android: {
    adaptiveIcon: {
      foregroundImage: './assets/adaptive-icon.png',
      backgroundColor: '#ffffff',
    },
    edgeToEdgeEnabled: true,
    permissions: [
      'android.permission.CAMERA',
      'android.permission.RECORD_AUDIO',
      'android.permission.MODIFY_AUDIO_SETTINGS',
    ],
    package: 'com.visionclaw.voice',
  },
  web: {
    favicon: './assets/favicon.png',
  },
  plugins: [
    [
      'expo-camera',
      {
        cameraPermission: 'بصيرة uses the camera to describe surroundings and read visible text.',
        microphonePermission:
          'بصيرة records short voice commands so the assistant can answer hands-free questions.',
        recordAudioAndroid: false,
      },
    ],
    'expo-secure-store',
    'expo-audio',
    'expo-asset',
    'onnxruntime-react-native',
  ],
  extra: {
    openRouterApiKey,
    geminiBackendUrl,
    eas: {
      projectId: 'a2c11edb-6807-4855-9d99-0c3b1ded4c18',
    },
  },
};
