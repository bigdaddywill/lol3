# LOL3 Benchmark History

No valid LOL3 benchmark has completed yet.

## Inherited LOL2 evidence
- Gemini Web security diagnosis: 24/24.
- Qwen 3B Q4 security diagnosis: 19/24.
- Qwen 1.5B Q4 security diagnosis: 10/24.
- 7B excluded for speed.
- Cases included SQL injection, XSS, path traversal, command injection, SSRF, and insecure deserialization.
- A later benchmark expanded to coding, debugging, reasoning, audit, and collective capability cases.
- One later GitHub run reached the runtime stage with commander, separate auditor, and subordinate successfully started, but the run was cancelled and is not a valid result.

## LOL3 rule
Do not copy inherited scores into LOL3. LOL3 needs its own benchmark against its own implementation and inputs.

## Benchmark design principles
- show individual case progression
- persist raw evidence
- validate browser traces when browser auditing is used
- execute generated code in a restricted test harness when appropriate
- inspect semantic correctness instead of relying on keyword scores alone
- record failures as failures rather than smoothing them into a pass