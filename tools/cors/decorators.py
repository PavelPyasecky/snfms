from functools import wraps
from typing import Callable, Any, List

from rest_framework.response import Response

ResponseHandlerType = Callable[[Any], Response]
CorsDecoratorType = Callable[[ResponseHandlerType], ResponseHandlerType]


def allow_cors(origin: str) -> CorsDecoratorType:

    def cors_decorator(func: ResponseHandlerType):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:
            response = func(*args, **kwargs)
            response['Access-Control-Allow-Origin'] = origin
            return response
        return wrapper
    return cors_decorator


def allow_cors_headers(headers_list: List[str]) -> CorsDecoratorType:

    def cors_decorator(func: ResponseHandlerType):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:
            response = func(*args, **kwargs)
            response['Access-Control-Allow-Headers'] = ', '.join([header.strip() for header in headers_list])
            return response
        return wrapper
    return cors_decorator


def allow_cors_methods(methods_list: List[str]) -> CorsDecoratorType:

    def cors_decorator(func: ResponseHandlerType):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:
            response = func(*args, **kwargs)
            response['Access-Control-Allow-Methods'] = ', '.join([method.strip() for method in methods_list])
            return response
        return wrapper
    return cors_decorator


def cors_max_age(age: int) -> CorsDecoratorType:

    def cors_decorator(func: ResponseHandlerType):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Response:
            response = func(*args, **kwargs)
            response['Access-Control-Max-Age'] = str(age)
            return response
        return wrapper
    return cors_decorator
