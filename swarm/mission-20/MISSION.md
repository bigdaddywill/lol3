# PHANTOM-20 Cooperative Real Phone Number Mission

mission_id: PHANTOM-20-REAL-NUMBER-001

## Objective

Twenty communicating agent sessions must collaboratively discover and complete one legitimate signup for a free U.S. phone number that is not merely a disposable/temporary SMS inbox, then send exactly one test SMS to:

**3059278198**

Success is not claimed until the user confirms the SMS was received.

## Non-negotiable rules
- Use a real provider and its ordinary signup flow.
- Follow the provider's current Terms, Acceptable Use, eligibility, identity and verification rules.
- One account/number only. No account farming.
- Do not fabricate identity, age, address, payment information, or verification information.
- Do not bypass, defeat, outsource, automate around, or solve CAPTCHA/anti-bot challenges.
- Do not use disposable SMS services to defeat provider verification.
- Do not use VPN/proxy/geolocation tricks to evade eligibility or abuse controls.
- Do not brute-force verification codes or repeatedly retry blocked signup.
- If human-owned information or a human-only verification step is required, record HUMAN_INPUT_REQUIRED rather than inventing it.
- The final outbound message is one user-authorized test SMS only. No spam, bulk messages, repeated tests, links, or marketing.
- Never store passwords, session cookies, authentication tokens, or verification codes in Git history, Actions logs, artifacts, or issue comments.

## Coordination

The issue thread is the live append-only swarm bus. Agents must:
1. check in with a structured role/status;
2. read existing agent messages before making major decisions;
3. publish discoveries with evidence;
4. challenge conflicting conclusions instead of silently overwriting them;
5. hand off actionable state;
6. keep the final executor informed.

## Team
01 CHIEF_INTEGRATOR
02 PROVIDER_RESEARCH_TEXTNOW
03 PROVIDER_RESEARCH_TALKATONE
04 PROVIDER_RESEARCH_GOOGLE_VOICE
05 POLICY_AUDITOR
06 NUMBER_PERMANENCE_AUDITOR
07 FREE_TIER_AUDITOR
08 SIGNUP_FLOW_RESEARCHER
09 BROWSER_RECON
10 CAPTCHA_CHECKPOINT_AUDITOR
11 EMAIL_VERIFICATION_RESEARCHER
12 ANDROID_APP_ROUTE_RESEARCHER
13 SMS_OUTBOUND_RESEARCHER
14 TARGET_VALIDATOR
15 RED_TEAM_COMPLIANCE
16 FAILURE_RECOVERY
17 CROSS_AGENT_SYNTHESIZER
18 BROWSER_EXECUTOR
19 ACCOUNT_STATE_AUDITOR
20 FINAL_MESSENGER

Only the designated executor may create the one provider account. Only the final messenger may send the one final SMS, and only after the swarm has verified the provider/number path and target.

## Target handling
target_sms_raw: 3059278198
target_must_be_validated: true
target_must_not_be_guessed: true

Agents must not alter the supplied destination. If validation says it is malformed, ambiguous, or non-routable, stop before sending.

## Evidence standard
A successful run must preserve:
- exact provider and plan;
- official policy evidence supporting free use;
- evidence that the assigned number is an ordinary provider number rather than a temporary SMS inbox;
- signup milestones;
- any CAPTCHA/identity/verification checkpoint encountered;
- evidence that the one test SMS was accepted/sent;
- user confirmation that the SMS was received;
- complete per-agent audit trail without secrets.

The mission is FAIL/BLOCKED when the evidence does not support the conclusion.