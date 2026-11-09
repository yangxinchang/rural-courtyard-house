"""Shared concept axes and service routes; positions only, never construction sizing."""


def engineering_layout(rooms, fixtures):
    """Return metre-based XYZ members, routes, devices and septic placement without importing design."""
    members, routes, devices, circuits = [], [], [], []
    septic = dict(bounds=[8.0,25.9,11.6,28.3], inlet=[8.0,27.1,-.55],
                  outlet=[11.6,27.1,-.7],
                  note="三格位置示意，容量/尺寸/退距/地下水及清掏条件待专项设计")

    def member(a, b, role, floor):
        members.append(dict(id=f"S-{len(members)+1:03}", a=tuple(a), b=tuple(b),
                            role=role, floor=floor))

    def route(system, floor, label, points):
        clean = []
        for point in points:
            point = tuple(round(v, 4) for v in point)
            if not clean or point != clean[-1]:
                clean.append(point)
        assert len(clean) >= 2, label
        routes.append(dict(id=f"R-{len(routes)+1:03}", system=system, points=clean,
                           floor=floor, label=label))

    def device(system, point, floor, label, kind):
        point = tuple(round(v, 4) for v in point)
        devices.append(dict(id=f"D-{len(devices)+1:03}", system=system, point=point,
                            floor=floor, label=label, type=kind))
        return point

    # shortcut: these axes belong to revision J; regenerate them when the building envelope changes.
    xs = (.72, 4.2, 7.8, 11.28)
    for floor, ys, bottom, top in (
        ("front", (.72, 6.48), .3, 3.6),
        ("rear1", (16.14, 21.4, 24.28), .3, 3.6),
        ("rear2", (16.14, 21.4, 24.28), 3.6, 6.9),
    ):
        for x in xs:
            for y in ys:
                member((x, y, bottom), (x, y, top), "column", floor)
            for y1, y2 in zip(ys, ys[1:]):
                member((x, y1, top), (x, y2, top), "beam", floor)
        for y in ys:
            for x1, x2 in zip(xs, xs[1:]):
                member((x1, y, top), (x2, y, top), "beam", floor)
    for x in (1.2, 10.8):
        for y in (9.0, 12.0):
            member((x, y, .3), (x, y, 3.6), "bridge_column", "site")
        member((x, 6.48, 3.6), (x, 14.64, 3.6), "bridge_beam", "site")
    for x in (11.52,14.22):
        for y in (16.62,21.76):
            member((x,y,.3),(x,y,3.6),"stair_column","rear1")
            member((x,y,3.6),(x,y,6.9),"stair_column","rear2")
        member((x,16.62,6.9),(x,21.76,6.9),"stair_roof_beam","rear2")
    for y in (16.62,21.76):
        member((11.52,y,6.9),(14.22,y,6.9),"stair_roof_beam","rear2")
    for floor,base,top in (('rear1',.3,3.6),('rear2',3.6,6.9)):
        for x in (11.28,14.22):
            member((x,24.28,base),(x,24.28,top),'suite_column',floor)
            member((x,21.76,top),(x,24.28,top),'suite_beam',floor)
        member((11.28,24.28,top),(14.22,24.28,top),'suite_beam',floor)
    member((11.64,21.52,1.95),(14.1,21.52,1.95),"stair_landing_beam","site")
    member((11.4,16.62,3.6),(14.22,16.62,3.6),"stair_top_beam","rear2")
    for x in (11.52,14.22):
        member((x,14.52,.3),(x,14.52,3.6),"entry_column","rear1")
        member((x,14.52,3.6),(x,16.62,3.6),"entry_roof_beam","rear1")
    member((11.52,14.52,3.6),(14.22,14.52,3.6),"entry_roof_beam","rear1")
    for x in (10.25,11.35):
        for y in (6.75,9.25,11.75,14.15):
            member((x,y,3.6),(x,y,6.4),"bridge_canopy_column","rear2")
        member((x,6.4,6.4),(x,14.64,6.4),"bridge_canopy_beam","rear2")
    for y in (6.75,9.25,11.75,14.15):
        member((10.25,y,6.4),(11.35,y,6.4),"bridge_canopy_crossbeam","rear2")

    panels = {
        "front": device("electric", (7.62, 1.65, 1.7), "front", "DB0 总配电箱（暂定）", "panel"),
        "rear1": device("electric", (7.62, 16.1, 1.7), "rear1", "DB1 首层分箱（暂定）", "panel"),
        "rear2": device("electric", (7.60, 18.60, 5.0), "rear2", "DB2 二层分箱（暂定）", "panel"),
    }
    meter = device("electric", (7.62, .35, 1.7), "site", "IN 电源入户（暂定）", "meter")
    route("electric", "front", "入户至通堂东墙 DB0", [meter, panels["front"]])
    route("electric", "site", "DB0 → DB1：东连廊下方馈线示意", [
        panels["front"], (7.62, 1.65, 2.85), (7.62, 6.1, 2.85),
        (10.45, 6.1, 2.85), (10.45, 14.85, 2.85), (7.62, 14.85, 2.85),
        (7.62, 16.1, 2.85), panels["rear1"],
    ])
    route("electric", "rear2", "DB1 → DB2：家庭厅东墙电气竖向通道", [panels['rear1'],(7.62,16.1,6.71),(7.60,16.1,6.71),(7.60,18.60,6.71),panels['rear2']])

    def electrical_branch(floor, point, label, kind, circuit=None, appliance_id=None):
        point = device("electric", point, floor, label, kind)
        panel = panels[floor]
        z = 6.71 if floor == "rear2" else 3.41
        row = 6.1 if floor == "front" else 16.1
        panel_id={'front':'DB0','rear1':'DB1','rear2':'DB2'}[floor]
        use='lighting' if kind in ('light','switch') else 'socket' if kind=='socket' else 'appliance'
        circuit=circuit or panel_id+'-'+('L' if use=='lighting' else 'S' if use=='socket' else f'A{sum(c["panel"]==panel_id and c["use"]=="appliance" for c in circuits)+1:02}')
        if not any(c['id']==circuit for c in circuits):
            circuits.append(dict(id=circuit,panel=panel_id,use=use,label=label if use=='appliance' else '照明与开关' if use=='lighting' else '普通插座',
                                 dedicated=use=='appliance',rcd_mA=None if use=='lighting' else 30,
                                 cable='按长度、敷设与负荷核算',breaker='按设备与线缆校核',earthing='PE保护导体连续；禁止以零线代替'))
        devices[-1]['circuit']=circuit
        if appliance_id:devices[-1]['applianceId']=appliance_id
        route("electric", floor, label, [panel, (panel[0], panel[1], z),
              (panel[0], row, z), (point[0], row, z),
              (point[0], point[1], z), point])
        routes[-1]['circuit']=circuit;routes[-1]['installation']='吊顶检修层穿管敷设，末端沿墙垂直下引'
        return point

    electrical_branch('rear2',(11.08,16.65,4.8),'ENT 侧主门照明开关','switch')
    sockets={
        ('front',0):(7.96,1.65,1.45),('front',1):(4.36,3.60,.65),('front',2):(.86,4.10,.65),
        ('rear1',0):(.86,20.35,.65),('rear1',2):(4.04,22.65,.65),('rear1',3):(7.64,20.60,.65),
        ('rear1',5):(11.12,18.55,1.0),('rear1',6):(11.10,23.30,1.45),('rear1',8):(11.66,15.95,.65),
        ('rear2',0):(.86,19.55,4.30),('rear2',2):(2.86,23.90,4.0),('rear2',3):(7.64,19.55,3.95),
        ('rear2',5):(11.12,18.85,4.30),('rear2',6):(11.10,23.50,4.00),('rear2',8):(7.64,16.0,4.0),
        ('rear2',9):(11.10,16.65,3.95)}
    entry_controls={
        'front':[(7.94,4.25,'厨房'),(7.64,1.0,'通堂'),(4.04,4.30,'客房')],
        'rear1':[(4.04,16.75,'起居室'),(2.54,21.8,'公卫门外'),(4.04,21.8,'家务'),(7.64,16.50,'堂屋'),(7.96,16.75,'老人房'),(11.10,23.10,'老人套卫门外'),(11.66,15.95,'门厅')],
        'rear2':[(4.04,16.75,'主卧'),(2.54,21.16,'套卫门外'),(4.40,16.30,'家庭厅'),(11.10,18.60,'次卧'),(11.10,23.10,'东套卫门外'),(.86,15.85,'公共过厅')]}
    for floor,points in entry_controls.items():
        for x,y,name in points:electrical_branch(floor,(x,y,(3.6 if floor=='rear2' else .3)+1.3),name+'入口照明开关','switch')

    for floor, floor_rooms in rooms.items():
        base = 3.6 if floor == "rear2" else .3
        for index, (name, bounds, kind) in enumerate(floor_rooms):
            if kind == "stair":
                electrical_branch(floor,(14.04,17.5,base+2.0),"ST 楼梯照明/感应位","light")
                continue
            x1, y1, x2, y2 = bounds
            cx, cy = (x1+x2)/2, (y1+y2)/2
            electrical_branch(floor, (cx, cy, base+2.55), f"L{index+1} {name}照明", "light")
            if kind != "wet":
                electrical_branch(floor, sockets[(floor,index)],
                                  f"S{index+1} {name}普通插座", "socket")
            if y2-y1 > 7:
                electrical_branch(floor, (cx, y2-1.5, base+2.55),
                                  f"L{index+1}b {name}北段照明", "light")
        equipment = {"hob": "K1 烟机/灶具预留", "oven": "K2 烤箱专用", "coffee": "K3 西厨台面",
                     "fridge": "K4 冰箱专用", "washer": "W1 洗衣机专用",
                     'dishwasher':'K5 洗碗机专用','microwave':'K6 微波炉电源',
                     'griddle':'K7 电饼铛电源','ricecooker':'K8 电饭煲电源'}
        for item in fixtures.get(floor, []):
            if item.get('dressing'):
                a,b,c,d=item['bounds']
                electrical_branch(floor,(.86 if floor=='rear2' else 11.12,(b+d)/2,base+1.7),item['name']+'镜前灯预留','light')
                electrical_branch(floor,(.86 if floor=='rear2' else 11.12,b+.12,base+1.05),item['name']+'台面插座','socket')
            if item["kind"] not in equipment:
                continue
            x1, y1, x2, y2 = item["bounds"]
            kitchen_points={'hob':(11.12,2.72,2.35),'oven':(7.96,3.5,1.15),'coffee':(7.96,1.75,1.45),
                            'fridge':(11.12,5.62,.95),'dishwasher':(11.12,3.86,.85),'microwave':(8.65,6.32,1.65),
                            'griddle':(8.60,.86,1.50),'ricecooker':(10.70,.86,1.50)}
            if item['kind']=='hob' and item.get('name','').startswith('猛火灶 2'):continue
            point=kitchen_points[item['kind']] if floor=='front' else (4.04,23.25,base+1.15)
            electrical_branch(floor,point,equipment[item['kind']],"equipment")
            if item['kind'] in ('oven','dishwasher'):
                devices[-1]['access']='相邻可开启柜内检修插座，避水管；设备不可封死检修口'

    for y in (8,10.5,13):
        electrical_branch('rear2',(10.8,y,6.28),'BR 二层东侧雨廊照明预留','light')
    for floor,base in (('rear1',.3),('rear2',3.6)):
        electrical_branch(floor,(14.10,22.65,base+2.7),'VF 东套卫排风电源预留','equipment')
    from hvac import hvac_layout
    for unit in hvac_layout()["units"]:
        electrical_branch(unit["floor"],unit["indoor"],unit["id"]+" 空调专用电源预留","equipment")
    from interiors import decoration
    for floor,items in decoration().items():
        ground=3.6 if floor=='rear2' else .3
        for item in items:
            if item['kind'] not in ('pendant','lightstrip','lantern'):continue
            x1,y1,x2,y2=item['bounds']
            electrical_branch(floor,((x1+x2)/2,(y1+y2)/2,ground+item['z']),
                              'DECO '+item['name']+' 预留','light')

    shafts = {
        "cold": ((.42, 23.92), (14.45, 23.92), .45, 1.05),
        "hot": ((.29, 23.78), (14.48, 23.78), .60, 1.15),
        "waste": ((.15, 23.64), (14.42, 23.64), -.3, .12),
    }
    inlet = device("cold", (13.4, .22, .45), "site", "CW 市政/水源接口待核", "inlet")
    route("cold", "site", "CW 外围供水干管（埋深待定）", [inlet,(14.45,.22,.45),
          (14.45,24.72,.45),(14.45,23.92,.45),
          (14.45,24.72,.45),(.42,24.72,.45),(.42,23.92,.45)])
    washer = next((f for f in fixtures.get("rear1", []) if f["kind"] == "washer"), None)
    heat_x = 4.0
    heat = device("hot", (heat_x, 23.10, 1.5), "rear1", "HW 热源接口（类型/容量待定）", "heater")
    device("cold", heat, "rear1", "HW 热源冷水接口", "heater_inlet")
    route("cold", "rear1", "热源进水", [(14.45, 23.92, .45), (14.45, 24.72, .45),
          (heat_x, 24.72, .45), (heat_x, 23.10, .45), heat])
    route("hot", "site", "HW 外围热水分配（保温/循环待深化）", [heat, (heat_x, 24.58, 1.5),
          (14.48,24.58,1.5),(14.48,24.58,.6),(14.48,23.78,.6),(14.48,.35,.6)])
    route("hot", "site", "HW 西侧支干管", [(14.48, 24.58, .6), (.29, 24.58, .6), (.29, 23.78, .6)])
    west_well = device("waste", (.95,25.1,-.3), "site", "IW1 西侧检查井（暂定）", "inspection")
    east_well = device("waste", (12.5,25.1,-.35), "site", "IW2 东侧检查井（暂定）", "inspection")
    collection = device("waste", (7.25,25.45,-.4), "site", "IW3 屋后汇集检查井（暂定）", "inspection")
    tank_in = device("waste", septic["inlet"], "site", "ST-IN 化粪池西侧进水", "septic_inlet")
    tank_out = device("waste", septic["outlet"], "site", "ST-OUT 化粪池东侧出水", "septic_outlet")
    downstream = device("waste", (13.4,28.7,-.8), "site", "后续处理/排放接点待定", "future_connection")
    route("waste", "site", "WW 西卫浴/洗衣至屋后检查井", [(.15,23.64,-.22), (.15,25.1,-.2419), (.95,25.1,-.2539), west_well])
    route("waste", "site", "WW 东卫浴至屋后检查井", [(14.42,23.64,-.25), (14.42,25.1,-.2719), (12.5,25.1,-.3007), east_well])
    route("waste", "site", "WW 西检查井至汇集井", [west_well, (7.25,25.1,-.3), (7.25,25.45,-.3), collection])
    route("waste", "site", "WW 东检查井至汇集井", [east_well, (12.5,25.45,-.35), (7.25,25.45,-.35), collection])
    route("waste", "site", "WW 汇集井至化粪池西侧进水", [collection, (7.25,27.1,-.4), (7.25,27.1,-.55), tank_in])
    route("waste", "site", "WW 三格过流关系（内部构造未设计）", [tank_in, (9.2,27.1,-.55),
          (9.2,27.1,-.6), (10.4,27.1,-.6), (10.4,27.1,-.65), (11.6,27.1,-.65), tank_out])
    route("waste", "site", "WW 后续处理/排放接点待定，不表示可直接外排", [tank_out,
          (12.45,27.1,-.7), (12.45,28.7,-.7), (12.45,28.7,-.8), downstream])
    for system, (west, east, base, offset) in shafts.items():
        for side, (x, y) in enumerate((west, east)):
            low, high = .3+offset, 3.6+offset
            lower, upper = [(x,y,base), (x,y,low)], [(x,y,low), (x,y,high)]
            if system == "waste":
                lower.reverse(); upper.reverse()
            route(system, "rear1", f"{'西' if side == 0 else '东'}{system}立管：首层/室外连接", lower)
            route(system, "rear2", f"{'西' if side == 0 else '东'}{system}立管：首层/二层连接", upper)

    def gravity_branch(floor,label,point,xy_path,ground,**meta):
        # shortcut: 1.5% is the concept routing allowance; size pipes and slab drops after survey.
        z=ground-(.27 if ground>3 else .15);points=[point,(point[0],point[1],z)]
        for x,y in xy_path:
            previous=points[-1];z-=.015*(abs(x-previous[0])+abs(y-previous[1]))
            points.append((x,y,z))
        route('waste',floor,label,points)
        routes[-1].update(slope_target=.015,installation='楼板下可检修排水；预留套管，禁止凿梁穿柱',**meta)

    supply_kinds = {"wc": .55, "vanity": .75, "shower": 1.15, "sink": .65, "washer": .65,'dishwasher':.65}
    for floor, floor_items in fixtures.items():
        ground = 3.6 if floor == "rear2" else .3
        for item in floor_items:
            kind = item["kind"]
            if kind not in supply_kinds:
                continue
            x1, y1, x2, y2 = item["bounds"]
            fx, fy = (x1+x2)/2, (y1+y2)/2
            side = 0 if fx < 6 else 1
            systems = ("cold", "hot", "waste") if kind in ("vanity", "shower", "sink") else ("cold", "waste")
            for system in systems:
                west, east, bottom, offset = shafts[system]
                sx, sy = (west, east)[side]
                z = ground+offset
                endpoint_z = ground+((.018 if kind=='shower' else .08 if kind=='wc' else .65 if kind in ('washer','dishwasher') else .50) if system=='waste' else supply_kinds[kind]+(.08 if system=='hot' else 0))
                point = device(system, (fx, fy, endpoint_z), floor, item["name"].split(" / ")[0], kind)
                if system=='waste':
                    if floor=='front':
                        side_x=11.9 if side else .15;outer_x=14.5 if side else .15
                        gravity_branch(floor,'WW 厨房排水沿外缘至污废水井',point,[(side_x,fy),(outer_x,fy),(outer_x,25.1)],ground)
                        last=routes[-1]['points'][-1];well=east_well if side else west_well
                        route('waste',floor,'厨房排水井接入',[last,(last[0],last[1],-.3),(well[0],last[1],-.3),well])
                    else:
                        wall_x=.93 if side==0 else 14.05
                        gravity_branch(floor,'WW '+item['name'].split(' / ')[0],point,[(wall_x,fy),(wall_x,sy),(sx,sy)],ground)
                    continue
                if floor == "front":
                    path = [(sx, fy, bottom), (sx, fy, z), (fx, fy, z), point]
                    if side==0:
                        path=[(sx,sy,bottom)]+path
                elif fx>11.4:
                    north={'cold':24.72,'hot':24.58,'waste':24.86}[system]
                    path=[(sx,sy,z),(sx,north,z),(14.45,north,z),(14.45,fy,z),(fx,fy,z),point]
                elif kind == "washer":
                    north = {"cold":24.72, "hot":24.58, "waste":24.86}[system]
                    path = [(sx, sy, z), (sx, north, z), (fx, north, z), (fx, fy, z), point]
                else:
                    wall_x = .93 if side == 0 else 11.07
                    path = [(sx, sy, z), (wall_x, sy, z), (wall_x, fy, z), (fx, fy, z), point]
                route(system, floor, f"{system} · {item['name'].split(' / ')[0]}", path)

    for floor,ground in (('rear1',.3),('rear2',3.6)):
        for room,points,shaft in ((1,[(1.70,23.65),(2.25,23.05)],(.15,23.64)),(7,[(12.50,23.65),(12.85,22.75)],(14.42,23.64))):
            for n,(x,y) in enumerate(points):
                point=device('waste',(x,y,ground+.018),floor,('西' if room==1 else '东')+('淋浴地漏' if n==0 else '卫浴干区地漏'),'floor_drain')
                devices[-1].update(roomId=f'{floor}-{room}',trap='带可维护水封防臭，避免重复存水弯')
                gravity_branch(floor,'卫浴地漏独立支管',point,[(x,shaft[1]),shaft],ground)

    from interiors import COURTYARD_LAUNDRY,TERRACE_LAUNDRY,TERRACE_PAVILION,UPPER_LAUNDRY,TERRACE_DRYING
    for laundry,floor,base,west_y in [(COURTYARD_LAUNDRY,'site',0,8.4),(TERRACE_LAUNDRY,'rear2',3.6,5.5)]:
        fixtures=[(m['bounds'],m['name'],m['kind'],m['z']) for m in laundry['machines']]
        fixtures.append((laundry['sink'],'院内洗衣池' if base==0 else '二楼洗衣池','sink',0))
        for bounds,label,kind,offset in fixtures:
            a,b,c,d=bounds;x,y=(a+c)/2,(b+d)/2
            if kind!='dryer':
                tap=device('cold',(x,y,base+.65),floor,label+'进水','tap')
                route('cold',floor,label+'冷水支管',[(.42,23.92,.45),(.42,west_y,.45),(.42,west_y,base+.65),(x,west_y,base+.65),tap])
            drain=device('waste',(x,y,base+.12),floor,label+('冷凝排水预留' if kind=='dryer' else '污废水排水'),'waste')
            route('waste',floor,label+'接西侧污废水井',[drain,(.15,y,base+.12),(.15,y,-.2),(.15,25.1,-.2),(.15,25.1,-.3),west_well])
            if kind!='sink':
                point=(.82,y,1.25) if base==0 else (x,5.59,4.80)
                socket=device('electric',point,floor,label+'防溅专用插座预留','equipment')
                circuit='DB0-W'+str(len([c for c in circuits if c['id'].startswith('DB0-W')])+1)
                devices[-1]['circuit']=circuit
                circuits.append(dict(id=circuit,panel='DB0',use='appliance',label=label,dedicated=True,rcd_mA=30,cable='按设备负荷和线路长度核算',breaker='按设备校核',earthing='独立PE保护导体'))
                route('electric',floor,label+'独立电源示意',[panels['front'],(7.62,1.65,2.85),(7.62,6.4,2.85),(.82,6.4,2.85),(.82,west_y,2.85),(.82,west_y,base+2.0),(point[0],west_y,base+2.0),(point[0],point[1],base+2.0),socket])
                routes[-1]['circuit']=circuit
        fd=device('waste',laundry['drain'],floor,'院内洗衣区防臭地漏' if base==0 else '二楼洗衣区防臭地漏','floor_drain')
        route('waste',floor,'洗衣区地漏接污废水（非雨水）',[fd,(.15,fd[1],fd[2]),(.15,fd[1],-.2),(.15,25.1,-.2),(.15,25.1,-.3),west_well])
    upper=UPPER_LAUNDRY
    electrical_branch('rear2',upper['socket'],'二楼过厅洗烘一体机防溅专用插座','equipment',circuit='DB2-W1',appliance_id='upper-combo')
    valve=device('cold',upper['valve'],'rear2','二楼过厅洗衣机可达关断阀','tap')
    route('cold','rear2','二楼洗衣冷水沿外墙及过厅吊顶至凹位',[(.42,23.92,4.65),(.42,23.92,6.45),(.42,15.45,6.45),(3.34,15.45,6.45),(3.34,16.25,6.45),valve])
    drain=device('waste',upper['standpipe'],'rear2','二楼洗衣机排水立管口（安装高度按机型核对）','waste')
    devices[-1].update(applianceId='upper-combo',trap='独立存水弯及可拆清扫口，禁止接雨水')
    gravity_branch('rear2','二楼洗衣机经过厅板下到西侧独立立管',drain,[(3.34,15.45),(.18,15.45)],3.6,applianceId='upper-combo')
    junction=routes[-1]['points'][-1]
    route('waste','rear2','二楼洗衣专用立管沿西外墙（可检修）',[(.18,15.45,3.72),(.18,15.45,-.08)])
    route('waste','site','二楼洗衣立管沿西侧埋地接检查井',[(.18,15.45,-.08),(.18,25.1,-.25),(.95,25.1,-.265),west_well])
    fd=device('waste',upper['drain'],'rear2','二楼过厅洗衣防臭地漏','floor_drain')
    devices[-1].update(roomId='rear2-8',trap='独立水封；保持补水与检修')
    gravity_branch('rear2','二楼洗衣地漏接同一污废水立管',fd,[(3.35,15.45),(.18,15.45)],3.6)
    route('waste','rear2','洗衣立管通气至屋面以上，终端避开门窗待深化',[(.18,15.45,3.72),(.18,15.45,10.6)])
    device('waste',(.18,15.45,3.20),'rear2','洗衣专用立管清扫口','cleanout')
    point=device('electric',(3.15,3.6,6.13),'rear2','亭子灯光预留','light')
    devices[-1]['circuit']='DB0-EXT-L'
    circuits.append(dict(id='DB0-EXT-L',panel='DB0',use='lighting',label='亭子及室外照明',dedicated=False,rcd_mA=30,cable='室外穿防护管，规格按敷设核算',breaker='按负荷核算',earthing='金属灯具PE连续'))
    route('electric','rear2','亭子灯光沿前屋檐口及亭梁穿管',[panels['front'],(7.62,1.65,3.41),(7.62,6.32,3.41),(1.95,6.32,3.41),(1.95,5.60,3.41),(1.95,5.60,6.13),(3.15,5.60,6.13),point])
    routes[-1]['circuit']='DB0-EXT-L'
    motor=device('electric',TERRACE_DRYING['motor'],'rear2','亭内电动升降晾衣机专用电源','equipment')
    devices[-1].update(circuit='DB0-D1',applianceId='pavilion-drying')
    control=device('electric',TERRACE_DRYING['control'],'rear2','电动晾衣机防溅墙控（带停止）','switch')
    devices[-1]['circuit']='DB0-D1'
    circuits.append(dict(id='DB0-D1',panel='DB0',use='appliance',label='亭内电动升降晾衣机',dedicated=True,rcd_mA=30,cable='沿前屋檐口与亭梁穿管，按机型功率选线',breaker='按设备校核',earthing='机壳及金属安装件PE连续'))
    route('electric','rear2','电动晾衣机沿檐口和亭梁专线',[panels['front'],(7.62,1.65,3.41),(7.62,6.32,3.41),(1.95,6.32,3.41),(1.95,5.60,3.41),(1.95,5.60,6.15),(4.30,5.60,6.15),control])
    routes[-1]['circuit']='DB0-D1'
    route('electric','rear2','墙控至晾衣机沿亭柱梁接线',[control,(4.30,5.60,6.15),(4.30,3.20,6.15),motor])
    routes[-1]['circuit']='DB0-D1'
    rain_out = device("rain", (13.75, .06, .24), "site", "RW 雨水独立出户（去向待核）", "outlet")
    route("rain", "site", "RW 西侧雨水收集", [(.12,15.28,.24), (.12,.06,.24), (12.08,.06,.24), rain_out])
    route("rain", "site", "RW 东侧雨水收集", [(14.54,15.28,.24),(14.54,.06,.24),(12.08,.06,.24)])
    stair_drain=device("rain",(14.15,17.0,6.9),"rear2","RW 新梯间屋面雨水口（暂定）","rain_drain")
    route("rain","rear2","RW 梯间屋面独立接雨水干管",[stair_drain,(14.54,17.0,6.9),
          (14.54,17.0,.24),(14.54,15.28,.24)])
    entry_drain=device("rain",(14.15,15.9,3.6),"rear1","RW 避雨门厅屋面雨水口（暂定）","rain_drain")
    route("rain","rear1","RW 避雨门厅屋面接独立雨水干管",[entry_drain,(14.54,15.9,3.6),
          (14.54,15.9,.24),(14.54,15.28,.24)])
    canopy_drain=device('rain',(11.48,13.95,6.56),'rear2','RW 二层东侧雨廊雨水口（暂定）','rain_drain')
    route('rain','rear2','RW 二层东侧雨廊接独立雨水干管',[canopy_drain,(11.58,13.95,6.56),
          (11.58,13.95,.24),(14.54,13.95,.24),(14.54,15.28,.24)])
    for floor, y, z in (("front",6.3,3.6), ("rear2",15.28,7.9)):
        for x in (.12, 11.94):
            drain = device("rain", (x,y,z), floor, "RW 屋面雨水口（暂定）", "rain_drain")
            gutter_x=.12 if x<6 else 14.54 if floor=="rear2" else 12.08
            points=[drain,(gutter_x,y,z),(gutter_x,y,.24)]
            if floor=="front" and x>6:points += [(gutter_x,.06,.24)]
            route("rain",floor,"RW 雨水立管（独立于污废水）",points)

    pavilion_drain=device('rain',(1.76,5.58,6.35),'rear2','亭子独立雨水槽','rain_drain')
    route('rain','rear2','亭子雨水接西侧雨水收集',[pavilion_drain,(1.78,5.58,6.35),(1.78,5.58,3.66),(.12,5.58,3.66),(.12,5.58,.24)])
    for x,y in ((.15,23.64),(14.42,23.64)):
        route("waste","rear2","污水立管通气延伸，终端位置待深化",[(x,y,3.72),(x,y,10.6)])
    route("waste","site","化粪池独立通气位置示意",[septic["outlet"],(11.6,28.15,-.7),(11.6,28.15,2.2)])
    suite_drain=device('rain',(14.12,24.15,6.9),'rear2','RW 东套卫屋面雨水口','rain_drain')
    route('rain','rear2','RW 东套卫屋面独立雨水',[suite_drain,(14.54,24.15,6.9),(14.54,24.15,.24),(14.54,15.28,.24)])

    notes = [
        "用户已确认按钢筋混凝土框架做方案；本图表达梁柱轴线，墙为填充/隔墙，未进行荷载、基础、抗震或构件验算。",
        "S 构件位置和显示粗细不代表施工截面；红瓦屋架、楼板、基础及封闭楼梯间配筋、通风采光和防火均待专项设计。",
        "DB0前屋、DB1后楼首层、DB2二层分区供电；二楼过厅洗烘机独立DB2-W1回路，厨房与洗烘大功率设备分别预留专线。",
        "插座及设备回路按30mA剩余电流保护设计意向，PE保护导体连续；最终保护器、线径、进线容量和分相须按实际负荷校核。",
        "室内支路在吊顶检修层穿管、末端沿墙垂直下引；室外线路沿檐口/梁柱防护敷设。穿墙及楼层转换预留套管，不得凿梁穿柱。",
        "四套卫浴上下对位；热源移到首层家务前室东侧实墙，避北窗；类型、容量、保温与循环待深化。",
        "室内排水按板下路径和1.5%概念降坡预留，卫浴补淋浴及干区地漏；最终管径、坡度、吊顶净高、存水弯和防水均须按现场校核。",
        "二楼洗衣位在主卧前公共过厅北侧凹位，朝南操作，前方1000mm；供水阀和插座在机器上方侧边，可拆面板检修，电水分置。",
        "洗衣专用立管沿西外墙至污废水井，设清扫口与通气；洗衣机排水口高度按机型，地漏独立水封，雨水不接洗衣污废水。",
        "污废水向屋后检查井汇集，再进入三格化粪池，西进东出；下游仅预留后续处理/排放接点，不表示允许直接外排。",
        "厨房排水经东侧封闭侧梯外缘绕行，基础实际外扩、隔油/清扫节点与埋深待核；雨水保持独立南向，不接化粪池。",
        "三格化粪池仅示意屋后位置与连接；容量、实际尺寸、退距、地下水、通气、结构、防渗及维护清掏条件需专项设计。",
        "后墙至后边界按用户给定的 5.00 m 净空表达，演示场地深度为 29.4 m；15.20 m 面宽仍为示意外包，检修维护与清掏可达条件待现场核实。",
        "本图为概念位置与路径沟通资料，不能据此施工。",
    ]
    return dict(members=members, routes=routes, devices=devices, circuits=circuits, notes=notes, septic=septic)
