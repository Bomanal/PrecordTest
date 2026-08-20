# Technical Specification

*The estate, the controls and the deployment — for client IT*

Generated 2026-08-14T09:17:40+00:00 by Specificity.ai. Every table and figure below is drawn from a committed artifact; each is cited where it appears.


## The environment as it stands

The client's current estate centers on Guidewire PolicyCenter (Life and Annuity Underwriting Module) hosted within an approved managed cloud landing zone. Direct database access is prohibited, requiring all agent interactions to go through the central API gateway. The infrastructure supports TLS 1.2 or higher for encryption in transit, AES-256 for encryption at rest, and Prometheus-compatible telemetry. The specific cloud provider and hosting region are not stated in the documentation. For identity management, SAML SSO is detected but remains unconfirmed, which represents a key technical dependency that must be resolved prior to deployment.

![System architecture](/api/artifacts/414f7932e7ad438cab3ef0c7d3e96d4e/content)

*System architecture — drawn from [`system_architecture_map` v1](/api/artifacts/86e5674d1be5489c91ffc1c42e0d6dd0/content).*

> Figure not available: no rendered image of `system_integration_map` — **not committed** has been generated.

### What client IT has established

| # | Area | Question | Answer | Status | Who holds it |
| --- | --- | --- | --- | --- | --- |
| Q1 | deployment | What cloud environment and region hosts the workflow system? | Guidewire PolicyCenter is hosted in an approved managed cloud landing zone, but the specific cloud provider (e.g., AWS, Azure) and region are not stated in the documents. | inferred | Client IT infrastructure team |
| Q2 | systems | What is the core workflow system of record? | Guidewire PolicyCenter (Life & Annuity Underwriting Module). | answered | Application owner |
| Q3 | interfaces | Which APIs are available for integration? | REST APIs over HTTPS with JSON payloads are available on Guidewire PolicyCenter, including /submissions, /parties/search, /submissions/{id}/financials, /underwriting/medical-grid, /submissions/{id}/medical/tests, /submissions/{id}/medical/results, /submissions/{id}/medical/impairments, /tele-underwriting/requests, /submissions/{id}/rating/evaluate, /submissions/{id}/rating/override, /submissions/{id}/decision, /reinsurance/referrals, /reinsurance/treaty-limits, /submissions/{id}/offer, /submissions/{id}/offer/response, /policies, /submissions/{id}/close, and /submissions/{id}/timeline. | answered | API catalogue |
| Q4 | security | What security and compliance controls are required? | Encryption in transit (TLS 1.2 or higher), encryption at rest (AES-256), OAuth 2.0 / SAML 2.0 SSO for interactive users, OAuth 2.0 client-credentials or mutual-TLS for service-to-service calls, role-based access control, and a 30-minute idle session timeout. Medical (PHI) and financial evidence are Restricted and must not leave the client's approved data residency zone. Client data must not be used to train AI models. | answered | Security team |
| Q5 | telemetry | What telemetry, tracking and alerting stack is in use? | The stack includes a central metrics platform (Prometheus-compatible ingestion) via push/scrape endpoints, a central log platform (structured JSON logs) via log shipping agents or direct API, distributed tracing via an OpenTelemetry-compatible tracing backend (OTLP exporter), a central alerting/on-call tool, and built-in API gateway health-check aggregation. | answered | SRE team |
| Q6 | agent_contract | What output payload can the workflow system accept from the agents? | PolicyCenter can accept JSON payloads over REST endpoints such as /submissions/{id}/medical/results to record physical vitals and MER/lab findings, /submissions/{id}/medical/impairments to add impairment records, /submissions/{id}/rating/override to write manual extra mortality overrides, /submissions/{id}/decision to save standard/rated-up/postpone/decline statuses, and /submissions/{id}/close to close cases with reason codes. Agents can read metadata, declared financials, required medical tests, and timelines via GET endpoints. | answered | Integration architect |

A blank answer is an open question, not permission to assume one. The form is [`it_requirements_questionnaire` v1](/api/artifacts/58d92953da19423ea1ae179fde2cb18d/content) and is editable in the workspace.

## Security and control requirements

The deployment enforces strict security controls to safeguard Restricted Protected Health Information and financial data. All data must remain within the client's approved data residency zone, and any cached data used during agent execution must be securely deleted upon case closure. Under no circumstances may client data be used to train external AI models. Encryption in transit via TLS 1.2 or higher and encryption at rest via AES-256 are mandatory. Interactive users will authenticate using OAuth 2.0 or SAML 2.0 SSO, while service-to-service communication will utilize OAuth 2.0 client-credentials or mutual TLS. Several critical controls must remain manual regulatory gates, including final risk binding, counter-offer negotiations, and pre-closing quality control checklists. The exact configuration of secret storage remains open.

### Stated security requirements

| Question | Answer | Status |
| --- | --- | --- |
| What security and compliance controls are required? | Encryption in transit (TLS 1.2 or higher), encryption at rest (AES-256), OAuth 2.0 / SAML 2.0 SSO for interactive users, OAuth 2.0 client-credentials or mutual-TLS for service-to-service calls, role-based access control, and a 30-minute idle session timeout. Medical (PHI) and financial evidence are Restricted and must not leave the client's approved data residency zone. Client data must not be used to train AI models. | answered |

### Controls that stay with a person

These are controls, not gaps. An agent whose autonomy exceeds the authority of the person who would otherwise decide has not automated a step — it has removed a control.

