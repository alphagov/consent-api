/**
 * For a detailed explanation regarding each configuration property, visit:
 * https://jestjs.io/docs/configuration
 */

/** @type {import('jest').Config} */
var config = {
  preset: 'ts-jest',
  // testEnvironment: 'node',
  coverageProvider: 'v8',
  // The test environment that will be used for testing
  testEnvironment: 'jest-environment-jsdom-global',
}

module.exports = config
