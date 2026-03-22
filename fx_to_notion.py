import os
import requests
from datetime import datetime, timezone, timedelta

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

API_URL = "https://api.frankfurter.app/latest?from=USD&to=KRW,JPY,CNY,EUR"
KST = timezone(timedelta(hours=9))

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }

def fetch_rates():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()
    data = r.json()

    if "rates" not in data:
        raise RuntimeError(f"Unexpected API response: {data}")

    rates = data["rates"]
    usd_krw = float(rates["KRW"])
    usd_jpy = float(rates["JPY"])
    usd_cny = float(rates["CNY"])
    usd_eur = float(rates["EUR"])  # USD -> EUR
    eur_usd = 1.0 / usd_eur if usd_eur != 0 else None

    return {
        "usd_krw": usd_krw,
        "usd_jpy": usd_jpy,
        "usd_cny": usd_cny,
        "eur_usd": eur_usd,
        "source": API_URL,
    }

def create_page(record_date_str, rates):
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Record": {"title": [{"text": {"content": record_date_str}}]},
            "Date": {"date": {"start": record_date_str}},
            "USD/KRW": {"number": round(rates["usd_krw"], 4)},
            "USD/JPY": {"number": round(rates["usd_jpy"], 4)},
            "USD/CNY": {"number": round(rates["usd_cny"], 4)},
            "EUR/USD": {"number": round(rates["eur_usd"], 6) if rates["eur_usd"] is not None else None},
            "Source": {"url": rates["source"]},
        },
    }

    resp = requests.post(url, headers=notion_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def main():
    now_kst = datetime.now(KST)
    record_date_str = now_kst.strftime("%Y-%m-%d")
    rates = fetch_rates()
    create_page(record_date_str, rates)
    print("OK", record_date_str, rates)

if __name__ == "__main__":
    main()
