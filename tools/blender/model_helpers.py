# model_helpers.py - shared helpers for Blender batch scripts that build Roblox models.
# Cleaned up from a shipped Roblox project's prop and structure helpers. Tested in Blender 5.2.
#
# Load it at the top level of each batch script, or of a Blender MCP execute_blender_code call:
#     exec(open(r"C:\path\to\repo\tools\blender\model_helpers.py", encoding="utf-8").read())
# exec re-reads the file every run, so edits apply without restarting Blender (an import would be cached).
#
# Conventions:
#   1 Blender unit = 1 stud. +Z is up. A model's front faces -Y (what Blender's Front view shows);
#   with the export below it arrives facing Roblox -Z, a Model's LookVector.
#   One mesh per colour role, named <Model><Part> (TreasureChestWood). The object and its mesh data
#   share that name. Roblox restyles every part by name, so Blender colours are previews only.
#   Each model rests on z = 0 with its footprint centred on the origin.
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix, Euler

# Export scale. "FBX_SCALE_NONE" is Blender's default and what the shipped project used: Studio then
# brings models in 100x too big, the grouping script scales them back, and no mesh may be longer than
# 2048 / 100 units before that. Roblox's docs recommend "FBX_SCALE_UNITS" for a 1:1 import instead.
# Set FBX_SCALE_MODE before exec() to try it, and read the import scale the grouping script prints.
FBX_SCALE_MODE = globals().get("FBX_SCALE_MODE", "FBX_SCALE_NONE")
# EXPORT_SCALE shrinks the FBX before Studio's 100x: 0.25 arrives at 25x, so a mesh may be 2048 / 25 = 82
# units long (the tall building tiers need it). The template builder detects the factor.
EXPORT_SCALE = globals().get("EXPORT_SCALE", 1.0)
IMPORT_FACTOR = (100.0 if FBX_SCALE_MODE == "FBX_SCALE_NONE" else 1.0) * EXPORT_SCALE
MAX_MESH_UNITS = 2048.0 / IMPORT_FACTOR * 0.98   # a Roblox part is at most 2048 studs on each axis
MAX_TRIANGLES = 18000                             # per mesh; Roblox allows 20,000


# ---------- geometry (all build into a bmesh) ----------

def M(location=(0, 0, 0), rotation=(0, 0, 0)):
    """A 4x4 matrix: rotate by Euler angles (radians), then move to location."""
    return Matrix.Translation(Vector(location)) @ Euler(rotation).to_matrix().to_4x4()


def align_z(direction):
    """A 4x4 rotation taking +Z onto direction."""
    return Vector((0, 0, 1)).rotation_difference(Vector(direction).normalized()).to_matrix().to_4x4()


def lathe(bm, profile, segments, matrix=Matrix()):
    """Revolve (radius, z) points round Z, bottom to top. A zero radius closes the end with a pole."""
    rings = []
    for r, z in profile:
        if r < 1e-4:
            rings.append([bm.verts.new(matrix @ Vector((0, 0, z)))])
        else:
            rings.append([bm.verts.new(matrix @ Vector((r * math.cos(2 * math.pi * i / segments),
                                                         r * math.sin(2 * math.pi * i / segments), z)))
                          for i in range(segments)])
    for a, b in zip(rings, rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        for i in range(segments):
            j = (i + 1) % segments
            if len(a) == 1:
                bm.faces.new((a[0], b[i], b[j]))
            elif len(b) == 1:
                bm.faces.new((a[i], a[j], b[0]))
            else:
                bm.faces.new((a[i], a[j], b[j], b[i]))


def cylinder(bm, base, radius, height, segments=16, top=None, direction=(0, 0, 1)):
    """A capped (optionally tapered) cylinder standing on base, along direction."""
    top = radius if top is None else top
    lathe(bm, [(0, 0), (radius, 0), (top, height), (0, height)], segments,
          Matrix.Translation(Vector(base)) @ align_z(direction))


def box(bm, center, size, rotation=(0, 0, 0)):
    """A sharp box. Prefer rounded_block for anything the player sees up close."""
    bmesh.ops.create_cube(bm, size=1.0, matrix=M(center, rotation) @ Matrix.Diagonal((*size, 1.0)))


def blob(bm, center, size, subdivisions=2, rotation=(0, 0, 0), floor=None):
    """An ellipsoid (size = radii per axis). floor flattens anything below that z."""
    sphere = bmesh.ops.create_icosphere(bm, subdivisions=subdivisions, radius=1.0)
    turn = Euler(rotation).to_matrix()
    for v in sphere["verts"]:
        v.co = Vector(center) + turn @ Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if floor is not None:
            v.co.z = max(v.co.z, floor)


def torus(bm, matrix, radius, minor, segments=24, minor_segments=8):
    """A ring in the matrix's XY plane (its axis is the matrix's Z)."""
    rings = []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        rings.append([bm.verts.new(matrix @ Vector(((radius + minor * math.cos(b)) * math.cos(a),
                                                    (radius + minor * math.cos(b)) * math.sin(a),
                                                    minor * math.sin(b))))
                      for b in (2 * math.pi * k / minor_segments for k in range(minor_segments))])
    for i in range(segments):
        a, b = rings[i], rings[(i + 1) % segments]
        for k in range(minor_segments):
            j = (k + 1) % minor_segments
            bm.faces.new((a[k], a[j], b[j], b[k]))


def sweep_frames(points):
    """Flip-free (tangent, normal, binormal) frames along a polyline (parallel transport)."""
    tangents = [(points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]).normalized() for i in range(len(points))]
    normal = tangents[0].cross(Vector((1, 0, 0)))
    if normal.length < 1e-3:
        normal = tangents[0].cross(Vector((0, 1, 0)))
    normal.normalize()
    frames = []
    for i, tangent in enumerate(tangents):
        if i > 0:
            normal = tangents[i - 1].rotation_difference(tangent) @ normal
            normal = (normal - tangent * normal.dot(tangent)).normalized()
        frames.append((tangent, normal, tangent.cross(normal)))
    return frames


