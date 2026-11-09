"""Create A3 vector concept sheets, SVGs and review PNGs from shared dimensions."""
import math
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, Circle, Arc
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import font_manager
from PIL import Image
from design import ROOT, FRONT, REAR, BAYS, ROOMS, walls, check, furnishings, room_specs, FINISHES, SITE, SITE_BOUNDS, FORECOURT, STORAGE, BRIDGES, STAIR, COVERED_ENTRY, EAST_CANOPY, EAST_SUITE, COURTYARD_WALLS, COURTYARD_WALL_TOPS, KITCHEN_EXHAUST, TERRACE_LAYOUT
from interiors import decoration, COURTYARD_LAUNDRY, TERRACE_LAUNDRY, TERRACE_PAVILION, UPPER_LAUNDRY, TERRACE_DRYING
from engineering import engineering_layout
from engineering_sheets import append_engineering_sheets
from hvac import hvac_layout
from material_recommendations import MATERIAL_PAGES, append_material_sheets

check()
FONT = "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
font_manager.fontManager.addfont(FONT)
plt.rcParams.update({"font.family":font_manager.FontProperties(fname=FONT).get_name(),
                     "pdf.fonttype":42,"svg.fonttype":"path","axes.unicode_minus":False})
INK, MUTED, GREEN, LINE = "#263a36", "#6c7770", "#476552", "#aebbb1"
COLORS = {"bed":"#f1e6d6","hall":"#eeeae0","wet":"#e1dfd3",
          "service":"#e5e8dd","stair":"#eeeee9"}
DECORATION_STYLES = {
    "panel": ("木饰背景 / 床头板", "#a77c4f", "///"),
    "curtain": ("窗帘两侧帘片", "#718b80", "|||"),
    "rug": ("厅区地毯", "#ba967c", ".."),
    "pendant": ("餐桌线形吊灯", "#b48736", None),
    "lightstrip": ("柜下 / 镜前 / 阅读灯", "#cf9d35", None),
    "grabbar": ("老人卫浴扶手", "#408d94", None),
    "bench": ("淋浴座凳", "#7d9990", "xx"),
    "wallcabinet": ("吊柜 / 浅鞋柜", "#798c68", "--"),
    "shelf": ("淋浴壁龛 / 层架", "#408d94", "//"),
    "bedbox": ("次卧上掀床箱", "#a77c4f", "++"),
    "cove": ("叠级灯槽", "#ba9c67", None),
    "slats": ("细木格栅", "#9c744d", "|||"),
    "lantern": ("木框暖光灯", "#b9955e", None),
    "sheer": ("透光纱帘", "#bab7aa", "..."),
    "art": ("水墨装饰画", "#80674d", None),
    "border": ("石材细边线", "#55534a", None),
}
PAGES = []


def txt(ax,x,y,s,size=8,color=INK,ha="left",va="center",**kwargs):
    return ax.text(x,y,s,fontsize=size,color=color,ha=ha,va=va,clip_on=True,**kwargs)


def rect(ax,x,y,w,h,fc="none",ec=INK,lw=.7,**kwargs):
    obj = Rectangle((x,y),w,h,facecolor=fc,edgecolor=ec,linewidth=lw,**kwargs)
    ax.add_patch(obj)
    return obj


def line(ax,xs,ys,color=INK,lw=.7,**kwargs):
    ax.plot(xs,ys,color=color,lw=lw,**kwargs)


def sheet(code,title,subtitle,scale="图示标尺 / 尺寸 mm"):
    fig = plt.figure(figsize=(420/25.4,297/25.4),facecolor="#fffefa")
    page = fig.add_axes([0,0,1,1]); page.set(xlim=(0,420),ylim=(0,297)); page.axis("off")
    rect(page,8,8,404,281,ec=LINE,lw=.65)
    txt(page,19,276,"院 · 居",20)
    txt(page,64,277,title,16)
    txt(page,19,263,subtitle,8.5,MUTED)
    txt(page,401,276,code,12,ha="right")
    line(page,[18,402],[255,255],GREEN,1)
    line(page,[18,402],[22,22],LINE,.6)
    txt(page,19,15,"精装方案 P·水电深化  /  2026.11.07  /  示意面宽 15.20 m  /  后方净空 5.00 m",7,MUTED)
    txt(page,402,15,f"{scale}  ·  A3 原尺寸打印  ·  概念方案，非施工图",7,MUTED,ha="right")
    return fig,page


def axes(fig,box,limits):
    x,y,w,h = box
    ax=fig.add_axes([x/420,y/297,w/420,h/297])
    ax.set_xlim(limits[0],limits[1]);ax.set_ylim(limits[2],limits[3]);ax.set_aspect("equal");ax.axis("off")
    return ax


def dim(ax,a,b,offset,label=None,vertical=False,size=6.7):
    if vertical:
        x,y1,y2 = offset,a,b
        line(ax,[x,x],[y1,y2],MUTED,.45)
        for y in (y1,y2): line(ax,[x-.13,x+.13],[y-.13,y+.13],MUTED,.6)
        txt(ax,x+.17,(y1+y2)/2,label or f"{(b-a)*1000:.0f}",size,MUTED,rotation=90,ha="center")
    else:
        y,x1,x2 = offset,a,b
        line(ax,[x1,x2],[y,y],MUTED,.45)
        for x in (x1,x2): line(ax,[x-.13,x+.13],[y-.13,y+.13],MUTED,.6)
        txt(ax,(x1+x2)/2,y+.15,label or f"{(b-a)*1000:.0f}",size,MUTED,ha="center",va="bottom")


def north(ax,x=-.95,y=25.8):
    ax.add_patch(Polygon([(x,y+.8),(x-.18,y),(x,y+.16),(x+.18,y)],facecolor=GREEN))
    txt(ax,x,y+1.12,"北 N",7,ha="center")


def scale_bar(ax,x=0,y=-1.45):
    for i in range(4): rect(ax,x+i,y,1,.12,GREEN if i%2==0 else "white",GREEN,.5)
    for i in (0,2,4):txt(ax,x+i,y-.2,str(i),6,MUTED,ha="center",va="top")
    txt(ax,x+4.45,y,"m",6,MUTED)


def yard(ax):
    rect(ax,0,6.6,12,7.8,"#f0f0e7",LINE,.6)
    for x in range(1,12):line(ax,[x,x],[6.6,14.4],"#d8ddd3",.3)
    for y in range(7,15):line(ax,[0,12],[y,y],"#d8ddd3",.3)
    rect(ax,4.8,6.6,2.4,7.8,"#e0e7da","none",0)
    rect(ax,8.65,10.1,1.3,.8,"#b4a08a",GREEN,.6)
    for x in (8.75,9.7):
        for y in (9.6,11.2):rect(ax,x-.2,y-.2,.4,.4,"#dad3c5",GREEN,.5)
    for x,y,w in [(4.8,6.6,2.4),(4.5,14.1,3)]:
        rect(ax,x,y,w,.3,"#ddd8ca",MUTED,.4)
    for a,b,c,d in COURTYARD_WALLS:rect(ax,a,b,c-a,d-b,INK,INK,.5)
    a,b,c,d=COURTYARD_LAUNDRY['bounds'];rect(ax,a,b,c-a,d-b,'#ceb28d',GREEN,.6)
    txt(ax,2.05,7.85,'洗衣区',5.5,GREEN,rotation=90,ha='center')


def site_outline(ax):
    a,b,c,d=SITE_BOUNDS
    rect(ax,a,b,c-a,d-b,ec=GREEN,lw=1,linestyle=(0,(5,3)))
    line(ax,[0,SITE[0]],[-8.5,-8.5],LINE,1.2)
    txt(ax,7.3,-9.0,"南侧通路位置示意 / 待实测",7,MUTED,ha="center")
    north(ax,-.9,28.1)
    dim(ax,0,SITE[0],30.3,"15200 示意面宽")
    dim(ax,-8,SITE[1],16,"37400 含门前空地示意总深",True)
    dim(ax,-8,0,-1,"8000 前场暂定",True)
    dim(ax,24.4,29.4,13,"5000 用户给定后方净空",True)
    for a,b in zip(BAYS[:-1],BAYS[1:]):dim(ax,a,b,25.1)
    for a,b in ((.6,6.6),(6.6,14.4),(14.4,24.4)):dim(ax,a,b,15,vertical=True)
    scale_bar(ax,y=-9.4)


def forecourt_plan(ax):
    a,b,c,d=FORECOURT['bounds'];rect(ax,a,b,c-a,d-b,'#eeeee5',LINE,.6)
    x1,y1,x2,y2=FORECOURT['entry_path'];rect(ax,x1,y1,x2-x1,y2-y1,'#dddcca','none',0)
    a,b,c,d=STORAGE['bounds'];rect(ax,a,b,c-a,d-b,'#e5dfd0',MUTED,.6)
    plan_walls(ax,'storage')
    txt(ax,(a+c)/2,(b+d)/2,'一层杂物屋\n3600×7400 暂定',6.4,GREEN,ha='center')
    txt(ax,2.5,-4,'门前开敞空地\n深8m暂定',7,GREEN,ha='center')


def plan_walls(ax,group):
    for wall in walls(group):
        x,y = wall["a"]; bx,by=wall["b"]
        horizontal=y==by
        length=abs(bx-x)+abs(by-y);t=wall["thickness"]
        start=0
        for op in wall["openings"]+[dict(offset=length,width=0,kind="end")]:
            stop=op["offset"]
            if stop>start:
                rect(ax,x+start if horizontal else x-t/2,y-t/2 if horizontal else y+start,
                     stop-start if horizontal else t,t if horizontal else stop-start,INK,INK,.2)
            if op["kind"]=="window":
                for d in (-t/2,0,t/2):
                    if horizontal:line(ax,[x+stop,x+stop+op["width"]],[y+d,y+d],GREEN,.6)
                    else:line(ax,[x+d,x+d],[y+stop,y+stop+op["width"]],GREEN,.6)
            elif op.get('operation')=='sliding':
                width=op['width']
                if horizontal:
                    line(ax,[x+stop,x+stop+width],[y-.04,y-.04],GREEN,1.2)
                    line(ax,[x+stop+width/2,x+stop+width],[y+.04,y+.04],GREEN,1.2)
                    ax.annotate('',xy=(x+stop+width*.80,y+.16),xytext=(x+stop+width*.25,y+.16),arrowprops=dict(arrowstyle='->',lw=.5,color=GREEN))
                else:
                    line(ax,[x-.04,x-.04],[y+stop,y+stop+width],GREEN,1.2)
            elif op["kind"]=="door":
                width=op["width"];sw=op["swing"]
                if width>1.5:
                    width/=2
                if horizontal:
                    hinge=(x+stop,y)
                    line(ax,[hinge[0],hinge[0]],[y,y+sw*width],MUTED,.6)
                    ax.add_patch(Arc(hinge,2*width,2*width,theta1=0 if sw>0 else 270,
                                     theta2=90 if sw>0 else 360,color=MUTED,lw=.5))
                    if op["width"]>1.5:
                        hx=x+stop+op["width"]
                        line(ax,[hx,hx],[y,y+sw*width],MUTED,.6)
                        ax.add_patch(Arc((hx,y),2*width,2*width,theta1=90 if sw>0 else 180,
                                         theta2=180 if sw>0 else 270,color=MUTED,lw=.5))
                else:
                    hinge=(x,y+stop+width if op.get('hinge_end') else y+stop)
                    line(ax,[x,x+sw*width],[hinge[1],hinge[1]],MUTED,.6)
                    theta1,theta2=((270,360) if sw>0 else (180,270)) if op.get('hinge_end') else ((0,90) if sw>0 else (90,180))
                    ax.add_patch(Arc(hinge,2*width,2*width,theta1=theta1,
                                     theta2=theta2,color=MUTED,lw=.5))
            start=stop+op["width"]


