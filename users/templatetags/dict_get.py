from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key)

@register.filter
def dict_sum(d, key):
    """
    Суммирует значения по ключу во вложенных словарях: {k: {'total': 1, ...}} -> сумма d[k][key]
    Пример: {{ mtypes|dict_sum:'total' }}
    """
    if not isinstance(d, dict):
        return 0
    return sum((v.get(key, 0) if isinstance(v, dict) else 0) for v in d.values()) 