from django import template

register = template.Library()

@register.filter
def get_grade_color(grade):
    if grade >= 90:
        return 'status-excellent'
    elif grade >= 80:
        return 'status-good'
    elif grade >= 70:
        return 'status-regular'
    return 'status-needs-improvement'

@register.filter
def get_progress_color(grade):
    if grade >= 90:
        return '#22c55e'
    elif grade >= 80:
        return '#3b82f6'
    elif grade >= 70:
        return '#eab308'
    return '#ef4444'