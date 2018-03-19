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
    return context.get("progress", {}).get(scope)


def on_progress_threshold(scope, count, callback):
    """
    Decorator to trigger a `callback` function when the number of calls in the
    specified `scope` reaches `count`.
    """

    def wrapped(r, c, *args, **kwargs):
        def decorator(func):
            if get_progress(c, scope) == count:
                callback(r, c)
            return func(r, c, *args, **kwargs)

        return decorator

    return wrapped
