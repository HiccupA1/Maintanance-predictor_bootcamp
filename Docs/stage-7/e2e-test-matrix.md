# End-to-End Test Matrix

| Flow | Expected result |
|---|---|
| Admin creates equipment | Equipment appears with criticality |
| Plant Manager configures threshold | Parameter is visible and active |
| Operator records in-range reading | Reading appears; no active breach |
| Operator records boundary reading | Alert is created because boundary is inclusive |
| Repeat breach | Existing active alert is updated, not duplicated |
| Plant Manager converts alert | One linked open work order is created |
| Engineer closes work order | Required fields validate; alert resolves; service date updates |
| Forbidden action | Clear denial; no mutation |
| API outage | Error state and retry affordance are shown |
