# BATTERY MRI — CODEX MASTER BUILD BRIEF

## Purpose

Build a polished, local, one-click web application called **Battery MRI** (working title) that demonstrates **closed-loop active electrochemical interrogation** of a lithium-ion cell.

The app should show, in a visually compelling but scientifically honest way, how software can use a physics model (PyBaMM) plus numerical optimization to design an electrical current waveform that makes two competing internal battery hypotheses respond differently. The app then runs that probe against a simulated “mystery” cell, updates the probability of each hypothesis from the observed response, and optionally designs a second probe based on what it just learned.

This is an independent technical prototype for an interview/demo. Do **not** imply affiliation with Ohm, do not use Ohm logos or proprietary assets, and do not claim this is a validated diagnostic device. The goal is to demonstrate a plausible new software capability that could complement an engineering co-scientist.

---

# 1. BUILD THIS END TO END — DO NOT STOP AT A SKELETON

You are responsible for implementing the complete working project, running it, fixing errors, testing it, and leaving a one-click local launcher on macOS.

Default project location:

`~/Desktop/BatteryMRI`

Do not stop after generating boilerplate. Do not merely write a README. Do not ask for permission between normal implementation steps. Make reasonable engineering choices when something is underspecified and document those choices.

At completion, the user should be able to double-click **Launch Battery MRI.command** from the project folder and have the app open in a browser with the guided demo ready to run.

---

# 2. PRODUCT IN ONE SENTENCE

**Battery MRI actively designs the electrical “question” to ask a battery so that competing physical explanations become easier to distinguish.**

The key concept is not “an LLM analyzes battery data.” The key concept is **optimal input / experiment design**:

1. Define two physically different hypotheses about the cell.
2. Simulate how each would respond to candidate current waveforms.
3. Search for a safe waveform that maximizes how differently the hypotheses respond.
4. Apply that waveform to a simulated hidden cell.
5. Use the noisy response to update the probability of each hypothesis.
6. If uncertainty remains, design the next waveform based on the updated belief.

The LLM, if present at all, is an optional orchestration/explanation layer. The scientific result must come from numerical simulation and optimization, not from fabricated prose.

---

# 3. IMPORTANT SCIENTIFIC POSITIONING

The app is a **simulation-based proof of concept**, not a medical MRI and not a certified battery diagnostic.

Use these labels consistently:

- “virtual cell” or “simulated cell” for PyBaMM outputs
- “probe” for the designed current waveform
- “hypothesis” for a candidate physical mechanism or parameter state
- “posterior probability” for updated beliefs after observing synthetic measurements
- “information score” only when the score is actually computed
- “simulated result” whenever the UI could otherwise be mistaken for physical lab data

Never claim that the app directly measures SEI thickness, diffusion coefficients, lithium plating, or any hidden variable from a real battery unless the mathematics and measurement model genuinely support that statement.

Never imply that a PyBaMM simulation replaces physical validation.

---

# 4. TECH STACK

Use a local web architecture, not Unreal Engine.

## Backend

- Python 3.11+ if available
- FastAPI
- Uvicorn
- PyBaMM
- NumPy
- SciPy
- Pandas only if genuinely useful
- Pydantic
- joblib or Python multiprocessing only if it improves candidate simulation performance without making the app fragile

## Frontend

- React
- TypeScript
- Vite
- Plotly.js for scientific time-series plots OR a comparable browser charting library if there is a strong implementation reason
- SVG/CSS for the battery cross-section and explanatory animations
- Framer Motion is allowed for UI transitions, but do not make the app dependent on animation libraries if they cause instability

## Final serving model

During development, separate Vite/FastAPI servers are fine. For the final one-click demo:

1. Build the frontend into static assets.
2. Have FastAPI serve the built frontend and the API from one local port.
3. The launcher starts one backend process and opens the browser automatically.

Core guided-demo functionality must require **no cloud API and no internet connection** once dependencies are installed.

---

# 5. REPOSITORY / FOLDER STRUCTURE

Use a clean structure similar to:

```text
BatteryMRI/
  README.md
  .gitignore
  requirements.txt
  pyproject.toml                 # optional if useful
  Launch Battery MRI.command
  Setup Battery MRI.command      # optional separate setup helper
  scripts/
    precompute_demo.py
    validate_science.py
    build_and_launch.sh
  backend/
    __init__.py
    main.py
    config.py
    api/
      routes_demo.py
      routes_lab.py
    science/
      pybamm_model.py
      hypotheses.py
      waveform.py
      simulator.py
      objective.py
      optimizer.py
      inference.py
      adaptive.py
      safety.py
      cache.py
    data/
      demo_cache/
      metadata/
    tests/
      test_waveform.py
      test_inference.py
      test_optimizer.py
      test_api.py
  frontend/
    package.json
    vite.config.ts
    tsconfig.json
    src/
      main.tsx
      App.tsx
      api/
      components/
      demo/
      lab/
      charts/
      visuals/
      styles/
    public/
```

