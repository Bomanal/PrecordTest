# Workflow and UI Understanding

The operator navigates across Guidewire PolicyCenter screens to execute financial, medical, and pricing underwriting before issuing the final terms. The documentation is thinnest during initial registration and when waiting on external medical/customer responses.

Channels with evidence: screen.

A channel absent above is undocumented, not absent from the process.

## SURF-01 — Financial Details

![Financial Details](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/a1d589e2240b491da179665a4fcb81b8/content)

*screenshot_1_financial_details.png*

- Channel: screen
- Purpose: Review financial justifications, occupation data, and evidence checklists to satisfy financial underwriting requirements.
- System: Guidewire PolicyCenter — Life & Annuity, Underwriting
- Steps served: S2 (high confidence)
- Next: navigation: Medical Exam Details->SURF-02, navigation: Pricing & Risk->SURF-03, navigation: Closing Summary->SURF-04
- Evidence: screenshot_1_financial_details.png

| data point | type | obligation | origin |
| --- | --- | --- | --- |
| Case ID | code | unknown | from_source_system |
| Proposer / Life Assured | free text | unknown | from_source_system |
| Product | free text | unknown | from_source_system |
| Term | free text | unknown | from_source_system |
| Sum Insured | currency | unknown | from_source_system |
| Declared annual income | currency | unknown | from_source_system |
| Income proof status | free text | unknown | unknown |
| Applied Sum Insured | currency | unknown | from_source_system |
| HLV-justified amount | currency | unknown | system_derived |
| Existing in-force cover (other insurers) | currency | unknown | from_source_system |
| Aggregate cover post-issue | currency | unknown | system_derived |
| Occupation | free text | unknown | from_source_system |
| Occupation class | free text | unknown | from_source_system |
| Employer | free text | unknown | from_source_system |
| Financial underwriter notes | free text | unknown | from_source_system |

Actions:
- **navigation: Submission Intake** (navigate): effect not documented
- **navigation: Financial Details** (navigate): effect not documented
- **navigation: Medical Exam Details** (navigate): SURF-02
- **navigation: Pricing & Risk** (navigate): SURF-03
- **navigation: Closing Summary** (navigate): SURF-04
- **Request Income Proof** (other): effect not documented
- **Record Proof Received** (other): effect not documented
- **Counter-Offer Sum Insured** (other): effect not documented
- **Set Financial UW Status** (other): effect not documented

## SURF-02 — Medical Exam Details

![Medical Exam Details](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/a0f64d94b1bd4e7dad60930e93f57afc/content)

*screenshot_2_medical_examination_details.png*

- Channel: screen
- Purpose: Review and record physical vitals, disclosed medical history, BMI band classifications, and laboratory flags.
- System: Guidewire PolicyCenter — Life & Annuity, Underwriting
- Steps served: S6 (high confidence)
- Next: navigation: Financial Details->SURF-01, navigation: Pricing & Risk->SURF-03, navigation: Closing Summary->SURF-04
- Evidence: screenshot_2_medical_examination_details.png

| data point | type | obligation | origin |
| --- | --- | --- | --- |
| Height | free text | unknown | user_entered |
| Weight | free text | unknown | user_entered |
| BMI (auto-calculated) | free text | unknown | system_derived |
| Blood pressure (sitting) | free text | unknown | user_entered |
| Tobacco use | free text | unknown | user_entered |
| MER reference | free text | unknown | user_entered |
| Condition | free text | unknown | user_entered |
| Family history | free text | unknown | user_entered |
| Impairment record | free text | unknown | user_entered |

Actions:
- **navigation: Submission Intake** (navigate): effect not documented
- **navigation: Financial Details** (navigate): SURF-01
- **navigation: Medical Exam Details** (navigate): effect not documented
- **navigation: Pricing & Risk** (navigate): SURF-03
- **navigation: Closing Summary** (navigate): SURF-04
- **Order Tests** (other): effect not documented
- **Record Results** (other): effect not documented
- **Request Tele-Underwriting** (other): effect not documented
- **Add Impairment** (other): effect not documented

## SURF-03 — Pricing & Risk

![Pricing & Risk](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/a576e007f5b54e52a3eeb41e9f27d14b/content)

*screenshot_3_pricing_and_risk.png*

- Channel: screen
- Purpose: Evaluate rating components, perform risk assessments, enter overrides, and manage reinsurance referrals.
- System: Guidewire PolicyCenter — Life & Annuity, Underwriting
- Steps served: S8 (high confidence), S9 (high confidence), S11 (high confidence)
- Next: navigation: Financial Details->SURF-01, navigation: Medical Exam Details->SURF-02, navigation: Closing Summary->SURF-04
- Evidence: screenshot_3_pricing_and_risk.png

