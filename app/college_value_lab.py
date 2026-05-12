#!/usr/bin/env python3
"""
Starter Streamlit dashboard for College Value Lab.

Run locally:
    streamlit run app/college_value_lab.py
"""

import difflib
import html
import json
import re
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "college_roi_clean.csv"
PROGRAM_DATA_PATH = ROOT / "data" / "processed" / "college_programs_clean.csv"
MERIT_AID_DATA_PATH = ROOT / "data" / "processed" / "college_merit_aid_clean.csv"
DATA_SCHEMA_VERSION = 4
PROGRAM_SCHEMA_VERSION = 3
MERIT_AID_SOURCE_URL = "https://www.collegetransitions.com/dataverse/merit-aid/"

NICKNAMES = {
    "asu": ["arizona state university"],
    "baruch": ["cuny bernard m baruch college"],
    "berkeley": ["university of california berkeley"],
    "cal": ["university of california berkeley"],
    "caltech": ["california institute of technology"],
    "cmu": ["carnegie mellon university"],
    "ga tech": ["georgia institute of technology"],
    "georgia tech": ["georgia institute of technology"],
    "gt": ["georgia institute of technology"],
    "mit": ["massachusetts institute of technology"],
    "mich state": ["michigan state university"],
    "msu": ["michigan state university"],
    "nyu": ["new york university"],
    "penn": ["university of pennsylvania"],
    "rutgers": ["rutgers university"],
    "stanford": ["stanford university"],
    "uc berkeley": ["university of california berkeley"],
    "ucb": ["university of california berkeley"],
    "uci": ["university of california irvine"],
    "ucla": ["university of california los angeles"],
    "ucsd": ["university of california san diego"],
    "ucsb": ["university of california santa barbara"],
    "uf": ["university of florida", "university of florida online"],
    "um": ["university of michigan ann arbor"],
    "umich": ["university of michigan ann arbor"],
    "unc": ["university of north carolina at chapel hill"],
    "uva": ["university of virginia main campus"],
    "uw": ["university of washington seattle campus"],
}

REGIONS = {
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast", "NH": "Northeast",
    "NJ": "Northeast", "NY": "Northeast", "PA": "Northeast", "RI": "Northeast",
    "VT": "Northeast",
    "IL": "Midwest", "IN": "Midwest", "IA": "Midwest", "KS": "Midwest",
    "MI": "Midwest", "MN": "Midwest", "MO": "Midwest", "NE": "Midwest",
    "ND": "Midwest", "OH": "Midwest", "SD": "Midwest", "WI": "Midwest",
    "AL": "South", "AR": "South", "DC": "South", "DE": "South",
    "FL": "South", "GA": "South", "KY": "South", "LA": "South",
    "MD": "South", "MS": "South", "NC": "South", "OK": "South",
    "SC": "South", "TN": "South", "TX": "South", "VA": "South",
    "WV": "South",
    "AK": "West", "AZ": "West", "CA": "West", "CO": "West",
    "HI": "West", "ID": "West", "MT": "West", "NM": "West",
    "NV": "West", "OR": "West", "UT": "West", "WA": "West",
    "WY": "West",
}

EARNINGS_OPTIONS = {
    "1 year after graduation": "median_earnings_1yr_after_completion",
    "4 years after graduation": "median_earnings_4yr_after_completion",
    "5 years after graduation": "median_earnings_5yr_after_completion",
    "6 years after entry": "median_earnings_6yr_after_entry",
    "10 years after entry": "median_earnings_10yr",
}

EARNINGS_FALLBACK_COLUMNS = list(EARNINGS_OPTIONS.values())

DEFAULT_INCOME_BRACKET = "Not sure / use average net price"
NO_NEED_AID_BRACKET = "Not expecting need-based aid / use full cost"

INCOME_BRACKETS = {
    DEFAULT_INCOME_BRACKET: None,
    "$0-$30k": "net_price_income_0_30000",
    "$30k-$48k": "net_price_income_30001_48000",
    "$48k-$75k": "net_price_income_48001_75000",
    "$75k-$110k": "net_price_income_75001_110000",
    "$110k+ with possible need-based aid": "net_price_income_110001_plus",
    NO_NEED_AID_BRACKET: "full_cost",
}

INCOME_NET_PRICE_COLUMNS = [
    column
    for column in INCOME_BRACKETS.values()
    if column and column != "full_cost"
]

INCOME_BRACKET_ALIASES = {
    "110k+": "$110k+ with possible need-based aid",
    "$110k+": "$110k+ with possible need-based aid",
    "$110k or more": "$110k+ with possible need-based aid",
    "$110,001+": "$110k+ with possible need-based aid",
    "Prefer not to say": DEFAULT_INCOME_BRACKET,
    "Prefer not to say / use average": DEFAULT_INCOME_BRACKET,
}

FOCUS_CIP_PREFIXES = {
    "accounting": ("5203",),
    "architecture": ("04",),
    "art": ("50",),
    "computer science": ("11",),
    "cs": ("11",),
    "business": ("52",),
    "biology": ("26",),
    "chemistry": ("4005",),
    "criminal justice": ("4301",),
    "data science": ("30", "11"),
    "nursing": ("5138",),
    "economics": ("4506",),
    "engineering": ("14", "15"),
    "english": ("23",),
    "finance": ("5208",),
    "history": ("54",),
    "journalism": ("0904",),
    "math": ("27",),
    "mathematics": ("27",),
    "medicine": ("26",),
    "pre med": ("26",),
    "physics": ("4008",),
    "political science": ("4510",),
    "public health": ("5122",),
    "psychology": ("42",),
    "education": ("13",),
    "sociology": ("4511",),
    "statistics": ("2705",),
}

FOCUS_TITLE_RULES = {
    "data science": {
        "required_any": (
            "data",
            "analytics",
            "analytic",
            "information",
            "informatics",
            "computer",
            "computing",
            "statistics",
            "statistical",
            "machine",
            "artificial",
        ),
        "blocked_any": (
            "plant",
            "animal",
            "crop",
            "soil",
            "food",
            "agriculture",
            "agricultural",
            "environmental",
            "natural resources",
        ),
    },
    "pre med": {
        "required_any": (
            "biology",
            "biological",
            "biomedical",
            "neuroscience",
            "health",
            "chemistry",
            "biochemistry",
        ),
        "blocked_any": ("plant", "animal", "agriculture", "food", "soil"),
    },
}

COMMON_ACADEMIC_FOCUSES = [
    "",
    "accounting",
    "architecture",
    "biology",
    "business",
    "chemistry",
    "computer science",
    "criminal justice",
    "data science",
    "economics",
    "education",
    "engineering",
    "english",
    "finance",
    "history",
    "journalism",
    "math",
    "nursing",
    "physics",
    "political science",
    "pre med",
    "public health",
    "psychology",
    "sociology",
    "statistics",
]

APPLICATION_STATUSES = [
    "Considering",
    "Planning to apply",
    "Applied - waiting",
    "Waitlisted",
    "Accepted",
    "Rejected",
    "Committed",
]

SCORE_BANDS = [
    ("90-100", "Unusually strong", "Rare combination of lower estimated cost, stronger outcomes, lower debt, and solid completion."),
    ("70-89", "Strong", "Worth serious attention, but still verify with the official calculator."),
    ("50-69", "Mixed", "Some signals are good, but cost, debt, completion, or missing data may weaken the case."),
    ("Below 50", "Risky or weak", "Likely expensive, lower payoff, lower completion, or too much missing data for this profile."),
]

VALIDATION_SCHOOL_NAMES = [
    "Princeton University",
    "Stanford University",
    "University of Michigan-Ann Arbor",
    "University of California-Los Angeles",
    "Georgia Institute of Technology-Main Campus",
    "Michigan State University",
    "CUNY Bernard M Baruch College",
    "University of Florida",
]


