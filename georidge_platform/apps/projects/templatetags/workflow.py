from django import template

register = template.Library()


@register.filter
def action_label(value):
    """Turn an audit action code like 'publish_completed' into 'Publish Completed'."""
    return str(value).replace("_", " ").title()
