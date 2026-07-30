# Backend Defect Log

| ID | Severity | Description | Status |
|---|---|---|---|
| D1 | P0 | Historical branch contained malformed router package content and missing `/v1` wiring. | Must verify in current main |
| D2 | P2 | Historical pagination ceiling was 100 instead of contract value 200. | Validation fix recorded |
| D3 | P3 | Empty update error may lack a field pointer. | Open improvement |
| D4 | P1 | Retest observed HTTP 500 for valid `page_size=200`. | Open; requires logs and regression test |
