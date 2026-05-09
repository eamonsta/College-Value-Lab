# College Value Lab Persona Audit

This audit stress-tests the app with made-up students who would use the product differently. The goal is not to prove the score is perfect. The goal is to find where the product helps, where it misleads, and what should improve before broader release.

## Test Personas

| Persona | Profile | What They Need |
|---|---|---|
| Maya | Low-income New Jersey student, pre-med, first-gen, $5k yearly budget | Find colleges that could be affordable after aid without unsafe debt |
| Arjun | California full-pay student, computer science, $90k yearly budget | Compare high-cost schools mostly by outcomes and major value |
| Sofia | Texas middle-income student, business, low debt tolerance | Find strong business options that do not exceed family budget |
| DeShawn | Low-income Georgia student, engineering, first-gen, $3k yearly budget | Avoid unaffordable out-of-state publics and identify strong-aid options |
| Lena | Upper-middle-income New York student, English/arts, $35k yearly budget | Balance fit, affordability, and lower-earning major risk |
| Noah | Rural Pennsylvania student, education, wants to stay near home | Find affordable, realistic, geographically sensible schools |
| Priya | Florida nursing student, wants a direct path to employment | Compare nursing outcomes, debt, and in-state affordability |
| Ethan | Massachusetts chemistry student, likely grad school | Compare strong completion/outcomes while recognizing early earnings limits |
| Grace | Michigan undecided student, budget-sensitive | Build a broad list without choosing a major yet |
| Marcus | Maryland full-pay finance student, prestige plus ROI | Compare full-cost schools where long-term earnings matter more |

## What Worked

- The app now separates family income from yearly family budget. This makes the results more realistic because a high-income family can still have a tight college budget, while a low-income student may receive large need-based aid.
- Financial Survivability is useful because it prevents high ROI from hiding a huge yearly budget gap.
- Program matching makes the app feel more personalized for nursing, engineering, business, computer science, chemistry, and similar interests.
- The official calculator override is important. It gives users a path from rough public-data estimate to stronger school-specific estimate.
- The selected-school workflow now feels closer to a real planning tool than a static dashboard.

## Where The App Lacks

- The biggest issue: elite private colleges often rank very high for low-income students because their reported net prices can be extremely low after aid. That can be financially true, but admissions-wise those schools are often reaches. The app now includes an Admissions Category column to reduce this risk.
- The app still does not know the student's grades, test scores, course rigor, activities, or admissions profile. It should not call anything a safety, target, or reach for the individual student yet.
- For students who care about location, the current home-state preference is not strong enough. A student like Noah can still see far-away schools at the top if the financial data is excellent.
- Program-level matching can be slow because it scans a large field-of-study dataset. Common focus options help, but custom searches are still heavier.
- Major outcomes are imperfect. Some fields are privacy-suppressed, and broad majors like "pre-med" are approximations rather than exact career paths.
- The model does not include merit aid probability, scholarship deadlines, honors colleges, housing differences, or graduate-school costs.
- The UI is much cleaner than before, but the product still needs a short "build your balanced list" nudge so students do not only chase the top score.

## Product Improvements To Prioritize

1. Add a balanced-list check: warn users if their selected schools are all extreme reach/reach, all out-of-budget, or all low-confidence.
2. Add stronger location controls: distance from home, preferred regions, and "must be in-state" or "within X miles" options.
3. Add an admissions-profile section later: GPA range, test optional/test score range, rigor, and desired selectivity comfort.
4. Add merit-aid signals where possible: percent receiving merit aid, average merit award, and schools known for merit support.
5. Cache or pre-index program matches so applying a major feels instant.
6. Add example walkthroughs for real user types: low-income/high-aid, full-pay, middle-income, first-gen, and major-focused.

## Honest Assessment

The project is now more than a surface-level ROI dashboard. The strongest concept is not "college ranking"; it is "financial survivability plus official-calculator workflow." That is more useful and more defensible. The remaining weakness is that college choice is not only financial. Before presenting this as a public tool, the app should push users toward a balanced shortlist that includes affordability, admissions realism, location, and verified calculator results.
