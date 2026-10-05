"""
main.py — CLI для системы автоматической маршрутизации пациентов.

Режимы:
  --demo              Прогоняет 8 встроенных протоколов, создаёт HTML
  --protocol <file>   Прогоняет один протокол из файла
  --open              Открывает результат в браузере

Пайплайн:
  read → preprocessor → extractor → router → generator.render_doctor

Пример:
  python3 main.py --demo --open
  python3 main.py --protocol my_protocol.txt \
      --patient-name "Иванова А.С." --patient-age 30 \
      --study-type "УЗИ ОМТ" --study-date "26.08.2026"
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import webbrowser
from pathlib import Path

# Добавляем src/ в путь
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from config_loader import ConfigLoader
from extractor import Extractor
from generator import Generator
from router import Router

# ============================================================================
#                        ВСТРОЕННЫЕ ПРОТОКОЛЫ
# ============================================================================

DEMO_PROTOCOLS = [
    # ------------------------------------------------------------------
    # 1. ОМТ — полип эндометрия (мягкий сценарий)
    # ------------------------------------------------------------------
    {
        "label": "ОМТ (полип эндометрия)",
        "study_type": "УЗИ ОМТ",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Иванова Анна Сергеевна",
            "initials": "ИА",
            "age": 30,
            "sex_label": "женский",
            "card_id": "1024",
        },
        "doctor": {"name": "Туаева А.С.", "initials": "АТ"},
        "visit": {"date": "26.08.2026", "time": "10:30", "doctor": "Туаева А.С."},
        "protocol": """
            УЛЬТРАЗВУКОВОЕ ИССЛЕДОВАНИЕ ОРГАНОВ МАЛОГО ТАЗА
            МАТКА: положение - срединное, отклонена - кпереди, форма - седловидная
            Размеры - 50 х 38 х 52 мм.
            Структура миометрия - диффузно-неоднородная, эхогенность средняя.
            М-ЭХО - 14.0 мм, неоднородной эхоструктуры, с анэхогенными мелкими включениями.
            В полости матки лоцируется гиперэхогенное образование 12 мм - полип эндометрия.
            ПРАВЫЙ ЯИЧНИК: Размеры - 35 х 22 х 29 мм, V - 12.0 мл.
            ЛЕВЫЙ ЯИЧНИК: Размеры - 28 х 14 х 25 мм, V - 5.0 мл.
            Свободная жидкость в малом тазу: не лоцируется.
            ЗАКЛЮЧЕНИЕ: УЗ признаки полипа эндометрия, несоответствия толщины эндометрия дню цикла,
            неоднородной эхоструктуры эндометрия, диффузных изменений миометрия.
        """,
    },
    # ------------------------------------------------------------------
    # 2. ОМТ — без патологии (no_action)
    # ------------------------------------------------------------------
    {
        "label": "ОМТ (без патологии)",
        "study_type": "УЗИ ОМТ",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Смирнова Ольга Ивановна",
            "initials": "ОС",
            "age": 42,
            "sex_label": "женский",
            "card_id": "1025",
        },
        "doctor": {"name": "Туаева А.С.", "initials": "АТ"},
        "visit": {"date": "26.08.2026", "time": "11:15", "doctor": "Туаева А.С."},
        "protocol": """
            УЗИ органов малого таза.
            М-ЭХО - 6.0 мм, однородной эхоструктуры.
            Полип эндометрия не выявлен.
            Свободная жидкость в малом тазу не лоцируется.
            ЗАКЛЮЧЕНИЕ: Без патологии.
        """,
    },
    # ------------------------------------------------------------------
    # 3. ЖП — полип + холестаз (мультидисциплинарный)
    # ------------------------------------------------------------------
    {
        "label": "ЖП (полип + холестаз)",
        "study_type": "УЗИ органов брюшной полости",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Петров Сергей Андреевич",
            "initials": "СП",
            "age": 45,
            "sex_label": "мужской",
            "card_id": "1026",
        },
        "doctor": {"name": "Евгения М.В.", "initials": "ЕМ"},
        "visit": {"date": "26.08.2026", "time": "09:45", "doctor": "Евгения М.В."},
        "protocol": """
            УЗИ органов брюшной полости (комплексное).
            ПЕЧЕНЬ: правая доля КВР 143 мм. Контуры четкие, ровные.
            ЖЕЛЧНЫЙ ПУЗЫРЬ: Размерами 63 х 17 мм, грушевидной формы с загибом в области шейки.
            По боковым стенкам определяются аваскулярные гиперэхогенные пристеночные образования
            размерами 3,3 х 2,8 мм; 2,8 х 1,9 мм; 3,1 х 1,8 мм.
            В просвете определяется большое количество хлопьевидного осадка.
            ЗАКЛЮЧЕНИЕ: Полипоз и холестаз желчного пузыря.
            Рекомендовано: консультация гастроэнтеролога.
        """,
    },
    # ------------------------------------------------------------------
    # 4. ПЖ — ДГПЖ + остаточная моча
    # ------------------------------------------------------------------
    {
        "label": "ПЖ (ДГПЖ + остаточная моча)",
        "study_type": "УЗИ предстательной железы",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Сидоров Иван Иванович",
            "initials": "ИС",
            "age": 62,
            "sex_label": "мужской",
            "card_id": "1027",
        },
        "doctor": {"name": "Кузнецова А.В.", "initials": "АК"},
        "visit": {"date": "26.08.2026", "time": "10:00", "doctor": "Кузнецова А.В."},
        "protocol": """
            УЗИ предстательной железы.
            Размеры 45 х 38 х 42 мм, объем 47 см3.
            В переходной зоне определяются аденоматозные узлы до 15 мм.
            Объем остаточной мочи 87 мл.
            ЗАКЛЮЧЕНИЕ: ДГПЖ 2 степени.
        """,
    },
    # ------------------------------------------------------------------
    # 5. МЖ — фиброаденома (BI-RADS 3)
    # ------------------------------------------------------------------
    {
        "label": "МЖ (фиброаденома, BI-RADS 3)",
        "study_type": "УЗИ молочных желез",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Морозова Людмила Викторовна",
            "initials": "ЛМ",
            "age": 48,
            "sex_label": "женский",
            "card_id": "1028",
        },
        "doctor": {"name": "Кузнецова А.В.", "initials": "АК"},
        "visit": {"date": "26.08.2026", "time": "11:00", "doctor": "Кузнецова А.В."},
        "protocol": """
            УЗИ молочных желез.
            В правой молочной железе лоцируется фиброаденома 12 мм.
            BI-RADS 3.
            ЗАКЛЮЧЕНИЕ: Фиброаденома правой молочной железы.
        """,
    },
    # ------------------------------------------------------------------
    # 6. НК — стеноз ОБА 55%
    # ------------------------------------------------------------------
    {
        "label": "НК (стеноз ОБА 55%)",
        "study_type": "УЗИ артерий нижних конечностей",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Кузнецов Дмитрий Михайлович",
            "initials": "ДК",
            "age": 55,
            "sex_label": "мужской",
            "card_id": "1029",
        },
        "doctor": {"name": "Кузнецова А.В.", "initials": "АК"},
        "visit": {"date": "26.08.2026", "time": "12:00", "doctor": "Кузнецова А.В."},
        "protocol": """
            УЗИ артерий нижних конечностей.
            В ОБА определяется стеноз 55%.
            ЗАКЛЮЧЕНИЕ: Стенозирующий атеросклероз.
        """,
    },
    # ------------------------------------------------------------------
    # 7. Кардио — ГЛЖ + ФВ 45% (urgent, мультидисциплинарный)
    # ------------------------------------------------------------------
    {
        "label": "Кардио (ГЛЖ + ФВ 45%)",
        "study_type": "Эхокардиография",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Орлова Елена Петровна",
            "initials": "ЕО",
            "age": 67,
            "sex_label": "женский",
            "card_id": "1030",
        },
        "doctor": {"name": "Кузнецова А.В.", "initials": "АК"},
        "visit": {"date": "26.08.2026", "time": "14:00", "doctor": "Кузнецова А.В."},
        "protocol": """
            Эхокардиография.
            Левый желудочек: гипертрофия стенок, МЖП 14 мм.
            Фракция выброса 45%, снижена.
            Диастолическая дисфункция 1 типа.
            Легочная гипертензия, СДЛА 42 мм рт.ст.
            ЗАКЛЮЧЕНИЕ: ГЛЖ, снижение ФВ, диастолическая дисфункция.
        """,
    },
    # ------------------------------------------------------------------
    # 8. Кардио — норма (no_action)
    # ------------------------------------------------------------------
    {
        "label": "Кардио (норма)",
        "study_type": "Эхокардиография",
        "study_date": "26.08.2026",
        "patient": {
            "name": "Александрова Мария Дмитриевна",
            "initials": "МА",
            "age": 35,
            "sex_label": "женский",
            "card_id": "1031",
        },
        "doctor": {"name": "Кузнецова А.В.", "initials": "АК"},
        "visit": {"date": "26.08.2026", "time": "15:00", "doctor": "Кузнецова А.В."},
        "protocol": """
            Эхокардиография.
            Фракция выброса в норме, 62%.
            Камеры сердца не расширены.
            ЗАКЛЮЧЕНИЕ: Показатели в пределах возрастной нормы.
        """,
    },
    # ------------------------------------------------------------------
    # 9. ЩЖ — узлы + TI-RADS 3 (эндокринолог)
    # ------------------------------------------------------------------
    {
        "label": "ЩЖ (узлы + TI-RADS 3)",
        "study_type": "УЗИ щитовидной железы",
        "study_date": "11.09.2026",
        "patient": {
            "name": "Николаева Ольга Владимировна",
            "initials": "ОН",
            "age": 50,
            "sex_label": "женский",
            "card_id": "1032",
        },
        "doctor": {"name": "Юлия Ю.", "initials": "ЮЮ"},
        "visit": {"date": "11.09.2026", "time": "14:21", "doctor": "Юлия Ю."},
        "protocol": """
            УЗИ ЩИТОВИДНОЙ ЖЕЛЕЗЫ.
            Расположена обычно. Контуры ровные.
            Общий объем железы: 25,6 см куб (увеличен).
            Правая доля: 28,0х35,0х40,0 мм, объем 20,4 см куб.
            Левая доля: 15,0х16,0х40,0 мм, объем 5,2 см куб.
            Перешеек: 5,1 мм (увеличен).
            Эхоструктура: неоднородная.
            В правой доле визуализируются гиперэхогенные узлы 26х25мм, 20х17мм,
            15х14мм, 25х21мм с перинодулярным кровотоком.
            В левой доле в нижнем полюсе изоэхогенный узел 24х13мм
            с активным перинодулярным кровотоком.
            Региональные лимфоузлы: не увеличены.
            ЗАКЛЮЧЕНИЕ: Узлы в обеих долях щитовидной железы,
            увеличение кровотока. EU-TIRADS справа 3, слева 3.
        """,
    },
]


# ============================================================================
#                        ОСНОВНАЯ ЛОГИКА
# ============================================================================


def process_protocol(
    protocol: str,
    study_type: str,
    study_date: str,
    patient: dict,
    visit: dict,
    doctor: dict,
    cfg,
    ext: Extractor,
    rt: Router,
    gen: Generator,
) -> tuple[Path, object]:
    """
    Прогоняет один протокол через пайплайн и сохраняет HTML.
    Возвращает (путь_к_HTML, route).
    """
    # 1. Извлечение
    extraction = ext.extract(protocol)

    # 2. Маршрут
    route = rt.build(extraction, study_type=study_type, study_date=study_date)

    # 3. Метаданные для generator
    meta = {
        "sentences_total": extraction.sentences_total,
        "positive_count": len(extraction.positive()),
        "negative_count": len(extraction.negative()),
        "organ_codes": extraction.organ_codes or ["—"],
    }

    # 4. Генерация HTML — экран врача
    output_path = gen.render_doctor(
        route=route,
        patient=patient,
        visit=visit,
        meta=meta,
        doctor=doctor,
    )

    # 4б. Генерация HTML — экран пациента
    gen.render_patient(
        route=route,
        patient=patient,
        visit=visit,
        meta=meta,
    )

    # 5. Журнал аудита (требование ТЗ: кто, что, когда, на каком основании)
    audit_dir = Path("output")
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_file = audit_dir / "routes_audit.jsonl"

    # Собираем данные для журнала
    audit_record = {
        # Кто
        "patient_id": patient.get("card_id", "unknown"),
        "patient_name": patient.get("name", ""),
        "patient_age": patient.get("age", 0),
        "doctor": doctor.get("name", ""),
        "visit_date": visit.get("date", ""),
        "visit_time": visit.get("time", ""),
        # Что
        "finding": route.finding_summary,
        "finding_id": route.primary_finding.id if route.primary_finding else None,
        "specialist": route.specialist,
        "urgency": route.urgency,
        "deadline_days": route.deadline_days,
        "scenario": route.scenario,
        "multidisciplinary": route.multidisciplinary,
        "dispute_applied": route.dispute_applied or None,
        # Когда
        "timestamp": "2026-08-26T14:00:00",  # модельное время (или datetime.now().isoformat())
        # На каком основании
        "basis": route.basis,
        "reason": route.reason,
        "quote": route.quote,
        "status": route.status,
        "status_label": route.status_label,
        "organ_codes": meta.get("organ_codes", []),
        "sentences_total": meta.get("sentences_total", 0),
        "positive_count": meta.get("positive_count", 0),
        "negative_count": meta.get("negative_count", 0),
    }

    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_record, ensure_ascii=False) + "\n")

    return output_path, route


def print_short_report(label: str, route, output_path: Path) -> None:
    """Короткий отчёт в консоль."""
    status_icon = {
        "no_action": "✅",
        "assigned": "📋",
    }.get(route.status, "•")

    specialists = ", ".join(route.specialist) if route.specialist else "—"
    urgency_icon = {
        "emergency": "🚨",
        "oncological": "⚠️",
        "urgent": "⏰",
        "planned": "📅",
        "observation": "👁",
    }.get(route.urgency, "•")

    print(f"  {status_icon} {label}")
    print(
        f"      → {specialists} | {urgency_icon} {route.urgency} | "
        f"{route.deadline_days} дн. | {route.status_label}"
    )
    print(f"      → {output_path.name}")


def run_demo(cfg, ext, rt, gen, output_dir: Path, open_browser: bool) -> None:
    """Прогоняет все встроенные протоколы."""
    print()
    print("=" * 70)
    print(f"ДЕМО: {len(DEMO_PROTOCOLS)} протоколов")
    print(f"Выход: {output_dir.resolve()}")
    print("=" * 70)

    last_output = None

    for i, item in enumerate(DEMO_PROTOCOLS, 1):
        print(f"\n[{i}/{len(DEMO_PROTOCOLS)}] {item['label']}")
        try:
            output_path, route = process_protocol(
                protocol=item["protocol"],
                study_type=item["study_type"],
                study_date=item["study_date"],
                patient=item["patient"],
                visit=item["visit"],
                doctor=item["doctor"],
                cfg=cfg,
                ext=ext,
                rt=rt,
                gen=gen,
            )
            print_short_report(item["label"], route, output_path)
            last_output = output_path
        except (KeyError, ValueError, AttributeError, TypeError) as e:
            print(f"  ❌ Ошибка: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()

    print()
    print("=" * 70)
    print(f"ГОТОВО: создано {len(list(output_dir.glob('doctor_*.html')))} файлов")
    print(f"Открыть: file://{output_dir.resolve()}/")
    print("=" * 70)

    if open_browser and last_output:
        print(f"\n🌐 Открываю {last_output.name} в браузере...")
        webbrowser.open(f"file://{last_output.resolve()}")


def run_single(
    protocol_path: Path,
    patient_name: str,
    patient_age: int,
    study_type: str,
    study_date: str,
    cfg,
    ext,
    rt,
    gen,
    output_dir: Path,
    open_browser: bool,
) -> None:
    """Прогоняет один протокол из файла."""
    if not protocol_path.exists():
        print(f"❌ Файл не найден: {protocol_path}")
        sys.exit(1)

    protocol = protocol_path.read_text(encoding="utf-8")
    initials = "".join(p[0] for p in patient_name.split()[:2]).upper()

    patient = {
        "name": patient_name,
        "initials": initials,
        "age": patient_age,
        "sex_label": "—",
        "card_id": "auto",
    }
    visit = {
        "date": study_date or "—",
        "time": "—",
        "doctor": "—",
    }
    doctor = {"name": "Врач", "initials": "ВР"}

    print(f"\n📄 Обрабатываю {protocol_path.name}...")
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

    print()
    print("=" * 70)
    print("РЕЗУЛЬТАТ:")
    print("=" * 70)
    print(f"  status:            {route.status}")
    print(f"  specialist:        {route.specialist}")
    print(f"  urgency:           {route.urgency}")
    print(f"  deadline_days:     {route.deadline_days}")
    print(f"  scenario:          {route.scenario}")
    print(f"  multidisciplinary: {route.multidisciplinary}")
    print(f"  status_label:      {route.status_label}")
    print(f"  reason:            {route.reason}")
    print(f"  finding_summary:   {route.finding_summary}")
    print(f"  all_findings:      {len(route.all_findings)}")
    print(f"\n  HTML: file://{output_path.resolve()}")

    if open_browser:
        webbrowser.open(f"file://{output_path.resolve()}")


# ============================================================================
#                        CLI
# ============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Система автоматической маршрутизации пациентов (MVP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры:
  python3 main.py --demo --open
  python3 main.py --protocol protocol.txt --patient-name "Иванова А.С." --patient-age 30
        """,
    )

    parser.add_argument(
        "--demo", action="store_true", help="Прогнать 8 встроенных протоколов"
    )
    parser.add_argument("--protocol", type=Path, help="Путь к файлу с протоколом")
    parser.add_argument(
        "--patient-name", type=str, default="Пациент П.П.", help="ФИО пациента"
    )
    parser.add_argument("--patient-age", type=int, default=0, help="Возраст пациента")
    parser.add_argument(
        "--study-type",
        type=str,
        default="УЗИ",
        help="Тип исследования (например, 'УЗИ ОМТ')",
    )
    parser.add_argument(
        "--study-date", type=str, default="", help="Дата исследования (DD.MM.YYYY)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Папка для HTML (по умолчанию ./output)",
    )
    parser.add_argument(
        "--open", action="store_true", help="Открыть результат в браузере"
    )

    args = parser.parse_args()

    # Логирование
    logging.basicConfig(
        level=logging.WARNING,  # только предупреждения, чтобы не зашумлять
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Загрузка конфигов
    print("🔧 Загрузка конфигов...")
    loader = ConfigLoader(ROOT / "config")
    cfg = loader.load()

    # Инициализация модулей
    ext = Extractor(cfg)
    rt = Router(cfg)
    gen = Generator(
        templates_dir=ROOT / "templates",
        output_dir=args.output_dir,
    )

    print(
        f"✅ Загружено: {len(cfg.organs)} органов, "
        f"{len(cfg.disputes)} спорных ситуаций"
    )

    # Режим
    if args.demo:
        run_demo(cfg, ext, rt, gen, args.output_dir, args.open)
    elif args.protocol:
        run_single(
            protocol_path=args.protocol,
            patient_name=args.patient_name,
            patient_age=args.patient_age,
            study_type=args.study_type,
            study_date=args.study_date,
            cfg=cfg,
            ext=ext,
            rt=rt,
            gen=gen,
            output_dir=args.output_dir,
            open_browser=args.open,
        )
    else:
        parser.print_help()
        print("\n⚠️  Укажите --demo или --protocol <file>")
        sys.exit(1)


if __name__ == "__main__":
    main()
