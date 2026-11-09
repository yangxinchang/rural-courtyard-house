"""Shared dimensions for the concept drawings and Blender scene (metres)."""
from pathlib import Path
import json
from interiors import furnishings, decoration, FINISHES, COURTYARD_LAUNDRY, TERRACE_PAVILION, TERRACE_LAUNDRY, UPPER_LAUNDRY, TERRACE_DRYING

ROOT = Path(__file__).resolve().parents[1]
SITE = (15.2, 29.4)
SITE_BOUNDS = (0,-8,15.2,29.4)
FORECOURT = dict(bounds=(0,-8,15.2,0),entry_path=(4.8,-8,7.2,0),dimensions_provisional=True)
STORAGE = dict(bounds=(11.0,-7.4,14.6,0.0),floor=.15,roof_level=3.3,floors=1,
               position_note='按用户蓝框覆盖右前方整块，尺寸暂按3.6×7.4米示意')
FRONT = (0.6, 0.6, 11.4, 6.6)
REAR = (0.6, 14.4, 11.4, 24.4)
BAYS = (0.6, 4.2, 7.8, 11.4)
LEVELS = {"ground": 0.3, "upper": 3.6, "attic": 6.9,
          "rear_plate": 8.0, "rear_ridge": 10.2,
          "front_plate": 3.6, "front_ridge": 3.6}
WALL = 0.24
BRIDGES = ((.6, 6.6, 1.8, 14.4), (10.2, 6.6, 11.4, 14.4))
STAIR = dict(bounds=(11.4,16.5,14.34,21.88), start_y=18.16, mid_y=20.59,
             flight_bounds=(18.16,20.59),top_landing=(11.4,16.74,14.1,18.16),
             mid_landing=(11.64,20.59,14.1,21.64),
             enclosed=True,wall_groups=['stair1','stair2'],roof_level=6.9,
             risers=20, rise=.165, tread=.27, width=1.05, landing=1.05)
COVERED_ENTRY = dict(bounds=(11.4,14.4,14.34,16.5),
                     roof_bounds=(11.4,14.4,14.34,16.74),roof_level=3.6)
EAST_CANOPY = dict(bounds=(10.1,6.4,11.5,14.64),roof_level=6.6,fall=.04,
                   post_x=(10.25,11.35),post_y=(6.75,9.25,11.75,14.15),post_size=.06)
EAST_SUITE = dict(bounds=(11.4,21.88,14.34,24.4),inner=(11.4,21.88,14.1,24.16),roof_level=6.9)
COURTYARD_WALLS = ((.6,6.48,.78,15.72),(11.22,6.48,11.42,14.64))
COURTYARD_WALL_TOPS = (LEVELS['upper']-.18,LEVELS['upper']-.18)
KITCHEN_EXHAUST = dict(points=[(10.84,1.6,2.18),(10.84,1.6,2.68),(11.8,1.6,2.68),(11.8,1.6,6.1)],
                       diameter=.18,concept=True,notes='独立上排，管径、静压、终端高度及风向按烟机与现场深化')
TERRACE_LAYOUT = dict(open_air=True,level=3.6,leisure_bounds=(1.8,2.0,4.2,4.6),
                      drying_rack=None,
                      central_clear_bounds=(4.8,1.0,7.0,6.0))
