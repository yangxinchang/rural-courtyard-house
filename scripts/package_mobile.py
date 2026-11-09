"""Build a self-contained HTTP(S) viewing site; keeps the full design delivery intact."""
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED
from html import escape
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import base64, hashlib, json, re, shutil
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'delivery/手机查看站点-O'
ARCHIVE=ROOT/'delivery/农村院落住宅-O-手机查看包.zip'
SOURCE=['3d.html','viewer/viewer.bundle.js','model/design-data.js','model/courtyard-house.glb']
hashfile=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline={name:hashfile(ROOT/name) for name in SOURCE}
data=json.loads((ROOT/'model/design.json').read_text())
assert data==json.loads((ROOT/'model/design-data.js').read_text().split('=',1)[1].strip().rstrip(';'))
assert base64.b64decode((ROOT/'model/scene-data.js').read_text().split("'",2)[1])==(ROOT/'model/courtyard-house.glb').read_bytes()
manifest=json.loads((ROOT/'精装效果图/manifest.json').read_text())
css='''*{box-sizing:border-box}body{margin:0;background:#f6f8f3;color:#233c32;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1000px;margin:auto;padding:24px 18px}h1{font:500 32px/1.3 serif;margin:18px 0}h2{font-size:21px;font-weight:500}p{color:#60736a}a{color:inherit;text-underline-offset:4px}nav{display:flex;flex-wrap:wrap;gap:12px}.button{display:inline-block;padding:12px 18px;border:1px solid #233c32;border-radius:5px;text-decoration:none}.primary{background:#233c32;color:white}.hero{width:100%;height:auto;border-radius:6px;margin:20px 0}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}figure{margin:0}figure img{display:block;width:100%;height:auto}figcaption{margin-top:7px}small{color:#60736a}a:focus-visible{outline:3px solid #a77f42;outline-offset:3px}@media(max-width:600px){.gallery{grid-template-columns:1fr}h1{font-size:28px}}'''
def page(title,body):
 return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,"><title>'+title+'</title><style>'+css+'</style></head><body><main>'+body+'</main></body></html>'

