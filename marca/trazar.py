"""Trazado de alta calidad del logo Dree Studio.

Frente a la version anterior: se trabaja a 8x, se limpia con un elemento
circular en vez de cuadrado (los cuadrados dejan esquinas y picos), y se
suaviza el contorno antes de vectorizar. A tamano grande la diferencia se ve.
"""
from PIL import Image
import numpy as np, cv2
from scipy import ndimage

SRC = "/Users/andree/Desktop/Logo Dree.png"
SCALE = 8


def disco(r):
    y, x = np.ogrid[-r:r+1, -r:r+1]
    return (x*x + y*y <= r*r).astype(np.uint8)


a = np.array(Image.open(SRC).convert("RGB")).astype(int)
lum = a.sum(2)/3
disp = a.max(2) - a.min(2)

outline = lum < 110
cerrado = ndimage.binary_fill_holes(outline)
# El filete interior de "studio" mide 1-2 px y llega antialiasado: con un
# umbral de 243 se parte en trozos. Lo que separa el blanco del beige no es el
# brillo sino la neutralidad, asi que se puede bajar el brillo sin colar fondo
# (el beige tiene disp 15 y aqui se exige menos de 9).
blanco = cerrado & (lum > 214) & (disp < 9)
blanco = ndimage.binary_closing(blanco, np.ones((3, 3)))
beige = ndimage.binary_opening(cerrado & ~outline & ~blanco, np.ones((3, 3)))
solid = ndimage.binary_closing(cerrado & ~beige, np.ones((3, 3)))

ys, xs = np.nonzero(solid)
x0, y0, x1, y1 = xs.min()-4, ys.min()-4, xs.max()+5, ys.max()+5
W, H = int(x1-x0), int(y1-y0)


def catmull(pts):
    n = len(pts)
    d = [f"M {pts[0][0]:.2f},{pts[0][1]:.2f}"]
    for i in range(n):
        p0 = np.array(pts[(i-1) % n]); p1 = np.array(pts[i])
        p2 = np.array(pts[(i+1) % n]); p3 = np.array(pts[(i+2) % n])
        c1 = p1 + (p2-p0)/6.0
        c2 = p2 - (p3-p1)/6.0
        d.append(f"C {c1[0]:.2f},{c1[1]:.2f} {c2[0]:.2f},{c2[1]:.2f} {p2[0]:.2f},{p2[1]:.2f}")
    return " ".join(d) + " Z"


def trazar(mask, min_area, eps, limpieza):
    m = mask[y0:y1, x0:x1].astype(np.uint8) * 255
    m = cv2.resize(m, (W*SCALE, H*SCALE), interpolation=cv2.INTER_LANCZOS4)
    _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)
    # Quitar picos y rellenar muescas con un elemento redondo
    k = disco(limpieza)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    # Suavizar el borde: desenfoque + umbral equivale a redondear el contorno
    m = cv2.GaussianBlur(m, (0, 0), limpieza * 0.9)
    _, m = cv2.threshold(m, 127, 255, cv2.THRESH_BINARY)
    cs, _ = cv2.findContours(m, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    salida, puntos = [], 0
    for c in cs:
        if cv2.contourArea(c) < min_area * SCALE * SCALE:
            continue
        c = cv2.approxPolyDP(c, eps * cv2.arcLength(c, True), True)
        pts = [(p[0][0]/SCALE, p[0][1]/SCALE) for p in c]
        if len(pts) < 4:
            continue
        puntos += len(pts)
        salida.append(catmull(pts))
    return " ".join(salida), len(salida), puntos


d_solid, n1, p1 = trazar(solid, 12, 0.0018, 7)
d_inner, n2, p2 = trazar(blanco, 8, 0.0018, 3)
print(f"placa: {n1} contornos / {p1} puntos | relleno: {n2} contornos / {p2} puntos")
open("bezier2.txt", "w").write(f"{W}\n{H}\n{d_solid}\n{d_inner}\n")


def svg(ruta, *capas):
    cuerpo = "".join(f'<path fill-rule="evenodd" fill="{c}" d="{d}"/>' for d, c in capas)
    open(ruta, "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">{cuerpo}</svg>\n')


# Un solo trazo con el interior calado: sirve sobre cualquier fondo
unico = d_solid + " " + d_inner
svg("logo-dree-negativo.svg", (unico, "#ede9e2"))
svg("logo-dree-mono.svg", (unico, "#07070a"))
svg("logo-dree-claro.svg", (d_solid, "#07070a"), (d_inner, "#ffffff"))
# Los dos que consume el script de Blender, por separado
svg("logo-solid.svg", (d_solid, "#000"))
svg("logo-inner.svg", (d_inner, "#000"))
