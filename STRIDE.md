# STRIDE Analysis of Supply Chain APIs

Threat model for the thin FastAPI service in `app.py`.

| Endpoint | S - Spoofing | T - Tampering | R - Repudiation | I - Info Disclosure | D - Denial of Service | E - Elevation of Privilege |
|---|---|---|---|---|---|---|
| POST /upload | Fake client uploads data | Malicious/poisoned CSV alters sales data | User denies uploading | Uploaded file exposed on disk | Huge files exhaust disk/memory | Upload path abuse to overwrite files |
| POST /process | Unauthorised pipeline trigger | Process step scripts modified | No durable audit of who ran it | Stack traces leak internals | Repeated Spark runs overload CPU/RAM | Caller triggers privileged batch jobs |
| GET /sales-summary, /warehouse-summary, /inventory-summary, /cluster-demand | Impersonating a partner | Response manipulated in transit | — | Competitors read stock/demand levels | Request flooding | Read APIs used to recon before write abuse |
| GET /cluster-plot | Same as above | Image swapped / MITM | — | Cluster strategy visible to rivals | Bandwidth abuse | — |
| POST /demand-simulation | Stolen API key | Prompt injection alters GPT output | No log of simulations | Business baselines sent to GPT | Cost/rate abuse of GPT calls | Unlisted scenarios / privilege via prompts |

## Mitigations

| Threat | Mitigation (prototype / production) |
|---|---|
| Spoofing | API key (`x-api-key`) on write endpoints; production: OAuth2/JWT + mTLS |
| Tampering | CSV-only upload, 20 MB size cap; HTTPS; schema validation; checksums (production) |
| Repudiation | Audit logging of user, endpoint, timestamp (production) |
| Info Disclosure | Least-data GPT prompts; generic 4xx/5xx messages; RBAC on inventory reads (production) |
| Denial of Service | 20 MB upload cap; rate limiting (API gateway / slowapi in production) |
| Elevation of Privilege | Scenario whitelist in `ai/demand_scenarios.py`; no shell input from users; separate process scripts |

## Prototype controls already in code

- `API_KEY` / `x-api-key` on `/upload`, `/process`, `/demand-simulation`
- CSV extension check + `MAX_UPLOAD = 20 MB`
- Scenario whitelist: Normal, Festival, Low demand, Supply disruption
- GPT fallback when `OPENAI_API_KEY` is unset (avoids hard failure / key leak in errors)
