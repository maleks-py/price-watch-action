#!/usr/bin/env python3
"""
Full DA Daily Price Index parser - extracts ALL 8 pages, ~150+ items.
Based on your PDF Daily-Price-Index-September-17-2026.pdf which has complete data.

The kauhla321 parser only got 29 items (page 1). This parser gets all pages.

Usage:
  python scripts/parse_da.py --dry-run
  python scripts/parse_da.py --output public/da-prices.json
  python scripts/parse_da.py --pdf /path/to/Daily-Price-Index-September-17-2026.pdf
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
from datetime import datetime, timedelta

import requests

try:
    import pdfplumber
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pdfplumber", "requests"])
    import pdfplumber

DA_LISTING_URL = "https://www.da.gov.ph/price-monitoring/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PalengkeWatch/1.0; +https://github.com/maleks-py/price-watch-app)"
}

CATEGORY_RULES = [
    ("Rice", ("rice", "bigas", "milled", "glutinous", "japonica", "jasponica", "basmati", "benteng", "sinandomeng", "dinorado", "fancy", "premium", "well milled", "regular milled")),
    ("Corn", ("corn", "mais", "grits", "cracked")),
    ("Legumes", ("mungbean", "monggo", "munggo")),
    ("Fish", ("bangus", "tilapia", "galunggong", "alumahan", "sardines", "tamban", "squid", "pusit", "tambakol", "tuna", "mackerel", "milkfish", "shrimp", "hipon", "pampano", "salmon", "tanigue", "bonito", "frigate", "isda")),
    ("Beef", ("beef", "brisket", "chuck", "forequarter", "fore limb", "flank", "loin", "plate", "rib eye", "rib set", "rump", "short ribs", "sirloin", "striploin", "tenderloin", "tongue", "baka")),
    ("Pork", ("pork", "kasim", "liempo", "baboy", "boston shoulder", "chop", "fore shank", "head", "hind leg", "pigue", "hind shank", "loin", "offals", "picnic shoulder", "rind", "skin", "spare ribs", "belly")),
    ("Carabeef", ("carabeef", "carabao")),
    ("Chicken", ("chicken", "manok", "drumstick", "feet", "leg quarter", "liver", "neck", "rind", "thigh", "wing", "whole", "magnolia", "bounty")),
    ("Eggs", ("egg", "itlog", "duck egg")),
    ("Duck", ("duck", "pec kin", "peckin")),
    ("Lowland Vegetables", ("ampalaya", "chilli green", "chili green", "haba", "panigang", "eggplant", "talong", "pechay native", "native pechay", "sitao", "sitaw", "pole sitao", "squash", "kalabasa", "tomato", "kamatis")),
    ("Highland Vegetables", ("bell pepper", "broccoli", "cauliflower", "cabbage", "rare ball", "scorpio", "wonder ball", "carrots", "carrot", "celery", "chayote", "sayote", "habichuelas", "baguio beans", "pechay baguio", "lettuce", "green ice", "iceberg", "romaine", "white potato", "potato", "patatas")),
    ("Spices", ("chilli red", "chili red", "tingala", "tiger chillies", "garlic", "bawang", "ginger", "luya", "red onion", "white onion", "sibuyas")),
    ("Fruits", ("avocado", "banana", "lakatan", "latundan", "saba", "calamansi", "mango", "carabao mango", "melon", "papaya", "pomelo", "watermelon", "pakwan")),
    ("Other", ("salt", "sugar", "cooking oil", "palm", "coconut", "minola", "spring", "jolly")),
]

def classify_category(name: str) -> str:
    t = name.lower()
    for cat, keywords in CATEGORY_RULES:
        if any(kw in t for kw in keywords):
            return cat
    return "Other"

def parse_price(text: str):
    if not text:
        return None
    txt = str(text).strip()
    if txt.lower() in ("n/a", "na", "-", "", "n / a"):
        return None
    # Remove peso, commas
    cleaned = re.sub(r"[₱,\s]", "", txt)
    # Handle range 100-120
    if "-" in cleaned and cleaned.count("-") == 1:
        parts = cleaned.split("-")
        try:
            return round((float(parts[0]) + float(parts[1])) / 2, 2)
        except:
            pass
    try:
        v = float(cleaned)
        return v if 0 < v < 10000 else None
    except:
        return None

def extract_from_pdf(pdf_path: Path):
    items = []
    with pdfplumber.open(pdf_path) as pdf:
        print(f"PDF has {len(pdf.pages)} pages")
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []

            # Method 1: Try tables first
            if tables:
                for table in tables:
                    if not table or len(table) < 2:
                        continue
                    # Find header row
                    header_idx = 0
                    for i, row in enumerate(table[:3]):
                        row_text = " ".join([str(c or "") for c in row]).lower()
                        if any(k in row_text for k in ["commodity", "prevailing", "price", "specification"]):
                            header_idx = i
                            break

                    for row in table[header_idx+1:]:
                        if not row or len(row) < 2:
                            continue
                        # Row like [Commodity, Specification, Price]
                        # Commodity could be first column, price last column
                        commodity = str(row[0] or "").strip() if len(row) > 0 else ""
                        spec = str(row[1] or "").strip() if len(row) > 1 else ""
                        price_cell = str(row[-1] or "").strip() if len(row) > 0 else ""

                        # Skip empty or category headers
                        if not commodity or commodity.upper() == commodity and len(commodity) < 25 and not parse_price(price_cell):
                            # Might be category header like "BEEF MEAT PRODUCTS" - skip
                            if len(commodity) < 30 and commodity.isupper():
                                continue

                        # Build full product name
                        full_name = commodity
                        if spec and spec.lower() not in ("n/a", "", "n / a") and len(spec) < 60:
                            # Avoid duplicating if spec already in commodity
                            if spec.lower() not in commodity.lower():
                                full_name = f"{commodity} {spec}".strip()

                        price = parse_price(price_cell)
                        # If price not in last column, search row from right
                        if price is None:
                            for cell in reversed(row):
                                p = parse_price(cell)
                                if p:
                                    price = p
                                    break

                        if full_name and price:
                            full_name = re.sub(r"\s+", " ", full_name).strip()
                            full_name = re.sub(r"[ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹*†‡§¶]+$", "", full_name).strip()
                            if 3 <= len(full_name) <= 100 and not full_name.lower().startswith("commodity") and not full_name.lower().startswith("note"):
                                # Avoid duplicates
                                if not any(ex["product"].lower() == full_name.lower() for ex in items):
                                    items.append({
                                        "product": full_name,
                                        "price": price,
                                        "unit": "kg",
                                        "category": classify_category(full_name),
                                        "page": page_num+1
                                    })

            # Method 2: Fallback text parsing for rows missed by table
            # Pattern: Product name ... price at end of line
            for line in text.split("\n"):
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                # Skip headers/footers
                if any(k in line.lower() for k in ["department of agriculture", "daily price index", "national capital region", "prevailing retail price", "commodity", "specification", "page", "note(s):", "prevailing price is defined", "covered markets", "n/a - not available"]):
                    continue
                # Skip market list
                if re.match(r"^\d+\.\s+.*Market", line):
                    continue
                # Try to extract price at end: "Product Name  123.45"
                m = re.search(r"^(.+?)\s+(\d+\.\d+|\d+)\s*$", line)
                if m:
                    name = m.group(1).strip()
                    price = parse_price(m.group(2))
                    # Filter
                    if name and price and 3 <= len(name) <= 100:
                        # Remove leading numbers like "1.  Agora"
                        name = re.sub(r"^\d+\s+", "", name).strip()
                        if not any(x in name.lower() for x in ["imported commercial rice", "local commercial rice", "corn products", "fish products", "beef meat", "pork meat", "other livestock", "poultry products", "lowland vegetables", "highland vegetables", "spices", "fruits", "other basic"]):
                            if not any(ex["product"].lower() == name.lower() for ex in items):
                                items.append({
                                    "product": name,
                                    "price": price,
                                    "unit": "kg",
                                    "category": classify_category(name),
                                    "page": page_num+1
                                })

    # Deduplicate by product name lower, keep last (most recent page)
    deduped = {}
    for it in items:
        key = it["product"].lower()
        # Keep highest price? Or last occurrence? Keep last
        deduped[key] = it

    result = list(deduped.values())
    result.sort(key=lambda x: (x["category"], x["product"]))
    return result

def find_latest_pdf_url(session: requests.Session):
    print(f"Fetching {DA_LISTING_URL}...")
    try:
        resp = session.get(DA_LISTING_URL, timeout=30)
        resp.raise_for_status()
        html = resp.text
        # Look for Daily Price Index PDFs in 2026/09 folder
        # Pattern: https://www.da.gov.ph/wp-content/uploads/2026/09/Daily-Price-Index-September-17-2026.pdf
        pdf_pattern = r'href=["\'](https://www\.da\.gov\.ph/wp-content/uploads/2026/09/[^"\']*Daily-Price-Index[^"\']*\.pdf)["\']'
        matches = re.findall(pdf_pattern, html, re.IGNORECASE)
        if matches:
            # Sort by date in filename, get latest
            print(f"Found {len(matches)} PDFs from listing")
            # Return most recent (last in list usually newest)
            return matches[0]

        # Fallback: any Daily Price Index PDF
        general_pattern = r'href=["\']([^"\']*Daily-Price-Index[^"\']*\.pdf)["\']'
        general_matches = re.findall(general_pattern, html, re.IGNORECASE)
        if general_matches:
            urls = [m if m.startswith("http") else urljoin(DA_LISTING_URL, m) for m in general_matches]
            print(f"Found {len(urls)} general DPI PDFs")
            return urls[0]

    except Exception as e:
        print(f"Failed to fetch listing: {e}")

    # Fallback: try yesterday and today patterns
    for days_ago in range(0, 7):
        date = datetime.now() - timedelta(days=days_ago)
        # Try both September and current month
        for month in [date.strftime("%m"), "09"]:
            url = f"https://www.da.gov.ph/wp-content/uploads/2026/{month}/Daily-Price-Index-{date.strftime('%B-%d-%Y')}.pdf"
            print(f"Trying {url}...")
            try:
                r = session.head(url, timeout=10)
                if r.status_code == 200:
                    print(f"Found via pattern: {url}")
                    return url
            except:
                continue
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output", default="public/da-prices.json")
    parser.add_argument("--pdf", help="Local PDF to parse")
    args = parser.parse_args()

    session = requests.Session()
    session.headers.update(HEADERS)

    pdf_path = None
    pdf_url = None

    if args.pdf:
        pdf_path = Path(args.pdf)
        print(f"Using local PDF: {pdf_path}")
    else:
        pdf_url = find_latest_pdf_url(session)
        if not pdf_url:
            print("No PDF URL found, trying known Sep 17 URL...")
            pdf_url = "https://www.da.gov.ph/wp-content/uploads/2026/09/Daily-Price-Index-September-17-2026.pdf"

        print(f"Downloading {pdf_url}...")
        try:
            resp = session.get(pdf_url, timeout=60)
            resp.raise_for_status()
            pdf_path = Path("/tmp/da-dpi.pdf")
            pdf_path.write_bytes(resp.content)
            print(f"Downloaded {len(resp.content)} bytes to {pdf_path}")
        except Exception as e:
            print(f"Download failed: {e}")
            sys.exit(1)

    if not pdf_path or not pdf_path.exists():
        print("No PDF to parse")
        sys.exit(1)

    items = extract_from_pdf(pdf_path)
    print(f"\nExtracted {len(items)} items total")

    by_cat = {}
    for it in items:
        by_cat[it["category"]] = by_cat.get(it["category"], 0) + 1

    print("\nBy category:")
    for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}")

    # Also show mapping to our products
    # Import mapping from remotePrices logic (simplified)
    print("\nSample items:")
    for it in items[:20]:
        print(f"  {it['category']:20} | {it['product']:50} | ₱{it['price']}")

    payload = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "DA Daily Price Index",
        "source_url": pdf_url or "https://www.da.gov.ph/price-monitoring/",
        "updated_at": datetime.now().isoformat(),
        "items": [{"category": i["category"], "product": i["product"], "price": i["price"], "unit": i["unit"]} for i in items],
        "meta": {
            "total_items": len(items),
            "by_category": by_cat,
            "pdf_url": pdf_url,
            "parser": "PalengkeWatch full parser v1 - all 8 pages"
        }
    }

    if args.dry_run:
        print("\n--- DRY RUN OUTPUT (first 5000 chars) ---")
        print(json.dumps(payload, indent=2)[:5000])
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote {out} with {len(items)} items")

if __name__ == "__main__":
    main()