def sweep(bm, points, radius, segments=10, radius_end=None, caps=True):
    """A round tube along a polyline of Vectors (pipes, arms, handles, stems), optionally tapered."""
    points = [Vector(p) for p in points]
    radius_end = radius if radius_end is None else radius_end
    rings = []
    for i, (p, (t, n, b)) in enumerate(zip(points, sweep_frames(points))):
        r = radius + (radius_end - radius) * i / (len(points) - 1)
        rings.append([bm.verts.new(p + (n * math.cos(2 * math.pi * k / segments) + b * math.sin(2 * math.pi * k / segments)) * r)
                      for k in range(segments)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segments):
            j = (k + 1) % segments
            bm.faces.new((a[k], a[j], b[j], b[k]))
    if caps:
        bm.faces.new(tuple(reversed(rings[0])))
        bm.faces.new(tuple(rings[-1]))


def rounded_rect(w, d, r, seg=3):
    """Counter-clockwise (x, y) outline of a centred w x d rectangle with corner radius r."""
    r = max(0.01, min(r, w / 2 - 0.005, d / 2 - 0.005))
    points = []
    for k, (cx, cy) in enumerate(((w / 2 - r, d / 2 - r), (r - w / 2, d / 2 - r), (r - w / 2, r - d / 2), (w / 2 - r, r - d / 2))):
        for i in range(seg + 1):
            a = math.pi / 2 * (k + i / seg)
            points.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return points


def loft(bm, sections):
    """Join equal-length closed point loops (bottom to top) into a solid capped at both ends."""
    rings = [[bm.verts.new(p) for p in section] for section in sections]
    n = len(sections[0])
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b[j], b[k]))
    bm.faces.new(tuple(reversed(rings[0])))
    bm.faces.new(tuple(rings[-1]))


def rounded_block(bm, size, matrix=Matrix(), corner=0.3, edge=0.1, corner_seg=3, edge_seg=2, taper=1.0):
    """The workhorse of the chunky look: a box centred on the matrix origin with rounded vertical
    corners (corner) and rounded top and bottom edges (edge). taper scales the top against the bottom."""
    w, d, h = size
    edge = max(0.0, min(edge, h / 2 - 0.001, w / 2 - 0.01, d / 2 - 0.01))
    levels = [(-h / 2, 0.0), (h / 2, 0.0)]
    if edge > 0 and edge_seg > 0:
        quarter = [k / edge_seg * math.pi / 2 for k in range(edge_seg + 1)]
        levels = [(-h / 2 + edge - edge * math.sin(a), edge * (1 - math.cos(a))) for a in reversed(quarter)]
        levels += [(h / 2 - edge + edge * math.sin(a), edge * (1 - math.cos(a))) for a in quarter]
    sections = []
    for z, inset in levels:
        s = 1 + (taper - 1) * (z + h / 2) / h
        outline = rounded_rect(w * s - 2 * inset, d * s - 2 * inset, corner * s - inset, corner_seg)
        sections.append([matrix @ Vector((x, y, z)) for x, y in outline])
    loft(bm, sections)


def double_sided_strip(bm, left, right):
    """A thin ribbon between two point rows, built twice with opposite winding. Roblox culls back
    faces, so flags, leaves and cloth need this to show from both sides."""
    for reverse in (False, True):
        lv, rv = [bm.verts.new(p) for p in left], [bm.verts.new(p) for p in right]
        for i in range(len(left) - 1):
            quad = (lv[i], rv[i], rv[i + 1], lv[i + 1])
            bm.faces.new(tuple(reversed(quad)) if reverse else quad)


