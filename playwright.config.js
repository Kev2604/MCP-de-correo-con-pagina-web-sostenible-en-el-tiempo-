module.exports = {
  testDir: './tests/playwright',
  timeout: 60000,
  use: {
    headless: true,
    baseURL: 'http://127.0.0.1:8123',
  },
};
