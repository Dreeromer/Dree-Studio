"""Sting animado del logo Dree Studio.

Toma los dos SVG trazados desde el PNG original (silueta exterior y relleno
interior), les da volumen, los ilumina con la paleta del sitio y renderiza
un bucle perfecto de 5 s.
"""
import bpy
import math
import os
import sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:]
BASE = ARGS[0]
OUT = ARGS[1]

FPS = 30
DUR = 5.0
FRAMES = int(FPS * DUR)          # 150: el bucle cierra exacto
RES_X, RES_Y = 1280, 720

CREAM = (0.803, 0.769, 0.706, 1)   # #ede9e2 en lineal aproximado
GOLD = (0.510, 0.333, 0.028, 1)    # #b8952a
DARK = (0.020, 0.020, 0.024, 1)    # #07070a


def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importar(nombre_svg):
    antes = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=os.path.join(BASE, nombre_svg))
    nuevos = [o for o in bpy.data.objects if o not in antes]
    curvas = [o for o in nuevos if o.type == "CURVE"]
    bpy.ops.object.select_all(action="DESELECT")
    for o in curvas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = curvas[0]
    if len(curvas) > 1:
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active


def caja(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return mn, mx


def material(nombre, color, metallic, roughness):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = color
    b.inputs["Metallic"].default_value = metallic
    b.inputs["Roughness"].default_value = roughness
    return m


limpiar()

# ---------------------------------------------------------------- geometría
back = importar("logo-solid.svg")
back.name = "LogoContorno"
front = importar("logo-inner.svg")
front.name = "LogoRelleno"

# Normalizar: mismo encuadre para los dos, ancho 4 unidades, centrado en origen
mn, mx = caja(back)
ancho = mx.x - mn.x
escala = 3.45 / ancho          # deja aire a los lados
centro = (mn + mx) / 2

padre = bpy.data.objects.new("LogoRaiz", None)
bpy.context.collection.objects.link(padre)

for obj in (back, front):
    obj.parent = padre
    obj.matrix_parent_inverse = padre.matrix_world.inverted()

padre.scale = (escala, escala, escala)
for obj in (back, front):
    obj.location.x -= centro.x
    obj.location.y -= centro.y
    obj.location.z -= centro.z

# Volumen: el contorno es la placa gruesa de atrás, el relleno la capa que sobresale.
# Todo se expresa en unidades finales (logo = 4 de ancho) y se divide por la
# escala del padre, porque estos valores viven en el espacio local de la curva.
u = 1.0 / escala


def volumen(obj, grosor, redondeo):
    obj.data.dimensions = "2D"
    obj.data.fill_mode = "BOTH"
    obj.data.resolution_u = 6
    obj.data.extrude = grosor * u
    obj.data.bevel_depth = redondeo * u
    obj.data.bevel_resolution = 4


volumen(back, 0.085, 0.014)
volumen(front, 0.060, 0.011)
front.location.z += 0.115 * u     # se levanta por encima del contorno

# Los SVG llegan tumbados: se ponen de pie mirando a la cámara
padre.rotation_euler = (math.radians(90), 0, 0)

# El importador de SVG deja su propio material negro en la ranura 0 y la
# geometría lo usa: hay que vaciarlas antes de poner los nuestros.
# El contorno negro del original desaparecería sobre el fondo oscuro del sitio:
# se traduce a oro, que es lo que le da definición y lo ata a la paleta.
back.data.materials.clear()
front.data.materials.clear()
back.data.materials.append(material("Contorno", GOLD, 1.0, 0.26))
front.data.materials.append(material("Relleno", CREAM, 0.10, 0.32))

for obj in (back, front):
    obj.data.use_fill_caps = True
    for p in obj.data.splines:
        p.use_smooth = True

# ------------------------------------------------------------------- escena
esc = bpy.context.scene
esc.render.engine = "BLENDER_EEVEE"
esc.render.resolution_x = RES_X
esc.render.resolution_y = RES_Y
esc.render.fps = FPS
esc.frame_start = 1
esc.frame_end = FRAMES
esc.render.film_transparent = True
esc.view_settings.view_transform = "AgX"
esc.view_settings.look = "AgX - Base Contrast"

ee = esc.eevee
for attr, val in (("use_raytracing", True), ("use_bloom", True),
                  ("bloom_intensity", 0.02), ("taa_render_samples", 64),
                  ("use_gtao", True)):
    if hasattr(ee, attr):
        setattr(ee, attr, val)

# Mundo: un gris muy bajo solo para que el metal tenga qué reflejar
mundo = bpy.data.worlds.new("Mundo")
esc.world = mundo
mundo.use_nodes = True
mundo.node_tree.nodes["Background"].inputs[0].default_value = (0.035, 0.035, 0.045, 1)
mundo.node_tree.nodes["Background"].inputs[1].default_value = 1.0

# Cámara
cam_data = bpy.data.cameras.new("Camara")
cam_data.lens = 65
cam = bpy.data.objects.new("Camara", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = (0, -9.2, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
esc.camera = cam


# Blanco de mira: cada luz se orienta sola hacia el logo, así el barrido
# de la luz clave no deja de iluminarlo al desplazarse.
mira = bpy.data.objects.new("Mira", None)
bpy.context.collection.objects.link(mira)
mira.location = (0, 0, 0)


def luz(nombre, energia, color, loc, tam=6.0):
    d = bpy.data.lights.new(nombre, "AREA")
    d.energy = energia
    d.color = color
    d.size = tam
    o = bpy.data.objects.new(nombre, d)
    bpy.context.collection.objects.link(o)
    o.location = loc
    c = o.constraints.new("TRACK_TO")
    c.target = mira
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return o

# Clave: barre de lado a lado y crea el brillo que recorre el logo
clave = luz("Clave", 4000, (1.0, 0.96, 0.90), (-5, -6, 4), tam=7)
# Contra dorado: separa el logo del fondo
luz("Contra", 3000, (1.0, 0.74, 0.26), (5.5, 4.0, 2.4), tam=6)
# Relleno frío muy suave para que las sombras no se cierren del todo
luz("Relleno", 500, (0.60, 0.68, 0.90), (4.5, -7, -3), tam=9)

# ---------------------------------------------------------------- animación
# Todo se deriva de senos de periodo exacto = bucle sin salto ni parpadeo
for f in range(1, FRAMES + 1):
    t = (f - 1) / FRAMES
    a = 2 * math.pi * t

    padre.rotation_euler = (
        math.radians(90) + math.radians(2.6) * math.sin(a),
        math.radians(7.5) * math.sin(a),
        math.radians(1.4) * math.sin(2 * a),
    )
    s = escala * (1 + 0.012 * math.sin(a - math.pi / 2))
    padre.scale = (s, s, s)
    padre.keyframe_insert("rotation_euler", frame=f)
    padre.keyframe_insert("scale", frame=f)

    clave.location = (-5 + 10 * math.sin(a), -6 + 1.2 * math.cos(a), 4 - 1.5 * math.sin(a))
    clave.keyframe_insert("location", frame=f)

def fcurvas(accion):
    """Blender 5 guarda las curvas en slots; las versiones previas, directas."""
    if hasattr(accion, "fcurves"):
        return list(accion.fcurves)
    salida = []
    for capa in accion.layers:
        for tira in capa.strips:
            for cb in tira.channelbags:
                salida.extend(cb.fcurves)
    return salida


# Con una clave por fotograma, lineal evita el rebote de las asas bezier
for accion in bpy.data.actions:
    for fc in fcurvas(accion):
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

# ------------------------------------------------------------------ salida
os.makedirs(OUT, exist_ok=True)
esc.render.image_settings.file_format = "PNG"
esc.render.image_settings.color_mode = "RGBA"
esc.render.filepath = os.path.join(OUT, "f_")
print("RENDER: %d frames a %dx%d" % (FRAMES, RES_X, RES_Y))
bpy.ops.render.render(animation=True)
print("RENDER OK")
