from django import template

register = template.Library()

@register.filter
def sum_field(queryset, field_name):
    """Sum a specific field from a queryset of dictionaries"""
    return sum(int(item[field_name]) for item in queryset if field_name in item)

@register.filter
def get_field(queryset, field_name):
    """Get a specific field from a queryset of dictionaries"""
    return [item[field_name] for item in queryset if field_name in item]
