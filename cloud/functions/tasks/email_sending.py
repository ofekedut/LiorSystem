import requests

from api_keys import API_KEY
from app_routes_helper import api_route
from https_helper import create_response_body
from monday_helper import process_monday_items
from request_payload import RequestPayload
from tasks.parse_items import Item


@api_route("GET", "/email/data")
def get_data_for_email_request(req: RequestPayload):
    item_id = req.queryParams["item_id"]
    if not item_id:
        return create_response_body(400)
    data: list[Item] = process_monday_items(API_KEY, item_ids=[int(item_id)])
    item: Item = data[0]
    return create_response_body(200, item.serialize())


def send_request_using_make(subject: str, body_html: str, tenants: list[str], asset_ids: list[int]):
    url = 'https://hook.eu2.make.com/mn6tssa15w6w7bmbe5ekpdqwy7sbk2so'
    result = requests.post(url, json={
        'subject': subject,
        'bodyHtml': body_html,
        'tenants': tenants,
        'mondayAssetIds': asset_ids
    })
    if result.status_code != 200 and result.status_code != 201:
        return False
    return True


@api_route("POST", "/email/send")
def get_data_for_email_request(req: RequestPayload):
    item_id = req.body["item_id"]
    if not item_id:
        return create_response_body(400)

    try:
        item = process_monday_items(API_KEY, item_ids=[int(item_id)])[0]
        client_name = item.name
        asset_ids = req.body['asset_ids']
        subject = req.body["subject"]
        email_template = req.body["email_template"]
        tenants = req.body["tenants"]
        send_request_using_make(
            tenants=tenants,
            asset_ids=asset_ids,
            subject=subject,
            body_html=email_template.replace('[CLIENT_NAME]', client_name),
        )

        return create_response_body(200, {"message": "Email sent successfully"})

    except Exception as e:
        return create_response_body(500, {"error": str(e)})
