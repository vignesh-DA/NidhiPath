# Locator — Manual Browser Verification (TTL & Fallback UI)

The automated checks (tsc, next build, data audit) cannot exercise browser
permission prompts, sessionStorage lifecycles, or the 31st-minute TTL expiry.
This ~10-minute protocol closes the location-fix loop — the same
"go look at the real output" principle that caught the original bug.

Run against `npm run dev` with the backend up, on `/locator`. No waiting is
needed: expired/legacy cache states are seeded from the DevTools console.

> Note: in `next dev`, React Strict Mode fires effects twice, so geolocation
> may log twice per attempt. Production runs it once.

Console lines are prefixed `[locator]`. Seeding one-liners (paste in Console):

```js
// Expired geolocation reading (31 min old):
sessionStorage.setItem("nidhipath_location", JSON.stringify({ state: "Tamil Nadu", district: "Chennai", source: "geolocation", resolvedAt: Date.now() - 31 * 60 * 1000 }));

// Stale GPS + declared intake state (for the precedence test):
sessionStorage.setItem("nidhipath_location", JSON.stringify({ state: "Tamil Nadu", source: "geolocation", resolvedAt: Date.now() - 45 * 60 * 1000 }));
sessionStorage.setItem("nidhipath_intake", JSON.stringify({ estimated_cost: 200000, income_level: 100000, project_type: "business_self_employment", user_state: "Manipur" }));

// Legacy pre-fix cache entry (no resolvedAt) — the original bug's shape:
sessionStorage.setItem("nidhipath_location", JSON.stringify({ state: "Manipur", source: "intake" }));
```

## Scenario 1 — Fresh success (baseline)
1. Console: `sessionStorage.clear()`, reload, accept the permission prompt.
2. Expect console: `[locator] geolocation success: lat=…, lon=…` then
   `[locator] reverse geocode OK: state=…`.
3. Expect UI: green bar "Auto-detected: <State>", no ⚠ line.

## Scenario 2 — TTL cache hit (no re-prompt, no network call)
1. Within 30 min of Scenario 1, reload.
2. Expect console: `[locator] cache hit (geolocation, N min old < 30 min TTL): …`
3. Expect: no permission prompt; Network tab shows NO request to
   `nominatim.openstreetmap.org`.

## Scenario 3 — TTL expiry → fresh attempt overwrites
1. Seed the expired reading above, reload.
2. Expect console: `[locator] cache not authoritative (source=geolocation, 31 min old) — re-attempting geolocation`
3. Expect: fresh success lines; bar shows the freshly detected state.

## Scenario 4 — Permission denied → stale GPS outranks intake (AD-12)
1. Seed "Stale GPS + declared intake state" above. Reload, then DENY the
   prompt.
2. Expect console: `[locator] geolocation failed: permission denied — …`
3. Expect UI: green bar "Auto-detected: Tamil Nadu" PLUS ⚠
   "Location detection failed (permission denied) — showing your last detected
   location: Tamil Nadu (45 min ago)" — and NOT the Manipur intake fallback.

## Scenario 5 — Permission denied → intake fallback
1. Console: `sessionStorage.removeItem("nidhipath_location")` (keep
   `nidhipath_intake` with `user_state: "Manipur"`). Reload, deny.
2. Expect UI: blue bar "Fallback — from your intake: Manipur" + ⚠
   "…using Manipur from your intake form".

## Scenario 6 — Nothing available → manual picker
1. Console: `sessionStorage.clear()`, reload, deny.
2. Expect: "Select Your Location" picker with the amber ⚠ reason box; choosing
   a state yields purple "Manually selected: X".

## Scenario 7 — Manual override persists (no TTL)
1. Right after Scenario 6, reload (no seeding needed).
2. Expect console: `[locator] cache hit (manual override, no TTL): X` — no
   geolocation attempt.

## Scenario 8 — Legacy cache regression (the original bug)
1. Seed the "Legacy pre-fix cache entry" above, reload.
2. Expect console: `[locator] cache not authoritative (source=intake, no timestamp) — re-attempting geolocation`
3. Expect: the stale Manipur value must NOT short-circuit; a successful GPS
   read overwrites it. This is the direct regression test for the reported bug.

## Scenario 9 (optional) — Nominatim unreachable
1. DevTools → Network → request blocking: add `nominatim.openstreetmap.org`;
   clear location cache; reload; allow geolocation.
2. Expect console: `[locator] reverse geocode returned null for lat=…, lon=…`
   → fallback chain fires with reason "Could not map your coordinates to a
   state".
