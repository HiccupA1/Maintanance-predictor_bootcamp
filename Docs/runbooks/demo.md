# Local Client Demo

This runs the whole product on one laptop with a realistic demo plant, with
no Supabase project needed. It is meant for client demos and for learning
the system. **It is not a deployment.**

## What runs
| Piece | Where | Notes |
|---|---|---|
| Frontend | http://127.0.0.1:4173 | Production build (`vite build`, then `vite preview`) |
| API | http://127.0.0.1:8000 (docs at `/docs`) | The real FastAPI app, with `APP_ENV=dev` |
| Sign-in stand-in | http://localhost:54321 | `tools/demo/auth_stub.py`; see below |
| Database | the Postgres you point it at | **Dropped and rebuilt on every start** |

### About sign-in
- The frontend normally signs in through Supabase Auth. In the demo,
  `tools/demo/auth_stub.py` answers those few endpoints with sessions signed
  by a local test key (`tools/testenv`).
- The API still verifies every token through its real JWKS code. Roles come
  from the database, and every permission check runs exactly as in
  production.
- Only the sign-in service itself is simulated.
- **Never deploy the stand-in.** The API only accepts its `file://` key
  outside production (`APP_ENV=dev` or `test`).

## Start
Prerequisites:
- Python venv with `pip install -e ".[dev,ml]"`;
- `npm ci` in `frontend/`;
- a Postgres you can use for disposable data.

```powershell
./tools/demo/start.ps1 -DatabaseUrl "postgresql+psycopg2://postgres:postgres@localhost:5432/demo"
```

The first run trains the model, which takes about a minute and downloads
the AI4I dataset. The script then:
1. resets the schema;
2. seeds users and keys;
3. starts the three servers;
4. loads the demo plant (`tools/demo/seed_data.py`, all through the real
   API).

Stop with `./tools/demo/stop.ps1`.

**Logins expire after 8 hours.** Run `start.ps1` again to get fresh ones.

## Demo accounts (password `demo1234`)
| Role | Email | Lands on |
|---|---|---|
| Admin | `admin@testenv.invalid` | Work Orders, plus Admin and Models |
| Plant Manager | `plantmanager@testenv.invalid` | Alerts |
| Operator | `operator@testenv.invalid` | Readings |
| Maintenance Engineer | `maintenanceengineer@testenv.invalid` | Work Orders |

## The demo plant
| Machine | State |
|---|---|
| Cooling pump P-101 | Temperature breach, handled: the work order is closed as a confirmed failure, the alert is resolved, and the service date is updated |
| Air compressor C-201 | Pressure breach with an **open** work order, ready to close |
| Boiler feed pump B-301 | Repeated bearing-temperature breach with an **open alert** and no work order yet |
| CNC mill CNC-01 | Worn-tool readings: the risk model (`ai4i-v1`, active) flags it, and a MODEL alert is raised |
| CNC mill CNC-02 | Healthy readings: low risk |

## Suggested walkthrough (about 10 minutes)
1. **Operator:** on Readings, record a value on P-101 → Temperature that is
   above 80. The alert is created automatically.
2. **Plant Manager:**
   - on Alerts, open the B-301 alert and **Convert to Work Order**. The work
     order is prefilled and linked, and a second conversion is refused.
   - note the "Model" badge on the CNC-01 alert.
3. **Maintenance Engineer:** open the C-201 work order, then **Edit** and set
   the status to Closed. Fill in the closure record: was this a real failure?
   Which failure mode? Save. The alert resolves and the service date
   updates.
4. **Admin:**
   - **Equipment → CNC-01** shows the risk panel (At risk, with score
     history).
   - **Models** shows the shadow evaluation against threshold alerts, drift
     status, and activate or retire.
   - **Admin** is where users and roles are managed.
5. Optional: show `/docs` (API contract) and the 401/403 behaviour.

## Talking points (keep them accurate)
- The risk model is trained on the public **AI4I 2020** benchmark, which is
  synthetic. On its held-out test set it catches 93% of failures (PR-AUC
  0.87, against 0.48 for engineer rules).
- New models start in **shadow** and are promoted only after they are
  evaluated against the client's confirmed failures.
- Closing a work order records the failure label that trains the next model.
- Measured evidence:
  - 111 browser E2E tests (`Docs/stage-7/e2e-test-matrix.md`);
  - a KLM workflow comparison: 66% fewer steps, and an estimated 75–83% less
    operator time (`Docs/stage-9/workflow-comparison.md`);
  - a load test: p95 102 ms at 75 users (`Docs/stage-9/performance-report.md`).