def stair(ax,upper=False):
    x1,y1,x2,y2=STAIR["bounds"]
    low_y,high_y=STAIR["flight_bounds"]
    width=STAIR["width"]
    rect(ax,x1,y1,x2-x1,y2-y1,COLORS["stair"],MUTED,.6)
    for center in (12.225,13.575):
        left=center-width/2
        rect(ax,left,low_y,width,high_y-low_y,ec=MUTED,lw=.6)
        for i in range(1,9):line(ax,[left,left+width],[low_y+i*STAIR["tread"]]*2,MUTED,.5)
    for key in ("mid_landing","top_landing"):
        lx1,ly1,lx2,ly2=STAIR[key]
        rect(ax,lx1,ly1,lx2-lx1,ly2-ly1,ec=MUTED,lw=.6)
    for x,ya,yb in ((13.575,low_y+.2,high_y+.45),(12.225,high_y+.45,low_y+.2)):
        ax.annotate("",xy=(x,yb),xytext=(x,ya),arrowprops=dict(arrowstyle="->",lw=.7,color=GREEN))
    line(ax,[12.225,13.575],[high_y+.45]*2,GREEN,.6)
    plan_walls(ax,"stair2" if upper else "stair1")
    txt(ax,12.9,(low_y+high_y)/2,"20级 · 上",6,ha="center",rotation=90,bbox=dict(fc="#fffefa",ec="none",pad=.6))
    txt(ax,12.87,17.05,"二层顶平台" if upper else "首层入口平台",5.9,GREEN,ha="center")


def furniture(ax,group,labels=False):
    if group=='rear2':
        a,b,c,d=UPPER_LAUNDRY['bounds'];rect(ax,a,b,c-a,d-b,'#bed1d1',GREEN,.7)
        txt(ax,(a+c)/2,(b+d)/2,'洗烘',4.8,ha='center')
    palette={"shower":"#b5d4cf","vanity":"#dde9de","wc":"#f8fbf7",
             "bed":"#fdfbf3","hob":"#495c56","sink":"#bed1d1","fridge":"#c1c9c3"}
    for obj in furnishings()[group]:
        x1,y1,x2,y2=obj["bounds"];kind=obj["kind"]
        if kind=='roundtable':
            ax.add_patch(Circle(((x1+x2)/2,(y1+y2)/2),(x2-x1)/2,fc='#ceb28d',ec=MUTED,lw=.55))
        else:rect(ax,x1,y1,x2-x1,y2-y1,palette.get(kind,"#ceb28d"),MUTED,.55)
        if kind=="bed":
            if obj["rotation"]%180==90:
                rect(ax,x2-.40 if obj["rotation"]==270 else x1+.12,y1+.12,.28,y2-y1-.24,"#e8ddc6",MUTED,.35)
            else:
                for dx in (.08,(x2-x1)/2+.04):
                    rect(ax,x1+dx,y2-.4,(x2-x1)/2-.12,.28,"#e8ddc6",MUTED,.35)
        if kind=="wc":
            ax.add_patch(Circle(((x1+x2)/2,(y1+y2)/2),min(x2-x1,y2-y1)*.3,fc="white",ec=MUTED,lw=.5))
        if kind=="chair":
            back_y=y1+.04 if obj.get('rotation')==180 else y2-.04
            line(ax,[x1+.03,x2-.03],[back_y,back_y],INK,1.1)
        if kind=='wardrobe' and obj.get('front')=='south':
            line(ax,[x1+.04,x2-.04],[y1+.025,y1+.025],INK,1.1)
        if kind=="shower":line(ax,[x1,x2],[y1,y1],GREEN,1.2)
        if kind=="hob":
            for cy in (((y1+y2)/2,) if obj.get('burners')==1 else (y1+.17,y2-.17)):ax.add_patch(Circle(((x1+x2)/2,cy),.09,ec="white",fc="none",lw=.5))
        if labels and kind not in ("chair","cabinet","nightstand"):
            label=obj['name'].split(' / ')[0]
            for suffix in ('（示意）','预留600','预留','操作位'):label=label.replace(suffix,'')
            txt(ax,(x1+x2)/2,(y1+y2)/2,label,4.8 if kind in ('griddle','ricecooker','hob','microwave','dishwasher') else 6,
                color='white' if kind=='hob' else INK,ha='center',
                rotation=90 if y2-y1>1.4*(x2-x1) else 0,
                bbox=dict(fc=palette.get(kind,"#ceb28d"),ec="none",pad=.5))
    if group!="front":stair(ax,group=="rear2")


def decoration_plan(ax,group):
    for obj in decoration()[group]:
        x1,y1,x2,y2=obj["bounds"]
        _,color,hatch=DECORATION_STYLES[obj["kind"]]
        if obj['kind']=='cove' and obj.get('north_gap'):
            line(ax,[x1,x1,x2,x2],[y2,y1,y1,y2],color,.8)
            line(ax,[x1,obj['north_gap'][0]],[y2,y2],color,.8)
            line(ax,[obj['north_gap'][1],x2],[y2,y2],color,.8)
        else:
            rect(ax,x1,y1,x2-x1,y2-y1,"none",color,.8,hatch=hatch)


def floor_plan(ax,group,decorate=False):
    bounds=FRONT if group=="front" else REAR
    if group=="rear1":
        rect(ax,.6,14.4,10.8,1.2,"#e4e4d9",MUTED,.6)
        txt(ax,6,14.95,"门廊 1200",6.5,MUTED,ha="center")
    # The later passage fill cuts the L-shaped bedroom out without a seam at its open study.
    for name,(x1,y1,x2,y2),kind in ROOMS[group]:
        rect(ax,x1,y1,x2-x1,y2-y1,COLORS[kind],"none",0)
    furniture(ax,group)
    if decorate:decoration_plan(ax,group)
    plan_walls(ax,group)
    if group=='rear1':plan_walls(ax,'entry')
    if group=='rear2':
        ex1,ey1,ex2,ey2=COVERED_ENTRY['roof_bounds']
        rect(ax,ex1,ey1,ex2-ex1,ey2-ey1,'#e3dfcf',MUTED,.6)
        txt(ax,12.87,15.45,'门厅顶面\n非上人',5.3,MUTED,ha='center')
    if group!="front":
        for x in (.72,4.2,7.8,11.28):rect(ax,x-.1,16.04,.2,.2,INK,INK,.4)
    for name,(x1,y1,x2,y2),kind in ROOMS[group]:
        if kind=="stair":continue
        x,y=(x1+x2)/2,(y1+y2)/2
        if y2-y1>4:
            y=5.6 if group=="front" and x>7 else (2.1 if group=="front" else 16.72)
        if name in ("堂屋","家庭厅"):y=17.55
        if name=="公共过厅":y=15.62
        box=dict(fc=COLORS[kind],ec="none",pad=.9)
        if group=="rear1" and name=="家务 / 公卫前室":
            txt(ax,x,22.56,"家务 / 公卫\n前室",5.4,ha="center",bbox=box)
            txt(ax,x,21.90,"1500×3000",5.1,MUTED,ha="center",bbox=box)
            continue
        if group=="rear2" and name=="次卧":
            txt(ax,9.4,18.83,"L形次卧 · 双人床1800",6,ha="center",bbox=box)
            continue
        if name=="侧门入户过道":
            txt(ax,10.55,17.22,"独立入户过道",5.8,ha="center",rotation=90,bbox=box)
            continue
        if name=="卧室书桌区":y=22.2
        txt(ax,x,y,name,6.8,ha="center",bbox=box)
        txt(ax,x,y-.42,f"{(x2-x1)*1000:.0f}×{(y2-y1)*1000:.0f}",5.6,MUTED,ha="center",bbox=box)
    if group=="front":rect(ax,4.6,0,2.8,.6,ec=MUTED,lw=.5)


def roof_plan(ax,bounds,front=False):
    if front:
        x1,y1,x2,y2=bounds
        rect(ax,x1,y1,x2-x1,y2-y1,"#e3dfcf",GREEN,.9)
        line(ax,[x1+.1,x1+.1,x2-.1,x2-.1],[y2-.1,y1+.1,y1+.1,y2-.1],MUTED,.6)
        line(ax,[1.84,10.16],[y2-.1,y2-.1],MUTED,.6)
        txt(ax,5,3.9,"前房平屋顶露台",7.5,ha="center")
        txt(ax,5,3.25,"+3.600 / 无琉璃瓦",6.5,MUTED,ha="center")
        for bx1,by1,bx2,by2 in BRIDGES:
            rect(ax,bx1,by1,bx2-bx1,by2-by1,"#dfd4b9",GREEN,.7)
            txt(ax,(bx1+bx2)/2,10.5,"连廊 1200",5.5,GREEN,ha="center",rotation=90)
        a,b,c,d=TERRACE_PAVILION['roof_bounds'];rect(ax,a,b,c-a,d-b,'#d3dbce',GREEN,.7,linestyle='--')
        txt(ax,3.15,3.3,'电动升降晾衣',6,GREEN,ha='center')
        a,b,c,d=TERRACE_LAUNDRY['bounds'];rect(ax,a,b,c-a,d-b,'#ceb28d',GREEN,.6)
        txt(ax,3.15,5.25,'水池收纳',5.3,ha='center')
        return
    x1,y1,x2,y2=bounds;cy=(y1+y2)/2
    rect(ax,x1-.45,y1-.45,x2-x1+.9,y2-y1+.9,"#ecd1c5",GREEN,.8)
    for x in [x1-.45+i*.26 for i in range(46)]:
        if x<x2+.45:line(ax,[x,x],[y1-.45,y2+.45],"#be836a",.25)
    for y in [y1-.45+i*.4 for i in range(26)]:
        if y<y2+.45:line(ax,[x1-.45,x2+.45],[y,y],"#c78e78",.25)
    line(ax,[x1-.48,x2+.48],[cy,cy],GREEN,1.3)
    for end in (y1+.5,y2-.5):
        ax.annotate("",xy=(6,end),xytext=(6,cy+(.3 if end>cy else -.3)),
                    arrowprops=dict(arrowstyle="->",lw=.8,color=GREEN))
    txt(ax,6,cy+.5,"东西向屋脊",7,ha="center",bbox=dict(fc="#ecd1c5",ec="none",pad=1))
    txt(ax,6,cy-.6,"+5.100" if front else "+10.200",7,ha="center",bbox=dict(fc="#ecd1c5",ec="none",pad=1))