# ---------- finishing: normals, bevels, shading, materials ----------

def bevel_edges(bm, width, segments=2, angle=50):
    """Bevel every edge sharper than angle degrees, so hard edges catch the light. The default 50
    leaves rounded_block's own rounding steps (30 and 45 degrees) alone."""
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(angle)]
    try:
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, profile=0.5, affect="EDGES", clamp_overlap=True)
    except TypeError:  # Blender before 2.90
        bmesh.ops.bevel(bm, geom=edges, offset=width, segments=segments, profile=0.5, vertex_only=False, clamp_overlap=True)


def set_material(obj, name, rgb):
    """A preview material: Base Color for renders, diffuse_color for the viewport and Workbench."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    if mat.node_tree is None:  # Blender 4.x makes node-less materials; 5.x always has nodes
        mat.use_nodes = True
    bsdf = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)  # by type: names are localized
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1)
        bsdf.inputs["Roughness"].default_value = 0.55
    mat.diffuse_color = (*rgb, 1)
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def finish(coll, name, bm, rgb, shading="hard", bevel=0.0, smooth_angle=50):
    """Turn a bmesh into a named, coloured object.
    shading: "hard" (flat planes, smooth edges; built things), "smooth" (organic shapes), or
    "soft" (open or double-sided pieces: normals are left exactly as built)."""
    if shading != "soft":
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if bevel:
            bevel_edges(bm, bevel)
    ngons = [f for f in bm.faces if len(f.verts) > 4]   # concave caps import badly: triangulate them
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    limit = math.radians(smooth_angle)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        e.smooth = shading != "hard" or not (len(e.link_faces) == 2 and e.calc_face_angle(0) > limit)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    set_material(obj, name, rgb)
    return obj


def build_looks(coll, meshes, looks):
    """looks: {part name: (preview rgb, shading[, bevel])}; meshes: {part name: bmesh}. Empty meshes
    are skipped with a note. Returns the objects."""
    objects = []
    for name, look in looks.items():
        bm = meshes[name]
        if not bm.verts:
            bm.free()
            print("empty mesh skipped:", name)
            continue
        objects.append(finish(coll, name, bm, look[0], look[1], look[2] if len(look) > 2 else 0.0))
    return objects


def triangles(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ---------- batch: collection, layout, checks, export ----------

def begin(collection):
    """A fresh, visible collection for this batch (old objects and their unused meshes removed, so
    repeated runs don't pile up data). Other collections are excluded so selection and renders only
    see this batch."""
    coll = bpy.data.collections.get(collection)
    if not coll:
        coll = bpy.data.collections.new(collection)
        bpy.context.scene.collection.children.link(coll)
    old_meshes = [o.data for o in coll.objects if o.type == "MESH"]
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in old_meshes:
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)
    for layer in bpy.context.view_layer.layer_collection.children:
        layer.exclude = layer.name != collection
    return coll


def bounds(objects):
    """World-space (low, high) corners of the objects' vertices."""
    points = [o.matrix_world @ v.co for o in objects for v in o.data.vertices]
    return (Vector((min(p[i] for p in points) for i in range(3))), Vector((max(p[i] for p in points) for i in range(3))))


def rest_and_place(groups, spacing=(30.0, 30.0), columns=6):
    """groups: {model name: [objects]}. Rests each model on z = 0 with its footprint centred on the
    origin (in the mesh data), then spreads the models on a grid so they don't overlap in Blender.
    The grouping script re-pivots each model, so the grid offset never reaches the game.
    Returns {model name: (x, y, z) size in Blender axes}."""
    sizes = {}
    for index, (model, objects) in enumerate(groups.items()):
        low, high = bounds(objects)
        shift = Matrix.Translation((-(low.x + high.x) / 2, -(low.y + high.y) / 2, -low.z))
        for obj in objects:
            obj.data.transform(shift)
            obj.location = ((index % columns) * spacing[0], (index // columns) * spacing[1], 0.0)
        sizes[model] = tuple(round(c, 3) for c in high - low)
    bpy.context.view_layer.update()
    return sizes


def check(objects):
    """Print triangle counts and sizes; return a list of problems (empty means safe to export)."""
    problems = []
    counts = {o.name: triangles(o) for o in objects}
    print("triangles:", counts, "total", sum(counts.values()))
    for o in objects:
        if "." in o.name or o.name != o.data.name:
            problems.append("name clash (Blender renamed it): %s / %s" % (o.name, o.data.name))
        if counts[o.name] > MAX_TRIANGLES:
            problems.append("%s has %d triangles (keep under %d)" % (o.name, counts[o.name], MAX_TRIANGLES))
        longest = max(o.dimensions)
        if longest > MAX_MESH_UNITS:
            problems.append("%s is %.1f units long (limit %.1f with %s)" % (o.name, longest, MAX_MESH_UNITS, FBX_SCALE_MODE))
    for p in problems:
        print("PROBLEM:", p)
    return problems


def export_fbx(objects, path):
    """Export exactly these mesh objects to one FBX. Modifiers are applied; no armature leaf bones,
    no animation. Axes stay at Blender's defaults (forward -Z, up Y), which Studio reads correctly."""
    for other in bpy.context.selected_objects:
        other.select_set(False)
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             use_mesh_modifiers=True, apply_unit_scale=True, apply_scale_options=FBX_SCALE_MODE, global_scale=EXPORT_SCALE,
                             axis_forward="-Z", axis_up="Y", add_leaf_bones=False, bake_anim=False)
    print("exported", path)


def write_manifest(path, fbx_path, groups, sizes):
    """The batch manifest the Studio grouping script reads: each model's part names and its size in
    studs on Roblox's axes (X, Y up, Z), used to measure and undo the import's scale."""
    models = {}
    for model, objects in groups.items():
        x, y, z = sizes[model]
        models[model] = {"parts": [o.name for o in objects], "size": [x, z, y]}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"file": os.path.basename(fbx_path), "models": models}, handle, indent=1)
    print("manifest", path, "with", len(models), "models")


