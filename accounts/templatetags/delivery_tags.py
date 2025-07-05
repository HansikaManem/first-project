from django import template

register = template.Library()

@register.filter
def get_next_status(status):
    transitions = {
        'Accepted': 'In Transit',
        'In Transit': 'Delivered',
    }
    return transitions.get(status, None)
