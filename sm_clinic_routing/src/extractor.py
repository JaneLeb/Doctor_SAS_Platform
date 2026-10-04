"""
extractor.py — Извлечение триггеров из текста протокола.

Пайплайн:
  1. Разбить текст на предложения (через Preprocessor)
  2. Определить органы для каждого предложения
  3. Для каждого предложения найти совпадения с синонимами триггеров
  4. Проверить отрицания (NegationDetector)
  5. Извлечь числа (parse_measures)
  6. Сравнить с порогами (compare_with_threshold), если применимо
  7. Вернуть список Finding с объяснениями

Пример:
    ext = Extractor(config)
    result = ext.extract(protocol_text)
    for f in result.findings:
        print(f.id, f.specialist, f.urgency, f.confidence)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from negations import NegationDetector, NegationResult
from numbers import (
    Measure,
    ThresholdCheck,
    compare_with_threshold,
    find_measure_for_param,
    parse_measures,
)
from preprocessor import Preprocessor, PreprocessedText

if TYPE_CHECKING:
    from config_loader import Config, Finding as ConfigFinding, OrganTriggers

log = logging.getLogger("extractor")


# ============================================================================
#                        DATACLASSES
# ============================================================================

@dataclass
class Finding:
    """Найденный триггер."""
    id: str
    organ_code: str
    matched_synonym: str
    specialist: list[str]
    urgency: str
    sentence: str
    quote: str
    negated: bool = False
    negated_reason: str = ""
    size_check: ThresholdCheck | None = None
    confidence: float = 1.0

    def __repr__(self) -> str:
        spec = ", ".join(self.specialist) if self.specialist else "—"
        neg = " [ОТРИЦАНИЕ]" if self.negated else ""
        return f"Finding({self.id} → {spec}, {self.urgency}{neg})"


@dataclass
class ExtractionResult:
    """Результат извлечения."""
    findings: list[Finding] = field(default_factory=list)
    sentences_total: int = 0
    organ_codes: list[str] = field(default_factory=list)
    primary_organ: str = ""

    def positive(self) -> list[Finding]:
        """Только не-отрицательные находки."""
        return [f for f in self.findings if not f.negated]

    def negative(self) -> list[Finding]:
        return [f for f in self.findings if f.negated]


# ============================================================================
#                        EXTRACTOR
# ============================================================================

class Extractor:
    """
    Извлекает триггеры из текста протокола УЗИ.

    Использование:
        ext = Extractor(config)
        result = ext.extract(protocol_text)
    """

    def __init__(self, config: "Config"):
        self.config = config
        self.preprocessor = Preprocessor(config)
        self.negation_detector = NegationDetector(
            negations=config.negations,
            negation_triggers=config.negation_triggers,
        )
        log.debug("Extractor инициализирован")

    # ------------------------------------------------------------------
    #  Поиск синонимов
    # ------------------------------------------------------------------

    @staticmethod
    def _stem_word(word: str) -> str:
        """Убирает падежные окончания: 'полипа' → 'полип'."""
        if len(word) <= 4:
            return word
        vowels = "аеёиоуыэюя"
        result = word
        while len(result) > 4 and result[-1] in vowels:
            result = result[:-1]
        return result

    @classmethod
    def _synonym_to_pattern(cls, synonym: str) -> str | None:
        """
        Превращает синоним в regex с учётом окончаний.
        'полип эндометрия' → 'полип\\s+эндометри[а-яё]{0,4}'
        """
        if not synonym or len(synonym) < 3:
            return None

        syn = synonym.lower().strip()
        # Удаляем скобки и их содержимое
        syn = re.sub(r"\([^)]*\)", "", syn).strip()
        if not syn:
            return None

        words = syn.split()
        parts = []
        for w in words:
            if len(w) <= 3:
                parts.append(re.escape(w))
            else:
                stem = cls._stem_word(w)
                parts.append(rf"{re.escape(stem)}[а-яё]{{0,4}}")

        body = r"\s+".join(parts)
        return rf"(?<![а-яёa-z]){body}(?![а-яёa-z])"

    # Синонимы, которых не должно быть в УЗИ-протоколах
    SKIP_SYNONYM_MARKERS = ["(морфология)", "морфология", "гистология"]

    def _find_synonym_matches(
        self,
        sentence: str,
        finding: "ConfigFinding",
    ) -> list[tuple[str, str]]:
        """..."""
        if not sentence:
            return []

        sentence_lower = sentence.lower()
        matches: list[tuple[str, str]] = []

        for syn in finding.synonyms:
            # Пропускаем морфологические синонимы — они не для УЗИ
            if any(marker in syn.lower() for marker in self.SKIP_SYNONYM_MARKERS):
                continue

            pattern = self._synonym_to_pattern(syn)
            if not pattern:
                continue
            try:
                for m in re.finditer(pattern, sentence_lower):
                    matches.append((syn, m.group(0)))
                    break  # одна находка на синоним в предложении
            except re.error as e:
                log.warning(f"Ошибка regex для '{syn}': {e}")

        return matches
    # ------------------------------------------------------------------
    #  Извлечение цитаты
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_quote(sentence: str, matched: str, context: int = 60) -> str:
        """Возвращает фрагмент вокруг совпадения."""
        if not matched:
            return sentence[:120]
        pos = sentence.lower().find(matched.lower())
        if pos < 0:
            return sentence[:120]
        start = max(0, pos - 15)
        end = min(len(sentence), pos + len(matched) + context)
        quote = sentence[start:end].strip()
        if start > 0:
            quote = "…" + quote
        if end < len(sentence):
            quote = quote + "…"
        return quote

    # ------------------------------------------------------------------
    #  Обработка одного finding
    # ------------------------------------------------------------------

    def _process_finding(
        self,
        finding: "ConfigFinding",
        sentence: str,
        matched_synonym: str,
        matched_text: str,
    ) -> Finding | None:
        """
        Обрабатывает одно найденное совпадение: отрицание, размеры, цитата.
        """
        # 1. Проверка отрицаний
        neg_result = self.negation_detector.check(sentence, matched_synonym)

        # 2. Цитата
        quote = self._extract_quote(sentence, matched_text)

        # 3. Если отрицается — фиксируем, но не отбрасываем
        if neg_result.is_negated:
            return Finding(
                id=finding.id,
                organ_code=finding.organ_code,
                matched_synonym=matched_synonym,
                specialist=[],
                urgency="negative",
                sentence=sentence,
                quote=quote,
                negated=True,
                negated_reason=neg_result.reason,
                confidence=0.0,
            )

        # 4. Числовые пороги (если есть)
        size_check: ThresholdCheck | None = None
        if self.config.sizes:
            size_check = self._check_size_rules(sentence, finding)

        # 5. Уверенность
        confidence = 0.9
        if size_check and not size_check.triggered:
            # Размер не превышает порог → менее уверенно, но триггер остаётся
            confidence = 0.6
        if len(matched_text.split()) > 1:
            confidence = min(1.0, confidence + 0.05)

        return Finding(
            id=finding.id,
            organ_code=finding.organ_code,
            matched_synonym=matched_synonym,
            specialist=list(finding.specialist),
            urgency=finding.urgency,
            sentence=sentence,
            quote=quote,
            negated=False,
            negated_reason="",
            size_check=size_check,
            confidence=confidence,
        )

    # ------------------------------------------------------------------
    #  Числовые пороги
    # ------------------------------------------------------------------

    def _check_size_rules(
        self,
        sentence: str,
        finding: "ConfigFinding",
    ) -> ThresholdCheck | None:
        """
        Проверяет размеры в предложении против sizes.yaml.

        Ищем параметр по синонимам finding в размерах.
        Например, для "полип эндометрия" — параметр "Размер полипа".
        """
        sentence_lower = sentence.lower()

        # Ищем подходящий параметр в sizes по ключевым словам
        for organ_name, params in self.config.sizes.items():
            for param in params:
                # Ключевые слова параметра: из param.param
                param_kw = param.param.lower()
                # Отрезаем общие слова вроде "Размер"
                tokens = [
                    t for t in re.split(r"\s+", param_kw)
                    if len(t) > 3 and t not in ("размер", "общий", "объем")
                ]
                if not tokens:
                    continue

                # Ищем хотя бы одно ключевое слово параметра в предложении
                hit = any(tok in sentence_lower for tok in tokens)
                if not hit:
                    continue

                # Ищем число рядом с ключевым словом
                measure = find_measure_for_param(sentence, tokens)
                if not measure:
                    continue

                # Если у параметра есть threshold — сравниваем
                if param.threshold is not None:
                    return compare_with_threshold(
                        measure,
                        threshold=param.threshold,
                        operator=param.operator,
                        threshold_unit=param.unit,
                    )
        return None

    # ------------------------------------------------------------------
    #  RegEx-паттерны (кардио)
    # ------------------------------------------------------------------

    def _extract_regex_patterns(
        self,
        sentence: str,
    ) -> list[Finding]:
        """Применяет RegEx-паттерны из cardio_regex.yaml."""
        findings: list[Finding] = []
        cardio_re = self.config.organs.get("cardio_regex")
        if not cardio_re:
            return findings

        for pattern_finding in cardio_re.patterns:
            if not pattern_finding.regex:
                continue
            try:
                for m in re.finditer(pattern_finding.regex, sentence, re.IGNORECASE):
                    matched = m.group(0)
                    quote = self._extract_quote(sentence, matched)
                    findings.append(Finding(
                        id=pattern_finding.id,
                        organ_code="cardio_regex",
                        matched_synonym=pattern_finding.source,
                        specialist=list(pattern_finding.specialist),
                        urgency=pattern_finding.urgency,
                        sentence=sentence,
                        quote=quote,
                        negated=False,
                        confidence=0.85,
                    ))
                    break  # одна находка на паттерн
            except re.error as e:
                log.warning(f"Ошибка regex {pattern_finding.regex!r}: {e}")

        return findings

    # ------------------------------------------------------------------
    #  Главный метод
    # ------------------------------------------------------------------

    def extract(self, text: str) -> ExtractionResult:
        """
        Извлекает все триггеры из текста протокола.

        Returns:
            ExtractionResult с полями findings, sentences, органы.
        """
        if not text:
            return ExtractionResult()

        log.info("=" * 60)
        log.info("Извлечение триггеров")
        log.info("=" * 60)

        # 1. Предобработка
        pre = self.preprocessor.process(text)
        log.info(f"Предложений: {len(pre.sentences)}, "
                 f"органы: {pre.organ_codes}")

        result = ExtractionResult(
            sentences_total=len(pre.sentences),
            organ_codes=list(pre.organ_codes),
            primary_organ=pre.primary_organ,
        )

        # Если не удалось определить орган — пробуем по всем
        organ_codes_to_check = pre.organ_codes or list(self.config.organs.keys())

        # 2. Обрабатываем предложения
        for sentence in pre.sentences:
            log.debug(f"Предложение: {sentence[:80]}...")

            # 2.1. Синонимы из всех релевантных органов
            for organ_code in organ_codes_to_check:
                organ = self.config.organs.get(organ_code)
                if not organ:
                    continue
                for finding in organ.findings:
                    matches = self._find_synonym_matches(sentence, finding)
                    for syn, matched in matches:
                        f = self._process_finding(finding, sentence, syn, matched)
                        if f:
                            result.findings.append(f)

            # 2.2. RegEx-паттерны (кардио)
            regex_findings = self._extract_regex_patterns(sentence)
            result.findings.extend(regex_findings)

        # 3. Убираем дубли: один и тот же finding.id + то же предложение
        result.findings = self._deduplicate(result.findings)

        log.info(f"Найдено находок: {len(result.findings)} "
                 f"(из них негативных: {len(result.negative())})")

        return result

    @staticmethod
    def _deduplicate(findings: list[Finding]) -> list[Finding]:
        """
        Удаляет дубли.

        Ключ дедупликации:
          • (matched_synonym, sentence) — если один и тот же синоним
            найден в одном и том же предложении через разные findings,
            оставляем только первый.
          • Для одинаковых id в разных предложениях — оставляем все,
            но упорядочиваем позитивные раньше негативных.
        """
        seen = set()
        unique = []
        # Сортируем: сначала позитивные, потом негативные
        # (чтобы при дедупликации выживали позитивные)
        sorted_findings = sorted(findings, key=lambda f: (f.negated, f.id))
        for f in sorted_findings:
            key = (f.matched_synonym.lower(), f.sentence[:60])
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)
        return unique


# ============================================================================
#                        ТЕСТ
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from config_loader import ConfigLoader

    project_root = Path(__file__).resolve().parent.parent
    loader = ConfigLoader(str(project_root / "config"))
    cfg = loader.load()

    ext = Extractor(cfg)

    # --- Тестовые протоколы ---
    tests = {
        "ОМТ (полип)": """
            УЗИ органов малого таза.
            М-ЭХО - 14.0 мм, неоднородной эхоструктуры.
            В полости матки лоцируется гиперэхогенное образование 12 мм —
            полип эндометрия.
            ЗАКЛЮЧЕНИЕ: УЗ признаки полипа эндометрия.
            Рекомендовано: консультация гинеколога.
        """,
        "ОМТ (без патологии)": """
            УЗИ органов малого таза.
            Размеры матки 50 х 38 х 52 мм.
            М-ЭХО - 6.0 мм, однородной эхоструктуры.
            Полип эндометрия не выявлен.
            Свободная жидкость в малом тазу не лоцируется.
            ЗАКЛЮЧЕНИЕ: Без патологии.
        """,
        "ОМТ (реальный)": """
            УЛЬТРАЗВУКОВОЕ ИССЛЕДОВАНИЕ ОРГАНОВ МАЛОГО ТАЗА
            МАТКА: положение - срединное, размеры - 50 х 38 х 52 мм.
            Структура миометрия - диффузно-неоднородная, эхогенность средняя.
            М-ЭХО - 14.0 мм, неоднородной эхоструктуры.
            ПРАВЫЙ ЯИЧНИК: Размеры - 35 х 22 х 29 мм, V - 12.0 мл.
            ЛЕВЫЙ ЯИЧНИК: Размеры - 28 х 14 х 25 мм, V - 5.0 мл.
            Свободная жидкость в малом тазу: не лоцируется.
            ЗАКЛЮЧЕНИЕ: УЗ признаки несоответствия толщины эндометрия дню цикла,
            неоднородной эхоструктуры эндометрия, диффузных изменений миометрия.
        """,
        "ЖП (полип)": """
            УЗИ органов брюшной полости.
            ЖЕЛЧНЫЙ ПУЗЫРЬ: Размерами 63 х 17 мм.
            По боковым стенкам определяются аваскулярные гиперэхогенные
            пристеночные образования размерами 3,3 х 2,8 мм.
            В просвете определяется большое количество хлопьевидного осадка.
            ЗАКЛЮЧЕНИЕ: Полипоз и холестаз желчного пузыря.
        """,
        "ПЖ (ДГПЖ)": """
            УЗИ предстательной железы.
            Размеры 45 х 38 х 42 мм, объем 47 см³.
            В переходной зоне определяются аденоматозные узлы до 15 мм.
            Объем остаточной мочи 87 мл.
            ЗАКЛЮЧЕНИЕ: ДГПЖ 2 степени.
        """,
        "МЖ (BI-RADS 3)": """
            УЗИ молочных желез.
            В правой молочной железе лоцируется фиброаденома 12 мм.
            BI-RADS 3.
            ЗАКЛЮЧЕНИЕ: Фиброаденома правой молочной железы.
        """,
    }

    for label, protocol in tests.items():
        print("\n" + "=" * 70)
        print(f"ПРОТОКОЛ: {label}")
        print("=" * 70)
        result = ext.extract(protocol)
        print(f"Органы: {result.organ_codes}")
        print(f"Найдено: {len(result.findings)} (позитивных: "
              f"{len(result.positive())}, отрицательных: {len(result.negative())})")
        print()
        for f in result.findings:
            status = "❌ ОТРИЦ" if f.negated else "✅ НАЙДЕНО"
            spec = ", ".join(f.specialist) if f.specialist else "—"
            print(f"  {status} | {f.id}")
            print(f"           специалист: {spec}")
            print(f"           urgency: {f.urgency}, confidence: {f.confidence:.2f}")
            print(f"           синоним: {f.matched_synonym}")
            print(f"           цитата: {f.quote[:80]}")
            if f.size_check:
                print(f"           размер: triggered={f.size_check.triggered}, "
                      f"{f.size_check.reason}")
            if f.negated:
                print(f"           причина: {f.negated_reason}")
            print()