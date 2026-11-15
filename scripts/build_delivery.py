"""Refresh the viewer, mobile ZIP, deployment site and single-file offline viewer."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

subprocess.run([
    str(ROOT / 'tools/web/node_modules/.bin/esbuild'), 'viewer/viewer.js',
    '--bundle', '--format=iife', '--minify',
    '--alias:three/addons=./tools/web/node_modules/three/examples/jsm',
    '--alias:three=./tools/web/node_modules/three', '--outfile=viewer/viewer.bundle.js',
], cwd=ROOT, check=True)
subprocess.run([sys.executable, str(ROOT / 'scripts/package_mobile.py')], cwd=ROOT, check=True)

data = json.loads((ROOT / 'model/design.json').read_text())
# The single-file viewer contains no gallery or drawing files.
data['interior_renderings'] = []
offline = (ROOT / '3d.html').read_text()
offline, count = re.subn(r'(<header>.*?<div>).*?(</div></header>)',
                        r'\1单文件离线3D · 图册与效果图请查看完整方案包\2', offline, count=1, flags=re.S)
assert count == 1, 'Missing offline header'
offline = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', offline, flags=re.S)
for name, content in (
    ('model/design-data.js', 'window.HOUSE_DESIGN=' + json.dumps(data, ensure_ascii=False, indent=2) + ';'),
    ('model/scene-data.js', (ROOT / 'model/scene-data.js').read_text()),
    ('viewer/viewer.bundle.js', (ROOT / 'viewer/viewer.bundle.js').read_text()),
):
    content = re.sub(r'</script', lambda match: '<\\/' + match[0][2:], content, flags=re.I)
    offline, count = re.subn(r'<script src="' + re.escape(name) + r'(?:\?[^"]*)?"></script>',
                            lambda _: '<script>' + content + '</script>', offline)
    assert count == 1, ('Missing offline script', name)


class OfflineLinks(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                assert value.startswith(('data:', '#')), ('Offline resource unavailable', value)


OfflineLinks().feed(offline)
mobile = ROOT / 'delivery/手机查看站点-O'
assert all(p.stat().st_size <= 25 * 1048576 for p in mobile.rglob('*') if p.is_file()), 'Site asset exceeds 25 MiB'
destination = ROOT / 'delivery/院居-3D-单文件离线版.html'
temporary = destination.with_suffix('.html.tmp')
temporary.write_text(offline)
temporary.replace(destination)
shutil.copytree(mobile, ROOT / 'site', dirs_exist_ok=True,
                ignore=shutil.ignore_patterns('.mobile-site-generated'))
print('DELIVERY PASS: viewer, mobile ZIP, site/ and single-file offline viewer refreshed.')
