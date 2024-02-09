from consent_api.config.types import Environment

other_service_origins = {
    Environment.TESTING: "http://dummy-service-1",
    Environment.DEVELOPMENT: "http://dummy-service-1",
    Environment.STAGING: "",
    Environment.PRODUCTION: "",
}


consent_api_origins = {
    Environment.TESTING: "http://consent-api",
    Environment.DEVELOPMENT: "http://consent-api",
    Environment.STAGING: "https://gds-single-consent-staging.app",
    Environment.PRODUCTION: "https://gds-single-consent.app",
}
