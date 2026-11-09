"""Validate rendered interiors and build an offline image gallery and overview."""
from pathlib import Path
from html import escape
import json
from PIL import Image,ImageDraw,ImageFont,ImageOps
from interior_views import INTERIOR_VIEWS
from material_recommendations import material_advice_html

ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'精装效果图'
data=json.loads((folder/'manifest.json').read_text())
views=data['views']
assert data['version']=='O' and len(views)==len(INTERIOR_VIEWS)
assert {view['id'] for view in views}=={view['id'] for view in INTERIOR_VIEWS},'效果图机位清单不完整'
font_path='/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'
font=ImageFont.truetype(font_path,24)
small=ImageFont.truetype(font_path,17)
overview=Image.new('RGB',(1800,1940),'#f3efe6')
draw=ImageDraw.Draw(overview)
draw.text((36,23),'院居 · 家具与装修细节深化',font=ImageFont.truetype(font_path,36),fill='#293c33')
draw.text((38,77),'Q版浅色 · 浅橡木／暖白／米色织物 · 后排石纹砖 · 晾衣亭浅色顶棚',font=font,fill='#71665a')
cards=[]
for i,view in enumerate(views):
    name=view['file']
    assert Path(name).name==name and name.endswith('.png'),name
    with Image.open(folder/name) as image:
        assert image.size==(2560,1440),(name,image.size)
        thumb=ImageOps.fit(image.convert('RGB'),(552,310))
    x=36+(i%3)*588;y=130+(i//3)*355
    overview.paste(thumb,(x,y));draw.text((x,y+319),view['name'],font=font,fill='#293c33')
    cards.append(f'<figure><a href="{escape(name)}"><img src="{escape(name)}" alt="{escape(view["name"])}精装设计效果" width="2560" height="1440" loading="lazy"></a><figcaption>{escape(view["name"])}<a href="{escape(name)}" download>保存原图</a></figcaption></figure>')
    if view.get('note'):
        cards[-1]=cards[-1].replace('</figure>',f'<p>{escape(view["note"])}</p></figure>')
draw.text((36,1910),'设计渲染，非已施工照片；家具、软装与灯具规格以选样和深化设计为准。',font=small,fill='#71665a')
overview.save(folder/'00-精装总览.jpg',quality=93)
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>院居 · 浅色精装效果图</title><style>
*{box-sizing:border-box}body{margin:0;background:#f3efe6;color:#293c33;font:15px/1.7 "Noto Sans CJK SC","Microsoft YaHei",sans-serif}a{color:inherit;text-underline-offset:5px}a:focus-visible{outline:3px solid #a8824c;outline-offset:5px}header,main,footer{max-width:1440px;margin:auto;padding:24px 32px}header{display:flex;justify-content:space-between;gap:20px;border-bottom:1px solid #d1c8b9}nav{display:flex;gap:22px;flex-wrap:wrap}.intro{padding:26px 0 28px;max-width:850px}h1{font:500 clamp(30px,5vw,56px)/1.2 "Noto Serif CJK SC",serif;margin:0 0 18px}p{color:#71665a;margin:8px 0}.gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:34px 24px}figure{margin:0}img{width:100%;height:auto;display:block;background:#e2dacb}figcaption{display:flex;justify-content:space-between;gap:15px;margin-top:10px;font-size:17px}figcaption a{font-size:13px;color:#71665a}footer{font-size:12px;color:#71665a;border-top:1px solid #d1c8b9;margin-top:35px}@media(max-width:700px){header,main,footer{padding:20px 16px}header{flex-wrap:wrap}.gallery{grid-template-columns:1fr;gap:28px}.intro{padding:12px 0 25px}nav{gap:15px}}
</style><header><a href="../index.html">院居 · 六人院落住宅</a><nav><a href="../3d.html">交互3D</a><a href="../drawings/农村院落住宅-水电深化P.pdf">当前图册 · 39页</a><a href="00-精装总览.jpg">图片总览</a><a href="#material-advice">装修选材建议</a></nav></header><main><div class="intro"><h1>浅橡木、暖白与米色织物，落在家的尺度里。</h1><p>按参考图调整整体为浅色精装：暖白墙面、浅橡木门与柜体、米色亚麻软包、浅灰米石纹地面，配细木格栅、暗藏灯槽与暖光。后排卧室不做木地板，改用浅色石纹砖；二楼晾衣亭顶棚由深色改为浅灰米金属顶，柱与梁改浅木／暖灰。</p><p>以下13张为同一模型的家具与装修细节重渲：补踢脚、门窗套、叠级灯槽与筒灯；卧室加亚麻软包床头、木格栅背墙与暗藏灯、亚麻床品与搭毯、地毯、壁灯与挂画；厨房补墙面砖、开放层架、门板拉手和台面器物；卫浴补墙裙砖、毛巾、地垫与瓶罐；门厅与堂屋补边柜、挂画、绿植和台灯。点击查看2560×1440原图。</p><p>本轮只调整装修观感、材料色系与家具细节，不改变O版房间布置、门窗、五列衣柜位置及P版水电。家具与软装为尺寸示意，材质、颜色与灯具规格以选样为准；图片后附本案装修材料建议。</p></div><div class="gallery">'''+''.join(cards)+'''</div>'''+material_advice_html()+'''</main><footer>Q版浅色精装 · 2026-11-07 · 设计渲染，非已施工现场照片。材料、软装与安装按实测、样板及具体产品深化。</footer></html>'''
html=html.replace('</style>', '''.material-photo-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:18px;margin:20px 0 38px}.material-photo-grid figure{background:#faf7f0;border:1px solid #d7cebf;min-width:0}.material-photo-image{display:block;height:200px;padding:10px;background:#e8e5dc}.material-photo-image img{height:100%;width:100%;object-fit:contain;background:transparent}.material-photo-grid figcaption{display:block;padding:15px;font-size:15px;line-height:1.65;margin:0}.material-photo-grid figcaption strong{font-weight:500}.material-photo-grid figcaption p{font-size:13px}.material-photo-grid figcaption small,.material-photo-grid figcaption a{font-size:11px;color:#71665a}.material-photo-grid a:focus-visible{outline:3px solid #a8824c;outline-offset:2px}@media(max-width:1100px){.material-photo-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:700px){.material-photo-grid{grid-template-columns:1fr}.material-photo-image{height:250px}}.material-advice{margin-top:56px;padding-top:28px;border-top:1px solid #cfc5b5;scroll-margin-top:24px}.material-advice>h2{font:500 clamp(26px,4vw,40px)/1.3 "Noto Serif CJK SC",serif;margin:0 0 18px}.material-advice>h2:not(:first-child){font:500 24px/1.4 "Noto Serif CJK SC",serif;margin-top:34px}.material-advice>p{max-width:900px}.material-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px;margin-top:18px}.material-grid article{background:#faf7f0;border:1px solid #d7cebf;padding:22px 24px;min-width:0}.material-grid h3{font-size:18px;font-weight:500;margin:0 0 12px;display:flex;align-items:center;gap:10px}.material-swatch{width:24px;height:24px;border:1px solid #c2b8a8;flex:none}.material-choice{color:#293c33}.material-grid ul{padding-left:20px;color:#71665a;font-size:14px}.material-grid li{margin:7px 0}.material-refs{font-size:12px}.material-refs a{display:inline-block;padding:2px 4px}.material-advice details{margin-top:26px;padding:18px 20px;border:1px solid #d7cebf;overflow-wrap:anywhere}.material-advice summary{cursor:pointer;font-size:16px}.material-advice details li{margin:8px 0}.material-advice [id^=material-source-]:target{background:#e6dcc9}@media(max-width:700px){.material-grid{grid-template-columns:1fr}.material-grid article{padding:18px}.material-advice{margin-top:36px}.material-grid h3{font-size:17px}}</style>''')
(folder/'index.html').write_text(html)
print('INTERIOR GALLERY PASS:',len(views),'full-resolution images, overview and offline HTML.')
