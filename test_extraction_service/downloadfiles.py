import requests
import os

# Replace with your Monday.com API token
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQ0MTU4NTU3NywiYWFpIjoxMSwidWlkIjo2Njg2NDAxMiwiaWFkIjoiMjAyNC0xMS0yNlQxODoyNzozOC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjU3NzQwNDEsInJnbiI6ImV1YzEifQ.YySR2Gpib2unD6a2AQET_Ub-Fwg0YWs-zyIMKBY_K9s"
API_URL = "https://api.monday.com/v2"

# Replace with your board ID
BOARD_ID = 1746094274

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
    file_path = os.path.join(DOWNLOAD_DIR, file_name)

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

def main():
    try:
        cursor = None
        while True:
            print("Fetching board items...")
            items, cursor = fetch_items(BOARD_ID, cursor)

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
    main()
