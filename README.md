# Mini-proyecto RAG: datos personales e inteligencia artificial en México

Sistema RAG sobre siete documentos mexicanos en español acerca de la protección de datos personales y la inteligencia artificial. Responde qué dice cada documento y debe distinguir entre una ley vigente, una guía no vinculante y una propuesta legislativa.

El caso de uso y la justificación del corpus están en [`docs/corpus.md`](docs/corpus.md).

## Documentos

| Documento | Tipo | Archivo en `data/raw/` | Fuente |
|---|---|---|---|
| Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP) | Ley vigente | `lfpdppp.pdf` | [Cámara de Diputados](https://www.diputados.gob.mx/LeyesBiblio/pdf/LFPDPPP.pdf) |
| Ley General de Protección de Datos Personales en Posesión de Sujetos Obligados (LGPDPPSO) | Ley vigente | `lgpdppso.pdf` | [Cámara de Diputados](https://www.diputados.gob.mx/LeyesBiblio/pdf/LGPDPPSO.pdf) |
| Reglamento de la LFPDPPP (2011) | Reglamento | `reglamento_lfpdppp.pdf` | [Cámara de Diputados](https://www.diputados.gob.mx/LeyesBiblio/regley/Reg_LFPDPPP.pdf) |
| Recomendaciones para el tratamiento de datos personales derivado del uso de la IA (INAI, 2024) | Guía no vinculante | `inai_recomendaciones_ia.pdf` | [INAI](https://home.inai.org.mx//wp-content/documentos/DocumentosSectorPublico/RecomendacionesPDP-IA.pdf) |
| México: evaluación del estadío de preparación de la IA (UNESCO, 2024) | Informe no vinculante | `unesco_ram_mexico.pdf` | [ONU México](https://mexico.un.org/es/download/163921/273089) |
| Principios de Chapultepec (2026) | Declaración no vinculante | `principios_chapultepec.pdf` | [SECIHTI](https://secihti.mx/wp-content/uploads/2026/02/Principios_Chapultepec.pdf) |
| Iniciativa de Ley General para el Uso y Control de la IA (Senado, 2025) | Propuesta; no es ley | `iniciativa_ley_ia_senado.pdf` | [Gaceta del Senado](https://infosen.senado.gob.mx/sgsp/gaceta/66/2/2025-12-03-1/assets/documentos/Inic_PVEM_Sen_Guerra_sector_pub_privado.pdf) |

Los PDF no se incluyen en el repositorio porque no son de este proyecto. Sus fuentes, fechas y sumas de verificación (SHA-256) están en [`data/manifest.json`](data/manifest.json). Se descargaron el 6 de noviembre de 2026.

## Estructura

| Ruta | Contenido |
|---|---|
| `main/parser.ipynb` | Parsing con Docling: limpieza de encabezados y pies, tablas, notas al pie y texto recuperado. Cada decisión está documentada en el notebook. |
| `main/rag.ipynb` | Chunking, consultas de evaluación y, más adelante, retrieval, generación y evaluación. |
| `data/manifest.json` | Metadatos de los documentos: título, tipo, estatus, fuente y suma de verificación. |
| `data/docling/` | Salida de Docling, un JSON por documento. |
| `data/elements.jsonl` | Un registro por elemento de los PDF, con las decisiones de limpieza. Es la entrada de `rag.ipynb`. |
| `data/markdown/` | Texto limpio de cada documento por página, para leerlo y anotar las consultas. |
| `data/queries.json` | Consultas de evaluación con sus respuestas ideales y pasajes esperados (en preparación). |
| `docs/corpus.md` | Caso de uso y justificación del corpus. Su sección de parsing describe una primera versión con PyMuPDF (`scripts/`), que se reemplazó por Docling en `main/parser.ipynb`. |
| `scripts/` | Scripts de esa primera versión del parsing. Los notebooks no los usan. |

## Cómo reproducirlo

Se usó Python 3.13.

1. Crear el entorno e instalar las dependencias:

   ```bash
   python -m venv .venv
   ```

   ```bash
   .venv/Scripts/python.exe -m pip install -r requirements.txt
   ```

   En Linux o macOS, el intérprete está en `.venv/bin/python`.

2. Solo para `parser.ipynb`: descargar los siete PDF de la tabla a `data/raw/`, con los nombres de la columna «Archivo», y verificarlos:

   ```bash
   python -c "import json, hashlib, pathlib; m = json.load(open('data/manifest.json', encoding='utf-8')); [print(d['file'], 'falta' if not (p := pathlib.Path('data/raw', d['file'])).exists() else 'OK' if hashlib.sha256(p.read_bytes()).hexdigest() == d['sha256'] else 'suma distinta') for d in m['documents']]"
   ```

   «suma distinta» significa que la fuente cambió desde la descarga (por ejemplo, una reforma a la ley) y los resultados pueden no coincidir.

3. Ejecutar los notebooks desde la carpeta `main/`, en orden:
   - `parser.ipynb` necesita los PDF. La conversión con Docling se omite para los documentos que ya están en `data/docling/`; si se borran, Docling descarga sus modelos la primera vez y tarda varios minutos.
   - `rag.ipynb` lee `data/elements.jsonl`, que ya está en el repositorio, así que se puede ejecutar sin los PDF.