| Step | Kind | Requirement |
| --- | --- | --- |
| S1 | judgement | Verifying proof of age and determining if the application has sufficient core information to begin assessment is highly unstructured and requires initial intake underwriter validation. |
| S7 | judgement | Evaluating health declarations for subjective self-reported risks requires underwriter critical thinking and holistic contextual evaluation of individual proposer hazards. |
| S8 | judgement | Determining whether combined impairments (such as diabetes and obesity) warrant non-linear rating joint considerations rather than standard mechanical summing requires advanced human clinical underwriter expertise. |
| S11 | regulatory | Binding final risk classifications and confirming standard, rated-up, or declined outcomes involves major legal and financial liabilities that must remain with a licensed human underwriter. |
| S12 | judgement | Deciding to offer standard terms versus negotiating a counter-offer with reduced sum assured or term requires commercial balancing and customer context. |
| S14 | regulatory | Formally declining or postponing coverage has strict legal notification requirements that require underwriter validation before case closure. |
| S15 | regulatory | Reviewing and signing off on pre-closing quality control checklists before policy issuance serves as a formal regulatory risk gate requiring certified human approval. |

### Review rates the design commits to

| Agent | Autonomy | Review rate (share of 1) | Escalation |
| --- | --- | --- | --- |
| Intake & Requirements Orchestrator | autonomous | 0.05 | Escalate to the Intake Underwriter if applicant smoker status is unverified or demographic values are corrupt. |
| Underwriting Evidence Assistant | draft_for_approval | 1 | Route to the Underwriter if the source PDF is illegible, password protected, or crucial values (e.g., net income) are missing. |
| Reinsurance Referral Dispatcher | draft_for_approval | 1 | Escalate to the senior underwriter for manual editing of the draft before dispatch. |

## Deployment and operation

The agent service will be deployed behind an authenticated integration boundary adjacent to Guidewire PolicyCenter, following Scenario A as an integrated agent workbench. The deployment will execute actions and transition states by calling approved POST endpoints via the API gateway. System health, performance, and model execution costs will be continuously observed using the established Prometheus-compatible metrics platform, structured JSON logging, and OpenTelemetry-compatible tracing. This observability framework will track key telemetry such as API hit counts, gateway health, data extraction latency, and agent-specific token consumption to ensure operational stability.

# Deployment Architecture & Requirements

Hosting: Guidewire PolicyCenter is hosted in an approved managed cloud landing zone, but the specific cloud provider (e.g., AWS, Azure) and region are not stated in the documents..

A component is **Evidenced** only where the questionnaire answered it from a
document. **Detected, unconfirmed** means a keyword matched somewhere in the
corpus and nothing confirmed it — a string, not a system. Both of those and
**Not available** must be settled with client IT before Experience 2 begins.

| Component | Value | Status |
|---|---|---|
| Cloud environment | Not available | **Not available** |
| Database | Not available | **Not available** |
| API gateway | API gateway | Evidenced |
| LLM provider | Not available | **Not available** |
| Secret storage | Not available | **Not available** |
| Identity / SSO | SAML SSO | Detected, unconfirmed |
| Telemetry / monitoring | Prometheus | Evidenced |

## Deployment model — Scenario A (integrated agent workbench)

Deploy the agent service behind an authenticated integration boundary next to the Guidewire PolicyCenter, reading and writing through the integration points in the inventory.

## The estate

The client's technical environment centers on Guidewire PolicyCenter (Life & Annuity Underwriting Module) as the core system of record. PolicyCenter is hosted in an approved managed cloud landing zone, with all integration traffic strictly mediated via a central API gateway; direct database access is prohibited. Integration with PolicyCenter occurs asynchronously and synchronously via REST over HTTPS using JSON payloads, authenticated via an OAuth 2.0 client-credentials grant (with 60-minute token expiry). An external agent can realistically read case details, required medical tests, financial statuses, and event timelines from GET endpoints (e.g., /submissions/{id}, /underwriting/medical-grid, and /submissions/{id}/timeline) and write or transition states by invoking POST endpoints (e.g., /submissions/{id}/medical/results, /submissions/{id}/rating/override, /submissions/{id}/decision, and /submissions/{id}/close). Sensitive data such as Protected Health Information (PHI) and financial documents must remain in the client's approved data residency zone, and any cached data for AI processing must be deleted upon case closure. Central telemetry is fully established using Prometheus-compatible metrics, structured JSON logging, and OpenTelemetry (OTLP) tracing.


## Missing / to confirm

- Cloud environment
- Database
- LLM provider
- Secret storage


> Figure not available: no rendered image of `deployment_architecture_map` — **not committed** has been generated.

Data movement is described in [`data_flow_map` v1](/api/artifacts/28282aef5c144b63a9d903cbec939e69/content); the integration build plan is `integration_plan` — **not committed**.

## Open items

Several critical technical and architectural details must be settled with the client's IT team before the build phase can begin. The specific hosting cloud provider and geographical region for the managed landing zone are not stated and must be confirmed. The underlying database technology, the specific LLM provider for the agent execution, and the designated secret storage solution are currently not available in the design records. Additionally, the integration status of SAML SSO for identity management remains unconfirmed and must be formally verified. Resolving these open items is a prerequisite for finalizing the security and deployment architecture.

### 0 question(s) client IT has not answered

_Every question on the form has been answered._
