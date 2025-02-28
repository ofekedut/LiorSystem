import json
import os
import re
import uuid
import requests

# ================================
# Configuration & Constants
# ================================

# Replace with your Monday.com API token
API_TOKEN_bar = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQ0MTYyMzM0MSwiYWFpIjoxMSwidWlkIjo2OTAxMjk3MSwiaWFkIjoiMjAyNC0xMS0yNlQxOTo0Mjo0Ni4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjY1NzYwMTUsInJnbiI6ImV1YzEifQ.uyqvVWDoYcLq1p-jEgSMvLQIa4zt_pPiX4Hbx0B8Jpk"
API_TOKEN_lior = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQ0MTU4NTU3NywiYWFpIjoxMSwidWlkIjo2Njg2NDAxMiwiaWFkIjoiMjAyNC0xMS0yNlQxODoyNzozOC4wMDBaIiwicGVyIjoibWU6d3JpdGUiLCJhY3RpZCI6MjU3NzQwNDEsInJnbiI6ImV1YzEifQ.YySR2Gpib2unD6a2AQET_Ub-Fwg0YWs-zyIMKBY_K9s"
API_TOKEN = API_TOKEN_bar
API_URL = "https://api.monday.com/v2"

# Base directory to save downloaded assets and metadata
DOWNLOAD_DIR = "../server/features/docs_processing/monday_assets_bar"

# File to track boards that have already been processed
DONE_BOARDS_FILE = "done_boards.json"

# HTTP headers for Monday.com API
headers = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}


# ================================
# Helper Functions
# ================================

