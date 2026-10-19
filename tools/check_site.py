#!/usr/bin/env python3
"""Check local support-page references and fragment links without contacting external services."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.links = set(), []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get('id'):
            self.ids.add(values['id'])
        for name in ['href', 'src']:
            if values.get(name):
                self.links.append(values[name])


pages = {path: Page(path.read_text()) for path in root.glob('*.html')}
errors = []
for path, page in pages.items():
    for link in page.links:
        target = urlsplit(link)
        if target.scheme or target.netloc:
            continue
        resolved = (path.parent / unquote(target.path)).resolve() if target.path else path
        if not resolved.is_relative_to(root) or not resolved.is_file():
            errors.append(f'{path.name}: missing or outside local target {link}')
        elif target.fragment and resolved in pages and unquote(target.fragment) not in pages[resolved].ids:
            errors.append(f'{path.name}: missing fragment {link}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Checked {len(pages)} support pages and their local links/assets')
