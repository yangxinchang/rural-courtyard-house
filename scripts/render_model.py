"""Run with Blender 4.2+: blender -b --python scripts/render_model.py.

The generated model is a concept model. Timber and masonry sizes are visual
placeholders, not structural specifications.
"""
import sys
from pathlib import Path
import math
import random
import json
import runpy
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design import ROOT, SITE, SITE_BOUNDS, FORECOURT, STORAGE, FRONT, REAR, BRIDGES, STAIR, COVERED_ENTRY, EAST_CANOPY, EAST_SUITE, COURTYARD_WALLS, COURTYARD_WALL_TOPS, COURTYARD_LAUNDRY, TERRACE_PAVILION, TERRACE_LAUNDRY, UPPER_LAUNDRY, TERRACE_DRYING, KITCHEN_EXHAUST, TERRACE_LAYOUT, LEVELS, walls, ROOMS, furnishings, decoration, room_specs
from engineering import engineering_layout
from hvac import hvac_layout

# Refresh shared browser data before replacing any model artifacts.
runpy.run_path(str(ROOT / "scripts" / "design.py"), run_name="__main__")
random.seed(42)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for old in list(bpy.data.collections):
    if old.name != "Collection":
        bpy.data.collections.remove(old)
COLS = {}
for key in ["Site", "Front", "Rear1", "Rear2", "Attic", "Roofs", "Terrace", "Stairs", "StairShell1", "StairShell2", "StairRoof", "EntryRoof", "BridgeCanopy", "Garden", "Outbuilding", "OutbuildingRoof", "Pavilion", "PavilionRoof", "Structure", "Electrical", "Plumbing", "HVAC", "Lights"]:
    col = bpy.data.collections.new(key)
    bpy.context.scene.collection.children.link(col)
    COLS[key] = col
CURRENT = "Site"