You may improve the structure, but keep scientific code separate from UI code.

Initialize git if git is available. Do not commit secrets, virtual environments, node_modules, caches, or generated build artifacts unless intentionally required.

---

# 6. DEFAULT SCIENTIFIC DEMO SCENARIO

The default guided demo should answer a very understandable question:

> **“Is this virtual cell’s abnormal response better explained by a resistive/SEI-related aging state or by slower negative-electrode solid diffusion?”**

The exact physical parameterization must be implemented honestly in PyBaMM.

## Baseline model

Prefer:

- PyBaMM lithium-ion **SPMe** for speed and enough electrochemical richness
- `Chen2020` parameter set if available in the installed PyBaMM version
- lumped thermal model if stable and fast enough

Use DFN only for an optional “high fidelity” validation mode or cached comparison. The guided demo should remain fast and reliable.

## Hypothesis A — resistive / SEI-related aging

Preferred implementation, if compatible with the selected PyBaMM model/version:

- enable an SEI model supported by current PyBaMM
- perturb a real SEI-related parameter such as SEI resistivity and/or initial SEI thickness in a scientifically coherent way

If the selected fast model cannot robustly support that configuration, use a clearly labeled **resistive-aging proxy** rather than pretending the mechanism is full SEI growth. The UI must then say “resistive-aging proxy,” not “SEI thickness measured.”

## Hypothesis B — diffusion-limited aging

Perturb a real negative-electrode solid-diffusion parameter, preferably:

- reduce `Negative particle diffusivity [m2.s-1]`

Do not hardcode parameter names without checking they exist in the installed parameter set. The backend should validate all required parameters at startup and produce a useful error if PyBaMM API/parameter naming has changed.

## Calibration requirement

Tune the severity of A and B so that a simple fixed baseline probe produces **similar-looking voltage responses**, while the optimized probe produces meaningfully greater separation.

This is central to the story. Do not hand-wave it.

Create a small calibration script that searches reasonable perturbation multipliers and selects a pair that satisfies something like:

- baseline probe: low-to-moderate separation
- optimized probe: substantially larger separation
- both remain inside voltage/temperature/SOC safety bounds

Store the chosen default configuration in a versioned JSON/YAML config file.

---

# 7. CURRENT WAVEFORM REPRESENTATION

Represent a candidate probe as a bounded piecewise-constant current sequence.

A good MVP representation is 6–8 segments. Each segment has:

- signed C-rate or current amplitude
- duration in seconds

Example only:

```text
+0.8C for 12 s
rest for 18 s
-1.5C for 8 s
rest for 12 s
+1.2C for 10 s
rest for 20 s
```

Do not use that exact sequence unless the optimizer chooses something similar.

Keep the search dimension tractable. For the first version, one of these is acceptable:

### Option A — fixed durations, optimize amplitudes

Fastest and most robust.

### Option B — optimize amplitudes plus durations from a bounded discrete set

More expressive but more expensive.

### Option C — optimize a smaller set of waveform primitives

For example pulse amplitude, pulse duration, rest duration, second pulse amplitude, second pulse duration.

Choose the simplest representation that creates a real, repeatable improvement over the baseline probe.

---

# 8. SAFETY / PHYSICAL CONSTRAINTS FOR THE VIRTUAL PROBE

The optimizer must not be rewarded for choosing absurd inputs.

Create explicit constraints for the default scenario. Use conservative illustrative bounds and make them visible in the UI’s “Assumptions” drawer.

Suggested starting constraints, to be validated against the chosen parameter set:

- maximum absolute C-rate: 2C for the default guided demo
- cell voltage: stay inside the parameter set’s configured lower and upper cutoffs
- initial SOC: around 50–60% for the default scenario
- SOC window: keep the short probe comfortably away from 0% and 100%
- temperature: initial 25 °C; if thermal model is enabled, reject candidates that exceed a conservative upper temperature threshold
- total probe duration: target roughly 60–180 seconds for a visually understandable demo

If current direction sign conventions differ in PyBaMM, encapsulate them in one module and test them. The UI should use plain “charge” and “discharge” labels, not expose sign-convention confusion.

Invalid candidates should be penalized or rejected deterministically.

---

# 9. THE OPTIMIZATION OBJECTIVE

This is the scientific heart of the project.

For every candidate waveform:

1. Simulate the waveform under Hypothesis A.
2. Simulate the same waveform under Hypothesis B.
3. Put both outputs on the same time grid.
4. Quantify how distinguishable the predicted measurements are under an explicit noise model.
5. Apply safety and duration penalties.
6. Return a scalar objective to the optimizer.

## MVP objective

Use a physically interpretable separation metric based primarily on terminal voltage and optionally temperature:

```text
separation = sum_t ((V_A(t) - V_B(t)) / sigma_V)^2
```

If temperature is modeled and informative:

```text
+ w_T * sum_t ((T_A(t) - T_B(t)) / sigma_T)^2
```

where `sigma_V` and `sigma_T` are explicit assumed sensor-noise values.

