# Cursos de astrofotografía (bonus de ASTRO)

Los cursos de Tomás Moreno se entregan aparte, a quien apoya ASTRO (10 € o más). Su contenido **no** está en este
repositorio, que es público; aquí solo está lo que los adapta al equipo de cada alumno.

- `personaliza.js`: el motor. Toma el equipo de ASTRO («Mi equipo») o del panel «Tu equipo» y:
  rellena las calculadoras, añade recuadros «Con tu equipo» (campos, escalas, NPF, muestreo planetario,
  rotación, exposición por toma, guiado) y rehace los ejemplos resueltos con el equipo del alumno.
- `ejemplos.js`: los ejemplos del curso que se rehacen (texto exacto del curso → plantilla con variables).
  Si el curso cambia una frase, hay que cambiarla aquí también.
- `empaquetar.py`: genera el paquete.

```
python3 herramientas/cursos/empaquetar.py "/ruta/a/Cursos de astrofotografia" cursos-astrofotografia-bonus.zip
```

En ASTRO: menú «Cursos (bonus)» → «Ya tengo el paquete: elegirlo…». Se instala en `<datos>/Cursos` y se abre en el
navegador con el equipo dentro. El enlace para conseguirlos se pone en `cursos.txt` (Ko-fi o Gumroad).
