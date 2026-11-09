"""Material advice shared by the drawing appendix and the offline image gallery."""
from html import escape
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MATERIAL_IMAGES=json.loads((ROOT/'assets/material-reference/sources.json').read_text())['images']

SOURCES = [
    ('上海市场监管：陶瓷砖消费提示', 'https://scjgj.sh.gov.cn/1072/20230803/2c984a7289b5d5330189babde8fd249a.html'),
    ('住建部：2025住宅质量问题重点整治', 'https://www.mohurd.gov.cn/gongkai/zc/wjk/art/2025/art_dd6b4e8904634f7681e22362cbdcfdb4.html'),
    ('住建部：保障性住房质量常见问题防治', 'https://www.mohurd.gov.cn/ztbd/bzxzlzfgz/zybmwj/art/2022/art_17768_764573.html'),
    ('北京住建：住宅防水施工与渗漏防治指南', 'https://zjw.beijing.gov.cn/bjjs/xxgk/zcwj2024/qtzcwj/xxyx13/436473157/index.shtml'),
    ('上海市场监管：中空玻璃抽查及消费提示', 'https://scjgj.sh.gov.cn/923/20241210/2c984a729367d8000193af68c8f83844.html'),
    ('立邦：配套抗碱内墙底漆', 'https://www.nipponpaint.com.cn/product/1279'),
    ('蒙娜丽莎：止滑砖产品资料', 'https://www.monalisa.com.cn/installationguide/info_itemid_14230.html'),
    ('TATA木门：产品使用说明书', 'https://www.tata.com.cn/uploads/files/2023/0329/6kiRZv5dbi8AhAXg0MnoFYVavpqSoj0QyX7L4104.pdf'),
]

