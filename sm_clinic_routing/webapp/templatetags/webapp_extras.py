"""
webapp_extras.py — Пользовательские фильтры шаблонов webapp.

Используются в Django-шаблонах интерфейса для работы со словарями
и агрегатами (словари аудита, счётчики urgency/status).
"""

from django import template

register = template.Library()


@register.filter
def get_item(mapping, key):
    """mapping[key] — доступ к элементу словаря по переменному ключу."""
    try:
        return mapping[key]
    except (KeyError, IndexError, TypeError):
        return ""


@register.filter
def split(value, sep=","):
    """str.split(sep) — разбивает строку на список."""
    try:
        return str(value).split(sep)
    except (TypeError, ValueError):
        return []


@register.filter
def count_if(iterable, key):
    """
    Считает элементы iterable, у которых значение по ключу key истинно.

    Поддерживает dict (record[key]) и объекты (getattr(record, key)).
    """
    total = 0
    for item in iterable or []:
        try:
            value = item[key]
        except (KeyError, TypeError):
            try:
                value = getattr(item, key)
            except AttributeError:
                value = None
        if value:
            total += 1
    return total