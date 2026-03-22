import os
import requests
from datetime import datetime, timezone, timedelta

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

# 안정적인 무료 API: Frankfurter
# USD 기준으로 KRW, JPY, CNY, EUR를 가져옵니다.
API_URL = "https://api.frankfurter.app/latest?from=USD&to=KRW,JPY,CNY,EUR"

KST = timezone(timedelta(hours=9))

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        # Notion API 버전 헤더 (일반적으로 이 값으로 충분합니다)
        "Notion-Version": "2022-06-28",
    }

def fetch_rates():
    r = requests.get(API_URL, timeout=30)
    r.raise_for_status()
    data = r.json()

    if "rates" not in data:
        raise RuntimeError(f"Unexpected API response (no 'rates'): {data}")

    rates = data["rates"]

    usd_krw = float(rates["KRW"])
    usd_jpy = float(rates["JPY"])
    usd_cny = float(rates["CNY"])
    usd_eur = float(rates["EUR"])  # USD -> EUR

    # EUR/USD = 1 / (USD/EUR)
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

    # 디버깅이 필요하면 아래 2줄을 잠깐 켜세요.
    # print("NOTION STATUS:", resp.status_code)
    # print("NOTION BODY:", resp.text)

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
