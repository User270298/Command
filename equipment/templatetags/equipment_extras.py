from django import template
from django.utils import timezone
from datetime import timedelta
from equipment.models import EquipmentRecord

register = template.Library()

@register.filter
def get_week_stats(worker_username, org_id):
    now = timezone.now()
    monday = now - timedelta(days=now.weekday())
    monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    sunday = monday + timedelta(days=6, hours=23, minutes=59, seconds=59)

    records = EquipmentRecord.objects.filter(
        user__username=worker_username,
        organization_id=org_id,
        date_created__gte=monday,
        date_created__lte=sunday
    )
    stats = {}
    for rec in records:
        mtype = rec.measurement_type.name
        stats[mtype] = stats.get(mtype, 0) + rec.quantity
    return stats 