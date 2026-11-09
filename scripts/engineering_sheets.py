"""Five A3 concept sheets rendered from the same engineering data as the model."""

COLORS = {"electric":"#e59928", "cold":"#2e86de", "hot":"#d74c47",
          "waste":"#8a5b37", "rain":"#29a3a3"}
INK, MUTED, STRUCTURE = "#293d39", "#6c7770", "#8b66c7"


def append_engineering_sheets(sheet, axes, rect, line, txt, save,
                              site_outline, floor_plan, layout):
    """Append structure, two electric, plumbing and rear septic layout pages."""
    def background(ax, *floors):
        for floor in floors:
            floor_plan(ax, floor)
        for artist in list(ax.patches)+list(ax.lines):
            artist.set_alpha(.22)
        for artist in list(ax.texts):
            artist.remove()

    def note(page, x, y, lines, size=8):
        for text in lines:
            txt(page, x, y, text, size, MUTED)
            y -= 6.4

    def legend(page, x, y, system, label):
        line(page, [x,x+12], [y,y], COLORS[system], 1.7)
        txt(page, x+16, y, label, 8, INK)

    def route_plan(ax, floors, systems, label_devices=True, flow=False):
        for route in layout["routes"]:
            if route["floor"] not in floors or route["system"] not in systems:
                continue
            points = route["points"]
            if all(p[:2] == points[0][:2] for p in points):
                x, y = points[0][:2]
                ax.plot(x, y, marker="o", ms=5.2, mfc="white", mec=COLORS[route["system"]],
                        mew=1.1, zorder=5)
                continue
            style = "--" if route["label"].startswith("S") else "-." if route["label"].startswith(("K","W1")) else "-"
            width = {"cold":2.5, "hot":1.65, "waste":.8, "rain":1.1}.get(route["system"], .85)
            if route["system"] == "hot":
                style = "--"
            line(ax, [p[0] for p in points], [p[1] for p in points],
                 COLORS[route["system"]], width, linestyle=style, alpha=.9, zorder=4)
            if flow:
                for a, b in zip(points, points[1:]):
                    distance = abs(b[0]-a[0])+abs(b[1]-a[1])
                    if distance < .7:
                        continue
                    start = tuple(a[i]+.45*(b[i]-a[i]) for i in (0,1))
                    end = tuple(a[i]+.65*(b[i]-a[i]) for i in (0,1))
                    ax.annotate("", xy=end, xytext=start, zorder=6,
                                arrowprops=dict(arrowstyle="->", color=COLORS[route["system"]], lw=1))
        markers = {"panel":"p", "meter":"D", "light":"o", "socket":"s", "equipment":"^",
                   "outlet":"v", "inspection":"s", "future_connection":"D"}
        for device in layout["devices"]:
            if device["floor"] not in floors or device["system"] not in systems:
                continue
            x, y, _ = device["point"]
            color = COLORS[device["system"]]
            marker_size = {"cold":6.6, "hot":4.9, "waste":3.1}.get(device["system"], 4.5)
            ax.plot(x, y, marker=markers.get(device["type"], "o"), ms=marker_size,
                    mfc="white", mec=color, mew=1, zorder=7)
            if label_devices and device["system"] == "electric":
                txt(ax, x+.14, y+.16, device["label"].split()[0], 5.9, color, zorder=8,
                    bbox=dict(fc="#fffefa", ec="none", pad=.35))

    def septic_plan(ax, labels=True):
        x1,y1,x2,y2 = layout["septic"]["bounds"]
        width = (x2-x1)/3
        rect(ax, x1, y1, x2-x1, y2-y1, "#eee4d6", COLORS["waste"], 1.2, zorder=2)
        for i in range(1,3):
            line(ax, [x1+i*width]*2, [y1,y2], COLORS["waste"], .8, zorder=3)
        for i in range(3):
            x = x1+(i+.5)*width
            rect(ax, x-.19, y2-.6, .38, .38, "#fffefa", COLORS["waste"], .7, zorder=3)
            if labels:
                txt(ax, x, y1+.35, f"第{i+1}格", 6.5, COLORS["waste"], ha="center", zorder=8)

    def structure(ax, floors):
        for member in layout["members"]:
            if member["floor"] not in floors:
                continue
            a, b = member["a"], member["b"]
            if a[:2] == b[:2]:
                rect(ax, a[0]-.12, a[1]-.12, .24, .24, STRUCTURE, STRUCTURE, .3, zorder=6)
            else:
                line(ax, [a[0],b[0]], [a[1],b[1]], STRUCTURE, 1.8, zorder=5)

    fig, page = sheet("S-101", "结构轴网与承重体系示意",
                      "已确认采用钢筋混凝土框架方案  /  梁柱承担荷载，墙体按填充/隔墙表达  /  未验算")
    ax = axes(fig, (17,45,178,202), (-1.1,15.2,-.9,29.4))
    background(ax, "front", "rear1")
    rect(ax, 0, 0, 15.2, 29.4, ec="#bdc7bc", lw=.7, linestyle="--")
    txt(ax, 7.3, 28.3, "屋后 5m 净空 / 排污设施见 P-102", 6.2, MUTED, ha="center")
    for x, label in zip((.72,4.2,7.8,11.28), "ABCD"):
        line(ax, [x,x], [-.2,25], "#b49c91", .45, linestyle="--")
        txt(ax, x, 25.5, label, 7, STRUCTURE, ha="center")
    for y, label in zip((.72,6.48,16.14,21.4,24.28), ("1","2","3","4","5")):
        line(ax, [-.25,14.25], [y,y], "#b49c91", .45, linestyle="--")
        txt(ax, -.6, y, label, 7, STRUCTURE, ha="center")
    structure(ax, {"front","rear1","site"})
    txt(ax, 6, 3.5, "前房 / 框架轴线", 7, INK, ha="center")
    txt(ax, 6, 19, "堂屋内部保持完整", 7, INK, ha="center")
    txt(ax, 6, 10.6, "两侧连廊支承示意", 6.8, INK, ha="center")
    txt(ax, 12.9, 19.2, "右后侧梯支承", 6, INK, ha="center", rotation=90)
    upper = axes(fig, (211,132,185,112), (-.2,14.7,13.6,25))
    background(upper, "rear2"); structure(upper, {"rear2"})
    txt(page, 214, 246, "后楼二层 / 与首层同轴，中央完整楼板", 9, STRUCTURE)
    rect(page, 215, 119, 3, 3, STRUCTURE, STRUCTURE, .4)
    txt(page, 222, 120.5, "柱位置符号", 8, INK)
    line(page, [269,282], [120.5,120.5], STRUCTURE, 2)
    txt(page, 287, 120.5, "梁 / 支承轴线", 8, INK)
    rect(page, 354, 119, 3, 3, "#e6e8df", "#bbc5bb", .4)
    txt(page, 361, 120.5, "填充墙", 8, INK)
    note(page, 214, 102, [
        "A—D：沿三开间边界及外墙布置柱轴；庭院保持开敞。",
        "中央堂屋 3.60 × 8.80 m，柱沿两侧边界布置。",
        "左右连廊、右后侧梯需独立核对支承与连接节点。",
        "二层墙体为填充/隔墙，不表示已核定承重墙。",
        "柱、梁的绘制宽度只供识别，不代表设计截面。",
        "基础、梁板、屋架、抗震、荷载及配筋均未设计验算。",
        "待现场勘察及结构设计深化后，确定实际截面与配筋。",
    ])
    txt(page, 20, 32, "本页仅说明可能的传力位置；不得据此拆改墙体、凿梁穿柱或施工。", 8.5, STRUCTURE)
    save(fig, "12-structure")

    fig, page = sheet("E-101", "首层电气位置与回路示意",
                      "通堂东墙暂设 DB0；经东连廊下方至后楼 DB1，再经竖井送至 DB2  /  线路均未选型")
    front = axes(fig, (19,68,180,108), (-.1,12.05,0,7.2))
    background(front, "front"); route_plan(front, {"front","site"}, {"electric"})
    rear = axes(fig, (210,67,188,170), (-.1,14.7,13.6,25.2))
    background(rear, "rear1"); route_plan(rear, {"rear1","site"}, {"electric"})
    txt(page, 22, 182, "前房：左客房 / 中通堂 / 右中西厨餐厅", 9, INK)
    txt(page, 215, 242, "后楼首层：照明及插座预留", 9, INK)
    legend(page, 22, 241, "electric", "强电路径 / 位置示意")
    note(page, 22, 228, [
        "○ L：照明    □ S：普通插座    △ K/W：设备电位",
        "实线：照明/馈线；虚线：插座；点划线：设备回路。",
        "K1 烟机/灶具    K2 烤箱    K3 西厨台面    K4 冰箱",
        "W1 洗衣机在家务前室北墙；电位跟随家具坐标定位。",
        "封闭梯间预留照明及电源；侧入口灯控与回路待深化。",
    ])
    for x, label in ((28,"入户 IN"),(77,"总箱 DB0"),(135,"首层 DB1")):
        rect(page, x, 49, 33, 11, "#fff8e8", COLORS["electric"], .7)
        txt(page, x+16.5, 54.5, label, 7.5, COLORS["electric"], ha="center")
    line(page, [61,77], [54.5,54.5], COLORS["electric"], 1)
    line(page, [110,135], [54.5,54.5], COLORS["electric"], 1)
    txt(page, 122.5, 44, "经东连廊", 6.5, MUTED, ha="center")
    note(page, 211, 52, [
        "图中线路走顶下/沿墙示意，尽量避开梁柱轴心。",
        "套管、竖井、保护、接地、负荷和线径未深化。",
        "弱电、开关联控及设备最终接线由后续设计确定。",
    ], 7.5)
    save(fig, "13-electrical-ground")

    fig, page = sheet("E-102", "二层电气与上下层连接示意",
                      "DB2 接首层 DB1；二层照明与插座分别示意  /  设备、线径、保护和接地尚未核定")
    upper = axes(fig, (18,70,262,175), (-.2,14.7,13.6,25.2))
    background(upper, "rear2"); route_plan(upper, {"rear2"}, {"electric"})
    txt(page, 24, 244, "后楼二层 / 配电箱位于家庭厅东侧墙邻近区域", 9, INK)
    legend(page, 289, 235, "electric", "二层强电")
    note(page, 289, 222, ["○ L  照明点", "□ S  普通插座", "五角符号  分配电箱", "编号按本层房间顺序。"], 8)
    for y, label, level in ((163,"DB2 二层分箱","+3.600 二层"),(108,"DB1 首层分箱","+0.300 首层")):
        rect(page, 300, y, 85, 16, "#fff8e8", COLORS["electric"], .8)
        txt(page, 342.5, y+8, label, 8.5, COLORS["electric"], ha="center")
        txt(page, 299, y-7, level, 7.4, MUTED)
    line(page, [343,343], [124,163], COLORS["electric"], 1.5)
    txt(page, 349, 143, "邻墙竖井", 7.5, COLORS["electric"])
    txt(page, 349, 136, "楼板套管待定", 7.5, MUTED)
    note(page, 22, 53, [
        "平面投影重合的上下段以分层数据区分，三维工程层可分别查看；竖井不穿梁柱轴心。",
        "照明图表达灯位与接箱路径；灯具、控制方式、普通插座数量与专用回路仍需使用需求及施工设计确认。",
        "此页不包含已验算的配电方案；不得按图示线条宽度选择电线、开孔或直接施工。",
    ])
    save(fig, "14-electrical-upper")

    fig, page = sheet("P-101", "给排水位置与立管关系示意",
                      "西湿区沿用，东套卫迁梯间北侧；首层公卫经起居室到前室；厨卫与洗衣接实际设备点，雨污分流")
    for box, floor, title in (((18,151,183,94),"rear1","后楼首层湿区"),
                              ((215,151,183,94),"rear2","后楼二层湿区")):
        ax = axes(fig, box, (-.15,14.7,21.0,25))
        background(ax, floor)
        route_plan(ax, {floor}, {"cold","hot","waste","rain"}, False)
        txt(page, box[0]+3, 244, title, 9, INK)
        txt(ax, 1.65, 21.48, "西公卫" if floor=="rear1" else "西套卫", 6.5, MUTED, ha="center")
        txt(ax, 12.85, 22.05, "老人套卫" if floor=="rear1" else "东卫浴", 6.5, MUTED, ha="center")
    for x, system, label in ((22,"cold","CW 冷水"),(116,"hot","HW 热水"),
                              (211,"waste","WW 污废水"),(309,"rain","RW 雨水")):
        legend(page, x, 143, system, label)
    sink = next(d for d in layout["devices"] if d["floor"] == "front" and d["type"] == "sink" and d["system"] == "cold")
    right = sink["point"][0] > 6
    front = axes(fig, (20,57,125,76), (7.5 if right else .05,12.3 if right else 4.8,.2,6.9))
    background(front, "front"); route_plan(front, {"front"}, {"cold","hot","waste"}, False)
    txt(page, 22, 132, "厨房水槽 / 同一设备点", 9, INK)
    txt(page, 22, 53, "厨房仅水槽接水；洗衣机接冷水和排水。", 7.2, MUTED)
    txt(page, 163, 130, "立管上下关系 / 展开示意", 9, INK)
    # A diagrammatic expansion separates close risers while preserving their floor relationships.
    for y, label in ((108,"二层"),(86,"首层"),(64,"暂定出户/水源")):
        line(page, [184,390], [y,y], "#d2d8cc", .5)
        txt(page, 158, y, label, 7, MUTED)
    for x, system, label in ((220,"cold","CW"),(260,"hot","HW"),(304,"waste","WW"),(359,"rain","RW")):
        line(page, [x,x], [64,118 if system == "rain" else 108], COLORS[system], 1.6)
        txt(page, x, 122, label, 7.5, COLORS[system], ha="center")
        if system != "rain":
            for y in (86,108):
                line(page, [x-10,x+10], [y,y], COLORS[system], 1.2)
                txt(page, x+11, y+2.5, "卫浴", 6.2, COLORS[system])
        else:
            txt(page, x+5, 113, "屋面收集", 6.5, COLORS[system])
            txt(page, x+5, 89, "独立雨水管", 6.5, COLORS[system])
    txt(page, 305, 57, "向北 → 化粪池（P-102）", 6.5, COLORS["waste"], ha="center")
    txt(page, 360, 57, "雨水去向待核", 6.5, COLORS["rain"], ha="center")
    note(page, 22, 40, [
        "路径与三维共用数据；洗衣机及热源在家务前室北侧。同投影管线宽窄/虚实错分，线宽不表示管径。",
        "竖井、套管、防水、管径、坡度、通气、清扫口和热水保温/循环未深化；高程用于分层识别，不表示实际埋深。",
    ], 7.5)
    save(fig, "15-plumbing")

    fig, page = sheet("P-102", "屋后排污与三格化粪池示意",
                      "后墙以北 5.00 m 净空  /  污废水经检查井汇集、西进东出  /  池体及下游仅为位置方案")
    overview = axes(fig, (18,43,151,202), (-.6,15.2,-.7,30.3))
    background(overview, "front", "rear1")
    rect(overview, 0, 0, 15.2, 29.4, ec="#b0bcb1", lw=.8, linestyle="--")
    septic_plan(overview, False)
    route_plan(overview, {"site","front"}, {"waste","rain"}, False, True)
    txt(overview, 6, 10.3, "院落", 7, MUTED, ha="center")
    txt(overview, 6, 20.4, "后楼", 7, MUTED, ha="center")
    txt(overview, 12.9, 19.2, "右后侧梯", 6, MUTED, ha="center", rotation=90)
    txt(overview, 6, 27.8, "屋后空地", 6, MUTED, ha="center")
    txt(overview, 5.1, 1.2, "雨水独立向南", 6.4, COLORS["rain"], ha="center")
    txt(page, 20, 242, "排污路径总览 / 箭头示意流向", 9, INK)

    detail = axes(fig, (180,142,220,95), (-.1,14.9,22.9,29.9))
    background(detail, "rear1")
    line(detail, [0,15.2], [29.4,29.4], "#9cae9d", .8, linestyle="--")
    line(detail, [.6,11.4], [24.4,24.4], INK, 1.2)
    txt(detail, 3.4, 24.15, "后楼北墙", 7, INK, ha="center")
    septic_plan(detail)
    route_plan(detail, {"site","front"}, {"waste"}, False, True)
    for device in layout["devices"]:
        if device["type"] == "inspection":
            x,y,_ = device["point"]
            txt(detail, x, y+.26, device["label"].split()[0], 7, COLORS["waste"], ha="center",
                bbox=dict(fc="#fffefa",ec="none",pad=.35))
    txt(detail, 9.8, 28.65, "三格化粪池 · 位置轮廓", 7.5, COLORS["waste"], ha="center")
    txt(detail, 7.76, 27.58, "进", 6.5, COLORS["waste"], ha="right")
    txt(detail, 11.82, 27.58, "出", 6.5, COLORS["waste"])
    txt(detail, 13.4, 29.15, "下游接点待定", 6.5, COLORS["waste"], ha="center")
    detail.annotate("", xy=(.35,29.4), xytext=(.35,24.4),
                    arrowprops=dict(arrowstyle="<->", color=MUTED, lw=.7))
    txt(detail, .1, 26.9, "后方净空 5.00 m", 6.8, MUTED, rotation=90, ha="center")
    txt(page, 183, 242, "屋后放大 / 检查井、三格池及待定下游", 9, INK)
    legend(page, 184, 130, "waste", "污废水 → 屋后检查井 → 三格池 → 待定后续处理")
    legend(page, 184, 119, "rain", "雨水独立南向，不接化粪池")
    note(page, 184, 103, [
        "厨房排污沿东侧绕封闭梯间外围向北，避开入户通口。",
        "绕行线不代表已避开实际基础：需核对基础外扩和埋深。",
        "池内三格等宽仅为图例，未确定有效容积或工艺尺寸。",
        "池后接点待专项确认，不表示允许直接向环境排放。",
        "容量、退距、地下水、防渗、通气和池体结构均待设计。",
        "厨房隔油、排水坡度、清扫口及接口高程均待深化。",
        "检修维护及清掏路径待现场核实，未核定车辆可达。",
    ], 7.7)
    txt(page, 20, 32, "场地面宽 15.20 m 仍为示意外包；后墙至后边界按用户给定 5.00 m 表达。本页不得直接用于施工。", 8, COLORS["waste"])
    save(fig, "16-septic-layout")
