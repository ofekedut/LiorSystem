from functools import wraps

from app_routes import routes, routes_metadata, RouteMetadata


def api_route(method, route, desc=None, package=None, returns=None):
    if not route.startswith("/"):
        raise ValueError('api route route must start with "/"')

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if method not in routes:
            raise Exception("Method is not valid - {}".format(method))
        if route in routes[method]:
            raise Exception("Route taken! {}".format(routes))
        routes[method][route] = wrapper

        if method not in routes_metadata:
            raise Exception("Method is not valid - {}".format(method))
        if route in routes_metadata[method]:
            raise Exception("Route taken! {}".format(routes))
        routes_metadata[method][route] = RouteMetadata(
            name=route,
            desc=desc or '',
            queryParams={},
            body={},
            auth=0,
            package='',
            returns=returns or dict,
        )

        return wrapper

    return decorator

def create_all_src_routes(method, pathname: str):
    def decorator(func):
        for path_prefix, src in [
            ('radio', 'radio'),
            ('zohar', 'zohar'),
            ('momentum', 'momentum_top'),
        ]:
            route_path = f'/{path_prefix}{pathname}'

            @api_route(method, route_path)
            def _(req):
                return func(req, src)

    return decorator