# Archivos de marca — Dree Studio

Generados a partir de `Logo Dree.png` (el PNG original de 1920×1080 con el fondo
beige incrustado). Ese PNG no servía como logotipo: no tenía fondo transparente
ni versión vectorial.

## Para usar

| Archivo | Cuándo |
|---|---|
| `logo-dree-oscuro.svg` | Fondos oscuros. Contorno oro `#b8952a`, relleno crema `#ede9e2`. Es la versión que usa la web. |
| `logo-dree-claro.svg` | Fondos claros. Contorno negro y relleno blanco, como el original. |
| `logo-dree-mono.svg` | Una sola tinta: sellos, bordados, serigrafía, documentos oficiales. |
| `logo-dree-transparente.png` | El original recortado, sin el fondo beige. Para cuando haga falta un mapa de bits. |

Los SVG escalan sin perder nitidez y pesan 29 KB.

## Para volver a generar la animación

- `logo-dree-3d.blend` — el proyecto de Blender, editable a mano.
- `logo_anim.py` — el script que construye la escena entera desde cero.
- `logo-solid.svg` / `logo-inner.svg` — los trazados que consume el script.

Para renderizar de nuevo:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python marca/logo_anim.py -- marca/ /ruta/de/salida

Salen 150 PNG (5 s a 30 fps, bucle exacto). Para pasarlos a vídeo web:

    ffmpeg -framerate 30 -i f_%04d.png -f lavfi -i color=c=0x07070a:s=1280x720:r=30 \
      -filter_complex "[1:v][0:v]overlay=shortest=1,format=yuv420p" -r 30 -frames:v 150 plano.mp4
    ffmpeg -i plano.mp4 -c:v libx264 -preset slow -crf 25 -movflags +faststart -an logo-anim.mp4
