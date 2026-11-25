# REJECTED (2026-11-25): baked AO is not used; ServerStorage.AOTest was deleted. Kept for reference.
# ao_bake.py - AO TEST: bakes ambient occlusion into one building tier's own texture (headless Blender, Cycles).
#   blender -b --factory-startup --python tools/blender/ao_bake.py -- IceDrill 5
# Opens store-assets/buildings/<Id>/<Id>.blend (the approved build), takes the tier's station meshes,
# gives every non-glow mesh one shared set of unique UVs (one atlas for the whole station), bakes
#   AO     (Cycles, a ground plane under the pad as an occluder, AO_DISTANCE studs)
#   COLOUR (the palette texture through the original UVs)
# and multiplies them: colour x (1 - AO_STRENGTH x (1 - ao)), in linear light. Glow meshes keep the palette
# and their own UVs (Neon in game). Out, in store-assets/ao-test/<Id>/:
#   <Id>_T<n>_AO.png            the station's texture (TEXTURE_SIZE square)
#   <Id>_T<n>_AOraw.png         the plain AO (for judging; not uploaded)
#   fbx/<Id>_T<n>_AO.fbx        the station with the new UVs (exported like the framework: quarter scale)
#   <Id>_T<n>_AO.json           every mesh, its triangles and whether it is baked
# The real models, ids and templates are not touched.
import bpy, bmesh, json, math, os, sys

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BID = argv[0] if argv else "IceDrill"
TIER = int(argv[1]) if len(argv) > 1 else 5
RENDER = "render" in argv  # also store-assets/ao-test/<Id>/<Id>_T<n>_AO_on.png and _off.png (EEVEE previews)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "store-assets", "ao-test", BID)
TEXTURE_SIZE = 1024
AO_DISTANCE = 3.0      # studs: how far a surface looks for occluders
AO_STRENGTH = 0.85     # 1 = the full baked darkening
SAMPLES = 96
EXPORT_SCALE = 0.25    # as framework.export_building: Studio's import arrives at 25x

bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, "store-assets", "buildings", BID, BID + ".blend"))
root = bpy.data.objects["%sT%d" % (BID, TIER)]
station = [o for o in root.children if o.type == "MESH"]
keep = set(station)
for o in list(bpy.data.objects):
    if o not in keep and o != root:
        bpy.data.objects.remove(o, do_unlink=True)
scene = bpy.context.scene
for o in station:
    o.hide_set(False)
    o.hide_render = False
    o.hide_viewport = False

# Modifiers applied into plain meshes (the bake and the export see the same geometry).
depsgraph = bpy.context.evaluated_depsgraph_get()
for o in station:
    mesh = bpy.data.meshes.new_from_object(o.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
    o.modifiers.clear()
    o.data = mesh
glow = [o for o in station if o.name.endswith("Glow")]
baked = [o for o in station if not o.name.endswith("Glow")]

# The palette's UVs by name; the new atlas UVs "AO" become the active (baked-into) layer.
palette_uv = baked[0].data.uv_layers[0].name
for o in baked:
    o.data.uv_layers.new(name="AO")
    o.data.uv_layers.active = o.data.uv_layers["AO"]
bpy.ops.object.select_all(action="DESELECT")
for o in baked:
    o.select_set(True)
bpy.context.view_layer.objects.active = baked[0]
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_all(action="SELECT")
bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.003, area_weight=0.0, scale_to_bounds=False)
bpy.ops.uv.select_all(action="SELECT")
bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
bpy.ops.object.mode_set(mode="OBJECT")

# A ground plane under the pad: an occluder only.
bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "AOGround"

scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = SAMPLES
if scene.world is None:
    scene.world = bpy.data.worlds.new("World")
scene.world.light_settings.distance = AO_DISTANCE
scene.render.bake.margin = 6
scene.render.bake.use_clear = True


def new_image(name, colourspace):
    image = bpy.data.images.new(name, TEXTURE_SIZE, TEXTURE_SIZE, alpha=False, float_buffer=True)
    image.colorspace_settings.name = colourspace
    return image


ao_image = new_image("BakeAO", "Non-Color")
colour_image = new_image("BakeColour", "Linear Rec.709")

# Every material on the baked meshes: the palette node reads the palette UVs explicitly; a target node
# (active) takes the bake.
materials = {s.material for o in baked for s in o.material_slots if s.material}
targets = {}
for mat in materials:
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for tex in [n for n in nodes if n.type == "TEX_IMAGE"]:
        uv = nodes.new("ShaderNodeUVMap")
        uv.uv_map = palette_uv
        links.new(uv.outputs["UV"], tex.inputs["Vector"])
    target = nodes.new("ShaderNodeTexImage")
    targets[mat] = target
    nodes.active = target


def bake(kind, image):
    for target in targets.values():
        target.image = image
        target.select = True
        target.id_data.nodes.active = target
    bpy.ops.object.select_all(action="DESELECT")
    for o in baked:
        o.select_set(True)
    bpy.context.view_layer.objects.active = baked[0]
    if kind == "DIFFUSE":
        scene.render.bake.use_pass_direct = False
        scene.render.bake.use_pass_indirect = False
        scene.render.bake.use_pass_color = True
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, margin=6, use_clear=True)
    else:
        bpy.ops.object.bake(type=kind, margin=6, use_clear=True)
    print("baked", kind)


