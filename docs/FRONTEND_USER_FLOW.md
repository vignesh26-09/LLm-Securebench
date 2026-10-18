# Frontend user flow

- `/`: public orange/charcoal landing page with Framer Motion animation, Lucide SVG icons, and an adapted React Bits CountUp component.
- `/benchmark`: public model selection and test settings. Guests can run installed Gemma 3 4B, Qwen 3.5 2B, or Llama 3.2 3B presets, with up to ten cases per job. Submitting a run opens `/testing/:runId`.
- `/testing/:runId`: dedicated animated testing screen with real completion counts and provider stages. Completed tests automatically open the charts and results report.
- `/history`: separate history view with current server-session jobs and, after sign-in, earlier persisted runs.
- `/results/:runId`: public model report with a use-assessment statement, automated metric bars, detector-warning bars, a response-time line graph, and all eight research metric families. Profiles are linked to the current run, its evaluations, or its dataset version. Undefined scalar values remain unavailable.
- `/workspace`: login/register screen, then a separate dashboard with metrics, explanations, current assessment, and saved run history.
- `/import`: login/register screen, then connection settings entered manually or loaded from a local JSON file. The Verify & save action checks an installed Ollama model or lists models on a compatible endpoint and persists the connection in the model library. API keys stay in memory and are excluded from persistence. Remote connections remain subject to the backend opt-in.
- Other research routes require login in the application entry point.

The default `apps.api.main:app` enables account protection. `create_app(require_auth=False)` remains available for existing programmatic integrations and tests; callers deploying the factory must explicitly use `require_auth=True`.

## Accounts

Accounts and expiring sessions are stored in the application's database. Passwords use PBKDF2-HMAC-SHA256 with independent salts and 310,000 iterations. Session tokens are random, stored as hashes, and sent in HttpOnly, SameSite=Strict cookies, with Secure enabled on HTTPS. Sessions expire after eight hours. Login and registration have a per-client attempt limit. Logout revokes the stored session. Authenticated users currently share the local research workspace; per-user private datasets and run ownership are not implemented.

The sign-in screen also offers a sample account through `/auth/sample`. This route accepts loopback requests only, creates the reserved sample account with an unknown random password, and establishes a normal expiring session. The sample account opens the same shared local research workspace. No hard-coded public password is introduced.

## Result colors

- Orange is the single accent for actions, active states, icons, chart marks, and highlighted measurements.
- Backgrounds and surfaces use black or neutral charcoal; supporting text uses white and gray.
- Written labels distinguish completed checks, failures, missing evidence, and review requirements.

The warning threshold is a display rule, not an empirically validated selection cutoff. Current evidence does not justify a final safe/unsafe recommendation, so overall suitability stays unestablished until validated outcomes support it.

## Animation

The landing-page orbital visualization illustrates the evaluation pipeline and is labeled as an illustration. Benchmark progress uses actual job polling and actual completion counts. Reduced-motion settings are respected. Source attribution for the adapted React Bits component is in `frontend/THIRD_PARTY_NOTICES.md`.

## Local verification

During the redesign, a public one-case Gemma test completed and its report was accessible without a login. The saved run identifier is `9db11cb5ed5f4274b197801c19281ad5`; it is engineering test activity, not a controlled model comparison.
