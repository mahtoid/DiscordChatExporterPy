from functools import wraps
from typing import Any, Dict, Tuple

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
        def _make_key(args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
            def _true_repr(o):
                if o.__class__.__repr__ is object.__repr__:
                    # this is how MessageConstruct can retain
                    # caching across multiple instances
                    return f'<{o.__class__.__module__}.{o.__class__.__name__}>'
                return repr(o)

            key = [f'{func.__module__}.{func.__name__}']
            key.extend(_true_repr(o) for o in args)
            for k, v in kwargs.items():
                key.append(_true_repr(k))
                key.append(_true_repr(v))

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