def move(obj, name, mat=None):
    obj.name = name
    obj["floorGroup"] = CURRENT
    obj["sectionable"] = name.startswith(("Wall", "Opening", "Glazing", "Window", "Open timber door", "Open glazed door", "Porch timber", "Attic knee wall", "Attic side knee wall"))
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    COLS[CURRENT].objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def material(name, color, roughness=0.6, metallic=0.0, noise=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if noise:
        tex = mat.node_tree.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = 75
        bump = mat.node_tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = noise
        bump.inputs["Distance"].default_value = 0.03
        mat.node_tree.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        mat.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def textured_material(name,filename,color,roughness=.65):
    mat=material(name,color,roughness)
    texture=mat.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image=bpy.data.images.load(str(ROOT/'assets/finishes'/filename),check_existing=True)
    texture.image.pack()
    mat.node_tree.links.new(texture.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    return mat


PLASTER = material("Warm lime plaster", (.815, .79, .735), .84, noise=.13)
STONE = material("Charcoal stone plinth", (.17, .19, .18), .82, noise=.2)
WOOD = textured_material("Warm oak doors and furniture",'warm-oak.png',(.40,.25,.12),.48)
PALEWOOD = textured_material("Pale ash interior joinery",'warm-oak.png',(.62,.52,.40),.52)
LIGHTFLOOR = textured_material("Pale limestone bedroom floor",'warm-stone.png',(.82,.80,.755),.52)
LIGHTROOF = material("Pale stone coated metal roof",(.80,.775,.715),.44,.05,noise=.05)
PAVILIONPOST = material("Warm grey bronze pavilion post",(.62,.565,.475),.34,.4)
DARKWOOD = material("Medium walnut frames", (.235, .175, .115), .44)
FLOOR = textured_material("Warm stone floor",'warm-stone.png',(.65,.62,.55),.65)
PAVE = [material("Courtyard stone %s" % i, (.43 + i*.025, .46+i*.022, .43+i*.02), .82, noise=.2) for i in range(4)]
ROOFMATS = [material("Glazed celadon tile %s" % i, (.30+i*.018, .045+i*.006, .025+i*.004), .24, .1) for i in range(6)]
GLASS = material("Blue grey glazing", (.55, .68, .68), .15, .1)
FABRIC = textured_material("Linen",'linen.png',(.65,.57,.45),.95)
BEDDING = material("Cotton", (.81, .77, .69), .94)
WATER = material("Sanitary porcelain", (.83, .85, .81), .25)
DOORMETAL=material('Charcoal glazed door frame',(.045,.047,.043),.35,.6)
GATEBRONZE=material('Gate bronze accents',(.32,.22,.12),.3,.7)
GATELIGHT=material('Gate warm lantern glass',(.95,.75,.40),.35)
GATELIGHT.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(1,.74,.36,1)
GATELIGHT.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=1.5
SCREEN=material('Dark television and appliance glass',(.006,.009,.012),.22,.12)
SOIL = material("Garden soil", (.12, .095, .06), 1)
GRASS = material("Moss green", (.18, .25, .09), .95)
LEAVES = [material("Leaf %s" % i, (.12+i*.025, .24+i*.023, .055+i*.012), .9) for i in range(5)]
EARTH = material("Surrounding ground", (.61, .61, .53), .98, noise=.2)


def cube(name, center, size, mat, bevel=0):
    x,y,z=(v/2 for v in size)
    vertices=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),
              (-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    data.update()
    obj=bpy.data.objects.new(name,data)
    COLS[CURRENT].objects.link(obj)
    obj.location=center
    move(obj,name,mat)
    if bevel:
        mod=obj.modifiers.new("Soft edges","BEVEL")
        mod.width,mod.segments=bevel,2
        obj.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return obj


def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    obj["floorGroup"]=CURRENT
    obj["sectionable"]=name=="Gable"
    COLS[CURRENT].objects.link(obj)
    if mat:
        data.materials.append(mat)
    return obj


def rod(name, a, b, radius, mat, vertices=12):
    vec=Vector(b)-Vector(a)
    assert vec.length>1e-8,(name,a,b)
    coords=[(radius*math.cos(i*math.tau/vertices),radius*math.sin(i*math.tau/vertices),z)
            for z in (-vec.length/2,vec.length/2) for i in range(vertices)]
    faces=[tuple(range(vertices-1,-1,-1)),tuple(range(vertices,2*vertices))]
    faces += [(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
    data=bpy.data.meshes.new(name);data.from_pydata(coords,[],faces);data.update()
    obj=bpy.data.objects.new(name,data);COLS[CURRENT].objects.link(obj)
    obj.location=(Vector(a)+Vector(b))/2
    obj.rotation_euler=vec.to_track_quat("Z","Y").to_euler()
    return move(obj,name,mat)


def build_walls(group, floor):
    ceiling = 3.3 if group=="stair1" else 3.12
    serial={"door":0,"window":0}
    group_label={"front":"前房一层","rear1":"后楼首层","rear2":"后楼二层","stair1":"首层楼梯","stair2":"二层楼梯","entry":"避雨门厅","storage":"杂物屋"}[group]
    for wall_index,item in enumerate(walls(group)):
        ax, ay = item["a"]
        bx, by = item["b"]
        length = abs(bx-ax)+abs(by-ay)
        horizontal = by == ay
        t = item["thickness"]

        def block(start, end, z0, height, mat=PLASTER, label="Wall"):
            if end-start < .001 or height < .001:
                return
            along = (start+end)/2
            cube(label, (ax+along if horizontal else ax,
                         ay if horizontal else ay+along, floor+z0+height/2),
                 (end-start if horizontal else t, t if horizontal else end-start, height), mat)

        previous = 0
        for opening_index,op in enumerate(item["openings"]):
            start, end = op["offset"], op["offset"]+op["width"]
            block(previous, start, 0, ceiling)
            block(start, end, 0, op["sill"])
            block(start, end, op["sill"]+op["height"], ceiling-op["sill"]-op["height"])
            if op["kind"] != "passage":
                before_opening=set(bpy.data.objects)
                serial[op['kind']]+=1
                opening_id=f'{group}-w{wall_index}-o{opening_index}'
                label='后楼首层 · 朝院横拉玻璃门' if op.get('operation')=='sliding' else '临街大门（双扇）' if op.get('style')=='grand' else f"{group_label} · {'窗' if op['kind']=='window' else '门'}{serial[op['kind']]:02}"
                z0 = floor+op["sill"]
                width, height = op["width"], op["height"]
                frame = .065
                for pos in (start+frame/2, end-frame/2):
                    block(pos-frame/2, pos+frame/2, op["sill"], height, DARKWOOD, "Opening jamb")
                block(start, end, op["sill"]+height-frame, frame, DARKWOOD, "Opening header")
                if op['kind']=='window' or op.get('operation')=='sliding':
                    sliding_door=op['kind']=='door'
                    sash_mat=DOORMETAL if sliding_door else DARKWOOD
                    block(start,end,op['sill'],.018 if sliding_door else frame,sash_mat,'Sliding door lower track' if sliding_door else 'Window sill')
                    if sliding_door:block(start,end,op['sill']+height-.025,.025,sash_mat,'Sliding door upper track')
                    clear_width=width-2*frame;sash_width=(clear_width+.035)/2
                    for index,along in enumerate((start+frame,start+frame+clear_width-sash_width)):
                        pivot=bpy.data.objects.new('Window sliding sash' if index==0 else 'Window fixed sash',None)
                        COLS[CURRENT].objects.link(pivot)
                        pivot.location=(ax+along if horizontal else ax,ay if horizontal else ay+along,z0+frame)
                        pivot.rotation_euler.z=0 if horizontal else math.pi/2
                        if index==0:
                            pivot['openingId']=opening_id;pivot['openingLabel']=label;pivot['openingKind']=op['kind']
                            pivot['floorGroup']=CURRENT;pivot['motion']='slide';pivot['travel']=clear_width-sash_width
                            pivot['defaultOpen']=sliding_door
                        parts=set(bpy.data.objects)
                        depth=.028 if index==0 else -.028
                        cube('Glazing', (sash_width/2,depth,(height-2*frame)/2), (sash_width-.07,.02,height-2*frame-.07), GLASS)
                        for x in (.0175,sash_width-.0175):
                            cube('Window sash stile',(x,depth,(height-2*frame)/2),(.035,.05,height-2*frame),sash_mat)
                        for z in (.0175,height-2*frame-.0175):
                            cube('Window sash rail',(sash_width/2,depth,z),(sash_width,.05,.035),sash_mat)
                        cube('Window sash transom',(sash_width/2,depth,.50),(sash_width,.05,.035),sash_mat)
                        for part in set(bpy.data.objects)-parts:part.parent=pivot
                        if index==0 and sliding_door:
                            if horizontal:pivot.location.x+=pivot['travel']
                            else:pivot.location.y+=pivot['travel']
                else:
                    leaves=((start,1),(end,-1)) if width>1.5 else ((end,-1),) if op.get('hinge_end') else ((start,1),)
                    for pos, side in leaves:
                        leaf_width = width/2 if width > 1.5 else width
                        pivot = bpy.data.objects.new("Door pivot", None)
                        COLS[CURRENT].objects.link(pivot)
                        pivot.location = (ax+pos if horizontal else ax, ay if horizontal else ay+pos, floor)
                        glazed=op.get('style')=='glazed'
                        grand=op.get('style')=='grand'
                        leaf = cube("Open glazed door" if glazed else "Open timber door", (0, 0, height/2),
                                    (leaf_width, .035 if glazed else .11 if grand else .055, height-.05), GLASS if glazed else (WOOD if grand else PALEWOOD), .01)
                        leaf.parent = pivot
                        leaf.location = (side*leaf_width/2, 0, height/2)
                        if glazed:
                            for xx in (side*.025,side*(leaf_width-.025)):
                                edge=cube('Opening glazed door frame',(0,0,0),(.05,.055,height),DOORMETAL,.005)
                                edge.parent=pivot;edge.location=(xx,0,height/2)
                            for zz in (.025,height-.025,height*.44):
                                edge=cube('Opening glazed door crossbar',(0,0,0),(leaf_width,.055,.05),DOORMETAL,.005)
                                edge.parent=pivot;edge.location=(side*leaf_width/2,0,zz)
                        if grand:
                            for xx in (leaf_width*.20,leaf_width*.80):
                                strip=cube('Grand gate bronze inlay',(0,0,0),(.018,.012,height-.28),GATEBRONZE,.003)
                                strip.parent=pivot;strip.location=(side*xx,-.061,height/2)
                            handle=cube('Grand gate bronze pull',(0,0,0),(.045,.075,.62),GATEBRONZE,.012)
                            handle.parent=pivot;handle.location=(side*(leaf_width-.17),-.102,1.12)
                            seal=cube('Grand gate lower inset',(0,0,0),(leaf_width-.22,.018,.28),DARKWOOD,.01)
                            seal.parent=pivot;seal.location=(side*leaf_width/2,-.063,.30)
                        closed=0 if horizontal else math.pi/2
                        opened=closed+(1 if horizontal else -1)*op['swing']*side*math.radians(75)
                        pivot.rotation_euler.z=opened
                        pivot['floorGroup']=CURRENT;pivot['openingId']=opening_id;pivot['openingLabel']=label
                        pivot['openingKind']='door';pivot['motion']='hinge';pivot['closedAngle']=closed
                        pivot['openAngle']=opened;pivot['defaultOpen']=True
                for part in set(bpy.data.objects)-before_opening:
                    if part.type=='MESH':
                        part['openingId']=opening_id;part['sectionable']=True
            previous = end
        block(previous, length, 0, ceiling)


def slab(bounds, z, label="Floor slab"):
    x1, y1, x2, y2 = bounds
    if z == .3:
        cube("Ground floor base", ((x1+x2)/2, (y1+y2)/2, .06), (x2-x1, y2-y1, .12), STONE)
    return cube(label, ((x1+x2)/2, (y1+y2)/2, z-.09), (x2-x1, y2-y1, .18), FLOOR)


def bed(x, y, z, width=1.6, head_top=1.15):
    cube("Bed timber base", (x, y, z+.22), (width+.12, 2.05, .36), DARKWOOD, .025)
    cube("Mattress", (x, y, z+.48), (width, 1.96, .2), BEDDING, .05)
    cube("Bedhead", (x, y+.99, z+.15+(head_top-.15)/2), (width+.14, .09, head_top-.15), DARKWOOD, .015)
    for dx in (-width*.25, width*.25):
        cube("Pillow", (x+dx, y+.65, z+.63), (width*.43, .43, .12), BEDDING, .045)
    vertices=[];faces=[]
    for row in range(33):
        yy=-1.03+row*1.66/32
        for col in range(25):
            xx=-(width/2+.07)+col*(width+.14)/24
            drop=max(0,abs(xx)-width/2+.025)*1.8+max(0,-yy-.92)*1.6
            zz=.605+.009*math.sin(col*.9+row*.45)+.004*math.sin(row*1.8)-drop
            vertices.append((x+xx,y+yy,z+zz))
    for row in range(32):
        for col in range(24):
            i=row*25+col;faces.append((i,i+1,i+26,i+25))
    quilt=mesh('Draped linen duvet',vertices,faces,BEDDING)
    for polygon in quilt.data.polygons:polygon.use_smooth=True


def table(x, y, z, width=1.4, depth=.8):
    cube("Timber table", (x, y, z+.76), (width, depth, .08), PALEWOOD, .025)
    for dx in (-width/2+.1, width/2-.1):
        for dy in (-depth/2+.1, depth/2-.1):
            cube("Table leg", (x+dx, y+dy, z+.37), (.06, .06, .74), DARKWOOD)


def chair(x, y, z, turn=0):
    seat = cube("Chair seat", (x, y, z+.43), (.43, .43, .08), PALEWOOD, .02)
    for dx in (-.16, .16):
        for dy in (-.16, .16):
            cube("Chair leg", (x+dx, y+dy, z+.21), (.045, .045, .42), DARKWOOD)
    cube("Chair back", (x, y+.18, z+.72), (.43, .055, .5), PALEWOOD, .015)


def bath(x, y, z):
    cube("Shower tray", (x, y+.8, z+.06), (.85, .85, .08), WATER, .02)
    cube("Shower screen", (x+.4, y+.8, z+1.0), (.015, .85, 1.85), GLASS)
    cube("WC cistern", (x, y-.25, z+.55), (.44, .2, .65), WATER, .07)
    cube("WC pan", (x, y-.52, z+.28), (.4, .58, .38), WATER, .12)


def rail(a, b, z, height=1.1):
    rod("Timber handrail", (*a, z+height), (*b, z+height), .035, DARKWOOD)
    length = (Vector(b)-Vector(a)).length
    for i in range(max(2, math.ceil(length/.11))+1):
        p = Vector(a).lerp(Vector(b), i/max(2, math.ceil(length/.11)))
        rod("Balustrade", (*p, z+.1), (*p, z+height), .013, DARKWOOD, 8)


CURRENT = "Site"
cube("Surrounding terrain", (6, 12, -.22), (300, 300, .2), EARTH)
sx1,sy1,sx2,sy2=SITE_BOUNDS
cube("Site plinth", ((sx1+sx2)/2,(sy1+sy2)/2,-.09),(sx2-sx1,sy2-sy1,.18),STONE)
cube("Rear service yard",(SITE[0]/2,26.9,.005),(SITE[0],5,.03),FLOOR)
cube("South road", (6, -10.4, -.045), (50, 4, .08), PAVE[0])
fx1,fy1,fx2,fy2=FORECOURT['bounds']
cube('Open front forecourt',((fx1+fx2)/2,(fy1+fy2)/2,.004),(fx2-fx1,fy2-fy1,.025),PAVE[2])
for x in range(1,16):cube('Forecourt paving joint',(x,-4,.019),(.006,8,.002),STONE)
for y in range(-7,1):cube('Forecourt paving joint',(SITE[0]/2,y,.019),(SITE[0],.006,.002),STONE)
cube('Forecourt central approach',(6,-4,.023),(2.4,8,.012),FLOOR)
CURRENT='Outbuilding'
slab(STORAGE['bounds'],STORAGE['floor'],'Storage ground slab')
build_walls('storage',STORAGE['floor'])
x1,y1,x2,y2=STORAGE['bounds']
cube('Storage entrance tread',(x1-.32,y1+1.50,.075),(.64,1.5,.15),FLOOR,.015)
for z in (.55,1.1,1.65,2.2):
    cube('Storage north shelf',((x1+x2)/2,y2-.42,z),(3.1,.50,.05),WOOD,.008)
    cube('Storage east shelf',(x2-.52,(y1+y2)/2,z),(.50,y2-y1-1.10,.05),WOOD,.008)
for x,y in ((x1+.3,y2-.42),(x2-.3,y2-.42),(x2-.52,y1+.55),(x2-.52,(y1+y2)/2),(x2-.52,y2-.55)):
    cube('Storage shelf upright',(x,y,1.20),(.045,.045,2.15),DARKWOOD)
for x,y in ((x1+.8,y2-.42),(x1+1.5,y2-.42),(x1+2.6,y2-.42),(x2-.52,y1+2.2)):
    cube('Storage covered box',(x,y,.78),(.46,.40,.38),WOOD,.012)
CURRENT='OutbuildingRoof'
slab(STORAGE['bounds'],STORAGE['roof_level'],'Storage flat roof slab')
CURRENT='Site'
for (a,b,c,d),top in zip(COURTYARD_WALLS,COURTYARD_WALL_TOPS):
    side=(a+c)/2;length=d-b;center=(b+d)/2
    boundary=cube("Courtyard boundary wall", (side, center, top/2), (c-a, length, top), PLASTER)
    boundary['sectionable']=True
    if top<3:
        coping=cube("Boundary coping", (side, center, top+.03), (.26, length, .12), STONE, .025)
        coping['sectionable']=True
    cube("Boundary plinth", (side, center, .23), (c-a+.04, length, .46), STONE)
for x in range(18):
    for y in range(13):
        cx, cy = .9+x*.6, 6.9+y*.6
        cube("Courtyard paving", (cx, cy, -.015), (.587, .587, .05), PAVE[(x+2*y)%4])
for cy in (6.78, 14.2):
    cube("Courtyard drain - indicative", (6, cy, .015), (9.8, .07, .02), STONE)
# Every +0.300 entrance has a visible intermediate +0.150 tread.
for x, y, width, depth in [(6, .3, 2.8, .6), (6, 6.85, 2.8, .5),
                           (6, 14.15, 3.1, .5)]:
    cube("150mm entrance tread", (x, y, .075), (width, depth, .15), FLOOR, .015)

CURRENT = "Front"
slab(FRONT, .3)
build_walls("front", .3)
for x in (4.62,7.38):
    cube('Grand entrance stone jamb',(x,.53,1.63),(.30,.38,2.66),STONE,.015)
    cube('Grand entrance wall lantern',(x,.31,2.08),(.09,.13,.38),GATEBRONZE,.014)
    cube('Grand entrance lantern glass',(x,.235,2.08),(.055,.02,.30),GATELIGHT,.005)
cube('Grand entrance stone lintel',(6,.53,2.98),(3.06,.38,.30),STONE,.015)
cube('Grand entrance deep shadow header',(6,.315,2.82),(2.48,.035,.045),DOORMETAL,.004)
cube('Grand entrance threshold',(6,.54,.31),(2.42,.40,.02),STONE,.008)
for left, right in ((.6, 4.8), (7.2, 11.4)):
    cube("Front stone base", ((left+right)/2, .59, .51), (right-left, .035, .42), STONE)

CURRENT = "Rear1"
slab(REAR, .3)
slab(EAST_SUITE['bounds'],.3,'East suite ground slab')
build_walls("rear1", .3)
for x in (.72, 4.2, 7.8, 11.28):
    cube("Porch timber post - indicative", (x, 16.14, 1.95), (.17, .17, 3.3), DARKWOOD, .01)
    cube("Post stone shoe", (x, 16.14, .5), (.27, .27, .4), STONE, .025)
cube("Porch timber lintel - indicative", (6, 16.14, 3.35), (10.65, .22, .25), DARKWOOD)
CURRENT = "Stairs"
slab(STAIR["bounds"],.3,"Enclosed stair ground landing")
flight_south,flight_north=STAIR["flight_bounds"]
for x,z_south,z_north in ((13.575,.27,1.76),(12.225,3.44,1.76)):
    slope=cube("Stair flight support - schematic",(x,(flight_south+flight_north)/2,(z_south+z_north)/2-.12),
               (1.05,math.hypot(flight_north-flight_south,z_north-z_south),.16),PLASTER)
    slope.rotation_euler.x=math.atan2(z_north-z_south,flight_north-flight_south)
for i in range(9):
    top=.3+(i+1)*.165
    cube("Lower stair tread %02d"%(i+1),(13.575,flight_south+(i+.5)*.27,top-.09),(1.05,.27,.18),FLOOR)
slab(STAIR["mid_landing"],1.95,"Stair midlanding")
for i in range(9):
    top=1.95+(i+1)*.165
    cube("Upper stair tread %02d"%(i+11),(12.225,flight_north-(i+.5)*.27,top-.09),(1.05,.27,.18),FLOOR)
slab(STAIR["top_landing"],3.6,"Enclosed stair top landing")
for x,lower in ((13.03,True),(14.06,True),(11.68,False),(12.77,False)):
    a=(x,flight_south,.465+1.1) if lower else (x,flight_south,3.6+1.1)
    b=(x,flight_north,1.95+1.1)
    rod("Stair handrail",a,b,.032,DARKWOOD)
    for i in range(25):
        t=i/24;p=Vector(a).lerp(Vector(b),t)
        rod("Stair baluster",p-Vector((0,0,1.1)),p,.012,DARKWOOD,8)
rail((12.82,flight_south),(14.06,flight_south),3.6)
# The former outdoor step is inside the new level vestibule.
CURRENT="Rear1"
slab(COVERED_ENTRY['bounds'],.3,"Covered entry ground slab")
CURRENT="StairShell1"
build_walls("stair1",.3)
build_walls("entry",.3)
CURRENT="StairShell2"
build_walls("stair2",3.6)
CURRENT="StairRoof"
slab(STAIR["bounds"],6.9,"Stairwell roof slab")
slab(EAST_SUITE['bounds'],6.9,'East suite roof slab')
CURRENT="EntryRoof"
slab(COVERED_ENTRY['roof_bounds'],COVERED_ENTRY['roof_level'],"Covered entry roof slab")
CURRENT = "Rear2"
slab(REAR,3.6)
slab(EAST_SUITE['bounds'],3.6,'East suite upper slab')
build_walls("rear2",3.6)
# The former open balcony is a shared enclosed foyer, with side entry and two terrace doors.

# Shared renovation layout: finish surfaces, fixtures and fittings.
OAK = textured_material("Warm oak floor",'warm-oak.png',(.47,.31,.16),.58)
TILE = textured_material("Warm limestone bathroom tile",'warm-stone.png',(.62,.60,.55),.62)
COUNTER = textured_material("Pale quartz",'warm-stone.png',(.73,.72,.66),.3)
METAL = material("Warm brushed bronze", (.32,.24,.14), .3, .65)
MIRROR = material("Mirror", (.68,.77,.78), .06, .85)
ACCENT = textured_material("Warm stone feature panel",'warm-stone.png',(.64,.59,.5),.65)
LED = material("Warm ceiling light", (.95,.85,.62), .4)
ledbsdf=LED.node_tree.nodes.get("Principled BSDF")
ledbsdf.inputs["Emission Color"].default_value=(1,.8,.5,1)
ledbsdf.inputs["Emission Strength"].default_value=2.5
GLASS.node_tree.nodes.get("Principled BSDF").inputs["Alpha"].default_value=.34
GLASS.surface_render_method="DITHERED"

CURRENT="EntryRoof"
rod('Covered entry east gutter',(14.28,14.45,3.61),(14.28,16.69,3.61),.035,METAL)
rod('Covered entry gutter outlet',(14.28,15.9,3.59),(14.54,15.9,3.59),.035,METAL)
CURRENT="StairShell1"
rod('Covered entry rain pipe',(14.54,15.9,.24),(14.54,15.9,3.59),.035,METAL)
for key,base in (('Rear1',.3),('Rear2',3.6)):
    CURRENT=key
    cube('East suite extraction grille',(14.345,22.65,base+2.7),(.04,.28,.22),METAL,.008)
    rod('East suite separate extract',(14.08,22.65,base+2.7),(14.47,22.65,base+2.7),.065,METAL,24)

for spec in room_specs():
    CURRENT={"front":"Front","rear1":"Rear1","rear2":"Rear2"}[spec["group"]]
    x1,y1,x2,y2=spec["inner"];z=spec["floor"];kind=spec["kind"]
    if kind!="stair":
        for fx1,fy1,fx2,fy2 in spec.get("floor_parts",[spec["inner"]]):
            timber_floor = kind=="bed" and spec["group"]=="front"
            floor_mat = OAK if timber_floor else LIGHTFLOOR if kind=="bed" else TILE if kind=="wet" else FLOOR
            floor_obj=cube("Interior floor / "+spec["name"],((fx1+fx2)/2,(fy1+fy2)/2,z+.009),
                (fx2-fx1,fy2-fy1,.018),floor_mat)
            floor_obj["roomId"]=spec["id"]
            if timber_floor:
                for i in range(int((fx2-fx1)/.18)):
                    x=fx1+(i+1)*.18
                    cube("Oak plank seam",(x,(fy1+fy2)/2,z+.019),(.006,fy2-fy1,.001),PALEWOOD)
            elif kind=="bed":
                for i in range(1,int((fx2-fx1)/.6)+1):
                    cube('Bedroom stone tile joint',(fx1+i*.6,(fy1+fy2)/2,z+.019),(.004,fy2-fy1,.001),COUNTER)
                for i in range(1,int((fy2-fy1)/1.2)+1):
                    cube('Bedroom stone tile joint',((fx1+fx2)/2,fy1+i*1.2,z+.019),(fx2-fx1,.004,.001),COUNTER)
            elif kind=="wet":
                for i in range(1,int((fy2-fy1)/.3)):
                    cube("Tile joint",((fx1+fx2)/2,fy1+i*.3,z+.02),(fx2-fx1,.005,.002),FLOOR)
            else:
                for i in range(1,int((fx2-fx1)/.8)+1):
                    cube('Stone tile fine joint',(fx1+i*.8,(fy1+fy2)/2,z+.019),(.003,fy2-fy1,.001),COUNTER)
                for i in range(1,int((fy2-fy1)/.8)+1):
                    cube('Stone tile fine joint',((fx1+fx2)/2,fy1+i*.8,z+.019),(fx2-fx1,.003,.001),COUNTER)
        # Wall-mounted boards keep interior lights readable with ceilings hidden.
        cube("Ceiling light",((x1+x2)/2,(y1+y2)/2,z+2.98),(.42,.42,.055),LED,.02)
        for cx1,cy1,cx2,cy2 in spec.get('floor_parts',[spec['inner']]):
            ceiling=cube('Interior ceiling panel',((cx1+cx2)/2,(cy1+cy2)/2,z+3.08),
                         (cx2-cx1,cy2-cy1,.04),PLASTER)
            ceiling['interiorCeiling']=True
            ceiling.hide_render=True

def wardrobe(obj,floor):
    """Five usable storage bays with independently hinged doors."""
    x1,y1,x2,y2=obj['bounds'];depth=x2-x1;length=y2-y1;height=obj['height']
    cabinet_id='wardrobe-'+obj['bedroom'];east=obj.get('mirrored',False)
    before=set(bpy.data.objects)
    def point(u,d,z):
        return (x1+d if east else x2-d,y1+u,floor+z)
    def board(name,u,d,z,w,t,h,mat=PALEWOOD,part='carcass'):
        panel=cube('Wardrobe '+name,point(u,d,z),(t,w,h),mat,.002)
        panel['wardrobePart']=part
        return panel
    for u in (.009,length-.009):board('side',u,depth/2,height/2,.018,depth,height)
    board('back',length/2,.0045,height/2,length-.036,.009,height)
    for z in (.12,height-.009):board('horizontal panel',length/2,depth/2,z,length-.036,depth,.018)
    board('plinth',length/2,depth-.10,.055,length-.036,.018,.11,DARKWOOD)
    board('quilt shelf',length/2,(depth-.08)/2,2.08,length-.036,depth-.08,.018,part='shelf')
    pitch=(length-.036)/5;bay=pitch-.018
    for index in range(1,5):board('divider',.018+pitch*index,(depth-.06)/2,1.10,.018,depth-.06,1.94,part='divider')
    for index,levels in ((2,(.75,1.16,1.58)),(3,(.47,.87,1.27,1.67)),(4,(.75,1.40))):
        u=.018+pitch*(index+.5)
        for z in levels:
            board('folded clothes shelf',u,(depth-.06)/2,z,bay,depth-.06,.018,part='shelf')
            for layer in range(2):board('folded linen',u,.25,z+.04+layer*.055,bay*.82,.32,.05,BEDDING if layer else FABRIC,'linen')
    drawer_u=.018+pitch*2.5
    for z in (.23,.43,.63):
        board('drawer front',drawer_u,depth-.055,z,bay-.008,.018,.18,part='drawer')
        board('drawer bottom',drawer_u,.25,z-.081,bay-.02,.42,.018,part='drawer')
        for u in (drawer_u-bay/2+.012,drawer_u+bay/2-.012):board('drawer side',u,.25,z,.018,.42,.16,part='drawer')
        board('drawer rear',drawer_u,.04,z,bay-.02,.018,.16,part='drawer')
        board('drawer pull',drawer_u,depth-.037,z+.04,.18,.025,.014,METAL,'drawer')
    for index,z in ((0,obj['rail_height']),(1,.95),(1,1.82)):
        u=.018+pitch*(index+.5)
        rail=rod('Wardrobe hanging rail',point(u-bay/2+.015,.26,z),point(u+bay/2-.015,.26,z),.012,METAL)
        rail['wardrobePart']='rail'
        for a,b in ((point(u,.26,z-.02),point(u,.065,z-.15)),
                    (point(u,.065,z-.15),point(u,.445,z-.15)),
                    (point(u,.445,z-.15),point(u,.26,z-.02))):
            hanger=rod('Wardrobe hanger',a,b,.009,PALEWOOD);hanger['wardrobePart']='hanger'
    board('lower storage box',.018+pitch*.5,.24,.25,bay*.72,.33,.23,FABRIC,'linen')
    for index in range(5):
        u=.018+pitch*(index+.5)
        board('quilt',u,.24,2.23,bay*.85,.35,.22,BEDDING,'linen')
    for index in range(5):
        u=.018+pitch*index;leaf_width=pitch-.003
        pivot=bpy.data.objects.new('Wardrobe hinged leaf',None);COLS[CURRENT].objects.link(pivot)
        pivot.location=point(u,depth-.016,0);pivot.rotation_euler.z=math.pi/2
        for key,value in dict(floorGroup=CURRENT,openingId=cabinet_id,openingLabel=obj['name'],
                              openingKind='wardrobe',motion='hinge',closedAngle=math.pi/2,
                              openAngle=0 if east else math.pi,defaultOpen=False,panelIndex=index).items():pivot[key]=value
        leaf=board('hinged door',u+leaf_width/2,depth-.016,(height+.12)/2,leaf_width,.018,height-.20,part='door')
        pull=board('recessed door pull',u+leaf_width-.045,depth+.002,1.1,.018,.012,.36,METAL,'door')
        for panel in (leaf,pull):
            panel.parent=pivot
            panel.matrix_parent_inverse=pivot.matrix_basis.inverted()
            panel['openingId']=cabinet_id
            panel['wardrobeDoorIndex']=index
    for part in set(bpy.data.objects)-before:
        part['wardrobeId']=cabinet_id


for group,items in furnishings().items():
    CURRENT={"front":"Front","rear1":"Rear1","rear2":"Rear2"}[group]
    floor=3.6 if group=="rear2" else .3
    for index,obj in enumerate(items):
        before=set(bpy.data.objects)
        x1,y1,x2,y2=obj["bounds"];cx,cy=(x1+x2)/2,(y1+y2)/2
        width,depth=x2-x1,y2-y1;kind=obj["kind"]
        if kind=="bed":
            rotation=math.radians(obj.get("rotation",0))
            bed(cx,cy,floor,(depth if obj.get("rotation",0)%180==90 else width)-.14,obj.get('head_top',1.15))
            for part in set(bpy.data.objects)-before:
                dx,dy=part.location.x-cx,part.location.y-cy
                part.location.x=cx+dx*math.cos(rotation)-dy*math.sin(rotation)
                part.location.y=cy+dx*math.sin(rotation)+dy*math.cos(rotation)
                part.rotation_euler.z+=rotation
        elif kind=='wardrobe' and obj.get('bedroom'):
            wardrobe(obj,floor)
        elif kind in ("cabinet","wardrobe","console","nightstand","bench","fridge","washer"):
            height=obj["height"]
            mat=WATER if kind in ("fridge","washer") else PALEWOOD
            if not obj.get('countertop_only'):
                cube(obj["name"],(cx,cy,floor+height/2),(width,depth,height),mat,.018)
            if kind=="cabinet":
                cube("Quartz countertop",(cx,cy,floor+height+.025),(width+.015,depth+.015,.05),COUNTER,.01)
                if obj.get('countertop_only'):
                    for y in (y1+.02,y2-.02):
                        cube('Dishwasher bay side support',(cx,y,floor+height/2),(width,.025,height),PALEWOOD)
                elif depth>width:
                    face=x1-.008 if cx>9.6 else x2+.008
                    for i in range(1,max(2,round(depth/.55))):
                        yy=y1+depth*i/max(2,round(depth/.55))
                        cube('Kitchen cabinet reveal',(face,yy,floor+height/2),(.009,.009,height-.10),DARKWOOD)
                else:
                    for i in range(1,max(2,round(width/.55))):
                        xx=x1+width*i/max(2,round(width/.55))
                        cube('Kitchen cabinet reveal',(xx,y2+.008,floor+height/2),(.009,.009,height-.10),DARKWOOD)
            if kind=="washer":
                rod("Washer door",(cx,y1-.012,floor+.43),(cx,y1-.04,floor+.43),.22,GLASS,32)
            if kind=='fridge':
                cube('Fridge door split',(x1-.014,cy,floor+.70),(.024,depth-.035,.016),STONE)
                for h in (.40,1.35):
                    cube('Fridge handle',(x1-.047,y2-.12,floor+h),(.065,.025,.30),METAL,.008)
            if kind=="wardrobe":
                if obj.get('front')=='south':
                    cube('South cabinet door',(cx,y1-.008,floor+height/2),(width-.025,.018,height-.04),PALEWOOD,.008)
                    cube('South cabinet door handle',(x2-.07,y1-.025,floor+1.15),(.018,.025,.16),METAL)
                else:
                    for y in (y1+depth/3,y1+2*depth/3):
                        cube("Sliding wardrobe door line",(x2+.008 if obj.get("mirrored") else x1-.008,y,floor+1.2),(.015,.015,2.35),DARKWOOD)
        elif kind=='roundtable':
            rod('Round gathering table top',(cx,cy,floor+obj['height']-.035),(cx,cy,floor+obj['height']+.035),width/2,PALEWOOD,64)
            rod('Round gathering pedestal',(cx,cy,floor+.08),(cx,cy,floor+obj['height']-.035),.15,DARKWOOD,32)
            rod('Round gathering base',(cx,cy,floor+.03),(cx,cy,floor+.09),.38,DARKWOOD,48)
            for i in range(6):
                a=i*math.pi/3;px=cx+.28*math.sin(a)+.10*math.cos(a);py=cy+.28*math.cos(a)-.10*math.sin(a)
                rod('Gathering tea cup',(px,py,floor+obj['height']+.045),(px,py,floor+obj['height']+.12),.045,WATER,24)
                px=cx+.43*math.sin(a);py=cy+.43*math.cos(a)
                rod('Round dining plate',(px,py,floor+obj['height']+.036),(px,py,floor+obj['height']+.050),.115,WATER,32)
        elif kind=='stool':
            cube(obj['name'],(cx,cy,floor+.40),(width,depth,.09),FABRIC,.035)
            for x in (x1+.06,x2-.06):
                for y in (y1+.06,y2-.06):cube('Dressing stool leg',(x,y,floor+.20),(.035,.035,.40),PALEWOOD)
        elif kind in ("table","desk"):
            top=obj["height"]
            cube(obj["name"],(cx,cy,floor+top),(width,depth,.065),PALEWOOD,.02)
            for x in (x1+.07,x2-.07):
                for y in (y1+.07,y2-.07):cube("Furniture leg",(x,y,floor+top/2),(.045,.045,top),DARKWOOD)
            if obj.get('dressing'):
                back=x1-.025 if obj['front']=='east' else x2+.025
                cube('Dressing mirror frame',(back,cy,floor+1.33),(.04,depth-.08,.80),PALEWOOD,.025)
                face=back+.023 if obj['front']=='east' else back-.023
                cube('Dressing mirror',(face,cy,floor+1.33),(.012,depth-.16,.72),MIRROR,.018)
                for y in (y1+.055,y2-.055):cube('Dressing mirror light',(face,y,floor+1.33),(.016,.016,.68),LED,.006)
                cube('Dressing drawer',(cx,y2-.12,floor+.65),(width-.04,.22,.14),PALEWOOD,.01)
            if obj.get('name')=='六人餐桌':
                for px in (x1+.30,cx,x2-.30):
                    for py in (y1+.19,y2-.19):
                        rod('Ceramic dinner plate',(px,py,floor+top+.039),(px,py,floor+top+.055),.115,WATER,32)
                        rod('Dining cup',(px+.11,py,floor+top+.05),(px+.11,py,floor+top+.13),.034,WATER,24)
                rod('Dining ceramic vase',(cx,cy,floor+top+.04),(cx,cy,floor+top+.26),.055,WATER,32)
            if kind=='desk':
                for i in range(3):
                    cube('Desk book',(x1+.24,y2-.18,floor+top+.055+i*.035),(.30,.22,.03),PALEWOOD if i%2 else BEDDING,.004)
        elif kind=="chair":
            chair(cx,cy,floor)
            if obj.get('upholstered'):
                cube('Dining chair seat cushion',(cx,cy,floor+.49),(.40,.40,.07),FABRIC,.035)
                cube('Dining chair padded back',(cx,cy+.15,floor+.74),(.36,.075,.31),FABRIC,.035)
        elif kind=='armchair':
            cube('Reading chair timber base',(cx,cy,floor+.23),(width-.10,depth-.10,.32),PALEWOOD,.035)
            cube('Reading chair cushion',(cx,cy-.035,floor+.45),(width-.14,depth-.13,.18),FABRIC,.07)
            cube('Reading chair back',(cx,y2-.08,floor+.65),(width,.16,.30),FABRIC,.065)
            for x in (x1+.07,x2-.07):
                cube('Reading chair arm',(x,cy,floor+.55),(.14,depth,.22),FABRIC,.055)
        elif kind=="banquette":
            cube("Dining banquette seat",(cx,cy,floor+.44),(width,depth,.13),FABRIC,.03)
            cube("Dining banquette back",(cx,y2-.05,floor+.64),(width,.1,.42),FABRIC,.025)
            cube("Dining banquette base",(cx,cy,floor+.2),(width,depth,.4),PALEWOOD)
        elif kind=="oven":
            cube("Built-in oven fascia",(x2+.012 if obj.get("mirrored") else x1-.012,cy,floor+.43),(.025,depth,.55),STONE,.015)
            cube("Oven glass",(x2+.03 if obj.get("mirrored") else x1-.03,cy,floor+.4),(.025,depth-.1,.34),GLASS,.02)
            rod("Oven handle",(x2+.07 if obj.get("mirrored") else x1-.07,y1+.08,floor+.62),(x2+.07 if obj.get("mirrored") else x1-.07,y2-.08,floor+.62),.016,METAL)
        elif kind in ('dishwasher','microwave','griddle','ricecooker'):
            bottom=obj.get('z',0);height=obj['height']
            cube(obj['name'],(cx,cy,floor+bottom+height/2),(width,depth,height),METAL if kind!='ricecooker' else WATER,.025)
            if kind=='dishwasher':
                cube('Dishwasher front',(x1-.012,cy,floor+.44),(.025,depth-.02,.85),METAL,.012)
                cube('Dishwasher control',(x1-.028,cy,floor+.77),(.018,depth-.08,.07),STONE,.006)
            elif kind=='microwave':
                cube('Microwave glass front',(cx,y1-.012,floor+bottom+.19),(width-.07,.025,.27),SCREEN,.014)
            elif kind=='griddle':
                cube('Electric griddle lid',(cx,cy,floor+bottom+height+.012),(width-.04,depth-.04,.025),STONE,.025)
        elif kind=="coffee":
            cube("Coffee machine",(cx,cy,floor+1.09),(width,depth,.33),METAL,.025)
            cube("Coffee machine front",(x2+.008 if obj.get("mirrored") else x1-.008,cy,floor+1.09),(.025,depth-.05,.27),STONE,.01)
        elif kind=="sofa":
            cube("Upholstered sofa",(cx,cy,floor+.30),(width,depth,.42),FABRIC,.09)
            cube("Sofa back",(x2-.09,cy,floor+.67),(.18,depth,.43),FABRIC,.065)
            for yy in (y1+.09,y2-.09):
                cube('Sofa soft arm',(cx,yy,floor+.52),(width,.18,.45),FABRIC,.06)
            for i in range(3):
                yy=y1+.18+(i+.5)*(depth-.36)/3
                cube('Sofa seat cushion',(cx-.03,yy,floor+.52),(width-.16,(depth-.36)/3-.025,.16),FABRIC,.065)
            for yy in (y1+.42,y2-.42):
                pillow=cube('Sofa loose cushion',(x2-.23,yy,floor+.73),(.18,.40,.36),BEDDING,.07)
                pillow.rotation_euler.y=math.radians(-12)
        elif kind=="tv":
            cube("TV console",(cx,cy,floor+.25),(width,depth,.5),PALEWOOD,.02)
            cube("TV screen",(x1+.035,cy,floor+1.2),(.05,depth,.66),SCREEN,.015)
        elif kind=="hob":
            cube('High-output gas hob concept',(cx,cy,floor+.931),(width,depth,.025),STONE,.012)
            rod('Gas burner ring',(cx,cy,floor+.95),(cx,cy,floor+.985),.14,METAL,32)
            for dy in (-.13,.13):cube('Gas pan support',(cx,cy+dy,floor+1.00),(.36,.025,.045),STONE)
            if obj['name'].startswith('猛火灶 1'):
                cube('Shared extractor hood for two hobs',(cx,1.88,floor+1.9),(.64,1.56,.16),METAL,.03)
                cube('Kitchen splashback',(11.145,1.88,floor+1.40),(.025,1.64,.85),COUNTER)
                rod('Shared hood branch',(cx,1.88,floor+1.98),(cx,1.60,floor+1.98),.09,METAL,24)
        elif kind=="sink":
            cube("Sink rim",(cx,cy,floor+.94),(width,depth,.03),METAL,.01)
            cube("Sink bowl",(cx,cy,floor+.96),(width-.09,depth-.09,.035),STONE,.03)
            rod("Kitchen tap",(x2-.06 if obj.get("mirrored") else x1+.06,cy,floor+.95),(x2-.06 if obj.get("mirrored") else x1+.06,cy,floor+1.24),.018,METAL)
            rod("Tap spout",(x2-.06 if obj.get("mirrored") else x1+.06,cy,floor+1.24),(cx,cy,floor+1.24),.018,METAL)
        elif kind=="shower":
            cube("Shower floor",(cx,cy,floor+.025),(width,depth,.03),TILE)
            cube("Shower sliding screen",(cx,y1,floor+1.03),(width,.018,2.05),GLASS)
            rod("Shower top track",(x1,y1,floor+2.08),(x2,y1,floor+2.08),.018,METAL)
            cube("Shower sliding stile",(cx,y1,floor+1.03),(.02,.04,2.05),METAL)
            rod("Shower riser",(cx,y2-.03,floor+.9),(cx,y2-.03,floor+1.96),.018,METAL)
            rod("Shower arm",(cx,y2-.03,floor+1.96),(cx,y2-.28,floor+1.96),.018,METAL)
            cube("Shower head",(cx,y2-.3,floor+1.96),(.22,.22,.035),METAL,.02)
            cube("Linear drain",(cx,y2-.07,floor+.045),(width-.15,.035,.01),METAL)
        elif kind=="wc":
            sign=1 if obj["rotation"]==0 else -1
            back=x1+.08 if sign==1 else x2-.08
            cube("WC cistern",(back,cy,floor+.46),(.16,depth,.65),WATER,.06)
            cube("WC pan",(cx,cy,floor+.27),(width-.1,depth-.06,.4),WATER,.13)
            cube("WC seat",(cx+sign*.05,cy,floor+.49),(width-.21,depth-.12,.055),WATER,.1)
        elif kind=="vanity":
            side=x1-.02 if obj["rotation"]==0 else x2+.02
            cube("Vanity cabinet",(cx,cy,floor+.45),(width,depth,.72),PALEWOOD,.02)
            cube("Vanity basin rim",(cx,cy,floor+.84),(width+.025,depth+.025,.09),WATER,.025)
            cube("Basin inset",(cx,cy,floor+.89),(width-.13,depth-.15,.025),GLASS,.04)
            cube("Bathroom mirror",(side,cy,floor+1.5),(.03,depth,.65),MIRROR,.01)
            rod("Basin tap",(side,cy,floor+.87),(side,cy,floor+1.03),.012,METAL)
        if kind in ('sofa','chair','tv','armchair') and obj.get('rotation'):
            angle=math.radians(obj['rotation'])
            for part in set(bpy.data.objects)-before:
                dx,dy=part.location.x-cx,part.location.y-cy
                part.location.x=cx+dx*math.cos(angle)-dy*math.sin(angle)
                part.location.y=cy+dx*math.sin(angle)+dy*math.cos(angle)
                part.rotation_euler.z+=angle
        for new in set(bpy.data.objects)-before:
            new["fixtureId"]=f"{group}-{index}"
            new["roomId"]=f"{group}-{obj['room']}"
            new["fixtureKind"]=kind

CURTAIN=textured_material('Warm ivory curtain','linen.png',(.78,.73,.64),.96)
INK_ART=textured_material('Reference ink landscape','reference-ink-art.png',(.70,.68,.62),.95)
SHEER=material('Translucent ivory sheer',(.93,.91,.85),.95)
SHEER.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.22
SHEER.surface_render_method='DITHERED'
decor_materials={'oak':WOOD,'quartz':COUNTER,'metal':METAL,'accent':ACCENT,'fabric':CURTAIN,'light':LED}
for group,items in decoration().items():
    CURRENT={'front':'Front','rear1':'Rear1','rear2':'Rear2'}[group]
    floor=3.6 if group=='rear2' else .3
    for index,obj in enumerate(items):
        before=set(bpy.data.objects)
        x1,y1,x2,y2=obj['bounds'];cx,cy=(x1+x2)/2,(y1+y2)/2
        width,depth=x2-x1,y2-y1;z=floor+obj['z'];height=obj['height'];kind=obj['kind']
        mat=decor_materials[obj['material']]
        name=obj['name']
        if kind=='art':
            for yy in (y1,y2):cube('Art timber frame',(cx,yy,z+height/2),(width,.025,height+.04),DARKWOOD,.004)
            for zz in (z,z+height):cube('Art timber frame',(cx,cy,zz),(width,depth,.025),DARKWOOD,.004)
            artwork=mesh('Framed ink landscape',[(x2+.001,y1,z),(x2+.001,y2,z),(x2+.001,y2,z+height),(x2+.001,y1,z+height)],[(0,1,2,3)],INK_ART)
            uv=artwork.data.uv_layers.new(name='ArtUV')
            for loop,value in zip(artwork.data.polygons[0].loop_indices,((0,0),(1,0),(1,1),(0,1))):uv.data[loop].uv=value
        elif kind=='border':
            for yy in (y1,y2):cube('Stone floor border',(cx,yy,z+height/2),(width,.018,height),DOORMETAL)
            for xx in (x1,x2):cube('Stone floor border',(xx,cy,z+height/2),(.018,depth,height),DOORMETAL)
        elif kind=='sheer':
            for i in range(16):
                if width>depth:
                    center=(x1+(i+.5)*width/16,cy+(.004 if i%2 else -.004),z+height/2)
                    size=(width/16,depth,height)
                else:
                    center=(cx+(.004 if i%2 else -.004),y1+(i+.5)*depth/16,z+height/2)
                    size=(width,depth/16,height)
                cube('Sheer curtain pleat',center,size,SHEER)
        elif kind=='cove':
            north_spans=[(x1,obj['north_gap'][0]),(obj['north_gap'][1],x2)] if obj.get('north_gap') else [(x1,x2)]
            fascia=[(x1,y1,x2,y1+.14),(x1,y1+.14,x1+.14,y2-.14),(x2-.14,y1+.14,x2,y2-.14)]
            fascia.extend((a,y2-.14,b,y2) for a,b in north_spans)
            for a,b,c,d in fascia:
                cube('Ceiling light / Cove fascia',((a+c)/2,(b+d)/2,z+height/2),(c-a,d-b,height),PLASTER,.01)
            strips=[((x1+.17,y1+.17,z+.08),(x2-.17,y1+.17,z+.08)),
                    ((x1+.17,y1+.17,z+.08),(x1+.17,y2-.17,z+.08)),
                    ((x2-.17,y1+.17,z+.08),(x2-.17,y2-.17,z+.08))]
            strips.extend(((max(a,x1+.17),y2-.17,z+.08),(min(b,x2-.17),y2-.17,z+.08)) for a,b in north_spans)
            for a,b in strips:
                rod('Ceiling light / Cove warm strip',a,b,.012,LED,8)
                trim_a=(a[0],a[1],z+.012);trim_b=(b[0],b[1],z+.012)
                rod('Ceiling light / Cove timber trim',trim_a,trim_b,.012,PALEWOOD,8)
        elif kind=='slats':
            count=max(2,int(max(width,depth)/.065))
            for i in range(count):
                if depth>width:
                    center=(cx,y1+(i+.5)*depth/count,z+height/2);size=(width,.025,height)
                else:
                    center=(x1+(i+.5)*width/count,cy,z+height/2);size=(.025,depth,height)
                cube('Timber feature slat',center,size,mat,.005)
        elif kind=='lantern':
            cube('Ceiling light / Lantern diffuser',(cx,cy,z+height/2),(width-.06,depth-.06,height-.06),LED,.025)
            for zz in (z+.025,z+height-.025):
                for yy in (y1+.015,y2-.015):
                    cube('Ceiling light / Lantern frame',(cx,yy,zz),(width,.035,.035),DARKWOOD,.004)
                for xx in (x1+.015,x2-.015):
                    cube('Ceiling light / Lantern frame',(xx,cy,zz),(.035,depth,.035),DARKWOOD,.004)
            for xx in (x1+.015,x2-.015):
                for yy in (y1+.015,y2-.015):
                    rod('Ceiling light / Lantern corner',(xx,yy,z),(xx,yy,z+height),.012,DARKWOOD,8)
            rod('Ceiling light / Lantern suspension',(cx,cy,z+height),(cx,cy,floor+2.99),.008,METAL,8)
        elif kind=='curtain':
            for i in range(8):
                if width>=depth:
                    center=(x1+(i+.5)*width/8,cy+(.013 if i%2 else -.013),z+height/2)
                    size=(width/8,depth,height)
                else:
                    center=(cx+(.013 if i%2 else -.013),y1+(i+.5)*depth/8,z+height/2)
                    size=(width,depth/8,height)
                cube('Curtain pleat / '+name,center,size,mat,.008)
            a,b=((x1-.04,cy,z+height+.04),(x2+.04,cy,z+height+.04)) if width>=depth else ((cx,y1-.04,z+height+.04),(cx,y2+.04,z+height+.04))
            rod('Curtain rod',a,b,.012,DARKWOOD)
        elif kind=='pendant':
            cube('Ceiling light / '+name,(cx,cy,z+height/2),(width,depth,height),DARKWOOD,.01)
            cube('Ceiling light / pendant diffuser',(cx,cy,z-.008),(width-.04,depth-.02,.015),LED)
            for x in (x1+.12,x2-.12):rod('Ceiling light / pendant cable',(x,cy,z+height),(x,cy,floor+2.98),.006,METAL,8)
        elif kind=='grabbar':
            rod('Bathroom grab rail / '+name,(cx,y1,z),(cx,y2,z),.018,METAL)
            for y in (y1+.04,y2-.04):rod('Grab rail stand-off',(x1,y,z),(cx,y,z),.012,METAL)
        elif kind=='bedbox':
            if width<depth:
                a=(x2+.07,cy,z+height/2);size=(.012,depth-.04,height)
            else:
                a=(cx,y1-.105,z+height/2);size=(width-.04,.012,height)
            cube('Lift bedbox side panel',a,size,PALEWOOD,.005)
            cube('Lift bedbox recessed grip',(a[0]+(.004 if width<depth else 0),a[1]-(.004 if width>depth else 0),a[2]+.035),
                 (.006,.16,.018) if width<depth else (.16,.006,.018),DARKWOOD)
        elif kind=='bench':
            cube('Shower seat / '+name,(cx,cy,z+height/2),(width,depth,height),PALEWOOD,.015)
            for x in (x1+.05,x2-.05):
                for y in (y1+.05,y2-.05):
                    rod('Shower seat leg',(x,y,floor+.03),(x,y,z),.016,METAL)
        else:
            prefix='Ceiling light / ' if kind=='lightstrip' else 'Decoration / '
            cube(prefix+name,(cx,cy,z+height/2),(width,depth,height),mat,.008 if kind!='lightstrip' else 0)
            if kind=='wallcabinet':
                for i in range(1,4):
                    if width>depth:
                        cube('Cabinet door reveal',(x1+width*i/4,y1-.004,z+height/2),(.008,.01,height-.04),DARKWOOD)
                    else:
                        cube('Cabinet door reveal',(x1-.004,y1+depth*i/4,z+height/2),(.01,.008,height-.04),DARKWOOD)
        for new in set(bpy.data.objects)-before:
            new['fixtureId']=f'decor-{group}-{index}'
            new['roomId']=f'{group}-{obj["room"]}'
            new['fixtureKind']='decor-'+kind
            new['decorKind']=kind
            new['sectionable']=kind in ('panel','curtain','sheer','slats','wallcabinet','lightstrip')

# Second finish layer: skirting, casings, downlights, bedding, rugs, art,
# plants and practical lamps.  Kept in one module so the room plan data stays
# untouched and the GLB/3D viewer receives exactly what the renders show.
import interior_details


def _set_detail_group(name):
    global CURRENT
    CURRENT = name


_detail_materials = {key: globals()[key] for key in (
    "WOOD", "PALEWOOD", "DARKWOOD", "PLASTER", "FLOOR", "LIGHTFLOOR", "COUNTER",
    "METAL", "MIRROR", "ACCENT", "LED", "FABRIC", "BEDDING", "WATER", "CURTAIN",
    "INK_ART", "SHEER", "GLASS", "STONE", "TILE", "OAK", "LEAVES")}
_detail_materials.update(material=material, textured_material=textured_material)
interior_details.build(dict(
    cube=cube, rod=rod, mesh=mesh, set_group=_set_detail_group, walls=walls,
    rooms=room_specs(), furniture=furnishings(), **_detail_materials))

CURRENT = "Attic"
slab(REAR, 6.9, "Second-floor top plate / attic floor")
cube("Attic inspection hatch", (6, 17.6, 6.81), (.75, .75, .02), WOOD)
for cy in (14.52, 24.28):
    cube("Attic knee wall", (6, cy, 7.45), (10.8, .24, 1.1), PLASTER)
for cx in (.72, 11.28):
    cube("Attic side knee wall", (cx, 19.4, 7.45), (.24, 10.0, 1.1), PLASTER)
    xs = (cx-.12, cx+.12)
    vertices = [(x, y, z) for x in xs for y, z in ((14.4, 8), (24.4, 8), (19.4, 10.2))]
    mesh("Gable", vertices, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)], PLASTER)
    out = cx+(.135 if cx > 6 else -.135)
    cube("Dark ventilation recess", (out, 19.4, 8.85), (.03, 1.4, .8), DARKWOOD)
    for i in range(8):
        cube("Gable ventilation louvre", (out+(.02 if cx>6 else -.02), 19.4, 8.51+i*.095),
             (.045, 1.35, .035), WOOD)


def roof(bounds, wall_z, ridge_z, name):
    x1, y1, x2, y2 = bounds
    cy = (y1+y2)/2
    slope = (ridge_z-wall_z)/((y2-y1)/2)
    x1, x2, ya, yb = x1-.45, x2+.45, y1-.45, y2+.45
    verts, faces, mids = [], [], []
    cols = math.ceil((x2-x1)/.2)
    dx = (x2-x1)/cols
    for sign, ye in ((-1, ya), (1, yb)):
        span = abs(ye-cy)
        rows = math.ceil(span/.285)
        for col in range(cols):
            for row in range(rows):
                base = len(verts)
                for s in (0, 1):
                    distance = (row+s)*span/rows
                    yy = cy+sign*distance
                    for j in range(7):
                        xx = x1+(col+j/6)*dx
                        # A shallow barrel profile and overlapping lower lip make real tile geometry.
                        zz = ridge_z-slope*distance+.037*math.sin(math.pi*j/6)+(.018 if s else .0)
                        verts.append((xx, yy, zz))
                for j in range(6):
                    faces.append((base+j, base+j+1, base+7+j+1, base+7+j))
                    mids.append((col*3+row)%6)
    obj = mesh(name+" glazed tiles", verts, faces, None)
    for mat in ROOFMATS:
        obj.data.materials.append(mat)
    for poly, mi in zip(obj.data.polygons, mids):
        poly.material_index, poly.use_smooth = mi, True
    eave_z = ridge_z-slope*abs(yb-cy)
    for ye in (ya, yb):
        cube(name+" timber fascia", ((x1+x2)/2, ye, eave_z-.1), (x2-x1, .14, .16), DARKWOOD)
    rod(name+" ridge cap", (x1-.04, cy, ridge_z+.06), (x2+.04, cy, ridge_z+.06), .10, ROOFMATS[3], 20)
    for xx in (x1, x2):
        for ye in (ya, yb):
            rod(name+" verge cap", (xx, cy, ridge_z+.055), (xx, ye, eave_z+.055), .065, ROOFMATS[2])
    return obj


CURRENT = "Roofs"
roof(REAR, 8, 10.2, "Rear")
CURRENT = "Terrace"
slab(FRONT,3.6,"Accessible flat roof terrace")
for index,bounds in enumerate(BRIDGES):
    slab(bounds,3.6,"West bridge" if index==0 else "East bridge")
for a,b in [((.7,.7),(11.3,.7)),((.7,.7),(.7,6.6)),((11.3,.7),(11.3,6.6)),
            ((1.84,6.5),(10.16,6.5)),((.65,6.6),(.65,14.35)),((1.75,6.6),(1.75,14.35)),
            ((10.25,6.6),(10.25,14.35)),((11.35,6.6),(11.35,14.35))]:
    rail(a,b,3.6)
CURRENT='BridgeCanopy'
cx1,cy1,cx2,cy2=EAST_CANOPY['bounds']
roof_west=EAST_CANOPY['roof_level'];roof_east=roof_west-EAST_CANOPY['fall']
mesh('East covered bridge roof',[(cx1,cy1,roof_west),(cx2,cy1,roof_east),(cx2,cy2,roof_east),(cx1,cy2,roof_west),
     (cx1,cy1,roof_west-.06),(cx2,cy1,roof_east-.06),(cx2,cy2,roof_east-.06),(cx1,cy2,roof_west-.06)],
     [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],PLASTER)
for x in EAST_CANOPY['post_x']:
    top=roof_west-EAST_CANOPY['fall']*(x-cx1)/(cx2-cx1)-.06
    cube('East canopy edge beam',(x,(cy1+cy2)/2,top-.06),(.06,cy2-cy1,.12),METAL)
    for y in EAST_CANOPY['post_y']:
        height=top-.12-3.6
        cube('East canopy post',(x,y,3.6+height/2),(EAST_CANOPY['post_size'],EAST_CANOPY['post_size'],height),METAL)
for y in EAST_CANOPY['post_y']:
    rod('East canopy crossbeam',(10.25,y,6.46),(11.35,y,6.43),.03,METAL)
for y in (8,10.5,13):
    cube('Ceiling light / East covered bridge',(10.8,y,6.28),(.28,.18,.045),LED,.01)
rod('East canopy gutter',(11.49,cy1,6.56),(11.49,cy2,6.56),.035,METAL)
rod('East canopy gutter outlet',(11.49,13.95,6.56),(11.58,13.95,6.56),.035,METAL)
rod('East canopy rain pipe',(11.58,13.95,.24),(11.58,13.95,6.56),.035,METAL)
for index,(a,b) in enumerate(zip(KITCHEN_EXHAUST['points'],KITCHEN_EXHAUST['points'][1:])):
    CURRENT='Front' if index<2 else 'Terrace'
    duct=rod('Independent kitchen exhaust',a,b,KITCHEN_EXHAUST['diameter']/2,METAL,32)
    duct['kitchenExhaust']=True
x,y,z=KITCHEN_EXHAUST['points'][-1]
CURRENT='Terrace'
cube('Kitchen exhaust weather cap',(x,y,z+.10),(.38,.38,.07),METAL,.025)
cube('Kitchen exhaust service access',(x+.105,y,2.40),(.025,.17,.24),METAL,.01)
CURRENT='Site'
for x in (1.2,10.8):
    for y in (9,12):cube("Bridge support - indicative",(x,y,1.71),(.18,.18,3.42),DARKWOOD)
for x in (11.76,13.98):cube("Stair support - indicative",(x,21.52,.885),(.2,.2,1.77),PLASTER)
CURRENT="Terrace"
for i in range(9):
    cube("Terrace tile seam",(1.2+i*1.05,3.6,3.606),(.008,5.75,.008),STONE)
CURRENT = "Garden"
table(9.3, 10.5, 0, 1.3, .8)
for x,y in [(8.75,9.8),(9.7,9.8),(8.75,11.2),(9.7,11.2)]:
    chair(x,y,0)
def laundry_machine(machine,base=0,front='east'):
    a,b,c,d=machine['bounds'];cx,cy=(a+c)/2,(b+d)/2;bottom=base+machine['z'];height=machine['height']
    start=set(bpy.data.objects)
    cube(machine['name'],(cx,cy,bottom+height/2),(c-a,d-b,height),WATER,.028)
    if front=='east':
        rod(machine['name']+' circular door',(c+.005,cy,bottom+height*.48),(c+.030,cy,bottom+height*.48),min(d-b,height)*.32,SCREEN,40)
        cube(machine['name']+' controls',(c+.014,cy,bottom+height-.09),(.022,d-b-.08,.08),METAL,.006)
    else:
        rod(machine['name']+' circular door',(cx,b-.005,bottom+height*.48),(cx,b-.030,bottom+height*.48),min(c-a,height)*.32,SCREEN,40)
        cube(machine['name']+' controls',(cx,b-.014,bottom+height-.09),(c-a-.08,.022,.08),METAL,.006)
    for obj in set(bpy.data.objects)-start:obj['laundryMachineId']=machine['id'];obj['laundryKind']=machine['kind']

def laundry_basin(bounds,base):
    a,b,c,d=bounds
    cube('Laundry basin bottom',((a+c)/2,(b+d)/2,base+.73),(c-a,d-b,.035),WATER,.012)
    for x in (a,c):cube('Laundry basin side',(x,(b+d)/2,base+.83),(.025,d-b,.20),WATER,.008)
    for y in (b,d):cube('Laundry basin end',((a+c)/2,y,base+.83),(c-a,.025,.20),WATER,.008)

before_laundry=set(bpy.data.objects)
lx1,ly1,lx2,ly2=COURTYARD_LAUNDRY['bounds']
cube('Laundry floor tile',((lx1+2.70)/2,(ly1+ly2)/2,.015),(2.70-lx1,ly2-ly1,.025),TILE)
for machine in COURTYARD_LAUNDRY['machines']:laundry_machine(machine)
cube('Stacking appliance support',(1.17,7.09,.915),(.60,.62,.04),METAL,.005)
cube('Laundry sink lower storage',(1.17,8.42,.34),(.60,.62,.63),WOOD,.014)
sx1,sy1,sx2,sy2=COURTYARD_LAUNDRY['sink']
for a,b,c,d in [(lx1,7.43,lx2,sy1),(lx1,sy2,lx2,ly2),(lx1,sy1,sx1,sy2),(sx2,sy1,lx2,sy2)]:
    cube('Laundry quartz worktop',((a+c)/2,(b+d)/2,.92),(c-a,d-b,.05),COUNTER,.005)
laundry_basin(COURTYARD_LAUNDRY['sink'],0)
rod('Laundry tap riser',(.88,8.4,.94),(.88,8.4,1.19),.015,METAL)
rod('Laundry tap spout',(.88,8.4,1.19),(1.10,8.4,1.19),.015,METAL)
cube('Laundry splashback',(.813,8.09,1.18),(.025,1.32,.48),COUNTER)
cube('Laundry upper storage',(1.01,8.09,1.92),(.34,1.32,.62),WOOD,.018)
cube('Laundry cabinet door joint',(1.185,8.09,1.92),(.01,.009,.56),DARKWOOD)
cube('Laundry task light',(1.15,8.09,1.59),(.035,1.22,.025),LED)
for part in set(bpy.data.objects)-before_laundry:
    part['fixtureId']='courtyard-laundry';part['fixtureKind']='laundry'
    part['sectionable']=part.name.startswith(('Laundry upper','Laundry cabinet','Laundry splash'))
x,y,z=COURTYARD_LAUNDRY['drain'];cube('Laundry trapped waste drain',(x,y,z),(.12,.12,.015),METAL)
before=set(bpy.data.objects)
a,b,c,d=COURTYARD_LAUNDRY['drying_bounds'];h=COURTYARD_LAUNDRY['drying_height']
for y in (b+.10,d-.10):
    cube('Lift drying rack ceiling unit',((a+c)/2,y,3.32),(c-a,.10,.10),WATER,.015)
    for x in (a,c):rod('Lift drying rack suspension',(x,y,h),(x,y,3.27),.006,METAL,8)
for x in (a,(a+c)/2,c):rod('Lift drying rail',(x,b,h),(x,d,h),.016,METAL,16)
for y in (b,d):rod('Lift drying end brace',(a,y,h),(c,y,h),.016,METAL,16)
cube('Courtyard drying towel',(1.35,10.4,h-.28),(.02,.60,.56),BEDDING,.01)
for part in set(bpy.data.objects)-before:part['fixtureId']='courtyard-drying';part['fixtureKind']='drying-rack'

CURRENT='Pavilion'
a,b,c,d=TERRACE_PAVILION['roof_bounds'];top=TERRACE_PAVILION['roof_level'];floor=3.6
for x,y in TERRACE_PAVILION['posts']:
    cube('Pavilion pale post',(x,y,(floor+top-.20)/2),(.10,.10,top-.20-floor),PAVILIONPOST,.008)
for y in (1.60,5.60):cube('Pavilion cross beam',(3.15,y,top-.20),(2.50,.10,.18),PALEWOOD,.01)
for x in (1.95,4.35):cube('Pavilion longitudinal beam',(x,3.60,top-.20),(.10,4.10,.18),PALEWOOD,.01)
for y in (2.5,4.7):cube('Ceiling light / Pavilion', (3.15,y,top-.32),(.30,.18,.035),LED,.01)
rod('Pavilion gutter',(1.76,b,top-.10),(1.76,d,top-.10),.035,METAL)
rod('Pavilion rain downpipe',(1.78,5.58,3.66),(1.78,5.58,top-.10),.035,METAL)
drying=TERRACE_DRYING
drying_start=set(bpy.data.objects)
ra,rb,rc,rd=drying['bounds'];raised=drying['raised'];cable_top=drying['cable_top']
cube('Drying hoist mounting spreader',(3.15,3.20,6.235),(2.30,.90,.045),METAL,.006)
cube('Motorized drying ceiling unit',drying['motor'],(1.10,.82,.12),WATER,.025)
cube('Motorized drying integrated light',(3.15,3.20,6.082),(.80,.48,.018),LED,.006)
cube('Motorized drying wall control',drying['control'],(.055,.10,.14),WATER,.008)
lift=bpy.data.objects.new('Motorized drying lift',None);COLS[CURRENT].objects.link(lift)
lift.location=(0,0,raised);lift['motorizedDryingId']='pavilion-lift';lift['liftTravel']=raised-drying['lowered'];lift['floorGroup']=CURRENT
before=set(bpy.data.objects)
for x in (ra,(ra+rc)/2,rc):rod('Motorized drying rail',(x,rb,raised),(x,rd,raised),.018,METAL,16)
for y in (rb,rd):rod('Motorized drying end brace',(ra,y,raised),(rc,y,raised),.022,METAL,16)
rod('Motorized drying quilt rail',(ra,rb+.10,raised-.17),(ra,rd-.10,raised-.17),.016,METAL,16)
cube('Motorized drying hanging sample',(rc,3.25,raised-.36),(.018,.70,.65),BEDDING,.008)
for part in set(bpy.data.objects)-before:
    part.parent=lift;part.matrix_parent_inverse=lift.matrix_basis.inverted()
    part['fixtureId']='pavilion-motorized-drying';part['fixtureKind']='drying-rack'
for x in (ra,rc):
    for y in (rb+.15,rd-.15):
        cable=bpy.data.objects.new('Motorized drying cable anchor',None);COLS[CURRENT].objects.link(cable)
        cable.location=(x,y,cable_top);cable['motorizedCable']=True;cable['cableLength']=cable_top-raised;cable['floorGroup']=CURRENT
        wire=rod('Motorized drying suspension',(x,y,raised),(x,y,cable_top),.004,METAL,8)
        wire.parent=cable;wire.matrix_parent_inverse=cable.matrix_basis.inverted()
        wire['fixtureId']='pavilion-motorized-drying';wire['fixtureKind']='drying-rack'
for y in (rb+.15,rd-.15):
    cube('Drying suspension beam',(3.15,y,6.20),(2.40,.055,.055),METAL,.004)
    for x in (ra,rc):rod('Drying beam suspension bracket',(x,y,cable_top),(x,y,6.19),.012,METAL)
for part in set(bpy.data.objects)-drying_start:
    part['fixtureId']='pavilion-motorized-drying';part['fixtureKind']='drying-rack'
start=set(bpy.data.objects)
for machine in TERRACE_LAUNDRY['machines']:laundry_machine(machine,3.6,'south')
cube('Pavilion storage replaces upper washer',(2.50,5.25,4.04),(.64,.54,.82),PALEWOOD,.016)
lx1,ly1,lx2,ly2=TERRACE_LAUNDRY['bounds'];sx1,sy1,sx2,sy2=TERRACE_LAUNDRY['sink']
for x1,y1,x2,y2 in [(lx1,ly1,sx1,ly2),(sx2,ly1,lx2,ly2),(sx1,ly1,sx2,sy1),(sx1,sy2,sx2,ly2)]:
    cube('Upper laundry quartz worktop',((x1+x2)/2,(y1+y2)/2,4.54),(x2-x1,y2-y1,.05),COUNTER,.006)
cube('Upper laundry sink cabinet',(3.54,5.25,3.94),(1.08,.54,.63),PALEWOOD,.016)
laundry_basin(TERRACE_LAUNDRY['sink'],3.6)
cube('Upper laundry splashback',(3.10,5.59,4.46),(2.12,.055,1.66),PLASTER,.012)
for x in (2.065,4.135):cube('Upper laundry side screen',(x,5.25,4.36),(.055,.69,1.46),PLASTER,.01)
rod('Upper laundry tap',(3.30,5.51,4.55),(3.30,5.51,4.80),.015,METAL)
rod('Upper laundry tap spout',(3.30,5.51,4.80),(3.30,5.31,4.80),.015,METAL)
cube('Upper laundry shelf',(3.5,5.47,5.18),(1.0,.23,.04),PALEWOOD,.012)
for part in set(bpy.data.objects)-start:part['fixtureId']='terrace-laundry';part['fixtureKind']='laundry'
x,y,z=TERRACE_LAUNDRY['drain'];cube('Upper laundry trapped drain',(x,y,z),(.12,.12,.015),METAL)
CURRENT='Rear2'
start=set(bpy.data.objects)
for machine in UPPER_LAUNDRY['machines']:laundry_machine(machine,3.6,'south')
a,b,c,d=UPPER_LAUNDRY['bounds']
cube('Hall laundry countertop',((a+c)/2,(b+d)/2,4.54),(c-a,d-b,.045),COUNTER,.008)
cube('Hall laundry vibration pad',(3.68,16.015,3.625),(.62,.67,.02),STONE,.006)
cube('Hall laundry waterproof tile',((a+c)/2,15.53,3.609),(c-a,1.78,.018),TILE)
cube('Hall laundry removable service panel',(3.68,16.416,4.82),(.66,.025,.40),PALEWOOD,.006)
cube('Hall laundry splashproof socket',UPPER_LAUNDRY['socket'],(.04,.09,.09),WATER,.005)
rod('Hall laundry water isolation valve',(3.34,16.22,4.72),(3.34,16.29,4.72),.025,METAL)
rod('Hall laundry drain standpipe',(3.34,16.25,3.70),UPPER_LAUNDRY['standpipe'],.025,METAL)
x,y,z=UPPER_LAUNDRY['drain'];cube('Hall laundry trapped floor drain',(x,y,z),(.10,.10,.015),METAL)
for part in set(bpy.data.objects)-start:part['fixtureId']='upper-hall-laundry';part['fixtureKind']='laundry';part['roomId']='rear2-8'
a,b,c,d=TERRACE_PAVILION['roof_bounds']
CURRENT='PavilionRoof'
mesh('Pavilion sloping roof',[(a,b,top),(c,b,top+.06),(c,d,top+.06),(a,d,top),
     (a,b,top-.09),(c,b,top-.03),(c,d,top-.03),(a,d,top-.09)],
     [(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],LIGHTROOF)
cube('Pavilion warm soffit',((a+c)/2,(b+d)/2,top-.09),(c-a-.12,d-b-.12,.025),PALEWOOD)
CURRENT='Garden'

for x,y in [(10.8,7.4),(1.15,13.3)]:
    bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=.24, radius2=.29, depth=.45, location=(x,y,.225))
    move(bpy.context.object,"Clay planter",STONE)
    for i in range(7):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=.16, location=(x+random.uniform(-.2,.2),y+random.uniform(-.2,.2),.6+random.random()*.2))
        move(bpy.context.object,"Planter foliage",LEAVES[i%5])

# Permanent air conditioning equipment; route overlays are separate from the architectural view.
hvac=hvac_layout()
for unit in hvac["units"]:
    CURRENT={"front":"Front","rear1":"Rear1","rear2":"Rear2"}[unit["floor"]]
    x,y,z=unit["indoor"]
    cube(unit["id"]+" Indoor AC",(x,y,z),(.2,.9,.28),WATER,.035)
    cube("AC indoor outlet",(x+(.11 if unit["side"]=="west" else -.11),y,z-.06),(.018,.77,.045),STONE)
    ox,oy,oz=unit["outdoor"]
    side_mount=unit["floor"]=="front"
    machine=cube(unit["id"]+" Outdoor AC",(ox,oy,oz),(.38,.9,.65) if side_mount else (.9,.38,.65),WATER,.025)
    machine["acOutdoor"]=True
    if side_mount:
        for i in range(9):cube("Outdoor AC grille",(ox-.202,oy-.35+i*.085,oz),(.025,.018,.48),STONE)
        rod("Outdoor fan",(ox-.21,oy,oz),(ox-.225,oy,oz),.23,STONE,32)
    else:
        for i in range(9):cube("Outdoor AC grille",(ox-.35+i*.085,oy+.202,oz),(.018,.025,.48),STONE)
        rod("Outdoor fan",(ox,oy+.21,oz),(ox,oy+.225,oz),.23,STONE,32)
    cube("AC mount position",(ox,oy,oz-.38),(.5,1,.08) if side_mount else (1,.5,.08),STONE)

layout=engineering_layout(ROOMS,furnishings())
COLORS={"Structure":(.44,.23,.7),"electric":(.85,.42,.06),"cold":(.05,.34,.8),
        "hot":(.7,.08,.06),"waste":(.3,.13,.05),"rain":(.02,.46,.46),
        "refrigerant":(.65,.08,.5),"condensate":(.07,.55,.22)}
ENG_MATS={name:material("Diagram "+name,color,.5) for name,color in COLORS.items()}
def tag_engineering(obj,floor,identifier):
    obj["engineeringFloor"]=floor
    obj["engineeringId"]=identifier
    return obj
CURRENT="Structure"
for member in layout["members"]:
    tag_engineering(rod("Frame axis "+member["id"],member["a"],member["b"],.09,
                        ENG_MATS["Structure"],8),member["floor"],member["id"])
for route in layout["routes"]:
    CURRENT="Electrical" if route["system"]=="electric" else "Plumbing"
    for a,b in zip(route["points"],route["points"][1:]):
        tag_engineering(rod("Route "+route["id"],a,b,.026 if CURRENT=="Electrical" else .04,
                            ENG_MATS[route["system"]],8),route["floor"],route["id"])
for device in layout["devices"]:
    CURRENT="Electrical" if device["system"]=="electric" else "Plumbing"
    tag_engineering(cube(device["label"],device["point"],(.16,.16,.16),ENG_MATS[device["system"]]),device["floor"],device["id"])
    if device["type"]=="inspection":
        CURRENT="Site";x,y,_=device["point"]
        cube("Sewage inspection cover",(x,y,.055),(.48,.48,.08),STONE,.02)
# Only outlines describe the buried three-compartment tank; no wall or depth specification.
x1,y1,x2,y2=layout["septic"]["bounds"]
CURRENT="Plumbing"
for z in (-1.05,-.12):
    for a,b in [((x1,y1,z),(x2,y1,z)),((x2,y1,z),(x2,y2,z)),((x2,y2,z),(x1,y2,z)),((x1,y2,z),(x1,y1,z))]:
        tag_engineering(rod("Septic concept outline",a,b,.045,ENG_MATS["waste"],8),"site","septic")
for x in (x1,x1+(x2-x1)/3,x1+2*(x2-x1)/3,x2):
    for y in (y1,y2):tag_engineering(rod("Septic divider outline",(x,y,-1.05),(x,y,-.12),.03,ENG_MATS["waste"],8),"site","septic")
    tag_engineering(rod("Septic compartment line",(x,y1,-.12),(x,y2,-.12),.03,ENG_MATS["waste"],8),"site","septic")
CURRENT="Site"
for i in range(3):cube("Septic access lid %d"%(i+1),(x1+(i+.5)*(x2-x1)/3,y2-.42,.06),(.55,.55,.09),STONE,.025)
CURRENT="HVAC"
for unit in hvac["units"]:
    for kind in ("refrigerant","condensate"):
        for a,b in zip(unit[kind],unit[kind][1:]):
            if Vector(a)==Vector(b):continue
            tag_engineering(rod(unit["id"]+" "+kind,a,b,.025,ENG_MATS[kind],8),unit["floor"],unit["id"])

CURRENT = "Lights"
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device='CPU'
try:
    devices=bpy.context.preferences.addons['cycles'].preferences
    devices.compute_device_type='OPTIX';devices.get_devices()
    if any(device.type=='OPTIX' for device in devices.devices):
        for device in devices.devices:device.use=device.type=='OPTIX'
        scene.cycles.device='GPU'
except RuntimeError as error:
    print('Cycles GPU unavailable, retaining CPU:',error,flush=True)
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 6
scene.cycles.diffuse_bounces = 3
scene.cycles.glossy_bounces = 3
scene.render.threads_mode = "FIXED"
scene.render.threads = 14
scene.render.resolution_x = 2000
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.use_nodes = True
world = scene.world.node_tree
background = world.nodes.get("Background")
background.inputs["Strength"].default_value = .35
sky = world.nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA"
sky.sun_elevation = math.radians(40)
sky.sun_rotation = math.radians(220)
world.links.new(sky.outputs["Color"], background.inputs["Color"])
bpy.ops.object.light_add(type="AREA", location=(4,-3,16))
light = move(bpy.context.object,"Large soft fill")
light.data.energy, light.data.shape, light.data.size = 1700, "DISK", 12
light.rotation_euler = (Vector((6,12,3))-light.location).to_track_quat("-Z","Y").to_euler()
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = -1.2
scene.render.film_transparent = False
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0


def camera(name, position, target, lens=43, ortho=None):
    bpy.ops.object.camera_add(location=position)
    cam = move(bpy.context.object, name)
    cam.rotation_euler = (Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()
    cam.data.lens = lens
    cam.data.clip_end = 300
    if ortho:
        cam.data.type, cam.data.ortho_scale = "ORTHO", ortho
    return cam


cameras = {
    "01-aerial": camera("01 Aerial / southwest", (39,-36,34), (7,10,2.8), 48),
    "02-courtyard": camera("02 Courtyard looking north", (7.8,7.05,2.25), (6,17,3), 16),
    "03-entrance": camera("03 South entrance", (23,-23,12), (6,5,2.6), 45),
    "04-cutaway": camera("04 Ground floor cutaway", (33,-24,43), (7,10,1), ortho=44),
    "05-grand-gate": camera('05 Modern Chinese entrance',(10,-9,3.8),(6,.72,1.7),48),
    "06-entertainment-terrace": camera('06 Open entertainment and drying terrace',(17,-8,15),(6,3.8,3.9),42),
    "08-west-enclosed-wall": camera("08 West enclosed courtyard wall",(-18,8,7),(1,11,2.0),42),
    "09-east-enclosed-wall": camera('09 East enclosed courtyard wall',(29,8,7),(11,11,2),42),
    "10-courtyard-laundry": camera('10 Courtyard laundry',(7.0,11.0,3.5),(1.15,8.9,1.30),30),
    "11-terrace-pavilion": camera('11 Terrace pavilion and laundry',(9,-2,8),(3.1,3.5,4.6),40),
    "12-kitchen-appliances": camera('12 Kitchen appliances',(9.15,5.1,2.5),(10.4,2.1,1.1),19),
    "07-front-forecourt": camera('07 Open forecourt and right storage',(-9,-22,14),(7.5,-2.2,1.1),45),
}
scene.camera = cameras["01-aerial"]
scene["Design status"] = "Revision O / layout and interior renovation; width15.2m provisional; rear clearance5m confirmed / concept only"
scene["Interior finish revision"] = "2026-11-07 / furniture, joinery details and layered lighting"
scene["Wardrobe revision"] = "2026-11-07 / 3 five-column wardrobes with 15 independent hinged doors"
scene["Dimensions"] = "Metres; same source as drawings. Rear: 2 floors + ventilated attic."
scene["Stair"] = "20 x 0.165m; 2 flights; upper-floor opening retained."
scene.render.filepath = str(ROOT/"renders"/"01-aerial.png")
# Project local repeatable textures onto handmade meshes before GLB embedding.
for obj in scene.objects:
    if obj.type!='MESH' or not any(mat and mat.use_nodes and any(n.type=='TEX_IMAGE' for n in mat.node_tree.nodes) for mat in obj.data.materials):
        continue
    if obj.data.uv_layers:continue
    uv=obj.data.uv_layers.new(name='FinishUV')
    for polygon in obj.data.polygons:
        normal=polygon.normal
        axes=(0,1) if abs(normal.z)>.5 else (1,2) if abs(normal.x)>.5 else (0,2)
        for loop in polygon.loop_indices:
            point=obj.data.vertices[obj.data.loops[loop].vertex_index].co
            uv.data[loop].uv=(point[axes[0]],point[axes[1]])
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"model"/"courtyard-house.blend"))
mesh_count = sum(obj.type=="MESH" for obj in scene.objects)
assert mesh_count > 100
assert all(abs(obj.dimensions.z-3.3)<.001 for obj in scene.objects if obj.name.startswith("Porch timber post"))
report = {"version":"O","decoration_items":sum(len(v) for v in decoration().values()),"blender":bpy.app.version_string,"mesh_objects":mesh_count,"units":"m",
          "covered_entry":COVERED_ENTRY,"east_canopy":EAST_CANOPY,"site":SITE,"rear_bays":3,"front_bays":3,
          "levels":LEVELS,"stairs":{"risers":20,"riser":.165,"tread":.27,"bounds":STAIR["bounds"]},
          "occupants":6,"front_roof":"flat accessible terrace","bridge_width":1.2,"bridge_count":2,"stair_location":"enclosed east stairwell","roof_color":"red","views":list(cameras),"status":"Concept geometry; no structural checks"}
