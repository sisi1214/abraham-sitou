"""
fetch_data.py — University Cost Dashboard auto-updater
Runs via GitHub Actions on a schedule; writes Datablog/data.json.

Auto-updated every week:
  • USD exchange rates (frankfurter.app — ECB reference, free, no key)
  • UK RPI from ONS (drives Plan 2 & Plan 5 loan rates)
  • Australia CPI from ABS (drives HECS-HELP indexation rate)
  • All tuition fees re-expressed in USD at current rates

Annually-updated values (hardcoded, needs human review each July/August):
  • US Federal loan rate (Dept of Education publishes each June for next academic year)
  • Singapore MOE loan rate (bank-rate linked, review quarterly)
"""

import json
import os
import sys
import requests
from datetime import datetime, date

# ─── LOCAL CURRENCY TUITION FEES ───────────────────────────────────────────
# Update the local amounts when governments change fee caps (usually annually).
TUITION_LOCAL = {
    "HK":         {"amount": 42100,  "currency": "HKD",
                   "note": "UGC standard rate — frozen since 1997/98"},
    "UK":         {"amount": 9250,   "currency": "GBP",
                   "note": "Domestic cap — Office for Students 2024/25"},
    "US_instate": {"amount": 11610,  "currency": "USD",
                   "note": "In-state public average — NCES 2024"},
    "US_private":  {"amount": 39000, "currency": "USD",
                   "note": "Private university average — NCES 2024"},
    "SG":         {"amount": 11200,  "currency": "SGD",
                   "note": "MOE subsidised avg across NUS/NTU/SMU AY2024/25"},
    "AU":         {"amount": 9540,   "currency": "AUD",
                   "note": "Average domestic — Study Australia 2024"},
    "CA":         {"amount": 7734,   "currency": "CAD",
                   "note": "National average — Statistics Canada 2024/25"},
    "DE":         {"amount": 144,    "currency": "EUR",
                   "note": "Semester administration fees only; no tuition"},
    "FR":         {"amount": 2770,   "currency": "EUR",
                   "note": "Public university average — MESRI 2024/25"},
}

# ─── STATIC LOAN RATES ─────────────────────────────────────────────────────
# These either change annually (US) or are policy-fixed (DE, CA, FR).
# Review and update each July/August.
STATIC_LOAN_RATES = {
    "DE":  0.000,   # BAföG — permanently 0%, fixed by law
    "CA":  0.000,   # Federal NSLSC — 0% since Dec 2023
    "FR":  0.005,   # State-guaranteed bank loan — ~0.5% fixed
    "HK":  0.030,   # NGNL no-gain-no-loss basis — review annually
    "US":  0.0639,  # *** UPDATE EACH JUNE for next academic year ***
                    # Source: studentaid.gov/understand-aid/types/loans/interest-rates
    "SG":  0.036,   # MOE TFL linked to DBS/OCBC/UOB — review quarterly
}


def fetch_exchange_rates() -> tuple[dict, str]:
    """
    Fetch ECB reference rates via frankfurter.app (free, no API key).
    Returns (rates_dict, date_string).
    rates_dict maps currency code → units per 1 USD.
    """
    url = "https://api.frankfurter.app/latest?from=USD&to=GBP,AUD,SGD,HKD,CAD,EUR"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    return payload["rates"], payload["date"]


def fetch_uk_rpi() -> float | None:
    """
    Fetch latest UK RPI (All Items) annual rate from the ONS API.
    Used to calculate Plan 2 (RPI + 3%, capped 6%) and Plan 5 (RPI + 0%) rates.
    Returns the rate as a decimal (e.g. 0.033 for 3.3%), or None on failure.
    """
    # ONS timeseries CZBH = RPI All Items, monthly series
    url = "https://api.ons.gov.uk/v1/datasets/mm23/timeseries/czbh/data"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # 'years' array holds annual data — take the latest full year
        years = data.get("years", [])
        if years:
            latest_year = years[-1]
            rpi_rate = float(latest_year["value"]) / 100
            print(f"  UK RPI: {rpi_rate:.3%} ({latest_year['year']})")
            return rpi_rate
    except Exception as exc:
        print(f"  Warning: Could not fetch UK RPI — {exc}")
    return None


