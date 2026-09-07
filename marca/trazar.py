"""Extrae del PNG original dos siluetas: la placa exterior y el relleno blanco.

La clave: dentro del contorno negro hay DOS cosas distintas, el blanco real del
logo y el beige del fondo que asoma por las contraformas (la panza de la D, la
t, la d, la o). Se separan por neutralidad de color, no por luminosidad: el
blanco es (255,255,255) y el beige es cálido, con 15 puntos entre R y B.
"""
from PIL import Image, ImageDraw
import numpy as np, cv2, re
from scipy import ndimage

SRC = "/Users/andree/Desktop/Logo Dree.png"
SCALE = 4

a = np.array(Image.open(SRC).convert("RGB")).astype(int)
lum = a.sum(2) / 3
disp = a.max(2) - a.min(2)

outline = lum < 110
cerrado = ndimage.binary_fill_holes(outline)
blanco = cerrado & (lum > 243) & (disp < 8)
blanco = ndimage.binary_closing(blanco, np.ones((3, 3)))
blanco = ndimage.binary_opening(blanco, np.ones((2, 2)))
blanco = ndimage.binary_closing(blanco, np.ones((2, 2)))

# La placa es el trazo mas su relleno. Las contraformas (el beige que asoma por
# la panza de la D, la t, la d y la o) NO se rellenan: quedan caladas de verdad.
# El blanco se dilata un pelo antes de unirlo para cerrar el borde antialiasado,
# que si no deja un anillo de huecos de un pixel y cientos de contornos basura.
# Ojo con el tamano de los operadores: las contraformas de "studio" miden pocos
# pixeles y un elemento de 5x5 se las come, dejando la palabra como un borron.
beige_dentro = cerrado & ~outline & ~blanco
beige_dentro = ndimage.binary_opening(beige_dentro, np.ones((3, 3)))
solid = cerrado & ~beige_dentro
solid = ndimage.binary_closing(solid, np.ones((3, 3)))

ys, xs = np.nonzero(solid)
x0, y0, x1, y1 = xs.min() - 4, ys.min() - 4, xs.max() + 5, ys.max() + 5
W, H = int(x1 - x0), int(y1 - y0)


def catmull(pts):
    n = len(pts)
    d = [f"M {pts[0][0]:.1f},{pts[0][1]:.1f}"]
    for i in range(n):
        p0 = np.array(pts[(i - 1) % n]); p1 = np.array(pts[i])
        p2 = np.array(pts[(i + 1) % n]); p3 = np.array(pts[(i + 2) % n])
        c1 = p1 + (p2 - p0) / 6.0
        c2 = p2 - (p3 - p1) / 6.0
        d.append(f"C {c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(d) + " Z"


def chaikin(pts, it=2):
    for _ in range(it):
        out = []
        for i in range(len(pts)):
            p, q = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
            out += [tuple(0.75 * p + 0.25 * q), tuple(0.25 * p + 0.75 * q)]
        pts = out
    return pts


def contornos(mask, min_area, eps):
    m = mask[y0:y1, x0:x1].astype(np.uint8) * 255
    m = cv2.resize(m, (W * SCALE, H * SCALE), interpolation=cv2.INTER_CUBIC)
    m = cv2.GaussianBlur(m, (7, 7), 0)
    _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)
    cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for c in cs:
        if cv2.contourArea(c) < min_area * SCALE * SCALE:
            continue
        c = cv2.approxPolyDP(c, eps * cv2.arcLength(c, True), True)
        pts = [(p[0][0] / SCALE, p[0][1] / SCALE) for p in c]
        if len(pts) >= 4:
            out.append(pts)
    return out


def escribir(nombre, listas, suave):
    d = " ".join((catmull(p) if not suave else
                  "M " + " L ".join(f"{x:.2f},{y:.2f}" for x, y in chaikin(p)) + " Z")
                 for p in listas)
    open(nombre, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<path fill-rule="evenodd" fill="#000" d="{d}"/></svg>')
    return d


c_solid = contornos(solid, 12, 0.0004)
c_inner = contornos(blanco, 8, 0.0004)
escribir("logo-solid.svg", c_solid, True)      # polilínea densa: para Blender
escribir("logo-inner.svg", c_inner, True)
b_solid = escribir("solid-bezier.svg", contornos(solid, 12, 0.0022), False)
b_inner = escribir("inner-bezier.svg", contornos(blanco, 8, 0.0022), False)
open("bezier.txt", "w").write(f"{W}\n{H}\n{b_solid}\n{b_inner}\n")
print(f"lienzo {W}x{H} | placa: {len(c_solid)} contornos | relleno blanco: {len(c_inner)} contornos")

# comprobación visual
img = Image.new("RGB", (W, H), "#07070a"); dr = ImageDraw.Draw(img)
for p in c_solid: dr.polygon(chaikin(p), fill="#b8952a")
for p in c_inner: dr.polygon(chaikin(p), fill="#ede9e2")
img.save("trazado-check.png")