(ROOT/"model"/"model-report.json").write_text(json.dumps(report,indent=2))

# Export editable geometry plus a file://-safe embedded GLB payload.
import base64
for key,col in COLS.items():
    if key=="Lights":continue
    group=bpy.data.objects.new(key,None)
    col.objects.link(group)
    group["floorGroup"]=key
    for obj in list(col.objects):
        if obj!=group and obj.parent is None:
            obj.parent=group
bpy.ops.object.select_all(action="DESELECT")
for obj in scene.objects:
    if obj.type in ("MESH","EMPTY") and obj.name not in ("Surrounding terrain","South road"):
        obj.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/"model"/"courtyard-house.glb"),
    export_format="GLB",use_selection=True,export_extras=True,export_cameras=False,
    export_lights=False,export_yup=True,export_apply=True)
payload=base64.b64encode((ROOT/"model"/"courtyard-house.glb").read_bytes()).decode("ascii")
(ROOT/"model"/"scene-data.js").write_text("window.HOUSE_MODEL='"+payload+"';")
(ROOT/"model"/"design-data.js").write_text("window.HOUSE_DESIGN="+(ROOT/"model"/"design.json").read_text()+";")
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"model"/"courtyard-house.blend"))
for key in ("Structure","Electrical","Plumbing","HVAC"):
    COLS[key].hide_render=True