def bullets(page,x,y,title,items,width=200):
    txt(page,x,y,title,12,GREEN)
    y-=11
    for item in items:
        for part in item.split("\n"):
            txt(page,x,y,part,8.4,MUTED);y-=6.4
        y-=4
    return y


def save(fig,name):
    PAGES.append(fig)
    fig.savefig(ROOT/"drawings"/(name+".svg"),facecolor=fig.get_facecolor())
    fig.savefig(ROOT/"drawings"/(name+".png"),dpi=120,facecolor=fig.get_facecolor())


LAYOUT=engineering_layout(ROOMS,furnishings())
HVAC=hvac_layout()

def main_plan(fig,groups=("front","rear1"),roof=False):
    ax=axes(fig,(18,29,149,222),(-1.8,17.2,-10,31.4));yard(ax);forecourt_plan(ax)
    if roof:
        roof_plan(ax,FRONT,True)
        cx1,cy1,cx2,cy2=EAST_CANOPY['bounds']
        rect(ax,cx1,cy1,cx2-cx1,cy2-cy1,'#e8e6d9',GREEN,.8)
        txt(ax,10.8,10.5,'二层东侧雨廊顶棚',5.5,GREEN,ha='center',rotation=90)
        roof_plan(ax,REAR)
        x1,y1,x2,y2=STAIR["bounds"]
        rect(ax,x1,y1,x2-x1,y2-y1,"#e3dfcf",GREEN,.8)
        txt(ax,(x1+x2)/2,(y1+y2)/2,"封闭侧梯顶盖\n+6.900",5.8,GREEN,ha="center")
        x1,y1,x2,y2=COVERED_ENTRY['roof_bounds']
        rect(ax,x1,y1,x2-x1,y2-y1,'#e3dfcf',GREEN,.8)
        txt(ax,(x1+x2)/2,(y1+y2)/2,'避雨门厅顶盖\n+3.600',5.3,GREEN,ha='center')
    else:
        for group in groups:floor_plan(ax,group)
    site_outline(ax)
    return ax

fig,p=sheet("A-000","双侧连廊 · 院居精装 O版","居住通路与收纳复核 / 圆桌暖灯 / 北区休闲与书桌 / 13张同模型精装图")
hero=ROOT/"renders"/"01-aerial.png"
if hero.exists():
    ax=fig.add_axes([19/420,59/297,266/420,185/297]);ax.imshow(Image.open(hero));ax.axis("off")
bullets(p,301,230,"后楼",["三开间两层 + 半层隔热阁楼。","右后侧封闭梯；二层经独立过道入户。","老人房2人、主卧2人、次卧2人。"])
bullets(p,301,168,"前房与院子",["平屋顶露台，无琉璃瓦。","左卧室、中央通堂、右中西厨。","东西两侧连廊，院内无树。"])
bullets(p,301,105,"布局与装修",["前屋两门改入通堂，北侧旧门改窗。","暖白木色精装，灯槽、格栅和双层帘实体。","39页图册含水电、衣柜及选材图文。"])
txt(p,25,42,"15.20 × 37.40 m（含暂定前场）",18,GREEN)
txt(p,200,42,"面宽暂定；后方净空5m为用户给定，非完整实测地块。",8,MUTED)
save(fig,"00-overview")

fig,p=sheet("A-001","总平面与后方设备预留区","南入北居，前后两栋位置保留；封闭梯移至右后侧，后墙至边界5米。")
a=main_plan(fig,roof=True)
x1,y1,x2,y2=LAYOUT["septic"]["bounds"]
rect(a,x1,y1,x2-x1,y2-y1,"#e7d7c4",MUTED,.7)
txt(a,9.8,27.1,"化粪池示意",6,ha="center")
txt(a,4,26,"空调设备区",6,ha="center")
bullets(p,188,234,"建筑与通行",["两栋均宽10.80m，每开间3.60m。","前房深6.00m、院子深7.80m、后楼深10.00m。","双侧连廊各名义宽1.20m，与过厅及露台同标高。","封闭侧梯沿用；南侧增2.94×2.10m避雨门厅。"])
bullets(p,188,166,"后方5米",["后墙Y24.40至后边界Y29.40，共5.00m。","化粪池在屋后东侧，空调外机在西侧设备架。","排污、雨水、空调冷凝水分别示意。","检查井、检修清掏及设备维护路径需现场确认。"])
bullets(p,188,98,"面积口径",["两栋常规层投影合计280.80m²，含门廊与过厅。","双连廊投影18.72m²；梯间每层约15.82m²，另记。","避雨门厅投影约6.17m²；露台和阁楼亦另记。","本表不是净使用面积、报建面积或法定计容面积。"])
save(fig,"01-site-plan")

fig,p=sheet("A-101","首层平面 · 堂屋北段圆桌客厅","按最新标注：西侧起居室、东侧老人卧室；公卫改在西北，堂屋北段圆桌客厅。")
a=main_plan(fig)
bullets(p,188,235,"首层动线",["南入口 → 通堂 → 院子 → 门廊 → 堂屋。","堂屋名义3.60×8.80m，参考净尺寸约3.36×8.32m。","堂屋北段圆桌；原900mm敞口封闭，公卫经起居室到达。","西公卫南门封闭；东侧老人套卫从卧室进入。"])
d=axes(fig,(194,65,101,126),(11.02,14.72,16.07,22.27));stair(d)
dim(d,11.4,14.34,16.18,"2940 外包")
bullets(p,309,178,"封闭双跑楼梯",["20级×165 = 3300mm。","9踏面×270 = 2430mm。","梯段宽1050mm。","北中间平台深1050mm。","南端平台净深1420mm。","周边外墙＋顶盖封闭。"])
txt(p,191,49,"房内尺寸为名义分区，墙体暂240mm；楼梯、栏杆和结构构件待施工设计。",8,MUTED)
save(fig,"02-ground-floor")

fig,p=sheet("A-102","后楼二层与右后侧梯","南端顶平台 → 东侧主门 → 独立入户过道 → 公共过厅；次卧一张1.8m双人床，采用L形分隔。")
a=axes(fig,(22,55,215,190),(0,14.7,13.5,26.2));floor_plan(a,"rear2")
dim(a,.6,11.4,25.2,"10800")
for lo,hi in zip(BAYS[:-1],BAYS[1:]):dim(a,lo,hi,24.7)
bullets(p,250,230,"六人常住分配",["一层老人房：2.2m双人床，2人。","二层主卧：2.2m双人床，2人。","二层次卧：1.8m双人床，2人。","前房左客房：1.8m双人床，备用。"])
bullets(p,250,158,"布局与家具",["侧主门Y17.00～18.10，经独立过道向南入过厅。","后楼加深1m，次卧床尾950mm、南侧830mm。","家庭厅西沙发、东电视，东北端高柜、2.25m书桌。","南侧入户及主卧门区保持无家具，详见I-105。"])
txt(p,40,46,"侧梯遮挡原东窗；北书桌外窗与卧室敞开相连，实际采光通风须专项校核。",8,MUTED)
save(fig,"03-upper-floor")

fig,p=sheet("A-103","红瓦隔热阁楼与平屋顶","仅后楼设红色琉璃瓦坡屋面；前房为上人平露台，双侧连廊贯通。")
a=main_plan(fig,roof=True)
bullets(p,187,234,"后楼半层",["二层顶板控制面+6.900。","阁楼墙顶+8.000，红瓦屋脊+10.200。","墙边约1.10m高、脊部约3.30m高。","东西山墙百叶通风；仅隔热检修，不作常住卧室。"])
d=axes(fig,(198,83,190,83),(0,12,0,5.25))
d.add_patch(Polygon([(1,.55),(1,1.65),(6,4.1),(11,1.65),(11,.55)],fc="#f0dfca",ec=INK,lw=.5))
line(d,[.6,6,11.4],[1.45,4.1,1.45],"#a94b36",4)
rect(d,1,.35,10,.2,"#89948b",INK,.7)
txt(d,6,1.8,"通风隔热阁楼",10,ha="center");txt(d,6,4.6,"红色琉璃瓦",9,ha="center")
txt(p,190,60,"瓦层、防水、保温、屋架及楼板均需施工设计；本图只表达空间层次。",8,MUTED)
save(fig,"04-roof-plan")

fig,p=sheet("A-201","南北向剖面与楼层标高","中央堂屋无楼梯；封闭侧梯位置与踏步见首层平面及I-103放大图。")
a=axes(fig,(25,70,275,149),(-1,30,-.8,12))
line(a,[-.3,29.4],[0,0],MUTED,.7)
for lo,hi in ((.6,6.6),(14.4,24.4)):rect(a,lo,.12,hi-lo,.18,"#bfc1b6",INK,.6)
rect(a,.6,3.42,6,.18,"#bfc1b6",INK,.6)
for z in (3.42,6.72):rect(a,14.4,z,10,.18,"#bfc1b6",INK,.6)
for y in (.72,6.48,15.72):rect(a,y-.12,2.7,.24,.72,"#d1d2c9",INK,.7)
rect(a,14.4,3.6,.24,.85,"#d1d2c9",INK,.7)
rect(a,14.4,6.05,.24,.67,"#d1d2c9",INK,.7)
line(a,[14.52,14.52],[4.45,6.05],GREEN,.5)
for z in (.3,3.6):
    rect(a,24.16,z,.24,.85,"#d1d2c9",INK,.7);rect(a,24.16,z+2.45,.24,.67,"#d1d2c9",INK,.7)
    line(a,[24.28,24.28],[z+.85,z+2.45],GREEN,.5)
