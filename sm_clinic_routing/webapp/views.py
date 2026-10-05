"""
views.py — HTTP-эндпоинты веб-интерфейса ArtKnit.

Страницы:
  GET  /                   — форма ввода протокола + демо-протоколы
  POST /process/           — обработка протокола через ядро маршрутизации
  GET  /doctor/<id>/       — экран врача (HTML генерируется ядром в output/)
  GET  /patient/<id>/      — экран пациента
  GET  /dashboard/         — дашборд руководителя (журнал аудита)
"""

from __future__ import annotations

import json
import logging
import time
from collections import Counter

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils.html import mark_safe
from django.views.decorators.http import require_GET, require_POST

from . import services

log = logging.getLogger("webapp.views")

OUTPUT_DIR = services.ROOT / "output"

URGENCY_META = {
    "emergency": {"label": "🚨 Срочно", "css": "u-emergency"},
    "oncological": {"label": "⚠️ Онконастороженность", "css": "u-oncological"},
    "urgent": {"label": "⏰ Ускоренно", "css": "u-urgent"},
    "planned": {"label": "📅 Планово", "css": "u-planned"},
    "observation": {"label": "👁 Наблюдение", "css": "u-observation"},
}

ERROR_MESSAGES = {
    "empty_protocol": "Вставьте текст протокола УЗИ перед отправкой.",
    "processing": "Не удалось обработать протокол. Проверьте текст и попробуйте снова.",
}


def _initials(name: str, fallback: str = "ПП") -> str:
    parts = [p for p in name.split() if p]
    if len(parts) >= 2:
        return "".join(p[0] for p in parts[:2]).upper()
    return fallback


@require_GET
def index(request):
    error = request.GET.get("error")
    demo = services.get_demo_protocols()
    return render(
        request,
        "webapp/index.html",
        {
            "demo": demo,
            "demo_json": mark_safe(json.dumps(demo, ensure_ascii=False)),
            "audit": services.read_audit(limit=8),
            "error_message": ERROR_MESSAGES.get(error, "") if error else "",
            "urgent_meta": URGENCY_META,
        },
    )


@require_POST
def process(request):
    protocol = (request.POST.get("protocol") or "").strip()
    if not protocol:
        return redirect("/?error=empty_protocol")

    study_type = (request.POST.get("study_type") or "").strip() or "УЗИ"
    study_date = (request.POST.get("study_date") or "").strip()

    patient_name = (request.POST.get("patient_name") or "").strip() or "Пациент П.П."
    card_id = (request.POST.get("card_id") or "").strip() or f"web{int(time.time())}"
    try:
        patient_age = int(request.POST.get("patient_age") or 0)
    except ValueError:
        patient_age = 0

    patient = {
        "name": patient_name,
        "initials": (request.POST.get("patient_initials") or "").strip()
        or _initials(patient_name),
        "age": patient_age,
        "sex_label": (request.POST.get("sex_label") or "").strip() or "—",
        "card_id": card_id,
    }
    doctor_name = (request.POST.get("doctor_name") or "").strip() or "Врач"
    doctor = {
        "name": doctor_name,
        "initials": (request.POST.get("doctor_initials") or "").strip()
        or _initials(doctor_name, "ВР"),
    }
    visit = {
        "date": (request.POST.get("visit_date") or "").strip() or "—",
        "time": (request.POST.get("visit_time") or "").strip() or "—",
        "doctor": doctor_name,
    }

    try:
        route, _ = services.run_pipeline(
            protocol=protocol,
            study_type=study_type,
            study_date=study_date,
            patient=patient,
            visit=visit,
            doctor=doctor,
        )
    except Exception:
        log.exception("Ошибка обработки протокола")
        return redirect("/?error=processing")

    return render(
        request,
        "webapp/result.html",
        {
            "route": route,
            "patient": patient,
            "visit": visit,
            "doctor": doctor,
            "study_type": study_type,
            "study_date": study_date,
            "doctor_url": f"/doctor/{card_id}/",
            "patient_url": f"/patient/{card_id}/",
            "urgent_meta": URGENCY_META,
        },
    )


def _serve_generated(filename: str) -> HttpResponse:
    """Отдаёт готовый HTML, сгенерированный ядром в output/."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise Http404(f"{filename} не найден — сначала обработайте протокол")
    return HttpResponse(
        path.read_text(encoding="utf-8"),
        content_type="text/html; charset=utf-8",
    )


@require_GET
def doctor_view(request, card_id: str):
    return _serve_generated(f"doctor_{card_id}.html")


@require_GET
def patient_view(request, card_id: str):
    return _serve_generated(f"patient_{card_id}.html")


@require_GET
def dashboard(request):
    records = services.read_audit(limit=200)
    by_status = Counter(r.get("status", "?") for r in records)
    by_urgency = Counter(r.get("urgency", "?") for r in records)
    by_specialist: Counter = Counter()
    for r in records:
        for spec in r.get("specialist") or []:
            by_specialist[spec] += 1

    return render(
        request,
        "webapp/dashboard.html",
        {
            "records": list(reversed(records)),
            "total": len(records),
            "by_status": by_status,
            "by_urgency": by_urgency,
            "top_specialists": by_specialist.most_common(10),
            "urgent_meta": URGENCY_META,
        },
    )