Normalize by number of samples so longer waveforms do not win purely by having more points, unless duration is intentionally part of the objective.

Add penalties for:

- voltage-limit violations
- temperature-limit violations
- SOC-limit violations
- excessive total duration
- excessively aggressive switching if needed

## Preferred advanced objective

If computationally practical, implement an **expected information gain** or hypothesis-discrimination objective rather than only curve distance.

A defensible implementation is:

- prior probabilities over hypotheses
- Gaussian measurement noise model
- synthetic measurement draws under each hypothesis
- Bayesian posterior update for each draw
- expected reduction in Shannon entropy, in bits

```text
EIG = H(prior) - E_y[H(posterior | y, waveform)]
```

Use Monte Carlo with a bounded number of noise draws for cached demo optimization. Keep the simple separation metric available as a fast mode.

Do not display “bits” unless the code actually computes Shannon information in base 2.

## Optional parameter-identifiability view

If stable, add finite-difference or PyBaMM sensitivity calculations and compute a Fisher-information-style metric for the selected uncertain parameters. This should be a secondary advanced panel, not a blocker for the core demo.

---

# 10. OPTIMIZER

Start with `scipy.optimize.differential_evolution` or another robust bounded black-box optimizer.

Why:

- the PyBaMM objective is not guaranteed smooth
- candidate simulations can fail at boundaries
- bounded global search is easy to reason about

Requirements:

- deterministic seed for guided-demo precomputation
- bounded iterations/population
- progress callback that records best score over generations
- preserve the top N candidate waveforms and scores for animation
- gracefully catch failed PyBaMM simulations and return a large penalty

Do not make the guided demo wait through thousands of live simulations. Precompute and cache the winning search trajectory.

The app can visually replay real saved optimizer history quickly.

---

# 11. BASELINE PROBE

Create a simple fixed probe that acts as the control condition.

It should be a reasonable, non-optimized sequence such as a symmetric pulse/rest pattern, chosen in code and documented.

The demo must compare:

- fixed baseline probe
- optimized Battery MRI probe

Show:

- predicted voltage-response separation
- information score
- probe duration

Do not claim the baseline is an industry-standard HPPC test unless it actually implements and documents a recognized protocol. Safer wording: **“fixed baseline probe.”**

---

# 12. VIRTUAL MYSTERY CELL

For the guided demo, create a hidden truth selected deterministically from one of the two hypotheses.

Recommended default:

- hidden truth = Hypothesis A
- seed fixed for reproducibility

Generate synthetic measurements by:

1. simulating the hidden model under the chosen waveform
2. sampling the solution on a fixed time grid
3. adding Gaussian voltage noise (and temperature noise if used)

Keep the noise realistic enough to make inference nontrivial but not so large that the story becomes unstable.

The frontend should never reveal the hidden truth until the user reaches a “Reveal Ground Truth” optional panel after the diagnosis.

---

# 13. BAYESIAN POSTERIOR UPDATE

Implement actual likelihood-based inference.

For each hypothesis H and observed measurement vector y:

- obtain predicted measurement vector `mu_H`
- assume an explicit Gaussian noise covariance or independent noise standard deviation
- compute log likelihood
- combine with prior log probability
- normalize with log-sum-exp

Output:

```json
{
  "prior": {"resistive": 0.5, "diffusion": 0.5},
  "posterior": {"resistive": 0.88, "diffusion": 0.12},
  "log_likelihoods": {...}
}
```

The percentages in the UI must come from this computation.

Never hardcode “89%” just because it looks good. Tune scenario/noise if necessary, then cache the real result.

---

# 14. CLOSED-LOOP SECOND PROBE

The second probe is the feature that makes the demo feel genuinely adaptive.

After Probe 1:

1. Take the posterior as the new prior.
2. Re-run the probe-design objective with the updated prior.
3. Design Probe 2 to maximize the remaining expected information.
4. Simulate Probe 2 on the same hidden virtual cell.
5. Update the posterior again.

If the posterior after Probe 1 is already above a configurable confidence threshold (for example 95%), the system may show:

> “Confidence threshold reached; a second probe is not necessary.”

For the guided demo, tune the default scenario so Probe 1 leaves enough uncertainty that designing Probe 2 is visually useful, and Probe 2 materially increases confidence.

The second waveform should visibly differ from the first. If it does not, investigate the objective or scenario rather than faking a different waveform.

---

# 15. PRECOMPUTE AND CACHE THE GUIDED DEMO

Reliability during an interview is more important than proving the laptop can optimize in real time.

Create:

`scripts/precompute_demo.py`

It should generate and save:

- baseline probe waveform
- baseline predictions under A and B
- baseline score
- optimizer search history for Probe 1
- best Probe 1 waveform
- A/B predictions under Probe 1
- noisy hidden-cell observation for Probe 1
- posterior after Probe 1
- optimizer search history for Probe 2
- best Probe 2 waveform
- predictions under Probe 2
- noisy hidden-cell observation for Probe 2
- posterior after Probe 2
- all assumption/config metadata
- PyBaMM version
- random seeds

