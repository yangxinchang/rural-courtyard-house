"""Interior finish and furniture detailing for the courtyard house model.

The shared plan data (design.py / interiors.py) is unchanged.  This module adds
the second layer a finished interior needs: skirting, door casings, recessed
downlights, upholstered headboards, layered bedding, rugs, artwork, plants,
styled tables and practical lamps.  Everything is built in the same Blender
scene, so the interactive 3D, the GLB and the effect renders stay one model.
"""
import math


class Finishes:
    """Material upgrades plus the extra finishes used by the detail layer."""

    def __init__(self, base):
        self.base = base
        self.wood = base["PALEWOOD"]
        self.warm_wood = base["WOOD"]
        self.darkwood = base["DARKWOOD"]
        self.plaster = base["PLASTER"]
        self.floor = base["FLOOR"]
        self.lightfloor = base["LIGHTFLOOR"]
        self.counter = base["COUNTER"]
        self.metal = base["METAL"]
        self.mirror = base["MIRROR"]
        self.accent = base["ACCENT"]
        self.led = base["LED"]
        self.fabric = base["FABRIC"]
        self.bedding = base["BEDDING"]
        self.water = base["WATER"]
        self.curtain = base["CURTAIN"]
        self.ink = base["INK_ART"]
        self.sheer = base["SHEER"]
        self.glass = base["GLASS"]
        self.stone = base["STONE"]
        self.tile = base["TILE"]
        self.oak = base["OAK"]
        self.leaves = base["LEAVES"]
        material = base["material"]
        textured = base["textured_material"]
        self.ceramic = material("Warm ceramic", (.87, .845, .79), .24)
        self.pot = material("Stoneware pot", (.32, .285, .245), .78)
        self.soil = material("Potting soil", (.14, .11, .075), .95)
        self.rug = textured("Wool rug", "linen.png", (.52, .47, .39), .95)
        self.rug_pale = textured("Pale wool rug", "linen.png", (.66, .615, .535), .95)
        self.boucle = textured("Boucle upholstery", "linen.png", (.74, .695, .60), .92)
        self.shade = material("Linen lamp shade", (.93, .875, .755), .9)
        shade = self.shade.node_tree.nodes.get("Principled BSDF")
        shade.inputs["Emission Color"].default_value = (1, .82, .58, 1)
        shade.inputs["Emission Strength"].default_value = .55
        self.branch = material("Dried branch", (.30, .235, .16), .85)
        self.brass = material("Brushed brass", (.46, .345, .19), .28, .8)
        self.blackmetal = material("Charcoal steel", (.045, .045, .042), .38, .75)
        self.towel = textured("Waffle towel", "linen.png", (.80, .755, .66), .95)
        self.throw = textured("Taupe linen throw", "linen.png", (.50, .425, .335), .96)

    def _bsdf(self, mat):
        return mat.node_tree.nodes.get("Principled BSDF")

    def _bump_from_image(self, mat, strength, distance):
        tree = mat.node_tree
        bsdf = self._bsdf(mat)
        source = next((node for node in tree.nodes if node.type == "TEX_IMAGE"), None)
        if not source:
            return
        bump = tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = strength
        bump.inputs["Distance"].default_value = distance
        tree.links.new(source.outputs["Color"], bump.inputs["Height"])
        tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    def _bump_noise(self, mat, scale, strength, distance):
        tree = mat.node_tree
        bsdf = self._bsdf(mat)
        tex = tree.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 6
        bump = tree.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = strength
        bump.inputs["Distance"].default_value = distance
        tree.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    def _roughness_noise(self, mat, low, high, scale):
        tree = mat.node_tree
        bsdf = self._bsdf(mat)
        ramp = tree.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = .20
        ramp.color_ramp.elements[1].position = .80
        ramp.color_ramp.elements[0].color = (low, low, low, 1)
        ramp.color_ramp.elements[1].color = (high, high, high, 1)
        tex = tree.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 3
        tree.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        tree.links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])

    def _tonal_shift(self, mat, amount, scale):
        tree = mat.node_tree
        bsdf = self._bsdf(mat)
        base = tuple(bsdf.inputs["Base Color"].default_value)[:3]
        tex = tree.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 2
        factor = tree.nodes.new("ShaderNodeMath")
        factor.operation = "MULTIPLY"
        factor.inputs[1].default_value = amount
        tree.links.new(tex.outputs["Fac"], factor.inputs[0])
        mix = tree.nodes.new("ShaderNodeMixRGB")
        mix.inputs["Color1"].default_value = (*base, 1)
        mix.inputs["Color2"].default_value = (base[0] * .955, base[1] * .94, base[2] * .905, 1)
        tree.links.new(factor.outputs["Value"], mix.inputs["Fac"])
        tree.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    def _insert_hue_sat(self, mat, saturation, value, hue_shift=.5):
        tree = mat.node_tree
        bsdf = self._bsdf(mat)
        source = next((node for node in tree.nodes if node.type == "TEX_IMAGE"), None)
        link = next((l for l in tree.links if l.to_socket == bsdf.inputs["Base Color"]), None)
        if not source or not link:
            return
        hue = tree.nodes.new("ShaderNodeHueSaturation")
        hue.inputs["Hue"].default_value = hue_shift
        hue.inputs["Saturation"].default_value = saturation
        hue.inputs["Value"].default_value = value
        tree.links.remove(link)
        tree.links.new(source.outputs["Color"], hue.inputs["Color"])
        tree.links.new(hue.outputs["Color"], bsdf.inputs["Base Color"])

    def _blend_with_color(self, mat, color, factor):
        tree = mat.node_tree
        bsdf = self._bsdf(mat)
        link = next((l for l in tree.links if l.to_socket == bsdf.inputs["Base Color"]), None)
        if not link:
            return
        source = link.from_socket
        mix = tree.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MIX"
        mix.inputs["Fac"].default_value = factor
        mix.inputs["Color2"].default_value = (*color, 1)
        tree.links.remove(link)
        tree.links.new(source, mix.inputs["Color1"])
        tree.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    def _multiply_color(self, mat, factor):
        tree = mat.node_tree
        bsdf = self._bsdf(mat)
        link = next((l for l in tree.links if l.to_socket == bsdf.inputs["Base Color"]), None)
        if not link:
            return
        source = link.from_socket
        mix = tree.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs["Fac"].default_value = 1.0
        mix.inputs["Color2"].default_value = (*factor, 1)
        tree.links.remove(link)
        tree.links.new(source, mix.inputs["Color1"])
        tree.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])

    def upgrade(self):
        self._bump_noise(self.plaster, 46, .28, .018)
        self._tonal_shift(self.plaster, .08, 3.0)
        self._insert_hue_sat(self.wood, .86, 1.10, hue_shift=.535)
        self._insert_hue_sat(self.oak, .82, 1.06, hue_shift=.53)
        self._multiply_color(self.floor, (.96, .95, .915))
        self._multiply_color(self.lightfloor, (1.0, .99, .96))
        self._multiply_color(self.tile, (.97, .965, .94))
        self._bump_from_image(self.wood, .16, .006)
        self._roughness_noise(self.wood, .36, .54, 9)
        self._bump_from_image(self.floor, .22, .004)
        self._roughness_noise(self.floor, .32, .56, 1.4)
        self._roughness_noise(self.counter, .15, .26, 4)
        self._bump_from_image(self.fabric, .32, .0015)
        self._bump_from_image(self.curtain, .18, .0015)
        self._roughness_noise(self.metal, .20, .34, 12)
        self._bump_from_image(self.rug, .40, .002)
        self._bump_from_image(self.boucle, .45, .0025)
        glass = self._bsdf(self.glass)
        glass.inputs["Roughness"].default_value = .045
        glass.inputs["Alpha"].default_value = .28
        if "IOR" in glass.inputs:
            glass.inputs["IOR"].default_value = 1.45
        glass.inputs["Base Color"].default_value = (.60, .72, .72, 1)
        sheer = self._bsdf(self.sheer)
        sheer.inputs["Alpha"].default_value = .12
        sheer.inputs["Roughness"].default_value = .9
        shade = self._bsdf(self.shade)
        shade.inputs["Emission Strength"].default_value = .55


