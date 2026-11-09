"""Air conditioner positions and connection routes for design coordination only."""

def hvac_layout():
    units=[]
    records=[
        ("AC-1","客房","front",(.98,4.7,2.75),(.27,4.7,1.0),"west"),
        ("AC-2","起居室","rear1",(1.0,19.65,2.75),(2.3,25.25,.85),"west"),
        ("AC-3","老人卧室","rear1",(10.95,19.7,2.75),(4.1,25.25,.85),"east"),
        ("AC-4","主卧","rear2",(1.0,19.65,6.05),(2.3,25.25,2.05),"west"),
        ("AC-5","次卧","rear2",(10.95,18.6,6.05),(4.1,25.25,2.05),"east"),
        ("AC-6","家庭厅","rear2",(7.62,20.8,6.05),(5.9,25.25,.85),"east"),
    ]
    for name,label,floor,indoor,outdoor,side in records:
        x,y,z=indoor;ox,oy,oz=outdoor
        if floor=="front":
            refrigerant=[indoor,(.45,y,z),(.45,y,oz),outdoor]
            condensate=[(x,y,z-.15),(.35,y,z-.15),(.35,y,.16),(.35,.12,.12)]
        elif side=="east":
            refrigerant=[indoor,(x,24.55,z),(ox,24.55,z),(ox,oy,z),outdoor]
            condensate=[(x,y,z-.15),(x,24.55,z-.15),(x,24.55,.18),
                        (6.9,24.55,.18),(6.9,24.8,.18),(6.9,28.8,.10)]
        else:
            sx=.42 if side=="west" else 11.58
            refrigerant=[indoor,(sx,y,z),(sx,24.8,z),(ox,24.8,z),(ox,oy,z),outdoor]
            condensate=[(x,y,z-.15),(sx,y,z-.15),(sx,24.8,z-.15),
                        (sx,24.8,.18),(6.9,24.8,.18),(6.9,28.8,.10)]
        units.append(dict(id=name,label=label,floor=floor,indoor=indoor,outdoor=outdoor,
                          side=side,refrigerant=refrigerant,condensate=condensate))
    return dict(units=units,notes=[
        "室内机避开床头和直吹床位，前房厨房暂不设空调，西厨餐区散热/排烟待设备选型。",
        "后楼室外机集中在屋后西半部设备架，西侧客房室外机位于侧墙，需核实邻界和散热净距。",
        "机架高度、上下间隔、支架和减振均为位置示意，按具体机型安装检修要求调整；不得以此确定机型或支架。",
        "冷媒管紫红色、冷凝水绿色；管线穿墙仅预留位置，不得穿承重梁柱，套管与防水封堵待深化。",
        "后楼东侧机组先沿室内高位向北，再从屋后服务区接外机，避开右后侧封闭楼梯；实际路由和冷凝水坡度待深化。",
        "冷凝水单独收集至待定排水接点，不接化粪池、不滴在走廊楼梯；坡度、存水与接驳方式待现场设计。",
        "空调独立电源点位见电气示意，负荷、电源保护、线径及接地待专业校核。",
        "屋后机位在化粪池西侧，保留分区；化粪池检修清掏、通气口及外机散热/维护条件需现场协调。",
    ])
