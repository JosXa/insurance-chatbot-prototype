from logzero import logger as log


def progress(scope):
    """ Decorator to increment a counter whenever a handler is called. """

    def decorator(func):
        def wrapped(r, c, *args, **kwargs):
            counter = c.setdefault("progress", {}).setdefault(scope, 0)
            c.get("progress")[scope] = counter + 1
            log.debug(f"Progress of {scope} is now at {counter + 1}")
            return func(r, c, *args, **kwargs)

        wrapped.__name__ = func.__name__
        return wrapped

    return decorator


def get_progress(context, scope):
    """ Returns the number of calls to callbacks registered in the specified `scope`. """
    return context.get("progress", {}).get(scope)
