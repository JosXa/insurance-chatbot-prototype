from functools import wraps


def progress(scope):
    """ Decorator to increment a counter whenever a handler is called. """

    def decorator(func):
        def wrapped(r, c, *args, **kwargs):
            counter = c.setdefault("progress", {}).setdefault(scope, 0)
            c.get_value("progress")[scope] = counter + 1
            return func(r, c, *args, **kwargs)

        return wrapped

    return decorator


def get_progress(context, scope):
    """ Returns the number of calls to callbacks registered in the specified `scope`. """
    return context.get_value("progress", {}).get(scope)
