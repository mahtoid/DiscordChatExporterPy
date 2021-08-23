from functools import wraps

_internal_cache: dict = {}


def _wrap_and_store_coroutine(cache, key, coro):
    async def func():
        value = await coro
        cache[key] = value
        return value
    return func()


def _wrap_new_coroutine(value):
    async def new_coroutine():
        return value
    return new_coroutine()


def clear_cache():
    _internal_cache.clear()


def cache():
    def decorator(func):
        def _make_key(args, kwargs):
            key = [f'{func.__module__}.{func.__name__}']
            key.extend(repr(o) for o in args)

            for k, v in kwargs.items():
                key.append(repr(k))
                key.append(repr(v))

            return ':'.join(key)

        @wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            try:
                value = _internal_cache[key]
            except KeyError:
                value = func(*args, **kwargs)
                return _wrap_and_store_coroutine(_internal_cache, key, value)
            else:
                return _wrap_new_coroutine(value)

        wrapper.cache = _internal_cache
        wrapper.clear_cache = _internal_cache.clear()
        return wrapper
    return decorator