Use compact JSON for frontend-friendly arrays or `.npz` plus JSON metadata. Prefer something easy to inspect and version.

At startup, if a valid cache exists, load instantly.

Provide a “Recompute Scientific Demo” developer command, but do not recompute by default during the presentation.

---

# 16. GUIDED DEMO — EXACT STORYBOARD

The app opens to a clean landing view with one primary button:

## `RUN BATTERY MRI`

The user should be able to click it once and watch the complete story unfold automatically in roughly 60–90 seconds.

Include small controls:

- Pause / Resume
- Next
- Replay
- Skip to Result
- “Show the Math” toggle or drawer

Do not make the demo depend on hover.

## Scene 1 — The Mystery

Visual:

- elegant schematic battery cross-section
- subtle ion motion or concentration-gradient animation labeled **conceptual visualization**
- a card: “Virtual NMC/graphite cell”

Text:

> “The cell shows an abnormal transient response. Two internal explanations remain plausible.”

Show two hypotheses at 50/50:

- Resistive / SEI-related aging
- Slower negative-electrode diffusion

Do not claim normal capacity fade alone uniquely implies these two mechanisms.

## Scene 2 — Why passive observation is not enough

Show the fixed baseline probe waveform and the two predicted voltage responses.

The curves should overlap substantially.

Display a real computed statement like:

> “Under this fixed probe, the two hypotheses generate very similar terminal-voltage signatures.”

Show the baseline information/separation score.

## Scene 3 — Design the Probe

Transition to:

### `DESIGN INFORMATION-MAXIMIZING PROBE`

Replay saved optimizer progress.

Show a compact evolving panel:

```text
Generation 1      score 0.xx
Generation 6      score 0.xx
Generation 18     score x.xx
...
```

Animate candidate current waveforms changing as the best score improves.

Do not pretend these are live calculations if they are cached. Label unobtrusively:

> “Replaying precomputed optimization”

At the end:

### `OPTIMAL SAFE PROBE FOUND`

## Scene 4 — Make the physics separate

Show the optimized current waveform prominently.

Below it, animate the two predicted voltage responses.

Highlight the time regions where the curves separate the most.

Add a small explanation:

> “The optimizer chose a waveform that amplifies the difference between the two virtual physical states while staying within the configured operating constraints.”

## Scene 5 — Interrogate the Mystery Cell

Hide hypothesis labels on the measurement plot.

Show the optimized current waveform being “applied” to the virtual cell.

Stream the cached noisy voltage samples across the plot in real time.

Simultaneously animate posterior bars from 50/50 to the real posterior from the inference engine.

End with something like:

> “Probe 1 favors resistive/SEI-related aging, but uncertainty remains.”

Use whatever real percentage the computation produces.

## Scene 6 — The experiment adapts

Display:

> “Battery MRI now redesigns the next probe using what it just learned.”

Replay the second optimizer search briefly.

Reveal a visibly different Probe 2.

Run the second virtual measurement and update the posterior again.

## Scene 7 — Result and architecture

Show final posterior and ground-truth reveal option.

Then show a simple system diagram:

```text
Engineering question
       ↓
Hypothesis set
       ↓
Battery MRI optimizer
       ↓
PyBaMM virtual physics
       ↓
Information-maximizing current probe
       ↓
Existing battery cycler / virtual cell
       ↓
Voltage / temperature response
       ↓
Bayesian update
       ↺ design next probe if needed
```

Final headline:

> **From passive analysis to active interrogation of the physical system.**

Final disclaimer:

> “Simulation-based proof of concept. A real deployment would require model calibration, hardware integration, safety validation, and physical-cell testing.”

---

# 16A. GUIDED-DEMO SUBTITLES, TECHNICAL CALLOUTS, AND ANIMATION LABELS — REQUIRED

The Guided Demo must teach the science **while it is moving**. Treat the 60–90 second sequence like a high-end technical explainer, not like a silent dashboard. A viewer should understand what PyBaMM, waveform optimization, hypothesis separation, Bayesian updating, and closed-loop adaptation mean without the presenter needing to stop and explain every chart.

## Persistent subtitle system

Create a synchronized subtitle/caption band near the bottom of the main demo area. It should be visually integrated into the product and should not look like browser closed captions.

Requirements:

- **Subtitles are ON by default** in Guided Demo.
- Each scene gets 1–3 short caption beats timed to the animation.
- Each caption should explain one technical idea in plain English while preserving the correct technical term.
- Prefer two layers when useful:
  - **Plain-English line:** what is happening and why it matters.
  - **Technical tag:** concise term such as `PyBaMM · SPMe physics model`, `Expected information gain`, or `Bayesian posterior update`.
- Keep each caption on screen long enough to read comfortably.
- Never cover the main scientific plot.
- Captions must update when the user presses Next, Replay, Pause, or Skip.
- Add a small `Subtitles` toggle, but keep it enabled for the default interview experience.
- Do not rely on narration or audio. The visual sequence plus captions must stand alone.

