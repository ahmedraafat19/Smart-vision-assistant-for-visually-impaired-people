const SECRET_PATTERNS = [
  /sk-or-v1-[A-Za-z0-9_-]+/g,
  /sk-[A-Za-z0-9_-]+/g,
  /AIza[ A-Za-z0-9_-]+/g,
  /Bearer\s+\S+/gi,
  /(OPENROUTER_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|BACKEND_CLIENT_TOKEN|API_KEY)\s*[:=]\s*[^\s,}]+/gi,
  /data:image\/[^;]+;base64,[A-Za-z0-9+/=]+/g,
  /"imageBase64"\s*:\s*"[A-Za-z0-9+/=]+"/g,
  /"base64"\s*:\s*"[A-Za-z0-9+/=]{80,}"/g,
  /[A-Za-z0-9+/=]{160,}/g,
];

const LOCAL_OR_PRIVATE_HOST_PATTERN =
  /^(localhost|127\.0\.0\.1|0\.0\.0\.0|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+|192\.168\.\d+\.\d+)$/;

function redactSensitiveText(value) {
  let redacted = String(value || '');
  for (const pattern of SECRET_PATTERNS) {
    redacted = redacted.replace(pattern, (match) => {
      if (/^Bearer\s+/i.test(match)) {
        return 'Bearer [redacted]';
      }
      if (/^(OPENROUTER_API_KEY|OPENAI_API_KEY|GEMINI_API_KEY|BACKEND_CLIENT_TOKEN|API_KEY)/i.test(match)) {
        const keyName = match.split(/[:=]/)[0].trim();
        return `${keyName}=[redacted]`;
      }
      return '[redacted]';
    });
  }
  return redacted;
}

function isSafeBackendUrl(value) {
  if (!value) return false;

  try {
    const parsed = new URL(value);
    if (parsed.protocol === 'https:') return true;
    if (parsed.protocol !== 'http:') return false;
    return LOCAL_OR_PRIVATE_HOST_PATTERN.test(parsed.hostname);
  } catch {
    return false;
  }
}

function safeBackendUrl(value) {
  const cleanValue = String(value || '').trim().replace(/\/$/, '');
  return isSafeBackendUrl(cleanValue) ? cleanValue : '';
}

function genericCloudError(providerName) {
  return `${providerName || 'Cloud AI'} request failed. Please check the connection and try again.`;
}

module.exports = {
  redactSensitiveText,
  isSafeBackendUrl,
  safeBackendUrl,
  genericCloudError,
};
