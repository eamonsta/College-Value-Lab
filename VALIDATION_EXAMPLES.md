# College Value Lab Validation Examples

Purpose: document 5-10 comparisons between the app's public-data estimate and each school's official net price calculator.

## How To Run A Validation Case

Use one consistent sample profile for the first 3-5 cases this week. Recommended beta sample:

- Home state: Michigan
- Family income range: `$75k-$110k`
- Yearly amount covered without loans: `$20,000`
- Maximum comfortable debt: `$40,000`
- Academic focus: Data science
- GPA/test assumptions: 3.8 unweighted GPA, 1450 SAT, EC strength 7/10

Record:

- Home state
- Family income range
- Yearly amount covered without loans
- Maximum comfortable debt
- Household size
- Approximate assets, if the calculator asks
- GPA/test assumptions, if the calculator asks
- Academic focus, if relevant

Then for each school:

1. Record the app's yearly estimated cost after aid.
2. Record the app's Estimated Debt Need and Estimate Confidence.
3. Open the official net price calculator.
4. Enter the same sample profile.
5. Record the official calculator's yearly result.
6. Record the difference.
7. Add a note explaining why the difference might exist.

## Validation Table

| Priority | School | Sample Profile | App Yearly Estimate | App Estimated Debt Need | Official Calculator Result | Difference | App Confidence | Notes |
|---:|---|---|---:|---:|---:|---:|---|---|
| 1 | Princeton University | Michigan, $75k-$110k, $20k non-loan budget, $40k max debt, data science |  |  |  |  |  |  |
| 2 | University of Michigan-Ann Arbor | Michigan, $75k-$110k, $20k non-loan budget, $40k max debt, data science |  |  |  |  |  |  |
| 3 | University of California-Los Angeles | Michigan, $75k-$110k, $20k non-loan budget, $40k max debt, data science |  |  |  |  |  |  |
| 4 | Georgia Institute of Technology | Michigan, $75k-$110k, $20k non-loan budget, $40k max debt, data science |  |  |  |  |  |  |
| 5 | Michigan State University | Michigan, $75k-$110k, $20k non-loan budget, $40k max debt, data science |  |  |  |  |  |  |
| 6 | Stanford University | Same beta sample profile |  |  |  |  |  |  |
| 7 | CUNY Baruch College | Same beta sample profile |  |  |  |  |  |  |
| 8 | University of Florida | Same beta sample profile |  |  |  |  |  |  |

## What Counts As A Useful Result

The goal is not to prove the app is perfectly accurate. The goal is to show:

- where the public-data estimate is close,
- where it is far off,
- which kinds of schools need manual verification fastest,
- and why official calculators should remain part of the workflow.

## Summary To Add Later

After completing validation, write:

- Number of schools validated.
- Average absolute yearly difference.
- Number within $5,000/year.
- Number where official calculator changed the affordability verdict.
- Most common reason for disagreement.
- One product change made because of validation.