# Sizes are this scheme's starting choices, not code thresholds or a purchase order.
MATERIAL_PAGES = [
    ('MAT-101', '装修选材建议 · 院子与室内地面', [
        ('院子主铺地', '#a8aaa0', '首选：暖灰、细颗粒面的室外专用瓷质铺地砖。', [
            '起选300×600或600×600mm，少用大亮面、复杂拼花。',
            '要求对应型号的湿态防滑及室外适用资料；寒冷地区核抗冻。',
            '备选火烧面／细荔枝面花岗岩，先看清洁难度与实样。',
            '人行、停车区分开核基层和厚度；先定排水，再排砖。'], [1, 2]),
        ('门廊、台阶与洗衣区', '#bcb5a7', '首选：同色系防滑地砖，台阶前缘易辨认。', [
            '起选300×600mm；踏步与平台统一色调，边口作细部处理。',
            '老人常走路线保持顺平，不用亮光石材或凸起装饰条。',
            '格栅沟盖、地漏和门口收边一起排版，避免细窄补砖。',
            '“哑光”只说明外观，防滑还要看试验方法和适用场景。'], [1, 2]),
        ('客厅、堂屋与厨房地面', '#d6cdbc', '首选：浅米灰哑光瓷质砖，公共区尽量统一。', [
            '本案起选600×600mm；通道大且预算允许再看600×1200。',
            '厨房同色可用更易擦洗的细纹面，避免粗糙沟纹藏油。',
            '用同色近色填缝，留缝宽度按产品与铺贴系统确定。',
            '不靠“无缝铺贴”或加厚找平掩盖基层问题。'], [1, 3]),
        ('卧室与衣帽区', '#bd9870', '首选：暖橡木色木纹瓷砖，延续现有木色效果。', [
            '起选150×900或200×1200mm，木纹宜柔和、少结疤。',
            '长条砖按厂家排版要求控制错缝，重点看翘曲与高低差。',
            '喜欢脚感可比样多层实木地板，先确认防潮与地暖条件。',
            '木纹砖和真木地板是不同材料，交界标高要分别计算。'], [1, 3]),
        ('卫生间与淋浴地面', '#c0c4bb', '首选：小规格湿区专用防滑砖，方便分区找坡。', [
            '本案起选300×300mm；墙面可用300×600mm同色系。',
            '淋浴区核湿脚防滑、清洁性和排水，不用光面大板冒充。',
            '地漏先定位，砖缝与找坡协调；门口不留反向积水点。',
            '填缝不代替防水，闭水及节点验收合格后再铺贴。'], [1, 4]),
        ('二层露台与亭内晾衣区', '#b8b7ac', '首选：轻量、室外适用的防滑铺装系统。', [
            '起选300×300或300×600mm，避开厚重叠铺与抛光面。',
            '先核楼板荷载、防水、坡向、雨水口和立管检修位置。',
            '不要把院子厚石材、砂浆垫层原样搬到楼顶。',
            '“砖更厚”不等于防水更好；伸缩、收边与排水一起设计。'], [2, 4]),
    ]),
    ('MAT-102', '装修选材建议 · 墙面、厨卫与柜体', [
        ('卧室与客厅普通墙面', '#f0e9da', '首选：暖白哑光水性内墙漆，少量暖灰作背景。', [
            '选同厂相容的基层、腻子、底漆和面漆配套体系。',
            '新墙先查含水与碱性，基层处理达到产品施工要求再涂。',
            '日常接触处看耐擦洗与修补色差，不必全屋艺术涂料。',
            '“净味”“儿童漆”不替代对应型号检测及竣工环境验收。'], [3, 6]),
        ('院墙与外墙', '#dad6c9', '首选：耐候外墙涂料；近地面做耐脏、耐水处理。', [
            '延续暖白／浅暖灰，压顶、滴水和墙脚颜色宜克制。',
            '先处理渗漏、泛碱和裂缝，再选外墙涂料及配套底涂。',
            '真石漆、仿石涂料可局部用，先比较纹理与后期清洁。',
            '外墙系统与保温相容；室内乳胶漆不直接用于室外。'], [3, 4]),
        ('厨房墙面与台面', '#ded7c8', '首选：好擦洗的浅色墙砖，台面先比样石英石。', [
            '墙砖起选300×600或600×1200mm，灶后少做密集小缝。',
            '台面看吸污、耐清洁剂和开孔工艺，不只看含石量宣传。',
            '水槽、灶具、洗碗机规格确定后出加工图和检修方案。',
            '台面与墙交界用相容密封材料，避免依靠硬填缝止水。'], [3, 4]),
        ('卫浴墙面与吊顶', '#d9d8cc', '首选：浅暖灰易清洁墙砖，配可检修的耐潮吊顶。', [
            '墙砖本案起选300×600mm，少做凹凸深纹和装饰腰线。',
            '吊顶可比样铝扣板；设备口、检修口和灯具提前排版。',
            '窗边、管根、地漏、门口与墙地交接先处理防水节点。',
            '防霉胶和美缝只是接缝材料，不等同完整防水系统。'], [3, 4]),
        ('卧室五列衣柜', '#bb9367', '首选：浅木色耐磨饰面板，柜门与柜体色差受控。', [
            '板材、封边、胶与五金一并核对，不仅看单张板材等级。',
            '优先完整封边、可维护铰链与抽屉五金，湿墙先治潮。',
            '给每个房间保留样板编号；把背板、隔板规格写入合同。',
            '预算优先给五金与封边，少为复杂雕花、满墙造型加价。'], [3]),
        ('洗衣池柜与浴室柜', '#a9b0a5', '首选：耐潮柜体，重视底部、开孔处及背面处理。', [
            '长期易溅水处可比样铝合金柜体或耐潮板材完整封边。',
            '柜底留清洁与检修条件，阀门、插座不能封在不可达处。',
            '石材／盆体先确认重量、支承、龙头开孔和软管空间。',
            '不把“防潮板”理解为可以长期泡水。'], [3, 4]),
    ]),
    ('MAT-103', '装修选材建议 · 窗户、大门与房门', [
        ('卧室与公共区外窗', '#666b63', '首选：深灰断桥铝窗，透明中空玻璃先比整窗性能。', [
            '要求整窗气密、水密、抗风压与节能资料及安装节点。',
            '按所在地气候、朝向选Low-E配置，玻璃厚度需另核。',
            '不只凭“几系型材”“几道密封”判断性能或直接下单。',
            '平开／内倒／推拉按净空选；模型中的开启方式为示意。'], [2, 5]),
        ('临街、低窗及大块玻璃', '#bdc9c4', '重点：安全玻璃、实际隔声与完整防护方案。', [
            '临街噪声先调查，再比较玻璃组合与整窗隔声报告。',
            '中空、夹层、钢化功能不同，不以层数多作为唯一标准。',
            '玻璃面积、安装位置和风作用决定选型，不能统一写死厚度。',
            '低窗、临空处和玻璃门的安全及防撞措施一起落实。'], [2, 3, 5]),
        ('窗边收口与五金', '#9a9f95', '重点：外侧挡雨排水、内侧气密及可维护五金。', [
            '窗台外排水、滴水、框墙接缝和排水孔须形成完整做法。',
            '五金按扇重选，备纱窗与可更换密封条，留清洁操作空间。',
            '填缝材料与密封胶按系统选，不用一圈发泡胶代替防水。',
            '安装完成核排水、开关与渗漏；报价包含拆装和修口。'], [2, 3, 4]),
        ('临街双扇大门', '#694e36', '首选：耐候金属门体配木纹饰面／铜色细节。', [
            '经济型比样防腐钢门，升级型可比样铝合金或铸铝门。',
            '本案用深木色＋少量铜色，保留原厚重现代中式比例。',
            '把防雨、门扇总重、铰链、锁具、门柱和限位一起核定。',
            '室内木门不直接当室外门；门越重不代表系统越安全。'], [2, 3]),
        ('后楼朝院玻璃推拉门', '#414944', '首选：深灰金属框，安全玻璃与轨道排水同选。', [
            '按已确认双轨横拉形式深化，兼顾有效通行宽度。',
            '比滑轮承载、防夹、限位、轨道清洁与外排水条件。',
            '低轨做法要与室内外高差、防水收口一起出节点。',
            '不以“无门槛”口号掩盖雨水倒灌问题。'], [2, 3, 4]),
        ('卧室门与卫浴门', '#c3a07a', '卧室：木色或暖白复合木门；卫浴：耐潮门套体系。', [
            '卧室重视门芯、密封、五金、门套固定与底部缝隙。',
            '卫浴可比样铝合金玻璃门，或厂家明确适用的耐潮木门。',
            '老人房把手与锁具方便操作，留应急开启与检修条件。',
            '室内木门使用边界及防潮维护按厂家说明落实。'], [3, 8]),
    ]),
    ('MAT-104', '装修选材建议 · 品牌候选与采购核对', [
        ('最适合本案的一套配色', '#d5c8b2', '暖灰院地＋浅米灰室内砖＋暖白墙＋橡木色柜门。', [
            '门窗用深灰，临街大门用深木色和少量铜色点缀。',
            '同一位置保留一套实物样板，在自然光和晚间灯下看色。',
            '先确定铺地与门窗，再对柜门、涂料和软装，不倒着选。',
            '本页色块仅表示搭配方向，不是品牌色卡或实物保证。'], []),
        ('瓷砖与涂料候选', '#b9b7a7', '瓷砖可先向蒙娜丽莎取样；涂料可先比样立邦配套。', [
            '询同规格、同用途产品，要求具体型号报告和授权渠道。',
            '品牌候选不代表全系列均适合室外或湿区。',
            '涂料以基层相容、耐擦洗与配套施工为先，不只比桶价。',
            '以上仅作找样起点，可用符合相同条件的其他品牌替换。'], [6, 7]),
        ('房门、外窗与大门候选', '#95816b', '室内木门可先向TATA取样；外窗与院门按整套系统比价。', [
            '室内门品牌不直接套作室外大门；不同用途分开选。',
            '外窗优先比较同配置整窗报告、安装队与本地售后。',
            '院门要求门体／门柱／五金节点与耐候做法完整报价。',
            '不把型材、玻璃或锁具品牌当成整窗／整门合格证明。'], [2, 3, 8]),
        ('预算优先花在哪里', '#a1ab9e', '优先：排水防水、地面防滑、门窗安装及耐用五金。', [
            '其次：平整度、密封、防潮封边与后期可检修性。',
            '可简化：全屋超大砖、复杂拼花、满墙石材和装饰线。',
            '建议同一清单询两到三家，分别列材料、辅材和施工。',
            '所在地及预算未定，本次不写可能误导的单价或总价。'], [2, 3, 4]),
        ('下单清单必须写清', '#d7d0bf', '位置、品牌型号、规格、色号批次、数量与完整施工范围。', [
            '瓷砖：排版、损耗、填缝、收边、补货与退换约定。',
            '门窗：玻璃组合、五金、纱窗、安装、密封与修口。',
            '涂料：基层处理、配套产品、施工条件与实际涂布要求。',
            '样板、检测、授权、质保及售后联系人写入交付清单。'], [2, 3, 6]),
        ('开工前与交付时核对', '#c0c8ba', '先做小样与节点样板，再批量进场施工。', [
            '湿态防滑试样与正式检测配合，不把手摸或踩样当认证。',
            '核对找坡排水、防水闭水、门窗渗漏和地面高低差。',
            '确认成品保护、通风及必要检测，按实际结果安排入住。',
            '以下官方资料为选型参考；性能限值按所在地和项目核定。'], [1, 2, 3, 4]),
    ]),
]


