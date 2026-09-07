# Archivos de marca — Dree Studio

Todo sale de `Logo Dree.png` (el original de 1920×1080 con el fondo beige
incrustado). Ese archivo no servía como logotipo: sin transparencia, sin vector
y con el logo ocupando solo el 39% del lienzo.

## Para usar

| Archivo | Cuándo |
|---|---|
| `logo-dree-oscuro.svg` | Fondos oscuros. Contorno oro `#b8952a`, relleno crema `#ede9e2`. Es el que usa la web (copiado en la raíz como `logo-dree.svg`). |
| `logo-dree-claro.svg` | Fondos claros. Contorno negro y relleno blanco, como el original. |
| `logo-dree-mono.svg` | Una sola tinta: sellos, bordados, serigrafía, documentos oficiales. |
| `logo-dree-transparente.png` | El original recortado, sin el fondo beige, por si hace falta un mapa de bits. |

Los SVG pesan 50 KB y escalan sin perder nitidez.

**Ojo con el tamaño mínimo.** "Dree" se lee bien desde unos 40 px de alto, pero
"studio" se convierte en una mancha por debajo de ~90 px: sus contraformas son
demasiado finas para el grosor del contorno. Para tamaños chicos, usar solo
"Dree" o rehacer "studio" con una tipografía que aguante.

## Cómo se separan las capas

Dentro del contorno negro conviven dos cosas distintas: el blanco real del logo
y el beige del fondo que asoma por las contraformas (la panza de la D, la t, la
d y la o). No se distinguen por luminosidad, porque el beige también es claro,
sino **por neutralidad de color**: el blanco es (255,255,255) y el beige es
cálido, con 15 puntos de diferencia entre R y B. `trazar.py` hace ese corte y
saca dos siluetas: la placa exterior (con las contraformas caladas de verdad) y
el relleno blanco.

## Para volver a generar la animación

- `logo-dree-3d.blend` — el proyecto de Blender, editable a mano.
- `logo_sting.py` — construye la escena entera desde cero.
- `trazar.py` — rehace los trazados desde el PNG original.
- `logo-solid.svg` / `logo-inner.svg` — lo que consume el script.

El revelado no es un recorte de geometría: cada material calcula su alfa
comparando la posición del punto dentro del logo con un valor "Progreso" que se
anima. Por eso el barrido respeta la forma de las letras y admite el destello
en el frente. "Dree" se escribe en el primer 62% del tiempo y "studio" del 55%
al 100%; ese reparto está en `w_arriba` y `w_abajo` dentro de `logo_sting.py`.

Renderizar:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python marca/logo_sting.py -- marca/ /ruta/de/salida

Salen 135 PNG (4.5 s a 30 fps). Para pasarlos a vídeo web:

    ffmpeg -framerate 30 -i f_%04d.png -f lavfi -i color=c=0x07070a:s=1280x720:r=30 \
      -filter_complex "[1:v][0:v]overlay=shortest=1,format=yuv420p" -r 30 -frames:v 135 plano.mp4
    ffmpeg -i plano.mp4 -c:v libx264 -preset slow -crf 26 -movflags +faststart -an logo-sting.mp4
    ffmpeg -sseof -0.2 -i plano.mp4 -frames:v 1 -q:v 3 logo-sting-poster.jpg

El fondo va aplanado a `#07070a` a propósito: el vídeo con canal alfa no es
fiable en Safari. En la web el borde se disuelve con una máscara radial en CSS,
porque tras la compresión ese negro no cae exacto sobre el fondo de la página y
si no se ve el rectángulo.
