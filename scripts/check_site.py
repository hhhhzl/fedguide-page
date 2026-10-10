"""Check published relative URLs and all data-backed media before deployment."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[1] / "dist"
paths = set()

class Assets(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in {"src", "href", "poster"} and value:
                url = urlsplit(value)
                if not url.scheme and not url.netloc and url.path:
                    paths.add(unquote(url.path))

Assets().feed((root / "index.html").read_text())
demos = json.loads((root / "demo-data.json").read_text())
results = json.loads((root / "results-data.json").read_text())
clips = 0
for env in demos["environments"]:
    paths.add(env["poster"])
    for method in env["methods"]:
        for client in env["clients"]:
            clip = method["videos"][str(client["id"])]
            paths.update((clip["src"], clip["poster"]))
            clips += 1
for env in results["environments"]:
    paths.add(env["curve"])
paths.update(("demo-data.json", "results-data.json"))
for path in paths:
    target = (root / path).resolve()
    assert target.is_relative_to(root.resolve()), f"Asset escapes site: {path}"
    assert target.is_file() and target.stat().st_size > 0, f"Missing or empty asset: {path}"
print(f"Validated {len(paths)} local resources, including {clips} client recordings.")