ROOMS = {
    "front": [
        ("中西厨房", (7.8, 0.6, 11.4, 6.6), "service"),
        ("通堂门厅", (4.2, 0.6, 7.8, 6.6), "hall"),
        ("多功能 / 客房", (0.6, 0.6, 4.2, 6.6), "bed"),
    ],
    "rear1": [
        ("起居室", (0.6, 15.6, 4.2, 21.4), "hall"),
        ("公卫", (0.6, 21.4, 2.7, 24.4), "wet"),
        ("家务 / 公卫前室", (2.7, 21.4, 4.2, 24.4), "service"),
        ("堂屋", (4.2, 15.6, 7.8, 24.4), "hall"),
        ("封闭侧楼梯", (11.4, 16.5, 14.34, 21.88), "stair"),
        ("老人卧室", (7.8, 15.6, 11.4, 21.4), "bed"),
        ("衣帽 / 休闲区", (7.8, 21.4, 11.4, 24.4), "bed"),
        ("老人套卫", EAST_SUITE['bounds'], "wet"),
        ("避雨门厅", COVERED_ENTRY["bounds"], "hall"),
    ],
    "rear2": [
        ("主卧", (0.6, 16.14, 4.2, 21.4), "bed"),
        ("套卫", (0.6, 21.4, 2.7, 24.4), "wet"),
        ("衣帽", (2.7, 21.4, 4.2, 24.4), "service"),
        ("家庭厅", (4.2, 16.14, 7.8, 24.4), "hall"),
        ("封闭侧楼梯", (11.4, 16.5, 14.34, 21.88), "stair"),
        ("次卧", (7.8, 16.14, 11.4, 21.4), "bed"),
        ("卧室书桌区", (7.8, 21.4, 11.4, 24.4), "bed"),
        ("套卫", EAST_SUITE['bounds'], "wet"),
        ("公共过厅", (.6, 14.4, 11.4, 16.14), "hall"),
        ("侧门入户过道", (9.8,16.14,11.4,18.35), "hall"),
    ],
}


def opening(offset, width, kind="door", sill=0.0, height=2.4, swing=1,hinge_end=False):
    return dict(offset=offset, width=width, kind=kind, sill=sill,
                height=height, swing=swing,hinge_end=hinge_end)


def wall(a, b, *openings):
    return dict(a=a, b=b, openings=list(openings), thickness=WALL)


