"""Renovation fixtures shared by drawings, Blender and the browser room guide."""
import math

COURTYARD_LAUNDRY = dict(bounds=(.84,6.72,1.50,8.75),work_area=(1.50,6.72,2.70,8.75),
    washer=(.87,6.78,1.47,7.40),sink=(.93,8.14,1.41,8.66),counter_height=.92,
    drain=(1.65,8.50,.025),drying_bounds=(.98,9.55,1.70,11.35),drying_height=2.10,
    machines=[dict(id='ground-main',name='主洗衣机',kind='washer',bounds=(.87,6.78,1.47,7.40),z=.05,height=.84),
              dict(id='ground-dryer',name='叠放烘干机',kind='dryer',bounds=(.87,6.78,1.47,7.40),z=.94,height=.84),
              dict(id='ground-small',name='分区洗衣机',kind='washer',bounds=(.93,7.47,1.47,8.01),z=.05,height=.72)])
TERRACE_PAVILION = dict(roof_bounds=(1.70,1.35,4.60,5.85),posts=((1.95,1.60),(4.35,1.60),(1.95,5.60),(4.35,5.60)),
    floor=3.6,roof_level=6.45,roof_fall=.06,table_center=(3.05,2.80),provisional=True)
TERRACE_LAUNDRY = dict(bounds=(2.10,4.95,4.10,5.55),sink=(3.02,5.03,3.58,5.47),
    work_area=(2.10,3.86,4.10,4.95),drain=(4.20,5.20,3.625),counter_height=.94,
    machines=[])
UPPER_LAUNDRY = dict(bounds=(3.32,15.64,4.04,16.42),work_area=(3.32,14.64,4.04,15.64),
    drain=(3.35,15.68,3.605),socket=(4.025,16.27,4.90),valve=(3.34,16.25,4.72),
    standpipe=(3.34,16.25,4.25),counter_height=.94,room='rear2-8',
    machines=[dict(id='upper-combo',name='二楼过厅洗烘一体机',kind='washer_dryer',bounds=(3.38,15.69,3.98,16.34),z=.04,height=.85)])
TERRACE_DRYING = dict(bounds=(2.45,1.95,3.85,4.25),floor=3.6,raised=5.85,lowered=4.85,
    motor=(3.15,3.20,6.15),control=(4.30,5.60,4.90),cable_top=6.08,
    verification=dict(site='未定',product='未定',structure='未定',status='空间复核；承重、锚固及室外适用性未核定'),
    note='亭内电动升降晾衣；桌椅和东侧旧晾衣架取消，水池保留；载荷及锚固按机型校核')

FINISHES = {
    "bed": ("暖橡木地板 / 米色织物", "#c3a47f"),
    "hall": ("浅米灰石纹砖 / 木线条", "#e4dfd3"),
    "wet": ("浅暖石纹防滑砖", "#cfcec2"),
    "service": ("浅米石纹砖 / 原木柜", "#dbd5c8"),
    "stair": ("浅色石材踏步", "#d5d4c7"),
}


def item(kind, room, bounds, name, height=.8, rotation=0):
    return dict(kind=kind, room=room, bounds=bounds, name=name,
                height=height, rotation=rotation)


def bathroom(room, mirror=False):
    data = [
        item("shower", room, (.90,22.20,2.52,23.10), "淋浴区",2.05),
        item("wc", room, (.93,21.50,1.65,22.00), "坐便器",.72),
        item("vanity", room, (.91,20.75,1.38,21.35), "洗手台 / 镜柜",.82),
    ]
    if mirror:
        for obj in data:
            x1,y1,x2,y2=obj["bounds"]
            obj["bounds"]=(12-x2,y1,12-x1,y2)
            obj["rotation"]=180
    return data


