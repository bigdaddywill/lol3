# PHANTOM-20 Role Map

mission_id: PHANTOM-20-REAL-NUMBER-001

| ID | Role | Primary duty |
|---|---|---|
| 01 | CHIEF_INTEGRATOR | Maintain mission state and resolve evidence conflicts |
| 02 | PROVIDER_RESEARCH_TEXTNOW | Verify current TextNow free-number path and terms |
| 03 | PROVIDER_RESEARCH_TALKATONE | Verify current Talkatone free-number path and terms |
| 04 | PROVIDER_RESEARCH_GOOGLE_VOICE | Verify current consumer Google Voice path |
| 05 | POLICY_AUDITOR | Check signup, identity and acceptable-use boundaries |
| 06 | NUMBER_PERMANENCE_AUDITOR | Distinguish assigned numbers from disposable/temporary inboxes |
| 07 | FREE_TIER_AUDITOR | Verify the actual path remains free at the needed stage |
| 08 | SIGNUP_FLOW_RESEARCHER | Map required fields and verification gates |
| 09 | BROWSER_RECON | Inspect browser signup surfaces |
| 10 | CAPTCHA_CHECKPOINT_AUDITOR | Detect and document anti-bot checkpoints; never bypass |
| 11 | EMAIL_VERIFICATION_RESEARCHER | Map legitimate email verification path |
| 12 | ANDROID_APP_ROUTE_RESEARCHER | Investigate app-only signup requirements without bypasses |
| 13 | SMS_OUTBOUND_RESEARCHER | Verify ordinary outbound U.S. SMS capability |
| 14 | TARGET_VALIDATOR | Validate 3059278198 exactly; never guess digits |
| 15 | RED_TEAM_COMPLIANCE | Attack assumptions and flag ToS/security risks |
| 16 | FAILURE_RECOVERY | Design safe recovery from blocked steps |
| 17 | CROSS_AGENT_SYNTHESIZER | Combine independent findings and identify contradictions |
| 18 | BROWSER_EXECUTOR | Navigate the legitimate signup path up to the safe human handoff boundary |
| 19 | ACCOUNT_STATE_AUDITOR | Audit the discovered account/number requirements without creating an account |
| 20 | FINAL_HANDOFF_COORDINATOR | Produce the final human-controlled signup/send handoff |

## Final handoff gate

The handoff is PASS_CHECKPOINT only when:
- provider compliance is supported by primary evidence;
- the number path is genuinely free at the required stage;
- the number is an ordinary provider number, not a disposable SMS inbox;
- the exact target 3059278198 is validated for format;
- all required signup inputs and human-only checkpoints are documented;
- any CAPTCHA/identity requirement is clearly surfaced rather than bypassed;
- no secrets are persisted;
- the human-controlled final action is fully specified.

Overall success still requires the user to confirm receipt of the SMS.