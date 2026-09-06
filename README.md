# Battery MRI

Battery MRI designs an electrical question for a virtual battery. PyBaMM predicts two physical hypotheses, a bounded optimizer selects an informative current waveform, and synthetic measurements update a Bayesian belief. The 83-second guided presentation runs automatically with readable captions and labeled scientific plots.

## Open it

Double-click **Launch Battery MRI.command** in this folder, then click **Start demo** in the browser. Keep the launcher terminal open. Control-C stops the server. The launcher prefers http://127.0.0.1:8765 and selects another available port when necessary. The actual URL is printed and recorded in `backend/data/last_launch.json`.

Dependencies and the production interface are already installed on this Mac. Subsequent launches serve saved computations locally, with no cloud API, external font, CDN or API key. First-time setup on another machine needs Python 3.10+ and Node 20.19+ (or 22.12+). Python 3.10 is used here because it is the installed version; current PyBaMM 26.8.0.0 supports it. Node is unnecessary once the frontend has been built.

## Thirty-second explanation

An ordinary fixed probe can produce nearly overlapping voltage predictions for distinct battery states. Instead of only analyzing that measurement, this prototype searches charge/discharge patterns that make the hypotheses easier to distinguish. It measures a simulated hidden cell, updates the probabilities and repeats the design using the new prior. Nothing is diagnosed from real hardware.

## Architecture

```
React guided timeline / optional live lab
                ↓ localhost HTTP
FastAPI — cached scientific data / single-worker live jobs
                ↓
SciPy differential evolution ↔ PyBaMM SPMe
                ↓
Expected information gain → synthetic voltage → Bayesian posterior
                                                   ↓
                                           next search prior
```

The frontend production build is served by the same FastAPI process as the API. Scientific code is in `backend/science`; presentation is in `frontend/src`. The seven scenes provide captions, pause/resume, next, replay, skip, glossary and assumptions drawers. Lab Mode permits bounded live changes and plays the computed experiment through the same presentation.

## Physical model and hypotheses

PyBaMM **26.8.0.0**, lithium-ion **SPMe**, **Chen2020**, lumped thermal, constant SEI and distributed SEI film resistance. IDAKLUSolver uses rtol 1e-6 / atol 1e-7. Electrode meshes have 12/8/12 through-thickness points and 16 radial points per electrode. All required parameter names are checked against installed PyBaMM.

- A: SEI resistivity 600,000 Ω·m (3× the 200,000 baseline), initial SEI thickness 5 nm, negative particle diffusivity 3.3e-14 m²/s.
- B: baseline SEI resistivity, negative particle diffusivity 2.97e-14 m²/s (0.9× baseline).
- Both: 5 Ah capacity, 55% initial SOC, 298.15 K initial/ambient temperature.
- Constant SEI means no growth during the experiment. This is not a direct measurement of film thickness, nor proof that an arbitrary abnormal battery has one of these two causes.

