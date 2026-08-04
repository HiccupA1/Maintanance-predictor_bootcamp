# Frontend Dev Server Troubleshooting

## 1) Vite preview says: "Blocked request. This host is not allowed"

**Symptom**
- When using the Kavia preview / reverse proxy, you may see a Vite error page:
  - `Blocked request. This host is not allowed`

**Cause**
- Vite performs host header validation and may reject the preview hostname unless explicitly allowed.

**Fix**
- In `vite.config.ts`, set:

```ts
server: {
  allowedHosts: true,
}
preview: {
  allowedHosts: true,
}
```

This allows the Kavia preview hostname (and other proxy hosts) to access the dev server.

---

## 2) Dev server crashes with esbuild SIGSEGV

**Symptom**
- `npm run dev` fails to start with errors like:
  - `SIGSEGV: segmentation violation`
  - `Error: The service was stopped`

**Notes**
- This environment has previously shown intermittent esbuild runtime faults.
- `VITE_SAFE_MODE=1` (or `npm run dev:safe`) disables Vite plugins, but it may not prevent an underlying esbuild binary crash.

**Potential mitigations**
- Try reinstalling dependencies (`npm install`) and ensure the runtime’s Node version matches the project’s expected version.
- If the crash persists, consider pinning to a known-good `esbuild` + `vite` combination for the runtime environment.