## Direct labels on animations and plots

Do not make the user decode unlabeled motion. Important animated objects must have visible labels **attached to or directly underneath them**. Avoid hover-only explanations.

Required examples:

- Battery cross-section: label **Negative electrode**, **Separator**, **Positive electrode**, and **Li+ movement (conceptual)**.
- PyBaMM stage: show a visible badge/label such as **PyBaMM physics simulation** and a small note: **predicts the virtual cell response to a proposed current input**.
- Current-waveform chart: label the y-axis **Current / C-rate**, x-axis **Time**, and annotate waveform segments as **charge**, **rest**, or **discharge**.
- Optimizer animation: label **Candidate probe**, **Information score**, **Generation / iteration**, and **Best so far**. If replaying cached data, visibly label **replaying real precomputed optimization history**.
- Hypothesis-response chart: label the curves directly near their endpoints as **Resistive / SEI-related hypothesis** and **Diffusion-limited hypothesis**, not only in a detached legend.
- Highlight the region of largest curve separation with an annotation such as **Most diagnostic part of the response**.
- Mystery-cell measurement: label **Observed synthetic measurement** and keep predicted A/B signatures visible but visually secondary.
- Probability animation: label **Prior belief** before the probe and **Posterior belief after measurement** after the Bayesian update.
- Closed-loop transition: visually label the arrow from measurement back to optimization as **Use new evidence to redesign the next probe**.
- Every schematic or animated illustration that is not a direct model output must be labeled **conceptual visualization**.

## Required first-use definitions

The first time each concept appears, display a short definition near the relevant animation or in the subtitle band. Use wording close to the following:

- **Battery MRI:** “Software that designs the electrical question to ask a battery so competing physical explanations become easier to distinguish.”
- **PyBaMM:** “An open-source battery-physics simulator. Here it predicts how each virtual battery hypothesis responds to the same current waveform.”
- **SPMe:** “A reduced electrochemical lithium-ion model that is fast enough for repeated optimization while retaining physically meaningful battery dynamics.”
- **Waveform / probe:** “The time-varying charge, discharge, and rest pattern we apply to the virtual cell.”
- **Waveform optimization:** “Search many safe current patterns and keep the one expected to separate the hypotheses most clearly.”
- **SEI / resistive aging:** “A resistive-aging state associated with changes at the electrode interface; in this demo use the exact implemented PyBaMM parameterization or label it as a proxy.”
- **Diffusion limitation:** “Lithium moves more slowly through active-material particles, changing the cell’s transient voltage response.”
- **Information gain:** “How much the proposed measurement is expected to reduce uncertainty between the competing hypotheses.” Only use this label if the implementation genuinely computes information gain.
- **Bayesian update:** “Combine what we believed before the measurement with how well each hypothesis predicts the observed response.”
- **Posterior probability:** “The updated probability assigned to each hypothesis after the measurement.”
- **Closed-loop / adaptive experiment:** “The next probe is redesigned using what the previous measurement just taught us.”

If the implementation uses the simpler curve-separation objective rather than expected information gain, replace `Information gain` language everywhere with **Discrimination score** or **Predicted response separation**. Never use a more sophisticated term than the code supports.

## Scene-by-scene subtitle script

Use these as the default narrative beats. Codex may tighten the wording for layout, but preserve the technical meaning.

### Scene 1 — The Mystery

1. **“The same abnormal battery response can be consistent with more than one internal physical explanation.”**
   Technical tag: `Hypothesis ambiguity`
2. **“Our two virtual hypotheses are resistive / SEI-related aging and slower negative-electrode diffusion.”**
   Technical tag: `Two physically distinct parameter states`

### Scene 2 — Why passive observation is not enough

1. **“PyBaMM predicts how both hypotheses respond to the same ordinary fixed probe.”**
   Technical tag: `PyBaMM · SPMe simulation`
2. **“The voltage signatures overlap, so this measurement does not contain much information for telling the mechanisms apart.”**
   Technical tag: `Low identifiability / low discrimination`

### Scene 3 — Design the probe

1. **“Instead of only analyzing the data we already have, Battery MRI chooses what electrical measurement should exist next.”**
   Technical tag: `Optimal experiment / input design`
2. **“The optimizer tests many safe charge–rest–discharge waveforms in the physics model and scores how well each separates the hypotheses.”**
   Technical tag: `Bounded numerical optimization + PyBaMM`
3. **“The best waveform becomes the next question we ask the battery.”**
   Technical tag: `Information-maximizing probe` or `Maximum-discrimination probe`, matching the implemented objective

### Scene 4 — Make the physics separate

1. **“Under the optimized probe, the two physical hypotheses predict measurably different voltage trajectories.”**
   Technical tag: `Hypothesis response separation`
2. **“This highlighted interval is where the measurement is most diagnostic.”**
   Technical tag: `Maximum predicted separation`

### Scene 5 — Interrogate the mystery cell

