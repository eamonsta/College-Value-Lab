# College Value Lab Product Migration Plan

This document explains how College Value Lab should move from a Streamlit prototype into a real website with accounts, saved school lists, and persistent data.

## Honest Product Assessment

The current Streamlit version is strong for a prototype: it proves the scoring logic, data workflow, user profile, shortlist workflow, and methodology. It is not yet a real consumer product because selected schools are saved only inside a browser session. If a user refreshes, changes browser, or comes back later, their progress can disappear.

The next product leap is not another chart. The next leap is persistence: users should be able to create an account, save their profile, save schools, return later, update official calculator results, and compare decisions over time.

## What To Do Next In Streamlit

Streamlit can still be useful for the next step, but do not overbuild it.

### Good Streamlit Additions

- Add optional export/import of selected schools as CSV or JSON.
- Improve Selected Schools so users know progress is temporary.
- Keep refining scoring, methodology, and validation.
- Use Streamlit Cloud for public beta testing.

### Bad Streamlit Additions

- Do not try to build serious account auth inside Streamlit.
- Do not rely on local SQLite for deployed user data.
- Do not store personal user data in session state only.
- Do not treat Streamlit Cloud as the final production infrastructure.

Why: Streamlit reruns the script often, sessions are fragile, and the free cloud environment is not designed for a polished multi-user consumer app.

## Recommended Real Website Stack

The best next stack for this project:

- Frontend: Next.js
- Styling: Tailwind CSS
- Database: Supabase Postgres
- Authentication: Supabase Auth
- Data/API layer: Next.js server routes
- Hosting: Vercel
- Data refresh scripts: Python scripts kept from this repo

This is a good stack because it is realistic for a student project, has free tiers, supports real accounts, and can scale beyond a prototype without becoming too complicated.

## Core Database Tables

### users

Handled by Supabase Auth.

### profiles

Stores one row per user.

Fields:

- user_id
- home_state
- family_income_bracket
- annual_family_budget
- max_comfortable_debt
- academic_focus
- unweighted_gpa
- sat_score
- act_score
- ec_score
- affordability_importance
- earnings_importance
- debt_importance
- graduation_importance
- aid_uncertainty
- first_gen
- created_at
- updated_at

### schools

Stores cleaned college-level data imported from College Scorecard.

Fields:

- unit_id
- name
- city
- state
- ownership
- student_size
- admission_rate
- annual_cost
- tuition_in_state
- tuition_out_of_state
- avg_net_price
- income-bracket net price fields
- graduation_rate
- on_time_completion_rate
- median_debt
- earnings fields
- net_price_calculator_url

### programs

Stores program-level field-of-study data.

Fields:

- unit_id
- cip_code
- program_title
- credential_level
- earnings_1yr
- earnings_4yr
- earnings_5yr
- national_earnings_4yr
- program_median_debt
- awards_latest
- program_data_points

### selected_schools

Stores the user's shortlist.

Fields:

- id
- user_id
- unit_id
- residency
- status
- personal_fit
- official_calculator_estimate
- notes
- created_at
- updated_at

### validation_cases

Stores manual validation examples.

Fields:

- id
- sample_profile_name
- unit_id
- app_estimated_cost
- official_calculator_cost
- public_avg_net_price
- difference
- confidence_label
- notes

## User Flow In The Real Product

1. User creates an account.
2. User fills out Personal Profile.
3. App computes personalized college scenarios.
4. User searches and filters colleges.
5. User adds colleges to Selected Schools.
6. User runs official net price calculators.
7. User enters official calculator estimates.
8. App updates affordability, survivability, and shortlist warnings.
9. User exports or shares a summary with family/counselor.

## What Changes Technically

### Current Streamlit Prototype

- Python script loads CSV files.
- Every interaction reruns the script.
- Selected schools live in `st.session_state`.
- No real users.
- No database.

### Real Website

- Frontend requests data from backend routes.
- Backend queries Supabase.
- User auth identifies which saved schools belong to which user.
- Scoring can run server-side or be precomputed.
- User progress persists across devices.

## Migration Steps

### Phase 1: Strengthen The Beta

- Keep Streamlit public.
- Add clear temporary-save warnings.
- Add export/import for shortlist.
- Finish validation examples.
- Get feedback from 10-20 real users.

### Phase 2: Create The Web App Skeleton

- Create a new Next.js app.
- Add Supabase Auth.
- Add a simple dashboard shell.
- Add profile form.
- Add saved shortlist table.

### Phase 3: Move The Data

- Import `college_roi_clean.csv` into Supabase.
- Import `college_programs_clean.csv` into Supabase.
- Recreate cost scenarios and scoring logic in TypeScript or server-side Python.
- Keep formulas documented next to the code.

### Phase 4: Rebuild Core Features

- Explorer page.
- College detail page.
- Selected Schools page.
- Official calculator override.
- Balanced shortlist warnings.
- Methodology page.

### Phase 5: Launch Public Beta

- Deploy on Vercel.
- Invite users.
- Track feedback.
- Add usage analytics.
- Write a public project article.

## Biggest Risks

- The scoring can look more precise than it really is.
- Admissions labels can be misread as actual chances.
- Official calculators are still more accurate for final price.
- Program-level data is incomplete.
- Saved personal financial data requires careful privacy wording.

## Positioning

Do not pitch this as "the app that knows what college you should attend."

Better:

> College Value Lab helps students build a financially realistic college list by combining public outcome data, family budget constraints, admissions realism, and official net price calculator results.

That positioning is more honest and much stronger.
