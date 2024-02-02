## [3.0.3] - 2024-01-18

### Changed

- **IE9 Compatibility**: Removed usage of the `Array.prototype.find` method
- **Error handling**: Requests error handling is now using callbacks

## [3.0.0] - 2024-01-18

### Changed

- **API URL Management**: Simplified the API URL configuration. Users now only need to provide the base URL, removing the requirement to specify the `api/v1` suffix. Introduced `ApiV1` class for streamlined URL handling. [PR #223](https://github.com/alphagov/consent-api/pull/223)
- **Refactoring**: Overhauled client code structure for enhanced simplicity and readability. Includes transition to more robust TypeScript usage, replacement of `var` with `const`, and better separation of concerns. [PR #223](https://github.com/alphagov/consent-api/pull/223)
- **Constructor Update**: Modified the constructor to accept an environment string (e.g., 'staging', 'production') instead of a base URL, with support for custom base URLs when needed. [PR #223](https://github.com/alphagov/consent-api/pull/223)
- **Documentation**: Updated documentation to reflect new usage patterns and API changes. [PR #223](https://github.com/alphagov/consent-api/pull/223)

Note: These changes are breaking and may require updates to existing implementations.
