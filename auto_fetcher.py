import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

STATE_SLUGS = {'AL': 'alabama', 'AK': 'alaska', 'AZ': 'arizona', 'AR': 'arkansas', 'CA': 'california', 'CO': 'colorado', 'CT': 'connecticut', 'DE': 'delaware', 'DC': 'district-of-columbia', 'FL': 'florida', 'GA': 'georgia', 'ID': 'idaho', 'IL': 'illinois', 'IN': 'indiana', 'IA': 'iowa', 'KS': 'kansas', 'KY': 'kentucky', 'LA': 'louisiana', 'ME': 'maine', 'MD': 'maryland', 'MA': 'massachusetts', 'MI': 'michigan', 'MN': 'minnesota', 'MS': 'mississippi', 'MO': 'missouri', 'MT': 'montana', 'NE': 'nebraska', 'NH': 'new-hampshire', 'NJ': 'new-jersey', 'NM': 'new-mexico', 'NY': 'new-york', 'NC': 'north-carolina', 'ND': 'north-dakota', 'OH': 'ohio', 'OK': 'oklahoma', 'OR': 'oregon', 'PA': 'pennsylvania', 'RI': 'rhode-island', 'SC': 'south-carolina', 'SD': 'south-dakota', 'TN': 'tennessee', 'TX': 'texas', 'VT': 'vermont', 'VA': 'virginia', 'WA': 'washington', 'WV': 'west-virginia', 'WI': 'wisconsin', 'WY': 'wyoming'}

HEADERS = {
    "User-Agent": "Mozilla/5.0 LotteryForecastEngine/1.0"
}

def _clean_number(text, length):
    digits = re.findall(r"\d", str(text))
    if len(digits) >= length:
        return "".join(digits[:length])
    return None

def fetch_lotteryusa_results(state_code, game="pick3", draw="both", limit=80):
    state_code = state_code.upper()
    if state_code not in STATE_SLUGS:
        raise ValueError("Unsupported state code.")

    slug = STATE_SLUGS[state_code]
    game_slug = "pick-3" if game.lower() == "pick3" else "pick-4"

    urls = []
    if draw.lower() in ["midday", "both"]:
        urls.append((f"https://www.lotteryusa.com/{slug}/{game_slug}-midday/", "midday"))
    if draw.lower() in ["evening", "both"]:
        urls.append((f"https://www.lotteryusa.com/{slug}/{game_slug}/", "evening"))

    rows = []
    length = 3 if game.lower() == "pick3" else 4

    for url, draw_name in urls:
        html = requests.get(url, headers=HEADERS, timeout=20).text
        soup = BeautifulSoup(html, "html.parser")
        page_text = soup.get_text("\n", strip=True)

        # Primary parser: look for date blocks followed by digit groups.
        date_pattern = r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})"
        matches = list(re.finditer(date_pattern, page_text))

        for idx, match in enumerate(matches):
            date_text = match.group(2)
            block_start = match.end()
            block_end = matches[idx + 1].start() if idx + 1 < len(matches) else min(len(page_text), block_start + 500)
            block = page_text[block_start:block_end]
            digits = re.findall(r"(?<!\d)(\d)(?!\d)", block)

            if len(digits) >= length:
                number = "".join(digits[:length])
                try:
                    date = datetime.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
                except Exception:
                    date = date_text

                rows.append({
                    "date": date,
                    "state": state_code,
                    "game": game.lower(),
                    "draw": draw_name,
                    "number": number
                })

        # Backup parser: HTML tables if present.
        try:
            tables = pd.read_html(html)
            for table in tables:
                for _, r in table.iterrows():
                    joined = " ".join(str(x) for x in r.values)
                    number = _clean_number(joined, length)
                    if number:
                        rows.append({
                            "date": "",
                            "state": state_code,
                            "game": game.lower(),
                            "draw": draw_name,
                            "number": number
                        })
        except Exception:
            pass

    df = pd.DataFrame(rows).drop_duplicates()
    if not df.empty:
        df = df.head(limit)
    return df

def sample_data(state_code="SC", game="pick3"):
    data = [
        ["2026-05-10", state_code, game, "evening", "040"],
        ["2026-05-09", state_code, game, "midday", "838"],
        ["2026-05-09", state_code, game, "evening", "836"],
        ["2026-05-08", state_code, game, "midday", "928"],
        ["2026-05-08", state_code, game, "evening", "223"],
        ["2026-05-07", state_code, game, "midday", "744"],
        ["2026-05-07", state_code, game, "evening", "910"],
        ["2026-05-06", state_code, game, "midday", "840"],
        ["2026-05-06", state_code, game, "evening", "087"],
        ["2026-05-05", state_code, game, "evening", "023"],
        ["2026-05-04", state_code, game, "evening", "302"],
        ["2026-05-03", state_code, game, "evening", "528"],
        ["2026-05-02", state_code, game, "evening", "673"],
        ["2026-05-01", state_code, game, "evening", "935"],
    ]
    return pd.DataFrame(data, columns=["date", "state", "game", "draw", "number"])