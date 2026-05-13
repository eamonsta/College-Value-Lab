# College Value Lab

College Value Lab is a public-data college affordability planner. It helps students compare whether colleges are financially realistic, risky, or worth stretching for by combining estimated cost after aid, non-loan budget fit, estimated debt need, graduation outcomes, major outcomes, admissions realism, and post-college earnings.

## Data Source

The dataset comes from the U.S. Department of Education College Scorecard API:

https://collegescorecard.ed.gov/data/api/

The starter script uses the public `DEMO_KEY`. For a larger or production version, request a free API key and run:

```bash
export COLLEGE_SCORECARD_API_KEY="your_key_here"
python3 scripts/fetch_college_scorecard.py
```

## Start Here

1. Create a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Fetch and clean the data.

```bash
python3 scripts/fetch_college_scorecard.py
```

If you hit the public demo-key rate limit, clean the cached raw records:

```bash
python3 scripts/clean_college_scorecard.py
```

Optional: fetch field-of-study/program outcomes. This adds major-level earnings and debt to the app when a user enters an Academic focus.

```bash
python3 scripts/fetch_college_programs.py
```

With the public `DEMO_KEY`, this script only pulls a starter sample. With your own API key, it can pull much more:

```bash
export COLLEGE_SCORECARD_API_KEY="your_key_here"
PROGRAM_MAX_PAGES=80 python3 scripts/fetch_college_programs.py
```

Optional: backfill official net price calculator links from College Scorecard.

```bash
python3 scripts/fetch_net_price_calculator_urls.py
```

3. Run the dashboard.

```bash
streamlit run app/college_value_lab.py
```

## Personalized Value And Major-Adjusted Value

The app first estimates yearly cost after aid. If a user enters a family income range, the app uses College Scorecard net price by income bracket when available; otherwise it falls back to average net price. Public colleges may appear as separate in-state and out-of-state scenarios.

The app uses two main comparison scores:

- Personalized Value Score when no academic focus is entered.
- Major-Adjusted Value when a user enters an academic focus or major.

Personalized Value combines five components:

- Current affordability: estimated cost after aid, budget fit, and debt pressure.
- Future ROI / earnings: 10-year earnings, earnings after graduation, ROI ratio, and graduation rate.
- Debt safety.
- Graduation confidence.
- Home-state fit.

Major-Adjusted Value becomes the main score when a focus is entered. It blends the personalized score with program-level earnings and debt when public field-of-study data is available. The Personal Profile page lets users adjust how much each component matters. This makes the score useful for different situations: one student may need current affordability above all else, while another may care more about long-term payoff. These are exploratory planning scores, not financial-aid estimators or guarantees of individual outcomes.

The raw future ROI ratio is:

```text
(10-year median earnings / max(estimated 4-year cost after aid, $20,000)) * graduation rate
```

The app displays this as ROI Score, a 0-100 percentile rank that is easier to interpret:

- 85-100: excellent.
- 70-84: strong.
- 50-69: above average.
- 30-49: below average.
- 0-29: weak.

Graduation rate uses College Scorecard's 150%-of-expected-time completion measure. For bachelor's institutions, that generally means completion within six years. On-time completion is tracked separately with the 100%-of-expected-time field, which generally means four years for bachelor's institutions.

## Decision Signals

The app adds plain-English labels so students do not have to interpret every number from scratch:

- Strong financial fit.
- Affordable but lower payoff.
- High payoff but risky cost.
- Likely unaffordable without major aid.
- Debt warning.
- Completion risk.
- Data limited - verify manually.

The app also calculates a yearly budget gap, Estimated Debt Need, and a debt-to-early-earnings ratio. Estimated Debt Need uses the yearly amount covered without loans from Personal Profile: uncovered yearly cost multiplied by four. If no non-loan budget is entered, it falls back to the college's typical median debt. These numbers make the tradeoff more concrete: can the student afford the college now, and does the likely borrowing need look reasonable compared with early career earnings?

## Net Price Calculator Companion

College Value Lab does not try to replace official net price calculators. Federal rules require many colleges to publish a net price calculator using institutional data. The app now links to each college's reported calculator when College Scorecard provides it, and treats the calculator as the next step before making a final cost judgment.

Estimate Confidence shows how much public evidence supports the app's estimate. It considers income-bracket net price, school-wide outcomes, debt, graduation, calculator-link availability, residency assumptions, and program-level data when an academic focus is selected.

## Current Features

- Searchable college explorer with filters for state, region, ownership, residency, size, estimated cost, graduation rate, and data coverage.
- Income-bracket cost estimates for need-based aid when Scorecard data is available.
- Personalized Value Score and Major-Adjusted Value with profile presets.
- Plain-English financial signals, budget-gap estimates, and debt-to-earnings warnings.
- Estimate confidence and official net price calculator links.
- Optional program-level outcomes by academic focus using College Scorecard field-of-study records.
- Optional merit-aid opportunity signals from Common Data Set-derived public tables.
- Dedicated methodology page explaining scores, data sources, and limitations.
- Selected Schools tracker with application status, personal fit rating, official calculator override, notes, shortlist comparison, decision score, and CSV/JSON export.
- Data coverage indicators so missing public data is visible.

## Competition / Beta Package

The project includes supporting materials for a public beta and Congressional App Challenge submission:

- `COMPETITION_PACKAGE.md`: written response draft, app pitch, data sources, impact plan, and limitations.
- `DEMO_VIDEO_SCRIPT.md`: 1-3 minute video script.
- `USER_TESTING_TRACKER.md`: testing protocol and feedback tracker.
- `VALIDATION_EXAMPLES.md`: official calculator validation worksheet.
- `PERSONA_AUDIT.md`: fake-user stress test and product risks.

## Next Features

- This week: verify Streamlit Cloud, run one full smoke test, start 3-5 official calculator validation examples, and test with 5-10 users.
- Before competition/resume use: finish 5-10 official calculator validation examples and test with 10-20 students, parents, teachers, or counselors.
- Add persistent user accounts and saved school lists in a future full web app.
- Rebuild the product with Next.js, Supabase Auth, Supabase Postgres, and Vercel when moving beyond Streamlit.
- See `PRODUCT_MIGRATION_PLAN.md` for the full database/authentication roadmap.
