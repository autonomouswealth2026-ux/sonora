"""Almacenamiento local: SQLite + ficheros en DATA_DIR.

Tablas:
- voices: voces clonadas y diseñadas (con consent_note obligatorio
  para las clonadas; sin consentimiento no hay clonación).
- history: cada generación (texto, voz, modelo, duración, fichero).
- pronunciation_rules: diccionario de pronunciación.
- jobs: trabajos asíncronos (doblaje; el resto de jobs 501 no usan tabla).
- dubbing_segments: segmentos de cada trabajo de doblaje.

El borrado de una voz borra de verdad su audio de referencia y sus
previews (checklist replica-backend: "account deletion that actually
deletes", adaptado a voces). Los audios generados viven en
DATA_DIR/audio y se sirven solo por su id, nunca por ruta.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .config import settings


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"


SCHEMA = """
CREATE TABLE IF NOT EXISTS voices (
    voice_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    source TEXT NOT NULL,              -- kokoro | cloned | designed
    language TEXT NOT NULL DEFAULT 'es',
    description TEXT DEFAULT '',
    model TEXT DEFAULT '',
    reference_path TEXT,               -- audio de referencia (clonadas)
    reference_text TEXT DEFAULT '',    -- transcripción de la referencia
    design_prompt TEXT DEFAULT '',     -- prompt de diseño (diseñadas)
    consent_note TEXT DEFAULT '',      -- obligatorio en clonadas
    favorite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS history (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    type TEXT NOT NULL,                -- tts | dialogue | sfx | music | dubbing | stt | isolate
    text TEXT DEFAULT '',
    voice_id TEXT DEFAULT '',
    model TEXT DEFAULT '',
    duration_s REAL DEFAULT 0,
    characters INTEGER DEFAULT 0,
    audio_path TEXT DEFAULT '',
    audio_format TEXT DEFAULT 'mp3'
);
CREATE TABLE IF NOT EXISTS pronunciation_rules (
    rule_id TEXT PRIMARY KEY,
    word TEXT NOT NULL,
    replacement TEXT NOT NULL,
    phonetic TEXT DEFAULT '',
    language TEXT NOT NULL DEFAULT 'es',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,                -- dubbing
    status TEXT NOT NULL,              -- queued | processing | done | failed
    stage TEXT DEFAULT '',
    progress REAL NOT NULL DEFAULT 0,
    error TEXT DEFAULT '',
    result_path TEXT DEFAULT '',
    payload TEXT DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS dubbing_segments (
    job_id TEXT NOT NULL,
    n INTEGER NOT NULL,
    language TEXT NOT NULL DEFAULT '',
    start_ms INTEGER NOT NULL,
    end_ms INTEGER NOT NULL,
    speaker TEXT DEFAULT '',
    source_text TEXT DEFAULT '',
    translated_text TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    audio_path TEXT DEFAULT '',
    PRIMARY KEY (job_id, n, language)
);
"""


class Store:
    def __init__(self, data_dir: Path | None = None) -> None:
        self.data_dir = Path(data_dir or settings.data_dir)
        self.audio_dir = self.data_dir / "audio"
        self.voices_dir = self.data_dir / "voices"
        self.db_path = self.data_dir / "clon.db"
        for d in (self.data_dir, self.audio_dir, self.voices_dir):
            d.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            # Migración A1: bases creadas antes de la columna language.
            cols = [r[1] for r in conn.execute(
                "PRAGMA table_info(dubbing_segments)").fetchall()]
            if cols and "language" not in cols:
                conn.execute(
                    "ALTER TABLE dubbing_segments "
                    "ADD COLUMN language TEXT NOT NULL DEFAULT ''")

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # -- voces ------------------------------------------------------------
    def create_voice(self, **fields) -> dict:
        fields.setdefault("voice_id", new_id("v_"))
        fields.setdefault("created_at", utcnow())
        cols = ", ".join(fields)
        marks = ", ".join("?" for _ in fields)
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO voices ({cols}) VALUES ({marks})",
                list(fields.values()),
            )
        return self.get_voice(fields["voice_id"])

    def get_voice(self, voice_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM voices WHERE voice_id = ?", (voice_id,)
            ).fetchone()
        return dict(row) if row else None

    def list_voices(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM voices ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_voice(self, voice_id: str) -> dict | None:
        voice = self.get_voice(voice_id)
        if not voice:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM voices WHERE voice_id = ?", (voice_id,))
        # Borrado real del audio de referencia y sus previews.
        ref = voice.get("reference_path") or ""
        if ref:
            try:
                Path(ref).unlink(missing_ok=True)
            except OSError:
                pass
        voice_dir = self.voices_dir / voice_id
        if voice_dir.exists():
            for p in voice_dir.iterdir():
                try:
                    p.unlink()
                except OSError:
                    pass
            try:
                voice_dir.rmdir()
            except OSError:
                pass
        return voice

    def set_favorite(self, voice_id: str, favorite: bool) -> dict | None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE voices SET favorite = ? WHERE voice_id = ?",
                (1 if favorite else 0, voice_id),
            )
        return self.get_voice(voice_id)

    # -- historial ----------------------------------------------------------
    def add_history(self, **fields) -> dict:
        fields.setdefault("id", new_id("gen_"))
        fields.setdefault("created_at", utcnow())
        cols = ", ".join(fields)
        marks = ", ".join("?" for _ in fields)
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO history ({cols}) VALUES ({marks})",
                list(fields.values()),
            )
        return fields

    def list_history(
        self, voice_id: str | None = None, since: str | None = None,
        limit: int = 50, offset: int = 0,
    ) -> tuple[int, list[dict]]:
        where, params = [], []
        if voice_id:
            where.append("voice_id = ?")
            params.append(voice_id)
        if since:
            where.append("created_at >= ?")
            params.append(since)
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        with self._connect() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) FROM history {clause}", params
            ).fetchone()[0]
            rows = conn.execute(
                f"SELECT * FROM history {clause} "
                "ORDER BY created_at DESC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
        return total, [dict(r) for r in rows]

    def get_history(self, gen_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM history WHERE id = ?", (gen_id,)
            ).fetchone()
        return dict(row) if row else None

    def delete_history(self, gen_id: str) -> dict | None:
        item = self.get_history(gen_id)
        if not item:
            return None
        with self._connect() as conn:
            conn.execute("DELETE FROM history WHERE id = ?", (gen_id,))
        audio = item.get("audio_path") or ""
        if audio:
            try:
                Path(audio).unlink(missing_ok=True)
            except OSError:
                pass
        return item

    def usage(self) -> dict:
        with self._connect() as conn:
            total_chars = conn.execute(
                "SELECT COALESCE(SUM(characters), 0) FROM history"
            ).fetchone()[0]
            total_min = conn.execute(
                "SELECT COALESCE(SUM(duration_s), 0) FROM history"
            ).fetchone()[0]
            by_model = {
                r["model"]: r["n"]
                for r in conn.execute(
                    "SELECT model, COUNT(*) n FROM history GROUP BY model"
                ).fetchall()
            }
            by_voice = {
                r["voice_id"]: r["n"]
                for r in conn.execute(
                    "SELECT voice_id, COUNT(*) n FROM history GROUP BY voice_id"
                ).fetchall()
            }
        return {
            "total_characters": int(total_chars),
            "total_minutes": round(float(total_min) / 60, 2),
            "by_model": by_model,
            "by_voice": by_voice,
        }

    # -- pronunciación ------------------------------------------------------
    def create_rule(self, **fields) -> dict:
        fields.setdefault("rule_id", new_id("rule_"))
        fields.setdefault("created_at", utcnow())
        cols = ", ".join(fields)
        marks = ", ".join("?" for _ in fields)
        with self._connect() as conn:
            conn.execute(
                f"INSERT INTO pronunciation_rules ({cols}) VALUES ({marks})",
                list(fields.values()),
            )
            row = conn.execute(
                "SELECT * FROM pronunciation_rules WHERE rule_id = ?",
                (fields["rule_id"],),
            ).fetchone()
        return dict(row)

    def list_rules(self, language: str | None = None) -> list[dict]:
        with self._connect() as conn:
            if language:
                rows = conn.execute(
                    "SELECT * FROM pronunciation_rules WHERE language = ? "
                    "ORDER BY word",
                    (language,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM pronunciation_rules ORDER BY word"
                ).fetchall()
        return [dict(r) for r in rows]

    def update_rule(self, rule_id: str, **fields) -> dict | None:
        if not fields:
            return self.get_rule(rule_id)
        sets = ", ".join(f"{k} = ?" for k in fields)
        with self._connect() as conn:
            conn.execute(
                f"UPDATE pronunciation_rules SET {sets} WHERE rule_id = ?",
                [*fields.values(), rule_id],
            )
        return self.get_rule(rule_id)

    def get_rule(self, rule_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM pronunciation_rules WHERE rule_id = ?",
                (rule_id,),
            ).fetchone()
        return dict(row) if row else None

    def delete_rule(self, rule_id: str) -> bool:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM pronunciation_rules WHERE rule_id = ?", (rule_id,)
            )
            return cur.rowcount > 0

    # -- jobs (doblaje) -----------------------------------------------------
    def create_job(self, kind: str, payload: dict | None = None) -> dict:
        job_id = new_id("job_")
        now = utcnow()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, kind, status, stage, progress, "
                "payload, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (job_id, kind, "queued", "queued", 0,
                 json.dumps(payload or {}), now, now),
            )
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
            ).fetchone()
        if not row:
            return None
        job = dict(row)
        job["payload"] = json.loads(job.get("payload") or "{}")
        return job

    def update_job(self, job_id: str, **fields) -> dict | None:
        fields["updated_at"] = utcnow()
        sets = ", ".join(f"{k} = ?" for k in fields)
        values = [
            json.dumps(v) if k == "payload" else v
            for k, v in fields.items()
        ]
        with self._connect() as conn:
            conn.execute(
                f"UPDATE jobs SET {sets} WHERE job_id = ?",
                [*values, job_id],
            )
        return self.get_job(job_id)

    def save_segments(self, job_id: str, segments: list[dict],
                      language: str = "") -> None:
        # A1: antes se borraban TODOS los segmentos del job en cada
        # idioma y solo quedaba el último. Ahora se borran solo los
        # de este idioma.
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM dubbing_segments "
                "WHERE job_id = ? AND language = ?", (job_id, language))
            for i, s in enumerate(segments):
                conn.execute(
                    "INSERT INTO dubbing_segments "
                    "(job_id, n, language, start_ms, end_ms, speaker, "
                    " source_text, translated_text, status) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (job_id, i, language, int(s["start_ms"]),
                     int(s["end_ms"]), s.get("speaker", ""),
                     s.get("source_text", ""),
                     s.get("translated_text", ""),
                     s.get("status", "pending")),
                )

    def list_segments(self, job_id: str,
                      language: str | None = None) -> list[dict]:
        with self._connect() as conn:
            if language is None:
                rows = conn.execute(
                    "SELECT * FROM dubbing_segments WHERE job_id = ? "
                    "ORDER BY language, n",
                    (job_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM dubbing_segments WHERE job_id = ? "
                    "AND language = ? ORDER BY n",
                    (job_id, language),
                ).fetchall()
        return [dict(r) for r in rows]

    def update_segment(
        self, job_id: str, n: int, language: str | None = None,
        **fields
    ) -> dict | None:
        sets = ", ".join(f"{k} = ?" for k in fields)
        with self._connect() as conn:
            if language is None:
                conn.execute(
                    f"UPDATE dubbing_segments SET {sets} "
                    "WHERE job_id = ? AND n = ?",
                    [*fields.values(), job_id, n],
                )
            else:
                conn.execute(
                    f"UPDATE dubbing_segments SET {sets} "
                    "WHERE job_id = ? AND n = ? AND language = ?",
                    [*fields.values(), job_id, n, language],
                )
            row = conn.execute(
                "SELECT * FROM dubbing_segments WHERE job_id = ? AND n = ? "
                "ORDER BY language LIMIT 1",
                (job_id, n),
            ).fetchone() if language is None else conn.execute(
                "SELECT * FROM dubbing_segments "
                "WHERE job_id = ? AND n = ? AND language = ?",
                (job_id, n, language),
            ).fetchone()
        return dict(row) if row else None


# Instancia compartida por todos los routers.
store = Store()
