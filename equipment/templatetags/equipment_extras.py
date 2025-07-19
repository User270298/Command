from django import template
from django.utils import timezone
from datetime import timedelta
from equipment.models import EquipmentRecord

register = template.Library()

@register.filter
def get_week_stats(args, org_id=None, week_start=None, week_end=None):
    # args: worker_username,org_id,week_start,week_end
    if isinstance(args, str) and ',' in args:
        parts = args.split(',')
        worker_username = parts[0]
        org_id = parts[1] if len(parts) > 1 else org_id
        week_start = parts[2] if len(parts) > 2 else week_start
        week_end = parts[3] if len(parts) > 3 else week_end
    else:
        worker_username = args
    from django.utils.dateparse import parse_datetime
    if isinstance(week_start, str):
        week_start = parse_datetime(week_start)
    if isinstance(week_end, str):
        week_end = parse_datetime(week_end)
    if not (week_start and week_end):
        return {}
    records = EquipmentRecord.objects.filter(
        user__username=worker_username,
        organization_id=org_id,
        date_created__gte=week_start,
        date_created__lt=week_end
    )
    stats = {}
    for rec in records:
        mtype = rec.measurement_type.name
        stats[mtype] = stats.get(mtype, 0) + rec.quantity
    return stats

@register.filter
def dict_sum(value):
    if isinstance(value, dict):
        return sum(value.values())
    return 0 