import uuid

import requests
import os

# Replace with your Monday.com API token
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQ0MTU4NTU3NywiYWFpIjoxMSwidWlkIjo2Njg2NDAxMiwiaWFkIjoiMjAyNC0xMS0yNlQxODoyNzozOC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjU3NzQwNDEsInJnbiI6ImV1YzEifQ.YySR2Gpib2unD6a2AQET_Ub-Fwg0YWs-zyIMKBY_K9s"
API_URL = "https://api.monday.com/v2"

# Replace with your board ID

# Directory to save downloaded assets
DOWNLOAD_DIR = "monday_assets"

headers = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}


def make_request(query, variables=None):
    response = requests.post(API_URL, json={"query": query, "variables": variables}, headers=headers)
    response_data = response.json()
    if "errors" in response_data:
        raise Exception(f"API Error: {response_data['errors']}")
    return response_data


def download_file(file_url, file_name):
    response = requests.get(file_url, stream=True)
    response.raise_for_status()

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f'{uuid.uuid4().hex[:8]}_{file_name}')

    with open(file_path, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    print(f"Downloaded: {file_name}")


def get_assets_from_items(items):
    for item in items:
        item_name = item.get("name")
        assets = item.get("assets", [])

        for asset in assets:
            file_url = asset.get("public_url")
            if file_url:
                file_name = f"{item_name}_{asset.get('name')}"
                download_file(file_url, file_name)
            else:
                print(f"No public URL available for asset: {asset.get('name')}")


def fetch_items(board_id, cursor=None):
    query = """
    query ($boardId: ID!, $cursor: String) {
      boards(ids: [$boardId]) {
        items_page (limit: 100, cursor: $cursor) {
          cursor
          items {
            name
            assets {
              name
              public_url
            }
            subitems {
              name
              assets {
                name
                public_url
              }
            }
          }
        }
      }
    }
    """
    variables = {"boardId": board_id, "cursor": cursor}
    data = make_request(query, variables)
    items_page = data["data"]["boards"][0]["items_page"]
    return items_page["items"], items_page["cursor"]


def fetch_boards():
    query = """
    query  {
      boards {
      id 
       name
        }
    }
    """
    data = make_request(query, {})
    data = data['data']
    data = data['boards']
    for b in data:
        print(b['id'], b['name'])


def main(b_id):
    try:
        cursor = None
        while True:
            print("Fetching board items...")
            items, cursor = fetch_items(b_id, cursor)

            print("Downloading assets from main items...")
            get_assets_from_items(items)

            print("Downloading assets from subitems...")
            for item in items:
                subitems = item.get("subitems", [])
                get_assets_from_items(subitems)

            if not cursor:
                break

        print("All assets have been downloaded.")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    # fetch_boards()
    ids = [
        (1754798480, 'Subitems of ראשי'),
        (1751338068, 'Subitems of מסמכים'),
        (1746094274, 'מסמכים'),
        (1733254561, 'ראשי'),
        (1733201864, 'מידע על גופי מימון'),
        (1733191950, 'מוצרים של גופי מימון'),
        (1663490947, 'Subitems of ביצוע(ארכיון)'),
        (1663490942, 'ביצוע(ארכיון)'),
        (1663477294, 'Subitems of השגת אישור(ארכיון)'),
        (1663477289, 'השגת אישור(ארכיון)'),
        (1663442670, 'אנשי קשר'),
        (1658868249, 'Subitems of ביצוע'),
        (1658868247, 'ביצוע'),
        (1657718289, 'Subitems of השגת אישור'),
        (1657686644, 'השגת אישור'),
        (1652348338, 'Subitems of הכנת תיק לקוח'),
        (1652242311, 'הכנת תיק לקוח'),
    ]
    for pair in ids:
        # if input(f"Donwload files for board {pair[1]}? Y/n").lower().startswith("y"):
        main(pair[0])
