# Data-flow Map

How data moves between the systems this process touches.

| From | To | What moves | Channel | Evidence |
| --- | --- | --- | --- | --- |
| SYS-03 | SYS-01 | Medical examination reports, lab results, and physical vitals results | API | guidewire_policycenter_life_uw_api_docs.pdf: POST /submissions/{id}/medical/results |
| SYS-01 | SYS-02 | Facultative reinsurance referrals, risk summaries, and case details | API | guidewire_policycenter_life_uw_api_docs.pdf: POST /reinsurance/referrals |
| SYS-01 | SYS-02 | Provisional risk summary before formal medicals are complete | unknown | interview_senior_underwriter_INT-2025-014.txt: S4 Send Provisional Referral |
| SYS-02 | SYS-01 | Reinsurance decisions and confirmed terms | API | guidewire_policycenter_life_uw_api_docs.pdf: GET /reinsurance/referrals/{id} |

## On the screens

### 1. process_performance_q2_2025.png

![process_performance_q2_2025.png](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/c104f51a3c4d4d6e8cf6e90114788d39/content)

**Data on this screen:** Proposer age, gender, occupation, and smoker status; Applied Sum Assured and policy term; Selected riders (e.g., CI, ADB, WOP); Proof of age; productCode (e.g., MST-2024); proposer partyId; lifeAssured partyId; sumInsured; termYears; premiumMode; riders.

### 2. screenshot_1_financial_details.png

![screenshot_1_financial_details.png](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/a1d589e2240b491da179665a4fcb81b8/content)

**Data on this screen:** Income proof status; Human Life Value limit; ITR (last 3 years) or CA-certified financials; declared income; proof status; HLV computation results; income-proof document reference.

### 3. screenshot_2_medical_examination_details.png

![screenshot_2_medical_examination_details.png](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/a0f64d94b1bd4e7dad60930e93f57afc/content)

**Data on this screen:** Non-medical limits (NML); Medical grid requirements; Proposer build (height, weight, BMI); age band; sumInsured; required tests list.

### 4. screenshot_3_pricing_and_risk.png

![screenshot_3_pricing_and_risk.png](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/a576e007f5b54e52a3eeb41e9f27d14b/content)

**Data on this screen:** Proposer profile; Referral trigger; Underwriter best-guess rating.

### 5. screenshot_4_closing_summary.png

![screenshot_4_closing_summary.png](/api/processes/96c51b6eb11f4f7284cf4699c14846a3/sources/2e0e012899fe4245b9cf8d51c6e015d3/content)

**Data on this screen:** Outstanding medical grid tests status; Incoming medical reports (MER, lab results, ECG/TMT).
