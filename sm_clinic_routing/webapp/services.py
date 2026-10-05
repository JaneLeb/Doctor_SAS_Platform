"""
services.py — Мост между Django и ядром маршрутизации (src/).

Позволяет веб-интерфейсу переиспользовать существующий пайплайн:
ConfigLoader → Extractor → Router → Generator (Jinja2 → HTML → output/).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Корень проекта sm_clinic_routing/
ROOT = Path(__file__).resolve().parent.parent

# Модули ядра импортируются как top-level (они ожидают src/ в sys.path)
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

log = logging.getLogger("webapp.services")

_pipeline: tuple | None = None


def get_pipeline() -> tuple:
    """Лениво инициализирует пайплайн и кэширует его (один раз на процесс)."""
    global _pipeline
    if _pipeline is None:
        # Относительные пути в ядре (output/, журнал аудита) считаются от ROOT
        os.chdir(ROOT)

        from config_loader import ConfigLoader
        from extractor import Extractor
        from generator import Generator
        from router import Router

        loader = ConfigLoader(ROOT / "config")
        cfg = loader.load()
        ext = Extractor(cfg)
        rt = Router(cfg)
        gen = Generator(
            templates_dir=ROOT / "templates",
            output_dir=ROOT / "output",
        )
        _pipeline = (cfg, ext, rt, gen)
        log.info(
            "Пайплайн инициализирован: %d органов, %d спорных ситуаций",
            len(cfg.organs),
            len(cfg.disputes),
        )
    return _pipeline


def run_pipeline(
    protocol: str,
    study_type: str,
    study_date: str,
    patient: dict[str, Any],
    visit: dict[str, Any],
    doctor: dict[str, Any],
) -> tuple:
    """Прогоняет протокол через ядро; возвращает (route, output_path)."""
    from main import process_protocol

    cfg, ext, rt, gen = get_pipeline()
    output_path, route = process_protocol(
        protocol=protocol,
        study_type=study_type,
        study_date=study_date,
        patient=patient,
        visit=visit,
        doctor=doctor,
        cfg=cfg,
        ext=ext,
        rt=rt,
        gen=gen,
    )
    return route, output_path


def get_demo_protocols() -> list[dict[str, Any]]:
    """Встроенные демо-протоколы из main.py в виде плоских dict для формы."""
    from main import DEMO_PROTOCOLS

    return [
        {
            "label": item["label"],
            "study_type": item["study_type"],
            "study_date": item["study_date"],
            "protocol": item["protocol"].strip(),
            "patient_name": item["patient"]["name"],
            "patient_initials": item["patient"]["initials"],
            "patient_age": item["patient"]["age"],
            "sex_label": item["patient"]["sex_label"],
            "card_id": item["patient"]["card_id"],
            "doctor_name": item["doctor"]["name"],
            "doctor_initials": item["doctor"]["initials"],
        }
        for item in DEMO_PROTOCOLS
    ]


def read_audit(limit: int = 100) -> list[dict[str, Any]]:
    """Читает журнал аудита output/routes_audit.jsonl (последние limit записей)."""
    audit_file = ROOT / "output" / "routes_audit.jsonl"
    if not audit_file.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in audit_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            log.warning("Пропущена битая строка журнала аудита")
    return records[-limit:]