a.add_patch(Polygon([(14.4,6.9),(14.4,8),(19.4,10.2),(24.4,8),(24.4,6.9)],fc="#f3e4d0",ec=INK,lw=.6))
line(a,[13.95,19.4,24.85],[7.78,10.2,7.78],"#aa4b35",2.6)
line(a,[6.6,14.4],[3.6,3.6],GREEN,.8,linestyle="--")
txt(a,10.5,3.96,"双侧连廊投影",7,ha="center")
for x,y,label in ((3.6,1.6,"前房"),(10.5,.8,"院子"),(19.4,1.7,"堂屋完整空间"),(19.4,5,"家庭厅"),(19.4,7.7,"隔热阁楼"),(27,1,"屋后5米")):
    txt(a,x,y,label,8,ha="center")
for z in (.3,3.6,6.9,8,10.2):txt(a,25,z,f"+{z:.3f}",7,MUTED)
for lo,hi in ((.6,6.6),(6.6,14.4),(14.4,24.4),(24.4,29.4)):dim(a,lo,hi,-.45)
bullets(p,315,224,"封闭侧梯",["首层+0.300。","北中间平台+1.950。","南顶平台+3.600。","每跑10个踢面。","侧梯由外墙、顶盖封闭。","侧门接独立入户过道。"])
bullets(p,28,48,"深化边界",["钢筋混凝土框架方案；截面、配筋、基础、上人露台、连廊及封闭侧梯均未结构验算。"])
save(fig,"05-longitudinal-section")

fig,p=sheet("A-301","朝院立面与前房平露台立面","首层堂屋正门、二层朝院中央窗及两端小门保留；右后侧梯南墙在本立面中投影表达。")
def facade(ax,rear):
    top=8 if rear else 3.6
    rect(ax,.6,.3,10.8,top-.3,"#e6e1d6",INK,.7)
    for x in (1.4,8.55):rect(ax,x,.3+.85,2.05,1.6,"#afc1bd",INK,.6)
    rect(ax,5.1,.3,1.8,2.4,"#a08260",INK,.6)
    if rear:
        for op in walls("rear2")[0]["openings"]:
            rect(ax,.72+op["offset"],3.6+op["sill"],op["width"],op["height"],
                 "#a08260" if op["kind"]=="door" else "#afc1bd",INK,.6)
    if rear:
        rect(ax,.15,7.78,11.7,2.42,"#b8664b",INK,.7)
        for x in [i*.21+.15 for i in range(56)]:line(ax,[x,x],[7.78,10.2],"#93412c",.35)
        rect(ax,.6,3.42,10.8,.18,"#adb2a4",INK,.5)
        for x in (.72,4.2,7.8,11.28):rect(ax,x-.07,.3,.14,3.1,"#8d7455",INK,.4)
        rect(ax,11.4,.3,2.94,6.6,"#dddcd0",INK,.7)
        for group,base in (("stair1",.3),("stair2",3.6)):
            for op in walls(group)[0]["openings"]:
                rect(ax,11.52+op["offset"],base+op["sill"],op["width"],op["height"],
                     "#a08260" if op["kind"]=="door" else "#afc1bd",INK,.6)
        rect(ax,11.4,6.72,2.94,.18,"#adb2a4",INK,.6)
        rect(ax,11.4,.3,2.94,3.12,'#dddcd0',INK,.7)
        for op in walls('entry')[0]['openings']:
            rect(ax,11.52+op['offset'],.3+op['sill'],op['width'],op['height'],'#afc1bd',INK,.6)
        rect(ax,11.4,3.42,2.94,.18,'#adb2a4',INK,.6)
    else:
        rect(ax,.6,3.42,10.8,.18,"#adb2a4",INK,.5);line(ax,[.6,11.4],[4.7,4.7],INK,.8)
    line(ax,[0,14.6],[0,0],MUTED,.7)
    dim(ax,.6,11.4,-.5,"10800")
a=axes(fig,(28,85,204,162),(-.2,14.6,-1,11));facade(a,True)
b=axes(fig,(249,126,153,90),(-.2,12,-1,5.8));facade(b,False)
txt(p,44,72,"后楼朝院立面（避雨门厅前墙与二层南墙平齐）",9,GREEN)
txt(p,265,110,"前房南立面：平屋顶无瓦",9,GREEN)
txt(p,36,43,"栏杆约1100mm；图示分格与构件只作外观示意，防护、结构和防水节点待施工设计。",8,MUTED)
save(fig,"06-elevations")

fig,p=sheet("I-101","右侧纯厨房与家电操作区","取消厨房餐位；洗碗机靠水槽，北小家电台，独立上排烟道。")
a=axes(fig,(35,47,136,199),(7.5,11.7,.3,6.9));floor_plan(a,"front");furniture(a,"front",True)
dim(a,7.92,9.17,5.55,"1250 通道")
bullets(p,202,232,"中厨＋西厨",["东侧及南侧L形地柜，设两只独立猛火灶、共用集烟罩和备餐位。","西侧西厨台：咖啡机、嵌入式烤箱；冰箱移东侧北段。","中西厨操作面间约2020mm。","取消厨房用餐，北侧电器台，洗碗机靠近水槽。","厨房内门沿用，洗碗机开启后仍保留操作通路。"])
bullets(p,202,154,"水电与空调",["厨房设备电源、冷热水和排水见工程分层图。","厨房排水向东外绕楼梯范围，再向北汇入检查井。","隔油、清扫、设备散热与烟道按型号深化。","厨房暂不设空调内机，独立排烟立管见K-102。"])
bullets(p,202,82,"材料意向",["浅木柜体、浅色石英石台面、耐擦洗背板及哑光地砖。","柜下与小家电台面灯，电器按产品留散热。"])
save(fig,"07-kitchen-interior")

fig,p=sheet("I-102","卫生间干湿分区与排水接口","西湿区上下对应，东套卫移至梯间北侧；污水、通气、冷水和热水位置另在工程图中标识。")
a=axes(fig,(36,61,121,177),(.45,3.35,20.4,25));floor_plan(a,"rear1")
for artist in list(a.texts):artist.remove()
furniture(a,"rear1",True)
dim(a,.84,2.58,24.55,"1740 净宽");dim(a,21.52,24.16,2.9,"2640 净深",True)
bullets(p,189,232,"布置",["后部淋浴区1620×900，移门玻璃分隔。","西公卫沿用；新东套卫在梯间北侧上下叠合。","两层东套卫西门接私用区，不通楼梯。","家务前室名义1500mm宽；洗衣机及储物柜集中北墙。"])
bullets(p,189,153,"排污与防水",["西湿区保留，东套卫上下叠合，立管沿侧后设备带布置。","污废水汇入屋后检查井，再进三格化粪池。","雨水及空调冷凝水不接化粪池。","地漏、防水、存水弯、通气、坡度和管径均待深化。"])
bullets(p,189,81,"使用条件",["堂屋旧北段门洞封闭；公卫经西起居室北门进入。","老人套卫补扶手、座凳、镜灯；无障碍及通风仍待核验。"])
save(fig,"08-bathroom-interior")

fig,p=sheet("I-103","1.8米次卧与右后侧梯","后楼加深1m，改为一张1.8m双人床，独立入户过道与完整卫浴保留。")
a=axes(fig,(27,70,150,173),(7.55,11.65,15.8,24.65));floor_plan(a,"rear2")
dim(a,7.92,9.68,15.93,"1760");dim(a,9.92,11.16,15.93,"1240过道")
b=axes(fig,(202,75,119,166),(11.02,14.8,16.02,22.32));stair(b,True);plan_walls(b,"rear2")
dim(b,11.4,14.34,16.18,"2940");dim(b,16.5,21.88,14.59,"5380",True)
bullets(p,331,228,"楼梯控制",["外墙＋顶盖封闭。","20×165=3300。","每跑9踏面×270。","梯段宽1050。","北中间平台1050。","南端平台净深1420。","侧主门北铰向梯间开。"])
txt(p,35,61,"次卧床垫1800、床架包络2150×1940；西侧床尾950、南侧830mm通路。",8,MUTED)
txt(p,35,51,"次卧床头朝东；衣帽书桌区及套卫北移1m，仍从私用区进入，不穿公共过道。",8,MUTED)
txt(p,35,38,"侧梯遮东窗，北书桌外窗加宽；卧室实际采光通风、梯间防火及平台结构均待专项设计。",8,MUTED)
save(fig,"09-bedroom-stair-interior")

fig,p=sheet("I-104","地面材料与圆桌客厅","院内去掉树及树池，保留铺装与可移动休闲家具。")
a=main_plan(fig)
y=231
for kind,(name,color) in FINISHES.items():
    rect(p,190,y-3,12,6,color,LINE,.5);txt(p,209,y,name,10,GREEN);y-=22
bullets(p,190,104,"装修协调",["卧室浅橡木、厅区暖灰、卫浴灰绿防滑砖。","堂屋北段圆桌，南侧活动通行保留。","木饰板、窗帘、灯具及收纳详见I-106装修专页。","红色琉璃瓦只用于后楼；前房为平露台。"])
save(fig,"10-finishes")

fig,p=sheet("A-104","双侧连廊与右侧封闭侧梯","左右两条名义1200mm连廊，由公共过厅两端小门通往前房露台。")
a=main_plan(fig,groups=("rear2",));roof_plan(a,FRONT,True)
for x in (.65,1.75,10.25,11.35):line(a,[x,x],[6.6,14.35],GREEN,1)
for x in (1.2,10.8):
    a.annotate("",xy=(x,7.1),xytext=(x,13.8),arrowprops=dict(arrowstyle="<->",color="#a67532",lw=1.2))
bullets(p,188,233,"连接关系",["侧主门 → 独立入户过道 → 公共过厅。","过厅接家庭厅；两端900mm小门接连廊与露台。","门洞与连廊端部对齐，通口不设横向栏杆。","过厅、露台、连廊完成面统一为+3.600。"])
bullets(p,188,157,"尺寸",["连廊名义1200mm，栏杆内净宽暂约1030mm。","桥下净高暂约3420mm；支撑位置避开院子中轴。","两侧廊下排水、防滑和夜间照明需施工深化。"])
bullets(p,188,90,"承重与使用",["连廊及封闭侧梯承重位置见结构层，截面配筋未设计。","不得在梁柱上随意穿电管、水管、空调冷媒管。","两侧临界、露台荷载及栏杆节点需现场专业设计。"])
save(fig,"11-terrace-connection")

