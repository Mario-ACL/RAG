# Corpus: datos personales e inteligencia artificial en México

## Caso de uso

Asistente de consulta para una organización en México que trata datos personales y usa o desarrolla sistemas de IA. Responde qué dice cada documento y debe distinguir entre una ley vigente, una guía no vinculante y una propuesta legislativa.

## Documentos

Las fuentes, fechas y sumas de verificación están en [`data/manifest.json`](../data/manifest.json).

| Documento | Tipo | Estatus | Páginas | Caracteres | Tablas |
|---|---|---|---:|---:|---:|
| LFPDPPP | Ley | Vigente; publicada en 2025, última reforma el 14-11-2025 | 24 | 66,650 | 0 |
| LGPDPPSO | Ley | Vigente; publicada en 2025, última reforma el 14-11-2025 | 37 | 136,701 | 0 |
| Reglamento de la LFPDPPP | Reglamento | Publicado como texto vigente; redactado para la ley de 2010 | 36 | 102,994 | 0 |
| Recomendaciones del INAI sobre datos personales e IA | Guía | No vinculante; edición de junio de 2024 | 48 | 93,635 | 26 |
| Evaluación de preparación en IA de UNESCO para México | Informe | No vinculante; 2024 | 74 | 201,353 | 2 |
| Principios de Chapultepec | Declaración | No vinculante; enero de 2026 | 2 | 7,425 | 0 |
| Iniciativa de Ley General para el Uso y Control de la IA | Iniciativa | Propuesta; no es ley vigente | 42 | 82,119 | 0 |
| **Total** | | | **263** | **690,877** | **28** |

Con fragmentos de 1,000 caracteres y traslape de 150, el corpus daría unos 800 chunks. Es solo una estimación: la estrategia de chunking aún no está definida.

## Por qué estos documentos

- **Tema común con traslape real.** Los derechos ARCO aparecen en las dos leyes y el reglamento (17, 46 y 22 menciones), y el consentimiento aparece en seis de los siete documentos. La IA aparece en cuatro. Así, el retriever tiene pasajes plausibles pero incorrectos entre los cuales elegir.
- **Contraste entre estrategias de retrieval.** Hay términos exactos que deberían favorecer a BM25 (`ARCO`, `LFPDPPP`, números de artículo) y conceptos que deberían favorecer a los embeddings, como pedir a una empresa que borre tus datos.
- **Confusión difícil.** La LFPDPPP y la LGPDPPSO comparten mucho vocabulario, pero una regula a particulares y la otra a sujetos obligados del sector público.
- **Autoridad distinta.** La mezcla de ley, guía y propuesta permite evaluar si el sistema presenta como vigente algo que no lo es.

## Elección del parser

Se compararon tres parsers sobre los siete documentos con [`scripts/compare_parsers.py`](../scripts/compare_parsers.py).

| Parser | Tiempo por documento | Resultado |
|---|---:|---|
| **PyMuPDF** (elegido) | 0.1 s o menos | Conserva el orden de las celdas y detecta tablas. Requiere filtrar falsos positivos. |
| pdfplumber | 0.2 a 4.9 s | Mezcla línea por línea las columnas de la tabla del INAI (p. 35). |
| pypdf | 0.1 a 1.7 s | Parte palabras, como `prese nte` y `Reglament o`. |

PyMuPDF se distribuye bajo AGPL o licencia comercial. No afecta a este proyecto académico, pero habría que revisarlo para un despliegue comercial.

## Retos de parsing

Las páginas son del PDF. En el informe de UNESCO, la página impresa es la del PDF menos 2.

