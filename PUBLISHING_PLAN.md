# College Value Lab Publishing Plan

## What You Have Now

- A cleaned starter dataset: `data/processed/college_roi_clean.csv`
- A raw API cache: `data/raw/college_scorecard_api_raw.jsonl`
- A reproducible data pull: `scripts/fetch_college_scorecard.py`
- A cache cleaner: `scripts/clean_college_scorecard.py`
- A starter Streamlit dashboard: `app/college_value_lab.py`

## First MVP

Build a dashboard that answers one clear question:

> Which colleges appear to offer strong financial value based on public federal data?

The MVP should include:

- Search for a college by name.
- Filter by state and public/private status.
- Rank college cost scenarios by ROI index.
- Show graduation rate and on-time completion separately.
- Show cost vs. earnings scatterplot.
- Explain the formula and limitations.

## Publishable Outputs

1. Public dashboard  
   Publish with Streamlit Community Cloud.

2. GitHub repository  
   Include the code, cleaned CSV, README, and source citation.

3. Short research article  
   Title idea: "What Makes a College a Good Financial Bet?"

## Methodology Paragraph

This project uses the U.S. Department of Education College Scorecard API to compare colleges by cost before aid, estimated cost after aid, graduation rate, on-time completion, median debt, and median earnings 10 years after entry. I created an exploratory ROI index that divides median earnings by estimated four-year cost after aid, with a $20,000 cost floor to reduce distortion from extremely low reported net prices, and multiplies the result by graduation rate. Graduation rate uses the 150%-of-expected-time completion measure, while on-time completion uses the 100%-of-expected-time measure when available. Public colleges can appear as separate in-state and out-of-state cost scenarios. Because College Scorecard does not provide a perfect residency-specific after-aid net price, the out-of-state after-aid scenario is estimated by adding the tuition difference to the overall average net price. The index is meant for comparison and exploration, not as a guarantee of individual outcomes.

## Next Coding Steps

1. Get your own free College Scorecard API key.
2. Re-run `scripts/fetch_college_scorecard.py` for the full dataset.
3. Improve the dashboard college search page.
4. Add separate rankings for public, private nonprofit, and state-specific colleges.
5. Add a "limitations" section directly in the app.
6. Record a 60-second demo video.

## Resume Bullet Draft

Built College Value Lab, a public-data dashboard analyzing college return on investment using U.S. Department of Education College Scorecard data; cleaned 2,000+ institution records, designed an exploratory ROI index, and published an interactive dashboard comparing cost, debt, graduation, on-time completion, and earnings outcomes.
