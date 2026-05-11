# College Value Lab Competition Package

Target competition: Congressional App Challenge 2026

Working deadline: October 26, 2026 at 8:00 PM ET

## One-Sentence Pitch

College Value Lab helps students build a financially realistic college list by combining public outcome data, family budget constraints, admissions realism, merit-aid signals, major outcomes, and official net price calculator results.

## Problem

College decisions are financially complicated. Students often compare sticker price, reputation, and scattered online rankings, but those do not answer the question that matters most for many families: can this student realistically afford, attend, finish, and benefit from this college?

Official net price calculators are important, but students usually have to run them school by school. College Value Lab acts as a comparison layer before that step, helping students decide which schools deserve deeper research.

## Users

Primary users:

- High school students building college lists.
- Families trying to compare affordability before application season.
- Counselors or teachers helping students understand financial fit.

The app is especially useful for students who need to think carefully about aid, debt, graduation likelihood, and realistic admissions balance.

## What The App Does

- Lets users enter a financial and academic profile.
- Estimates yearly cost after aid using public College Scorecard data.
- Separates current affordability from long-term ROI.
- Shows major/program-level earnings and debt when available.
- Adds admissions realism labels so a student does not build a list only from reach schools.
- Adds merit-aid opportunity signals when reliable Common Data Set-derived data is available.
- Lets users shortlist schools, rate personal fit, enter official net price calculator results, and compare final affordability.
- Warns when a shortlist is too reach-heavy, over budget, missing official calculator estimates, or based on low-confidence data.

## Data Sources

- U.S. Department of Education College Scorecard API for institution outcomes, costs, debt, earnings, graduation, and field-of-study data.
- College Scorecard net price calculator links when available.
- College Transitions merit-aid table, compiled from institutional Common Data Set reports, used only as an opportunity signal.
- Official net price calculators entered manually by users during validation/shortlist comparison.

## Scoring Method

College Value Lab uses several transparent planning signals:

- Financial Survivability: asks whether the student can realistically afford and finish the school without unsafe debt.
- Need Value Score: combines affordability, budget fit, debt, graduation, earnings, and home-state fit.
- Major-Adjusted Value: adjusts Need Value using program-level earnings and debt when the user enters an academic focus.
- Future ROI Score: standardizes long-term payoff relative to other schools in the dataset.
- Admissions Fit: a conservative realism label using reported admission rate plus optional GPA, SAT/ACT, and extracurricular strength.

The app does not claim to predict exact financial-aid offers, scholarships, admissions results, or individual career outcomes.

## What I Built

- Data fetching and cleaning scripts for public college outcome data.
- Streamlit app with profile inputs, filters, searchable explorer, selected-school workflow, validation worksheet, and methodology pages.
- Personalized scoring model for affordability, ROI, debt, graduation, and admissions realism.
- Shortlist health warnings and official calculator override workflow.
- Documentation, persona audit, migration roadmap, and competition package.

## Impact Plan

Before submission:

- Test with 10-20 students, parents, teachers, or counselors.
- Run 5-10 validation examples comparing app estimates with official net price calculators.
- Record the top 3-5 product changes made because of user feedback.
- Publish a public beta link and keep the GitHub repo readable.

## Limitations

- Public data can be missing, delayed, or privacy-suppressed.
- Net price by income does not perfectly predict a specific student’s aid offer.
- Merit aid is an opportunity signal, not guaranteed money.
- Admissions Fit is not a chance calculator.
- Major-level outcomes are historical medians and do not guarantee individual earnings.

## Demo Video Outline

1. Open with the problem: college cost is confusing and sticker price is misleading.
2. Enter a sample student profile.
3. Show Explorer filters and admissions fit.
4. Add several schools to Selected Schools.
5. Show shortlist health warnings.
6. Enter one official calculator estimate.
7. Explain why the app is transparent and limited.
8. End with impact: helping students build financially realistic college lists.
