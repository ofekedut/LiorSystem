import datetime
import decimal
import json


class JsonEncoderPro(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, datetime.date):
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


def create_response_body(status, response=None):
    to_return = {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
        "isBase64Encoded": False,
    }
    if response:
        if isinstance(response, str):
            to_return["body"] = response
        else:
            to_return["body"] = json.dumps(
                response,
                ensure_ascii=False,
                indent=4,
                sort_keys=True,
                cls=JsonEncoderPro,
            )
    return to_return


def create_response_body_html(status, response=None):
    return {
        "statusCode": status,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "text/html",
        },
        "body": response,
        "isBase64Encoded": False,
    }


def create_response_body_item_missing_on_monday():
    return create_response_body(400, {"message": "item was not found on Monday.com"})