1. **“We now apply the optimized probe to a hidden virtual cell and add an explicit measurement-noise model.”**
   Technical tag: `Synthetic observation`
2. **“As voltage samples arrive, Bayesian inference asks which hypothesis better predicted what we actually observed.”**
   Technical tag: `Likelihood → posterior update`
3. **“The probability shift is computed from the model predictions and noise assumptions, not written by the LLM.”**
   Technical tag: `Numerical inference`

### Scene 6 — The experiment adapts

1. **“The first measurement changed what we know, so the most useful next experiment can change too.”**
   Technical tag: `Closed-loop adaptive design`
2. **“Probe 2 is optimized using the posterior from Probe 1 as the new prior.”**
   Technical tag: `Posterior₁ → Prior₂`
3. **“The experiment is now adapting to this specific cell rather than replaying one fixed diagnostic protocol.”**
   Technical tag: `Active interrogation`

### Scene 7 — Result and architecture

1. **“Battery MRI is a software layer: physics simulation proposes the probe, existing cycler hardware would apply it, and the measured response closes the loop.”**
   Technical tag: `Software-defined experiment`
2. **“The core shift is from passive analysis of existing measurements to actively designing the next measurement.”**
   Technical tag: `Passive analysis → active interrogation`
3. Keep the simulation disclaimer visible before the sequence ends.

## Technical explainer overlays

Add small, tasteful `What is this?` or info callouts for advanced viewers. These should open short inline explanations without leaving the demo. At minimum support:

- PyBaMM
- SPMe
- C-rate
- SEI / resistive-aging proxy
- solid-state diffusion
- waveform optimization
- expected information gain or discrimination score
- Bayesian posterior
- measurement noise
- closed-loop experiment design

These overlays are secondary to the always-visible subtitles and labels. The default 60–90 second flow should remain clean and understandable without opening them.

## Visual hierarchy rule

Every technical scene should answer three questions on screen at the same time:

1. **What am I looking at?** — direct labels on the object/plot.
2. **What is the software doing?** — synchronized subtitle.
3. **Why does it matter?** — one concise consequence or comparison.

If an animation looks impressive but a technical viewer cannot answer all three within a few seconds, redesign it.

---

# 17. VISUAL DESIGN

The app should look like a serious engineering product, not a hackathon dashboard.

Style goals:

- dark or deep-neutral technical canvas
- crisp typography
- restrained accent colors
- one persistent color for Hypothesis A and another for Hypothesis B
- clear grid and spacing
- subtle motion
- no neon cyberpunk overload
- no fake 3D photorealism
- no unnecessary glassmorphism

The central scientific plots should dominate.

Use animation to explain causality, not as decoration.

## Battery visual

Use an SVG schematic of a pouch or cylindrical cell cross-section. It can show:

- negative electrode
- separator
- positive electrode
- conceptual lithium-ion movement

Label it “conceptual schematic.”

Do not imply that SVG particle motion is direct PyBaMM state output unless it is actually driven by a model variable.

## Charts

Required charts:

1. current waveform vs time
2. voltage response A vs B
3. observed noisy voltage vs predictions
4. posterior probabilities over time or by probe stage
5. optimizer best-score history

Optional:

- temperature response
- parameter sensitivity panel
- SOC trajectory

---

# 18. TWO MODES

## Mode A — Guided Demo

This is the default and must be flawless.

- one click
- deterministic
- cached scientific results
- automatic narrative
- no internet
- no API keys

## Mode B — Lab Mode

After the guided demo works, add an interactive mode.

Controls can include:

- initial SOC
- temperature
- maximum C-rate
- voltage-noise level
- hypothesis severity multipliers
- probe duration budget
- optimizer effort: Fast / Detailed

Button:

### `RECOMPUTE PROBE`

This can call the live backend optimizer.

Show a clear loading state and progress.

If live optimization takes too long, allow a Fast mode using a smaller candidate set or surrogate score.

Never let Lab Mode complexity compromise the Guided Demo.

---

# 19. OPTIONAL NATURAL-LANGUAGE AGENT LAYER

Do not make this a dependency.

If an API key is present, an optional text box may allow:

> “Design a probe to distinguish resistive aging from diffusion limitation.”

The LLM may map natural language into one of the supported hypothesis templates and explain the result.

However:

- do not let the LLM invent unsupported mechanisms or parameter names
- validate its output against a fixed schema
- only execute recognized hypothesis templates
- the optimization result still comes from PyBaMM/SciPy
- the Guided Demo must work without any LLM call

If no API key exists, hide or disable this feature gracefully.

---

# 20. FASTAPI API DESIGN

Implement clean endpoints. Suggested shape:

```text
GET  /api/health
GET  /api/demo/manifest
GET  /api/demo/baseline
GET  /api/demo/probe/1
GET  /api/demo/probe/2
GET  /api/demo/result
POST /api/lab/simulate
POST /api/lab/optimize
POST /api/lab/infer
```

The exact API can differ, but keep it typed and documented.