def append_material_sheets(sheet, rect, txt, save):
    for page_index, (code, title, items) in enumerate(MATERIAL_PAGES):
        fig, page = sheet(code, title, '暖白木色与现代中式 / 中档耐用、易维护 / 规格为本案起选建议，非采购定案')
        for index, (name, color, recommendation, lines, refs) in enumerate(items):
            x, y = 20+(index%2)*200, 181-(index//2)*75
            rect(page, x, y, 180, 65, '#f4f1e9', '#d1d2c8', .5)
            if page_index==3 and index==5:
                txt(page, x+5, y+56, '官方资料索引（电子PDF可点击）', 10.5, '#355b48')
                for source_index,(source_title,url) in enumerate(SOURCES,1):
                    txt(page, x+5, y+46-(source_index-1)*5.6,
                        f'{source_index}. {source_title}', 7.4, '#56665d', url=url)
                continue
            txt(page, x+5, y+56, name, 11.5, '#355b48')
            rect(page, x+159, y+51, 15, 10, color, '#c0c1b8', .3)
            txt(page, x+5, y+43, recommendation, 8.2, '#293d39')
            for line_index, text in enumerate(lines):
                txt(page, x+5, y+34-line_index*6.2, text, 8.0, '#56665d')
            if refs:
                txt(page, x+5, y+4.5, '依据 '+','.join(str(i) for i in refs)+' / 索引见MAT-104，网页含原文链接', 6.7, '#778176')
        save(fig, f'{33+page_index:02}-material-advice-{page_index+1}')
    from PIL import Image
    for page_index in range(2):
        fig,page=sheet(f'MAT-{105+page_index}','装修材料图片参考 · '+('地面与墙面' if page_index==0 else '门窗与木色饰面'),
            '厂家展示与本案设计渲染分别标注 / 仅看外观搭配，颜色以实物为准，不是采购定案')
        for index,item in enumerate(MATERIAL_IMAGES[page_index*4:page_index*4+4]):
            x,y=20+(index%2)*200,139-(index//2)*108
            rect(page,x,y,180,106,'#f4f1e9','#d1d2c8',.5)
            txt(page,x+5,y+98,item['title'],11.5,'#355b48')
            axis=fig.add_axes([(x+4)/420,(y+27)/297,172/420,65/297])
            with Image.open(ROOT/item['path']) as image:axis.imshow(image)
            axis.axis('off')
            txt(page,x+5,y+18,item['note'],8.0,'#56665d')
            source_kwargs={'url':item['source_page']} if item['source_page'] else {}
            txt(page,x+5,y+8,'图片来源：'+item['source'],7.6,'#778176',**source_kwargs)
        save(fig,f'{37+page_index:02}-material-images-{page_index+1}')


def material_photos_html(image_prefix="../"):
    cards=[]
    for item in MATERIAL_IMAGES:
        url=image_prefix+item['path'];width,height=item['size']
        source=(f'<a href="{escape(item["source_page"],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(item["source"])}</a>'
                if item['source_page'] else escape(item['source']))
        cards.append(f'<figure><a class="material-photo-image" href="{url}" target="_blank" rel="noopener">'
            f'<img src="{url}" alt="{escape(item["title"])}，{escape(item["source"])}" width="{width}" height="{height}" loading="lazy"></a>'
            f'<figcaption><strong>{escape(item["title"])}</strong><p>{escape(item["note"])}</p>'
            f'<small>图片来源：{source}</small></figcaption></figure>')
    return ('<h2 id="material-photos">材料图片参考</h2><p>点击可放大。厂家展示图与本案设计渲染已分别标注；外观图片不能证明防滑、环保、隔声或防水性能。</p>'
            '<div class="material-photo-grid">'+''.join(cards)+'</div>')


def material_advice_html():
    sections=[]
    for _, title, items in MATERIAL_PAGES:
        cards=[]
        for name, color, recommendation, lines, refs in items:
            citations=' '.join(f'<a href="#material-source-{i}">[{i}]</a>' for i in refs)
            cards.append(f'<article><h3><span class="material-swatch" style="background:{color}"></span>{escape(name)}</h3>'
                         f'<p class="material-choice">{escape(recommendation)}</p><ul>'
                         +''.join(f'<li>{escape(line)}</li>' for line in lines)
                         +f'</ul><p class="material-refs">{citations}</p></article>')
        sections.append(f'<h2>{escape(title.replace("装修选材建议 · ",""))}</h2><div class="material-grid">'+''.join(cards)+'</div>')
    sources=''.join(f'<li id="material-source-{i}"><a href="{escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{escape(title)}</a></li>' for i,(title,url) in enumerate(SOURCES,1))
    return ('<section id="material-advice" class="material-advice"><h2>装修材料，按位置来选。</h2>'
            '<p>放在效果图之后的采购参考：中档耐用、易清洁，适配本案暖白木色。尺寸为起选建议，品牌只作取样候选；所在地、预算和具体型号尚未确定。</p>'
            +material_photos_html()+''.join(sections)+'<details><summary>选型依据与官方资料（2026-11-07核查）</summary><p>厂家资料仅说明相应产品，不是全品牌质量背书；地方建设资料不直接作为异地项目的强制条款。</p><ol>'+sources+'</ol></details></section>')
