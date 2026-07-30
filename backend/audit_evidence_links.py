import sys
import re
import os
import time
import urllib.parse
import pandas as pd
import requests

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'config', 'model_powertrain_review.csv')

def is_generic_url(url):
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return True

    # Split path segments
    segments = [seg for seg in path.split('/') if seg]

    # Check if segments are only language or country codes
    lang_country_codes = {'th', 'en', 'zh', 'th-th', 'en-us', 'en-th', 'th_th', 'en_us'}
    non_lang_segments = [seg for seg in segments if seg.lower() not in lang_country_codes]
    if not non_lang_segments:
        return True

    # Check if we have only one non-language segment and it is generic
    if len(non_lang_segments) == 1:
        generic_segments = {'whatsnew', 'whats-new', 'news', 'home', 'homepage', 'index.html', 'index.php'}
        if non_lang_segments[0].lower() in generic_segments:
            return True

    return False

def get_source_type(url):
    url_lower = url.lower()
    if url_lower.endswith('.pdf') or 'brochure' in url_lower or 'pricelist' in url_lower or 'spec' in url_lower:
        return 'specification'

    news_domains = {
        'headlightmag.com', 'autolifethailand.tv', 'paultan.org', 'springnews.co.th',
        'bitauto.com', 'electrek.co', 'marklines.com', 'thedriven.io', 'car250.com',
        'autoinfo.co.th'
    }
    for domain in news_domains:
        if domain in url_lower:
            return 'article'

    official_domains = {
        'kia.com', 'reverautomotive.com', 'byd.com', 'neta.co.th', 'zeekrlife.com',
        'stellantis.com', 'global-seres.com', 'wulingthai.com'
    }
    for domain in official_domains:
        if domain in url_lower:
            return 'specification'

    return 'article'

def audit():
    try:
        df = pd.read_csv(CSV_PATH)
    except Exception as e:
        print(f"Error reading CSV {CSV_PATH}: {e}")
        sys.exit(1)

    approved = df[df['review_status'] == 'approved']
    url_regex = re.compile(r'https?://[^\s(),;]+')

    total_approved = len(approved)
    checked_count = 0
    passed_count = 0
    failed_count = 0
    skipped_count = 0

    failures = []
    print("brand | raw_model | HTTP status | final URL | source type")
    print("-" * 70)

    for idx, r in approved.iterrows():
        brand = r['brand2']
        raw_model = r['raw_model']
        evidence = str(r['evidence'])

        match = url_regex.search(evidence)
        if not match:
            print(f"{brand} | {raw_model} | SKIPPED_NO_URL | | ")
            skipped_count += 1
            continue

        url = match.group(0).rstrip('.,;)')
        checked_count += 1

        req_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        last_exc = None
        resp = None
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=req_headers, allow_redirects=True, timeout=15)
                break  # success — exit retry loop
            except Exception as exc:
                last_exc = exc
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))  # 1.5s, then 3s
        time.sleep(0.3)  # polite inter-request delay

        if resp is None:
            # All retries exhausted — network/resolution failure
            print(f"{brand} | {raw_model} | ERROR | {url} | {get_source_type(url)}")
            failures.append(f"{brand} | {raw_model} failed request: {last_exc}")
            failed_count += 1
        else:
            status = resp.status_code
            final_url = resp.url

            source_type = get_source_type(final_url)

            if status == 403:
                status_display = "UNVERIFIED"
            else:
                status_display = str(status)

            # Print the required report format
            print(f"{brand} | {raw_model} | {status_display} | {final_url} | {source_type}")

            if not (200 <= status < 300):
                if status == 403:
                    failures.append(f"{brand} | {raw_model} is UNVERIFIED (403): {final_url}")
                else:
                    failures.append(f"{brand} | {raw_model} returns {status}: {final_url}")
                failed_count += 1
            elif is_generic_url(final_url):
                failures.append(f"{brand} | {raw_model} redirected to generic URL: {final_url}")
                failed_count += 1
            else:
                passed_count += 1

    print("-" * 70)
    print(f"Approved rows: {total_approved}")
    print(f"Checked URLs: {checked_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped: {skipped_count}")

    if failures:
        print(f"\nAudit failed with {len(failures)} issues:")
        for fail in failures:
            print(f"  - {fail}")
        sys.exit(1)
    else:
        print("\nAudit passed! All evidence links are active and model-specific.")
        sys.exit(0)

if __name__ == '__main__':
    audit()