def walls(group):
    """Wall centre lines; offsets run from the first endpoint."""
    d, w = opening, lambda off, width=1.8: opening(off, width, "window", 0.85, 1.6)
    if group=='storage':
        x1,y1,x2,y2=STORAGE['bounds'];x1+=.12;y1+=.12;x2-=.12;y2-=.12
        return [wall((x1,y1),(x2,y1),opening(.60,1.4,'window',1.4,.8)),
                wall((x1,y2),(x2,y2)),wall((x2,y1),(x2,y2)),
                wall((x1,y1),(x1,y2),opening(.78,1.2,'door',height=2.2,swing=1))]
    if group == 'entry':
        return [wall((11.52,14.52),(14.22,14.52),w(.55,1.3)),
                wall((14.22,14.52),(14.22,16.62),w(.35,1.1)),
                wall((11.52,14.52),(11.52,16.62),d(.12,.9,swing=1))]
    if group in ('stair1','stair2'):
        upper=group=='stair2'
        return [
            wall((11.52,16.62),(14.22,16.62),
                 opening(.65,1.3,'window',1.0,1.2) if upper else opening(1.28,1.1,'door',swing=1)),
            wall((14.22,16.62),(14.22,21.76),opening(2.4,1.4,'window',1.05,1.3)),
            wall((11.52,21.76),(14.22,21.76)),
            wall((11.52,16.62),(11.52,21.76),
                 *([opening(.38,1.1,'passage')] if upper else [])),
        ]
    if group == "front":
        return [
            wall((0.72, 0.72), (11.28, 0.72), w(.70,1.8), {**d(4.08, 2.4),'style':'grand'}, opening(7.86,1.8,'window',1.05,1.4)),
            wall((0.72, 6.48), (11.28, 6.48),
                 w(1.28,1.0), d(4.08, 2.4, "passage"), opening(7.28,1.0,'window',1.05,1.4)),
            wall((0.72, 0.72), (0.72, 6.48)),
            wall((11.28, 0.72), (11.28, 6.48)),
            wall((4.2, 0.72), (4.2, 6.48),d(3.83,1.0,swing=-1)),
            wall((7.8, 0.72), (7.8, 6.48),{**d(3.83,1.0,swing=1),'style':'glazed'}),
        ]
    assert group in ("rear1", "rear2")
    result = [
        wall((0.72, 15.72), (11.28, 15.72), w(0.68, 2.05), d(4.38, 1.8), w(7.83, 2.05)),
        wall((0.72, 24.28), (11.28, 24.28),
             opening(.4,.8,"window",1.5,.7), w(2.28, .8),
             opening(4.58,1.4,"window",1.9,1.1), w(7.4, .85), opening(9.05,.8,"window",1.5,.7)),
        wall((0.72, 15.72), (0.72, 24.28), w(1.3), w(6.7, 0.8)),
        wall((11.28, 15.72), (11.28, 24.28), w(1.3), w(6.7, 0.8)),
        wall((4.2, 15.72), (4.2, 24.28), d(1.28, 1.0, swing=1)),
        wall((7.8, 15.72), (7.8, 24.28), d(1.28, 1.0, swing=-1)),
        wall((0.72, 21.4), (4.2, 21.4), d(.68, .8, swing=-1), d(2.28, .8, swing=-1)),
        wall((7.8, 21.4), (11.28, 21.4), d(.2, .8, swing=-1), d(1.8, .8, swing=-1)),
        wall((2.7, 21.4), (2.7, 24.28)),
        wall((9.3, 21.4), (9.3, 24.28)),
    ]
    if group=='rear1':
        result[0]['openings'][1].update(style='glazed',operation='sliding')
        result[3]=wall((11.28,15.72),(11.28,24.28),d(6.36,.9,swing=1))
        result[4]=wall((4.2,15.72),(4.2,24.28),d(1.28,1.0,swing=-1))
        result[5]=wall((7.8,15.72),(7.8,24.28),d(1.28,1.0,swing=1))
        result[6]=wall((.72,21.4),(4.2,21.4),d(2.48,.8,swing=-1))
        result[8]=wall((2.7,21.4),(2.7,24.28),d(.6,.8,swing=-1))
    else:
        result[0]=wall((.72,14.52),(11.28,14.52),d(.16,.9),w(1.55,1.3),w(4.38,1.8),w(7.7,1.3),d(9.50,.9))
        result[2]=wall((.72,14.52),(.72,24.28),w(2.5,1.8),w(7.9,.8))
        result[3]=wall((11.28,14.52),(11.28,24.28),w(.3,1.1),d(2.48,1.1,swing=1,hinge_end=True),d(7.56,.9,swing=1))
        result[4]=wall((4.2,16.14),(4.2,24.28),d(.86,1.0,swing=1))
        result[5]=wall((7.8,16.14),(7.8,24.28))
        result[1]['openings'][3]=opening(7.3,1.15,'window',.8,1.8)
        result += [wall((.72,16.14),(4.2,16.14),w(.68,1.80),opening(2.60,.76,'passage',height=1.55)),
                   wall((7.8,16.14),(9.8,16.14),w(.3,1.35)),
                   wall((9.8,16.14),(9.8,18.35)),
                   wall((9.8,18.35),(11.28,18.35),d(.3,.9,swing=-1)),
                   {**wall((3.28,16.14),(3.28,16.47)), 'thickness':.08},
                   {**wall((3.28,16.47),(4.20,16.47)), 'thickness':.08}]
    result=[item for item in result if item['a'][0]!=9.3 and item['a']!=(7.8,21.4) and item['a']!=(9.3,21.4)]
    result[1]['openings'][-1]=w(9.05,.8)
    # Five-column wardrobes use the north wall ends; windows stay beside their cabinet footprints.
    result[1]['openings'][1]=w(2.18,.5) if group=='rear2' else result[1]['openings'][1]
    result[1]['openings'][3]=w(8.0,.85)
    result += [wall((14.22,21.76),(14.22,24.28),opening(1.45,.75,'window',1.5,.7)),
               wall((11.28,24.28),(14.22,24.28),opening(.42,1.2,'window',1.5,.7))]
    return result


