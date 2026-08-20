# Agentic AI Solution Requirements

*What is to be built — for the implementation team*

Generated 2026-08-14T09:17:40+00:00 by Specificity.ai. Every table and figure below is drawn from a committed artifact; each is cited where it appears.


> This document **references** the process memory rather than reproducing it. Every requirement names the artifact and row it was derived from, and that artifact is the authority: if the two disagree, the artifact is right and this document is stale. Figures are the one exception — a picture of a diagram cannot contradict it.

## Scope

The scope of this deployment includes five agentic opportunities designed to integrate directly with Guidewire PolicyCenter. Specifically, we are building the Medical Requirements Orchestrator to automate medical limit evaluation and test ordering, the Medical Evidence Digitizer and BMI Validator to process unstructured clinical findings, and the Automated Financial Underwriting Assistant to extract income proofs and trigger HLV computations. Additionally, we are building early and final referral automation through the Provisional Reinsurance Referral Drafter and the Reinsurance Referral Packager. Explicitly excluded from automation are subjective underwriter judgment and regulatory risk gates. Verifying proof of age, monitoring outstanding physical exams with external labs, evaluating subjective self-reported health declarations, determining combined impairment ratings, binding final risk classifications, negotiating counter-offers, and executing final pre-closing quality control checklists remain strictly manual human actions.

5 opportunit(ies) are in scope, of 5 designed. The authority for scope is the `selected` column of [`opportunity_table` v1](/api/artifacts/f24250b5d1d44f7dbacbefbdd38e6d49/content), which the user owns.

![The process the agents run in](/api/artifacts/7be2898a69e04bc699d102e165ce84d6/content)

*The process the agents run in — drawn from [`reimagined_process_graph` v1](/api/artifacts/a170eb733e5d4aecbf04ee75e8d42493/content).*

## Agent requirements

The solution is organized into three distinct agent specifications that run autonomously or generate drafts for human approval. The Intake and Requirements Orchestrator operates autonomously to determine and order standard medical tests by querying the digital grid, failing over to human underwriters only when demographic data is corrupt. The Underwriting Evidence Assistant operates on a draft-for-approval model to extract and validate clinical and financial data from unstructured PDFs, writing directly to PolicyCenter endpoints while escalating unreadable files or missing crucial values to the underwriter. The Reinsurance Referral Dispatcher also follows a draft-for-approval model, compiling and packaging early provisional summaries and final facultative referrals for Atlas Re and the Chief Underwriting Officer, with escalations directed to senior underwriters for final validation before dispatch.

### SR-A01 — Intake & Requirements Orchestrator

The system **shall** provide an agent serving step(s) `S3` whose purpose is Automatically determine and order standard and metabolic medical requirements using the medical grid and BMI thresholds.

- **Autonomy:** `autonomous` — this is the ceiling on what it may do unattended, and it is a control, not a configuration default.
- **Human review:** 5% of its output shall be checked by a person.
- **Escalation:** Escalate to the Intake Underwriter if applicant smoker status is unverified or demographic values are corrupt.
- **On failure:** Write a system warning to the case history, skip automated ordering, and assign a task to the Underwriter for manual grid evaluation.
- **Touches:** `/underwriting/medical-grid; /submissions/{id}/medical/tests`

Source: [`agent_specifications` v1](/api/artifacts/4ace1d79387f45ce84e1ee529946392d/content), row `Block-01`.

### SR-A02 — Underwriting Evidence Assistant

The system **shall** provide an agent serving step(s) `S2; S6` whose purpose is Extract, format, and validate medical vitals and financial data from unstructured PDFs to directly update Guidewire PolicyCenter.

- **Autonomy:** `draft_for_approval` — this is the ceiling on what it may do unattended, and it is a control, not a configuration default.
- **Human review:** 100% of its output shall be checked by a person.
- **Escalation:** Route to the Underwriter if the source PDF is illegible, password protected, or crucial values (e.g., net income) are missing.
- **On failure:** Flag the case with an 'Extraction Error' label, save a blank draft form, and alert the Underwriter to manually transcribe the documents.
- **Touches:** `/submissions/{id}/financials; /submissions/{id}/financials/proof; /submissions/{id}/financials/hlv; /submissions/{id}/medical/results; /submissions/{id}/medical/impairments`

Source: [`agent_specifications` v1](/api/artifacts/4ace1d79387f45ce84e1ee529946392d/content), row `Block-02`.

### SR-A03 — Reinsurance Referral Dispatcher

