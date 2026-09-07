# Archivos de marca — Dree Studio

Todo sale de `Logo Dree.png` (el original de 1920×1080 con el fondo beige
incrustado). Ese archivo no servía como logotipo: sin transparencia, sin vector
y con el logo ocupando solo el 39% del lienzo.

## Para usar

| Archivo | Cuándo |
|---|---|
| `logo-dree-oscuro.svg` | **El que usa la web** (copiado en la raíz como `logo-dree.svg`). Contorno oro `#b8952a`, relleno crema `#ede9e2`: es la unica version en la que "studio" se lee sobre el fondo oscuro. |
| `logo-dree-claro.svg` | Fondos claros. Colores del original: contorno negro, relleno blanco. |
| `logo-dree-mono.svg` | Una sola tinta: sellos, bordados, serigrafía, documentos oficiales. |
| `logo-dree-transparente.png` | El original recortado, sin el fondo beige, por si hace falta un mapa de bits. |

Los SVG pesan 50 KB y escalan sin perder nitidez.

**Por qué el negativo.** En el original el logo vive sobre beige: el trazo es
negro y el interior de las letras, blanco. Sobre el fondo casi negro del sitio
eso no funciona — el trazo desaparece y "studio", que es una mancha maciza, se
pierde entera. La versión negativa invierte esa relación: el trazo pasa a crema
y el interior queda **calado**, no pintado, así que el fondo se ve a través. Es
un solo trazado con regla par-impar, de modo que el mismo archivo sirve sobre
cualquier fondo oscuro sin repintar nada.

Sobre fondo claro se usa `logo-dree-claro.svg`, que sí respeta los colores del
original.

**Tamaño mínimo:** "Dree" aguanta desde unos 40 px de alto; "studio" empieza a
cerrarse por debajo de ~45 px. En la barra del sitio va a 48 px, que es el
límite. Por debajo de eso conviene usar solo "Dree".

## Cómo se separan las capas

Dentro del contorno negro conviven dos cosas distintas: el blanco real del logo
y el beige del fondo que asoma por las contraformas (la panza de la D, la t, la
d y la o). No se distinguen por luminosidad, porque el beige también es claro,
sino **por neutralidad de color**: el blanco es (255,255,255) y el beige es
cálido, con 15 puntos de diferencia entre R y B. `trazar.py` hace ese corte y
saca dos siluetas: la placa exterior (con las contraformas caladas de verdad) y
el relleno blanco.

Ese mismo criterio permite bajar el umbral de brillo hasta 214 sin colar fondo,
que es lo que hace falta para que el filete interior de "studio" —de uno o dos
píxeles y antialiasado— salga continuo en vez de a trozos.

El trazado se hace a 8x con elementos morfológicos **circulares**: los cuadrados
dejan esquinas y picos que a tamaño grande se leen como trabajo mal hecho.

## Animación (no se usa en la web)

Se montó un sting en el que el logo se escribía de cero y luego se retiró del
sitio. El material queda aquí por si se retoma.

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