The real SEI model solves successfully; a series-resistance proxy was therefore unnecessary. See [PyBaMM model options](https://docs.pybamm.org/en/stable/source/api/models/base_models/base_battery_model.html) and [PyBaMM documentation](https://docs.pybamm.org/en/stable/).

## Probe design, calibration and constraints

Six equal-duration piecewise-constant segments, 120 seconds total by default. Positive C-rate means discharge; negative means charge. The fixed, deliberately weak control is `[0.15, 0, -0.15, 0, 0.15, 0] C`, not an industry-standard HPPC protocol. Thus the comparison demonstrates input design relative to this control, not superiority to established diagnostic methods.

`calibrate.py` scans 12 combinations of modest SEI and diffusion multipliers. `backend/data/calibration.json` records the complete scan and candidate witness; the selected default is encoded in `simulator.py` and the cache config. The target was low baseline EIG and moderate optimized EIG to leave room for a second measurement. Measurement seed 42 was selected from four documented trial seeds (2026, 42, 17, 123) for an interpretable two-step story. This is a curated demonstration, not a statistical performance evaluation.

Each candidate must satisfy ±2C, voltage 2.5–4.2 V, SOC 20–80%, temperature ≤313.15 K, and total duration 60–180 seconds. Solver cutoff events and finite sampled output checks reject invalid candidates. This is a numerical screening check at solver/output resolution, not a continuous-time safety certificate. Bounds are illustrative and apply only to this virtual model.

Differential evolution optimizes six amplitudes with popsize 4, seven generations, deterministic seeds 731 and 732, no polishing. Saved histories and top-eight candidates are real evaluations. Model setup is reused. Guided playback does not run this search live.

## Objective and inference

Observations are voltage sampled every two seconds at mid-bin times, avoiding ideal current discontinuities. Independent Gaussian noise has σ = 0.020 V. This is an illustrative effective uncertainty assumption, not a specification for a particular sensor. Thermal output is used for constraint checks, not inference.

The binary equal-covariance Gaussian log-likelihood ratio has a one-dimensional normal distribution. We compute expected posterior entropy by 32-point Gauss-Hermite quadrature and subtract it from prior Shannon entropy (base 2). Accordingly, displayed scores really are expected information gain in bits. Fixed observation counts prevent longer default probes winning merely by accumulating more samples.

Inference uses `log L = -0.5 Σ ((y−V_H)/σ)^2`, prior log weights and log-sum-exp normalization. Every displayed posterior and sequential update is computed from observations. The default hidden truth is A, revealed only on request. The cached result contains no fabricated percentages.

Each probe assumes a controlled reset to the same SOC and thermal equilibrium. A real protocol would require reconditioning; continuous electrochemical state is not carried from probe 1 to probe 2. This assumption is visible in the demo and model drawer.

**Important adaptation limit:** with two fixed hypotheses and equal Gaussian covariance, EIG is monotonic in Mahalanobis separation. Updating the prior changes expected information but need not change the globally optimal waveform. Our independently seeded bounded searches return different probes; this is not evidence that the global optimum became uniquely cell-specific. A richer parameter ensemble would be required to demonstrate that stronger claim. The posterior-to-prior conditioning is real.

## Recompute and test

Double-click `Recompute Scientific Demo.command`, or:

```sh
.venv/bin/python scripts/precompute_demo.py
.venv/bin/python scripts/validate_science.py
cd frontend
npm ci
npm run build
npx playwright test
```

The browser test expects the launcher running on port 8765. It blocks nonlocal network requests, checks the complete automatic timeline, pause/resume, skip, replay, math drawer, charts and responsive widths. Screenshots are saved in `Reports/`.

Manual server: `.venv/bin/python scripts/launch.py`. Set `BATTERY_MRI_NO_BROWSER=1` for automated testing. Live requests: `POST /api/lab/optimize`, poll `GET /api/lab/jobs/{id}`. API documentation: `/docs`. Only one live job runs at once; invalid inputs receive typed validation errors.

Saved scientific results: `backend/data/demo.json`. `/api/demo` omits ground truth until `/api/demo/result` is requested. Health reports PyBaMM version, cache availability/version and frontend availability. Version-mismatched saved data retains its explicit original version and should be recomputed before scientific comparison.

## Limits

This prototype demonstrates simulation-driven optimal experiment design. Real diagnostic use would require calibrated cell-specific models, instrumentation error models, safety review, cycler integration, and physical validation.

No real cell, hardware driver, clinical MRI, certified diagnostic, external affiliation, proprietary branding, LLM or remote API is involved. Conceptual ion animation is not a sampled internal model field. The binary hypothesis set excludes alternative mechanisms and model discrepancy. Confidence is conditional on that restrictive set. No DFN validation, parameter-identifiability estimate or hardware safety claim is made.

## Verification status on this Mac

Six scientific/API tests and two DOM interface tests pass. A fresh two-probe Lab Mode job and actual launcher HTTP/asset checks pass. The scientific cache was recomputed twice with identical scores/posteriors. Default assumptions are versioned in `backend/data/default_scenario.json`.

**Rendered browser acceptance remains unverified:** this managed execution session denies Chromium's macOS Mach-port registration (`Permission denied 1100`). macOS Launch Services also rejected automatic browser opening here (`-10661`). These are recorded environmental blockers; no screenshot or successful browser test is claimed. The executable launcher prints the local address if automatic opening fails. The DOM tests exercise the full automatic sequence with a mocked plot renderer and do not substitute for layout/visual inspection. `Reports/build_manifest.json` records the distinction.
