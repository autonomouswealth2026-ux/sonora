"""Diccionario de pronunciación (§15).

Reglas palabra -> reemplazo, aplicadas al texto antes de sintetizar
(ver tts.apply_dictionary). Importación/exportación en PLS (XML,
estándar de ElevenLabs) para compatibilidad.
"""

import xml.etree.ElementTree as ET

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from ..schemas import PronunciationRuleCreate, PronunciationRuleUpdate
from ..security import require_auth
from ..store import store

router = APIRouter(prefix="/api/v1/pronunciation",
                   dependencies=[Depends(require_auth)])

PLS_NS = "http://www.w3.org/2005/01/pronunciation-lexicon"


@router.post("", status_code=201)
def create_rule(req: PronunciationRuleCreate):
    return store.create_rule(**req.model_dump())


@router.get("")
def list_rules(language: str | None = None):
    return {"rules": store.list_rules(language)}


@router.put("/{rule_id}")
def update_rule(rule_id: str, req: PronunciationRuleUpdate):
    changes = {k: v for k, v in req.model_dump().items() if v is not None}
    updated = store.update_rule(rule_id, **changes)
    if not updated:
        raise HTTPException(status_code=404, detail="Regla desconocida.")
    return updated


@router.delete("/{rule_id}")
def delete_rule(rule_id: str):
    if not store.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Regla desconocida.")
    return {"deleted": True, "rule_id": rule_id}


@router.post("/import")
async def import_pls(file: UploadFile = File(...)):
    """Importa un fichero .pls (XML). Devuelve cuántas reglas se crearon."""
    data = await file.read()
    if len(data) > 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichero PLS > 1 MB.")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise HTTPException(
            status_code=400, detail=f"XML PLS no válido: {exc}"
        )
    created = 0
    for lexeme in root.iter(f"{{{PLS_NS}}}lexeme"):
        grapheme = lexeme.find(f"{{{PLS_NS}}}grapheme")
        alias = lexeme.find(f"{{{PLS_NS}}}alias")
        phoneme = lexeme.find(f"{{{PLS_NS}}}phoneme")
        if grapheme is None or grapheme.text is None:
            continue
        replacement = None
        if alias is not None and alias.text:
            replacement = alias.text
        elif phoneme is not None and phoneme.text:
            replacement = phoneme.text
        if not replacement:
            continue
        store.create_rule(
            word=grapheme.text.strip(),
            replacement=replacement.strip(),
            phonetic=phoneme.text.strip() if phoneme is not None and phoneme.text else "",
            language="es",
        )
        created += 1
    return {"imported": created}


@router.get("/export")
def export_pls(language: str | None = None):
    """Exporta las reglas como fichero .pls (XML)."""
    rules = store.list_rules(language)
    lexicon = ET.Element("lexicon", {
        "version": "1.0",
        "xmlns": PLS_NS,
        "alphabet": "ipa",
        "xml:lang": language or "es-ES",
    })
    for rule in rules:
        lexeme = ET.SubElement(lexicon, "lexeme")
        grapheme = ET.SubElement(lexeme, "grapheme")
        grapheme.text = rule["word"]
        if rule.get("phonetic"):
            phoneme = ET.SubElement(lexeme, "phoneme")
            phoneme.text = rule["phonetic"]
        alias = ET.SubElement(lexeme, "alias")
        alias.text = rule["replacement"]
    xml = ET.tostring(lexicon, encoding="unicode", xml_declaration=True)
    return Response(content=xml, media_type="application/pls+xml",
                    headers={"Content-Disposition":
                             "attachment; filename=pronunciation.pls"})
