def check_condition(template, context):
    """
    Checks a condition formatted as jinja2 template.
    May raise Exceptions if the evaluation fails.
    """
    if not template:
        return True
    rendered = template.render(**context)
    return bool(eval(str(rendered)))