def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be safe for use as a file or folder name.
    Replaces any character that is not alphanumeric, space, hyphen or underscore.
    """
    sanitized = re.sub(r"[^\w\s-]", "", name).strip()
    return sanitized.replace(" ", "_")


def build_download_path(base_dir: str, board_id: str, board_name: str,
                        item_id: str, item_name: str,
                        subitem_id: str = None, subitem_name: str = None) -> str:
    """
    Build the directory path for an asset download.
    If subitem info is provided, nest the subitem folder under the item folder.
    """
    board_folder = f"{board_id}_{sanitize_filename(board_name)}"
    item_folder = f"{item_id}_{sanitize_filename(item_name)}"
    if subitem_id and subitem_name:
        subitem_folder = f"{subitem_id}_{sanitize_filename(subitem_name)}"
        return os.path.join(base_dir, board_folder, item_folder, "subitems", subitem_folder)
    else:
        return os.path.join(base_dir, board_folder, item_folder)


def download_file(directory_path: str, file_name: str, file_url: str):
    """
    Download a file from the provided URL into the specified directory.
    Appends a short UUID to the file name to avoid collisions.
    """
    response = requests.get(file_url, stream=True)
    response.raise_for_status()

    # Ensure the directory exists
    os.makedirs(directory_path, exist_ok=True)

    unique_suffix = f"_{uuid.uuid4().hex[:8]}"
    sanitized_name = sanitize_filename(file_name)
    file_path = os.path.join(directory_path, f"{sanitized_name}{unique_suffix}")

    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Downloaded: {file_path}")


def save_metadata(directory_path: str, data: dict, filename="metadata.json"):
    """
    Save the given data dictionary as a JSON file (default filename is metadata.json)
    in the specified directory.
    """
    os.makedirs(directory_path, exist_ok=True)
    file_path = os.path.join(directory_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Saved metadata: {file_path}")


def make_request(query: str, variables: dict = None) -> dict:
    """
    Make a POST request to the Monday.com API with the given GraphQL query
    and variables. Raises an exception if the API returns errors.
    """
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(API_URL, json=payload, headers=headers)
    response_data = response.json()

    if "errors" in response_data:
        raise Exception(f"API Error: {response_data['errors']}")

    return response_data


# ================================
# API Functions
# ================================

def fetch_items(board_id: str, cursor: str = None) -> (list, str):
    """
    Fetch a page of items for the given board.
    Returns a tuple of (items_list, next_cursor).
    This query also extracts common fields like column_values.
    """
    query = """
    query ($boardId: ID!, $cursor: String) {
      boards(ids: [$boardId]) {
        items_page(limit: 500, cursor: $cursor) {
          cursor
          items {
            id
            name
            column_values {
                column {
                  id
                  title
                }
              text
              value
            }
            assets {
              name
              public_url
            }
            subitems {
              id
              name
              column_values {
              column {
                title
                id
              }
                text
                value
              }
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


def fetch_all_board_items(board_id: str) -> list:
    """
    Retrieve all items for a given board by paginating through results.
    """
    items, cursor = fetch_items(board_id)
    while cursor:
        more_items, cursor = fetch_items(board_id, cursor)
        items.extend(more_items)
    return items


def fetch_boards() -> list:
    """
    Fetch all boards from Monday.com.
    """
    query = """
    query {
      boards {
        id
        name
      }
    }
    """
    data = make_request(query)
    return data["data"]["boards"]


def record_board_done(board: dict):
    """
    Record that a board has been processed by adding its data
    to the DONE_BOARDS_FILE.
    """
    if not os.path.exists(DONE_BOARDS_FILE):
        with open(DONE_BOARDS_FILE, "w") as f:
            json.dump([], f, ensure_ascii=False, indent=4)

    with open(DONE_BOARDS_FILE, "r") as f:
        done_boards = json.load(f)

    # Append the board if not already present
    if board not in done_boards:
        done_boards.append(board)

    with open(DONE_BOARDS_FILE, "w") as f:
        json.dump(done_boards, f, indent=4, ensure_ascii=False)


# ================================
# Main Processing Function
# ================================

def main():
    # Ensure the done boards file exists
    if not os.path.exists(DONE_BOARDS_FILE):
        with open(DONE_BOARDS_FILE, "w") as f:
            json.dump([], f)

    with open(DONE_BOARDS_FILE, "r") as f:
        done_boards = json.load(f)
    done_board_ids = [b["id"] for b in done_boards if "id" in b]

    boards = fetch_boards()

    for board in boards:
        board_id = board["id"]
        board_name = board["name"]

        if board_id in done_board_ids:
            print(f"Skipping board {board_id} - {board_name}")
            continue

        print(f"Processing board {board_id} - {board_name}")
        if input("Process this board? (Y/n): ").lower() != "y":
            record_board_done(board)
            continue

        # Fetch all items for the board
        items = fetch_all_board_items(board_id)
        board_dir = os.path.join(DOWNLOAD_DIR, f"{board_id}_{sanitize_filename(board_name)}")
        os.makedirs(board_dir, exist_ok=True)

        for item in items:
            item_id = item["id"]
            item_name = item["name"]

            # Build item directory and save its metadata (including column values)
            item_dir = build_download_path(DOWNLOAD_DIR, board_id, board_name, item_id, item_name)
            os.makedirs(item_dir, exist_ok=True)
            save_metadata(item_dir, item)

            # Download item assets
            for asset in item.get("assets", []):
                file_url = asset.get("public_url")
                if file_url:
                    download_file(item_dir, asset["name"], file_url)
                else:
                    print(f"No public URL for asset: {asset.get('name')}")

            # Process subitems (with column values), nesting them under the parent item
            subitems = item.get("subitems", [])
            if subitems:
                for subitem in subitems:
                    subitem_id = subitem["id"]
                    subitem_name = subitem["name"]

                    subitem_dir = build_download_path(
                        DOWNLOAD_DIR, board_id, board_name, item_id, item_name, subitem_id, subitem_name
                    )
                    os.makedirs(subitem_dir, exist_ok=True)
                    save_metadata(subitem_dir, subitem)

                    for asset in subitem.get("assets", []):
                        s_file_url = asset.get("public_url")
                        if s_file_url:
                            download_file(subitem_dir, asset["name"], s_file_url)
                        else:
                            print(f"No public URL for subitem asset: {asset.get('name')}")

        record_board_done(board)


# ================================
# Entry Point
# ================================

if __name__ == "__main__":
    main()
