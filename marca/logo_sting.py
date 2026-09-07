"""Sting del logo Dree Studio: se escribe de cero y queda formado.

El trazado se revela por shader, no por geometría: cada material calcula su
alfa a partir de la posición del punto dentro del logo, comparada con un valor
"progreso" que se anima. Así el barrido respeta la forma real de las letras y
se puede añadir un destello en el frente de escritura.

"Dree" se escribe primero, de izquierda a derecha; "studio" entra después.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
BASE, OUT = ARGS[0], ARGS[1]
SOLO_BLEND = "--solo-blend" in ARGS

FPS = 30
FRAMES = 135                      # 4.5 s
F_ESCRITURA = 104                 # el trazado termina aquí; el resto es reposo
RES_X, RES_Y = 1280, 720

CREAM = (0.803, 0.769, 0.706, 1)
GOLD = (0.510, 0.333, 0.028, 1)
GOLD_LUZ = (1.0, 0.72, 0.22, 1)

SUAVE = 0.026                     # ancho del borde de revelado: estrecho, si no parece un borrón
CORTE_V = 0.30                    # por debajo de esta altura empieza "studio"


def importar(svg):
    antes = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=os.path.join(BASE, svg))
    curvas = [o for o in bpy.data.objects if o not in antes and o.type == "CURVE"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in curvas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = curvas[0]
    if len(curvas) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def caja(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    return (Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))),
            Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts))))


bpy.ops.wm.read_factory_settings(use_empty=True)

back = importar("logo-solid.svg"); back.name = "Placa"
front = importar("logo-inner.svg"); front.name = "Relleno"

mn, mx = caja(back)
ancho, alto = mx.x - mn.x, mx.y - mn.y
escala = 3.45 / ancho
centro = (mn + mx) / 2

padre = bpy.data.objects.new("LogoRaiz", None)
bpy.context.collection.objects.link(padre)
for o in (back, front):
    o.parent = padre
    o.matrix_parent_inverse = padre.matrix_world.inverted()
padre.scale = (escala,) * 3
for o in (back, front):
    o.location -= centro

u = 1.0 / escala


def volumen(obj, grosor, redondeo):
    obj.data.dimensions = "2D"
    obj.data.fill_mode = "BOTH"
    obj.data.resolution_u = 6
    obj.data.extrude = grosor * u
    obj.data.bevel_depth = redondeo * u
    obj.data.bevel_resolution = 4
    obj.data.use_fill_caps = True


volumen(back, 0.085, 0.014)
volumen(front, 0.060, 0.011)
front.location.z += 0.115 * u
padre.rotation_euler = (math.radians(90), 0, 0)

# --------------------------------------------------------------- materiales
# El nodo "Progreso" es el mismo objeto de datos para los dos materiales, así
# que una sola animación mantiene ambas capas perfectamente sincronizadas.
progreso_nodos = []


def material(nombre, color, metallic, roughness):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    n = nt.nodes
    bsdf = n["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Emission Color"].default_value = GOLD_LUZ

    def nodo(tipo, x, y, **kw):
        nd = n.new(tipo)
        nd.location = (x, y)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    coord = nodo("ShaderNodeTexCoord", -1800, 0)
    # Normalizar las coordenadas de objeto a 0..1 sobre la caja del logo
    resta = nodo("ShaderNodeVectorMath", -1600, 0, operation="SUBTRACT")
    resta.inputs[1].default_value = (mn.x, mn.y, 0)
    div = nodo("ShaderNodeVectorMath", -1420, 0, operation="DIVIDE")
    div.inputs[1].default_value = (ancho, alto, 1)
    sep = nodo("ShaderNodeSeparateXYZ", -1240, 0)
    nt.links.new(coord.outputs["Object"], resta.inputs[0])
    nt.links.new(resta.outputs["Vector"], div.inputs[0])
    nt.links.new(div.outputs["Vector"], sep.inputs[0])

    # Frente de escritura inclinado, como el ángulo de una pluma
    inclina = nodo("ShaderNodeMath", -1060, 220, operation="MULTIPLY_ADD")
    inclina.inputs[1].default_value = 0.07
    nt.links.new(sep.outputs["Y"], inclina.inputs[0])
    nt.links.new(sep.outputs["X"], inclina.inputs[2])

    # "Dree" ocupa el primer 62% del tiempo; "studio", del 55% al 100%
    w_arriba = nodo("ShaderNodeMath", -880, 340, operation="MULTIPLY")
    w_arriba.inputs[1].default_value = 0.62
    nt.links.new(inclina.outputs[0], w_arriba.inputs[0])

    w_abajo = nodo("ShaderNodeMath", -880, 160, operation="MULTIPLY_ADD")
    w_abajo.inputs[1].default_value = 0.45
    w_abajo.inputs[2].default_value = 0.55
    nt.links.new(inclina.outputs[0], w_abajo.inputs[0])

    es_arriba = nodo("ShaderNodeMath", -880, -20, operation="GREATER_THAN")
    es_arriba.inputs[1].default_value = CORTE_V
    nt.links.new(sep.outputs["Y"], es_arriba.inputs[0])

    w = nodo("ShaderNodeMix", -700, 240, data_type="FLOAT")
    nt.links.new(es_arriba.outputs[0], w.inputs["Factor"])
    nt.links.new(w_abajo.outputs[0], w.inputs[2])    # factor 0 -> studio
    nt.links.new(w_arriba.outputs[0], w.inputs[3])   # factor 1 -> Dree

    prog = nodo("ShaderNodeValue", -700, -20)
    prog.label = "Progreso"
    prog.outputs[0].default_value = 0.0
    progreso_nodos.append(prog)

    # d = progreso - w  ->  positivo en lo ya escrito
    d = nodo("ShaderNodeMath", -520, 120, operation="SUBTRACT")
    nt.links.new(prog.outputs[0], d.inputs[0])
    nt.links.new(w.outputs[0], d.inputs[1])

    alfa = nodo("ShaderNodeMath", -340, 220, operation="DIVIDE", use_clamp=True)
    alfa.inputs[1].default_value = SUAVE
    nt.links.new(d.outputs[0], alfa.inputs[0])
    nt.links.new(alfa.outputs[0], bsdf.inputs["Alpha"])

    # Destello en el frente: pico cuando d está cerca de 0
    centro_d = nodo("ShaderNodeMath", -340, -60, operation="SUBTRACT")
    centro_d.inputs[1].default_value = SUAVE * 0.5
    nt.links.new(d.outputs[0], centro_d.inputs[0])
    absoluto = nodo("ShaderNodeMath", -180, -60, operation="ABSOLUTE")
    nt.links.new(centro_d.outputs[0], absoluto.inputs[0])
    caida = nodo("ShaderNodeMath", -20, -60, operation="DIVIDE", use_clamp=True)
    caida.inputs[1].default_value = SUAVE * 1.6
    nt.links.new(absoluto.outputs[0], caida.inputs[0])
    invertir = nodo("ShaderNodeMath", 140, -60, operation="SUBTRACT", use_clamp=True)
    invertir.inputs[0].default_value = 1.0
    nt.links.new(caida.outputs[0], invertir.inputs[1])
    fuerza = nodo("ShaderNodeMath", 300, -60, operation="MULTIPLY")
    fuerza.inputs[1].default_value = 2.0
    nt.links.new(invertir.outputs[0], fuerza.inputs[0])
    nt.links.new(fuerza.outputs[0], bsdf.inputs["Emission Strength"])

    # Con alfa hay que evitar el ordenado por transparencia: dithered no falla
    for attr, val in (("surface_render_method", "DITHERED"),
                      ("blend_method", "HASHED")):
        if hasattr(m, attr):
            try:
                setattr(m, attr, val)
            except TypeError:
                pass
    return m


back.data.materials.clear()
front.data.materials.clear()
back.data.materials.append(material("Placa", GOLD, 1.0, 0.26))
front.data.materials.append(material("Relleno", CREAM, 0.10, 0.32))

# ------------------------------------------------------------------- escena
esc = bpy.context.scene
esc.render.engine = "BLENDER_EEVEE"
esc.render.resolution_x, esc.render.resolution_y = RES_X, RES_Y
esc.render.fps = FPS
esc.frame_start, esc.frame_end = 1, FRAMES
esc.render.film_transparent = True
esc.view_settings.view_transform = "AgX"
esc.view_settings.look = "AgX - Base Contrast"
for attr, val in (("use_raytracing", True), ("taa_render_samples", 64), ("use_gtao", True)):
    if hasattr(esc.eevee, attr):
        setattr(esc.eevee, attr, val)

mundo = bpy.data.worlds.new("Mundo")
esc.world = mundo
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.035, 0.045, 1)

cam_data = bpy.data.cameras.new("Camara")
cam_data.lens = 65
cam = bpy.data.objects.new("Camara", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0, -9.2, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
esc.camera = cam

mira = bpy.data.objects.new("Mira", None)
bpy.context.collection.objects.link(mira)


def luz(nombre, energia, color, loc, tam=6.0):
    d = bpy.data.lights.new(nombre, "AREA")
    d.energy, d.color, d.size = energia, color, tam
    o = bpy.data.objects.new(nombre, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    c = o.constraints.new("TRACK_TO")
    c.target = mira
    c.track_axis, c.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"
    return o


clave = luz("Clave", 4000, (1.0, 0.96, 0.90), (-5, -6, 4), tam=7)
luz("Contra", 3000, (1.0, 0.74, 0.26), (5.5, 4.0, 2.4), tam=6)
luz("Relleno", 500, (0.60, 0.68, 0.90), (4.5, -7, -3), tam=9)

# ---------------------------------------------------------------- animación
def suave_fin(t):
    """Suave al entrar y al salir, casi constante en medio: así se lee como un
    trazo continuo. Una caída tipo (1-t)^n adelanta demasiado el recorrido y
    la palabra aparece de golpe en el primer tercio."""
    return t * t * (3 - 2 * t)


for f in range(1, FRAMES + 1):
    if f <= F_ESCRITURA:
        t = (f - 1) / (F_ESCRITURA - 1)
        p = suave_fin(t) * (1.0 + SUAVE * 2)
    else:
        p = 1.0 + SUAVE * 2
    for nodo_p in progreso_nodos:
        nodo_p.outputs[0].default_value = p
        nodo_p.outputs[0].keyframe_insert("default_value", frame=f)

    # Reposo: una deriva mínima para que no quede una imagen congelada
    a = 2 * math.pi * (f - 1) / FRAMES
    padre.rotation_euler = (math.radians(90) + math.radians(1.6) * math.sin(a),
                            math.radians(4.5) * math.sin(a),
                            math.radians(0.8) * math.sin(2 * a))
    padre.keyframe_insert("rotation_euler", frame=f)
    clave.location = (-6 + 12 * (f - 1) / FRAMES, -6, 4 - 1.2 * math.sin(a))
    clave.keyframe_insert("location", frame=f)


def fcurvas(accion):
    if hasattr(accion, "fcurves"):
        return list(accion.fcurves)
    salida = []
    for capa in accion.layers:
        for tira in capa.strips:
            for cb in tira.channelbags:
                salida.extend(cb.fcurves)
    return salida


for accion in bpy.data.actions:
    for fc in fcurvas(accion):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

os.makedirs(OUT, exist_ok=True)
if SOLO_BLEND:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "logo-dree-3d.blend"))
    print("BLEND OK")
else:
    esc.render.image_settings.file_format = "PNG"
    esc.render.image_settings.color_mode = "RGBA"
    esc.render.filepath = os.path.join(OUT, "f_")
    bpy.ops.render.render(animation=True)
    print("RENDER OK")
