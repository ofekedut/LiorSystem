from request_payload import RequestPayload
from https_helper import create_response_body
from app_routes import routes
import json


def handle_rest_req(event, context):
    print(event)
    method = event["requestContext"]["http"]["method"]
    route = event["requestContext"]["http"]["path"]
    if (
        route.startswith("/Prod")
        or route.startswith("/Dev")
        or route.startswith("/dev")
        or route.startswith("/prod")
        or route.startswith("/Qa")
        or route.startswith("/qa")
    ):
        route = (
            route.replace("/Prod", "", 1)
            .replace("/Dev", "", 1)
            .replace("/dev", "", 1)
            .replace("/prod", "", 1)
            .replace("/Qa", "", 1)
            .replace("/qa", "", 1)
        )
    if method == "POST" or method == "PUT" or method == "PATCH":
        request_body = event.get("body") or {}
        request_body = (
            json.loads(request_body) if isinstance(request_body, str) else request_body
        )
        query_string_parameters = event.get("queryStringParameters") or {}
        task = routes[method].get(route)
        if not task:
            return create_response_body(404, {"message": "endpoint not found"})
        headers = event.get("headers") or {}
        return task(
            RequestPayload(
                body=request_body,
                queryParams=query_string_parameters,
                headers=headers,
            )
        )
    elif method == "GET":
        query_string_parameters = event.get("queryStringParameters") or {}
        task = routes["GET"].get(route)
        if not task:
            return create_response_body(404, {"message": "not found"})
        return task(
            RequestPayload(
                body={},
                queryParams=query_string_parameters,
                headers=event.get("headers") or {},
            )
        )