# ---------- look checks without Studio ----------

def shots(objects, views, out_dir, size=640, distance=None, lens=50):
    """Workbench PNGs of objects for checks when Studio can't capture. views: {name: (dx, dy, dz)}
    directions from the objects' centre toward the camera, or {name: ((eye), (look at))} for an exact
    player-eye shot. Back faces are culled, as in Roblox, so flipped normals show as holes.
    Every setting changed is restored. Returns the PNG paths."""
    scene = bpy.context.scene
    shading = scene.display.shading
    saved = (scene.render.engine, scene.camera, scene.render.resolution_x, scene.render.resolution_y,
             scene.render.resolution_percentage, scene.render.filepath,
             shading.light, shading.color_type, shading.show_backface_culling)
    try:
        scene.render.engine = "BLENDER_WORKBENCH"
    except TypeError as error:  # the message lists the valid engines
        raise RuntimeError("no Workbench engine: %s" % error)
    shading.light, shading.color_type, shading.show_backface_culling = "STUDIO", "MATERIAL", True
    hidden = [o for o in scene.objects if o not in objects and not o.hide_render]
    for o in hidden:
        o.hide_render = True
    camera = bpy.data.objects.new("ShotCamera", bpy.data.cameras.new("ShotCamera"))
    camera.data.lens = lens
    scene.collection.objects.link(camera)
    low, high = bounds(objects)
    centre, radius = (low + high) / 2, (high - low).length / 2
    paths = []
    try:
        scene.camera = camera
        scene.render.resolution_x = scene.render.resolution_y = size
        scene.render.resolution_percentage = 100
        os.makedirs(out_dir, exist_ok=True)
        for name, view in views.items():
            if isinstance(view[0], (int, float)):
                eye, target = centre + Vector(view).normalized() * (distance or radius * 3.2), centre
            else:
                eye, target = Vector(view[0]), Vector(view[1])
            camera.location = eye
            camera.rotation_euler = (target - eye).to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(out_dir, name + ".png")
            bpy.ops.render.render(write_still=True)
            paths.append(scene.render.filepath)
    finally:
        bpy.data.objects.remove(camera, do_unlink=True)
        for o in hidden:
            o.hide_render = False
        (scene.render.engine, scene.camera, scene.render.resolution_x, scene.render.resolution_y,
         scene.render.resolution_percentage, scene.render.filepath,
         shading.light, shading.color_type, shading.show_backface_culling) = saved
    return paths


def check_spin_centred(objects, spins):
    """spins: {mesh name: (axis point, axis)} in build coordinates, so call it before rest_and_place.
    A MeshPart turns about its bounding-box centre, so a spinning mesh must be centred on its axis.
    Prints how far each one is off (should be ~0)."""
    by_name = {o.name: o for o in objects}
    for name, (point, axis) in spins.items():
        if name not in by_name:
            print("spin check: no mesh", name)
            continue
        low, high = bounds([by_name[name]])
        offset = (low + high) / 2 - Vector(point)
        n = Vector(axis).normalized()
        off = (offset - n * offset.dot(n)).length
        print("spin check %s: %.3f off its axis%s" % (name, off, "  <-- PROBLEM" if off > 0.05 else ""))