| Reto | Dónde | Solución |
|---|---|---|
| Encabezados y pies repetidos en cada página | Leyes, reglamento, INAI e iniciativa | Se eliminan por repetición y posición. Son entre 5.5 y 8.2 % de las palabras en leyes, reglamento e iniciativa. |
| Encabezado con letras espaciadas (`R E C O M E N DA C I O N E S`) | INAI, todas las páginas | La comparación ignora espacios, así que también se elimina. |
| Tablas de cuatro columnas con el contenido central | INAI, pp. 33-41 | Cada fila se convierte en campos con etiqueta (`PRINCIPIO:`, `FUNDAMENTO LEGAL:`...). |
| Tablas que continúan sin encabezado | INAI, p. 13 | Se hereda el encabezado de la página anterior. |
| Casillas de verificación sin contenido | INAI, pp. 42-47 | Se eliminan las columnas `Si`, `No` y `No aplica`. |
| Falsos positivos de tablas | UNESCO: 32 detectadas, 2 reales | Se filtran por área y proporción de celdas llenas. |
| Celda combinada que separa actividades y cifras | UNESCO, Tabla 1, p. 45 | Corrección manual, verificada contra la imagen de la página. |
| Notas al pie intercaladas y marcadores pegados (`pensar33`) | INAI y UNESCO | 160 bloques de letra pequeña se guardan aparte y se quitan los marcadores. |
| Guiones de fin de línea, incluso en acrónimos (`LFPD-` y `PPP`) | INAI y UNESCO | Se unen las palabras al reconstruir los párrafos. |
| Ligaduras (`modiﬁcar`) | Principios de Chapultepec | Se reemplazan por letras normales. |
| PDF escaneado con OCR ruidoso (`II` como `11`, `Artículo 10` como `Artículo 1 O`) | Iniciativa | 92 reparaciones acotadas de numeración y 149 líneas de ruido eliminadas. |

## Verificación

[`scripts/check_corpus.py`](../scripts/check_corpus.py) compara el resultado con los PDF. Todas sus verificaciones pasan:

- **Contenido:** al menos 99.8 % de las palabras del PDF están en el texto, las notas o las líneas eliminadas registradas.
- **Numeración:** no faltan encabezados de artículo en las leyes, el reglamento ni la iniciativa. La iniciativa salta del artículo 119 al 121, pero así aparece en la propia página escaneada (p. 40).
- **Artefactos:** no quedan palabras partidas conocidas, acrónimos partidos ni marcadores pegados.
- **Fuentes:** las sumas de verificación coinciden con el manifiesto.

También se revisaron manualmente páginas de muestra, no todas las tablas: INAI 5, 13, 35, 42 y 47; UNESCO 12, 45 y 52; iniciativa 10 y 40.

## Limitaciones conocidas

- **Figuras como imagen.** Los datos de las figuras de UNESCO (numeradas hasta la 17) no se extraen. Por ejemplo, el puntaje de cada estado en la Figura 4 (p. 25) solo existe en la imagen. Las queries que dependan de ellas fallarán por parsing, no por retrieval.
- **Citas de artículos desactualizadas.** El INAI (p. 35) ubica las excepciones al consentimiento en el artículo 10 de la LFPDPPP. En la ley de 2025 están en el artículo 9, y el artículo 10 trata sobre la calidad de los datos. Es un caso útil para el análisis de errores.
- **Reglamento anterior a la ley.** Se redactó para la ley de 2010 y puede diferir de la de 2025. El decreto de 2025 ordenó armonizar los reglamentos en 90 días, pero no se encontró un sustituto.
- **Ruido residual de OCR.** Quedan errores en la iniciativa, sobre todo en sellos y firmas (p. 41), y palabras como `establ ce`.
- **Una sola iniciativa.** Se eligió porque se pudo abrir y extraer, no por ser la principal. Existen otras iniciativas sobre IA.
- **Estado legislativo.** La fuente más reciente consultada es de octubre de 2026 y no se confirmó en una fuente oficial. Las respuestas reflejan estos textos, no necesariamente el derecho vigente en otra fecha.

## Reproducir

```bash
python -m venv .venv
```

```bash
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

```bash
.venv/Scripts/python.exe scripts/parse_corpus.py
```

```bash
.venv/Scripts/python.exe scripts/check_corpus.py
```

El resultado queda en `data/parsed/`: un `.jsonl` por documento para el pipeline y un `.md` para leerlo y anotar el ground truth.
