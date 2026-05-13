# College Value Lab Public Beta Week Checklist

Goal: make the current Streamlit beta safe to share this week. Do not start the full Next.js/Supabase rebuild yet.

## 1. Reliability

- [ ] Push latest commits to GitHub.
- [ ] Confirm Streamlit Cloud rebuilds without red errors.
- [ ] Open the app from a fresh browser session.
- [ ] Run the full smoke flow:
  - Personal Profile
  - Explorer
  - Add 3-5 schools
  - Selected Schools
  - Enter one yearly official calculator estimate
  - Download full progress JSON
  - Restore full progress JSON from Personal Profile
- [ ] Record any slow screen or action.

## 2. Validation

Use the beta sample profile from `VALIDATION_EXAMPLES.md`.

- [ ] Princeton University
- [ ] University of Michigan-Ann Arbor
- [ ] University of California-Los Angeles
- [ ] Georgia Institute of Technology
- [ ] Michigan State University

Record app yearly estimate, app Estimated Debt Need, official calculator result, difference, confidence label, and notes.

## 3. User Testing

- [ ] Test with 5-10 people this week.
- [ ] Ask each tester to enter a profile, filter Explorer, add 3 schools, read warnings, enter one calculator estimate, and export progress.
- [ ] Record the confusing moment, least trusted number, slowest part, missing feature, and one change to make.
- [ ] Summarize the top 3 repeated confusions.

## 4. Presentation

- [ ] Update the demo script after testing if users use different language than the app.
- [ ] Record a rough 1-3 minute demo.
- [ ] Keep the resume bullet honest: only say deployed, validated, or tested after those steps are actually complete.

## Done Criteria

The beta is ready to share more widely when the app loads, one full smoke flow works, at least 3 validation cases are started, at least 5 users test it, and the top feedback patterns are written down.