append_engineering_sheets(sheet,axes,rect,line,txt,save,site_outline,floor_plan,LAYOUT)

fig,p=sheet("H-101","空调室内外机与管路位置","紫红：冷媒管 / 绿色：冷凝水 / 编号与模型一致；选型、散热净距及支架待设备设计。")
a=main_plan(fig)
for unit in HVAC["units"]:
    x,y,z=unit["indoor"];ox,oy,oz=unit["outdoor"]
    color="#a83d91" if unit["floor"]!="rear2" else "#7249af"
    for points,c in ((unit["refrigerant"],color),(unit["condensate"],"#389557")):
        line(a,[p[0] for p in points],[p[1] for p in points],c,.7,linestyle="--" if unit["floor"]=="rear2" else "-")
    rect(a,x-.12,y-.4,.24,.8,"white",color,.8)
    rect(a,ox-.45,oy-.19,.9,.38,"#d0d7cb",color,.7)
    txt(a,x+.2,y,unit["id"],5.7,color)
bullets(p,188,233,"设备位置",["AC-1：前房左客房，外机侧墙预留。","AC-2：西起居室；AC-3：东老人房；外机屋后西侧。","AC-4/5/6：主卧、次卧、家庭厅；外机屋后设备架。","屋后外机与化粪池分区，须保证检修及通气协调。"])
bullets(p,188,157,"管线与排水",["冷媒沿侧墙设备带接外机，避免穿梁柱。","冷凝水分别收集到南侧/后侧待定接点。","不接化粪池、不滴落到院子、走廊和楼梯。","空调专用电源点见电气层，保护和负荷待校核。"])
bullets(p,188,87,"深化条件",["设备架仅示意，机型、容量、噪声、风向、减振、","支架固定、防雨和检修净距须按厂家及现场条件设计。","西侧客房外机距邻界较近，必须核对可安装和散热条件。"])
save(fig,"17-hvac-layout")

fig,p=sheet("A-105","右后侧梯与侧门入户通道","南端顶平台 → 东侧主门 → 独立入户过道 → 公共过厅 → 家庭厅 / 双连廊；主通行不穿卧室。")
route_color="#ad6d2d"
a=axes(fig,(18,40,151,204),(-.1,14.8,-.1,25.3))
yard(a);floor_plan(a,"rear2");roof_plan(a,FRONT,True)
for x in (1.33,10.67):
    line(a,[6,x,x],[15.35,15.35,4.9],route_color,1.2)
    a.annotate("",xy=(x,7.7),xytext=(x,10.5),arrowprops=dict(arrowstyle="->",lw=1.2,color=route_color))
line(a,[12.225,10.55,10.55,6,6],[17.5,17.5,15.35,15.35,16.8],route_color,1.2)
txt(p,23,246,"二层完整连接 / +3.600",9,GREEN)
txt(p,22,32,"两端小门分别连通西廊、东廊；前露台汇合。",7.8,MUTED)

b=axes(fig,(179,112,221,132),(.3,14.75,13.4,24.75));floor_plan(b,"rear2")
for artist in list(b.texts):
    if artist.get_text():artist.remove()
for x in (1.33,10.67):
    line(b,[x,x],[13.0,14.4],GREEN,.9)
    line(b,[6,x,x],[15.35,15.35,13.65],route_color,1.4)
    b.annotate("",xy=(x,13.55),xytext=(x,14.35),arrowprops=dict(arrowstyle="->",lw=1.4,color=route_color))
b.annotate("",xy=(6,16.95),xytext=(6,15.35),arrowprops=dict(arrowstyle="->",lw=1.4,color=route_color))
b.annotate("",xy=(10.55,17.5),xytext=(12.225,17.5),arrowprops=dict(arrowstyle="->",lw=1.4,color=route_color))
line(b,[10.55,10.55,6],[17.5,15.35,15.35],route_color,1.4)
b.annotate("",xy=(10.55,16.4),xytext=(10.55,17.05),arrowprops=dict(arrowstyle="->",lw=1.4,color=route_color))
for x,label in ((2.4,"主卧"),(6,"家庭厅")):
    txt(b,x,17.65,label,7.8,GREEN,ha="center")
txt(b,9.4,18.83,"L形次卧 · 1800床",6.8,GREEN,ha="center")
txt(b,8.55,22.08,"敞开书桌区",6.2,GREEN,ha="center")
txt(b,10.28,16.8,"入户过道",5.8,GREEN,ha="center",rotation=90)
txt(b,6,16.63,"中央敞开连接",6.2,MUTED,ha="center",bbox=dict(fc="#fffefa",ec="none",pad=.3))
txt(b,6,15.82,"公共过厅",7.5,GREEN,ha="center")
txt(b,12.5,16.15,"侧主门 1100 / Y17.00～18.10",5.8,GREEN,ha="center")
line(b,[11.75,11.4],[16.35,17.2],GREEN,.6)
for x,label in ((1.33,"西小门 900"),(10.67,"东小门 900")):
    txt(b,x,13.7,label,6.4,GREEN,ha="center")
txt(b,12.88,17.05,"南顶平台 +3.600",5.7,GREEN,ha="center")
txt(b,12.9,19.4,"封闭侧梯",6.1,GREEN,ha="center",rotation=90,
    bbox=dict(fc=COLORS["stair"],ec="none",pad=.3))
txt(b,12.9,21.35,"北中间平台 +1.950",5.6,GREEN,ha="center")
txt(p,184,246,"入口放大 / 门洞与开放接口",9,GREEN)
bullets(p,183,99,"本版设计选择与通行关系",[
    "① 南顶平台经1100mm侧门入过道，北铰门扇向梯间开。",
    "② 过道向南接公共过厅，北门进次卧；一张1.8m双人床。",
    "③ 过厅中央接家庭厅，两端900mm小门接1200mm连廊。",
    "④ 北书桌区与卧室敞开，侧门进套卫；正面中央窗保留。",
])
txt(p,183,39,"侧梯遮东窗；北外窗采光联系及通风、防火、结构待专项校核。",7.3,MUTED)
save(fig,"18-entry-circulation")

fig,p=sheet("I-105","居住布局优化 · 公卫与家具通路","堂屋北门封闭；公卫经西起居室到前室，圆桌在堂屋北段。")
a=axes(fig,(18,126,204,116),(.35,8.05,16.60,24.65));floor_plan(a,"rear1")
for artist in list(a.texts):artist.remove()
points=((5.0,17.5),(3.30,17.5),(3.30,20.1),(3.6,20.1),(3.6,22.4),(2.35,22.4))
line(a,[q[0] for q in points],[q[1] for q in points],route_color,1.3)
a.annotate('',xy=points[-1],xytext=points[-2],arrowprops=dict(arrowstyle='->',color=route_color,lw=1.3))
txt(a,6.0,23.75,'堂屋圆桌区',8,GREEN,ha='center')
txt(a,3.44,24.42,'北墙洗衣 / 窗下柜',6.5,GREEN,ha='center')
txt(a,4.46,22.55,'本轮封闭',6.2,GREEN,ha='center',rotation=90)
txt(p,21,246,'01  封门后：经起居室到西公卫',9,GREEN)
bullets(p,20,115,'新公卫路线',[
    '堂屋 → 起居室南门 → 北门 → 家务前室 → 公卫。',
    '堂屋北段西墙不再开门；茶几缩窄，保留通行路线。',
    '圆桌与六椅放堂屋北段，南侧卧室入门空间保留。',
    '东侧套卫迁梯间北侧，原湿区归入卧室私用区。',
])
b=axes(fig,(238,102,79,138),(4.0,8.0,16.0,24.65));floor_plan(b,"rear2")
b.annotate("",xy=(6.65,21.55),xytext=(6.65,17.0),
           arrowprops=dict(arrowstyle="->",color=route_color,lw=1.2))
txt(p,238,246,"02  家庭厅",9,GREEN)
txt(p,238,95,"北墙双人书桌 / 西侧沙发",7.3,MUTED)
txt(p,238,87,"东侧电视 / 高柜移至东北端",7.3,MUTED)
txt(p,238,79,"南段入户与主卧门区保持空出",7.3,MUTED)
txt(p,238,71,"沙发前500 / 对电视柜段东侧1100",7.3,MUTED)
c=axes(fig,(330,116,72,124),(.5,4.3,.5,6.85));floor_plan(c,"front")
c.annotate("",xy=(2.75,4.0),xytext=(2.75,6.1),
           arrowprops=dict(arrowstyle="->",color=route_color,lw=1.2))
dim(c,.98,3.13,1.18,"2150 床架",size=5.8)
txt(p,330,246,"03  前客房",9,GREEN)
txt(p,330,105,"床头朝西 / 1.80m备用床",7.1,MUTED)
txt(p,330,97,"北侧衣柜与入户通路保留",7.1,MUTED)
txt(p,238,56,"茶几、座椅及床架按实际占地表达。",7.5,MUTED)
txt(p,238,48,"移动家具与装修意向见I-106及3D家具层。",7.5,MUTED)
txt(p,20,33,"箭头仅示意日常通行；净宽、门框、设备检修及适老化条件仍需结合现场与产品复核。",7.8,MUTED)
save(fig,"19-layout-optimization")

fig,p=sheet("I-106","装修设计 · 材料、收纳与灯光","米白、暖灰与木色沿用原风格；装饰图形按类别表示，与3D同步平面投影、安装高度和材质意向。")
for box,group,title,caption in (
    ((18,152,118,87),"front","01  前客房 / 厨餐","西床头板、南窗帘 / 厨餐背板、吊柜及吊灯"),
    ((145,147,124,93),"rear1","02  后楼首层","起居背景、地毯 / 老人卫浴扶手及淋浴座凳"),
    ((278,147,124,93),"rear2","03  后楼二层","高柜北移、双人学习 / 次卧上掀床箱"),
):
    limits=(.45,11.65,.45,6.8) if group=="front" else (.45,11.65,15.45,24.65)
    a=axes(fig,box,limits);floor_plan(a,group,decorate=True)
    txt(p,box[0]+2,246,title,9,GREEN)
    txt(p,box[0]+2,138,caption,6.6,MUTED)