def room_specs():
    result=[]
    for group, rooms in ROOMS.items():
        for index,(name,bounds,kind) in enumerate(rooms):
            x1,y1,x2,y2=bounds
            inner=[x1+(.24 if x1==.6 else .12),
                   y1+(0 if y1==19.2 else .24 if y1 in (.6,15.6) else .12),
                   x2-(.24 if x2==11.4 else .12),
                   y2-(0 if y2==19.2 else .24 if y2 in (6.6,24.4) else .12)]
            if kind=='stair':
                inner=[x1+.24,y1+.24,x2-.24,y2-.24]
            elif group=='rear2' and name=='公共过厅':
                inner[1]=y1+.24
            finish=FINISHES[kind][0]
            if kind=="bed" and group in ("rear1","rear2"):
                finish="浅色石纹砖 / 米色织物"
            spec=dict(id=f"{group}-{index}",group=group,index=index,name=name,
                               bounds=bounds,inner=inner,kind=kind,finish=finish,
                               floor=3.6 if group=="rear2" else .3)
            if group=='rear1' and index==5:
                spec['shape_note']='老人卧室与北侧衣帽休闲区连通；2.2米床位于北段，南段梳妆，通往东套卫。'
            if group=='rear2' and index==5:
                spec['floor_parts']=[(7.92,16.26,9.68,21.28),(9.68,18.47,11.16,21.28)]
                spec['shape_note']='L形次卧；侧门入户过道独立分隔，一张1.8m双人床。'
            if group in ('rear1','rear2') and index==6:
                spec['inner'][1]=21.28
            if group in ('rear1','rear2') and index==7:
                spec['inner']=EAST_SUITE['inner']
            if group=='rear2' and index==9:
                spec['inner']=(9.92,16.14,11.16,18.23)
            if group=='rear1' and index==8:
                spec['inner']=[11.64,14.64,14.1,16.5]
                spec['finish']='耐水防滑地砖意向'
            result.append(spec)
    return result


def check():
    assert abs((FRONT[2] - FRONT[0]) - 3 * 3.6) < 1e-8
    assert abs(REAR[1] - FRONT[3] - 7.8) < 1e-8
    assert abs(20 * 0.165 - (LEVELS["upper"] - LEVELS["ground"])) < 1e-8
    assert 9 * 0.27 + 1.05 < 4.2 - WALL
    for box in (FRONT, REAR):
        assert box[0] - .45 >= 0 and box[2] + .45 <= SITE[0]
        assert box[1] - .45 >= 0 and box[3] + .45 <= SITE[1]
    assert FORECOURT['bounds'][1]==SITE_BOUNDS[1]
    assert STORAGE['bounds'][0] > FORECOURT['entry_path'][2]
    assert FRONT[1]-STORAGE['bounds'][3] >= .6-1e-8
    assert abs(COURTYARD_WALL_TOPS[0]-(LEVELS['upper']-.18))<1e-8
    for group in ("front", "rear1", "rear2","stair1","stair2","entry","storage"):
        for item in walls(group):
            a, b = item["a"], item["b"]
            assert (a[0] == b[0]) != (a[1] == b[1])
            length = abs(b[0] - a[0]) + abs(b[1] - a[1])
            previous_end = 0.0
            for op in sorted(item["openings"], key=lambda op: op["offset"]):
                assert previous_end <= op["offset"]
                assert op["offset"] + op["width"] < length
                assert 0 <= op["sill"] < op["sill"] + op["height"] <= 3.3
                previous_end = op["offset"] + op["width"]

    # These are furniture layout targets for this scheme, not code compliance limits.
    fixtures = furnishings()["rear2"]
    guest = next(obj for obj in fixtures if obj['kind']=='bed' and obj['room']==5)
    assert sum(obj['kind']=='bed' and obj['room']==5 for obj in fixtures)==1, "次卧改为一张双人床"
    assert guest['bounds'][0]-7.92 >= .9-1e-8, "次卧西侧床尾通路不足900mm"
    assert guest['bounds'][1]-18.47 >= .6-1e-8, "次卧南侧通路不足600mm"
    family = {obj["kind"]: obj["bounds"] for obj in fixtures if obj["room"] == 3 and obj["kind"] in ("sofa", "table")}
    assert family["table"][0] - family["sofa"][2] >= .5 - 1e-8, "家庭厅沙发茶几净距不足500mm"
    assert COVERED_ENTRY['bounds'][2] <= SITE[0]
    assert COVERED_ENTRY['roof_bounds'][3] >= STAIR['top_landing'][1]
    assert EAST_CANOPY['bounds'][0]<=BRIDGES[1][0] and EAST_CANOPY['bounds'][2]>=BRIDGES[1][2]
    assert EAST_CANOPY['bounds'][1]<=BRIDGES[1][1] and EAST_CANOPY['bounds'][3]>=BRIDGES[1][3]
    for group,index,rotation in (('rear1',5,270),('rear2',0,90)):
        bed = next(obj for obj in furnishings()[group] if obj['kind']=='bed' and obj['room']==index)
        room = next(spec for spec in room_specs() if spec['id']==f'{group}-{index}')
        assert bed['rotation']==rotation and bed['head_top']<=.75, "大床低床头及方向与房间不符"
        foot_clearance=bed['bounds'][0]-room['inner'][0] if rotation==270 else room['inner'][2]-bed['bounds'][2]
        assert foot_clearance >= .9, "床尾通路不足本轮900mm目标"
        if group=='rear2':
            assert room['inner'][3]-bed['bounds'][3] >= 1.1, "主卧北侧卫浴通路不足本轮1100mm目标"
    # The elderly suite has an open north zone; check the actual turn around the bed, not the old room-label boundary.
    import math
    elder=[obj for obj in furnishings()['rear1'] if obj['room'] in (5,6)]
    route=[(8.4,17.6),(8.4,21.76),(9.2,21.76),(9.2,22.55),(11.5,22.55)]
    for start,end in zip(route,route[1:]):
        for step in range(101):
            x=start[0]+(end[0]-start[0])*step/100;y=start[1]+(end[1]-start[1])*step/100
            for obj in elder:
                a,b,c,d=obj['bounds']
                assert math.hypot(max(a-x,0,x-c),max(b-y,0,y-d))>=.3-1e-8, ('老人房600mm通路被阻挡',obj['name'],x,y)