def fetch_australia_cpi() -> float | None:
    """
    Fetch Australia CPI annual indexation rate from the ABS.
    Returns the rate as a decimal (e.g. 0.036 for 3.6%), or None on failure.
    """
    # ABS CPI All Groups, quarterly — series ID 640101
    url = (
        "https://api.data.abs.gov.au/data/CPI/1.10001.10.Q"
        "?startPeriod=2024-Q1&format=jsondata"
    )
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        # Navigate: dataSets[0].series -> find the series with observations
        series_map = payload["dataSets"][0]["series"]
        # Grab the first (and usually only) series
        series = list(series_map.values())[0]
        observations = series["observations"]
        # Observations keyed 0,1,2... in time order; take latest
        latest_idx = str(max(int(k) for k in observations.keys()))
        cpi_value = float(observations[latest_idx][0])
        # ABS CPI All Groups is an index level, not a rate.
        # Use the change vs one year prior (4 quarters ago)
        prior_idx = str(max(0, int(latest_idx) - 4))
        prior_value = float(observations[prior_idx][0])
        cpi_rate = (cpi_value - prior_value) / prior_value
        print(f"  AU CPI annual rate: {cpi_rate:.3%}")
        return round(cpi_rate, 4)
    except Exception as exc:
        print(f"  Warning: Could not fetch AU CPI — {exc}")
    return None


def calculate_tuitions_usd(rates: dict) -> dict:
    """Convert all local tuition amounts to USD at current exchange rates."""
    result = {}
    for key, info in TUITION_LOCAL.items():
        currency = info["currency"]
        local_amount = info["amount"]
        if currency == "USD":
            usd = local_amount
        else:
            fx = rates.get(currency)
            usd = round(local_amount / fx) if fx else None
        result[key] = {
            "local_amount": local_amount,
            "local_currency": currency,
            "usd": usd,
            "note": info["note"],
        }
    return result


def build_loan_rates(uk_rpi: float | None, au_cpi: float | None) -> dict:
    """Merge static rates with freshly-fetched variable rates."""
    rates = dict(STATIC_LOAN_RATES)

    # UK Plan 5: RPI + 0%, no cap
    rates["UK_plan5"] = round(uk_rpi, 4) if uk_rpi is not None else 0.032

    # UK Plan 2: RPI + 3%, hard-capped at 6% from Sep 2026
    if uk_rpi is not None:
        plan2 = uk_rpi + 0.03
        rates["UK_plan2"] = round(min(plan2, 0.06), 4)
    else:
        rates["UK_plan2"] = 0.062

    # Australia HECS-HELP: CPI-indexed (not true interest)
    rates["AU_cpi"] = au_cpi if au_cpi is not None else 0.036

    return rates


def main() -> None:
    print(f"\n{'='*55}")
    print(f"University Cost Data Fetch — {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*55}")

    # 1. Exchange rates
    print("\n[1/3] Fetching exchange rates from frankfurter.app ...")
    rates, rate_date = fetch_exchange_rates()
    for code, val in rates.items():
        print(f"  1 USD = {val} {code}")

    # 2. UK RPI
    print("\n[2/3] Fetching UK RPI from ONS ...")
    uk_rpi = fetch_uk_rpi()

    # 3. Australia CPI
    print("\n[3/3] Fetching Australia CPI from ABS ...")
    au_cpi = fetch_australia_cpi()

    # Build derived values
    tuitions = calculate_tuitions_usd(rates)
    loan_rates = build_loan_rates(uk_rpi, au_cpi)

    print("\n─── Tuition fees (USD) ───")
    for key, t in tuitions.items():
        usd_str = f"${t['usd']:,}" if t["usd"] else "n/a"
        print(f"  {key:12s}  {t['local_amount']:>8,} {t['local_currency']}  →  {usd_str}")

    print("\n─── Loan rates ───")
    for key, rate in loan_rates.items():
        print(f"  {key:12s}  {rate:.2%}")

    # Assemble data.json
    data = {
        "meta": {
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "exchange_rate_date": rate_date,
            "generator": "fetch_data.py via GitHub Actions",
        },
        "exchange_rates_from_usd": rates,
        "tuitions_usd": tuitions,
        "loan_rates": loan_rates,
        "data_sources": {
            "exchange_rates": "frankfurter.app — ECB reference rates, daily",
            "uk_rpi": "ONS MM23 timeseries CZBH — monthly publication",
            "au_cpi": "ABS CPI All Groups quarterly series 640101",
            "us_loan_rate": "US Dept of Education — updated annually each June",
            "tuitions": (
                "HK UGC, UK Office for Students, NCES, "
                "MOE Singapore, ABS, Statistics Canada, MESRI France"
            ),
        },
    }

    # Write output next to this script (i.e. Datablog/data.json)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "data.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Saved → {output_path}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
