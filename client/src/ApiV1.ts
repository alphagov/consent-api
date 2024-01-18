class ApiV1 {
  version = 'v1'
  private baseUrl: string

  static readonly Routes = {
    origins: '/origins',
    consents: '/consent',
  }

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl
  }

  private buildUrl(endpoint: string, pathParam?: string): string {
    let url = `${this.baseUrl}/api/${this.version}${endpoint}`
    if (pathParam) {
      url += `/${pathParam}`
    }
    return url
  }

  origins(): string {
    return this.buildUrl(ApiV1.Routes.origins)
  }

  consents(id?: string): string {
    return this.buildUrl(ApiV1.Routes.consents, id || '')
  }
}

export default ApiV1