`/api/health` should report:

- app status
- PyBaMM installed version
- whether demo cache is valid
- whether frontend build exists

Use structured errors, not raw stack traces in the browser.

---

# 21. PERFORMANCE STRATEGY

PyBaMM simulations can become expensive. Optimize for reliability:

1. Use SPMe for the core search.
2. Reuse model setup where possible.
3. Cache parameterized models or processed simulations if PyBaMM API permits safely.
4. Use coarser time grids during optimization and a finer final simulation for plots.
5. Downsample frontend plot data where necessary.
6. Precompute guided-demo results.
7. Bound optimizer population and generations.
8. Handle solver failures as invalid candidates, not fatal app errors.

Do not prematurely overengineer distributed compute.

---

# 22. ONE-CLICK MAC LAUNCHER

Create an executable file:

`Launch Battery MRI.command`

It should:

1. resolve its own project directory
2. create/use `.venv` if needed
3. verify Python dependencies
4. verify frontend build exists; build it if missing and Node is available
5. verify demo cache exists; generate it only if missing
6. select an available local port, preferably 8765
7. start the FastAPI server in the background
8. wait until `/api/health` succeeds
9. open the default browser to the app
10. keep terminal output concise and useful
11. shut down cleanly when the launcher terminal is closed if practical

Make the file executable with `chmod +x`.

Also create a developer script for rebuild/recompute.

The first-ever launch may take longer because dependencies install. Subsequent launches should be fast.

---

# 23. SCIENTIFIC VALIDATION TESTS

Write automated tests and a validation script.

At minimum verify:

## Waveform tests

- all segment durations positive
- total duration within configured bounds
- C-rate within bounds
- current direction conversion correct

## Simulation tests

- both default hypotheses solve successfully
- outputs contain finite time/voltage arrays
- same candidate uses same time grid after interpolation

## Inference tests

- posterior probabilities sum to 1
- log-sum-exp normalization is stable
- if the observation is generated exactly from A with near-zero noise, posterior strongly favors A
- symmetric identical predictions do not create artificial confidence

## Optimizer tests

- optimized probe score is greater than fixed baseline score for the default scenario
- ideally by a meaningful configured margin, for example 25%+, but use a threshold that the actual stable implementation supports
- optimized probe respects all safety constraints

## Adaptive test

- Probe 2 uses the Probe 1 posterior as its prior
- the cached default scenario shows non-decreasing expected diagnostic confidence across stages in the intended hidden-truth run

## Reproducibility

- fixed random seed reproduces the same cached guided-demo posterior to tight tolerance

Create:

`scripts/validate_science.py`

It should print a concise pass/fail report with the baseline score, optimized score, posterior after each probe, safety minima/maxima, and PyBaMM version.

---

# 24. FRONTEND QUALITY TESTS

At minimum:

- app loads with backend running
- Run Battery MRI button works
- pause/resume works
- replay works
- skip-to-result works
- charts render without NaN/undefined values
- resizing the browser does not break the layout
- 13–15 inch laptop viewport looks excellent
- no horizontal page scrolling at normal desktop size

If Playwright is already easy to use, create one smoke test. Do not let end-to-end testing become a multi-hour dependency rabbit hole.

---

# 25. ERROR HANDLING

The demo must fail gracefully.

Examples:

- if PyBaMM is missing: launcher installs it or shows a precise setup message
- if a PyBaMM parameter name changed: startup validator reports the missing name and available close matches
- if a simulation fails: optimizer marks candidate invalid; UI does not crash
- if cache is incompatible with current PyBaMM version: warn and offer developer recompute, but retain a known-good cached dataset when safe
- if Node is unavailable after a production frontend build already exists: still launch
- if no internet: Guided Demo still runs

---

# 26. ASSUMPTIONS / SCIENCE DRAWER

Add a small “Assumptions & Model” button.

It should show:

- PyBaMM model used (SPMe or actual fallback)
- parameter set
- exact hypothesis parameter perturbations
- initial SOC
- initial temperature
- C-rate limits
- voltage limits
- noise model
- waveform duration budget
- objective used
- solver used
- whether the result is cached or live
- PyBaMM version

This is important. It makes the project feel transparent and engineering-grade.

---

# 27. README

Create a strong README with:

1. what Battery MRI is
2. 30-second explanation
3. one-click launch instructions
4. manual developer launch instructions
5. architecture diagram in text/Markdown
6. scientific method
7. default hypotheses and parameters
8. optimization objective
9. Bayesian inference method
10. limitations
11. how to recompute the demo
12. test commands
13. where cached results are stored
14. how to switch between Guided Demo and Lab Mode

Include this limitation explicitly:

> “This prototype demonstrates simulation-driven optimal experiment design. Real diagnostic use would require calibrated cell-specific models, instrumentation error models, safety review, cycler integration, and physical validation.”

---

# 28. DO NOT DO THESE THINGS

