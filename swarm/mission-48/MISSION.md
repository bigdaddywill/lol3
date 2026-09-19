# 48-Session Coordination Mission

mission_id: 48-SESSION-COORDINATION-001
single_purpose: Prove that 48 isolated worker sessions can receive one shared directive, execute independently, and return evidence that a single integrator can verify.

shared_directive: Every worker must boot, load this exact mission, validate the mission contract, and return one machine-readable result tied to its unique session identity.

evidence_requirement: Each worker must prove that it loaded the shared mission, ran on a Linux GitHub-hosted VM, and that its result belongs to this mission.

integration_rule: The mission passes only if exactly 48 unique worker identities report, every worker references the same mission, every worker sees the same mission hash, every worker reports the expected runner platform, and the integrator can synthesize one consolidated result.

failure_rule: The integrator must run even when one or more workers fail, record the partial evidence, and mark the mission FAIL unless all required conditions are satisfied.

## Scope

This is the infrastructure/coordination proof first. It does not claim that 48 actual ChatGPT UI conversations were spawned. The workers are isolated GitHub-hosted VM sessions. The next phase can replace the deterministic worker body with real model-driven agent work once the coordination primitive is proven.

## Success condition

48/48 workers report READY, identities are unique, the shared mission hash is identical across all workers, every worker reports the expected Linux VM environment, and the integrator produces a persisted PASS report in `swarm/runs/`.

## Audit revision

The final proof must preserve worker start/end timestamps, runner identity/platform evidence, measured maximum worker overlap, and the provenance source commit of the run. A PASS without that evidence is not considered final.

## Next phase

After this proof is independently audited, replace the deterministic worker body with real model-driven agents while preserving the same mission/evidence/integration gates.
