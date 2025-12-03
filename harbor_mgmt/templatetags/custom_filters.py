from django import template

register = template.Library()

@register.filter
def multiply(value, arg):  # ← Changed from 'mul' to 'multiply'
    """Multiply the value by the argument"""
    try:
        return float(value) * float(arg)  # ← Changed to float for decimal prices
    except (ValueError, TypeError):
        return 0