if __name__ == "__main__":
    check()
    data = dict(units="metres", status="concept / assumed site", site=SITE,
                front=FRONT, rear=REAR, bays=BAYS, levels=LEVELS, rooms=ROOMS,
                walls={key: walls(key) for key in ("front", "rear1", "rear2","stair1","stair2","entry","storage")},
                furniture=furnishings(),decorations=decoration(),room_specs=room_specs(),version="精装方案 O · 浅色精装（Q）",
                occupants=6,front_roof="accessible flat terrace",bridges=BRIDGES,stair=STAIR,
                courtyard_tree=False,roof_color="red",rear_clearance=5.0,
                bridge={"bounds":[10.2,6.6,11.4,14.4],"level":3.6,"width":1.2})
    from engineering import engineering_layout
    from hvac import hvac_layout
    data["covered_entry"]=COVERED_ENTRY
    data['site_bounds']=SITE_BOUNDS
    data['forecourt']=FORECOURT
    data['storage']=STORAGE
    data["east_canopy"]=EAST_CANOPY
    data['east_suite']=EAST_SUITE
    data['courtyard_walls']=COURTYARD_WALLS
    data['courtyard_wall_tops']=COURTYARD_WALL_TOPS
    data['courtyard_laundry']=COURTYARD_LAUNDRY
    data['terrace_pavilion']=TERRACE_PAVILION
    data['terrace_laundry']=TERRACE_LAUNDRY
    data['upper_laundry']=UPPER_LAUNDRY
    data['terrace_drying']=TERRACE_DRYING
    data['services_revision']='2026-11-07 / 二楼过厅洗衣与全屋水电复核'
    data['kitchen_exhaust']=KITCHEN_EXHAUST
    data['terrace_layout']=TERRACE_LAYOUT
    data['interior_style']={'name':'暖白木色·简约新中式','source':'用户提供的六张本地风格参考图',
                            'finishes':['木纹柜体','浅米灰石材','米色织物','暗藏暖灯','细木格栅','深色细框玻璃']}
    from interior_views import INTERIOR_VIEWS
    data['interior_renderings']=[{'room':view['room'],'title':view['name'],
                                 'path':f"精装效果图/{view['id']}-{view['name']}.png"} for view in INTERIOR_VIEWS]
    data['wardrobe_revision']='2026-11-07 / 三卧室五列衣柜与15扇独立柜门'
    data['interior_rendering_note']='Q版浅色精装渲染；后排石纹砖、晾衣亭浅色顶棚；五列衣柜及二楼洗衣位置以交互3D为准；非现场照片'
    data['entry_route']={'door_y':(17.0,18.1),'hall':'rear2-9','connection':'rear2-8',
                         'interior_change':'L-shaped guest bedroom and independent entry passage'}
    data["engineering"]=engineering_layout(ROOMS,furnishings())
    data["hvac"]=hvac_layout()
    (ROOT / "model" / "design.json").write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print("Geometry checks passed; model/design.json written.")
