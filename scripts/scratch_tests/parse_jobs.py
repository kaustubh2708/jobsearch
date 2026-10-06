import urllib.request
import json
import re

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, ' ', raw_html)

jobs_to_check = [
    ('stripe', 8031833),
    ('stripe', 8209970),
    ('stripe', 7543868),
    ('rubrik', 8166523),
    ('rubrik', 8166537),
    ('rubrik', 7956918),
    ('coinbase', 8165441),
    ('coinbase', 7985187)
]

for board, jid in jobs_to_check:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            title = data.get('title')
            content = clean_html(data.get('content', ''))
            # search for experience or graduation requirements
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            text_summary = ' '.join(content.split()[:200])
            print(f"=== {board.upper()} {jid}: {title} ===")
            print(f"URL: {data.get('absolute_url')}")
            # print snippets mentioning degree, year, experience
            for sentence in re.split(r'\. |\n', content):
                if any(w in sentence.lower() for w in ['year', 'graduat', 'bachelor', 'intern', 'experience', 'python', 'sql', '0-']):
                    print(f"  * {sentence.strip()[:150]}")
            print("\n")
    except Exception as e:
        print(f"Error {board} {jid}: {e}")