class Details:
    def __init__(self, ctx):
        self.cube = ctx["cube"]
        self.rod = ctx["rod"]
        self.plane = ctx["mesh"]
        self.enter = ctx["set_group"]
        self.rooms = {room["id"]: room for room in ctx["rooms"]}
        self.furniture = ctx["furniture"]
        walls = ctx["walls"]
        self.walls = walls
        self.F = Finishes(ctx)

    # -- primitives -------------------------------------------------------
    def box(self, name, x1, y1, x2, y2, z, height, mat, bevel=.004, tag=None):
        obj = self.cube(name, ((x1 + x2) / 2, (y1 + y2) / 2, z + height / 2),
                        (abs(x2 - x1), abs(y2 - y1), height), mat, bevel)
        if tag:
            obj["decorKind"] = tag
        return obj

    def cyl(self, name, x, y, z1, z2, radius, mat, vertices=20, tag=None):
        obj = self.rod(name, (x, y, z1), (x, y, z2), radius, mat, vertices)
        if tag:
            obj["decorKind"] = tag
        return obj

    def cone(self, name, x, y, z, radius_bottom, radius_top, height, mat, segments=24):
        vertices = []
        for zz, radius in ((0, radius_bottom), (height, radius_top)):
            for index in range(segments):
                angle = index * math.tau / segments
                vertices.append((x + radius * math.cos(angle), y + radius * math.sin(angle), z + zz))
        faces = [(i, (i + 1) % segments, (i + 1) % segments + segments, i + segments)
                 for i in range(segments)]
        return self.plane(name, vertices, faces, mat)

    def lamp(self, x, y, z, height=.52, energy=9, shade_radius=.14, name="table"):
        self.cyl("Lamp base " + name, x, y, z, z + .022, .072, self.F.blackmetal, 24)
        self.cyl("Lamp stem " + name, x, y, z + .02, z + height - .12, .011, self.F.brass, 16)
        self.cone("Lamp shade " + name, x, y, z + height - .17, shade_radius, shade_radius * .64,
                  .19, self.F.shade)
        bulb = self.cyl("Lamp bulb " + name, x, y, z + height - .18, z + height - .13, .038,
                        self.F.led, 16)
        bulb["lampWatt"] = energy

    def plant(self, x, y, z, height=1.15, pot_radius=.16):
        self.cyl("Plant pot", x, y, z, z + .32, pot_radius, self.F.pot, 24)
        self.cyl("Plant pot rim", x, y, z + .32, z + .345, pot_radius * 1.04, self.F.pot, 24)
        self.cyl("Potting soil", x, y, z + .335, z + .352, pot_radius * .92, self.F.soil, 20)
        stems = ((.00, .00, 1.0), (.06, .05, .80), (-.05, .04, .72), (.02, -.06, .90))
        for index, (dx, dy, scale) in enumerate(stems):
            top = z + .34 + (height - .34) * scale
            lean_x, lean_y = x + dx * 1.6, y + dy * 1.6
            self.rod("Plant stem", (x + dx * .4, y + dy * .4, z + .34), (lean_x, lean_y, top),
                     .011, self.F.branch, 8)
            for leaf in range(5):
                angle = leaf * math.tau / 5 + index * .9
                radius = .07 + .045 * (leaf % 3)
                lx = lean_x + radius * math.cos(angle)
                ly = lean_y + radius * math.sin(angle)
                lz = top - .06 - leaf * .11
                blade = self.cube("Plant leaf", (lx, ly, lz), (.145, .010, .062),
                                  self.F.leaves[(index + leaf) % len(self.F.leaves)], .028)
                blade.rotation_euler.z = angle
                blade.rotation_euler.y = math.radians(-26 + leaf * 13)
                blade.rotation_euler.x = math.radians(8 - leaf * 4)

    def vase(self, x, y, z, height=.30, material=None):
        mat = material or self.F.ceramic
        self.cyl("Vase body", x, y, z, z + height * .60, .072, mat, 24)
        self.cyl("Vase shoulder", x, y, z + height * .60, z + height * .84, .052, mat, 24)
        self.cyl("Vase neck", x, y, z + height * .84, z + height, .026, mat, 20)
        for index in range(3):
            angle = index * 2.1 + .3
            top = (x + .09 * math.cos(angle), y + .09 * math.sin(angle), z + height + .24)
            self.rod("Vase branch", (x, y, z + height - .02), top, .004, self.F.branch, 6)
            self.cyl("Vase seed head", top[0], top[1], top[2], top[2] + .05, .012,
                     self.F.branch, 8)

    def books(self, x, y, z, count=3, length=.24):
        for index in range(count):
            self.box("Stacked book", x - length / 2 + .012 * index, y - .15 + .012 * index,
                     x + length / 2 - .012 * index, y + .15 - .012 * index,
                     z + index * .034, .030,
                     self.F.boucle if index % 2 else self.F.fabric, .002)

    def bowl(self, x, y, z, radius=.14):
        mat = self.F.ceramic
        self.cyl("Bowl foot", x, y, z, z + .014, radius * .55, mat, 24)
        for index in range(3):
            self.cyl("Bowl ring", x, y, z + .014 + index * .021, z + .035 + index * .021,
                     radius * (1 - index * .22), mat, 24)
        for index in range(3):
            angle = index * 2.1 + .4
            self.cyl("Fruit", x + .05 * math.cos(angle), y + .05 * math.sin(angle), z + .05,
                     z + .115, .036, self.F.leaves[(index + 1) % len(self.F.leaves)], 16)

    def cushion(self, x, y, z, width=.42, height=.40, mat=None, turn=12):
        obj = self.box("Loose cushion", x - width / 2, y - .09, x + width / 2, y + .09, z,
                       height, mat or self.F.boucle, .07)
        obj.rotation_euler.z = math.radians(turn)
        return obj

    def draped_throw(self, foot_x, inward, y1, y2, z):
        """Loose throw folded over the foot of the bed with a soft hanging edge."""
        ny, top_n = 18, 6
        verts, faces = [], []
        for i in range(top_n + 1):
            for j in range(ny + 1):
                xx = foot_x - inward * .44 * (1 - i / top_n)
                yy = y1 + (y2 - y1) * j / ny
                zz = z + .050 + .010 * math.sin(j * .85 + i * .6) + .004 * math.sin(i * 1.9)
                verts.append((xx, yy, zz))
        for i in range(top_n):
            for j in range(ny):
                a = i * (ny + 1) + j
                faces.append((a, a + 1, a + ny + 2, a + ny + 1))
        flap_n = 6
        base = len(verts)
        for i in range(flap_n + 1):
            for j in range(ny + 1):
                xx = foot_x + inward * (.004 + .012 * i / flap_n) + .010 * math.sin(j * .8)
                yy = y1 + (y2 - y1) * j / ny
                zz = z + .050 - .36 * i / flap_n + .004 * math.sin(j * .7 + i * .5)
                verts.append((xx, yy, zz))
        for i in range(flap_n):
            for j in range(ny):
                a = base + i * (ny + 1) + j
                faces.append((a, a + 1, a + ny + 2, a + ny + 1))
        obj = self.plane("Draped bed throw", verts, faces, self.F.throw)
        self.rod("Bed throw fold roll", (foot_x - inward * .44, y1 + .04, z + .062),
                 (foot_x - inward * .44, y2 - .04, z + .062), .032, self.F.throw, 12)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        return obj

    def rug(self, x1, y1, x2, y2, z, mat=None, border=True):
        z = z + .008
        self.box("Woven rug", x1, y1, x2, y2, z, .016, mat or self.F.rug, .004)
        if border:
            self.box("Rug border", x1 + .09, y1 + .09, x2 - .09, y1 + .12, z + .012, .003,
                     self.F.rug_pale, 0)
            self.box("Rug border", x1 + .09, y2 - .12, x2 - .09, y2 - .09, z + .012, .003,
                     self.F.rug_pale, 0)
            self.box("Rug border", x1 + .09, y1 + .09, x1 + .12, y2 - .09, z + .012, .003,
                     self.F.rug_pale, 0)
            self.box("Rug border", x2 - .12, y1 + .09, x2 - .09, y2 - .09, z + .012, .003,
                     self.F.rug_pale, 0)

    def art(self, cx, cy, z, width, height, axis, facing, name="Framed artwork"):
        if axis == "x":
            self.box(name + " frame", cx - .012, cy - width / 2, cx + .012, cy + width / 2,
                     z, height, self.F.darkwood, .004)
            face = cx + facing * .014
            verts = [(face, cy - width / 2 + .04, z + .04), (face, cy + width / 2 - .04, z + .04),
                     (face, cy + width / 2 - .04, z + height - .04),
                     (face, cy - width / 2 + .04, z + height - .04)]
        else:
            self.box(name + " frame", cx - width / 2, cy - .012, cx + width / 2, cy + .012,
                     z, height, self.F.darkwood, .004)
            face = cy + facing * .014
            verts = [(cx - width / 2 + .04, face, z + .04), (cx + width / 2 - .04, face, z + .04),
                     (cx + width / 2 - .04, face, z + height - .04),
                     (cx - width / 2 + .04, face, z + height - .04)]
        picture = self.plane(name, verts, [(0, 1, 2, 3)], self.F.ink)
        uv = picture.data.uv_layers.new(name="ArtUV")
        for loop, value in zip(picture.data.polygons[0].loop_indices,
                               ((0, 0), (1, 0), (1, 1), (0, 1))):
            uv.data[loop].uv = value
        return picture

    # -- architectural layer ---------------------------------------------
    def skirting(self, room):
        if room["kind"] == "stair":
            return
        x1, y1, x2, y2 = room["inner"]
        z = room["floor"]
        wet = room["kind"] == "wet"
        mat = self.F.tile if wet else self.F.wood
        height = .085 if wet else .075
        thick = .014
        for side in ("s", "n", "w", "e"):
            horizontal = side in ("s", "n")
            line = (y1 - .12 if side == "s" else y2 + .12) if horizontal else (x1 - .12 if side == "w" else x2 + .12)
            face = (y1 if side == "s" else y2) if horizontal else (x1 if side == "w" else x2)
            start, end = (x1, x2) if horizontal else (y1, y2)
            gaps = []
            for wall in self.walls(room["group"]):
                wall_horizontal = abs(wall["a"][1] - wall["b"][1]) < 1e-6
                if wall_horizontal != horizontal:
                    continue
                if abs((wall["a"][1] if horizontal else wall["a"][0]) - line) > .02:
                    continue
                for op in wall["openings"]:
                    if op["sill"] > .001 or op["kind"] not in ("door", "passage"):
                        continue
                    a = (wall["a"][0] if horizontal else wall["a"][1]) + op["offset"]
                    gaps.append((a, a + op["width"]))
            cursor = start
            segments = []
            for a, b in sorted(gaps):
                a, b = max(a, start), min(b, end)
                if b <= start or a >= end or b <= a:
                    continue
                if a > cursor:
                    segments.append((cursor, a))
                cursor = max(cursor, b)
            if cursor < end:
                segments.append((cursor, end))
            for a, b in segments:
                if b - a < .05:
                    continue
                if horizontal:
                    offset = .007 if side == "s" else -.007
                    self.box("Wall skirting", a, face + offset - thick / 2,
                             b, face + offset + thick / 2, z, height, mat, .002)
                else:
                    offset = .007 if side == "w" else -.007
                    self.box("Wall skirting", face + offset - thick / 2, a,
                             face + offset + thick / 2, b, z, height, mat, .002)

    def casings(self, room):
        if room["kind"] == "stair":
            return
        x1, y1, x2, y2 = room["inner"]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        z = room["floor"]
        for wall in self.walls(room["group"]):
            horizontal = abs(wall["a"][1] - wall["b"][1]) < 1e-6
            thickness = wall.get("thickness", .24)
            for op in wall["openings"]:
                if op["kind"] not in ("door", "passage"):
                    continue
                if horizontal:
                    line = wall["a"][1]
                    a = wall["a"][0] + op["offset"]
                    b = a + op["width"]
                    if not (x1 - .35 <= a and b <= x2 + .35):
                        continue
                    if not (y1 - .30 <= line <= y2 + .30):
                        continue
                    sign = 1 if cy > line else -1
                    face = line + sign * (thickness / 2 + .022)
                    h = op["height"] + .06
                    self.box("Door casing", a - .075, face - .018, a, face + .018, z, h,
                             self.F.wood, .005)
                    self.box("Door casing", b, face - .018, b + .075, face + .018, z, h,
                             self.F.wood, .005)
                    self.box("Door casing", a - .075, face - .018, b + .075, face + .018,
                             z + h, .062, self.F.wood, .005)
                else:
                    line = wall["a"][0]
                    a = wall["a"][1] + op["offset"]
                    b = a + op["width"]
                    if not (y1 - .35 <= a and b <= y2 + .35):
                        continue
                    if not (x1 - .30 <= line <= x2 + .30):
                        continue
                    sign = 1 if cx > line else -1
                    face = line + sign * (thickness / 2 + .022)
                    h = op["height"] + .06
                    self.box("Door casing", face - .018, a - .075, face + .018, a, z, h,
                             self.F.wood, .005)
                    self.box("Door casing", face - .018, b, face + .018, b + .075, z, h,
                             self.F.wood, .005)
                    self.box("Door casing", face - .018, a - .075, face + .018, b + .075,
                             z + h, .062, self.F.wood, .005)

    def downlights(self, room):
        if room["kind"] == "stair":
            return
        x1, y1, x2, y2 = room["inner"]
        z = room["floor"] + 3.035
        nx = max(1, min(3, round((x2 - x1) / 2.1)))
        ny = max(1, min(3, round((y2 - y1) / 2.1)))
        for ix in range(nx):
            for iy in range(ny):
                px = x1 + (ix + .5) * (x2 - x1) / nx
                py = y1 + (iy + .5) * (y2 - y1) / ny
                self.cyl("Recessed downlight ring", px, py, z - .006, z + .004, .055,
                         self.F.blackmetal, 20)
                bulb = self.cyl("Recessed downlight lens", px, py, z - .024, z - .006, .042,
                                self.F.led, 20)
                bulb["downlightWatt"] = 5.5

    # -- furniture dressing ----------------------------------------------
    def slat_feature(self, wall_x, inward, centre_y, width, floor):
        """Warm timber slat panel with concealed light, as in the reference bedrooms."""
        z0 = floor + .02
        height = 2.52
        self.box("Slat wall linen backing", wall_x + inward * .002, centre_y - width / 2,
                 wall_x + inward * .022, centre_y + width / 2, z0, height,
                 self.F.boucle, .004, "feature-wall")
        count = max(6, int(width / .072))
        for index in range(count):
            yy = centre_y - width / 2 + (index + .5) * width / count
            self.box("Timber wall slat", wall_x + inward * .022, yy - .019,
                     wall_x + inward * .052, yy + .019, z0 + .05, height - .10,
                     self.F.wood, .006, "feature-wall")
        for zz, name in ((z0 + .035, "Slat wall lower light"), (z0 + height - .045, "Slat wall upper light")):
            strip = self.box(name, wall_x + inward * .012, centre_y - width / 2 + .04,
                             wall_x + inward * .020, centre_y + width / 2 - .04, zz, .018,
                             self.F.led, 0, "feature-wall")
            strip["lampWatt"] = 3.0

    def bed_dressing(self, room):
        floor = room["floor"]
        bed = next((item for item in self.furniture[room["group"]]
                    if item["room"] == room["index"] and item["kind"] == "bed"), None)
        if not bed:
            return
        x1, y1, x2, y2 = bed["bounds"]
        ix1, iy1, ix2, iy2 = room["inner"]
        rotation = bed.get("rotation", 0)
        head_east = rotation == 270
        along_y = rotation % 180 == 90
        width = (y2 - y1) if along_y else (x2 - x1)
        wall_x = ix2 if head_east else ix1
        inward = -1 if head_east else 1
        head_line = x2 if head_east else x1
        # Upholstered headboard panel fixed to the wall behind the bed.
        panel = width + .26
        self.box("Headboard oak frame", wall_x + inward * .001, (y1 + y2) / 2 - panel / 2,
                 wall_x + inward * .036, (y1 + y2) / 2 + panel / 2, floor + .10, 1.16,
                 self.F.wood, .014, "headboard")
        self.box("Linen upholstered headboard", wall_x + inward * .034,
                 (y1 + y2) / 2 - panel / 2 + .035,
                 wall_x + inward * .070, (y1 + y2) / 2 + panel / 2 - .035,
                 floor + .135, 1.09, self.F.boucle, .035, "headboard")
        for index in range(1, 6):
            yy = (y1 + y2) / 2 - panel / 2 + panel * index / 6
            self.box("Headboard channel seam", wall_x + inward * .069, yy - .004,
                     wall_x + inward * .073, yy + .004, floor + .15, 1.05,
                     self.F.boucle, .001)
        # Bedside sconces above the nightstands.
        for ny in (y1 + .20, y2 - .20):
            sx = wall_x + inward * .075
            self.cyl("Bedside sconce backplate", sx, ny, floor + 1.34, floor + 1.38, .042,
                     self.F.brass, 20)
            self.cyl("Bedside sconce shade", sx + inward * .02, ny, floor + 1.38, floor + 1.50,
                     .050, self.F.shade, 20)
            bulb = self.cyl("Bedside sconce bulb", sx + inward * .02, ny, floor + 1.375,
                            floor + 1.40, .038, self.F.led, 16)
            bulb["lampWatt"] = 4.5
        # Four-pillow layering: two European shams, two sleeping pillows.
        for yy in (y1 + width * .30, y2 - width * .30):
            sham = self.box("European pillow", head_line + inward * .08, yy - .17,
                            head_line + inward * .20, yy + .17, floor + .64, .30,
                            self.F.bedding, .10)
            sham.rotation_euler.y = math.radians(14 if head_east else -14)
            sleeper = self.box("Sleeping pillow", head_line + inward * .20, yy - .25,
                               head_line + inward * .40, yy + .25, floor + .63, .13,
                               self.F.bedding, .09)
            sleeper.rotation_euler.y = math.radians(8 if head_east else -8)
        self.cushion(head_line + inward * .62, y1 + width * .30, floor + .66, .40, .32,
                     self.F.boucle, 10)
        self.cushion(head_line + inward * .62, y2 - width * .30, floor + .66, .40, .32,
                     self.F.fabric, -12)
        self.draped_throw(x1 if head_east else x2, inward, y1 + .06, y2 - .06, floor + .60)
        # Rug under the bed, sized to the room.
        if along_y:
            rug_x1 = max(ix1 + .05, x1 - .50) if head_east else x1 + .05
            rug_x2 = x2 - .05 if head_east else min(ix2 - .05, x2 + .50)
        else:
            rug_x1, rug_x2 = x1 - .35, x2 + .35
        rug_y1 = max(iy1 + .05, y1 - .35)
        rug_y2 = min(iy2 - .05, y2 + .35)
        if rug_x2 - rug_x1 > .8 and rug_y2 - rug_y1 > .8:
            self.rug(rug_x1, rug_y1, rug_x2, rug_y2, floor + .014, self.F.rug)
        feature = room["id"] in ("rear1-5", "rear2-5")
        if feature:
            self.slat_feature(wall_x, inward, (y1 + y2) / 2, panel + .62, floor)
        # Art above the headboard where the wall is solid (main bedroom heads a window).
        if room["id"] != "rear2-0":
            offset = .085 if feature else .012
            self.art(wall_x + inward * offset, (y1 + y2) / 2, floor + 1.42, .92, .60, "x", inward)
        # Bedside lamps.
        for item in self.furniture[room["group"]]:
            if item["room"] != room["index"] or item["kind"] != "nightstand":
                continue
            a, b, c, d = item["bounds"]
            if not (b < y2 + .25 and d > y1 - .25):
                continue
            self.lamp((a + c) / 2, (b + d) / 2, floor + .50, .40, 6, .10, "bedside")
        # Bench at the foot in the main bedroom only.
        if room["id"] == "rear2-0":
            self.box("Bed-end bench", x2 + .06, y1 + .18, x2 + .40, y2 - .18, floor + .30, .15,
                     self.F.boucle, .05)
            for yy in (y1 + .28, y2 - .28):
                self.cyl("Bench leg", x2 + .10, yy, floor, floor + .30, .022,
                         self.F.darkwood, 12)

    def living_dressing(self, room, lamp_xy, plant_xy):
        floor = room["floor"]
        table = next((item for item in self.furniture[room["group"]]
                      if item["room"] == room["index"] and item["kind"] == "table"), None)
        sofa = next((item for item in self.furniture[room["group"]]
                     if item["room"] == room["index"] and item["kind"] == "sofa"), None)
        if table:
            tx1, ty1, tx2, ty2 = table["bounds"]
            cx, cy = (tx1 + tx2) / 2, (ty1 + ty2) / 2
            self.books(cx - .08, cy - .06, floor + .42, 3, .26)
            self.vase(cx + .18, cy + .04, floor + .42, .26)
            self.bowl(cx - .12, cy + .24, floor + .42, .10)
        if sofa:
            sx1, sy1, sx2, sy2 = sofa["bounds"]
            self.box("Sofa arm blanket", sx1 + .10, sy1 + .06, sx2 - .10, sy1 + .34,
                     floor + .58, .035, self.F.fabric, .012)
            self.box("Sofa arm blanket fold", sx1 + .10, sy1 + .06, sx2 - .10, sy1 + .10,
                     floor + .36, .22, self.F.fabric, .01)
            for yy in (sy1 + .30, sy2 - .30):
                self.cushion(sx1 + .32, yy, floor + .58, .38, .34, self.F.boucle, 8)
        tv = next((item for item in self.furniture[room["group"]]
                   if item["room"] == room["index"] and item["kind"] == "tv"), None)
        if tv:
            a, b, c, d = tv["bounds"]
            self.bowl((a + c) / 2, (b + d) / 2, floor + .52, .11)
            self.books((a + c) / 2 + .22, (b + d) / 2, floor + .52, 2, .20)
        self.lamp(lamp_xy[0], lamp_xy[1], floor, .58, 11, .17, "floor")
        self.plant(plant_xy[0], plant_xy[1], floor, 1.20, .15)

    def dining_dressing(self, room):
        floor = room["floor"]
        ix1, iy1, ix2, iy2 = room["inner"]
        table = next((item for item in self.furniture[room["group"]]
                      if item["room"] == room["index"] and item["kind"] == "roundtable"), None)
        if table:
            cx = (table["bounds"][0] + table["bounds"][2]) / 2
            cy = (table["bounds"][1] + table["bounds"][3]) / 2
            top = floor + table["height"]
            self.box("Linen table runner", cx - .15, cy - .58, cx + .15, cy + .58, top + .004,
                     .007, self.F.fabric, .003)
            self.vase(cx, cy, top + .008, .24)
            self.bowl(cx + .22, cy - .16, top + .008, .12)
        # Low sideboard against the north wall, below the wall panelling.
        self.box("Dining sideboard", ix1 + .12, iy2 - .50, ix1 + .82, iy2 - .05, floor, .80,
                 self.F.wood, .012)
        self.box("Sideboard top", ix1 + .10, iy2 - .52, ix1 + .84, iy2 - .03, floor + .80, .032,
                 self.F.counter, .005)
        self.lamp(ix1 + .33, iy2 - .28, floor + .83, .40, 7, .12, "sideboard")
        self.vase(ix1 + .64, iy2 - .28, floor + .83, .30)
        self.art((ix1 + .12 + ix1 + .82) / 2, iy2 - .012, floor + 1.32, .95, .58, "y", -1)
        self.rug(ix1 + .55, iy1 + 2.60, ix2 - .35, iy2 - .55, floor + .014, self.F.rug)
        self.plant(ix2 - .30, iy2 - .40, floor, 1.05, .14)
        self.art(ix1 + .012, iy1 + 5.55, floor + 1.20, .82, .56, "x", 1)

    def kitchen_dressing(self, room):
        floor = room["floor"]
        x1, y1, x2, y2 = room["inner"]
        top = floor + .88
        self.box("Kitchen splashback tile", 8.95, y2 - .030, 11.12, y2, top + .02, 1.52,
                 self.F.tile, .003)
        for index in range(1, 5):
            zz = top + .02 + index * .30
            self.box("Kitchen tile joint", 8.95, y2 - .038, 11.12, y2 - .031, zz, .005,
                     self.F.counter, 0)
        self.box("Kitchen open shelf", 9.06, y2 - .34, 10.52, y2 - .07, floor + 1.74, .042,
                 self.F.wood, .006)
        for index, xx in enumerate((9.24, 9.58, 9.92, 10.26)):
            self.cyl("Pantry jar", xx, y2 - .20, floor + 1.782, floor + 1.99, .072,
                     self.F.ceramic if index % 2 else self.F.glass, 20)
            self.cyl("Pantry jar lid", xx, y2 - .20, floor + 1.99, floor + 2.01, .075,
                     self.F.darkwood, 20)
        self.box("Cutting board", 9.50, y2 - .46, 9.92, y2 - .20, top + .028, .024, self.F.wood, .008)
        self.cyl("Kettle", 10.60, y2 - .35, top + .028, top + .25, .10, self.F.blackmetal, 24)
        self.cyl("Utensil crock", 10.24, y2 - .40, top + .028, top + .19, .062, self.F.ceramic, 20)
        for index in range(3):
            self.rod("Utensil", (10.22 + index * .02, y2 - .40, top + .19),
                     (10.20 + index * .02, y2 - .40, top + .40), .005, self.F.wood, 6)
        for xx in (9.08, 9.19):
            self.cyl("Oil bottle", xx, y2 - .33, top + .028, top + .25, .040, self.F.glass, 16)
        self.bowl(9.32, 1.16, top + .028, .13)
        self.plant(10.72, 5.95, top + .028, .42, .095)
        for yy in (1.10, 2.05, 3.02, 3.98, 4.55):
            self.box("Cabinet pull", 10.532, yy - .010, 10.548, yy + .010, floor + .60, .22,
                     self.F.brass, .005)
        for xx in (9.20, 9.72, 10.25):
            self.box("Cabinet pull", xx - .010, 1.462, xx + .010, 1.482, floor + .60, .22,
                     self.F.brass, .005)
        # East counter styling and a readable fridge front.
        self.box("Counter board", 10.60, 3.28, 11.05, 3.62, floor + .94, .022, self.F.wood, .006)
        self.cyl("Counter kettle", 10.62, 3.12, floor + .94, floor + 1.17, .095,
                 self.F.blackmetal, 24)
        self.bowl(10.94, 2.98, floor + .94, .11)
        self.box("Fridge door seam", 10.332, 4.76, 10.342, 5.54, floor + 1.28, .012,
                 self.F.darkwood, 0)
        for zz in (.55, 1.62):
            self.box("Fridge handle", 10.300, 4.80, 10.316, 4.86, floor + zz, .32,
                     self.F.metal, .008)

    def bath_dressing(self, room):
        floor = room["floor"]
        x1, y1, x2, y2 = room["inner"]
        self.box("Bathroom tile wainscot", x1, y2 - .030, x2, y2, floor, 1.32, self.F.tile, .003)
        self.box("Bathroom tile wainscot", x1, y1, x1 + .030, y2, floor, 1.32, self.F.tile, .003)
        for index in range(1, 5):
            zz = floor + index * .30
            self.box("Bath tile joint", x1, y2 - .034, x2, y2 - .029, zz, .006,
                     self.F.counter, 0)
            self.box("Bath tile joint", x1 + .024, y1, x1 + .029, y2, zz, .006,
                     self.F.counter, 0)
        for index in range(1, 5):
            xx = x1 + (x2 - x1) * index / 4
            self.box("Bath tile joint", xx - .004, y2 - .034, xx + .004, y2 - .029,
                     floor, 1.32, self.F.counter, 0)
        self.box("Tile trim", x1, y2 - .045, x2, y2 - .025, floor + 1.32, .022, self.F.metal, .003)
        self.rod("Towel rail", (x1 + .05, y1 + .30, floor + 1.24), (x1 + .05, y1 + 1.05, floor + 1.24),
                 .014, self.F.metal, 12)
        for index in range(2):
            y0 = y1 + .38 + index * .32
            for fold in range(3):
                self.box("Bath towel", x1 + .045 + fold * .012, y0,
                         x1 + .062 + fold * .012, y0 + .24, floor + .70, .53,
                         self.F.towel, .006)
        self.box("Bath mat", x1 + .28, y1 + .30, x1 + .92, y1 + .90, floor + .010, .012,
                 self.F.towel, .008)
        vanity = next((item for item in self.furniture[room["group"]]
                       if item["room"] == room["index"] and item["kind"] == "vanity"), None)
        if vanity:
            vx1, vy1, vx2, vy2 = vanity["bounds"]
            self.cyl("Soap dispenser", (vx1 + vx2) / 2, (vy1 + vy2) / 2 + .16, floor + .86,
                     floor + 1.01, .030, self.F.ceramic, 16)
            self.box("Folded hand towel", vx1 + .02, vy2 - .16, vx2 - .03, vy2 - .05,
                     floor + .86, .045, self.F.towel, .01)
        shower = next((item for item in self.furniture[room["group"]]
                       if item["room"] == room["index"] and item["kind"] == "shower"), None)
        if shower:
            sx1, sy1, sx2, sy2 = shower["bounds"]
            bottles = (self.F.branch, self.F.ceramic, self.F.pot)
            for index in range(3):
                self.cyl("Shower bottle", sx1 + .18 + index * .12, sy2 - .08, floor + 1.16,
                         floor + 1.34 + index * .04, .035, bottles[index], 14)

    def entry_dressing(self, room):
        floor = room["floor"]
        x1, y1, x2, y2 = room["inner"]
        self.rug(x1 + .20, y1 + .25, x2 - .20, y2 - .40, floor + .014, self.F.rug_pale)
        # Coat hooks on the east wall clear of the window.
        for index in range(3):
            yy = y1 + 1.28 + index * .20
            self.rod("Coat hook", (x2 - .015, yy, floor + 1.58), (x2 - .11, yy, floor + 1.62),
                     .011, self.F.brass, 10)
        bench = next((item for item in self.furniture[room["group"]]
                      if item["room"] == room["index"] and item["kind"] == "bench"), None)
        if bench:
            a, b, c, d = bench["bounds"]
            self.box("Entry bench cushion", a + .015, b + .03, c - .015, d - .03,
                     floor + .45, .055, self.F.boucle, .02)
        self.art(x1 + .012, y2 - .34, floor + 1.42, .52, .52, "x", 1)
        self.cyl("Umbrella stand", x1 + .22, y2 - .28, floor, floor + .52, .11,
                 self.F.stone, 24)
        for index in range(2):
            self.rod("Umbrella", (x1 + .20 + index * .04, y2 - .28, floor + .10),
                     (x1 + .17 + index * .04, y2 - .28, floor + .82), .018,
                     self.F.darkwood, 10)

    def study_dressing(self, room, plant_at):
        floor = room["floor"]
        x1, y1, x2, y2 = room["inner"]
        desk = next((item for item in self.furniture[room["group"]]
                     if item["room"] == room["index"] and item["kind"] == "desk"), None)
        if not desk:
            return
        dx1, dy1, dx2, dy2 = desk["bounds"]
        top = floor + desk["height"]
        self.lamp(dx1 + .26, (dy1 + dy2) / 2, top, .38, 5.5, .095, "desk")
        self.books(dx2 - .32, (dy1 + dy2) / 2, top, 3, .24)
        self.cyl("Pen cup", dx1 + .52, dy2 - .10, top, top + .11, .042, self.F.ceramic, 16)
        self.plant(plant_at[0], plant_at[1], floor, .85, .115)

    # -- assemble ---------------------------------------------------------
    def build(self):
        self.F.upgrade()
        for group, label in (("front", "Front"), ("rear1", "Rear1"), ("rear2", "Rear2")):
            self.enter(label)
            for room in self.rooms.values():
                if room["group"] != group:
                    continue
                self.skirting(room)
                self.casings(room)
                self.downlights(room)
        r = self.rooms
        self.enter("Front")
        self.bed_dressing(r["front-2"])
        self.kitchen_dressing(r["front-0"])
        floor = r["front-1"]["floor"]
        self.rug(4.72, 1.15, 7.28, 5.55, floor + .014, self.F.rug_pale)
        self.box("Hall console", 7.22, 2.55, 7.62, 3.85, floor, .80, self.F.wood, .01)
        self.box("Hall console top", 7.20, 2.53, 7.64, 3.87, floor + .80, .03, self.F.counter, .005)
        self.vase(7.40, 2.80, floor + .83, .28)
        self.bowl(7.40, 3.58, floor + .83, .11)
        self.art(7.665, 3.20, floor + 1.30, .95, .60, "x", -1)
        self.plant(7.18, 1.12, floor, 1.05, .13)
        self.plant(4.55, 5.95, floor, 1.10, .14)
        bench = next(item for item in self.furniture["front"]
                     if item["room"] == 1 and item["kind"] == "bench")
        bx1, by1, bx2, by2 = bench["bounds"]
        self.box("Bench cushion", bx1 + .02, by1 + .04, bx2 - .02, by2 - .04, floor + .45, .06,
                 self.F.boucle, .025)

        self.enter("Rear1")
        self.bed_dressing(r["rear1-5"])
        self.living_dressing(r["rear1-0"], (3.10, 20.92), (3.58, 16.18))
        self.dining_dressing(r["rear1-3"])
        self.bath_dressing(r["rear1-1"])
        self.bath_dressing(r["rear1-7"])
        self.entry_dressing(r["rear1-8"])
        floor = r["rear1-6"]["floor"]
        self.rug(8.20, 21.62, 10.72, 23.62, floor + .014, self.F.rug_pale)
        self.lamp(10.86, 21.55, floor, .56, 10, .16, "floor")
        self.books(10.80, 23.72, floor + .66, 3, .22)
        self.art(11.14, 21.95, floor + 1.28, .78, .52, "x", -1)
        self.plant(9.10, 21.70, floor, .95, .12)

        self.enter("Rear2")
        self.bed_dressing(r["rear2-0"])
        self.living_dressing(r["rear2-3"], (5.02, 21.60), (7.34, 16.72))
        self.bath_dressing(r["rear2-1"])
        self.bath_dressing(r["rear2-7"])
        self.bed_dressing(r["rear2-5"])
        self.study_dressing(r["rear2-6"], (11.00, 23.78))
        floor = r["rear2-3"]["floor"]
        self.lamp(4.62, 23.78, floor + .76, .36, 5.5, .095, "desk")
        self.books(6.15, 23.80, floor + .78, 3, .24)


def build(ctx):
    Details(ctx).build()
