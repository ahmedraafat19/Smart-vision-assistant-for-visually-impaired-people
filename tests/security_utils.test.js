const assert = require('assert');
const {
  genericCloudError,
  isSafeBackendUrl,
  redactSensitiveText,
  safeBackendUrl,
} = require('../security/security_utils');

function testRedaction() {
  const imageBlob = 'A'.repeat(200);
  const fakeOpenRouterKey = `sk-or-v1-${'secret'}`;
  const redacted = redactSensitiveText(
    `OPENROUTER_API_KEY=${fakeOpenRouterKey} Bearer token data:image/jpeg;base64,${imageBlob}`
  );

  assert(!redacted.includes(fakeOpenRouterKey));
  assert(!redacted.includes('Bearer token'));
  assert(!redacted.includes(imageBlob.slice(0, 100)));
  assert(redacted.includes('[redacted]'));
}

function testBackendUrlGuard() {
  assert.equal(isSafeBackendUrl('https://backend.example.com'), true);
  assert.equal(isSafeBackendUrl('http://127.0.0.1:5055'), true);
  assert.equal(isSafeBackendUrl('http://192.168.8.225:5055'), true);
  assert.equal(isSafeBackendUrl('http://example.com'), false);
  assert.equal(safeBackendUrl('http://example.com'), '');
}

function testGenericCloudError() {
  const message = genericCloudError('OpenRouter');
  assert(message.includes('OpenRouter'));
  assert(!message.includes('sk-'));
}

testRedaction();
testBackendUrlGuard();
testGenericCloudError();

console.log('security_utils tests passed');
