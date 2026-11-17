## Answerable questions

**Confidentiality (the ones you liked)**
| # | Question | Expected answer and where it is |
|---|---|---|
| 1 | ¿Qué obligación de confidencialidad tiene una empresa con los datos personales que maneja, y hasta cuándo dura? | The company must make sure everyone who handles the data keeps it confidential, even after their relationship ends. LFPDPPP art. 20, p. 6 |
| 2 | ¿La obligación de guardar confidencialidad es igual para empresas que para dependencias de gobierno? | Almost the same text; the public sector adds an exception for access to public information. LFPDPPP art. 20, p. 6; LGPDPPSO art. 36, p. 10 |
| 3 | ¿En qué artículo de la LFPDPPP está el deber de confidencialidad? | Art. 20. The INAI guide (p. 41) says art. 21, the 2010 numbering. |
| 4 | Si contrato un servicio en la nube, ¿el proveedor tiene que guardar confidencialidad de los datos? | Yes. Reglamento art. 52, pp. 13–14, also quoted by INAI on pp. 28 and 30. |

**Other topics**
| # | Question | Expected answer and where it is | What it tests |
|---|---|---|---|
| 5 | ¿Puedo oponerme a que un banco decida si me da un crédito usando solo un algoritmo? | Yes: the right to object to automated processing without human intervention that evaluates, for example, your economic situation. Not available when the processing is a legal obligation. LFPDPPP art. 26 fr. II, pp. 7–8 | Paraphrase; nothing in the question appears in the law's text |
| 6 | Mi app de salud guarda el historial médico de los usuarios, ¿qué tipo de consentimiento necesito? | Health data are sensitive (art. 2 fr. VI, p. 2), so consent must be express and in writing (art. 8, p. 4). INAI recommends the same (pp. 35–36). | Two steps: a definition, then a rule |
| 7 | Si le pido a una empresa que borre mis datos personales, ¿cuánto tiempo tiene para responderme? | 20 days to respond, plus 15 more to carry it out; each period can be extended once. LFPDPPP art. 31, p. 8 | "Borrar" vs. the law's "cancelación" |
| 8 | ¿Qué multa puede recibir una empresa si un empleado filtra datos personales de sus clientes? | Breaching confidentiality (art. 58 fr. VIII) is fined 200 to 320,000 times the UMA (art. 59 fr. III), up to double for sensitive data. LFPDPPP pp. 15–17 | Two articles to connect |
| 9 | ¿Qué es la privacidad desde el diseño y cómo se aplica al desarrollar un sistema de IA? | Building privacy in from the design stage: data minimisation, access control, anonymisation, explaining the logic of decisions. INAI pp. 22–23 | A developer's question |
| 10 | ¿Qué le recomienda la UNESCO a México para regular la inteligencia artificial? | Identify which existing norms apply, regulate by principles and risk management, and consider banning high-risk systems. UNESCO Tabla 2, p. 52, and p. 54 | One of the tables, without forcing it |
| 11 | ¿México ya firmó la actualización del Convenio 108 sobre protección de datos? | Not at the time of the report. UNESCO p. 22 | A single fact, phrased like a lawyer would |
| 12 | ¿Qué dicen los Principios de Chapultepec sobre quién responde por una decisión tomada con IA? | Every AI-supported decision must have human responsible parties, and "if a decision can't be explained, it shouldn't be automated". Pp. 1–2 | The non-binding declaration |
| 13 | Si se aprueba la iniciativa de ley de IA del Senado, ¿qué castigo tendría usar IA para suplantar la identidad de alguien? | 1 to 5 years in prison and 400 to 600 días multa; it's only a proposal. Art. 112, p. 38 | The scanned bill (its OCR text reads "uno .a cinco") |
| 14 | ¿La iniciativa de ley de IA obligaría a las empresas a capacitar a sus empleados en IA? | Yes, linked to art. 153 of the Ley Federal del Trabajo. Art. 67, p. 29 | The bill, one passage |
| 15 | ¿La ley de protección de datos personales aplica cuando una empresa usa inteligencia artificial? | The LFPDPPP never mentions AI, but UNESCO (p. 19) says its principles apply to data used in AI. Art. 26 fr. II covers automated decisions. | Combining what a document says with what it doesn't say |

## Traps
| # | Question | Why it's a trap and what the right answer says |
|---|---|---|
| 16 | ¿Qué multas establece la ley de inteligencia artificial que está vigente en México? | **False premise:** there's no AI law in force. UNESCO (p. 19) lists only laws that apply indirectly, plus bills introduced in 2023. The Senate bill proposes penalties (e.g., art. 109) but isn't law. |
| 17 | ¿Cómo presento una queja ante el INAI si una empresa no responde mi solicitud para borrar mis datos? | **Outdated premise:** the complaint now goes to the Secretaría Anticorrupción y Buen Gobierno (LFPDPPP arts. 2 and 40). A transitional article (p. 18) says references to the INAI now apply to the bodies that took over its functions. The INAI guide and the Reglamento still name the INAI. |
| 18 | Si mi empresa sufre un hackeo con datos de clientes, ¿tengo 72 horas para avisar a la autoridad? | **Near miss:** the documents set no 72-hour deadline. For companies, the LFPDPPP (art. 19) and Reglamento (art. 64) require informing affected people immediately; only the public-sector law mentions notifying an authority. |
| 19 | ¿Qué dice la Ley Federal del Trabajo sobre vigilar con IA a los empleados? | **Not in the corpus:** that law isn't among the documents. The only mention is the bill's art. 67, which is about training, so retrieval will bring back something plausible but wrong. |
| 20 | ¿Cuál es la multa máxima del reglamento europeo de protección de datos (RGPD)? | **Not in the corpus:** the RGPD is mentioned only once, for a definition (INAI p. 8). Easier to spot than #19. |

## Suggested set of 10
**2, 3, 4, 5, 6, 10, 12, 13, 16, 17.**
- **All 7 documents are covered.**
- **Confidentiality gets 3 questions,** the ones that each test something different.
- **There's a mix** of one-passage and two-passage questions, and of questions that name a document and ones that don't.
- **It has the minimum 2 traps.** If you want a third, #18 is the best swap.

Pick freely; you can also edit the wording. Once you choose, I'll search all 7 documents for every passage that answers each question and write the quotes and ideal answers into `data/queries.json` for you to review. After that, the last decision is how the traps are scored.