with TemporaryDirectory(prefix='house-mobile-') as temp:
 site=Path(temp)
 def write(name,content):
  p=site/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
 def copy(name):
  p=site/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,p)
 for name in ['viewer/viewer.bundle.js','model/courtyard-house.glb','vendor/three-LICENSE.txt']:copy(name)
 html=(ROOT/'3d.html').read_text().replace('src="model/scene-data.js"','src="model/model-url.js"').replace('>全部方案</a>','>手机使用说明</a>')
 html=re.sub(r'<a href="drawings/农村院落住宅-装修方案[FG]\.pdf">.*?</a>','历史版本见完整方案包',html)
 pdfs=list(dict.fromkeys(re.findall(r'href="(drawings/[^"]+\.pdf)"',html)))
 assert pdfs,'Missing current drawing PDF link'
 for name in pdfs:
  baseline[name]=hashfile(ROOT/name);copy(name)
 primary_pdf=pdfs[0]
 html=html.replace('<title>','<link rel="icon" href="data:,"><title>',1)
 write('3d.html',html)
 write('model/model-url.js',"window.HOUSE_MODEL_URL='model/courtyard-house.glb';\n")
 for view in data['interior_renderings']:view['path']=view['path'].replace('.png','.jpg')
 write('model/design-data.js','window.HOUSE_DESIGN='+json.dumps(data,ensure_ascii=False)+';')
 cards=[]
 for v in manifest['views']:
  name='精装效果图/'+Path(v['file']).with_suffix('.jpg').name
  p=site/name;p.parent.mkdir(parents=True,exist_ok=True)
  with Image.open(ROOT/'精装效果图'/v['file']) as im:
   im=im.convert('RGB');im.thumbnail((1280,720));im.save(p,quality=83,optimize=True)
  cards.append(f'<figure><a href="{escape(p.name)}"><img src="{escape(p.name)}" alt="{escape(v["name"])}" loading="lazy" width="1280" height="720"></a><figcaption>{escape(v["name"])}</figcaption></figure>')
 write('精装效果图/index.html',page('院居 · 手机精装效果图','<nav><a href="../index.html">使用说明</a><a href="../3d.html">交互3D</a></nav><h1>室内精装效果</h1><p>手机版图片，可点开查看。高清原图保留在完整方案包。</p><div class="gallery">'+''.join(cards)+'</div>'))
 cards=[]
 exterior_sources=sorted((ROOT/'renders').glob('*.png'))
 for source in exterior_sources:
  name='renders/'+source.with_suffix('.jpg').name;p=site/name;p.parent.mkdir(parents=True,exist_ok=True)
  with Image.open(source) as im:
   im=im.convert('RGB');im.thumbnail((1280,960));im.save(p,quality=83,optimize=True)
  cards.append(f'<figure><a href="{p.name}"><img src="{p.name}" alt="建筑与功能效果 {source.stem[:2]}" loading="lazy" width="1280" height="960"></a></figure>')
 write('renders/index.html',page('院居 · 外观与功能效果','<nav><a href="../index.html">使用说明</a><a href="../3d.html">交互3D</a></nav><h1>院落、亭子与洗衣区</h1><div class="gallery">'+''.join(cards)+'</div>'))
 first_load=sum((site/n).stat().st_size for n in ['3d.html','viewer/viewer.bundle.js','model/design-data.js','model/model-url.js','model/courtyard-house.glb'])/1048576
 pending_docs=list(dict.fromkeys(re.findall(r'href="(docs/[^"]+\.md)"',html)))
 copied_docs=set()
 while pending_docs:
  name=pending_docs.pop(0)
  if name in copied_docs:continue
  copied_docs.add(name);baseline[name]=hashfile(ROOT/name)
  text=(ROOT/name).read_text()
  text=re.sub(r'(\]\(\.\./renders/[^)]+)\.png\)',r'\1.jpg)',text)
  for target in re.findall(r'\]\(([^)]+)\)',text):
   u=urlsplit(target)
   if not u.scheme and u.path:
    linked=(ROOT/name).parent.joinpath(unquote(u.path)).resolve().relative_to(ROOT)
    if linked.parts[0]=='docs' and linked.suffix=='.md':pending_docs.append(str(linked))
  write(name,text)
 write('index.html',page('院居 · 手机查看',f'''<small>院居 / O版手机查看</small><h1>把家放在手中看。</h1><p>旋转院落、走进房间，查看装修、门窗、亭子与洗衣区。</p><nav><a class="button primary" href="3d.html">打开交互3D</a><a class="button" href="精装效果图/index.html">看室内效果图</a><a class="button" href="renders/index.html">看院落与亭子</a></nav><img class="hero" src="renders/01-aerial.jpg" alt="院落整体效果"><h2>手机怎么操作</h2><ol><li>单指拖动旋转，双指缩放或平移。</li><li>竖屏时，控制区在3D画面下方；横屏时在左侧。</li><li>选择楼层或房间，点击“室内视角”看装修。</li><li>点门窗可开关，也可使用门窗列表。用“恢复整屋”回到初始视角。</li><li>在“太阳与光影”开启日照，可拖动时间或播放日轨，进入房间查看窗影；画面内可暂停或关闭。</li></ol><p>首次打开3D需加载约{first_load:.1f} MiB，建议使用Wi-Fi。若手机出现卡顿，可先看静态效果图；文件预览中未显示3D时，用浏览器打开网站链接。</p><nav><a href="{escape(primary_pdf)}">查看当前装修图册</a></nav><p><small>设计效果示意，尺寸与施工条件仍需实测深化。</small></p>'''))
 write('README.txt','手机交付包必须部署或用本地HTTP服务器打开。部署时上传本目录内容，index.html为入口，分享部署后的HTTPS链接。不要仅发送3d.html，也不要让手机直接运行ZIP预览。所有模型/贴图/运行依赖已包含；无外部CDN。此包不含Blender源文件及历史图册。\n')
 write('.mobile-site-generated','Generated by scripts/package_mobile.py\n')
 class Links(HTMLParser):
  def handle_starttag(self,tag,attrs):
   for key,value in attrs:
    if key not in ('href','src') or not value:continue
    u=urlsplit(value)
    if not u.scheme and u.path:assert (self.source.parent/unquote(u.path)).exists(),(self.source,value)
 for p in site.rglob('*.html'):
  parser=Links();parser.source=p;parser.feed(p.read_text())
 for doc in site.rglob('*.md'):
  for target in re.findall(r'\]\(([^)]+)\)',doc.read_text()):
   u=urlsplit(target)
   if not u.scheme and u.path:assert doc.parent.joinpath(unquote(u.path)).exists(),(doc,target)
 for v in data['interior_renderings']:assert (site/v['path']).exists(),v
 assert all(hashfile(ROOT/name)==h for name,h in baseline.items()),'Source changed during build; run again.'
 if OUT.exists():
  assert (OUT/'.mobile-site-generated').exists(),'Refusing to replace an unowned folder'
  shutil.rmtree(OUT)
 shutil.copytree(site,OUT)
files=sorted(p for p in OUT.rglob('*') if p.is_file())
with ZipFile(ARCHIVE,'w',ZIP_DEFLATED) as archive:
 for p in files:archive.write(p,p.relative_to(OUT))
 assert archive.testzip() is None
report=dict(version='O-mobile',files=len(files),interior_images=len(manifest['views']),exterior_and_detail_images=len(exterior_sources),site_bytes=sum(p.stat().st_size for p in files),zip_bytes=ARCHIVE.stat().st_size,first_3d_load_mib=round(first_load,2),largest_asset_mib=round(max(p.stat().st_size for p in files)/1048576,2),zip_sha256=hashfile(ARCHIVE),source_hashes=baseline,all_local_links_valid=True,publicly_deployed=False,path=str(ARCHIVE.relative_to(ROOT)))
(ROOT/'check/mobile-package-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
