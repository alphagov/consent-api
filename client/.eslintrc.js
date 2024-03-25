module.exports = {
  env: {
    browser: true,
    es2021: false,
    node: true,
  },
  extends: "eslint:recommended",
  overrides: [],
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: "module",
    project: "tsconfig.json",
  },
  rules: {
    semi: ["error", "never"],
    "no-extra-semi": ["off"],
  },
  ignorePatterns: ["src/*.test.js"],
};
