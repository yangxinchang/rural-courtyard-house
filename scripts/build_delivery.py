"""Stage and verify the full, mobile and offline deliveries before replacing them."""
from pathlib import Path
from html.parser import HTMLParser
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = 'viewer/viewer.bundle.js'
OFFLINE = 'delivery/院居-3D-单文件离线版.html'
FULL_ZIP = 'delivery/农村院落住宅-玻璃顶深化-完整方案.zip'
MOBILE_ZIP = 'delivery/农村院落住宅-O-手机查看包.zip'
MOBILE_SITE = 'delivery/手机查看站点-O'
MOBILE_REPORT = 'check/mobile-package-report.json'
GLB = 'model/courtyard-house.glb'
PDF = 'drawings/农村院落住宅-水电深化P.pdf'


class Links(HTMLParser):
    def __init__(self, path, stage):
        super().__init__()
        self.path = path
        self.stage = stage

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ('href', 'src') or not value:
                continue
            if self.path == self.stage / OFFLINE:
                assert value.startswith(('data:', '#')), ('Offline resource unavailable', value)
                continue
            url = urlsplit(value)
            if not url.scheme and not url.netloc and url.path:
                target = (self.path.parent / unquote(url.path)).resolve()
                assert target.is_relative_to(self.stage) and target.is_file(), ('Missing full-package link', self.path.name, value)


def write_offline(stage):
    data = json.loads((stage / 'model/design.json').read_text())
    data['interior_renderings'] = []
    offline = (stage / '3d.html').read_text()
    offline, count = re.subn(r'(<header>.*?<div>).*?(</div></header>)',
                            r'\1单文件离线3D · 图册与效果图请查看完整方案包\2', offline, count=1, flags=re.S)
    assert count == 1, 'Missing offline header'
    offline = re.sub(r'<a\b[^>]*>(.*?)</a>', r'\1', offline, flags=re.S)
    for name, content in (
        ('model/design-data.js', 'window.HOUSE_DESIGN=' + json.dumps(data, ensure_ascii=False, indent=2) + ';'),
        ('model/scene-data.js', (stage / 'model/scene-data.js').read_text()),
        (BUNDLE, (stage / BUNDLE).read_text()),
    ):
        content = re.sub(r'</script', lambda match: '<\\/' + match[0][2:], content, flags=re.I)
        offline, count = re.subn(r'<script src="' + re.escape(name) + r'(?:\?[^"]*)?"></script>',
                                lambda _: '<script>' + content + '</script>', offline)
        assert count == 1, ('Missing offline script', name)
    (stage / OFFLINE).write_text(offline)


def build():
    files = (ROOT / 'docs/delivery-files.txt').read_text().splitlines()
    files = [name.strip() for name in files if name.strip() and not name.lstrip().startswith('#')]
    assert len(files) == len(set(files)), 'Duplicate full-package entry'
    for name in files:
        path = Path(name)
        assert not path.is_absolute() and '..' not in path.parts, ('Invalid delivery path', name)
        assert path.parts[0] not in {'test', 'tests', 'check', 'tmp', 'tools'}, ('Local-only delivery path', name)
        if name not in (BUNDLE, OFFLINE):
            assert (ROOT / name).is_file(), ('Missing delivery source', name)
    assert {BUNDLE, OFFLINE, GLB, PDF} <= set(files), 'Incomplete full-package manifest'
    mobile = ROOT / MOBILE_SITE
    if mobile.exists():
        assert (mobile / '.mobile-site-generated').is_file(), 'Refusing to replace an unowned mobile site'

    with TemporaryDirectory(prefix='.build-', dir=ROOT / 'delivery') as temp:
        stage = Path(temp)
        for name in files:
            if name in (BUNDLE, OFFLINE):
                continue
            destination = stage / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, destination)
        (stage / 'tools').symlink_to(ROOT / 'tools', target_is_directory=True)
        (stage / 'delivery').mkdir(exist_ok=True)
        subprocess.run([
            str(stage / 'tools/web/node_modules/.bin/esbuild'), 'viewer/viewer.js',
            '--bundle', '--format=iife', '--minify',
            '--alias:three/addons=./tools/web/node_modules/three/examples/jsm',
            '--alias:three=./tools/web/node_modules/three', f'--outfile={BUNDLE}',
        ], cwd=stage, check=True)
        subprocess.run([sys.executable, str(stage / 'scripts/package_mobile.py')], cwd=stage, check=True)
        write_offline(stage)
        for name in files:
            if name.endswith('.html'):
                page = stage / name
                Links(page, stage).feed(page.read_text())

        staged_mobile = stage / MOBILE_SITE
        assert all(p.stat().st_size <= 25 * 1048576 for p in staged_mobile.rglob('*') if p.is_file()), 'Site asset exceeds 25 MiB'
        with ZipFile(stage / FULL_ZIP, 'w', ZIP_DEFLATED) as archive:
            for name in files:
                archive.write(stage / name, name)
        with ZipFile(stage / FULL_ZIP) as full, ZipFile(stage / MOBILE_ZIP) as small:
            assert full.testzip() is None, 'Corrupt full archive'
            for name in (GLB, PDF):
                assert full.read(name) == small.read(name), ('Delivery versions differ', name)

        # shortcut: publication is per file, not crash-atomic across all workspace outputs.
        (ROOT / 'check').mkdir(exist_ok=True)
        for name in (BUNDLE, OFFLINE, FULL_ZIP, MOBILE_ZIP, MOBILE_REPORT):
            (stage / name).replace(ROOT / name)
        shutil.copytree(staged_mobile, ROOT / 'site', dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('.mobile-site-generated'))
        if mobile.exists():
            mobile.rename(stage / 'previous-mobile-site')
        staged_mobile.rename(mobile)
    print(f'DELIVERY PASS: {FULL_ZIP}, mobile ZIP, site/ and single-file offline viewer refreshed.')


if __name__ == '__main__':
    build()