def furnishings():
    front = [
        item("cabinet",0,(.86,1.01,1.46,3.87),"厨房西侧地柜",.88),
        item("cabinet",0,(1.46,.87,3.12,1.47),"厨房南侧地柜",.88),
        item("cabinet",0,(3.48,1.80,4.04,3.70),"西厨 / 咖啡台",.9),
        item("oven",0,(3.50,2.65,4.02,3.27),"嵌入式烤箱",.65),
        item("coffee",0,(3.57,1.97,3.95,2.43),"咖啡机",1.25),
        item("hob",0,(.91,1.29,1.41,1.91),"双眼灶 / 烟机",.93),
        item("sink",0,(.91,3.05,1.41,3.73),"水槽",.93),
        item("fridge",0,(3.22,.87,4.02,1.65),"冰箱",2.05),
        item("table",0,(.98,4.85,2.78,5.65),"六人餐桌",.76),
        item("banquette",0,(.88,5.80,2.83,6.30),"三人餐区卡座",.85),
        item("chair",0,(1.05,4.29,1.47,4.71),"餐椅",.9,180),
        item("chair",0,(1.70,4.29,2.12,4.71),"餐椅",.9,180),
        item("chair",0,(2.35,4.29,2.77,4.71),"餐椅",.9,180),
        item("bench",1,(4.38,2.3,4.78,4.4),"入户换鞋凳",.45),
        item("bed",2,(8.72,1.65,10.36,3.80),"客房 1.5m 床",.95),
        item("wardrobe",2,(10.56,4.45,11.10,6.10),"客房滑门衣柜",2.4),
    ]
    rear1 = [
        {**item("bed",5,(8.87,16.75,11.02,19.09),"老人房 2.2m 东向低床头床",.75,270),"head_top":.75},
        item("nightstand",5,(10.60,16.30,11.02,16.70),"床头柜",.5),
        item("nightstand",5,(10.62,19.30,11.02,19.80),"床头柜",.5),
        {**item("wardrobe",6,(7.96,20.75,8.51,22.10),"滑门衣柜",2.4),"mirrored":True},
        item("console",3,(4.4,18.0,4.75,18.70),"玄关柜",.9),
        item("sofa",0,(.99,17.05,1.79,19.65),"起居沙发",.86,180),
        item("table",0,(2.45,17.65,2.95,18.95),"茶几",.4),
        item("tv",0,(3.66,18.25,4.02,19.30),"电视 / 矮柜",.55,180),
        item("washer",2,(3.36,22.42,4.02,23.08),"洗衣机",.88),
        item("cabinet",2,(2.88,22.42,3.33,23.08),"窗下家务矮柜",.76),
        item("bench",8,(13.62,14.92,14.08,15.92),"门厅换鞋凳",.45),
    ] + bathroom(1) + bathroom(7,True)
    rear2 = [
        {**item("bed",0,(.98,16.75,3.13,19.09),"主卧 2.2m 西向低床头床",.75,90),"head_top":.75},
        item("nightstand",0,(.98,16.30,1.40,16.70),"床头柜",.5),
        item("nightstand",0,(.98,19.30,1.38,19.80),"床头柜",.5),
        item("wardrobe",2,(3.49,20.75,4.04,22.10),"滑门衣柜",2.4),
        item("sofa",3,(4.40,18.80,5.20,21.10),"家庭厅三人沙发",.86,180),
        item("table",3,(5.70,19.30,6.20,20.40),"家庭厅茶几",.4),
        item("tv",3,(7.30,20.30,7.66,21.50),"家庭厅电视 / 矮柜",.55),
        item("wardrobe",3,(7.06,21.55,7.66,23.15),"北端共用滑门收纳柜",2.4),
        item("desk",3,(4.40,22.50,6.65,23.06),"双人共享学习桌",.75),
        item("chair",3,(4.75,21.83,5.25,22.33),"学习椅 A",.9,180),
        item("chair",3,(5.70,21.83,6.20,22.33),"学习椅 B",.9,180),
        {**item("bed",5,(8.87,19.30,11.02,21.24),"次卧 1.8m 东向低床头床",.75,270),"head_top":.75},
        {**item("wardrobe",6,(7.96,20.95,8.51,22.30),"次卧独立滑门衣柜",2.4),"mirrored":True},
        item("desk",6,(9.25,22.50,10.75,23.06),"次卧窗下书桌",.75),
        item("chair",6,(9.75,21.85,10.25,22.35),"书桌椅",.9,180),
    ] + bathroom(1) + bathroom(7,True)
    for obj in front:
        if obj["room"] in (0,2):
            x1,y1,x2,y2=obj["bounds"]
            obj["bounds"]=(12-x2,y1,12-x1,y2)
            obj["mirrored"]=True
            obj["name"]=obj["name"].replace("厨房西侧","厨房东侧")
    rear1=[obj for obj in rear1 if obj["room"]!=3]
    guest=next(obj for obj in front if obj['kind']=='bed')
    guest.update(bounds=(.98,1.4,3.13,3.34),rotation=90,name='客房 1.8m 横向床')
    for group in (rear1,rear2):
        for obj in group:
            if obj["room"] in (1,2,6,7) or obj["room"]==3 and obj["kind"] in ("wardrobe","desk","chair"):
                x1,y1,x2,y2=obj["bounds"]
                obj["bounds"]=(x1,y1+1,x2,y2+1)
        group[:]=[obj for obj in group if obj['room']!=7]
        group += [item('shower',7,(11.65,23.20,13.30,24.06),'北侧淋浴区',2.05),
                  item('wc',7,(13.31,22.70,14.02,23.20),'坐便器',.72,180),
                  item('vanity',7,(13.55,22.03,14.02,22.63),'洗手台 / 镜柜',.82,180)]
    front=[obj for obj in front if not (obj['room']==0 and obj['kind'] in ('table','chair','banquette'))]
    next(obj for obj in front if obj['kind']=='fridge')['bounds']=(10.34,4.75,11.14,5.55)
    front += [item('dishwasher',0,(10.54,4.00,11.14,4.60),'洗碗机预留600',.88),
              {**item('cabinet',0,(10.54,3.87,11.14,4.70),'洗涤与电器地柜',.88),'countertop_only':True},
              item('cabinet',0,(8.95,5.70,11.10,6.30),'北侧小家电操作台',.88),
              {**item('wardrobe',0,(7.96,3.75,8.52,4.35),'厨房食品高柜',2.35),'mirrored':True},
              {**item('microwave',0,(9.00,5.76,9.60,6.23),'微波炉预留',.38),'z':.94},
              {**item('griddle',0,(9.04,.91,9.53,1.36),'电饼铛操作位',.14),'z':.94},
              {**item('ricecooker',0,(9.75,.91,10.15,1.31),'电饭煲操作位',.35),'z':.94}]
    rear1 += [item('armchair',6,(9.68,23.20,10.48,23.98),'老人窗边休闲椅',.80),
              item('nightstand',6,(10.62,23.42,11.08,24.05),'老人休闲区矮边柜',.65)]
    for obj in rear1:
        if obj['room']==5 and obj['kind'] in ('bed','nightstand'):
            a,b,c,d=obj['bounds'];obj['bounds']=(a,b+2.35,c,d+2.35)
    north_stand=next(obj for obj in rear1 if obj['room']==5 and obj['kind']=='nightstand' and obj['bounds'][1]>21)
    north_stand['bounds']=(10.62,21.59,11.02,21.99)
    next(obj for obj in rear1 if obj['room']==6 and obj['kind']=='wardrobe')['bounds']=(7.96,22.15,8.51,23.50)
    rear1 += [{**item('desk',5,(10.66,17.10,11.12,18.20),'老人房梳妆台',.75),'dressing':True,'front':'west'},
              item('stool',5,(10.53,17.45,10.93,17.85),'老人梳妆凳（收进台下）',.44)]
    rear2 += [{**item('desk',0,(.90,19.96,1.38,20.96),'主卧梳妆台',.75),'dressing':True,'front':'east'},
              item('stool',0,(1.02,20.15,1.40,20.53),'主卧梳妆凳（收进台下）',.44)]
    hob=next(obj for obj in front if obj['kind']=='hob')
    hob.update(bounds=(10.59,1.20,11.09,1.82),name='猛火灶 1（示意）',burners=1)
    front.append({**item('hob',0,(10.59,1.94,11.09,2.56),'猛火灶 2（示意）',.93),'mirrored':True,'burners':1})
    rear1.append(item('roundtable',3,(5.40,21.80,6.60,23.00),'六人圆桌餐叙会客',.76))
    for i in range(6):
        angle=math.radians(i*60);cx=6+.89*math.sin(angle);cy=22.4+.89*math.cos(angle)
        rear1.append({**item('chair',3,(cx-.22,cy-.22,cx+.22,cy+.22),'圆桌软垫会客椅',.9,-i*60),'upholstered':True})
    for items,room,bedroom,name,rail in ((rear1,6,'rear1-5','老人房独立衣柜',1.55),
                                       (rear2,2,'rear2-0','主卧独立衣柜',1.85),
                                       (rear2,6,'rear2-5','次卧独立衣柜',1.75)):
        wardrobe=next(obj for obj in items if obj['room']==room and obj['kind']=='wardrobe')
        a,b,c,d=wardrobe['bounds']
        wardrobe.update(name=name,bedroom=bedroom,rail_height=rail,bounds=(a,22.08,c,24.08),columns=5,
                        layout='由南至北五列：长衣、双层短衣、抽屉叠放、活动层板、被褥杂物；顶部通长被褥区')
    return dict(front=front,rear1=rear1,rear2=rear2)


