# Phase 5 - Additional Insights

## 1) Churn/Risk signal scoring
Signals combined:
- Negative sentiment pressure (utterance-level)
- Renewal/commercial language
- Urgency markers
- Incident/outage mentions
- Churn/concern key moments

Top risk meetings:
- 01KQ7BF0D56037FF89DC89B6 | support | Support Troubleshooting & Case Resolution | score=93.58 (critical) | Support Case #3266 - Trailhead Marketplace Detect Alerts Not Firing
- 01KQ46A9DE0AECB006D897A0 | ambiguous | Incident Response & Outage Management | score=92.15 (critical) | Detect Outage - Escalation Bridge
- 01KQ88B8EAEAA819C26CCBE7 | external | Compliance & Audit Readiness | score=92.13 (critical) | ESCALATION: Northstar Pharma - Detect Outage Impact on Compliance
- 01KQEDB92E33CF9945A7F71B | external | Incident Response & Outage Management | score=91.11 (critical) | URGENT: Cobalt Software - Aegis Detect Dashboard Down
- 01KQ2331EFD78BF3B1CAB747 | ambiguous | Incident Response & Outage Management | score=90.91 (critical) | Detect Outage - Customer Impact Assessment
- 01KQ2D93184912F0147315E7 | external | Incident Response & Outage Management | score=90.82 (critical) | URGENT: Blackridge Investments - Complete Loss of Threat Visibility
- 01KQ351E141926AB7CAB668D | external | Incident Response & Outage Management | score=86.94 (critical) | Aegis / Northstar Pharma - Urgent: Detect Outage Impact
- 01KQ8C5A044F54EE1774D53C | external | Incident Response & Outage Management | score=86.25 (critical) | Aegis / Helix Data - Post-Incident Review

## 2) Action-item execution pressure
Method:
- Parse action items from summaries
- Infer owner/function and work type
- Score pressure by recurrence + urgency share + negative context

Highest pressure work types:
- technical_remediation: pressure=52.36, count=29, functions=engineering:27;program_management:1;customer_success_sales:1
- coordination_followup: pressure=51.99, count=229, functions=other:65;customer_success_sales:44;engineering:42
- analysis_reporting: pressure=51.33, count=30, functions=program_management:8;customer_success_sales:7;support:7
- general_followup: pressure=50.0, count=68, functions=other:37;customer_success_sales:20;engineering:9
- support_followup: pressure=31.8, count=13, functions=support:5;customer_success_sales:5;engineering:3
- compliance_followthrough: pressure=28.6, count=15, functions=support:7;compliance_security:5;customer_success_sales:3

## 3) Cross-functional friction map
Method:
- Detect disagreement/tension markers in summary + transcript
- Blend discourse markers with negative sentiment into friction score
- Aggregate by topic and call type

Highest-friction meetings:
- 01KQ5A966832A146DA4B7D41 | external | Identity, Access & Provisioning | friction=78.96 | speakers=Maria Santos:6;Alicia Monroe:6
- 01KQBBF753B44DE677670E6D | support | Support Troubleshooting & Case Resolution | friction=78.02 | speakers=David Kim:6;Gregory Fisk:4;Alicia Monroe:3
- 01KQ9772B2348F500FB09D1E | support | Support Troubleshooting & Case Resolution | friction=77.64 | speakers=Elena Vasquez:6;Vanessa Cruz:5
- 01KQC166F678CBA584AAFF8B | support | Support Troubleshooting & Case Resolution | friction=77.34 | speakers=Sarah Chen:8;Derek Owens:1
- 01KQBB7C4D4789DB2F3DA9C2 | support | Support Troubleshooting & Case Resolution | friction=77.2 | speakers=Dr. Linda Cheng:4;Priya Patel:4;Sarah Chen:2
- 01KQ7BF0D56037FF89DC89B6 | support | Support Troubleshooting & Case Resolution | friction=74.51 | speakers=Elena Vasquez:3;David Kim:1
- 01KQEDB92E33CF9945A7F71B | external | Incident Response & Outage Management | friction=73.07 | speakers=David Kim:5;Lauren Bishop:2
- 01KQ5EC1665DCFD7A6B62A59 | support | Support Troubleshooting & Case Resolution | friction=72.81 | speakers=Vanessa Cruz:4;Elena Vasquez:3;Marcus Williams:1

## Why this matters
- Risk scoring helps revenue and support leaders prioritize accounts before churn manifests.
- Execution pressure identifies repeating operational burdens that can stall sentiment recovery.
- Friction mapping shows where alignment breaks down across teams and call contexts.