selected=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
for name,cam in cameras.items():
    if "no-render" in selected or (selected and name not in selected):continue
    for key in ("Roofs","Attic","Rear2","Terrace","StairShell2","StairRoof","EntryRoof","BridgeCanopy","OutbuildingRoof","Pavilion","PavilionRoof"):COLS[key].hide_render=name=="04-cutaway"
    for obj in scene.objects:
        if obj.get('decorKind') in ('cove','lantern'):obj.hide_render=name=='04-cutaway'
    effect_light=None
    if name=='12-kitchen-appliances':
        lamp=bpy.data.lights.new('Kitchen effect fill','AREA');lamp.energy=260;lamp.shape='DISK';lamp.size=2.0;lamp.color=(1,.9,.78)
        effect_light=bpy.data.objects.new('Kitchen effect fill',lamp);COLS['Lights'].objects.link(effect_light)
        effect_light.location=(9.2,3.6,3.05)
        effect_light.rotation_euler=(Vector((10.4,2.4,1.2))-effect_light.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=cam
    scene.render.filepath=str(ROOT/"renders"/(name+".png"))
    print("RENDER START",name,flush=True)
    bpy.ops.render.render(write_still=True)
    if effect_light:bpy.data.objects.remove(effect_light,do_unlink=True)
    print("RENDER DONE",name,flush=True)
for key,col in COLS.items():col.hide_render=key in ("Structure","Electrical","Plumbing","HVAC")
scene.camera=cameras["01-aerial"]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"model"/"courtyard-house.blend"))
print("MODEL AND RENDERS COMPLETE",flush=True)
