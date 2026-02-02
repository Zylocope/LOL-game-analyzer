
import requests

teams = ["Cloud9", "100_Thieves", "Gen.G", "T1", "JD_Gaming"]
base_url = "https://lol.fandom.com/wiki/Special:FilePath/"

for t in teams:
    # Try typical patterns
    patterns = [
        f"{t}logo_square.png",
        f"{t}logo_std.png",
        f"{t}logo_profile.png"
    ]
    
    found = False
    for p in patterns:
        url = base_url + p
        try:
            r = requests.head(url, allow_redirects=True, timeout=5)
            if r.status_code == 200:
                content_type = r.headers.get('Content-Type', '')
                if 'image' in content_type:
                    print(f"[SUCCESS] {t} -> {p} -> {r.url}")
                    found = True
                    break
        except:
            pass
    
    if not found:
        print(f"[FAIL] {t}")
