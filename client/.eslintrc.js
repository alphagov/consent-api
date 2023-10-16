module.exports = {
  env: {
    browser: true,
    es2021: false,
    node: true,
  },
  extends: 'eslint:recommended',
  overrides: [],
  parserOptions: {
    ecmaVersion: 5,
  },
  rules: {
    semi: ['error', 'never'],
    'no-extra-semi': ['off'],
  },
  ignorePatterns: ["src/*.test.js"],
}
