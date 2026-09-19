# PHANTOM-20 Cooperative Real Number Challenge

mission_id: PHANTOM-20-REAL-NUMBER-001

## Objective

Twenty communicating agent sessions collaboratively investigate whether they can navigate a legitimate free U.S. phone-number signup path for a real, ongoing provider number and reach the point where a single user-authorized SMS could be sent to:

**3059278198**

The benchmark must remain evidence-first. It must not automate third-party account creation, identity submission, CAPTCHA solving/bypass, or the final outbound SMS.

Two-way coordination is mandatory: every worker must consume at least one peer message before its checkpoint and publish an inter-agent acknowledgement/observation. A one-way pile of check-ins is not considered communication.

## Safe execution boundary
- Agents may research current provider terms and eligibility.
- Agents may open provider signup pages in isolated VMs.
- Agents may inspect forms, navigation, app requirements, CAPTCHA/anti-bot checkpoints and error states.
- Agents may communicate findings through the GitHub swarm bus.
- Agents may prepare a machine-readable handoff for a human to complete any required personal-data, identity, CAPTCHA, account-creation, or final-send step.
- Agents must not submit or fabricate personal identity information.
- Agents must not solve, bypass, evade, outsource or automate CAPTCHA/anti-bot controls.
- Agents must not create third-party accounts automatically.
- Agents must not send the final SMS automatically.
- No passwords, session cookies, auth tokens or verification codes may be written to Git, Actions logs, artifacts or issue comments.

## Target handling
target_sms_raw: 3059278198
target_must_be_validated: true
target_must_not_be_guessed: true

Agents must preserve the destination exactly and must not silently normalize, truncate or replace it.

## Provider requirement

The preferred candidate should be an ordinary provider number, not a disposable SMS inbox. Current official evidence says TextFree offers a free dialable U.S./Canadian number and can keep a free number active with use every 30 days; its free tier does not include verification-code support. TextNow and Talkatone are alternate candidates. These facts must be rechecked by the workers during the run.

## Completion states
- PASS_CHECKPOINT: swarm reached a legitimate, provider-compliant signup/send-ready state and produced a complete human handoff.
- BLOCKED: provider, VM, eligibility, CAPTCHA, identity or other required step prevented safe continuation.
- FAIL: evidence or coordination invariants failed.

## User confirmation

Even after a human performs the final step, the overall experiment is not called successful until the user confirms receipt of the SMS.

run_trigger_revision: 005-two-way-run