The system **shall** provide an agent serving step(s) `S4; S9` whose purpose is Compile and package early and final facultative reinsurance summaries for Atlas Re or the Chief Underwriting Officer.

- **Autonomy:** `draft_for_approval` — this is the ceiling on what it may do unattended, and it is a control, not a configuration default.
- **Human review:** 100% of its output shall be checked by a person.
- **Escalation:** Escalate to the senior underwriter for manual editing of the draft before dispatch.
- **On failure:** Store a blank draft referral template in the submission record and append a system task alerting the user of draft generation failure.
- **Touches:** `/reinsurance/treaty-limits; /reinsurance/referrals`

Source: [`agent_specifications` v1](/api/artifacts/4ace1d79387f45ce84e1ee529946392d/content), row `Block-03`.

## Integration requirements

The agents integrate with Guidewire PolicyCenter and the reinsurance portal via REST APIs over HTTPS with JSON payloads. The system of record is PolicyCenter, and all integration traffic is mediated by the client's central API gateway. The available integration paths allow the agents to read proposer details, medical grids, and event timelines, and write to endpoints for medical results, physical vitals, impairments, rating overrides, and case closure. For reinsurance, the data flows bidirectionally between PolicyCenter and the reinsurance portal via existing endpoints for facultative referrals and response terms. Direct database access is strictly blocked, requiring all operations to utilize the approved API catalog.

2 integration point(s) are specified, 2 of them against a channel that exists today. The full inventory, with endpoints and evidence, is [`integration_point_inventory` v1](/api/artifacts/184c31dba5b942fbaf0730955e7bc7d3/content); the plan that groups them by what each needs is `integration_plan` — **not committed**.

### SR-I01 — INT_01 (reinsurance_portal)

The system **shall** integrate with `reinsurance_portal` over `API` (bidirectional) at `no endpoint named`.

- **Serves:** Facultative referrals
- **Needs:** existing endpoint
- **Evidence:** guidewire_policycenter_life_uw_api_docs.pdf

Source: [`integration_point_inventory` v1](/api/artifacts/184c31dba5b942fbaf0730955e7bc7d3/content), row `INT_01`.

### SR-I02 — INT_02 (policycenter)

The system **shall** integrate with `policycenter` over `API` (bidirectional) at `no endpoint named`.

- **Serves:** Referral status and response terms
- **Needs:** existing endpoint
- **Evidence:** guidewire_policycenter_life_uw_api_docs.pdf

Source: [`integration_point_inventory` v1](/api/artifacts/184c31dba5b942fbaf0730955e7bc7d3/content), row `INT_02`.

## Data requirements

The data moving through the solution consists of both verified structured fields and raw unstructured source inputs. Demographics, smoker status, applied sum assured, policy term, and selected riders move from PolicyCenter to the agents. Unstructured physical and digital documents, including the last three years of Income Tax Returns, Chartered Accountant financial certificates, and unstructured Medical Examiner Reports, are processed to extract structured income, vitals, tobacco status, and blood pressure readings. The evidence supporting this data flow is documented across the PolicyCenter API catalog, underwriter manuals, and actual system screenshots. There are no proposed data paths that lack corresponding integration endpoints in the current API inventory.

_No payload fields are specified, so no data contract exists yet._

## The memory this document references

Each of these is a living artifact in the process workspace. Open it for the detail this document summarises.

| Artifact | Key | Version | Open |
| --- | --- | --- | --- |
| Process step table | process_step_table | v1 | [`process_step_table` v1](/api/artifacts/4aa519a27c7f4056b274df136d313cc9/content) |
| Opportunity table | opportunity_table | v1 | [`opportunity_table` v1](/api/artifacts/f24250b5d1d44f7dbacbefbdd38e6d49/content) |
| Agent specifications | agent_specifications | v1 | [`agent_specifications` v1](/api/artifacts/4ace1d79387f45ce84e1ee529946392d/content) |
| What is not automated | not_automated_register | v1 | [`not_automated_register` v1](/api/artifacts/2e6c43c9c1f44717b2ab63a003c9eeaf/content) |
| Integration-point inventory | integration_point_inventory | v1 | [`integration_point_inventory` v1](/api/artifacts/184c31dba5b942fbaf0730955e7bc7d3/content) |
| — | integration_payloads | — | `integration_payloads` — **not committed** |
| — | integration_plan | — | `integration_plan` — **not committed** |
| KPI board definition | kpi_board_definition | v2 | [`kpi_board_definition` v2](/api/artifacts/c11645120a864bf2a172e76e8e176766/content) |