def decoration():
    """Finish and fitting positions, lower height measured from each finished floor."""
    data={key:[] for key in ('front','rear1','rear2')}
    def add(group,kind,room,bounds,name,z,height,material):
        data[group].append(dict(kind=kind,room=room,bounds=bounds,name=name,
                               z=z,height=height,material=material))
    add('front','panel',2,(.88,1.31,.94,3.43),'客房木色床头背景',.08,1.15,'oak')
    add('front','panel',0,(11.12,2.10,11.15,3.85),'中厨耐擦洗背板',.95,.6,'quartz')
    add('front','wallcabinet',0,(10.78,2.85,11.10,3.85),'中厨吊柜',1.60,.75,'oak')
    add('front','lightstrip',0,(10.78,2.89,10.81,3.81),'厨房柜下照明',1.56,.025,'light')
    add('front','lightstrip',0,(8.98,6.26,10.98,6.29),'小家电台面照明',1.56,.025,'light')
    add('front','wallcabinet',1,(4.38,.95,4.73,2.10),'通堂浅鞋柜',0,1.15,'oak')
    add('rear1','panel',5,(11.06,19.00,11.12,21.54),'老人房东墙低床头背景',.08,.64,'oak')
    add('rear2','panel',0,(.88,16.65,.94,19.19),'主卧西窗下低床头背景',.08,.64,'oak')
    add('rear1','panel',0,(4.03,18.05,4.07,19.55),'起居室电视背景',.55,1.65,'accent')
    add('rear2','panel',5,(11.06,19.20,11.12,21.34),'次卧东墙低床头背景',.08,.64,'oak')
    add('rear2','panel',3,(7.69,20.17,7.73,21.62),'家庭厅电视背景',.55,1.65,'accent')
    add('rear1','panel',0,(.85,17.20,.88,19.50),'起居室西窗下低背景',.08,.64,'accent')
    add('rear1','rug',0,(1.95,17.50,3.45,19.50),'起居区织物地毯',.024,.012,'fabric')
    add('rear2','rug',3,(5.27,18.65,6.96,21.17),'家庭厅休闲地毯',.024,.012,'fabric')
    add('rear2','lightstrip',3,(4.58,24.10,6.45,24.14),'双人学习桌阅读灯',1.65,.035,'light')
    add('rear1','grabbar',7,(14.03,22.72,14.10,23.18),'坐便区扶手意向',.74,.035,'metal')
    add('rear1','grabbar',7,(11.44,23.35,11.51,23.98),'淋浴扶手意向',.92,.035,'metal')
    add('rear1','bench',7,(11.85,23.60,12.33,24.02),'老人淋浴座凳意向',.42,.06,'oak')
    for group,room,y,spans in (
        ('front',2,.90,((1.42,1.70),(2.94,3.22))),
        ('rear1',5,15.90,((8.55,8.82),(10.32,10.60))),
        ('rear1',0,15.90,((1.40,1.68),(3.18,3.45))),
        ('rear2',0,16.30,((1.40,1.68),(2.93,3.20))),
        ('rear2',6,24.08,((8.60,8.77),(9.40,9.57))),
    ):
        for x1,x2 in spans:
            add(group,'curtain',room,(x1,y,x2,y+.07),'暖米色窗帘侧片',.15,2.6,'fabric')
    for group,objects in furnishings().items():
        for obj in objects:
            x1,y1,x2,y2=obj['bounds'];room=obj['room']
            if obj['kind']=='vanity':
                lx=x1 if obj['rotation']==0 else x2-.035
                add(group,'lightstrip',room,(lx,y1+.06,lx+.025,y2-.06),'洗手台镜前灯',1.88,.045,'light')
            if obj['kind']=='shower':
                add(group,'shelf',room,(x1+.18,y2-.20,x1+.63,y2+.06),'淋浴置物层板',1.25,.05,'quartz')
            if obj['kind']=='bed' and group=='rear2' and room==5:
                add(group,'bedbox',room,(x1+.08,y1+.12,x2-.08,y2-.12),'上掀式床箱意向',.13,.22,'oak')
    for group,room,x,north_y in (('rear1',5,11.12,19.17),('rear2',0,.85,19.50)):
        for y in (16.72,north_y):
            if group=='rear1':y+=2.35
            add(group,'lightstrip',room,(x,y,x+.03,y+.06),'床头两侧阅读灯',1.3,.32,'light')
    for group in ('rear1','rear2'):
        for y1,y2 in ((16.80,17.02),(18.82,19.04)):
            add(group,'curtain',0,(.86,y1,.93,y2),'西窗两侧帘片',.15,2.6,'fabric')
    for group,room,bounds in (
        ('front',0,(7.96,.88,11.12,6.32)),('front',1,(4.36,.88,7.64,6.32)),
        ('front',2,(.88,.88,4.04,6.32)),('rear1',0,(.88,15.88,4.04,21.24)),
        ('rear1',3,(4.36,15.88,7.64,24.12)),('rear1',5,(7.96,15.88,11.12,21.24)),
        ('rear2',0,(.88,16.30,4.04,21.24)),('rear2',3,(4.36,16.30,7.64,24.12)),
        ('rear1',6,(7.96,21.44,11.12,24.12)),
        ('rear2',5,(7.96,16.30,9.64,21.24)),('rear2',6,(7.96,21.44,11.12,24.12)),
    ):
        add(group,'cove',room,bounds,'暖白叠级顶面与暗藏灯槽',2.88,.10,'oak')
        if group in ('rear1','rear2') and room==3:
            data[group][-1]['north_gap']=(5.22,6.78)
    add('front','slats',1,(4.33,2.35,4.37,4.20),'通堂木格栅背景',.10,2.35,'oak')
    add('rear1','slats',3,(4.33,18.80,4.37,20.50),'堂屋侧墙木格栅',.18,2.35,'oak')
    add('rear1','slats',0,(4.025,18.05,4.07,18.48),'起居电视侧格栅',.55,1.65,'oak')
    add('rear2','slats',3,(7.69,20.17,7.735,20.60),'家庭厅电视侧格栅',.55,1.65,'oak')
    add('rear1','art',3,(4.38,19.05,4.405,20.15),'堂屋水墨装饰画',1.05,1.1,'oak')
    add('rear1','panel',3,(4.55,24.10,7.45,24.14),'圆桌厅北墙木色护墙',.08,1.1,'oak')
    add('rear2','art',3,(4.33,19.25,4.36,20.35),'家庭厅水墨装饰画',1.10,1.1,'oak')
    add('front','border',1,(4.52,1.00,7.48,6.10),'通堂石材细边线',.018,.001,'metal')
    add('rear1','border',3,(4.52,16.05,7.48,22.95),'堂屋石材细边线',.018,.001,'metal')
    add('front','lantern',1,(5.72,3.10,6.28,3.55),'通堂木框暖光灯',2.44,.30,'metal')
    add('rear1','lantern',3,(5.65,19.25,6.35,19.85),'堂屋框形暖光灯',2.42,.33,'metal')
    add('rear1','lantern',3,(5.65,22.05,6.35,22.75),'圆桌中心木框餐叙灯',2.10,.26,'metal')
    add('rear1','lightstrip',6,(11.10,23.48,11.13,23.78),'老人休闲区阅读灯',1.45,.30,'light')
    add('rear1','lightstrip',5,(11.10,18.35,11.13,18.75),'老人夜间导向灯',.25,.045,'light')
    add('rear2','lightstrip',6,(9.35,24.10,9.65,24.14),'次卧桌面阅读灯',1.12,.045,'light')
    add('rear2','lightstrip',6,(7.94,21.95,7.97,23.30),'次卧衣柜侧照明',2.50,.035,'light')
    for group in ('rear1','rear2'):
        for a,b in ((9.50,9.74),(10.61,10.88)):
            add(group,'curtain',6,(a,24.07,b,24.14),'北区窗边帘片',.15,2.6,'fabric')
        add(group,'sheer',6,(9.77,24.12,10.57,24.14),'北区透光纱帘',.15,2.6,'fabric')
    for group,room,bounds in (
        ('front',2,(1.70,.87,2.94,.89)),('rear1',5,(8.82,15.87,10.32,15.89)),
        ('rear1',0,(1.68,15.87,3.18,15.89)),
        ('rear2',0,(1.68,16.27,2.93,16.29)),('rear2',6,(8.77,24.125,9.40,24.145)),
        ('rear1',0,(.85,17.04,.87,18.80)),('rear2',0,(.85,17.04,.87,18.80)),
    ):
        add(group,'sheer',room,bounds,'透光米白纱帘意向',.15,2.6,'fabric')
    return data
