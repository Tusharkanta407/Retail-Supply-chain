# STRIDE Analysis of Supply Chain APIs

| Endpoint | S - Spoofing | T - Tampering | R - Repudiation | I - Info Disclosure | D - Denial of Service | E - Elevation of Privilege |
|---|---|---|---|---|---|---|
| POST /upload | Fake client uploads data | Malicious/poisoned CSV alters sales data | User denies uploading | Uploaded file exposed | Huge files exhaust disk/memory | Upload path abuse to write arbitrary files |
| POST /process | Unauthorised trigger | Pipeline scripts modified | No record of who ran it | Stack traces leak internals | Repeated runs overload Spark | Command injection via inputs |
| GET /warehouse-summary, /inventory-summary | Impersonating a partner | Response manipulated in transit | - | Competitors read stock levels | Request flooding | Read-only role calling write APIs |
| POST /demand-simulation | Stolen API key | Prompt injection alters GPT output | No log of simulations | Business data sent to GPT | Cost/rate abuse of GPT calls | Free user using admin scenarios |

## Mitigations
| Threat | Mitigation (implemented in app.py unless noted) |
|---|---|
| Spoofing | API key check on write endpoints; production: OAuth2/JWT + mTLS |
| Tampering | CSV-only, size limit, schema validation; HTTPS; checksums (production) |
| Repudiation | Audit logging of user, endpoint, timestamp (production) |
| Info Disclosure | HTTPS, least-data prompts to GPT, generic error messages, RBAC |
| Denial of Service | 20 MB upload cap; rate limiting (e.g. slowapi/API gateway) |
| Elevation of Privilege | Role-based access, scenario whitelist, no shell input from users |