txt(p,20,119,"装修物件图例 / 按实际平面投影示意",10,GREEN)
for i,(_, (label,color,hatch)) in enumerate(DECORATION_STYLES.items()):
    x=20+(i//8)*101;y=105-(i%8)*9.2
    rect(p,x,y-2.5,10,5,"none",color,.8,hatch=hatch)
    txt(p,x+14,y,label,7.5,MUTED)
txt(p,234,119,"材料意向",10,GREEN)
for i,(label,color) in enumerate((("米白墙面","#eeeae0"),("浅橡木","#d6ba91"),
                                 ("浅石英石","#e4e0d5"),("灰绿防滑砖","#91aaa2"),("暖色金属","#b48736"))):
    x=234+i*33
    rect(p,x,99,27,10,color,LINE,.5)
    txt(p,x+13.5,94,label,6.8,MUTED,ha="center")
bullets(p,234,81,"装修安排",[
    "老人房／主卧用2.2m床；次卧／前客房用1.8m床。",
    "窗帘分列两侧，不跨门洞；厨房操作区不放地毯。",
    "厨餐柜下灯、餐桌吊灯；卫浴镜灯、壁龛及适老细节。",
])
txt(p,20,33,"灯具高度、表面材质、柜体、扶手和座凳均为装修意向；未完成照度、产品安装与施工节点验算。",7.8,MUTED)
save(fig,"20-decoration-design")

fig,p=sheet('A-106','红框区域避雨门厅 · 门廊到楼梯','新增一层有顶、有侧墙和采光窗的入口；仅表达空间与排水方向，结构和防水构造待深化。')
a=axes(fig,(20,80,185,165),(10.1,14.85,13.8,18.4));floor_plan(a,'rear1')
for artist in list(a.texts):artist.remove()
ex1,ey1,ex2,ey2=COVERED_ENTRY['roof_bounds']
rect(a,ex1,ey1,ex2-ex1,ey2-ey1,'none',GREEN,.8,linestyle='--')
route=[(10.4,15.09),(12.5,15.09),(13.35,15.65),(13.35,17.2)]
line(a,[q[0] for q in route],[q[1] for q in route],GREEN,1.4)
a.annotate('',xy=route[-1],xytext=route[-2],arrowprops=dict(arrowstyle='->',color=GREEN,lw=1.4))
txt(a,12.8,15.7,'避雨门厅',7,GREEN,ha='center')
txt(a,10.8,15.65,'有顶门廊',6,GREEN,ha='center')
txt(a,13.84,15.45,'换鞋凳',5.4,MUTED,ha='center',rotation=90)
txt(a,12.05,17.35,'原梯间',6,GREEN,ha='center')
dim(a,11.4,14.34,14.03,'2940 外包')
dim(a,14.4,16.5,14.65,'2100',True)
txt(p,23,252,'01  西门入厅，北门上楼 / 虚线为连续顶盖',8,GREEN)
b=axes(fig,(230,147,165,96),(13.8,18.55,-.15,4.4))
rect(b,14.4,.12,3.76,.18,'#c4c5bb',INK,.6)
rect(b,14.4,3.42,2.34,.18,'#c4c5bb',INK,.6)
rect(b,16.74,3.42,1.42,.18,'#c4c5bb',INK,.6)
rect(b,14.4,.3,.24,.85,'#dddcd0',INK,.6)
rect(b,14.4,2.75,.24,.67,'#dddcd0',INK,.6)
line(b,[14.52,14.52],[1.15,2.75],GREEN,1)
rect(b,16.5,2.7,.24,.72,'#dddcd0',INK,.6)
line(b,[13.9,18.4],[0,0],MUTED,.6)
txt(b,15.4,1.3,'门厅 +0.300',7,GREEN,ha='center')
txt(b,17.3,1.0,'原首层平台',6,MUTED,ha='center')
txt(b,15.7,3.9,'新顶盖接原平台板边 +3.600',6,GREEN,ha='center')
txt(p,232,252,'02  南北剖面 / 西侧入门位于剖面外',8,GREEN)
bullets(p,232,130,'避雨与使用',[
    '从有顶门廊侧门进厅，再入原封闭梯；不穿堂屋或卧室。',
    '西门900mm，原梯门1100mm，均为名义洞口尺寸。',
    '室内平接，不保留原梯门前的150mm露天踏步。',
    '南、东侧窗采光；东窗下换鞋凳，通行留在西侧。',
    '屋面单独收集雨水；新增屋面不作为上人露台。',
    '找坡、泛水、门窗接缝、基础及结构须现场深化。',
])
txt(p,24,55,'新增封闭投影约6.17m²，另记；面宽及退界仍待实测。外侧管线已避开门厅投影。',8,MUTED)
txt(p,24,38,'本页落实用户红框区域的空间遮雨安排；不表示防水等级、节点、荷载或施工条件已验算。',8,MUTED)
save(fig,'21-rain-entry')

fig,p=sheet('A-107','二层东侧连廊连续加顶','用户补充确认二层东侧连廊加顶；保留西侧连廊与开敞庭院，新增浅色轻型顶棚和独立收水。')
a=axes(fig,(20,67,165,177),(9.65,12.05,5.8,15.1))
rect(a,10.2,6.6,1.2,7.8,'#dfd4b9',GREEN,.7)
cx1,cy1,cx2,cy2=EAST_CANOPY['bounds']
rect(a,cx1,cy1,cx2-cx1,cy2-cy1,'none',GREEN,1,linestyle='--')
line(a,[10.25,10.25],[6.6,14.35],MUTED,.7)
line(a,[11.35,11.35],[6.6,14.35],MUTED,.7)
for x in EAST_CANOPY['post_x']:
    for y in EAST_CANOPY['post_y']:rect(a,x-.03,y-.03,.06,.06,INK,INK,.3)
line(a,[10.8,10.8],[6.85,14.15],GREEN,1.2)
a.annotate('',xy=(10.8,14.15),xytext=(10.8,13.4),arrowprops=dict(arrowstyle='->',color=GREEN,lw=1.2))
txt(a,10.8,6.1,'前房露台',7,GREEN,ha='center')
txt(a,10.8,14.86,'后楼二层小门',7,GREEN,ha='center')
txt(a,10.78,10.45,'东侧连廊 / 整段有顶',6.2,GREEN,ha='center',rotation=90)
dim(a,10.1,11.5,6.32,'1400 顶棚',size=5.8)
dim(a,6.4,14.64,11.82,'8240 顶棚',True,size=5.8)
txt(p,24,251,'01  连廊平面 / 虚线为顶棚外轮廓',8,GREEN)
b=axes(fig,(215,156,181,83),(5.9,15.1,3.1,7.3))
rect(b,6.6,3.42,7.8,.18,'#c4c5bb',INK,.6)
rect(b,6.4,6.52,8.24,.06,'#e8e6d9',GREEN,.7)
rect(b,6.4,6.40,8.24,.12,'#b8bdb4',INK,.5)
for y in EAST_CANOPY['post_y']:rect(b,y-.03,3.6,.06,2.8,'#9ea69d',INK,.4)
rect(b,14.4,6.0,.24,.72,'#dddcd0',INK,.6)
txt(b,10.5,6.92,'轻型顶棚控制面 +6.600',7,GREEN,ha='center')
txt(b,10.5,4.95,'示意最小梁下净高约2.78m',7,MUTED,ha='center')
txt(b,10.5,3.14,'连廊与前露台、二层同为 +3.600',6.5,GREEN,ha='center')
txt(p,218,251,'02  纵向示意 / 立柱沿原栏杆线设置',8,GREEN)
bullets(p,218,132,'遮雨安排',[
    '仅二层东侧连廊新增顶棚，西侧连廊维持原样。',
    '前露台端略出挑，北端搭接后楼小门上方。',
    '浅色轻型板面、细框架；柱不比原扶手更占通路。',
    '屋面向东收水，雨水管接独立雨水干管。',
    '不向连廊、楼梯口或院内通行面直接滴水。',
    '图示构件粗细不是施工截面，连接与抗风需深化。',
])
txt(p,23,51,'屋面横向高差40mm为模型排水方向意向；搭接、泛水、管径、固定、防水及侧向飘雨条件需现场深化。',7.6,MUTED)
txt(p,23,35,'整屋显示顶棚；首层及二层布局自动隐藏高处顶棚以看清通路，可用“查看东侧雨廊”直接查看。',7.6,MUTED)
save(fig,'22-east-covered-bridge')

fig,p=sheet('I-107','前屋内门与精装风格','按用户红框设通堂两侧内门；六张参考图转化为暖白、木色、浅石、米色织物及简化新中式细部。')
a=axes(fig,(20,150,179,91),(.3,11.7,.3,6.9));floor_plan(a,'front',decorate=True)
for x in (4.2,7.8):
    a.annotate('新内门',xy=(x,5.05),xytext=(x+(-1.2 if x<6 else 1.2),6.72),ha='center',fontsize=6,color=GREEN,
               arrowprops=dict(arrowstyle='->',color=GREEN,lw=.7))
txt(p,22,249,'01  客房／厨餐由通堂进入，旧朝院门改窗',8,GREEN)
bullets(p,22,133,'门位与精装安排',[
    '客房X4.20、厨餐X7.80内隔墙，门洞Y4.55～5.55。',
    '客房木门向西开，厨餐细框玻璃门向东开。',
    '通堂鞋柜南移，2.40m南北贯通通口保留。',
    '木纹／石纹／织物嵌入离线模型，不依赖网络贴图。',
    '首层西起居、东卧室；堂屋保留完整活动地面。',
    '灯槽、格栅、帘片、柜面及软装为3D实体。',
])
txt(p,22,56,'暖白 / 原木与胡桃木 / 浅米灰石材 / 米色织物 / 暖光',8,GREEN)
for i,color in enumerate(('#eeeae0','#bb9874','#6c5137','#d5d1c4','#c8baa5','#d3af73')):
    rect(p,22+i*28,40,22,10,color,LINE,.5)
txt(p,219,249,'02  用户提供的风格参考（不是本项目渲染成品）',8,GREEN)
references=sorted((ROOT/'装修图片及风格').iterdir())
for i,path in enumerate(references):
    xx=219+(i%2)*93;yy=195-(i//2)*61
    ax=fig.add_axes([xx/420,yy/297,88/420,49/297]);ax.imshow(Image.open(path));ax.axis('off')
    txt(p,xx+44,yy-4,f'参考 {i+1}',6.3,MUTED,ha='center')
txt(p,23,32,'精装效果图保存在本地“精装效果图”目录；图片由同一源模型渲染，灯光色差、材料和安装仍需按实际产品深化。',7.4,MUTED)
save(fig,'23-finished-style')

fig,p=sheet('K-101','套卫外移与圆桌客厅','东侧两层套卫移至梯间北侧；原湿区还给套房，封闭堂屋北段西门洞。')
for box,group,title in (((18,104,184,136),'rear1','首层：圆桌餐叙与老人套房'),((216,104,184,136),'rear2','二层：独立入户与套卫')):
    a=axes(fig,box,(.3,14.6,15.3,24.7));floor_plan(a,group)
    txt(p,box[0]+3,246,title,9,GREEN)
    a.annotate('',xy=(12.8,23),xytext=(10.2,23),arrowprops=dict(arrowstyle='->',color=GREEN,lw=1.2))
    a.annotate('独立墙排',xy=(14.3,22.65),xytext=(13.3,21.55),fontsize=6,color=GREEN,arrowprops=dict(arrowstyle='->',color=GREEN,lw=.7))
bullets(p,20,88,'空间与门位',[
    '新增东套卫各约2.94×2.52m，参考净空约2.70×2.28m。',
    '两层原约6.30m²名义湿区各并回北侧衣帽／书桌休闲区。',
    '套卫仅从私用区西门进入，不通梯间，梯间原北窗封闭。',
])
bullets(p,216,88,'客厅与公卫',[
    '堂屋北段1.20m圆桌、六椅，兼用餐会客，南段保留活动。',
    '堂屋北段西门洞封闭；西公卫经起居室和家务前室到达。',
    '前屋厚重中式现代双开大门；后排一楼堂屋用玻璃门。',
])
save(fig,'24-suite-and-gathering')

fig,p=sheet('K-102','娱乐晾晒露台与厨房独立排烟','前屋屋顶西侧亭内电动晾衣、水池，东侧旧架取消；厨房不设餐位，设备、工作台及排烟统一协调。')
a=axes(fig,(18,101,181,137),(.3,12.3,.3,7.0));roof_plan(a,FRONT,True)
for bounds,label,color in ((TERRACE_DRYING['bounds'],'电动升降晾衣',GREEN),(TERRACE_LAYOUT['central_clear_bounds'],'活动／通行','#889c97')):
    x1,y1,x2,y2=bounds;rect(a,x1,y1,x2-x1,y2-y1,'none',color,1,linestyle='--');txt(a,(x1+x2)/2,(y1+y2)/2,label,7,color,ha='center')
txt(a,11.8,1.6,'↑ 排烟立管',6.2,GREEN,ha='center')
b=axes(fig,(216,101,179,137),(7.5,12.3,.3,6.9));floor_plan(b,'front');furniture(b,'front',True)
txt(p,21,246,'01  亭内电动晾衣 · 右侧旧架取消 · 中间通行',9,GREEN)
txt(p,219,246,'02  中西厨房：家电与操作区',9,GREEN)
bullets(p,20,87,'厨房与排烟',[
    '撤餐桌卡座；洗碗机靠水槽，北侧微波炉台、南侧电饼铛／电饭煲位。',
    '预留微波炉、电饼铛、电饭煲、冰箱、烤箱和咖啡机。',
    '烟机上接东墙外独立立管，示意出口+6.10m。',
])
bullets(p,216,87,'露台及院墙',[
    '电动晾衣杆可升起，右侧旧架取消，保留中部及连廊通路。',
    '侧院墙接前后屋，东侧接门厅，避免堵避雨入口。',
    '排烟管径／静压、固定、排放口、屋面荷载和防水待深化。',
])
save(fig,'25-terrace-and-exhaust')

fig,p=sheet('L-101','门前开敞空地与右前方一层杂物屋','O版按蓝框扩展整块杂物屋，暂3.6×7.4米；实际位置和地界待测。')
a=axes(fig,(18,55,240,188),(-.4,16,-8.8,2.0));forecourt_plan(a);floor_plan(a,'front')
dim(a,11.0,14.6,-7.85,'3600 杂物屋暂定')
dim(a,-7.4,0,10.55,'7400 暂定',True)
dim(a,-8,0,15,'8000 门前空地暂定',True)
a.annotate('',xy=(6,.3),xytext=(6,-7.5),arrowprops=dict(arrowstyle='->',color=GREEN,lw=1.2))
txt(a,6,-4.0,'入户通道',7,GREEN,ha='center',rotation=90)
bullets(p,275,229,'位置与使用',[
    '杂物屋按最新箭头移到大门右前方。',
    '杂物屋一层平顶，西门朝空地，南侧高窗。',
    '杂物屋延至前场北边线，北／东货架同步延长。',
    '大门正前方直达通道，其余前场保持开敞。',
])
bullets(p,275,137,'尺寸口径',[
    '主屋及后院原示意深29.4m不变。',
    '门前另加8m，合计示意深37.4m。',
    '杂物屋投影约26.64m²，非实测／报建面积。',
    '地界、采光、防火、排水和结构待现场深化。',
])
txt(p,20,34,'门前空地与杂物屋为本轮暂定示意，不据此确认宅基地权属、法定面积或道路位置。',7.7,MUTED)
save(fig,'26-forecourt-storage')

fig,p=sheet('M-101','居住动作与精装复核','保留已确认建筑格局；次卧床位与独立收纳、老人北区和主卧窗前柜体协调。')
for box,group,title in (((18,108,182,132),'rear1','01  老人窗边休闲／圆桌餐叙'),((216,108,182,132),'rear2','02  次卧收纳／主卧窗前让位')):
    a=axes(fig,box,(.4,14.6,15.5,24.7));floor_plan(a,group,decorate=True)
    txt(p,box[0]+2,246,title,9,GREEN)
    if group=='rear2':
        a.annotate('',xy=(8.4,21.6),xytext=(8.4,18.8),arrowprops=dict(arrowstyle='->',color=GREEN,lw=1.2))
        a.annotate('',xy=(11.05,22.4),xytext=(9.2,22.4),arrowprops=dict(arrowstyle='->',color=GREEN,lw=1.2))
bullets(p,20,91,'实际布局改善',[
    '次卧床北移200mm：南侧630→830mm，西侧950mm沿用。',
    '西侧独立滑门衣柜，1500mm窗下书桌东移，保持套卫路线。',
    '老人北区单椅＋矮柜，衣柜和中部路线不压门扇。',
    '主卧衣柜北端退至Y23.10，北窗前留约1060mm。',
])
bullets(p,216,91,'装修与成品',[
    '圆桌上方木框暖灯，软垫椅及餐具；北区补阅读灯和帘片。',
    '洗碗机上方连续台面，柜身让出机器位，不以实心柜包住。',
    '全套13张高清图从O完整模型输出，含门前杂物屋环境。',
    '效果灯光非日照／照度计算，实际产品与施工仍须核验。',
])
save(fig,'27-layout-finish-review')

fig,p=sheet('N-101','整块杂物屋与两侧院墙封闭','杂物屋向北扩至前场边线，两侧院墙补高至连廊板底；其余主屋布局沿用。')
a=axes(fig,(18,103,176,137),(9.9,15.1,-7.9,1.0));forecourt_plan(a)
dim(a,11,14.6,-7.75,'3600');dim(a,-7.4,0,14.92,'7400',True)
txt(p,20,246,'01  右前方整块杂物屋',9,GREEN)
b=axes(fig,(214,108,184,132),(5.8,16.3,-.2,4.3))
rect(b,6.48,0,15.72-6.48,COURTYARD_WALL_TOPS[0],'#e2dfd4',INK,.8)
rect(b,6.6,3.42,7.8,.18,'#aaa99f',INK,.6)
line(b,[6.48,15.72],[2,2],MUTED,.7,linestyle='--')
txt(b,11,1.05,'新增上段连同原墙形成整面实墙',7,GREEN,ha='center')
txt(b,11,2.70,'原上方缺口封闭',7.5,GREEN,ha='center')
txt(b,10.5,3.83,'二层连廊板底 +3.420',7,GREEN,ha='center')
dim(b,0,3.42,16,'3420 墙顶标高',True)
txt(p,216,246,'02  西侧院墙示意立面',9,GREEN)
bullets(p,20,85,'杂物屋',[
    '名义3.60×7.40m，单层平顶+3.300，西门朝空地。',
    '原北侧露天空地并入屋内，墙、地坪、货架、屋顶同步。',
    '北侧距前屋南墙600mm，实际退距及构造需现场核验。',
])
bullets(p,216,85,'院墙',[
    '东西墙均补到+3.420板底，不留上部通透缺口。',
    '移除原中部压顶，勒脚外凸20mm，东侧门厅入口保留。',
    '3D整屋显示实墙；调低墙体后仍可看院内布局。',
])
save(fig,'28-storage-and-wall-enclosure')

fig,p=sheet('O-101','洗衣、梳妆与双灶家电布局','东西院墙封闭 / 老人床与梳妆台换位 / 56处门窗支持开关')
a=axes(fig,(20,130,115,110),(.6,2.9,6.6,9.3))
rect(a,.6,6.6,.18,2.7,INK)
for key,color in [('bounds','#ceb28d'),('sink','#c1d8d4')]:
    x1,y1,x2,y2=COURTYARD_LAUNDRY[key];rect(a,x1,y1,x2-x1,y2-y1,color,MUTED,.6)
for machine in COURTYARD_LAUNDRY['machines']:
    if machine['kind']=='dryer':continue
    x1,y1,x2,y2=machine['bounds'];rect(a,x1,y1,x2-x1,y2-y1,'#f9f7f2',MUTED,.6)
rect(a,1.50,6.72,1.20,2.03,'none',GREEN,.6,linestyle='--')
rect(a,1.11,8.91,.18,.18,INK)
txt(a,1.17,7.09,'洗＋烘叠放',6,ha='center',rotation=90);txt(a,1.17,8.40,'洗衣池',6,ha='center',rotation=90)
txt(a,2.12,7.85,'1200 操作区',6,ha='center',rotation=90)
dim(a,6.72,8.75,2.82,'2030 总长',True)
txt(a,1.17,7.74,'分区洗衣',5.5,ha='center',rotation=90)
txt(p,20,246,'01 西连廊下洗衣区',9,GREEN)
b=axes(fig,(145,130,115,110),(7.7,11.45,16.5,22.8));furniture(b,'rear1')
for f in furnishings()['rear1']:
    if f['kind']=='bed' and f['room']==5 or f.get('dressing'):
        x1,y1,x2,y2=f['bounds'];txt(b,(x1+x2)/2,(y1+y2)/2,'2200床' if f['kind']=='bed' else '梳妆台',6,ha='center')
txt(p,145,246,'02 老人床北、梳妆台南',9,GREEN)
c=axes(fig,(278,130,119,110),(7.7,11.45,.6,6.6));furniture(c,'front',True)
txt(p,278,246,'03 双猛火灶与家电标签',9,GREEN)
bullets(p,20,109,'洗衣区',[
    '总长2030、深660；主洗＋烘干叠放，另加分区洗衣机。',
    '水池与吊柜集中；北距柱160，前方1200示意操作区。',
    '北侧两柱间增升降晾衣架；洗衣废水与院内雨水分流。',
])
bullets(p,20,65,'卧室',[
    '老人床Y19.10～21.44，梳妆台Y17.10～18.20。',
    '主卧西墙北段设1000长梳妆台；均配镜灯和台下凳。',
])
bullets(p,217,109,'开关与厨房',[
    '门窗侧栏单项开关／全部开关；也可点模型门窗操作。',
    '后楼首层朝院双轨玻璃门横拉，双扇叠合开启。',
    '厨房电器标签仅厨房视角显示，两个猛火灶分别编号。',
    '两个灶位共用集烟罩连独立排烟；燃气／排风按型号深化。',
    '东西院墙补到+3.420；墙脚饰面错面，去除共面暗纹。',
])
save(fig,'29-operable-openings-laundry-dressing')

fig,p=sheet('O-102','二楼亭子与两层洗衣晾晒','亭子为暂定尺寸意向；亭内电动晾衣，右侧旧架取消，水电与屋面节点另行深化。')
a=axes(fig,(20,115,185,125),(.4,11.7,.4,6.8));roof_plan(a,FRONT,True)
for text in list(a.texts):
    if text.get_text() in ('前房平屋顶露台','+3.600 / 无琉璃瓦'):text.remove()
for x,y in TERRACE_PAVILION['posts']:rect(a,x-.05,y-.05,.1,.1,INK)
for m in TERRACE_LAUNDRY['machines']:
    x1,y1,x2,y2=m['bounds'];rect(a,x1,y1,x2-x1,y2-y1,'#f8f7f0',MUTED,.6)
x1,y1,x2,y2=TERRACE_LAUNDRY['sink'];rect(a,x1,y1,x2-x1,y2-y1,'#c1d8d4',MUTED,.6)
x1,y1,x2,y2=TERRACE_DRYING['bounds'];rect(a,x1,y1,x2-x1,y2-y1,'none',GREEN,.8)
txt(a,8.7,3.7,'旧晾衣架取消\n保持开敞',6,GREEN,ha='center')
dim(a,1.70,4.60,1.08,'2900 亭顶示意');dim(a,1.35,5.85,4.77,'4500',True)
txt(p,20,246,'01 二楼露台平面',9,GREEN)
b=axes(fig,(222,115,177,125),(6.35,12.2,-.1,3.8))
rect(b,6.6,3.42,5.4,.18,'#d3dbce',MUTED,.6)
for y in (9,12):rect(b,y-.09,0,.18,3.42,'#8b6a45',MUTED,.5)
for m in COURTYARD_LAUNDRY['machines']:
    _,y1,_,y2=m['bounds'];rect(b,y1,m['z'],y2-y1,m['height'],'#f8f7f0',MUTED,.6)
    b.add_patch(Circle(((y1+y2)/2,m['z']+m['height']*.48),.17,fc='#677675',ec=MUTED,lw=.5))
rect(b,8.08,.05,.67,.59,'#ceb28d',MUTED,.5);line(b,[7.43,8.75],[.92,.92],GREEN,1)
rect(b,7.43,1.61,1.32,.62,'#ceb28d',MUTED,.5)
line(b,[9.55,11.35],[2.10,2.10],GREEN,1.2)
for y in (9.65,11.25):line(b,[y,y],[2.10,3.27],MUTED,.6)
txt(b,10.45,1.65,'升降晾衣',7,GREEN,ha='center')
txt(p,222,246,'02 首层三台洗烘及晾衣',9,GREEN)
bullets(p,20,103,'二楼',[
    '亭顶2.90×4.50m，四柱，木色梁底与深色薄檐。',
    '亭内电动升降晾衣，杆高2250／1250mm；桌椅取消。',
    '右侧旧晾衣架取消，中央X4.8～7.0m通路留空。',
    '亭子雨水独立汇集；洗衣机／池／地漏接污废水。',
])
bullets(p,222,103,'首层与实施条件',[
    '老人可在首层洗衣和晾晒，两层设备各有使用位置。',
    '机器、堆叠支架、检修和实际开门范围按选型核实。',
    '亭子柱脚、屋面荷载、防水、抗风和排水须专业深化。',
    '本图表达布置和功能，不能用作设备安装或结构施工图。',
])
save(fig,'30-pavilion-laundry-drying')

fig,p=sheet('P-101','二楼过厅洗衣机与水电深化','按用户蓝框移位；保留1000mm通行／操作带，设备及专业安装条件待核。')
ax=axes(fig,(20,118,137,123),(2.55,4.45,14.35,17.1))
plan_walls(ax,'rear2');furniture(ax,'rear2')
a,b,c,d=UPPER_LAUNDRY['work_area'];rect(ax,a,b,c-a,d-b,'#e4eee0',GREEN,.7,linestyle='--')
txt(ax,3.68,15.12,'1000\n操作通行带',6.5,GREEN,ha='center')
for key,color,label in [('socket','#e59928','电源'),('valve','#2e86de','水阀'),('drain','#8a5b37','地漏')]:
    x,y,_=UPPER_LAUNDRY[key];ax.plot(x,y,'o',color=color,ms=4);txt(ax,x+(.10 if key=='socket' else -.10),y+.13,label,5.5,color,ha='left' if key=='socket' else 'right')
dim(ax,14.64,15.64,3.16,'1000',True)
txt(p,20,246,'01 机位与通道（局部平面）',9,GREEN)
bullets(p,170,237,'布置与检修',[
    '720宽×780深凹位；机器暂按600宽×650深，朝南开门。',
    '北墙局部后退330mm，主卧南窗由2050收至1800mm。',
    '保留原床、主卧门和东侧家庭厅通行；开机门与走人分时。',
    '上方台面、可拆检修板，左右分别设水阀和防溅插座。',
    '水阀1120、插座1300、排水口650mm，均按本层完成面。',
    '地面防水连续上翻，抗振垫；实际机型与检修净距待核。',
])
bullets(p,170,161,'全屋水电修正',[
    'DB0前屋、DB1后楼首层、DB2二楼；洗烘机专用DB2-W1。',
    '厨房高负荷设备、洗烘机与空调分设专线预留。',
    '入口照明开关补齐；插座避衣柜、电器中心、门洞和窗。',
    '四卫补淋浴和干区地漏，室内排水转板下可检修路径。',
    '洗衣专用立管设清扫与通气，接西污废水井；雨污分开。',
])
bullets(p,20,96,'回路与施工前核对',[
    f'共{len(LAYOUT["circuits"])}个回路分组；详表见model/design.json及docs/laundry-and-services.md。',
    '插座／设备按30mA剩余电流保护设计意向；PE保护导体连续。',
    '管径、线径、断路器、电源容量、排水坡度与荷载均待实际选型校核。',
    '1.5%仅为本次排水空间预留；不得据模型开孔、凿梁或直接施工。',
])
save(fig,'31-upper-laundry-services')

fig,p=sheet('P-102','三卧室五列衣柜','老人房、主卧、次卧均为五列／五扇门；内部可展示，平开与通行分时。')
ax=axes(fig,(20,99,205,145),(-.18,2.18,-.40,2.55))
rect(ax,0,0,2,2.4,'#e3ceb3',GREEN,1)
for i in range(1,5):line(ax,[i*.4,i*.4],[.12,2.08],GREEN,.7)
line(ax,[0,2],[2.08,2.08],GREEN,.8)
for i in range(5):
    txt(ax,.2+i*.4,2.24,'被褥',6.5,ha='center')
    txt(ax,.2+i*.4,2.47,str(i+1),7.5,GREEN,ha='center')
line(ax,[.04,.36],[1.55,1.55],INK,1.3)
for z in (.95,1.82):line(ax,[.44,.76],[z,z],INK,1.3)
for z in (.23,.43,.63):rect(ax,.82,z-.09,.36,.18,'#c09b70',MUTED,.5)
for z in (.75,1.16,1.58):line(ax,[.8,1.2],[z,z],GREEN,.7)
for z in (.47,.87,1.27,1.67):line(ax,[1.2,1.6],[z,z],GREEN,.7)
for z in (.75,1.40):line(ax,[1.6,2],[z,z],GREEN,.7)
for x,label in [(.2,'长衣'),(.6,'双层短衣'),(1.,'抽屉叠放'),(1.4,'活动层板'),(1.8,'被褥杂物')]:txt(ax,x,.10,label,5.5,ha='center')
dim(ax,0,2,-.27,'2000')
bullets(p,246,234,'三套规格',[
    '均为2000宽×550深×2400高mm，五列约400mm。',
    '南到北五列分区，暖木色柜门、细金属拉手。',
    '老人房长衣杆1550，主卧1850，次卧1750mm。',
    '柜门单扇平开约400mm，可逐扇点击，也可五扇全开。',
    '内部展示暂时隐藏门，查看挂衣、层板及抽屉结构。',
])
bullets(p,246,153,'布局协调',[
    '三套位于原各卧室私用衣帽／书桌区，柜体加长至2m。',
    '北窗横向让位，避免高柜遮窗；窗帘随窗洞同步调整。',
    '老人床北至柜南端约640mm，检查600mm人体转弯。',
    '主卧衣帽插座移到可达实墙，避新柜体。',
    '门打开时占操作通道，使用后关闭，实际五金待选型。',
])
txt(p,20,64,'立面以老人房1550mm长衣杆示意；其余两套杆高按右侧表述，柱宽及实际板厚随定制深化。',8,MUTED)
save(fig,'32-five-column-wardrobes')

append_material_sheets(sheet, rect, txt, save)
assert len(PAGES)==33+len(MATERIAL_PAGES)+2, "Drawing set must include advice and two material image sheets"

with PdfPages(ROOT/"drawings"/"农村院落住宅-水电深化P.pdf") as pdf:
    pdf.infodict()["Title"]="农村前后院住宅 · 精装方案 P 水电深化与装修选材建议"
    pdf.infodict()["Subject"]="Revision P; operable wardrobes, laundry and motorized drying; material advice appendix; concept design, product selection pending"
    for figure in PAGES:pdf.savefig(figure,facecolor=figure.get_facecolor())
for figure in PAGES:plt.close(figure)
print(f"Created {len(PAGES)} A3 PDF pages, SVG sheets and PNG previews.")