@st.cache_data
def load_data(data_updated_at, schema_version, merit_data_updated_at):
    data = pd.read_csv(DATA_PATH)
    required_columns = set(EARNINGS_OPTIONS.values())
    missing_columns = sorted(required_columns - set(data.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        st.error(
            "The cleaned dataset is missing newer earnings columns. "
            f"Missing: {missing}. Run `python3 scripts/fetch_college_scorecard.py` to refresh the data."
        )
        st.stop()
    for column in INCOME_NET_PRICE_COLUMNS:
        if column not in data.columns:
            data[column] = None
    for column in ["school_url", "net_price_calculator_url"]:
        if column not in data.columns:
            data[column] = None
    merit_data = load_merit_aid_data(merit_data_updated_at)
    if not merit_data.empty:
        data = data.merge(merit_data, on="unit_id", how="left")
    for column in [
        "merit_aid_percent",
        "merit_aid_average_award",
        "merit_cost_of_attendance_in_state",
        "merit_cost_of_attendance_out_of_state",
    ]:
        if column not in data.columns:
            data[column] = None
    if "merit_aid_source_year" not in data.columns:
        data["merit_aid_source_year"] = None
    data["merit_aid_signal"] = data.apply(
        lambda row: merit_aid_signal(row.get("merit_aid_percent"), row.get("merit_aid_average_award")),
        axis=1,
    )
    return data


@st.cache_data
def load_merit_aid_data(data_updated_at):
    if data_updated_at is None:
        return pd.DataFrame()
    data = pd.read_csv(MERIT_AID_DATA_PATH)
    expected_columns = [
        "unit_id",
        "merit_aid_percent",
        "merit_aid_average_award",
        "merit_cost_of_attendance_in_state",
        "merit_cost_of_attendance_out_of_state",
        "merit_aid_source_year",
    ]
    for column in expected_columns:
        if column not in data.columns:
            data[column] = None
    for column in [
        "unit_id",
        "merit_aid_percent",
        "merit_aid_average_award",
        "merit_cost_of_attendance_in_state",
        "merit_cost_of_attendance_out_of_state",
    ]:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    return data[expected_columns].drop_duplicates("unit_id")


@st.cache_data
def load_program_data(data_updated_at, schema_version):
    if data_updated_at is None:
        return pd.DataFrame()
    usecols = [
        "unit_id",
        "cip_code",
        "program_title",
        "credential_level",
        "awards_latest",
        "earnings_1yr",
        "earnings_4yr",
        "earnings_5yr",
        "national_earnings_4yr",
        "program_median_debt",
        "program_debt_payment",
        "debt_to_earnings_1yr",
        "program_data_points",
    ]
    data = pd.read_csv(PROGRAM_DATA_PATH, usecols=usecols)
    for column in [
        "unit_id",
        "credential_level",
        "awards_latest",
        "earnings_1yr",
        "earnings_4yr",
        "earnings_5yr",
        "earnings_highest_1yr",
        "earnings_highest_2yr",
        "earnings_highest_3yr",
        "national_earnings_4yr",
        "program_median_debt",
        "program_debt_payment",
        "program_debt_count",
        "debt_to_earnings_1yr",
        "program_data_points",
    ]:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    if "program_title" in data.columns:
        data["program_search_text"] = data["program_title"].apply(normalize_search_text)
    return data


def money(value):
    if pd.isna(value):
        return "N/A"
    return f"${value:,.0f}"


def markdown_safe(text):
    return str(text).replace("$", r"\$")


def markdown_money(value):
    return markdown_safe(money(value))


def plain_html(text, tag="p", class_name="plain-text"):
    return f'<{tag} class="{class_name}">{html.escape(str(text))}</{tag}>'


def plain_markdown_text(text):
    return st.markdown(plain_html(text), unsafe_allow_html=True)


def plain_caption(text):
    return st.markdown(plain_html(text, tag="p", class_name="plain-caption"), unsafe_allow_html=True)


def plain_note(text):
    return st.markdown(plain_html(text, tag="div", class_name="plain-note"), unsafe_allow_html=True)


def summary_card(title, college, detail, help_text=None):
    help_html = f'<div class="summary-help">{html.escape(help_text)}</div>' if help_text else ""
    st.markdown(
        f"""
<div class="summary-card">
    <div class="summary-title">{html.escape(str(title))}</div>
    <div class="summary-college">{html.escape(str(college))}</div>
    <div class="summary-detail">{html.escape(str(detail))}</div>
    {help_html}
</div>
        """,
        unsafe_allow_html=True,
    )


def pct(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def number(value, decimals=0):
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def missing_reason(value, label, fallback="Not enough public data available"):
    if pd.isna(value):
        return f"{label}: {fallback}"
    return None


def score_band_label(score):
    if pd.isna(score):
        return "Not enough public data available"
    if score >= 90:
        return "Unusually strong"
    if score >= 70:
        return "Strong"
    if score >= 50:
        return "Mixed"
    return "Risky or weak"


def clean_url(value):
    if pd.isna(value) or not str(value).strip():
        return None
    url = str(value).strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def signed_money(value):
    if pd.isna(value):
        return "N/A"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.0f}"


def signed_percent(value):
    if pd.isna(value):
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{value:.1%}"


def major_earnings_difference_label(delta, percent_delta):
    if pd.isna(delta):
        return "Program earnings unavailable"
    if delta > 0:
        return f"{money(delta)} above school median ({signed_percent(percent_delta)})"
    if delta < 0:
        return f"{money(abs(delta))} below school median ({signed_percent(percent_delta)})"
    return "Matches school median"


def debt_risk_label(median_debt, max_debt, earnings_after_grad):
    if pd.isna(median_debt):
        return "Debt data unavailable"
    signals = []
    if max_debt > 0:
        if median_debt <= max_debt:
            signals.append(f"under debt limit by {money(max_debt - median_debt)}")
        else:
            signals.append(f"over debt limit by {money(median_debt - max_debt)}")
    ratio = debt_to_earnings_ratio(median_debt, earnings_after_grad)
    if pd.notna(ratio):
        if ratio <= 0.35:
            signals.append("manageable vs earnings")
        elif ratio <= 0.60:
            signals.append("watch vs earnings")
        else:
            signals.append("high vs earnings")
    return "; ".join(signals) if signals else "Add debt limit for risk"


def annual_budget_gap(cost_after_aid, yearly_budget):
    if yearly_budget <= 0 or pd.isna(cost_after_aid):
        return float("nan")
    return cost_after_aid - yearly_budget


def four_year_budget_gap(cost_after_aid, yearly_budget):
    gap = annual_budget_gap(cost_after_aid, yearly_budget)
    if pd.isna(gap):
        return float("nan")
    return gap * 4


def debt_to_earnings_ratio(median_debt, earnings):
    if pd.isna(median_debt) or pd.isna(earnings) or earnings <= 0:
        return float("nan")
    return median_debt / earnings


def debt_safety_label(ratio):
    if pd.isna(ratio):
        return "Debt data limited"
    if ratio <= 0.35:
        return "Debt looks manageable"
    if ratio <= 0.60:
        return "Debt worth watching"
    return "Debt warning"


def roi_rating(score):
    if pd.isna(score):
        return "No ROI data"
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Strong"
    if score >= 50:
        return "Above average"
    if score >= 30:
        return "Below average"
    return "Weak"


def merit_aid_signal(percent_receiving, average_award):
    if pd.isna(percent_receiving) and pd.isna(average_award):
        return "Merit data unavailable"
    if pd.notna(percent_receiving) and percent_receiving <= 1 and (pd.isna(average_award) or average_award == 0):
        return "Little/no merit aid"
    if pd.notna(percent_receiving) and percent_receiving >= 35 and pd.notna(average_award) and average_award >= 15000:
        return "Strong merit opportunity"
    if pd.notna(percent_receiving) and percent_receiving >= 20 and pd.notna(average_award) and average_award >= 8000:
        return "Possible merit opportunity"
    if pd.notna(percent_receiving) and percent_receiving >= 10:
        return "Limited merit opportunity"
    return "Rare merit aid"


def admissions_category(admission_rate):
    if pd.isna(admission_rate):
        return "Admissions data unavailable"
    if admission_rate <= 0.10:
        return "Extreme reach"
    if admission_rate <= 0.25:
        return "Reach"
    if admission_rate <= 0.50:
        return "Selective"
    if admission_rate <= 0.75:
        return "Moderately selective"
    return "Less selective"


def has_academic_profile(profile):
    return (
        profile.get("unweighted_gpa", 0) > 0
        or profile.get("sat_score", 0) > 0
        or profile.get("act_score", 0) > 0
        or profile.get("ec_score", 0) > 0
    )


def academic_strength_score(profile):
    pieces = []
    weights = []

    gpa = profile.get("unweighted_gpa", 0)
    if gpa > 0:
        pieces.append(clamp_score((gpa - 2.5) / 1.5 * 100))
        weights.append(0.45)

    sat = profile.get("sat_score", 0)
    act = profile.get("act_score", 0)
    if sat > 0:
        pieces.append(clamp_score((sat - 900) / 700 * 100))
        weights.append(0.35)
    elif act > 0:
        pieces.append(clamp_score((act - 17) / 19 * 100))
        weights.append(0.35)

    ec_score = profile.get("ec_score", 0)
    if ec_score > 0:
        pieces.append(clamp_score(ec_score * 10))
        weights.append(0.20)

    if not pieces:
        return float("nan")

    total_weight = sum(weights)
    return sum(piece * weight for piece, weight in zip(pieces, weights)) / total_weight


def personalized_admissions_fit(admission_rate, profile):
    base_label = admissions_category(admission_rate)
    if pd.isna(admission_rate):
        return "Admissions data unavailable"
    if not has_academic_profile(profile):
        return base_label

    strength = academic_strength_score(profile)
    if pd.isna(strength):
        return base_label

    # Ultra-selective colleges stay far reaches for everyone; strong stats only reduce how far the reach is.
    if admission_rate <= 0.05:
        if strength >= 90:
            return "Far reach"
        return "Extreme reach"
    if admission_rate <= 0.08:
        if strength >= 95:
            return "Far reach"
        if strength >= 78:
            return "Far reach"
        return "Extreme reach"
    if admission_rate <= 0.12:
        if strength >= 95:
            return "Reach"
        if strength >= 78:
            return "Far reach"
        return "Extreme reach"
    if admission_rate <= 0.25:
        if strength >= 88:
            return "Target/reach"
        if strength >= 70:
            return "Reach"
        return "Far reach"
    if admission_rate <= 0.50:
        if strength >= 82:
            return "Target"
        if strength >= 62:
            return "Target/reach"
        return "Reach"
    if admission_rate <= 0.75:
        if strength >= 68:
            return "Likely"
        if strength >= 48:
            return "Target"
        return "Target/reach"
    if strength >= 45:
        return "Likely"
    return "Target"


def risk_label(row, profile):
    cost = row["cost_after_aid"]
    graduation = row["graduation_rate"]
    data_coverage = row["data_coverage"]
    gap = annual_budget_gap(cost, profile["annual_family_budget"])
    debt_ratio = row["debt_to_earnings_after_grad"]

    if pd.notna(data_coverage) and data_coverage < 80:
        return "Data limited - verify manually"

    if profile["annual_family_budget"] > 0 and pd.notna(gap):
        verdict = affordability_verdict(gap, profile["annual_family_budget"])
        if verdict == "Within budget":
            if row["future_roi_score"] >= 70:
                return "Within budget + strong payoff"
            return "Within budget"
        if verdict == "Small gap":
            return "Slightly above budget"
        if verdict == "Moderate gap":
            return "Above budget - compare aid"
        return "Likely unaffordable at this cost"

    if row.get("net_price_source") == "full cost":
        return "Full-cost estimate - add budget"
    if pd.notna(debt_ratio) and debt_ratio > 0.75:
        return "Debt warning"
    if pd.notna(graduation) and graduation < 0.45:
        return "Completion risk"
    if row["current_affordability_score"] >= 75 and row["future_roi_score"] >= 70:
        return "Strong financial fit"
    if row["current_affordability_score"] >= 75 and row["future_roi_score"] < 55:
        return "Affordable but lower payoff"
    if row["current_affordability_score"] < 45 and row["future_roi_score"] >= 75:
        return "High payoff but risky cost"
    return "Balanced option"


def budget_gap_sentence(row, profile):
    if profile["annual_family_budget"] <= 0:
        return "Add a yearly family budget in Personal Profile to see the budget gap."

    yearly_gap = annual_budget_gap(row["cost_after_aid"], profile["annual_family_budget"])
    total_gap = four_year_budget_gap(row["cost_after_aid"], profile["annual_family_budget"])
    if pd.isna(yearly_gap):
        return "Budget gap cannot be calculated because estimated cost after aid is missing."
    if yearly_gap <= 0:
        return (
            f"Estimated cost is {money(abs(yearly_gap))} under your yearly budget, "
            f"or about {money(abs(total_gap))} under budget over four years."
        )
    return (
        f"Estimated cost is {money(yearly_gap)} above your yearly budget, "
        f"or about {money(total_gap)} above budget over four years."
    )


def plain_english_summary(row, profile):
    strengths = []
    cautions = []

    if row["current_affordability_score"] >= 70:
        strengths.append("the estimated cost looks relatively workable")
    elif row["current_affordability_score"] < 45:
        cautions.append("the estimated cost may be hard to manage")

    if row["future_roi_score"] >= 70:
        strengths.append("earnings relative to cost look strong")
    elif row["future_roi_score"] < 45:
        cautions.append("the earnings payoff is weaker than many schools in this dataset")

    if pd.notna(row["graduation_rate"]) and row["graduation_rate"] >= 0.75:
        strengths.append("the graduation rate is strong")
    elif pd.notna(row["graduation_rate"]) and row["graduation_rate"] < 0.50:
        cautions.append("the graduation rate is a real concern")

    debt_ratio = row["debt_to_earnings_after_grad"]
    if pd.notna(debt_ratio) and debt_ratio <= 0.35:
        strengths.append("typical debt looks manageable compared with early earnings")
    elif pd.notna(debt_ratio) and debt_ratio > 0.60:
        cautions.append("typical debt is high compared with early earnings")

    if row["risk_label"].startswith("Data limited"):
        cautions.append("some key public-data fields are missing")

    if profile["academic_focus"] and pd.notna(row.get("program_earnings_vs_school")):
        difference = row["program_earnings_vs_school"]
        if difference > 0:
            strengths.append(f"the matched major earns about {money(difference)} more than the school's overall early-career median")
        elif difference < 0:
            cautions.append(f"the matched major earns about {money(abs(difference))} less than the school's overall early-career median")

    if strengths:
        first_sentence = f"This school looks promising because {', '.join(strengths[:3])}."
    else:
        first_sentence = "This school does not clearly stand out on the strongest financial signals yet."

    if cautions:
        second_sentence = f"The main caution is that {', '.join(cautions[:3])}."
    else:
        second_sentence = "There is no major red flag from the public fields currently used here."

    return f"{first_sentence} {second_sentence} {budget_gap_sentence(row, profile)}"


def estimate_confidence(row, profile):
    points = 0
    reasons = []

    if pd.notna(row.get("cost_after_aid")):
        if row.get("net_price_source") == "full cost":
            points += 32
            reasons.append("uses full cost because no need-based aid is expected")
        elif row.get("net_price_source") == "income bracket":
            points += 30
            reasons.append("uses income-bracket net price")
        else:
            points += 18
            reasons.append("uses average net price fallback")
    else:
        reasons.append("missing estimated cost after aid")

    evidence_checks = [
        ("graduation rate", row.get("graduation_rate"), 10),
        ("median debt", row.get("median_debt"), 10),
        ("10-year earnings", row.get("earnings_10yr_used"), 10),
        ("early earnings", row.get("earnings_after_grad"), 5),
        ("on-time completion", row.get("on_time_completion_rate"), 5),
    ]
    for label, value, weight in evidence_checks:
        if pd.notna(value):
            points += weight
        else:
            reasons.append(f"missing {label}")

    if clean_url(row.get("net_price_calculator_url")):
        points += 15
        reasons.append("official calculator link available")
    else:
        reasons.append("official calculator link missing")

    if row.get("residency") == "Out-of-state":
        points -= 5
        reasons.append("out-of-state after-aid cost is estimated from tuition difference")

    if profile["academic_focus"]:
        if pd.notna(row.get("program_match")):
            points += 6
            reasons.append("matched field-of-study program")
        else:
            points -= 8
            reasons.append("no matching program data for focus")
        if pd.notna(row.get("program_earnings_1yr")):
            points += 7
        else:
            reasons.append("missing program earnings")
        if pd.notna(row.get("program_debt")):
            points += 5
        else:
            reasons.append("missing program debt")
    else:
        points += 8

    score = clamp_score(points)
    if score >= 80:
        label = "High"
    elif score >= 55:
        label = "Medium"
    else:
        label = "Low"
    return score, label, "; ".join(reasons[:5])


def add_estimate_confidence(data, profile):
    data = data.copy()
    confidence = data.apply(lambda row: estimate_confidence(row, profile), axis=1)
    data["estimate_confidence_score"] = confidence.apply(lambda value: value[0])
    data["estimate_confidence"] = confidence.apply(lambda value: value[1])
    data["estimate_confidence_notes"] = confidence.apply(lambda value: value[2])
    data["financial_survivability_score"] = data.apply(
        lambda row: financial_survivability_score_for_values(
            row.get("cost_after_aid"),
            profile["annual_family_budget"],
            profile["max_comfortable_debt"],
            row.get("median_debt"),
            row.get("earnings_after_grad"),
            row.get("graduation_rate"),
            row.get("estimate_confidence_score"),
            profile["aid_uncertainty"],
        ),
        axis=1,
    )
    data["financial_survivability_label"] = data["financial_survivability_score"].apply(
        financial_survivability_label
    )
    data["data_warning"] = "Enough public data"
    data.loc[data["data_coverage"] < 80, "data_warning"] = "Verify missing public data"
    data.loc[data["estimate_confidence"] == "Low", "data_warning"] = "Low confidence - verify"
    if profile["academic_focus"]:
        data.loc[data["program_match"].isna(), "data_warning"] = "Program-level data unavailable"
    return data


def set_profile_preset(
    affordability,
    earnings,
    debt,
    graduation,
    aid_uncertainty,
    in_state=None,
):
    st.session_state["affordability_importance"] = affordability
    st.session_state["earnings_importance"] = earnings
    st.session_state["debt_importance"] = debt
    st.session_state["graduation_importance"] = graduation
    st.session_state["aid_uncertainty"] = aid_uncertainty
    if in_state is not None:
        st.session_state["in_state_importance"] = in_state
    st.rerun()


TOOLTIPS = {
    "colleges": "Number of college cost scenarios currently shown after sidebar filters. If you entered a home state, public colleges show the realistic residency for you: in-state in your state and out-of-state elsewhere.",
    "cost_before_aid": "Estimated yearly cost before financial aid and scholarships. This is an annual amount, not a four-year total. For out-of-state public colleges, this adds the out-of-state tuition difference.",
    "cost_after_aid": "Estimated yearly cost after grants and scholarships. This is an annual amount, not a four-year total. If you choose an income range, this uses Scorecard net price by income when available. If you choose no need-based aid expected, it uses full annual cost.",
    "residency": "Cost scenario used for the row. If you entered a home state, public colleges use in-state only for that state and out-of-state for other states. If no home state is entered, both scenarios are shown.",
    "graduation_rate": "College Scorecard graduation rate, generally completion within 150% of expected time. For bachelor's schools, that usually means within six years.",
    "on_time_completion_rate": "Completion within 100% of expected time. For bachelor's schools, that usually means within four years.",
    "median_debt": "Median federal student loan debt among students who completed at that college.",
    "selected_earnings": "Median earnings used in the table or chart. The app now shows both earnings after graduation and earnings 10 years later instead of using a timeline filter.",
    "median_earnings_10yr": "Median earnings 10 years after students first entered the college.",
    "need_value_score": "Personalized 0-100 value score for cost-sensitive students. Higher is better. It uses estimated yearly cost after aid, budget fit, debt, graduation rate, earnings, and profile settings.",
    "focus_adjusted_score": "Personalized 0-100 value score when Academic focus is entered. Higher is better. It blends Personalized Value with major/program-level earnings and debt when available.",
    "financial_survivability": "Personalized 0-100 safety score asking: can this student realistically afford and finish this college without taking on unsafe debt? It uses yearly budget fit, debt stress, graduation rate, and estimate trust.",
    "roi_score": "0-100 payoff score compared with other rows in this dataset. It uses reported early earnings and 10-year earnings, not lifetime earnings. Higher is better.",
    "roi_index": "Raw future ROI ratio: (10-year median earnings / max(estimated 4-year cost after aid, $20,000)) * graduation rate. This is not lifetime earnings.",
    "estimated_4yr_net_cost": "Estimated total after-aid cost for four years.",
    "student_size": "Undergraduate student enrollment reported by College Scorecard.",
    "budget_gap": "Estimated yearly cost after aid minus the yearly amount your family can actually pay. Negative means under budget; positive means above budget.",
    "debt_to_earnings": "Median debt divided by median earnings after graduation. Lower is safer because early earnings can cover debt more easily.",
    "risk_label": "Plain-English financial status based on budget fit, payoff, debt, graduation rate, and data completeness.",
    "estimate_confidence": "Trust level for the app's estimate. High means stronger public cost/outcome/program evidence and a calculator link; Low means fallback data or missing key fields.",
    "net_price_calculator": "Official college net price calculator when College Scorecard reports a link. These school calculators use institutional data and should be checked before making application or enrollment decisions.",
    "admissions_category": "Rough admissions realism label using reported admission rate and, if entered, GPA/test/EC profile. This is not a personalized chance calculator. Ultra-selective schools stay reaches for everyone.",
    "academic_strength": "Rough 0-100 academic profile signal from GPA, SAT or ACT, and extracurricular strength. It only affects admissions display labels, not financial value scores.",
    "merit_aid": "Merit aid means non-need aid for freshmen without financial need, based on College Transitions' Common Data Set compilation when available. This is an opportunity signal, not a guaranteed scholarship.",
}


def normalize_search_text(value):
    value = str(value).lower()
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def acronym_for_name(value):
    stopwords = {"a", "an", "and", "at", "for", "in", "main", "of", "the"}
    tokens = [token for token in normalize_search_text(value).split() if token not in stopwords]
    return "".join(token[0] for token in tokens if token)


def estimate_roi(earnings, yearly_after_aid_cost, graduation_rate):
    if pd.isna(earnings) or pd.isna(yearly_after_aid_cost) or yearly_after_aid_cost < 0:
        return None
    estimated_4yr_cost = yearly_after_aid_cost * 4
    return (earnings / max(estimated_4yr_cost, 20000)) * graduation_rate


def get_profile_settings():
    saved_income_bracket = st.session_state.get("family_income_bracket", DEFAULT_INCOME_BRACKET)
    income_bracket = INCOME_BRACKET_ALIASES.get(saved_income_bracket, saved_income_bracket)
    if income_bracket not in INCOME_BRACKETS:
        income_bracket = DEFAULT_INCOME_BRACKET

    return {
        "home_state": st.session_state.get("home_state", "Prefer not to say"),
        "family_income_bracket": income_bracket,
        "academic_focus": st.session_state.get("academic_focus", "").strip(),
        "annual_family_budget": st.session_state.get("annual_family_budget", 0),
        "max_comfortable_debt": st.session_state.get("max_comfortable_debt", 0),
        "affordability_importance": st.session_state.get("affordability_importance", 6),
        "earnings_importance": st.session_state.get("earnings_importance", 6),
        "debt_importance": st.session_state.get("debt_importance", 5),
        "graduation_importance": st.session_state.get("graduation_importance", 5),
        "in_state_importance": st.session_state.get("in_state_importance", 0),
        "aid_uncertainty": st.session_state.get("aid_uncertainty", 5),
        "first_gen": st.session_state.get("first_gen", False),
        "unweighted_gpa": st.session_state.get("unweighted_gpa", 0.0),
        "sat_score": st.session_state.get("sat_score", 0),
        "act_score": st.session_state.get("act_score", 0),
        "ec_score": st.session_state.get("ec_score", 0),
    }


def profile_has_personalization(profile):
    return (
        profile["home_state"] != "Prefer not to say"
        or profile["family_income_bracket"] != DEFAULT_INCOME_BRACKET
        or bool(profile["academic_focus"])
        or profile["annual_family_budget"] > 0
        or profile["max_comfortable_debt"] > 0
        or profile["affordability_importance"] != 6
        or profile["earnings_importance"] != 6
        or profile["debt_importance"] != 5
        or profile["graduation_importance"] != 5
        or profile["in_state_importance"] != 0
        or profile["aid_uncertainty"] != 5
        or profile["first_gen"]
        or has_academic_profile(profile)
    )


def clamp_score(value):
    if pd.isna(value):
        return float("nan")
    return max(0, min(100, value))


def budget_fit_score(cost_after_aid, yearly_budget):
    if yearly_budget <= 0 or pd.isna(cost_after_aid):
        return float("nan")
    if cost_after_aid <= yearly_budget:
        return 100
    over_budget_ratio = (cost_after_aid - yearly_budget) / max(yearly_budget, 1)
    return clamp_score(100 - (over_budget_ratio * 125))


def selected_school_cost_score(cost, yearly_budget):
    if pd.isna(cost):
        return 0
    if yearly_budget <= 0:
        return clamp_score(100 - (cost / 90000 * 100))
    return budget_fit_score(cost, yearly_budget)


def debt_stress_score(median_debt, earnings_after_grad):
    ratio = debt_to_earnings_ratio(median_debt, earnings_after_grad)
    if pd.isna(ratio):
        return float("nan")
    return clamp_score(100 - (ratio * 120))


def financial_survivability_score_for_values(
    yearly_cost,
    yearly_budget,
    max_debt,
    median_debt,
    earnings_after_grad,
    graduation_rate,
    confidence_score,
    aid_uncertainty=5,
):
    if yearly_budget <= 0 or pd.isna(yearly_cost):
        return float("nan")

    budget_score = budget_fit_score(yearly_cost, yearly_budget)
    debt_score = debt_fit_score(median_debt, max_debt) if max_debt > 0 else float("nan")
    debt_stress = debt_stress_score(median_debt, earnings_after_grad)
    if pd.notna(debt_score) and pd.notna(debt_stress):
        debt_component = debt_score * 0.65 + debt_stress * 0.35
    elif pd.notna(debt_score):
        debt_component = debt_score
    elif pd.notna(debt_stress):
        debt_component = debt_stress
    else:
        debt_component = 55

    completion_component = graduation_rate * 100 if pd.notna(graduation_rate) else 55
    trust_component = confidence_score if pd.notna(confidence_score) else 55
    raw_score = (
        budget_score * 0.55
        + debt_component * 0.20
        + completion_component * 0.15
        + trust_component * 0.10
    )

    yearly_gap = yearly_cost - yearly_budget
    if yearly_gap > max(10000, yearly_budget * 0.50):
        raw_score = min(raw_score, 49)
    elif yearly_gap > max(5000, yearly_budget * 0.25):
        raw_score = min(raw_score, 64)

    uncertainty_penalty = max(0, aid_uncertainty - 5) * 1.5
    return clamp_score(raw_score - uncertainty_penalty)


def financial_survivability_label(score):
    if pd.isna(score):
        return "Add budget"
    if score >= 85:
        return "Financially safe"
    if score >= 70:
        return "Manageable"
    if score >= 50:
        return "Risky stretch"
    return "Likely unsafe"


def financial_survivability_summary(label):
    explanations = {
        "Financially safe": "Cost fits the entered budget with manageable debt/completion risk.",
        "Manageable": "Looks possible, but still verify the official calculator and aid letter.",
        "Risky stretch": "Could work only with stronger aid, lower debt, or a bigger family contribution.",
        "Likely unsafe": "The cost gap or debt risk is too high for this profile.",
        "Add budget": "Enter a yearly family budget to calculate survivability.",
    }
    return explanations.get(label, "Use this as a planning signal, not a final decision.")


def affordability_gap_penalty(data, profile):
    if profile["annual_family_budget"] <= 0 or profile["affordability_importance"] < 7:
        return pd.Series(0, index=data.index)
    over_budget_ratio = (data["annual_budget_gap"] / max(profile["annual_family_budget"], 1)).clip(lower=0)
    penalty = over_budget_ratio * 35 * (profile["affordability_importance"] / 10)
    return penalty.clip(upper=30).fillna(0)


def affordability_verdict(yearly_gap, yearly_budget):
    if yearly_budget <= 0 or pd.isna(yearly_gap):
        return "Add budget"
    if yearly_gap <= 0:
        return "Within budget"
    if yearly_gap <= max(3000, yearly_budget * 0.15):
        return "Small gap"
    if yearly_gap <= max(8000, yearly_budget * 0.40):
        return "Moderate gap"
    return "Large gap"


def selected_school_next_step(row, profile):
    if pd.isna(row.get("Official Calculator Estimate")):
        return "Run official calculator"
    if row.get("Admissions Category") in ("Extreme reach", "Reach"):
        return "Keep, but add safer admissions options"
    if row.get("Admissions Category") in ("Far reach", "Target/reach"):
        return "Balance with likelier admissions options"
    if profile["annual_family_budget"] <= 0:
        return "Add yearly budget"
    if row["Affordability Verdict"] == "Large gap":
        return "Ask aid office / find scholarships"
    if row["Affordability Verdict"] == "Moderate gap":
        return "Compare aid appeal and cheaper options"
    if profile["academic_focus"] and row.get("Focus Match") != "Matched program":
        return "Verify major outcomes manually"
    if row.get("Estimate Trust Level", row.get("Estimate Confidence")) == "Low":
        return "Verify missing data"
    return "Keep on shortlist"


def selected_schools_summary_markdown(table, profile):
    lines = [
        "# College Value Lab Shortlist",
        "",
        f"Academic focus: {profile['academic_focus'] or 'Not selected'}",
        f"Yearly budget: {money(profile['annual_family_budget']) if profile['annual_family_budget'] else 'Not entered'}",
        "",
        "| College | Status | Decision | Cost Used | Verdict | Next Step |",
        "|---|---:|---:|---:|---|---|",
    ]
    for _, row in table.iterrows():
        lines.append(
            "| "
            f"{row['College']} | {row['Status']} | {number(row['Decision Score'])} | "
            f"{money(row['Cost Used In Decision'])} | {row['Affordability Verdict']} | {row['Next Step']} |"
        )
    lines.extend(
        [
            "",
            "Note: Official calculator estimates, when entered, are school-specific and replace the public-data cost inside Decision Score.",
        ]
    )
    return "\n".join(lines)


def selected_schools_export_json(selected, profile):
    payload = {
        "app": "College Value Lab",
        "version": 1,
        "profile_snapshot": {
            "home_state": profile["home_state"],
            "family_income_bracket": profile["family_income_bracket"],
            "academic_focus": profile["academic_focus"],
            "annual_family_budget": profile["annual_family_budget"],
            "max_comfortable_debt": profile["max_comfortable_debt"],
        },
        "selected_schools": selected,
    }
    return json.dumps(payload, indent=2, default=str).encode("utf-8")


def parse_selected_schools_import(uploaded_file):
    try:
        payload = json.loads(uploaded_file.getvalue().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, "That file was not valid College Value Lab JSON."

    selected = payload.get("selected_schools") if isinstance(payload, dict) else None
    if not isinstance(selected, dict):
        return None, "The JSON file did not include a selected_schools object."
    for key, value in selected.items():
        if not isinstance(key, str) or not isinstance(value, dict) or "College" not in value:
            return None, "The selected_schools data did not match the expected format."
    return selected, None


def score_band_table():
    return pd.DataFrame(SCORE_BANDS, columns=["Score range", "Interpretation", "How to read it"])


def debt_fit_score(median_debt, max_debt):
    if max_debt <= 0 or pd.isna(median_debt):
        return float("nan")
    if median_debt <= max_debt:
        return 100
    over_debt_ratio = (median_debt - max_debt) / max(max_debt, 1)
    return clamp_score(100 - (over_debt_ratio * 70))


def home_state_score(row, home_state):
    if home_state == "Prefer not to say":
        return float("nan")
    if row["state"] == home_state and row["residency"] == "In-state":
        return 100
    if row["state"] == home_state:
        return 80
    if row["residency"] == "Out-of-state":
        return 35
    return 55


def default_component_weights():
    return {
        "current_affordability_score": 0.35,
        "future_roi_score": 0.35,
        "debt_safety_score": 0.15,
        "graduation_confidence_score": 0.15,
        "home_state_fit": 0.00,
    }


def need_value_weights(profile):
    if not profile_has_personalization(profile):
        return default_component_weights()

    affordability = profile["affordability_importance"]
    earnings = profile["earnings_importance"]
    debt = profile["debt_importance"]
    graduation = profile["graduation_importance"]
    in_state = profile["in_state_importance"]
    aid_uncertainty = profile["aid_uncertainty"]

    raw_weights = {
        "current_affordability_score": affordability + (aid_uncertainty * 0.5),
        "future_roi_score": earnings,
        "debt_safety_score": debt + (aid_uncertainty * 0.3),
        "graduation_confidence_score": graduation + (3 if profile["first_gen"] else 0),
        "home_state_fit": in_state if profile["home_state"] != "Prefer not to say" else 0,
    }
    total = sum(raw_weights.values())
    if total <= 0:
        return default_component_weights()
    return {key: value / total for key, value in raw_weights.items()}


def weighted_score(row, weights):
    total = 0
    used_weight = 0
    for column, weight in weights.items():
        value = row[column]
        if pd.notna(value) and weight > 0:
            total += value * weight
            used_weight += weight
    if used_weight == 0:
        return float("nan")
    return total / used_weight


def describe_score_mode(profile):
    if not profile_has_personalization(profile):
        return "Public score: using the default need-value formula."
    parts = [
        "Personalized score",
        f"current affordability {profile['affordability_importance']}/10",
        f"future ROI/earnings {profile['earnings_importance']}/10",
        f"debt concern {profile['debt_importance']}/10",
    ]
    if profile["annual_family_budget"] > 0:
        parts.append(f"yearly budget {money(profile['annual_family_budget'])}")
    if profile["family_income_bracket"] != DEFAULT_INCOME_BRACKET:
        parts.append(f"income bracket {profile['family_income_bracket']}")
    if profile["academic_focus"]:
        parts.append(f"academic focus {profile['academic_focus']}")
    if profile["max_comfortable_debt"] > 0:
        parts.append(f"max debt {money(profile['max_comfortable_debt'])}")
    if profile["home_state"] != "Prefer not to say":
        parts.append(f"home state {profile['home_state']}")
    if profile["first_gen"]:
        parts.append("first-generation support emphasized")
    if has_academic_profile(profile):
        parts.append(f"academic profile signal {number(academic_strength_score(profile))}/100")
    return "; ".join(parts) + "."


def percentile(series, higher_is_better=True):
    ranked = series.rank(pct=True) * 100
    if higher_is_better:
        return ranked
    return 100 - ranked


def add_need_value_score(data, profile=None):
    profile = profile or get_profile_settings()
    data = data.copy()
    data["earnings_after_grad"] = data["median_earnings_1yr_after_completion"]
    for fallback_column in [
        "median_earnings_4yr_after_completion",
        "median_earnings_5yr_after_completion",
        "median_earnings_6yr_after_entry",
        "median_earnings_10yr",
    ]:
        data["earnings_after_grad"] = data["earnings_after_grad"].fillna(data[fallback_column])

    data["earnings_10yr_used"] = data["median_earnings_10yr"]
    for fallback_column in [
        "median_earnings_6yr_after_entry",
        "median_earnings_5yr_after_completion",
        "median_earnings_4yr_after_completion",
        "median_earnings_1yr_after_completion",
    ]:
        data["earnings_10yr_used"] = data["earnings_10yr_used"].fillna(data[fallback_column])

    data["selected_earnings"] = data["earnings_10yr_used"]
    data["roi_index"] = data.apply(
        lambda row: estimate_roi(row["earnings_10yr_used"], row["cost_after_aid"], row["graduation_rate"]),
        axis=1,
    )
    data["early_roi_index"] = data.apply(
        lambda row: estimate_roi(row["earnings_after_grad"], row["cost_after_aid"], row["graduation_rate"]),
        axis=1,
    )

    data["roi_percentile"] = percentile(data["roi_index"])
    data["roi_score"] = data["roi_percentile"]
    data["roi_rating"] = data["roi_score"].apply(roi_rating)
    data["early_roi_percentile"] = percentile(data["early_roi_index"])
    data["earnings_10yr_percentile"] = percentile(data["earnings_10yr_used"])
    data["earnings_after_grad_percentile"] = percentile(data["earnings_after_grad"])
    data["affordability_percentile"] = percentile(data["cost_after_aid"], higher_is_better=False)
    data["low_debt_percentile"] = percentile(data["median_debt"], higher_is_better=False)
    data["graduation_percent"] = data["graduation_rate"] * 100
    data["budget_fit"] = data["cost_after_aid"].apply(
        lambda value: budget_fit_score(value, profile["annual_family_budget"])
    )
    data["debt_fit"] = data["median_debt"].apply(
        lambda value: debt_fit_score(value, profile["max_comfortable_debt"])
    )
    data["home_state_fit"] = data.apply(
        lambda row: home_state_score(row, profile["home_state"]),
        axis=1,
    )

    data["future_roi_score"] = (
        data["earnings_10yr_percentile"] * 0.45
        + data["roi_percentile"] * 0.30
        + data["earnings_after_grad_percentile"] * 0.10
        + data["early_roi_percentile"] * 0.05
        + data["graduation_percent"] * 0.10
    )
    if profile["annual_family_budget"] > 0:
        data["current_affordability_score"] = (
            data["budget_fit"] * 0.75
            + data["affordability_percentile"] * 0.15
            + data["low_debt_percentile"] * 0.10
        )
    else:
        data["current_affordability_score"] = (
            data["affordability_percentile"] * 0.75
            + data["low_debt_percentile"] * 0.25
        )
    if profile["max_comfortable_debt"] > 0:
        data["debt_safety_score"] = data["debt_fit"] * 0.60 + data["low_debt_percentile"] * 0.40
    else:
        data["debt_safety_score"] = data["low_debt_percentile"]
    data["graduation_confidence_score"] = data["graduation_percent"]
    coverage_columns = [
        "cost_after_aid",
        "earnings_after_grad",
        "earnings_10yr_used",
        "graduation_rate",
        "on_time_completion_rate",
        "median_debt",
    ]
    data["data_coverage"] = data[coverage_columns].notna().mean(axis=1) * 100

    weights = need_value_weights(profile)
    data["need_value_score"] = data.apply(lambda row: weighted_score(row, weights), axis=1)
    data["score_mode"] = describe_score_mode(profile)
    data["annual_budget_gap"] = data["cost_after_aid"].apply(
        lambda value: annual_budget_gap(value, profile["annual_family_budget"])
    )
    data["four_year_budget_gap"] = data["cost_after_aid"].apply(
        lambda value: four_year_budget_gap(value, profile["annual_family_budget"])
    )
    data["affordability_gap_penalty"] = affordability_gap_penalty(data, profile)
    if profile["annual_family_budget"] > 0 and profile["affordability_importance"] >= 9:
        data["need_value_score"] = (
            data["need_value_score"] - (data["affordability_gap_penalty"] * 0.35)
        ).apply(clamp_score)
    data["debt_to_earnings_after_grad"] = data.apply(
        lambda row: debt_to_earnings_ratio(row["median_debt"], row["earnings_after_grad"]),
        axis=1,
    )
    data["debt_to_earnings_10yr"] = data.apply(
        lambda row: debt_to_earnings_ratio(row["median_debt"], row["earnings_10yr_used"]),
        axis=1,
    )
    data["debt_safety_label"] = data["debt_to_earnings_after_grad"].apply(debt_safety_label)
    data["admissions_selectivity"] = data["admission_rate"].apply(admissions_category)
    data["academic_strength_score"] = academic_strength_score(profile)
    data["admissions_category"] = data["admission_rate"].apply(
        lambda value: personalized_admissions_fit(value, profile)
    )
    data["risk_label"] = data.apply(lambda row: risk_label(row, profile), axis=1)
    return data


def income_adjusted_net_price(row, profile):
    income_column = INCOME_BRACKETS.get(profile["family_income_bracket"])
    if income_column == "full_cost":
        if pd.notna(row["annual_cost"]):
            return max(row["annual_cost"], 0), "full cost"
        if pd.notna(row["tuition_out_of_state"]):
            return max(row["tuition_out_of_state"], 0), "full tuition fallback"
    if income_column and income_column in row and pd.notna(row[income_column]):
        return max(row[income_column], 0), "income bracket"
    if pd.notna(row["avg_net_price"]):
        return max(row["avg_net_price"], 0), "average"
    return row["avg_net_price"], "average"


def build_cost_scenarios(data, profile=None):
    profile = profile or get_profile_settings()
    scenarios = []
    for _, row in data.iterrows():
        tuition_gap = row["tuition_out_of_state"] - row["tuition_in_state"]
        base_net_price, net_price_source = income_adjusted_net_price(row, profile)
        has_residency_split = (
            row["ownership"] == "Public"
            and pd.notna(row["tuition_in_state"])
            and pd.notna(row["tuition_out_of_state"])
            and tuition_gap > 1
        )

        base = row.to_dict()
        if has_residency_split:
            if net_price_source in ("full cost", "full tuition fallback"):
                in_state_after_aid = row["annual_cost"]
                out_state_after_aid = row["annual_cost"] + tuition_gap if pd.notna(row["annual_cost"]) else base_net_price
            else:
                in_state_after_aid = base_net_price
                out_state_after_aid = base_net_price + tuition_gap if pd.notna(base_net_price) else None
            if profile["home_state"] == "Prefer not to say":
                scenario_specs = [
                    ("In-state", row["annual_cost"], in_state_after_aid),
                    ("Out-of-state", row["annual_cost"] + tuition_gap, out_state_after_aid),
                ]
            elif row["state"] == profile["home_state"]:
                scenario_specs = [("In-state", row["annual_cost"], in_state_after_aid)]
            else:
                scenario_specs = [("Out-of-state", row["annual_cost"] + tuition_gap, out_state_after_aid)]
        else:
            scenario_specs = [("All students", row["annual_cost"], base_net_price)]

        for residency, before_aid, after_aid in scenario_specs:
            scenario = base.copy()
            scenario["residency"] = residency
            scenario["region"] = REGIONS.get(row["state"], "Other")
            scenario["display_name"] = f"{row['name']} ({residency.lower()})" if residency != "All students" else row["name"]
            scenario["cost_before_aid"] = before_aid
            scenario["cost_after_aid"] = after_aid
            scenario["net_price_source"] = net_price_source
            scenario["family_income_bracket"] = profile["family_income_bracket"]
            scenario["estimated_4yr_after_aid_cost"] = after_aid * 4 if pd.notna(after_aid) else None
            scenario["scenario_id"] = f"{row['unit_id']}-{normalize_search_text(residency)}"
            scenarios.append(scenario)

    return pd.DataFrame(scenarios)


def search_colleges(data, query, limit=None):
    clean_query = normalize_search_text(query)
    if not clean_query:
        return data.head(0)

    nickname_targets = NICKNAMES.get(clean_query, [])
    query_tokens = clean_query.split()
    scored_rows = []
    for index, row in data.iterrows():
        college_name = row["display_name"]
        clean_name = normalize_search_text(college_name)
        acronym = acronym_for_name(college_name)
        name_tokens = clean_name.split()
        phrase_similarity = difflib.SequenceMatcher(None, clean_query, clean_name).ratio()
        token_similarity = 0

        if query_tokens and name_tokens:
            token_similarity = sum(
                max(difflib.SequenceMatcher(None, query_token, name_token).ratio() for name_token in name_tokens)
                for query_token in query_tokens
            ) / len(query_tokens)
            token_coverage = 0
            for query_token in query_tokens:
                best_token_match = max(
                    difflib.SequenceMatcher(None, query_token, name_token).ratio()
                    for name_token in name_tokens
                )
                if best_token_match >= 0.8:
                    token_coverage += 1
                elif query_token == "tech" and "technology" in name_tokens:
                    token_coverage += 1
                elif query_token == "tech" and "technical" in name_tokens:
                    token_coverage += 0.4
            coverage_bonus = token_coverage / len(query_tokens)
        else:
            coverage_bonus = 0

        if clean_query in clean_name:
            score = 1 + phrase_similarity
        elif any(target in clean_name for target in nickname_targets):
            score = 1.3 + phrase_similarity
        elif len(clean_query) <= 5 and clean_query == acronym:
            score = 1.2
        else:
            score = (phrase_similarity * 0.3) + (token_similarity * 0.4) + (coverage_bonus * 0.3)

        scored_rows.append((score, index))

    best_indexes = [
        index
        for score, index in sorted(scored_rows, reverse=True)
        if score >= 0.35
    ]
    if limit is not None:
        best_indexes = best_indexes[:limit]
    return data.loc[best_indexes]


@st.cache_data(show_spinner=False)
def program_focus_matches(program_data_updated_at, focus_query):
    clean_query = normalize_search_text(focus_query)
    if not clean_query:
        return pd.DataFrame()

    program_data = load_program_data(program_data_updated_at, PROGRAM_SCHEMA_VERSION)
    if program_data.empty:
        return pd.DataFrame()

    query_tokens = clean_query.split()
    programs = program_data[program_data["credential_level"] == 3].copy()
    if programs.empty:
        return programs

    cip_prefixes = FOCUS_CIP_PREFIXES.get(clean_query)
    if cip_prefixes is None:
        for focus_name, prefixes in FOCUS_CIP_PREFIXES.items():
            if focus_name in clean_query or clean_query in focus_name:
                cip_prefixes = prefixes
                break
    if cip_prefixes:
        programs = programs[programs["cip_code"].astype(str).str.startswith(cip_prefixes, na=False)]

    title_rules = FOCUS_TITLE_RULES.get(clean_query)
    if title_rules:
        required_any = title_rules.get("required_any", ())
        blocked_any = title_rules.get("blocked_any", ())

        def title_allowed(text):
            clean_title = normalize_search_text(text)
            has_required = any(term in clean_title for term in required_any)
            has_blocked = any(term in clean_title for term in blocked_any)
            return has_required and not has_blocked

        programs = programs[programs["program_title"].apply(title_allowed)]

    def match_score(text):
        clean_title = normalize_search_text(text)
        title_tokens = clean_title.split()
        if clean_query in clean_title:
            return 1.0
        if not query_tokens or not title_tokens:
            return 0.0
        token_scores = []
        for query_token in query_tokens:
            token_scores.append(
                max(difflib.SequenceMatcher(None, query_token, title_token).ratio() for title_token in title_tokens)
            )
        return sum(token_scores) / len(token_scores)

    programs["program_match_score"] = programs["program_title"].apply(match_score)
    score_floor = 0.35 if cip_prefixes else 0.75
    if title_rules:
        score_floor = 0.20
    programs = programs[programs["program_match_score"] >= score_floor]
    if programs.empty:
        return programs

    programs["has_program_earnings"] = programs["earnings_1yr"].notna().astype(int)
    programs["has_program_debt"] = programs["program_median_debt"].notna().astype(int)
    programs = programs.sort_values(
        [
            "unit_id",
            "program_match_score",
            "has_program_earnings",
            "has_program_debt",
            "awards_latest",
        ],
        ascending=[True, False, False, False, False],
        na_position="last",
    )
    return programs.drop_duplicates("unit_id")


def add_program_focus(data, program_data_updated_at, profile):
    data = data.copy()
    default_columns = {
        "program_match": None,
        "program_match_score": None,
        "program_earnings_1yr": None,
        "program_earnings_4yr": None,
        "program_earnings_5yr": None,
        "program_national_earnings_4yr": None,
        "program_debt": None,
        "program_debt_payment": None,
        "program_debt_to_earnings": None,
        "program_awards": None,
        "program_value_score": None,
        "program_earnings_vs_school": None,
        "program_earnings_vs_school_pct": None,
        "program_earnings_vs_school_label": None,
        "program_data_points": None,
        "program_roi_index": None,
        "focus_adjusted_score": None,
        "focus_match_status": "No academic focus entered",
    }
    for column, value in default_columns.items():
        data[column] = value

    matches = program_focus_matches(program_data_updated_at, profile["academic_focus"])
    if matches.empty:
        if profile["academic_focus"]:
            data["focus_adjusted_score"] = data["need_value_score"] * 0.75
            data["focus_match_status"] = "No matching program data"
        return data

    match_columns = [
        "unit_id",
        "program_title",
        "program_match_score",
        "earnings_1yr",
        "earnings_4yr",
        "earnings_5yr",
        "national_earnings_4yr",
        "program_median_debt",
        "program_debt_payment",
        "debt_to_earnings_1yr",
        "awards_latest",
        "program_data_points",
    ]
    matches = matches[match_columns].rename(
        columns={
            "program_title": "program_match",
            "earnings_1yr": "program_earnings_1yr",
            "earnings_4yr": "program_earnings_4yr",
            "earnings_5yr": "program_earnings_5yr",
            "national_earnings_4yr": "program_national_earnings_4yr",
            "program_median_debt": "program_debt",
            "debt_to_earnings_1yr": "program_debt_to_earnings",
            "awards_latest": "program_awards",
        }
    )
    data = data.drop(columns=list(default_columns.keys())).merge(matches, on="unit_id", how="left")
    data["program_roi_index"] = data.apply(
        lambda row: estimate_roi(row["program_earnings_1yr"], row["cost_after_aid"], row["graduation_rate"]),
        axis=1,
    )
    data["program_earnings_vs_school"] = data["program_earnings_1yr"] - data["earnings_after_grad"]
    data["program_earnings_vs_school_pct"] = data["program_earnings_vs_school"] / data["earnings_after_grad"].replace(0, float("nan"))
    data["program_earnings_vs_school_label"] = data.apply(
        lambda row: major_earnings_difference_label(row["program_earnings_vs_school"], row["program_earnings_vs_school_pct"]),
        axis=1,
    )
    data["program_roi_percentile"] = percentile(data["program_roi_index"])
    data["program_earnings_percentile"] = percentile(data["program_earnings_1yr"])
    data["program_low_debt_percentile"] = percentile(data["program_debt"], higher_is_better=False)
    data["program_value_score"] = (
        data["program_roi_percentile"] * 0.55
        + data["program_earnings_percentile"] * 0.25
        + data["program_low_debt_percentile"] * 0.20
    )
    if profile["academic_focus"]:
        data["focus_adjusted_score"] = data["need_value_score"] * 0.75
        has_program_score = data["program_value_score"].notna()
        data.loc[has_program_score, "focus_adjusted_score"] = (
            data.loc[has_program_score, "need_value_score"] * 0.60
            + data.loc[has_program_score, "program_value_score"] * 0.40
        )
        if "affordability_gap_penalty" in data.columns:
            data["focus_adjusted_score"] = (
                data["focus_adjusted_score"] - data["affordability_gap_penalty"]
            ).apply(clamp_score)
        data["focus_match_status"] = "No matching program data"
        data.loc[data["program_match"].notna(), "focus_match_status"] = "Matched program"
    return data


@st.cache_data(show_spinner="Scoring colleges for this profile...")
def prepare_scenario_data(data_updated_at, program_data_updated_at, merit_data_updated_at, schema_version, program_schema_version, profile_items):
    profile = dict(profile_items)
    data = load_data(data_updated_at, schema_version, merit_data_updated_at)
    scenarios = build_cost_scenarios(data, profile)
    scenarios = add_need_value_score(scenarios, profile)
    scenarios = add_program_focus(scenarios, program_data_updated_at, profile)
    scenarios = add_estimate_confidence(scenarios, profile)
    return scenarios


def show_college_profile(row):
    st.markdown(f"#### {row['display_name']}")
    st.caption(f"{row['ownership']} · {row['city']}, {row['state']} · {row['residency']} cost scenario")

    col1, col2, col3, col4 = st.columns(4)
    profile = get_profile_settings()
    col1.metric("Yearly Estimated Cost After Aid", money(row["cost_after_aid"]), help=TOOLTIPS["cost_after_aid"])
    col2.metric("Yearly Over/Under Budget", signed_money(row["annual_budget_gap"]), help=TOOLTIPS["budget_gap"])
    col3.metric(
        "Estimated 4-Year Cost",
        money(row["cost_after_aid"] * 4) if pd.notna(row["cost_after_aid"]) else "N/A",
        help="Estimated yearly cost after aid multiplied by four. This is a planning estimate, not a bill.",
    )
    col4.metric("Earnings After Grad", money(row["earnings_after_grad"]), help="Median earnings 1 year after graduation when available.")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Earnings 10 Years Later", money(row["earnings_10yr_used"]), help="Median earnings 10 years after entry when available. This is not lifetime earnings.")
    col2.metric("Median Debt", money(row["median_debt"]), help=TOOLTIPS["median_debt"])
    col3.metric(
        "Debt / Early Earnings",
        pct(row["debt_to_earnings_after_grad"]),
        help=TOOLTIPS["debt_to_earnings"],
    )
    col4.metric("Graduation Rate", pct(row["graduation_rate"]), help=TOOLTIPS["graduation_rate"])

    plain_note(
        f"Decision labels: {row['financial_survivability_label']} financially, "
        f"{row['admissions_category']} for admissions, and {row['risk_label']} on budget/value. "
        f"{financial_survivability_summary(row['financial_survivability_label'])}"
    )
    st.caption(
        f"Trust label: {row['estimate_confidence']} confidence ({number(row['estimate_confidence_score'])}/100). "
        f"Why: {row['estimate_confidence_notes'] or 'core public fields are available.'}"
    )
    score_to_show = row["focus_adjusted_score"] if profile["academic_focus"] else row["need_value_score"]
    score_label = "Major-Adjusted Value" if profile["academic_focus"] else "Personalized Value Score"
    score_to_explain = row["focus_adjusted_score"] if profile["academic_focus"] else row["need_value_score"]
    st.caption(
        f"Score interpretation: {score_band_label(score_to_explain)}. "
        "Scores are sorting helpers; use the dollar estimates and official calculator before treating this as a final affordability answer."
    )
    if profile["academic_focus"]:
        plain_note(
            f"Major effect: because you entered {profile['academic_focus']}, this detail view shows Major-Adjusted Value when matching program data exists. "
            "Future ROI Score still uses school-wide earnings; Program Outcomes below show the major/focus-specific earnings and debt data."
        )
    else:
        plain_note(
            "Major effect: Future ROI Score uses school-wide earnings. Enter an Academic focus in Personal Profile to add major/focus-specific program data when it is available."
        )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Yearly Full Cost Before Aid", money(row["cost_before_aid"]), help=TOOLTIPS["cost_before_aid"])
    col2.metric(
        "Financial Survivability",
        number(row["financial_survivability_score"]),
        row["financial_survivability_label"],
        help=TOOLTIPS["financial_survivability"],
    )
    col3.metric(score_label, number(score_to_show), help=TOOLTIPS["focus_adjusted_score"] if profile["academic_focus"] else TOOLTIPS["need_value_score"])
    col4.metric("Future ROI Score", number(row["roi_score"]), row["roi_rating"], help=TOOLTIPS["roi_score"])

    merit_cols = st.columns(3)
    merit_cols[0].metric("Merit Aid Signal", row["merit_aid_signal"], help=TOOLTIPS["merit_aid"])
    merit_cols[1].metric("Freshmen w/o Need Getting Merit", pct(row["merit_aid_percent"] / 100) if pd.notna(row["merit_aid_percent"]) else "N/A", help=TOOLTIPS["merit_aid"])
    merit_cols[2].metric("Avg Merit Award", money(row["merit_aid_average_award"]), help=TOOLTIPS["merit_aid"])

    col4, col5, col6 = st.columns(3)
    col4.metric("Raw ROI Index", number(row["roi_index"], 2), help=TOOLTIPS["roi_index"])
    col5.metric("On-Time Completion", pct(row["on_time_completion_rate"]), help=TOOLTIPS["on_time_completion_rate"])
    col6.metric("Admissions Fit", row["admissions_category"], help=TOOLTIPS["admissions_category"])

    if has_academic_profile(profile):
        st.caption(
            f"Admissions fit uses your academic profile signal ({number(row['academic_strength_score'])}/100) "
            f"plus the school's reported admission rate. It is not a chance of admission."
        )
    plain_note(plain_english_summary(row, get_profile_settings()))
    if pd.notna(row.get("program_match")):
        st.markdown("##### Program Outcomes")
        st.caption(
            "Program-level data is matched by 4-digit CIP field of study. Missing values usually mean the data was privacy-suppressed."
        )
        st.write(f"Matched program: **{row['program_match']}**")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric(
            "Major Earnings Difference",
            signed_money(row["program_earnings_vs_school"]),
            signed_percent(row["program_earnings_vs_school_pct"]),
            help="Matched program earnings minus this school's overall early-career earnings median. This is descriptive, not a guarantee that the major causes the difference.",
        )
        p2.metric("Program Earnings 1 Year", money(row["program_earnings_1yr"]))
        p3.metric("Program Debt", money(row["program_debt"]))
        p4.metric("Program Value", number(row["program_value_score"]), help="Within the current dataset: program ROI, program earnings, and lower program debt.")
        p5, p6, p7 = st.columns(3)
        p5.metric("Program Earnings 4 Years", money(row["program_earnings_4yr"]))
        p6.metric("National 4-Year Program Earnings", money(row["program_national_earnings_4yr"]))
        p7.metric("Recent Awards", number(row["program_awards"]), help="Recent IPEDS awards for this program field at the school.")
    elif profile["academic_focus"]:
        st.warning(
            f"Program-level data unavailable for {profile['academic_focus']} at this school. "
            "That does not prove the major is bad; it means the public field-of-study data is missing, suppressed, or did not match cleanly."
        )
    st.markdown("##### Calculator Companion")
    calculator_url = clean_url(row.get("net_price_calculator_url"))
    if calculator_url:
        st.markdown(
            f"[Open the official net price calculator for {markdown_safe(row['name'])}]({calculator_url})"
        )
        st.caption(
            "Use this app to decide which schools deserve deeper research. Use the college's official calculator before making a final cost judgment."
        )
    else:
        search_url = "https://collegecost.ed.gov/net-price"
        st.markdown(f"[Search the federal Net Price Calculator Center]({search_url})")
        st.caption(
            "College Scorecard did not provide a calculator URL for this row. The federal calculator center may still have one."
        )
    st.caption(f"Data coverage for this row: {number(row['data_coverage'])}% of core fields available.")
    plain_caption(row["score_mode"])

    missing_items = [
        missing_reason(row.get("cost_after_aid"), "Estimated cost after aid"),
        missing_reason(row.get("earnings_after_grad"), "Earnings after graduation"),
        missing_reason(row.get("earnings_10yr_used"), "Earnings 10 years later"),
        missing_reason(row.get("graduation_rate"), "Graduation rate"),
        missing_reason(row.get("on_time_completion_rate"), "On-time completion"),
        missing_reason(row.get("median_debt"), "Median debt"),
    ]
    missing_items = [item for item in missing_items if item]
    if missing_items:
        with st.expander("Missing public data"):
            for item in missing_items:
                st.write(f"- {item}")

    if profile_has_personalization(profile):
        with st.expander("Why this score looks this way"):
            cols = st.columns(4)
            cols[0].metric("Future ROI", number(row["future_roi_score"]), help="Blends 10-year earnings, earnings after graduation, ROI ratio, and graduation rate.")
            cols[1].metric("Current Affordability", number(row["current_affordability_score"]), help="Blends estimated cost after aid, budget fit, and debt.")
            cols[2].metric("Debt Safety", number(row["debt_safety_score"]), help="Higher means lower debt and better fit with your debt comfort level.")
            cols[3].metric("Graduation Confidence", number(row["graduation_confidence_score"]), help="Based on graduation rate.")
            st.write(
                "The personalized score does not estimate your actual financial-aid offer. "
                "It reweights public College Scorecard outcomes around the limits you entered."
            )


def show_selected_college(data):
    selected_id = st.session_state.get("selected_college_id")
    if selected_id in set(data["scenario_id"]):
        selected_row = data[data["scenario_id"] == selected_id].iloc[0]
        show_college_profile(selected_row)

        if st.button("Add to selected schools", key=f"add_{selected_id}"):
            add_selected_school(selected_row)

        st.markdown("##### What this means")
        yearly_after_aid = selected_row["cost_after_aid"]
        four_year_after_aid = selected_row["estimated_4yr_after_aid_cost"]
        earnings_after_grad = selected_row["earnings_after_grad"]
        earnings_10yr = selected_row["earnings_10yr_used"]
        median_debt = selected_row["median_debt"]
        debt_ratio = selected_row["debt_to_earnings_after_grad"]
        plain_note(
            f"For {selected_row['display_name']}, the estimated yearly cost after aid is "
            f"{money(yearly_after_aid)}, or about {money(four_year_after_aid)} over four years. "
            f"Median earnings after graduation are {money(earnings_after_grad)}, and median earnings "
            f"10 years later are {money(earnings_10yr)}. Median debt among completers is {money(median_debt)}. "
            f"Debt is about {pct(debt_ratio)} of early earnings, which this app labels as "
            f"{selected_row['debt_safety_label'].lower()}. "
            f"The graduation rate is "
            f"{pct(selected_row['graduation_rate'])}, while on-time completion is "
            f"{pct(selected_row['on_time_completion_rate'])}."
        )
        plain_markdown_text(
            "The Personalized Value Score combines earnings, cost after aid, debt, and graduation outcomes. "
            "If you filled out Personal Profile, it also adjusts around your budget, debt comfort, "
            "home state, and affordability pressure."
        )
        st.caption(
            "Score guide: 90-100 is unusually strong, 70-89 is strong, 50-69 is mixed, and below 50 needs caution or verification."
        )
        if selected_row.get("net_price_source") == "full cost":
            st.caption(
                "Cost after aid uses full annual cost because Personal Profile says not to expect need-based aid."
            )
        elif selected_row.get("net_price_source") == "income bracket":
            st.caption(
                f"Cost after aid uses College Scorecard net price for family income {selected_row['family_income_bracket']}."
            )
        else:
            st.caption("Cost after aid uses average net price because no income bracket was selected or bracket data was unavailable.")
    else:
        st.info("Select a college row from the explorer or search for a college to see detailed data here.")


def add_selected_school(row, show_message=True):
    if "selected_schools" not in st.session_state:
        st.session_state["selected_schools"] = {}
    st.session_state["selected_schools"].setdefault(
        row["scenario_id"],
        {
            "College": row["display_name"],
            "State": row["state"],
            "Status": "Considering",
            "Financial Survivability": row.get("financial_survivability_score"),
            "Survivability Label": row.get("financial_survivability_label"),
            "Personalized Value Score": round(row["need_value_score"], 0) if pd.notna(row["need_value_score"]) else None,
            "Budget/Value Status": row["risk_label"],
            "Estimated Cost After Aid": row["cost_after_aid"],
            "Yearly Over/Under Budget": row["annual_budget_gap"],
            "Future ROI Score": row["roi_score"],
            "ROI Rating": row["roi_rating"],
            "Major-Adjusted Value": row.get("focus_adjusted_score"),
            "Focus Match": row.get("focus_match_status"),
            "Estimate Trust Level": row.get("estimate_confidence"),
            "Estimate Trust Score": row.get("estimate_confidence_score"),
            "Missing Data Warning": row.get("data_warning"),
            "Admissions Category": row.get("admissions_category"),
            "Admissions Selectivity": row.get("admissions_selectivity"),
            "Calculator URL": row.get("net_price_calculator_url"),
            "Official Calculator Estimate": None,
            "Debt / Early Earnings": row["debt_to_earnings_after_grad"] * 100 if pd.notna(row["debt_to_earnings_after_grad"]) else None,
            "Program Match": row.get("program_match"),
            "Program Earnings": row.get("program_earnings_1yr"),
            "Program Debt": row.get("program_debt"),
            "Program Value": row.get("program_value_score"),
            "Major Earnings Difference": row.get("program_earnings_vs_school"),
            "Major Earnings Difference %": row.get("program_earnings_vs_school_pct") * 100 if pd.notna(row.get("program_earnings_vs_school_pct")) else None,
            "Major Earnings vs School": row.get("program_earnings_vs_school_label"),
            "Earnings After Grad": row["earnings_after_grad"],
            "Earnings 10 Years Later": row["earnings_10yr_used"],
            "Graduation Rate": row["graduation_rate"],
            "Median Debt": row["median_debt"],
            "Personal Fit": 5,
            "Notes": "",
        },
    )
    if show_message:
        st.success(f"Added {row['display_name']} to selected schools.")


def refresh_selected_school_data(selected, scenario_data):
    refreshed = {}
    scenario_lookup = scenario_data.set_index("scenario_id")
    for scenario_id, saved in selected.items():
        if scenario_id in scenario_lookup.index:
            row = scenario_lookup.loc[scenario_id]
            refreshed[scenario_id] = {
                **saved,
                "College": row["display_name"],
                "State": row["state"],
                "Financial Survivability": row.get("financial_survivability_score"),
                "Survivability Label": row.get("financial_survivability_label"),
                "Personalized Value Score": round(row["need_value_score"], 0) if pd.notna(row["need_value_score"]) else None,
                "Budget/Value Status": row["risk_label"],
                "Estimated Cost After Aid": row["cost_after_aid"],
                "Yearly Over/Under Budget": row["annual_budget_gap"],
                "Future ROI Score": row["roi_score"],
                "ROI Rating": row["roi_rating"],
                "Major-Adjusted Value": row.get("focus_adjusted_score"),
                "Focus Match": row.get("focus_match_status"),
                "Estimate Trust Level": row.get("estimate_confidence"),
                "Estimate Trust Score": row.get("estimate_confidence_score"),
                "Missing Data Warning": row.get("data_warning"),
                "Admissions Category": row.get("admissions_category"),
                "Admissions Selectivity": row.get("admissions_selectivity"),
                "Calculator URL": row.get("net_price_calculator_url"),
                "Official Calculator Estimate": saved.get("Official Calculator Estimate"),
                "Debt / Early Earnings": row["debt_to_earnings_after_grad"] * 100 if pd.notna(row["debt_to_earnings_after_grad"]) else None,
                "Program Match": row.get("program_match"),
                "Program Earnings": row.get("program_earnings_1yr"),
                "Program Debt": row.get("program_debt"),
                "Program Value": row.get("program_value_score"),
                "Major Earnings Difference": row.get("program_earnings_vs_school"),
                "Major Earnings Difference %": row.get("program_earnings_vs_school_pct") * 100 if pd.notna(row.get("program_earnings_vs_school_pct")) else None,
                "Major Earnings vs School": row.get("program_earnings_vs_school_label"),
                "Earnings After Grad": row["earnings_after_grad"],
                "Earnings 10 Years Later": row["earnings_10yr_used"],
                "Graduation Rate": row["graduation_rate"],
                "Median Debt": row["median_debt"],
            }
        else:
            refreshed[scenario_id] = saved
    return refreshed


def show_personal_profile_page():
    st.subheader("Personal Profile")
    st.caption(
        "Start here. Your profile changes cost estimates, aid assumptions, residency, major outcomes, admissions realism, budget fit, and which columns matter most in Explorer."
    )

    st.markdown("##### Quick scoring presets")
    preset_cols = st.columns(4)
    if preset_cols[0].button("Balanced", width="stretch"):
        set_profile_preset(6, 6, 5, 5, 5)
    if preset_cols[1].button("Affordability first", width="stretch"):
        set_profile_preset(10, 3, 8, 6, 8)
    if preset_cols[2].button("Future ROI first", width="stretch"):
        set_profile_preset(2, 10, 2, 4, 2)
    if preset_cols[3].button("Low debt first", width="stretch"):
        set_profile_preset(7, 4, 10, 5, 7)

    st.markdown("##### Admissions Profile")
    st.caption(
        "Optional. These inputs only change admissions realism labels like reach, target, and likely. They do not change financial scores."
    )
    admissions_cols = st.columns(4)
    st.session_state["unweighted_gpa"] = admissions_cols[0].number_input(
        "Unweighted GPA",
        min_value=0.0,
        max_value=4.0,
        value=float(st.session_state.get("unweighted_gpa", 0.0)),
        step=0.01,
        help="Use 0 if you do not want to include GPA. This is a rough signal, not an admissions prediction.",
    )
    st.session_state["sat_score"] = admissions_cols[1].number_input(
        "SAT score",
        min_value=0,
        max_value=1600,
        value=int(st.session_state.get("sat_score", 0)),
        step=10,
        help="Use 0 if not submitted or unknown. If both SAT and ACT are entered, SAT is used.",
    )
    st.session_state["act_score"] = admissions_cols[2].number_input(
        "ACT score",
        min_value=0,
        max_value=36,
        value=int(st.session_state.get("act_score", 0)),
        step=1,
        help="Use 0 if not submitted or unknown.",
    )
    st.session_state["ec_score"] = admissions_cols[3].slider(
        "EC strength",
        0,
        10,
        int(st.session_state.get("ec_score", 0)),
        help="Rough self-rating from 0 to 10 for activities, leadership, awards, work, service, projects, or responsibilities.",
    )

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["home_state"] = st.selectbox(
            "Home state",
            ["Prefer not to say"] + sorted(REGIONS.keys()),
            index=(["Prefer not to say"] + sorted(REGIONS.keys())).index(
                st.session_state.get("home_state", "Prefer not to say")
            ),
            help="Used to reward in-state public options, because those can be financially safer for many students.",
        )
        saved_income_bracket = st.session_state.get("family_income_bracket", DEFAULT_INCOME_BRACKET)
        saved_income_bracket = INCOME_BRACKET_ALIASES.get(saved_income_bracket, saved_income_bracket)
        if saved_income_bracket not in INCOME_BRACKETS:
            saved_income_bracket = DEFAULT_INCOME_BRACKET
        st.session_state["family_income_bracket"] = st.selectbox(
            "Estimated family income range",
            list(INCOME_BRACKETS.keys()),
            index=list(INCOME_BRACKETS.keys()).index(saved_income_bracket),
            help="Used to estimate yearly cost after aid. Choose the no-need-aid option if your family is unlikely to receive need-based aid; expensive private schools will then show full annual cost.",
        )
        if st.session_state["family_income_bracket"] == NO_NEED_AID_BRACKET:
            st.caption(
                "This mode assumes little or no need-based aid. Cost after aid uses full annual cost before grants, scholarships, or merit aid."
            )
        st.session_state["annual_family_budget"] = st.number_input(
            "Yearly amount your family can actually pay",
            min_value=0,
            max_value=150000,
            value=st.session_state.get("annual_family_budget", 0),
            step=1000,
            help="This is not family income. It is the yearly amount available for college from savings, current income, or family support before loans.",
        )
        st.caption(
            "Important: family income estimates aid; yearly amount your family can pay determines whether a college is within budget."
        )
        st.session_state["max_comfortable_debt"] = st.number_input(
            "Maximum total debt you would feel comfortable taking",
            min_value=0,
            max_value=300000,
            value=st.session_state.get("max_comfortable_debt", 0),
            step=2500,
            help="Used to reward colleges where median debt is under or near your comfort level.",
        )
        saved_focus = st.session_state.get("academic_focus", "")
        default_focus = saved_focus if saved_focus in COMMON_ACADEMIC_FOCUSES else "Custom"
        focus_options = COMMON_ACADEMIC_FOCUSES + ["Custom"]
        selected_focus = st.selectbox(
            "Academic focus or major",
            focus_options,
            index=focus_options.index(default_focus),
            format_func=lambda value: "No focus selected" if value == "" else value.title(),
            help="Common focuses use faster, cleaner program-code matching. Choose Custom only if your interest is not listed.",
        )
        if selected_focus == "Custom":
            st.session_state["academic_focus"] = st.text_input(
                "Custom academic focus",
                value=saved_focus if saved_focus not in COMMON_ACADEMIC_FOCUSES else "",
                placeholder="Try finance, architecture, public health...",
                help="Custom focus uses fuzzy matching, which can be slower and less precise than listed focuses.",
            )
        else:
            st.session_state["academic_focus"] = selected_focus

    with col2:
        st.session_state["first_gen"] = st.checkbox(
            "First-generation college student",
            value=st.session_state.get("first_gen", False),
            help="Raises the weight on graduation rate because completion support can matter more when navigating college without family experience.",
        )
        st.session_state["in_state_importance"] = st.slider(
            "How much do you prefer in-state options?",
            0,
            10,
            st.session_state.get("in_state_importance", 0),
            help="Only affects the score when you choose a home state.",
        )

    st.markdown("##### What should matter most?")
    slider_col1, slider_col2 = st.columns(2)
    with slider_col1:
        st.session_state["affordability_importance"] = st.slider(
            "Current affordability importance",
            0,
            10,
            st.session_state.get("affordability_importance", 6),
            help="Higher values put more weight on whether the college is affordable now: after-aid cost and budget fit.",
        )
        st.session_state["debt_importance"] = st.slider(
            "Debt concern",
            0,
            10,
            st.session_state.get("debt_importance", 5),
            help="Higher values put more weight on lower student debt and your debt comfort limit.",
        )
        st.session_state["aid_uncertainty"] = st.slider(
            "Aid uncertainty",
            0,
            10,
            st.session_state.get("aid_uncertainty", 5),
            help="Higher values make the score more conservative about cost and debt.",
        )
    with slider_col2:
        st.session_state["earnings_importance"] = st.slider(
            "Future ROI / earnings importance",
            0,
            10,
            st.session_state.get("earnings_importance", 6),
            help="Higher values put more weight on long-term payoff: earnings relative to cost.",
        )
        st.session_state["graduation_importance"] = st.slider(
            "Graduation support importance",
            0,
            10,
            st.session_state.get("graduation_importance", 5),
            help="Higher values put more weight on graduation rate.",
        )

    profile = get_profile_settings()
    weights = need_value_weights(profile)
    st.markdown("##### Current score recipe")
    plain_note(
        "Profile logic: family income estimates aid, the yearly amount your family can actually pay decides budget fit, "
        "and debt comfort decides debt safety. These are separate because a high-income family may still have a low college budget, "
        "or may be able to pay full cost without need-based aid."
    )
    st.write(describe_score_mode(profile))
    if has_academic_profile(profile):
        st.metric(
            "Academic Profile Signal",
            number(academic_strength_score(profile)),
            help=TOOLTIPS["academic_strength"],
        )
        st.caption(
            "Admissions labels are intentionally conservative. For example, ultra-selective colleges remain reaches even for excellent applicants."
        )

    weights_table = pd.DataFrame(
        [
            ("Current affordability", weights["current_affordability_score"]),
            ("Future ROI / earnings", weights["future_roi_score"]),
            ("Debt safety", weights["debt_safety_score"]),
            ("Graduation confidence", weights["graduation_confidence_score"]),
            ("Home-state fit", weights["home_state_fit"]),
        ],
        columns=["Factor", "Weight"],
    )
    weights_table["Weight"] = weights_table["Weight"] * 100
    st.dataframe(
        weights_table,
        width="stretch",
        hide_index=True,
        column_config={
            "Weight": st.column_config.ProgressColumn("Weight", format="%.0f%%", min_value=0, max_value=100)
        },
    )
    st.caption(
        "This is not a financial-aid estimator. With a yearly budget entered, current affordability is mostly budget fit, not generic cheapness."
    )


def show_what_if_simulator(selected_table, profile):
    st.markdown("##### What-if Simulator")
    with st.expander("Test scholarship, budget, or debt changes", expanded=False):
        st.caption(
            "Use this to answer questions like: what if this school gives me another grant, or what if my family can pay a little more?"
        )
        col1, col2, col3 = st.columns(3)
        temp_budget = col1.number_input(
            "Temporary yearly family budget",
            min_value=0,
            max_value=150000,
            value=int(profile["annual_family_budget"]),
            step=1000,
            help="Try a different yearly amount your family can pay without changing Personal Profile.",
        )
        extra_scholarship = col2.number_input(
            "Extra yearly grant/scholarship",
            min_value=0,
            max_value=100000,
            value=0,
            step=1000,
            help="Subtracts this amount from each selected school's yearly cost.",
        )
        temp_debt_limit = col3.number_input(
            "Temporary max total debt comfort",
            min_value=0,
            max_value=300000,
            value=int(profile["max_comfortable_debt"]),
            step=2500,
            help="Try a different total debt limit without changing Personal Profile.",
        )

        sim = selected_table.copy()
        sim["Simulated Yearly Cost"] = (
            pd.to_numeric(sim["Cost Used In Decision"], errors="coerce") - extra_scholarship
        ).clip(lower=0)
        sim["Simulated Yearly Over/Under Budget"] = sim["Simulated Yearly Cost"] - temp_budget
        if temp_budget <= 0:
            sim["Simulated Yearly Over/Under Budget"] = None
        sim["Simulated Survivability"] = sim.apply(
            lambda row: financial_survivability_score_for_values(
                row["Simulated Yearly Cost"],
                temp_budget,
                temp_debt_limit,
                row.get("Median Debt"),
                row.get("Earnings After Grad"),
                row.get("Graduation Rate"),
                row.get("Estimate Trust Score"),
                profile["aid_uncertainty"],
            ),
            axis=1,
        )
        sim["Simulated Label"] = sim["Simulated Survivability"].apply(financial_survivability_label)
        sim = sim.sort_values("Simulated Survivability", ascending=False, na_position="last")
        st.dataframe(
            sim[
                [
                    "College",
                    "Simulated Label",
                    "Simulated Survivability",
                    "Simulated Yearly Cost",
                    "Simulated Yearly Over/Under Budget",
                    "Cost Used In Decision",
                ]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "Simulated Survivability": st.column_config.ProgressColumn(
                    "Simulated Survivability (0-100)",
                    min_value=0,
                    max_value=100,
                    format="%.0f",
                    help=TOOLTIPS["financial_survivability"],
                ),
                "Simulated Yearly Cost": st.column_config.NumberColumn(format="$%d"),
                "Simulated Yearly Over/Under Budget": st.column_config.NumberColumn(format="$%d"),
                "Cost Used In Decision": st.column_config.NumberColumn(
                    "Original Yearly Cost Used",
                    format="$%d",
                ),
            },
        )


def balanced_shortlist_warnings(selected_table, profile):
    warning_rows = []
    school_count = len(selected_table)
    if school_count == 0:
        return

    reach_labels = ["Extreme reach", "Far reach", "Reach", "Target/reach"]
    realistic_labels = ["Target", "Likely", "Selective", "Moderately selective", "Less selective"]
    reach_count = int(selected_table["Admissions Category"].isin(reach_labels).sum())
    realistic_count = int(selected_table["Admissions Category"].isin(realistic_labels).sum())
    within_budget_count = int((selected_table["Affordability Verdict"] == "Within budget").sum())
    risky_cost_count = int(selected_table["Survivability Label"].isin(["Risky stretch", "Likely unsafe"]).sum())
    calculator_count = int(selected_table["Official Calculator Estimate"].notna().sum())
    low_trust_count = int(selected_table["Estimate Trust Level"].eq("Low").sum())
    focus_unmatched_count = 0
    if profile["academic_focus"] and "Focus Match" in selected_table.columns:
        focus_unmatched_count = int(selected_table["Focus Match"].ne("Matched program").sum())

    if school_count < 5:
        warning_rows.append((
            "List is still small",
            f"You have {school_count} school(s). A useful shortlist usually needs more options before comparing tradeoffs.",
            "Add a few financial safeties, realistic options, and reach schools before trusting the ranking.",
        ))
    if school_count >= 3 and reach_count / school_count >= 0.70:
        warning_rows.append((
            "Too reach-heavy",
            f"{reach_count} of {school_count} selected schools are reach or extreme-reach schools by admission rate.",
            "Keep them if you like them, but add less selective schools that are also financially survivable.",
        ))
    if school_count >= 3 and realistic_count == 0:
        warning_rows.append((
            "No admissions balance",
            "Every selected school is currently categorized as a reach-type school or missing admissions data.",
            "Add schools with more realistic admission rates so the list is not only aspirational.",
        ))
    if profile["annual_family_budget"] > 0 and within_budget_count == 0:
        warning_rows.append((
            "No clear budget fit",
            "None of the selected schools are currently within the yearly family budget.",
            "Run official calculators, then add at least one school that fits without a major aid surprise.",
        ))
    if profile["annual_family_budget"] > 0 and school_count >= 3 and risky_cost_count / school_count >= 0.50:
        warning_rows.append((
            "Financial risk is high",
            f"{risky_cost_count} of {school_count} selected schools are risky stretches or likely unsafe for this budget.",
            "Use the what-if simulator, compare lower-cost schools, and do not rely on uncertain scholarships.",
        ))
    if calculator_count == 0:
        warning_rows.append((
            "Official calculator step missing",
            "No selected school has an official net price calculator estimate entered yet.",
            "Run calculators for your top schools and enter the yearly result so the comparison gets more trustworthy.",
        ))
    if low_trust_count > 0:
        warning_rows.append((
            "Some estimates are low confidence",
            f"{low_trust_count} selected school(s) have low public-data confidence.",
            "Treat those rows as research leads, not final answers.",
        ))
    if focus_unmatched_count > 0:
        warning_rows.append((
            "Major data gaps",
            f"{focus_unmatched_count} selected school(s) do not have a clean public program match for {profile['academic_focus']}.",
            "Check department outcomes, career reports, and program pages manually before trusting the major-adjusted score.",
        ))

    if warning_rows:
        st.markdown("##### Shortlist Health Check")
        for title, issue, action in warning_rows:
            st.warning(f"**{title}:** {issue} **Next move:** {action}")
    else:
        st.success(
            "Shortlist health check: this list has a healthier mix of admissions realism, affordability, calculator progress, and data quality."
        )


def show_selected_schools_page(scenario_data):
    st.subheader("Selected Schools")
    selected = st.session_state.get("selected_schools", {})
    profile = get_profile_settings()
    show_budget_gap = profile["annual_family_budget"] > 0

    if not selected:
        st.info("No schools selected yet. Go to Explorer, choose a college, and click Add to selected schools.")
        with st.expander("Restore a saved shortlist"):
            uploaded_shortlist = st.file_uploader(
                "Upload College Value Lab shortlist JSON",
                type=["json"],
                help="Upload the JSON file created from a previous Selected Schools page.",
                key="empty_shortlist_restore",
            )
            if uploaded_shortlist is not None:
                imported, error = parse_selected_schools_import(uploaded_shortlist)
                if error:
                    st.error(error)
                elif st.button("Restore uploaded shortlist", width="stretch", key="empty_restore_button"):
                    st.session_state["selected_schools"] = imported
                    st.success("Restored selected schools from JSON.")
                    st.rerun()
        return

    selected = refresh_selected_school_data(selected, scenario_data)
    st.session_state["selected_schools"] = selected
    selected_table = pd.DataFrame(selected.values())
    if "Personal Fit" not in selected_table.columns:
        selected_table["Personal Fit"] = 5
    if "Score Mode" in selected_table.columns:
        selected_table = selected_table.drop(columns=["Score Mode"])
    if "Cost After Aid" in selected_table.columns and "Estimated Cost After Aid" not in selected_table.columns:
        selected_table = selected_table.rename(columns={"Cost After Aid": "Estimated Cost After Aid"})
    if "Budget Gap / Year" in selected_table.columns and "Yearly Budget Gap" not in selected_table.columns:
        selected_table = selected_table.rename(columns={"Budget Gap / Year": "Yearly Budget Gap"})
    rename_for_clarity = {
        "Financial Signal": "Budget/Value Status",
        "Yearly Budget Gap": "Yearly Over/Under Budget",
        "ROI Score": "Future ROI Score",
        "Focus-Adjusted Score": "Major-Adjusted Value",
        "Estimate Confidence": "Estimate Trust Level",
        "Data Warning": "Missing Data Warning",
        "Need Value Score": "Personalized Value Score",
    }
    for old_name, new_name in rename_for_clarity.items():
        if old_name in selected_table.columns and new_name not in selected_table.columns:
            selected_table = selected_table.rename(columns={old_name: new_name})
    if "Median Earnings" in selected_table.columns and "Earnings 10 Years Later" not in selected_table.columns:
        selected_table = selected_table.rename(columns={"Median Earnings": "Earnings 10 Years Later"})
    if "Earnings After Grad" not in selected_table.columns:
        selected_table["Earnings After Grad"] = None
    if "Budget/Value Status" not in selected_table.columns:
        selected_table["Budget/Value Status"] = "Not calculated"
    if "Financial Survivability" not in selected_table.columns:
        selected_table["Financial Survivability"] = None
    if "Survivability Label" not in selected_table.columns:
        selected_table["Survivability Label"] = "Add budget"
    if "Yearly Over/Under Budget" not in selected_table.columns:
        selected_table["Yearly Over/Under Budget"] = None
    if "Future ROI Score" not in selected_table.columns:
        selected_table["Future ROI Score"] = None
    if "ROI Rating" not in selected_table.columns:
        selected_table["ROI Rating"] = "No ROI data"
    if "Major-Adjusted Value" not in selected_table.columns:
        selected_table["Major-Adjusted Value"] = None
    if "Focus Match" not in selected_table.columns:
        selected_table["Focus Match"] = "No academic focus entered"
    if "Estimate Trust Level" not in selected_table.columns:
        selected_table["Estimate Trust Level"] = "Not calculated"
    if "Estimate Trust Score" not in selected_table.columns:
        selected_table["Estimate Trust Score"] = selected_table["Estimate Trust Level"].map(
            {"High": 85, "Medium": 65, "Low": 35}
        )
    selected_table["Estimate Trust Score"] = pd.to_numeric(
        selected_table["Estimate Trust Score"], errors="coerce"
    )
    if "Missing Data Warning" not in selected_table.columns:
        selected_table["Missing Data Warning"] = "Enough public data"
    if "Admissions Category" not in selected_table.columns:
        selected_table["Admissions Category"] = "Admissions data unavailable"
    if "Admissions Selectivity" not in selected_table.columns:
        selected_table["Admissions Selectivity"] = selected_table["Admissions Category"]
    if "Calculator URL" not in selected_table.columns:
        selected_table["Calculator URL"] = None
    if "Official Calculator Estimate" not in selected_table.columns:
        selected_table["Official Calculator Estimate"] = None
    if "Debt / Early Earnings" not in selected_table.columns:
        selected_table["Debt / Early Earnings"] = None
    if "Median Debt" not in selected_table.columns:
        selected_table["Median Debt"] = None
    if "Graduation Rate" not in selected_table.columns:
        selected_table["Graduation Rate"] = None
    selected_table["Earnings After Grad"] = pd.to_numeric(
        selected_table["Earnings After Grad"], errors="coerce"
    )
    selected_table["Graduation Rate"] = pd.to_numeric(
        selected_table["Graduation Rate"], errors="coerce"
    )
    for column in ["Program Match", "Program Earnings", "Program Debt", "Program Value", "Major Earnings Difference", "Major Earnings Difference %", "Major Earnings vs School"]:
        if column not in selected_table.columns:
            selected_table[column] = None
    if "Personalized Value Score" not in selected_table.columns:
        selected_table["Personalized Value Score"] = None
    score_for_decision = selected_table["Personalized Value Score"]
    if profile["academic_focus"]:
        score_for_decision = selected_table["Major-Adjusted Value"].fillna(selected_table["Personalized Value Score"])
    official_calculator_cost = pd.to_numeric(selected_table["Official Calculator Estimate"], errors="coerce")
    public_estimated_cost = pd.to_numeric(selected_table["Estimated Cost After Aid"], errors="coerce")
    selected_table["Cost Used In Decision"] = official_calculator_cost.fillna(public_estimated_cost)
    selected_table["Yearly Gap Using Calculator"] = selected_table["Cost Used In Decision"] - profile["annual_family_budget"]
    if profile["annual_family_budget"] <= 0:
        selected_table["Yearly Gap Using Calculator"] = None
    selected_table["Four-Year Gap"] = selected_table["Yearly Gap Using Calculator"] * 4
    selected_table["Affordability Verdict"] = selected_table["Yearly Gap Using Calculator"].apply(
        lambda value: affordability_verdict(value, profile["annual_family_budget"])
    )
    selected_table["Calculator Cost Score"] = selected_table["Cost Used In Decision"].apply(
        lambda value: selected_school_cost_score(value, profile["annual_family_budget"])
    )
    selected_table["Median Debt"] = pd.to_numeric(selected_table["Median Debt"], errors="coerce")
    estimated_debt = (
        pd.to_numeric(selected_table["Debt / Early Earnings"], errors="coerce")
        / 100
        * pd.to_numeric(selected_table["Earnings After Grad"], errors="coerce")
    )
    selected_table["Median Debt"] = selected_table["Median Debt"].fillna(estimated_debt)
    selected_table["Financial Survivability"] = selected_table.apply(
        lambda row: financial_survivability_score_for_values(
            row["Cost Used In Decision"],
            profile["annual_family_budget"],
            profile["max_comfortable_debt"],
            row.get("Median Debt"),
            row.get("Earnings After Grad"),
            row.get("Graduation Rate"),
            row.get("Estimate Trust Score"),
            profile["aid_uncertainty"],
        ),
        axis=1,
    )
    selected_table["Survivability Label"] = selected_table["Financial Survivability"].apply(
        financial_survivability_label
    )
    has_official_cost = official_calculator_cost.notna()
    selected_table["Decision Score"] = score_for_decision.fillna(0) * 0.70 + selected_table["Personal Fit"].fillna(0) * 10 * 0.30
    selected_table.loc[has_official_cost, "Decision Score"] = (
        score_for_decision[has_official_cost].fillna(0) * 0.50
        + selected_table.loc[has_official_cost, "Calculator Cost Score"].fillna(0) * 0.30
        + selected_table.loc[has_official_cost, "Personal Fit"].fillna(0) * 10 * 0.20
    )
    selected_table["Next Step"] = selected_table.apply(
        lambda row: selected_school_next_step(row, profile),
        axis=1,
    )
    selected_table = selected_table.sort_values("Decision Score", ascending=False)

    best_survival = selected_table.sort_values("Financial Survivability", ascending=False, na_position="last").iloc[0]
    lowest_cost = selected_table.sort_values("Estimated Cost After Aid", ascending=True, na_position="last").iloc[0]
    best_fit = selected_table.sort_values("Personal Fit", ascending=False, na_position="last").iloc[0]
    if show_budget_gap and selected_table["Yearly Gap Using Calculator"].notna().any():
        best_budget_fit = selected_table.sort_values("Yearly Gap Using Calculator", ascending=True, na_position="last").iloc[0]
    else:
        best_budget_fit = lowest_cost
    calculators_needed = int(selected_table["Official Calculator Estimate"].isna().sum())
    within_budget = int((selected_table["Affordability Verdict"] == "Within budget").sum())
    if profile["academic_focus"] and selected_table["Major-Adjusted Value"].notna().any():
        best_focus = selected_table.sort_values("Major-Adjusted Value", ascending=False, na_position="last").iloc[0]
        summary_cols = st.columns(5)
        with summary_cols[4]:
            summary_card(
                "Best For Focus",
                best_focus["College"],
                f"Major-adjusted value: {number(best_focus['Major-Adjusted Value'])}",
                "Highest major-adjusted value score in your selected list.",
            )
    else:
        summary_cols = st.columns(4)
    with summary_cols[0]:
        summary_card(
            "Safest Financial Fit",
            best_survival["College"],
            f"{best_survival['Survivability Label']} · cost used: {money(best_survival['Cost Used In Decision'])}",
            "Strongest mix of budget fit, debt stress, graduation rate, and estimate trust in your selected list.",
        )
    with summary_cols[1]:
        summary_card(
            "Best Budget Fit",
            best_budget_fit["College"],
            f"Yearly gap: {signed_money(best_budget_fit['Yearly Gap Using Calculator'])}" if show_budget_gap else f"Yearly estimate: {money(best_budget_fit['Estimated Cost After Aid'])}",
            "Closest or most favorable fit against the yearly budget you entered.",
        )
    with summary_cols[2]:
        summary_card(
            "Lowest Estimated Cost",
            lowest_cost["College"],
            f"Yearly estimate: {money(lowest_cost['Estimated Cost After Aid'])}",
            "Lowest yearly estimated cost after aid in your selected list.",
        )
    with summary_cols[3]:
        summary_card(
            "Best Personal Fit",
            best_fit["College"],
            f"Personal fit: {int(best_fit['Personal Fit'])}/10" if pd.notna(best_fit["Personal Fit"]) else "Personal fit: N/A",
            "Highest personal fit rating you entered.",
        )
    action_cols = st.columns(2)
    action_cols[0].metric("Schools Still Needing Official Calculator", calculators_needed, help="Selected schools where you have not entered an official net price calculator result yet.")
    action_cols[1].metric("Schools Within Your Yearly Budget", within_budget, help="Selected schools at or below the yearly amount your family can actually pay, using the cost used for decisions.")

    balanced_shortlist_warnings(selected_table, profile)

    st.caption(
        "One shortlist table. Public-data columns refresh automatically; you edit only status, personal fit, official calculator estimate, and notes."
    )
    st.info(
        "You can edit only four planning fields here: Status, Personal Fit, Yearly Official Calculator Estimate, and Notes. "
        "The objective fields such as cost, scores, admissions fit, earnings, debt, and location are locked because they come from the app's data/model."
    )
    st.info(
        "After you open a school's official calculator, enter its yearly result in Yearly Official Calculator Estimate. Do not enter a four-year total. "
        "That school-specific number replaces the app's public estimate in Yearly Cost Used For Decisions."
    )
    st.caption(
        "This page leads with real yearly cost, budget gap, debt, earnings, and next steps. "
        "Scores still help sort and compare, but they should not replace the official calculator result."
    )
    if not show_budget_gap:
        st.info("Add the yearly amount your family can actually pay in Personal Profile to show Yearly Over/Under Budget.")
    show_shortlist_details = st.toggle(
        "Show detailed shortlist columns",
        value=False,
        help="Turn on for ROI, earnings, debt, program outcomes, trust level, and extra public-data fields. Off keeps the shortlist focused on decisions.",
    )
    selected_column_order = [
        "College",
        "Status",
        "Next Step",
        "Cost Used In Decision",
        "Yearly Over/Under Budget",
        "Affordability Verdict",
        "Survivability Label",
        "Admissions Category",
        "Official Calculator Estimate",
        "Personal Fit",
        "Notes",
    ]
    if show_shortlist_details:
        selected_column_order = [
            "College",
            "State",
            "Status",
            "Next Step",
            "Calculator URL",
            "Decision Score",
            "Financial Survivability",
            "Survivability Label",
            "Admissions Category",
            "Budget/Value Status",
            "Affordability Verdict",
            "Cost Used In Decision",
            "Estimated Cost After Aid",
            "Official Calculator Estimate",
            "Yearly Over/Under Budget",
            "Four-Year Gap",
            "Personal Fit",
            "Personalized Value Score",
            "Major-Adjusted Value",
            "Future ROI Score",
            "ROI Rating",
            "Earnings After Grad",
            "Earnings 10 Years Later",
            "Debt / Early Earnings",
            "Estimate Trust Level",
            "Missing Data Warning",
            "Notes",
        ]
    if not show_budget_gap:
        selected_column_order.remove("Yearly Over/Under Budget")
        if "Four-Year Gap" in selected_column_order:
            selected_column_order.remove("Four-Year Gap")
    if not profile["academic_focus"]:
        if "Major-Adjusted Value" in selected_column_order:
            selected_column_order.remove("Major-Adjusted Value")
    if selected_table["Program Match"].notna().any():
        program_columns = ["Major Earnings vs School", "Major Earnings Difference", "Major Earnings Difference %", "Program Value", "Program Match", "Focus Match", "Program Earnings", "Program Debt"]
        if show_shortlist_details:
            insertion_index = selected_column_order.index("Future ROI Score") if "Future ROI Score" in selected_column_order else len(selected_column_order) - 1
            for program_column in reversed(program_columns):
                if program_column not in selected_column_order:
                    selected_column_order.insert(insertion_index, program_column)
            if not profile["academic_focus"] and "Focus Match" in selected_column_order:
                selected_column_order.remove("Focus Match")

    edited = st.data_editor(
        selected_table,
        width="stretch",
        hide_index=True,
        column_order=selected_column_order,
        disabled=[
            "College",
            "State",
            "Decision Score",
            "Financial Survivability",
            "Survivability Label",
            "Admissions Category",
            "Personalized Value Score",
            "Major-Adjusted Value",
            "Focus Match",
            "Budget/Value Status",
            "Estimate Trust Level",
            "Missing Data Warning",
            "Calculator URL",
            "Estimated Cost After Aid",
            "Cost Used In Decision",
            "Affordability Verdict",
            "Next Step",
            "Yearly Over/Under Budget",
            "Four-Year Gap",
            "Future ROI Score",
            "ROI Rating",
            "Debt / Early Earnings",
            "Program Match",
            "Program Earnings",
            "Program Debt",
            "Major Earnings vs School",
            "Major Earnings Difference",
            "Major Earnings Difference %",
            "Program Value",
            "Earnings After Grad",
            "Earnings 10 Years Later",
        ],
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=APPLICATION_STATUSES,
                required=True,
            ),
            "Decision Score": st.column_config.ProgressColumn(
                "Decision Score (0-100)",
                help="Shortlist helper. Higher is better. Before an official calculator result: 70% data score and 30% personal fit. After an official calculator result: 50% data score, 30% calculator cost fit, and 20% personal fit.",
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Financial Survivability": st.column_config.ProgressColumn(
                "Financial Survivability (0-100)",
                help=TOOLTIPS["financial_survivability"],
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Survivability Label": st.column_config.TextColumn(
                "Survivability Label",
                help="Plain-English interpretation of Financial Survivability.",
            ),
            "Admissions Category": st.column_config.TextColumn(
                "Admissions Fit",
                help=TOOLTIPS["admissions_category"],
            ),
            "Estimated Cost After Aid": st.column_config.NumberColumn("App's Yearly Estimated Cost After Aid", format="$%d", help=TOOLTIPS["cost_after_aid"]),
            "Official Calculator Estimate": st.column_config.NumberColumn(
                "Yearly Official Calculator Estimate",
                format="$%d",
                min_value=0,
                help="Optional: after running the college's official net price calculator, enter the yearly result here. Enter an annual amount, not a four-year total. Selected Schools will use it in Decision Score.",
            ),
            "Cost Used In Decision": st.column_config.NumberColumn(
                "Yearly Cost Used For Decisions",
                format="$%d",
                help="Annual cost used in Decision Score. Uses the yearly official calculator estimate when entered; otherwise uses the app's yearly public-data estimate.",
            ),
            "Affordability Verdict": st.column_config.TextColumn(
                "Budget Verdict",
                help="Budget status using Cost Used In Decision and your Personal Profile yearly budget.",
            ),
            "Next Step": st.column_config.TextColumn(
                help="Most useful next action for this school.",
            ),
            "Yearly Over/Under Budget": st.column_config.NumberColumn(
                "Yearly Over/Under Budget",
                format="$%d",
                help="Yearly Cost Used For Decisions minus the yearly amount your family can actually pay. Negative means under budget; positive means over budget.",
            ),
            "Four-Year Gap": st.column_config.NumberColumn(
                "Four-Year Over/Under Budget",
                format="$%d",
                help="Approximate four-year budget gap using Yearly Cost Used For Decisions and your yearly budget.",
            ),
            "Future ROI Score": st.column_config.ProgressColumn("Future ROI Score (0-100)", format="%.0f", min_value=0, max_value=100, help=TOOLTIPS["roi_score"]),
            "ROI Rating": st.column_config.TextColumn(help="Plain-English interpretation of ROI Score."),
            "Estimate Trust Level": st.column_config.TextColumn("Estimate Trust Level", help=TOOLTIPS["estimate_confidence"]),
            "Missing Data Warning": st.column_config.TextColumn(
                "Missing Data Warning",
                help="Plain-language warning when a row is low confidence, missing key data, or lacks program-level data for your focus."
            ),
            "Calculator URL": st.column_config.LinkColumn(
                "Official Calculator",
                help=TOOLTIPS["net_price_calculator"],
                display_text="Open calculator",
            ),
            "Debt / Early Earnings": st.column_config.NumberColumn(
                format="%.0f%%",
                help="Median debt divided by median early earnings. Lower is safer.",
            ),
            "Earnings After Grad": st.column_config.NumberColumn(format="$%d"),
            "Earnings 10 Years Later": st.column_config.NumberColumn(format="$%d"),
            "Program Earnings": st.column_config.NumberColumn(format="$%d"),
            "Program Debt": st.column_config.NumberColumn(format="$%d"),
            "Major Earnings vs School": st.column_config.TextColumn(
                help="Plain-English version of the matched major's early earnings compared with this school's overall early-career median."
            ),
            "Major Earnings Difference": st.column_config.NumberColumn(
                format="$%d",
                help="Matched major earnings minus the school's overall early-career median earnings.",
            ),
            "Major Earnings Difference %": st.column_config.NumberColumn(
                format="%.1f%%",
                help="Matched major earnings difference as a percent of the school's overall early-career median earnings.",
            ),
            "Program Value": st.column_config.ProgressColumn("Program Value (0-100)", format="%.0f", min_value=0, max_value=100),
            "Personalized Value Score": st.column_config.ProgressColumn("Personalized Value Score (0-100)", format="%.0f", min_value=0, max_value=100, help=TOOLTIPS["need_value_score"]),
            "Major-Adjusted Value": st.column_config.ProgressColumn("Major-Adjusted Value (0-100)", format="%.0f", min_value=0, max_value=100, help=TOOLTIPS["focus_adjusted_score"]),
            "Focus Match": st.column_config.TextColumn(help="Whether the selected academic focus has a matching program row."),
            "Personal Fit": st.column_config.NumberColumn(
                "Personal Fit",
                min_value=1,
                max_value=10,
                step=1,
                help="Your personal liking/fit rating from 1 to 10. This is intentionally subjective.",
            ),
            "Notes": st.column_config.TextColumn("Notes"),
        },
        num_rows="fixed",
        key="selected_schools_editor",
    )

    save_col, remove_col = st.columns([1, 1])
    with save_col:
        save_clicked = st.button("Save changes", width="stretch")

    if save_clicked:
        by_college = {row["College"]: row for row in selected.values()}
        updated = {}
        for row in edited.to_dict("records"):
            original = by_college.get(row["College"], row)
            scenario_id = next(
                (key for key, value in selected.items() if value["College"] == original["College"]),
                row["College"],
            )
            updated[scenario_id] = {
                **selected.get(scenario_id, original),
                "Status": row["Status"],
                "Personal Fit": row["Personal Fit"],
                "Official Calculator Estimate": row.get("Official Calculator Estimate"),
                "Notes": row["Notes"],
            }
        st.session_state["selected_schools"] = updated
        st.success("Saved selected-school status, personal fit, and notes for this session.")

    with remove_col:
        remove_options = list(selected.keys())
        remove_labels = {key: value["College"] for key, value in selected.items()}
        school_to_remove = st.selectbox(
            "Remove a school",
            remove_options,
            format_func=lambda key: remove_labels.get(key, key),
            key="remove_selected_school_id",
        )
        if st.button("Remove selected school", width="stretch"):
            removed_name = remove_labels.get(school_to_remove, "Selected school")
            st.session_state["selected_schools"].pop(school_to_remove, None)
            st.success(f"Removed {removed_name}.")
            st.rerun()

    show_what_if_simulator(selected_table, profile)

    st.download_button(
        "Download selected schools CSV",
        edited.to_csv(index=False).encode("utf-8"),
        "selected_schools.csv",
        "text/csv",
    )
    st.download_button(
        "Download restorable shortlist JSON",
        selected_schools_export_json(st.session_state["selected_schools"], profile),
        "college_value_lab_shortlist.json",
        "application/json",
        help="Use this file to restore your selected schools later in the same app.",
    )
    st.download_button(
        "Download counselor/family summary",
        selected_schools_summary_markdown(selected_table, profile).encode("utf-8"),
        "college_shortlist_summary.md",
        "text/markdown",
    )
    with st.expander("Restore a saved shortlist"):
        uploaded_shortlist = st.file_uploader(
            "Upload College Value Lab shortlist JSON",
            type=["json"],
            help="Upload the JSON file created by Download restorable shortlist JSON.",
        )
        if uploaded_shortlist is not None:
            imported, error = parse_selected_schools_import(uploaded_shortlist)
            if error:
                st.error(error)
            elif st.button("Restore uploaded shortlist", width="stretch"):
                st.session_state["selected_schools"] = imported
                st.success("Restored selected schools from JSON.")
                st.rerun()
    st.caption(
        "For now, progress is saved in this browser session. A real deployed version should use user accounts and a database."
    )


def show_validation_page(scenario_data):
    st.subheader("Validation Lab")
    st.caption(
        "This is where the prototype becomes credible. Pick a sample student profile, run official school calculators, "
        "and compare those results against the app's public-data estimate."
    )
    st.warning(
        "Do not mark the app as validated until someone has actually run the linked official calculators with the same sample profile."
    )

    profile = get_profile_settings()
    validation_rows = []
    for school_name in VALIDATION_SCHOOL_NAMES:
        matches = scenario_data[
            scenario_data["name"].str.lower().eq(school_name.lower())
            | scenario_data["display_name"].str.lower().str.contains(school_name.lower(), regex=False, na=False)
        ]
        if matches.empty:
            matches = search_colleges(scenario_data, school_name, limit=1)
        if matches.empty:
            continue
        preferred = matches[matches["residency"].isin(["In-state", "All students"])]
        row = preferred.iloc[0] if not preferred.empty else matches.iloc[0]
        income_column = INCOME_BRACKETS.get(profile["family_income_bracket"])
        validation_rows.append(
            {
                "College": row["display_name"],
                "State": row["state"],
                "Income Range Used": profile["family_income_bracket"],
                "App Yearly Estimate": row["cost_after_aid"],
                "Public Avg Net Price": row.get("avg_net_price"),
                "Income-Band Net Price": row.get(income_column) if income_column else None,
                "Official Calculator Result": None,
                "Difference": None,
                "Confidence": row["estimate_confidence"],
                "Why Confidence": row["estimate_confidence_notes"],
                "Calculator URL": row.get("net_price_calculator_url"),
                "Notes": "",
            }
        )

    if not validation_rows:
        st.info("No validation examples matched the current dataset.")
        return

    validation_table = pd.DataFrame(validation_rows)
    st.markdown("##### Sample validation worksheet")
    st.write(
        "Use one consistent sample profile, such as family income range, state, household size, assets, GPA, and test score. "
        "Enter each official calculator's yearly result here, then compare it with the app's yearly estimate."
    )
    edited = st.data_editor(
        validation_table,
        width="stretch",
        hide_index=True,
        disabled=[
            "College",
            "State",
            "Income Range Used",
            "App Yearly Estimate",
            "Public Avg Net Price",
            "Income-Band Net Price",
            "Difference",
            "Confidence",
            "Why Confidence",
            "Calculator URL",
        ],
        column_config={
            "App Yearly Estimate": st.column_config.NumberColumn(format="$%d"),
            "Public Avg Net Price": st.column_config.NumberColumn(format="$%d"),
            "Income-Band Net Price": st.column_config.NumberColumn(format="$%d"),
            "Official Calculator Result": st.column_config.NumberColumn(
                "Official Calculator Result",
                format="$%d",
                min_value=0,
                help="Enter the yearly net price returned by the school's official calculator for the same sample profile.",
            ),
            "Difference": st.column_config.NumberColumn(format="$%d"),
            "Confidence": st.column_config.TextColumn(help=TOOLTIPS["estimate_confidence"]),
            "Why Confidence": st.column_config.TextColumn(help="Main reasons behind the confidence label."),
            "Calculator URL": st.column_config.LinkColumn("Official Calculator", display_text="Open calculator"),
        },
        key="validation_editor",
    )

    calculated = edited.copy()
    official = pd.to_numeric(calculated["Official Calculator Result"], errors="coerce")
    app_estimate = pd.to_numeric(calculated["App Yearly Estimate"], errors="coerce")
    calculated["Difference"] = official - app_estimate
    if official.notna().any():
        st.markdown("##### Validation summary")
        validated = calculated[official.notna()].copy()
        validated["Absolute Difference"] = validated["Difference"].abs()
        avg_abs_difference = validated["Absolute Difference"].mean()
        within_5000 = int((validated["Absolute Difference"] <= 5000).sum())
        summary_cols = st.columns(3)
        summary_cols[0].metric("Validated Schools", f"{len(validated):,}")
        summary_cols[1].metric("Avg Absolute Difference", money(avg_abs_difference))
        summary_cols[2].metric("Within $5k/year", f"{within_5000}/{len(validated)}")
        st.caption(
            "This is not a final accuracy claim. It is a transparency check showing how close the public-data estimate is to official calculator results for one sample profile."
        )
        summary = validated[["College", "App Yearly Estimate", "Official Calculator Result", "Difference", "Absolute Difference"]]
        st.dataframe(
            summary,
            width="stretch",
            hide_index=True,
            column_config={
                "App Yearly Estimate": st.column_config.NumberColumn(format="$%d"),
                "Official Calculator Result": st.column_config.NumberColumn(format="$%d"),
                "Difference": st.column_config.NumberColumn(
                    format="$%d",
                    help="Official calculator result minus the app estimate. Positive means the official calculator was more expensive.",
                ),
                "Absolute Difference": st.column_config.NumberColumn(format="$%d"),
            },
        )
    st.download_button(
        "Download validation worksheet",
        calculated.to_csv(index=False).encode("utf-8"),
        "college_value_validation_worksheet.csv",
        "text/csv",
    )


def show_user_testing_page():
    st.subheader("User Testing")
    st.caption("Before publishing widely, test whether real students understand it, trust it, and know what to do next.")
    st.markdown(
        """
1. Ask 10-20 students, parents, teachers, or counselors to use the app without you explaining it.
2. Watch where they hesitate, misunderstand a score, or cannot find the next step.
3. Ask them to add 3 schools, run at least 1 official calculator, and compare the shortlist.
4. Record confusing moments as issues, not as personal feedback.
5. Fix the top 3 repeated problems before calling the site public.
"""
    )
    st.markdown("##### Tester task script")
    task_table = pd.DataFrame(
        [
            [1, "Enter a profile", "Add home state, income range, budget, intended focus, and optional GPA/test/EC fields."],
            [2, "Explore", "Find one likely/target school, one reach school, and one school that looks financially safe."],
            [3, "Shortlist", "Add 3-5 schools and read the shortlist health warnings."],
            [4, "Verify", "Open one official calculator and enter its yearly result."],
            [5, "React", "Say which score or label felt least clear."],
        ],
        columns=["Step", "Task", "What to observe"],
    )
    st.dataframe(task_table, width="stretch", hide_index=True)

    st.markdown("##### Questions to ask testers")
    testing_questions = pd.DataFrame(
        [
            ["Clarity", "Was the yearly cost, budget gap, debt, and earnings view more useful than the 0-100 scores?"],
            ["Clarity", "Which score or label still felt too abstract?"],
            ["Admissions", "Did Admissions Fit feel like a warning label or like a fake admissions chance?"],
            ["Trust", "Which number did you trust least, and why?"],
            ["Workflow", "Could you figure out what to do after adding a school?"],
            ["Verification", "Did you understand why the official calculator step matters?"],
            ["Usefulness", "Would this change which colleges you research?"],
            ["Missing piece", "What information did you expect but could not find?"],
        ],
        columns=["Area", "Question"],
    )
    st.dataframe(testing_questions, width="stretch", hide_index=True)
    st.download_button(
        "Download user-testing questions CSV",
        testing_questions.to_csv(index=False).encode("utf-8"),
        "college_value_lab_user_testing_questions.csv",
        "text/csv",
    )


def show_build_roadmap_page():
    st.subheader("Build Roadmap")
    st.write(
        "This prototype is still a Streamlit app, but the product direction is now bigger: "
        "a college affordability planner for students with financial need."
    )
    st.markdown(
        """
1. Public beta: keep Streamlit Cloud stable, add import/export for shortlists, and make the profile -> explorer -> shortlist -> calculator workflow obvious.
2. Credibility: validate 5-10 schools against official calculators and publish the method/limitations clearly.
3. Testing: get 10-20 real users and fix the top repeated confusions.
4. Competition package: prepare a 1-3 minute demo video, GitHub README, methodology, and Congressional App Challenge written response.
5. Version 2: move from session-only selected schools to persistent accounts, saved lists, and a database.
"""
    )
    st.markdown("##### Congressional App Challenge target")
    st.write(
        "Target submission package: working public app link, GitHub repository, demo video, short explanation of the problem, "
        "data sources, scoring method, student impact, what was personally built, limitations, and next steps."
    )
    st.caption("Working deadline target: October 26, 2026 at 8:00 PM ET.")
    st.markdown("##### Why AI Is Not In The Prototype Yet")
    st.write(
        "AI could eventually help students turn messy goals into school-list actions, but adding it "
        "before program-level earnings and debt data would make the product feel less trustworthy. "
        "The stronger move is to first add field-of-study data, then use AI to explain those results "
        "in plain English while keeping the score formula visible."
    )


def show_methodology_page():
    st.subheader("Methodology")
    st.caption("This page is here so the app can be challenged. A useful score needs to be understandable, not mysterious.")

    st.warning(
        "Beta disclaimer: College Value Lab is for comparison and planning, not final financial advice. "
        "Always verify costs with each college's official net price calculator and final financial-aid letter."
    )

    st.markdown("##### How to use the app")
    st.markdown(
        """
1. Enter profile.
2. Explore schools.
3. Add a shortlist.
4. Run official calculators.
5. Compare final affordability.
"""
    )
    st.caption(
        "That flow matters because the app is strongest at narrowing choices, while official calculators and aid letters are strongest at final price."
    )

    st.markdown("##### Score guide")
    st.caption(
        "Scores are comparison tools, not the main answer. The app intentionally leads with real dollar terms, debt, earnings, and risk labels because those are easier to verify and act on."
    )
    st.dataframe(score_band_table(), width="stretch", hide_index=True)

    st.markdown("##### Score dictionary")
    score_table = pd.DataFrame(
        [
            ["Financial Survivability", "Memorable safety score: can this student realistically afford and finish this school without unsafe debt?", "0-100, higher is safer", "Yearly budget fit, debt stress, graduation rate, and estimate trust. Large budget gaps cap the score."],
            ["Personalized Value Score", "Main personalized comparison score for the entered profile.", "0-100, higher is better", "Estimated yearly cost after aid, budget fit, debt, graduation, earnings, home-state fit, and profile priorities."],
            ["Major-Adjusted Value", "Main score when Academic focus is entered.", "0-100, higher is better", "60% Personalized Value and 40% Program Value when program data exists. Schools without matching program data receive a penalty."],
            ["Future ROI Score", "Standardized future payoff score.", "0-100, higher is better", "Percentile rank of the raw ROI Index compared with other rows. 85+ excellent, 70-84 strong, 50-69 mixed, under 50 weak."],
            ["Raw ROI Index", "Transparent formula behind ROI Score.", "ratio", "(10-year earnings / max(estimated 4-year cost after aid, $20,000)) * graduation rate."],
            ["Program Value", "Major/focus-specific value signal when field-of-study data exists.", "0-100", "Program earnings, program ROI, and lower program debt."],
            ["Admissions Fit", "Admissions realism warning so students do not build a list only from reach schools.", "label", "Reported admission rate plus optional GPA, SAT/ACT, and EC profile. Ultra-selective schools stay reaches for everyone."],
            ["Budget/Value Status", "Plain-English risk category.", "label", "Combines affordability, debt, graduation, payoff, and missing-data warnings."],
            ["Decision Score", "Shortlist helper only.", "0-100", "Normally 70% data score and 30% personal fit. If the user enters an official calculator estimate, the score uses 50% data score, 30% calculator cost fit, and 20% personal fit."],
        ],
        columns=["Score", "What it means", "Scale", "Main ingredients"],
    )
    st.dataframe(score_table, width="stretch", hide_index=True)

    st.markdown("##### Financial Survivability formula")
    st.write(
        "Financial Survivability is intentionally different from ROI. ROI asks whether the long-term payoff looks strong; "
        "Survivability asks whether the student can realistically handle the college financially now. The score is roughly "
        "55% yearly budget fit, 20% debt stress, 15% graduation probability, and 10% estimate trust. If a school is far above "
        "the entered yearly budget, the score is capped so high earnings cannot hide an unaffordable price."
    )

    st.markdown("##### Data sources")
    st.write(
        "Institution and field-of-study data come from the U.S. Department of Education College Scorecard API. "
        "The app uses public fields for cost, income-bracket net price, debt, graduation/completion, school-wide earnings, "
        "and program-level earnings/debt when available."
    )

    st.markdown("##### Cost estimates")
    st.write(
        "Estimated cost after aid uses College Scorecard net price by family-income bracket when the user selects an income range "
        "and the school reports that field. If the user selects the no-need-aid option, the app uses full annual cost because "
        "some families will not receive need-based aid at expensive private colleges. Otherwise, it falls back to average net price. "
        "Estimated Aid Savings is the estimated yearly cost before aid minus the estimated yearly cost after aid; it is a comparison signal, not a guaranteed scholarship or grant. "
        "If the user enters a home state, public colleges show the realistic residency scenario for that user: in-state for colleges in that state "
        "and out-of-state for public colleges elsewhere. If no home state is entered, the app shows both in-state and out-of-state scenarios. "
        "Because Scorecard does not provide perfect after-aid net price by residency, the out-of-state after-aid estimate adds the tuition difference to the estimated net price."
    )

    st.markdown("##### Debt display")
    st.write(
        "Raw median debt is kept as supporting evidence instead of a default table column because debt only makes sense in context. "
        "The default Explorer shows Debt Risk when the profile includes a max comfortable debt or high debt concern; that label compares typical debt with the user's debt limit and early-career earnings."
    )

    st.markdown("##### Net price calculator companion")
    st.write(
        "Federal rules require Title IV institutions enrolling full-time, first-time undergraduate students to post a net price calculator. "
        "Those calculators use institutional data and can include school-specific aid formulas, so this app should not be presented as a replacement. "
        "College Value Lab is a comparison layer: it helps students decide which schools are worth running through official calculators."
    )
    st.write(
        "In Selected Schools, users can enter the yearly result from an official calculator. When they do, Decision Score uses that school-specific "
        "cost instead of the app's public-data estimate for that school."
    )

    st.markdown("##### Estimate confidence")
    st.write(
        "Estimate confidence is based on how much evidence supports the estimate: income-bracket net price, school-wide outcomes, debt, graduation, "
        "official calculator link availability, residency assumptions, and program-level data when an academic focus is selected. "
        "High confidence does not mean guaranteed accuracy; it means the public-data estimate has stronger evidence behind it."
    )

    st.markdown("##### Program-level data")
    st.write(
        "Academic focus matching uses bachelor's-level 4-digit CIP field-of-study records. For common focuses like computer science, "
        "business, biology, nursing, economics, engineering, psychology, and education, the app uses CIP-code families to reduce bad fuzzy matches. "
        "When a focus is entered, Explorer sorts by Major-Adjusted Value instead of plain Personalized Value Score, and Selected Schools uses that score in its Decision Score. "
        "Major Earnings Difference shows matched program earnings minus the school's overall early-career median earnings, so users can read major impact in dollars and percent instead of only a score. "
        "That comparison is descriptive public data, not proof that the major alone causes the difference. "
        "Earnings and debt can be missing because College Scorecard suppresses small or sensitive cells."
    )

    st.markdown("##### Merit-aid data")
    st.write(
        "Merit Aid Signal uses College Transitions' Average Merit Aid table when the optional processed file is present. "
        "That table reports the percent of incoming freshmen without financial need who received institutional merit aid and the average merit award, "
        "compiled from each institution's Common Data Set. This app treats it as an opportunity signal only. It does not subtract the award from cost "
        "because merit scholarships depend on applicant strength, institutional priorities, deadlines, and scholarship rules."
    )
    st.markdown(f"[Open the merit-aid source table]({MERIT_AID_SOURCE_URL})")

    st.markdown("##### Important limitations")
    st.markdown(
        """
- This is not a financial-aid offer and cannot know merit scholarships.
- Program outcomes are historical medians, not predictions for a specific student.
- Admissions Fit is not a personalized chance of admission. It does not know essays, recommendations, course rigor, hooks, institutional priorities, or school-specific applicant pools.
- Major choice, location, internships, family support, and graduate school can change outcomes a lot.
- Some fields are privacy-suppressed or missing.
- The score is meant to support comparison, not replace college research or financial-aid letters.
"""
    )


def show_cost_earnings_chart(data):
    chart_data = data.rename(
        columns={
            "estimated_4yr_after_aid_cost": "Estimated 4-Year Cost After Aid ($)",
            "earnings_10yr_used": "Median Earnings 10 Years After Entry ($)",
            "graduation_rate": "Graduation Rate",
            "need_value_score": "Personalized Value Score",
            "display_name": "College",
        }
    )

    chart = (
        alt.Chart(chart_data)
        .mark_circle(size=70, opacity=0.7)
        .encode(
            x=alt.X(
                "Estimated 4-Year Cost After Aid ($):Q",
                axis=alt.Axis(format="$,.0f", title="Estimated 4-Year Cost After Aid"),
            ),
            y=alt.Y(
                "Median Earnings 10 Years After Entry ($):Q",
                axis=alt.Axis(format="$,.0f", title="Median Earnings 10 Years After Entry"),
            ),
            color=alt.Color(
                "Personalized Value Score:Q",
                scale=alt.Scale(scheme="blues"),
                legend=alt.Legend(format=".0f", title="Personalized Value Score"),
            ),
            tooltip=[
                "College:N",
                "state:N",
                alt.Tooltip("Estimated 4-Year Cost After Aid ($):Q", format="$,.0f"),
                alt.Tooltip("Median Earnings 10 Years After Entry ($):Q", format="$,.0f"),
                alt.Tooltip("Graduation Rate:Q", format=".1%"),
                alt.Tooltip("Personalized Value Score:Q", format=".0f"),
            ],
        )
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)


def show_college_browser(data, visible_rows=15, show_grad_priority=False):
    profile = get_profile_settings()
    show_program_columns = bool(profile["academic_focus"]) and data["program_match"].notna().any()
    show_debt_priority = profile["max_comfortable_debt"] > 0 or profile["debt_importance"] >= 7
    show_aid_priority = (
        profile["aid_uncertainty"] >= 7
        or profile["family_income_bracket"] not in [DEFAULT_INCOME_BRACKET, NO_NEED_AID_BRACKET]
    )
    show_grad_priority = show_grad_priority or profile["graduation_importance"] >= 7 or profile["first_gen"]
    table = data[
        [
            "scenario_id",
            "display_name",
            "state",
            "risk_label",
            "financial_survivability_score",
            "financial_survivability_label",
            "cost_before_aid",
            "cost_after_aid",
            "annual_budget_gap",
            "roi_score",
            "roi_rating",
            "earnings_after_grad",
            "earnings_10yr_used",
            "graduation_rate",
            "median_debt",
            "debt_to_earnings_after_grad",
            "program_match",
            "program_earnings_1yr",
            "program_debt",
            "program_value_score",
            "program_earnings_vs_school",
            "program_earnings_vs_school_pct",
            "program_earnings_vs_school_label",
            "focus_adjusted_score",
            "focus_match_status",
            "estimate_confidence",
            "estimate_confidence_score",
            "data_warning",
            "admissions_category",
            "admissions_selectivity",
            "academic_strength_score",
            "merit_aid_signal",
            "merit_aid_percent",
            "merit_aid_average_award",
            "net_price_calculator_url",
            "need_value_score",
            "data_coverage",
        ]
    ].rename(
        columns={
            "scenario_id": "ID",
            "display_name": "College name",
            "state": "State",
            "risk_label": "Budget/Value Status",
            "financial_survivability_score": "Financial Survivability",
            "financial_survivability_label": "Survivability Label",
            "cost_before_aid": "Estimated Yearly Cost Before Aid",
            "cost_after_aid": "Estimated Yearly Cost After Aid",
            "annual_budget_gap": "Yearly Over/Under Budget",
            "roi_score": "Future ROI Score",
            "roi_rating": "ROI Rating",
            "earnings_after_grad": "Earnings After Grad",
            "earnings_10yr_used": "Earnings 10 Years Later",
            "graduation_rate": "Grad Rate",
            "median_debt": "Debt",
            "debt_to_earnings_after_grad": "Debt / Early Earnings",
            "program_match": "Program Match",
            "program_earnings_1yr": "Program Earnings",
            "program_debt": "Program Debt",
            "program_value_score": "Program Value",
            "program_earnings_vs_school": "Major Earnings Difference",
            "program_earnings_vs_school_pct": "Major Earnings Difference %",
            "program_earnings_vs_school_label": "Major Earnings vs School",
            "focus_adjusted_score": "Major-Adjusted Value",
            "focus_match_status": "Focus Match",
            "estimate_confidence": "Confidence",
            "estimate_confidence_score": "Confidence Score",
            "data_warning": "Missing Data Warning",
            "admissions_category": "Admissions Category",
            "admissions_selectivity": "Admissions Selectivity",
            "academic_strength_score": "Academic Profile Signal",
            "merit_aid_signal": "Merit Aid Signal",
            "merit_aid_percent": "Merit Aid %",
            "merit_aid_average_award": "Avg Merit Award",
            "net_price_calculator_url": "Official Calculator URL",
            "need_value_score": "Personalized Value Score",
            "data_coverage": "Data Coverage",
        }
    )
    table["Grad Rate"] = table["Grad Rate"] * 100
    table["Debt / Early Earnings"] = table["Debt / Early Earnings"] * 100
    table["Major Earnings Difference %"] = table["Major Earnings Difference %"] * 100
    table["Estimated Aid Savings"] = (table["Estimated Yearly Cost Before Aid"] - table["Estimated Yearly Cost After Aid"]).clip(lower=0)
    table["Debt Risk"] = table.apply(
        lambda row: debt_risk_label(row["Debt"], profile["max_comfortable_debt"], row["Earnings After Grad"]),
        axis=1,
    )
    table["Official Calculator"] = table["Official Calculator URL"].apply(
        lambda value: "Verify with calculator" if clean_url(value) else "Calculator link unavailable"
    )
    show_budget_gap = profile["annual_family_budget"] > 0
    show_detailed_columns = st.toggle(
        "Show detailed table columns",
        value=False,
        help="Turn this on for supporting evidence like raw debt, data coverage, detailed ROI, merit-aid fields, and confidence score.",
    )
    st.caption(
        "Default columns change based on your profile. The score comes first for comparison; the next columns show the real numbers behind it: cost, aid savings, budget fit, program earnings, and profile-specific risks."
    )
    column_order = [
        "College name",
        "State",
        "Personalized Value Score",
        "Financial Survivability",
        "Estimated Yearly Cost Before Aid",
        "Estimated Yearly Cost After Aid",
        "Estimated Aid Savings",
        "Survivability Label",
        "Budget/Value Status",
        "Admissions Category",
    ]
    if show_budget_gap:
        column_order.append("Yearly Over/Under Budget")
    if show_grad_priority:
        column_order.append("Grad Rate")
    if show_debt_priority:
        column_order.append("Debt Risk")
    if show_aid_priority:
        column_order.extend(["Confidence", "Official Calculator"])
    if show_detailed_columns:
        column_order.extend([
            "Earnings After Grad",
            "Earnings 10 Years Later",
            "Debt",
            "Debt / Early Earnings",
            "Future ROI Score",
            "ROI Rating",
            "Admissions Selectivity",
            "Academic Profile Signal",
            "Merit Aid Signal",
            "Merit Aid %",
            "Avg Merit Award",
            "Confidence Score",
            "Missing Data Warning",
            "Data Coverage",
        ])
    if show_program_columns:
        column_order = [
            "College name",
            "State",
            "Major-Adjusted Value",
            "Personalized Value Score",
            "Financial Survivability",
            "Estimated Yearly Cost Before Aid",
            "Estimated Yearly Cost After Aid",
            "Estimated Aid Savings",
            "Program Match",
            "Program Earnings",
            "Major Earnings vs School",
            "Survivability Label",
            "Admissions Category",
        ]
        if show_budget_gap:
            column_order.append("Yearly Over/Under Budget")
        if show_grad_priority:
            column_order.append("Grad Rate")
        if show_debt_priority:
            column_order.append("Debt Risk")
        if show_aid_priority:
            column_order.extend(["Confidence", "Official Calculator"])
        if show_detailed_columns:
            column_order.extend([
                "Earnings After Grad",
                "Earnings 10 Years Later",
                "Program Debt",
                "Program Value",
                "Major Earnings Difference",
                "Major Earnings Difference %",
                "Future ROI Score",
                "ROI Rating",
                "Debt",
                "Debt / Early Earnings",
                "Focus Match",
                "Admissions Selectivity",
                "Academic Profile Signal",
                "Merit Aid Signal",
                "Merit Aid %",
                "Avg Merit Award",
                "Confidence Score",
                "Missing Data Warning",
                "Data Coverage",
            ])
    column_order = list(dict.fromkeys([column for column in column_order if column in table.columns]))
    visible_count = min(len(table), visible_rows)
    table_height = 38 + (visible_count + 1) * 35

    event = st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        height=table_height,
        on_select="rerun",
        selection_mode="single-row",
        column_order=column_order,
        column_config={
            "ID": None,
            "College name": st.column_config.TextColumn(
                help="Click a row to open that college in College Details below."
            ),
            "State": st.column_config.TextColumn(help="U.S. state where the college is located."),
            "Budget/Value Status": st.column_config.TextColumn(help=TOOLTIPS["risk_label"]),
            "Admissions Category": st.column_config.TextColumn("Admissions Fit", help=TOOLTIPS["admissions_category"]),
            "Admissions Selectivity": st.column_config.TextColumn(
                help="Generic selectivity label using only the school's reported admission rate."
            ),
            "Merit Aid Signal": st.column_config.TextColumn(help=TOOLTIPS["merit_aid"]),
            "Merit Aid %": st.column_config.NumberColumn(format="%.1f%%", help=TOOLTIPS["merit_aid"]),
            "Avg Merit Award": st.column_config.NumberColumn(format="$%d", help=TOOLTIPS["merit_aid"]),
            "Academic Profile Signal": st.column_config.ProgressColumn(
                help=TOOLTIPS["academic_strength"],
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Financial Survivability": st.column_config.ProgressColumn(
                "Financial Survivability (0-100)",
                help=TOOLTIPS["financial_survivability"],
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Survivability Label": st.column_config.TextColumn(
                help="Plain-English label for whether this school looks financially survivable for the profile."
            ),
            "Estimated Yearly Cost Before Aid": st.column_config.NumberColumn("Est. Yearly Cost Before Aid", format="$%d", help=TOOLTIPS["cost_before_aid"]),
            "Estimated Yearly Cost After Aid": st.column_config.NumberColumn("Est. Yearly Cost After Aid", format="$%d", help=TOOLTIPS["cost_after_aid"]),
            "Estimated Aid Savings": st.column_config.NumberColumn(
                "Est. Aid Savings",
                format="$%d",
                help="Estimated yearly cost before aid minus estimated yearly cost after aid. This is not a guaranteed aid offer.",
            ),
            "Yearly Over/Under Budget": st.column_config.NumberColumn("Yearly Over/Under Budget", format="$%d", help=TOOLTIPS["budget_gap"]),
            "Debt Risk": st.column_config.TextColumn(
                help="Personalized debt signal using your max comfortable debt and early-career earnings, when available."
            ),
            "Official Calculator": st.column_config.TextColumn(
                help="Whether this row has an official net price calculator link to verify your real school-specific estimate."
            ),
            "Future ROI Score": st.column_config.ProgressColumn(
                "Future ROI Score (0-100)",
                help=TOOLTIPS["roi_score"],
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "ROI Rating": st.column_config.TextColumn(help="Plain-English interpretation of Future ROI Score."),
            "Confidence": st.column_config.TextColumn(help=TOOLTIPS["estimate_confidence"]),
            "Missing Data Warning": st.column_config.TextColumn(
                help="Plain-language warning when the row has low confidence, missing public data, or unavailable program-level data."
            ),
            "Confidence Score": st.column_config.ProgressColumn(
                help=TOOLTIPS["estimate_confidence"],
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Earnings After Grad": st.column_config.NumberColumn(format="$%d", help="Median earnings 1 year after graduation when available."),
            "Earnings 10 Years Later": st.column_config.NumberColumn(format="$%d", help="Median earnings 10 years after entry when available."),
            "Grad Rate": st.column_config.NumberColumn(format="%.1f%%", help=TOOLTIPS["graduation_rate"]),
            "Debt": st.column_config.NumberColumn(format="$%d", help=TOOLTIPS["median_debt"]),
            "Debt / Early Earnings": st.column_config.NumberColumn(format="%.0f%%", help=TOOLTIPS["debt_to_earnings"]),
            "Program Match": st.column_config.TextColumn(help="Best matching bachelor's program for your Academic focus."),
            "Focus Match": st.column_config.TextColumn(help="Whether the academic focus matched a bachelor's program row."),
            "Program Earnings": st.column_config.NumberColumn(format="$%d", help="Median earnings 1 year after completion for the matched program when available."),
            "Program Debt": st.column_config.NumberColumn(format="$%d", help="Median federal student loan debt for the matched program when available."),
            "Major Earnings vs School": st.column_config.TextColumn(
                help="Plain-English comparison between matched major earnings and this school's overall early-career median earnings."
            ),
            "Major Earnings Difference": st.column_config.NumberColumn(
                format="$%d",
                help="Matched major earnings minus this school's overall early-career median earnings. Useful for seeing whether this focus appears stronger or weaker than the school's average outcome.",
            ),
            "Major Earnings Difference %": st.column_config.NumberColumn(
                format="%.1f%%",
                help="Matched major earnings difference as a percent of this school's overall early-career median earnings.",
            ),
            "Program Value": st.column_config.ProgressColumn(
                "Program Value (0-100)",
                help="Program-specific score using program ROI, program earnings, and lower program debt.",
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Major-Adjusted Value": st.column_config.ProgressColumn(
                "Major-Adjusted Value (0-100)",
                help=TOOLTIPS["focus_adjusted_score"],
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Personalized Value Score": st.column_config.ProgressColumn(
                "Personalized Value Score (0-100)",
                help=TOOLTIPS["need_value_score"],
                format="%.0f",
                min_value=0,
                max_value=100,
            ),
            "Data Coverage": st.column_config.ProgressColumn(
                help="Percent of core fields available for this row: estimated cost, earnings, graduation, completion, and debt.",
                format="%.0f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )

    selected_rows = event.selection.rows
    if selected_rows:
        selected_id = table.iloc[selected_rows[0]]["ID"]
        st.session_state["selected_college_id"] = selected_id
        st.session_state["details_source"] = "explorer"

    if len(data) > visible_rows:
        st.caption(f"Showing {visible_rows} rows at a time. Scroll inside the table to see all {len(data):,} rows.")


def show_why_project_page():
    st.subheader("Why This Project")
    st.caption("The short version: college price is too important to compare with vibes and sticker price alone.")

    st.markdown("##### The problem")
    plain_markdown_text(
        "College can be expensive. In 2025-26, College Board reports average published tuition "
        "and fees of $11,950 for in-state public four-year colleges, $31,880 for out-of-state "
        "public four-year colleges, and $45,000 for private nonprofit four-year colleges."
    )

    st.markdown("##### Sticker price is not the whole story")
    plain_markdown_text(
        "Aid can lower the real cost, but students often have to compare dozens of schools, "
        "income assumptions, debt risk, graduation rates, and major outcomes. For some families, "
        "the numbers still are not possible."
    )

    st.markdown("##### What this tool is trying to do")
    plain_markdown_text(
        "College Value Lab turns public data into a decision workflow. It compares yearly estimated "
        "cost after aid, budget gaps, debt, graduation outcomes, earnings, official calculator links, "
        "and major-level data so students can decide which schools deserve deeper research."
    )

    why_table = pd.DataFrame(
        [
            ["Compare", "Put cost, debt, completion, and earnings in one table instead of scattered tabs."],
            ["Verify", "Use official net price calculators before trusting any school as affordable."],
            ["Decide", "Build a shortlist around realistic next steps, not a generic ranking."],
        ],
        columns=["Step", "Purpose"],
    )
    st.dataframe(why_table, width="stretch", hide_index=True)

    st.markdown("##### Example use cases")
    case_table = pd.DataFrame(
        [
            [
                "Low-income, high-aid student",
                "Needs schools that are affordable now, not just prestigious later.",
                "Income-band net price, budget gap, Financial Survivability, official calculator verification.",
            ],
            [
                "Full-pay family",
                "May not receive need aid, so full cost matters more than average net price.",
                "No-need-aid mode, Future ROI Score, Major-Adjusted Value.",
            ],
            [
                "Budget-limited out-of-state applicant",
                "A high-ROI school can still be financially unsafe if the yearly gap is too large.",
                "Home-state residency logic, Survivability caps, what-if scholarship simulator.",
            ],
        ],
        columns=["Student type", "Decision problem", "What the app checks"],
    )
    st.dataframe(case_table, width="stretch", hide_index=True)

    st.info(
        "This is a planning aid, not a financial-aid estimator. Official school calculators and aid letters "
        "should still decide final affordability."
    )


def inject_lab_theme():
    st.markdown(
        """
<style>
    [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 10% 8%, rgba(125, 207, 255, 0.18), transparent 23rem),
            radial-gradient(circle at 92% 18%, rgba(86, 232, 185, 0.10), transparent 24rem),
            linear-gradient(135deg, #08111c 0%, #172235 42%, #0e151f 100%);
        color: rgba(255, 255, 255, 0.90);
    }
    [data-testid="stAppViewContainer"]:before {
        content: "";
        position: fixed;
        inset: -35%;
        pointer-events: none;
        background:
            linear-gradient(90deg, transparent 0 48%, rgba(255, 255, 255, 0.035) 49% 51%, transparent 52% 100%),
            linear-gradient(0deg, transparent 0 48%, rgba(255, 255, 255, 0.026) 49% 51%, transparent 52% 100%);
        background-size: 130px 130px;
        transform: rotate(-8deg);
        opacity: 0.40;
    }
    [data-testid="stSidebar"] {
        background: rgba(7, 13, 22, 0.88);
        border-right: 1px solid rgba(158, 216, 255, 0.16);
    }
    [data-testid="stHeader"] {
        background: transparent;
        backdrop-filter: none;
        pointer-events: none;
    }
    .block-container {
        max-width: 1280px;
        padding-top: 1.75rem;
        padding-bottom: 4rem;
    }
    html, body, [class*="css"] {
        font-size: 16px;
    }
    h1, h2, h3 {
        color: #f8fbff;
        letter-spacing: 0;
    }
    h2, h3 {
        margin-top: 1rem;
    }
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] label,
    [data-testid="stMarkdownContainer"] span {
        letter-spacing: 0;
        word-break: normal;
        overflow-wrap: break-word;
        line-height: 1.55;
    }
    .plain-text {
        margin: 0 0 0.85rem 0;
        color: rgba(235, 245, 255, 0.82);
        line-height: 1.6;
        letter-spacing: 0;
        word-break: normal;
        overflow-wrap: break-word;
        white-space: normal;
    }
    .plain-caption {
        margin: 0.15rem 0 0.65rem 0;
        color: rgba(235, 245, 255, 0.84);
        line-height: 1.45;
        letter-spacing: 0;
        word-break: normal;
        overflow-wrap: break-word;
        white-space: normal;
        font-size: 0.9rem;
    }
    .plain-note {
        border: 1px solid rgba(158, 216, 255, 0.16);
        border-radius: 8px;
        background: rgba(67, 130, 180, 0.14);
        color: rgba(244, 250, 255, 0.92);
        padding: 0.8rem 0.95rem;
        line-height: 1.55;
        letter-spacing: 0;
        word-break: normal;
        overflow-wrap: break-word;
        white-space: normal;
        margin: 0.4rem 0 0.9rem 0;
    }
    .summary-card {
        border: 1px solid rgba(158, 216, 255, 0.16);
        border-radius: 8px;
        background: rgba(9, 15, 25, 0.62);
        padding: 0.9rem 1rem;
        min-height: 8.25rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16);
    }
    .summary-title {
        color: rgba(226, 241, 252, 0.88);
        font-size: 0.82rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0;
        margin-bottom: 0.45rem;
    }
    .summary-college {
        color: #ffffff;
        font-size: 1.05rem;
        font-weight: 800;
        line-height: 1.25;
        letter-spacing: 0;
        word-break: normal;
        overflow-wrap: break-word;
        margin-bottom: 0.55rem;
    }
    .summary-detail {
        color: #9ed8ff;
        font-size: 0.98rem;
        font-weight: 750;
        line-height: 1.35;
        letter-spacing: 0;
    }
    .summary-help {
        color: rgba(226, 241, 252, 0.78);
        font-size: 0.82rem;
        line-height: 1.35;
        letter-spacing: 0;
        margin-top: 0.55rem;
    }
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] p {
        word-break: normal;
        overflow-wrap: break-word;
        white-space: normal;
    }
    [data-testid="stMetric"],
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    [data-testid="stExpander"],
    [data-testid="stAlert"] {
        border: 1px solid rgba(158, 216, 255, 0.14);
        border-radius: 8px;
        background: rgba(8, 14, 23, 0.76);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.18);
        backdrop-filter: blur(14px);
    }
    [data-testid="stMetric"] {
        padding: 0.85rem 0.95rem;
    }
    [data-testid="stMetricLabel"] {
        color: rgba(235, 245, 255, 0.88);
        font-weight: 700;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff;
    }
    [data-testid="stCaptionContainer"],
    .stCaption {
        color: rgba(235, 245, 255, 0.78);
    }
    [data-testid="stDataFrame"] {
        color: #f8fbff;
    }
    div[data-testid="stTabs"] button {
        border-radius: 8px 8px 0 0;
        color: rgba(235, 245, 255, 0.78);
        font-weight: 700;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #ffffff;
        border-bottom-color: #56e8b9;
    }
    .stButton button,
    .stDownloadButton button {
        border-radius: 8px;
        border: 1px solid rgba(158, 216, 255, 0.28);
        background: rgba(11, 22, 35, 0.74);
        color: #f8fbff;
        font-weight: 700;
    }
    .stButton button:hover,
    .stDownloadButton button:hover {
        border-color: rgba(86, 232, 185, 0.82);
        color: #ffffff;
        box-shadow: 0 0 22px rgba(86, 232, 185, 0.16);
    }
    div[data-baseweb="input"],
    div[data-baseweb="select"] > div,
    div[data-baseweb="textarea"] {
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.06);
    }
    hr {
        border-color: rgba(158, 216, 255, 0.16);
    }
    .lab-header {
        border: 1px solid rgba(158, 216, 255, 0.16);
        border-radius: 8px;
        padding: 1.15rem 1.25rem;
        margin: 0 0 1rem 0;
        background: rgba(9, 15, 25, 0.62);
        box-shadow: 0 20px 70px rgba(0, 0, 0, 0.22);
        position: relative;
        overflow: hidden;
    }
    .lab-toprow {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
    }
    .lab-header:before {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        height: 3px;
        background: linear-gradient(90deg, #9ed8ff, #56e8b9, #ffe08a);
    }
    .lab-kicker {
        color: #9ed8ff;
        font-size: 0.84rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0;
        margin-bottom: 0.25rem;
    }
    .lab-title {
        color: #ffffff;
        font-size: 2.15rem;
        font-weight: 850;
        line-height: 1.05;
        margin: 0;
        letter-spacing: 0;
    }
    .lab-subtitle {
        max-width: 860px;
        color: rgba(235, 245, 255, 0.74);
        font-size: 1rem;
        line-height: 1.5;
        margin-top: 0.55rem;
    }
</style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="College Value Lab", layout="wide")

inject_lab_theme()
st.markdown(
    """
<div class="lab-header">
    <div class="lab-toprow">
        <div>
            <div class="lab-kicker">College affordability decision lab</div>
            <div class="lab-title">College Value Lab</div>
            <div class="lab-subtitle">
                Compare yearly estimated cost after aid, debt, graduation outcomes, major-level earnings, official calculator links, and shortlist next steps.
            </div>
        </div>
    </div>
</div>
    """,
    unsafe_allow_html=True,
)

st.warning(
    "Beta planning tool: use this to compare colleges and build a shortlist, not as a final financial-aid answer. "
    "Before making decisions, verify each school with its official net price calculator and financial-aid letter."
)

flow_cols = st.columns(5)
for index, step in enumerate([
    "1. Enter profile",
    "2. Explore schools",
    "3. Add shortlist",
    "4. Run calculators",
    "5. Compare affordability",
]):
    flow_cols[index].caption(step)

merit_updated_at = MERIT_AID_DATA_PATH.stat().st_mtime if MERIT_AID_DATA_PATH.exists() else None
df = load_data(DATA_PATH.stat().st_mtime, DATA_SCHEMA_VERSION, merit_updated_at)
programs_updated_at = PROGRAM_DATA_PATH.stat().st_mtime if PROGRAM_DATA_PATH.exists() else None
profile_settings = get_profile_settings()
scenario_df = prepare_scenario_data(
    DATA_PATH.stat().st_mtime,
    programs_updated_at,
    merit_updated_at,
    DATA_SCHEMA_VERSION,
    PROGRAM_SCHEMA_VERSION,
    tuple(profile_settings.items()),
)

with st.sidebar:
    st.header("College Filters")
    if profile_settings["home_state"] == "Prefer not to say":
        st.caption(
            "Use these controls to narrow the table by location, school type, residency, size, cost, and graduation rate. Add a home state in Personal Profile to remove duplicate public in-state/out-of-state rows."
        )
    else:
        st.caption(
            f"Using {profile_settings['home_state']} as your home state: public colleges in {profile_settings['home_state']} show in-state cost; public colleges elsewhere show out-of-state cost."
        )
    if profile_settings["annual_family_budget"] > 0:
        sort_column = "financial_survivability_score"
    elif profile_settings["academic_focus"]:
        sort_column = "focus_adjusted_score"
    else:
        sort_column = "need_value_score"
    scenario_df = scenario_df.sort_values(sort_column, ascending=False, na_position="last")
    only_program_matches = False
    if profile_settings["academic_focus"]:
        if programs_updated_at is None:
            st.warning("Program-level data has not been fetched yet. Run `python3 scripts/fetch_college_programs.py`.")
        else:
            focus_matches = scenario_df["program_match"].notna().sum()
            st.caption(f"Academic focus matches: {focus_matches:,} college scenario(s).")
            st.caption("With an Academic focus entered, Explorer sorts by Major-Adjusted Value instead of plain Personalized Value Score.")
            only_program_matches = st.checkbox(
                "Only show schools with matching program data",
                value=False,
                help="Keeps colleges that have a bachelor's program matching the Academic focus in Personal Profile.",
            )

    states = sorted(scenario_df["state"].dropna().unique())
    selected_states = st.multiselect("State", states, default=[])
    regions = sorted(scenario_df["region"].dropna().unique())
    selected_regions = st.multiselect("Region", regions, default=[])
    degrees = sorted(scenario_df["predominant_degree"].dropna().unique())
    selected_degrees = st.multiselect("Predominant degree", degrees, default=["Bachelor"])
    admissions_fit_options = [
        "Likely",
        "Target",
        "Target/reach",
        "Reach",
        "Far reach",
        "Extreme reach",
        "Admissions data unavailable",
    ]
    available_admissions_fits = [
        label
        for label in admissions_fit_options
        if label in set(scenario_df["admissions_category"].dropna())
    ]
    selected_admissions_fits = st.multiselect(
        "Admissions fit",
        available_admissions_fits,
        default=[],
        help="Filter by rough admissions realism for your GPA/test/EC profile. This is not an admission probability.",
    )

    st.caption("Ownership")
    ownerships = sorted(scenario_df["ownership"].dropna().unique())
    selected_ownerships = [
        ownership
        for ownership in ownerships
        if st.checkbox(ownership, value=True, key=f"ownership_{ownership}")
    ]

    selected_residencies = []
    if profile_settings["home_state"] == "Prefer not to say":
        st.caption("Residency")
        residencies = sorted(scenario_df["residency"].dropna().unique())
        selected_residencies = [
            residency
            for residency in residencies
            if st.checkbox(residency, value=True, key=f"residency_{residency}")
        ]

    student_min = int(scenario_df["student_size"].dropna().min())
    student_max = int(scenario_df["student_size"].dropna().max())
    selected_student_range = st.slider(
        "Student size",
        student_min,
        student_max,
        (1000, student_max),
        step=250,
        help=TOOLTIPS["student_size"],
    )
    student_input_1, student_input_2 = st.columns(2)
    student_lower = student_input_1.number_input(
        "Min students",
        min_value=student_min,
        max_value=student_max,
        value=selected_student_range[0],
        step=100,
    )
    student_upper = student_input_2.number_input(
        "Max students",
        min_value=student_min,
        max_value=student_max,
        value=selected_student_range[1],
        step=100,
    )
    selected_student_range = (min(student_lower, student_upper), max(student_lower, student_upper))

    valid_costs = scenario_df["cost_after_aid"].dropna()
    cost_min = max(0, int(valid_costs.min()))
    cost_max = int(valid_costs.max())
    selected_cost_range = st.slider(
        "Estimated cost after aid",
        cost_min,
        cost_max,
        (cost_min, cost_max),
        step=1000,
        help=TOOLTIPS["cost_after_aid"],
    )
    cost_input_1, cost_input_2 = st.columns(2)
    cost_lower = cost_input_1.number_input(
        "Min cost",
        min_value=cost_min,
        max_value=cost_max,
        value=selected_cost_range[0],
        step=500,
    )
    cost_upper = cost_input_2.number_input(
        "Max cost",
        min_value=cost_min,
        max_value=cost_max,
        value=selected_cost_range[1],
        step=500,
    )
    selected_cost_range = (min(cost_lower, cost_upper), max(cost_lower, cost_upper))

    min_grad_rate = st.slider(
        "Minimum graduation rate",
        0,
        100,
        0,
        step=5,
        help=TOOLTIPS["graduation_rate"],
    )
    min_data_coverage = st.slider(
        "Minimum data coverage",
        0,
        100,
        80,
        step=5,
        help="Keeps rows with enough public data for the estimate to be useful.",
    )

filtered = scenario_df.copy()
if selected_states:
    filtered = filtered[filtered["state"].isin(selected_states)]
if selected_regions:
    filtered = filtered[filtered["region"].isin(selected_regions)]
if selected_ownerships:
    filtered = filtered[filtered["ownership"].isin(selected_ownerships)]
if selected_degrees:
    filtered = filtered[filtered["predominant_degree"].isin(selected_degrees)]
if selected_residencies:
    filtered = filtered[filtered["residency"].isin(selected_residencies)]
if selected_admissions_fits:
    filtered = filtered[filtered["admissions_category"].isin(selected_admissions_fits)]
if only_program_matches:
    filtered = filtered[filtered["program_match"].notna()]
filtered = filtered[
    filtered["student_size"].between(selected_student_range[0], selected_student_range[1])
    & filtered["cost_after_aid"].between(selected_cost_range[0], selected_cost_range[1])
    & (filtered["graduation_rate"] >= min_grad_rate / 100)
    & (filtered["data_coverage"] >= min_data_coverage)
]

top = filtered.head(25)

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "College Scenarios",
    f"{len(filtered):,}",
    help=f"{TOOLTIPS['colleges']} Cleaned schools: {len(df):,}. Cost scenarios: {len(scenario_df):,}.",
)
col2.metric("Median Yearly Est. Cost After Aid", money(filtered["cost_after_aid"].median()), help=TOOLTIPS["cost_after_aid"])
if profile_settings["annual_family_budget"] > 0:
    col3.metric(
        "Median Financial Survivability",
        number(filtered["financial_survivability_score"].median()),
        help=TOOLTIPS["financial_survivability"],
    )
else:
    col3.metric("Median Earnings After Grad", money(filtered["earnings_after_grad"].median()), help="Median earnings 1 year after graduation when available.")
col4.metric("Median Earnings 10 Years Later", money(filtered["earnings_10yr_used"].median()), help="Median earnings 10 years after entry when available.")

if not filtered.empty:
    signal_counts = filtered["risk_label"].value_counts().head(3)
    signal_text = " | ".join(f"{label}: {count:,}" for label, count in signal_counts.items())
    st.caption(f"Most common financial signals in this view: {signal_text}")

plain_caption(
    f"Median yearly estimated cost after aid for this filtered view: {money(filtered['cost_after_aid'].median())}. "
    "Costs shown in the app are yearly unless a label explicitly says 4-year. "
    "The score is the first comparison signal, but the table backs it up with readable numbers: cost before aid, cost after aid, estimated aid savings, budget fit, program earnings, and profile-specific risks. "
    f"{describe_score_mode(profile_settings)}"
)

profile_tab, explorer_tab, selected_tab, validation_tab, methodology_tab, roadmap_tab, why_tab = st.tabs(
    [
        "Personal Profile",
        "Explorer",
        "Selected Schools",
        "Validation & Testing",
        "Methodology",
        "Build Roadmap",
        "Why This Project",
    ]
)

with profile_tab:
    show_personal_profile_page()

with explorer_tab:
    st.subheader("College ROI Explorer")
    st.caption(
        "Sorted by the clearest value score for your profile. If you entered a yearly budget, the table prioritizes Financial Survivability. Without a budget, it uses Major-Adjusted Value when a focus is entered, otherwise Personalized Value Score."
    )
    st.info(
        "Quick read: earnings are reported snapshots, not lifetime earnings. Future ROI uses school-wide early and 10-year earnings. "
        "The score appears first for comparison, then the table shows the numbers a reader can actually judge. "
        "If you enter an Academic focus, Major-Adjusted Value and Program Outcomes use major/focus-specific earnings and debt when public data is available."
    )
    header_col, search_col = st.columns([1, 2])
    header_col.subheader("College")
    query = search_col.text_input(
        "College name",
        placeholder="Start typing: mich, ucla, umich, georgia tech...",
        label_visibility="visible",
    )
    table_view = filtered
    if query:
        table_view = search_colleges(filtered, query)
        if table_view.empty:
            st.info("No close matches found. Try a shorter search, like the main college name.")
        else:
            st.caption(f"Showing {len(table_view)} search match(es) inside the table.")

    if table_view.empty:
        st.info("No colleges match the current filters. Try widening the cost, size, or graduation-rate range.")
    else:
        st.caption("Click a row to open College Details below. Use the list control under the table to add schools.")
        if not profile_has_personalization(profile_settings):
            st.info(
                "This table is using the public/default scoring recipe. Fill out Personal Profile to personalize cost, aid, residency, major outcomes, admissions fit, and which columns appear first."
            )
        if profile_settings["annual_family_budget"] <= 0:
            st.info("Add the yearly amount your family can actually pay in Personal Profile to show Yearly Over/Under Budget in the table.")
        show_college_browser(table_view, show_grad_priority=min_grad_rate > 0)
        list_options = table_view["scenario_id"].tolist()
        display_names = table_view.set_index("scenario_id")["display_name"].to_dict()
        selected_table_ids = st.multiselect(
            "Choose schools to add to your list",
            options=list_options,
            format_func=lambda scenario_id: display_names.get(scenario_id, scenario_id),
            placeholder="Select one or more colleges...",
        )
        if st.button(
            f"Add selected colleges ({len(selected_table_ids)})",
            disabled=not selected_table_ids,
        ):
            selected_rows = scenario_df[scenario_df["scenario_id"].isin(selected_table_ids)]
            for _, row in selected_rows.iterrows():
                add_selected_school(row, show_message=False)
            st.success(f"Added {len(selected_rows)} college scenario(s) to Selected Schools.")
        if selected_table_ids:
            st.caption("Selected schools will be added to your list.")

    st.divider()
    st.subheader("College Details")
    show_selected_college(scenario_df)

    st.divider()
    st.subheader("Cost vs. Earnings")
    if not filtered.empty:
        show_cost_earnings_chart(filtered)

with selected_tab:
    show_selected_schools_page(scenario_df)

with validation_tab:
    show_validation_page(scenario_df)
    st.divider()
    show_user_testing_page()

with methodology_tab:
    show_methodology_page()

with roadmap_tab:
    show_build_roadmap_page()

with why_tab:
    show_why_project_page()