- Do not use Unreal Engine.
- Do not build a static mockup with fake numbers.
- Do not hardcode final posterior percentages.
- Do not pretend an LLM performed numerical optimization.
- Do not label arbitrary scores as “Fisher information” or “bits.”
- Do not claim the app measures an internal battery state directly.
- Do not claim a simulated optimal waveform is safe on arbitrary real cells.
- Do not make the core demo depend on OpenAI, Anthropic, or internet access.
- Do not use an enormous DFN optimization loop if it makes the demo unreliable.
- Do not overfocus on fancy 3D graphics at the expense of real science.
- Do not use Ohm branding or imply this is an official Ohm product.
- Do not stop with TODOs on visible controls.

---

# 29. BUILD ORDER

Follow this order so the project does not become a beautiful fake demo.

## Phase 1 — prove the science in Python

1. Install current PyBaMM.
2. Build baseline SPMe simulation.
3. Implement the two hypothesis parameterizations.
4. Implement a fixed probe.
5. Verify both hypotheses simulate successfully.
6. Plot responses and calibrate perturbation severities.
7. Implement separation objective.
8. Implement bounded optimizer.
9. Demonstrate optimized probe beats baseline.
10. Implement noisy hidden-cell observation and Bayesian posterior.
11. Implement second adaptive probe.
12. Save deterministic results.

Do not proceed to a polished frontend until this works.

## Phase 2 — backend

1. Wrap science modules in typed FastAPI endpoints.
2. Add cache loader.
3. Add health endpoint.
4. Add tests.

## Phase 3 — frontend

1. Build Guided Demo first.
2. Implement all seven scenes.
3. Add scientific charts.
4. Add smooth transitions.
5. Implement the synchronized subtitle/caption system and direct animation labels from Section 16A.
6. Add assumptions drawer.
7. Add pause/replay/skip controls.

## Phase 4 — live Lab Mode

Add interactive recomputation only after Guided Demo is solid.

## Phase 5 — one-click packaging

1. build frontend
2. launcher
3. fresh-launch test
4. offline guided-demo test
5. final README

---

# 30. ACCEPTANCE CRITERIA — DO NOT DECLARE DONE UNTIL THESE PASS

The project is complete only when all of the following are true:

- `Launch Battery MRI.command` launches the app locally with one double-click.
- Guided Demo works without internet or API keys.
- One Run button triggers the complete 60–90 second narrative.
- The baseline and optimized waveforms are generated from real scientific code, not hardcoded fiction.
- The optimized default probe has a demonstrably better computed discrimination/information objective than the fixed baseline probe.
- The hidden-cell observations are generated from PyBaMM plus an explicit noise model.
- Posterior probabilities are calculated from likelihoods.
- Probe 2 is conditioned on Probe 1’s posterior.
- All displayed percentages and scores are sourced from saved computation results.
- Safety constraints are checked by code.
- The assumptions drawer exposes the actual model and parameters.
- The user can pause, replay, and skip the narrative.
- Guided Demo subtitles are enabled by default and synchronized with every scene.
- PyBaMM, waveform/probe design, optimization, hypothesis curves, Bayesian updating, posterior probabilities, and the adaptive feedback loop are visibly labeled and explained on-screen.
- Animated battery components, waveform segments, and scientific plots have direct labels; critical meaning is never hover-only.
- The final result screen includes a simulation/validation disclaimer.
- Automated science tests pass.
- `/api/health` passes.
- No visible TODO buttons remain.
- README is complete.

---

# 31. PRESENTATION POLISH

The finished app should be understandable to a technical founder in under two minutes without narration.

A viewer should leave with this mental model:

> “Normal AI reasons over measurements that already exist. Battery MRI uses a physics model and information theory to decide what electrical measurement should exist next.”

Then, if the user narrates it, the core explanation is:

> “I wanted to explore what happens if an engineering co-scientist becomes active rather than passive. Instead of only analyzing whatever test data already exists, this system asks what safe current waveform would maximally reduce uncertainty between two physical explanations. PyBaMM predicts how each hypothesis responds, the optimizer finds the most discriminating probe, and after each simulated measurement the system updates its belief and can redesign the next probe.”

The app should make that story visually obvious.

---

# 32. FINAL IMPLEMENTATION BEHAVIOR FOR CODEX

Start by inspecting the local environment and current PyBaMM API/version. Adapt code to the installed/current version rather than blindly assuming old examples compile.

When a scientific implementation choice is uncertain:

1. prefer the simplest physically defensible implementation
2. validate it numerically
3. label proxies honestly
4. document the choice in README and the Assumptions drawer

Do not sacrifice truthfulness for a prettier demo.

Run the application yourself before finishing. Run the validation script and tests. Fix failures. Verify the browser app is reachable locally and the cached Guided Demo data loads correctly.

At the very end, print a concise completion summary containing:

- project path
- launcher path
- local URL
- PyBaMM version
- baseline score
- optimized Probe 1 score
- posterior after Probe 1
- posterior after Probe 2
- test result summary
- any remaining limitations that are genuinely unavoidable

**Build the complete working project now.**
