# Deployment Architecture & Requirements

Hosting has not been established; the deployment question is open.

A component is **Evidenced** only where the questionnaire answered it from a
document. **Detected, unconfirmed** means a keyword matched somewhere in the
corpus and nothing confirmed it — a string, not a system. Both of those and
**Not available** must be settled with client IT before Experience 2 begins.

| Component | Value | Status |
|---|---|---|
| Cloud environment | AWS | Evidenced |
| Database | Not available | **Not available** |
| API gateway | API gateway | Evidenced |
| LLM provider | Not available | **Not available** |
| Secret storage | Not available | **Not available** |
| Identity / SSO | SAML SSO | Detected, unconfirmed |
| Telemetry / monitoring | Prometheus | Evidenced |

## Deployment model — Scenario A (integrated agent workbench)

Deploy the agent service behind an authenticated integration boundary next to the Guidewire PolicyCenter, reading and writing through the integration points in the inventory.

## The estate

The client's technical architecture is built around Guidewire PolicyCenter as the core workflow system of record. PolicyCenter manages individual life underwriting submissions, and all traffic from external platforms must route through the client's central API Gateway using REST over HTTPS. Relational database storage, blob storage for physical evidence documents, and secret managers are decoupled and managed centrally as infrastructure services. Interactive users authenticate via SAML 2.0 or OAuth 2.0 Single Sign-On (SSO). AI agents can interact with this environment through the API Gateway, utilizing the REST API surface to read case details (such as the timeline event stream or specific evidence files via document retrieval endpoints) and write validated details, impairment records, or rating overrides back into PolicyCenter. Telemetry and observability are handled through centralized log, metrics, and tracing platforms via OpenTelemetry standards.


## Missing / to confirm

- Database
- LLM provider
- Secret storage