bake("AO", ao_image)
bake("DIFFUSE", colour_image)

import numpy as np
n = TEXTURE_SIZE * TEXTURE_SIZE
ao = np.array(ao_image.pixels[:], dtype=np.float32).reshape(n, 4)[:, 0]
colour = np.array(colour_image.pixels[:], dtype=np.float32).reshape(n, 4)[:, :3]
shade = 1.0 - AO_STRENGTH * (1.0 - np.clip(ao, 0, 1))
linear = colour * shade[:, None]


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


os.makedirs(os.path.join(OUT, "fbx"), exist_ok=True)


def save_png(rgb, path):
    image = bpy.data.images.new(os.path.basename(path), TEXTURE_SIZE, TEXTURE_SIZE, alpha=False)
    image.colorspace_settings.name = "Non-Color"  # the values are already sRGB-encoded
    rgba = np.ones((n, 4), dtype=np.float32)
    rgba[:, :3] = rgb
    image.pixels[:] = rgba.ravel()
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
    print("saved", path)


tex_path = os.path.join(OUT, "%s_T%d_AO.png" % (BID, TIER))
save_png(to_srgb(linear), tex_path)
save_png(np.repeat(np.clip(shade, 0, 1)[:, None], 3, axis=1), os.path.join(OUT, "%s_T%d_AOraw.png" % (BID, TIER)))

# The export: baked meshes keep only the atlas UVs (Roblox reads the first UV set), and a material showing
# the new texture; glow meshes are unchanged.
final = bpy.data.images.load(tex_path)
mat = bpy.data.materials.new("%sT%dAO" % (BID, TIER))
mat.use_nodes = True
bsdf = next(nd for nd in mat.node_tree.nodes if nd.type == "BSDF_PRINCIPLED")
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = final
mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
for o in baked:
    for layer in [l for l in o.data.uv_layers if l.name != "AO"]:
        o.data.uv_layers.remove(layer)
    o.data.uv_layers["AO"].name = "UVMap"
    o.data.materials.clear()
    o.data.materials.append(mat)
bpy.data.objects.remove(ground, do_unlink=True)
bpy.ops.object.select_all(action="DESELECT")
for o in station:
    o.select_set(True)
bpy.context.view_layer.objects.active = station[0]
fbx_path = os.path.join(OUT, "fbx", "%s_T%d_AO.fbx" % (BID, TIER))
bpy.ops.export_scene.fbx(filepath=fbx_path, use_selection=True, object_types={"MESH"}, use_mesh_modifiers=True,
                         apply_unit_scale=True, apply_scale_options="FBX_SCALE_NONE", global_scale=EXPORT_SCALE,
                         axis_forward="-Z", axis_up="Y", add_leaf_bones=False, bake_anim=False)
print("exported", fbx_path)


def preview(path):
    """An EEVEE render from the front three-quarter view (the station's front is -Y)."""
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 900, 1100
    scene.render.film_transparent = False
    world = scene.world
    world.use_nodes = True
    bg = next(nd for nd in world.node_tree.nodes if nd.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.75, 0.82, 0.92, 1)
    bg.inputs["Strength"].default_value = 0.9
    if "AOSun" not in bpy.data.objects:
        sun = bpy.data.objects.new("AOSun", bpy.data.lights.new("AOSun", "SUN"))
        sun.data.energy = 3.2
        sun.rotation_euler = (math.radians(50), 0, math.radians(-35))
        scene.collection.objects.link(sun)
        cam = bpy.data.objects.new("AOCam", bpy.data.cameras.new("AOCam"))
        cam.data.lens = 50
        scene.collection.objects.link(cam)
        target = (0, 0, 12.5)
        eye = (18, -42, 20)
        from mathutils import Vector
        d = Vector(target) - Vector(eye)
        cam.location = eye
        cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        scene.camera = cam
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


if RENDER:
    preview(os.path.join(OUT, "%s_T%d_AO_on.png" % (BID, TIER)))
    plain = bpy.data.images.new("Plain", TEXTURE_SIZE, TEXTURE_SIZE, alpha=False)
    plain.colorspace_settings.name = "Non-Color"  # linear values, as the shader reads them
    rgba = np.ones((n, 4), dtype=np.float32)
    rgba[:, :3] = colour
    plain.pixels[:] = rgba.ravel()
    tex.image = plain
    preview(os.path.join(OUT, "%s_T%d_AO_off.png" % (BID, TIER)))


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


info = {"id": BID, "tier": TIER, "texture": os.path.basename(tex_path), "textureSize": TEXTURE_SIZE,
        "aoDistance": AO_DISTANCE, "aoStrength": AO_STRENGTH,
        "meshes": {o.name: {"tris": tris(o), "baked": o in baked} for o in station}}
with open(os.path.join(OUT, "%s_T%d_AO.json" % (BID, TIER)), "w", encoding="utf-8") as handle:
    json.dump(info, handle, indent=1, sort_keys=True)
print("AO_DONE", len(baked), "baked meshes,", len(glow), "glow meshes")