| data point | type | obligation | origin |
| --- | --- | --- | --- |
| Case ID | code | unknown | from_source_system |
| Proposer / Life Assured | free text | unknown | from_source_system |
| Product | free text | unknown | from_source_system |
| Term | free text | unknown | from_source_system |
| Sum Insured | currency | unknown | from_source_system |
| Decision Status Header | free text | unknown | system_derived |
| Rating engine suggested EM | free text | unknown | system_derived |
| Underwriter override | free text | unknown | user_entered |
| Referred to | free text | unknown | user_entered |
| Reinsurer terms | free text | unknown | user_entered |
| Decision | free text | unknown | user_entered |
| Override reason | free text | mandatory | user_entered |

Actions:
- **navigation: Submission Intake** (navigate): effect not documented
- **navigation: Financial Details** (navigate): SURF-01
- **navigation: Medical Exam Details** (navigate): SURF-02
- **navigation: Pricing & Risk** (navigate): effect not documented
- **navigation: Closing Summary** (navigate): SURF-04
- **Enter / Override EM** (other): effect not documented
- **Raise Referral** (refer): effect not documented
- **Select Decision** (other): effect not documented

Enforced rules:
- Override reason is mandatory when underwriter override is entered. — blocking ("not stated")

## SURF-04 — Closing Summary

![Closing Summary](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/2e0e012899fe4245b9cf8d51c6e015d3/content)

*screenshot_4_closing_summary.png*

- Channel: screen
- Purpose: Review final terms and case timeline to confirm and complete policy issuance.
- System: Guidewire PolicyCenter — Life & Annuity, Underwriting
- Steps served: S12 (high confidence), S14 (high confidence), S15 (high confidence)
- Next: navigation: Financial Details->SURF-01, navigation: Medical Exam Details->SURF-02, navigation: Pricing & Risk->SURF-03
- Evidence: screenshot_4_closing_summary.png

| data point | type | obligation | origin |
| --- | --- | --- | --- |
| Case ID | code | unknown | from_source_system |
| Proposer / Life Assured | free text | unknown | from_source_system |
| Product | free text | unknown | from_source_system |
| Term Length | free text | unknown | from_source_system |
| Header Sum Insured | currency | unknown | from_source_system |
| Header Status | free text | unknown | system_derived |
| Sum Insured | currency | unknown | from_source_system |
| Term | free text | unknown | from_source_system |
| Riders | free text | unknown | from_source_system |
| Rating | free text | unknown | from_source_system |
| Annual premium | currency | unknown | from_source_system |
| Premium mode | free text | unknown | from_source_system |
| Referral outcome | free text | unknown | from_source_system |
| Evidence relied upon | free text | unknown | from_source_system |
| Application received | date | unknown | from_source_system |
| Financial UW complete | date | unknown | from_source_system |
| Medical evidence complete | date | unknown | from_source_system |
| Rating assessed / referral raised | date | unknown | from_source_system |
| Referral response received | date | unknown | from_source_system |
| Decision recorded / policy issued | date | unknown | from_source_system |

Actions:
- **navigation: Submission Intake** (navigate): effect not documented
- **navigation: Financial Details** (navigate): SURF-01
- **navigation: Medical Exam Details** (navigate): SURF-02
- **navigation: Pricing & Risk** (navigate): SURF-03
- **navigation: Closing Summary** (navigate): effect not documented
- **Issue Offer** (other): effect not documented
- **Record Acceptance** (other): effect not documented
- **Close as NTU / Decline** (reject): effect not documented
- **Issue Policy** (approve): effect not documented

## Steps with no surface

Work the step table records that no supplied surface serves. Either it happens outside the system — which is where an automation case usually lives — or the screen for it was never uploaded. A finding, not an error.

- **S1** Register Application — Done on a surface nobody supplied (Submission Intake screen is referenced in navigation but no screenshot is present).
- **S3** Determine Medical Requirements — Done on a surface nobody supplied (medical grid rules lookup and test ordering configuration are not shown).
- **S4** Send Provisional Referral — done outside the system
- **S5** Wait for Medical Results — done outside the system
- **S7** Review Health Declaration — Done on a surface nobody supplied (applicable for non-medical acceptance cases, but screen is missing).
- **S10** Wait for Reinsurance Response — done outside the system
- **S13** Wait for Customer Response — done outside the system

## What is not documented

- Missing Registration Surface: The screen for S1 (Register Application) is referenced but no screenshot was supplied. (ask: Intake Underwriter)
- Missing Medical Grid / Requirements Surface: The screen or interface for determining medical requirements (S3) is not supplied. (ask: Underwriting Operations)
- Missing Health Declaration Surface: No screen was supplied for S7 (Review Health Declaration) which is used for non-medical acceptance cases. (ask: Underwriter)
- Provisional Reinsurance Referral Channel Details: Details of the provisional summary template and the communication channel used in S4 are absent. (ask: Reinsurance Desk)
