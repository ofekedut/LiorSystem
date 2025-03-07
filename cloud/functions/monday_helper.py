import requests
import json
from typing import List, Dict, Any

from api_keys import API_KEY
from tasks.parse_items import Item


def query_monday_items(
    item_ids: List[int], api_key: str, api_url: str = "https://api.monday.com/v2"
) -> Dict[str, Any]:
    """
    Query Monday.com items using GraphQL to fetch column values, subitems, and assets.

    Args:
        item_ids (List[int]): List of Monday.com item IDs to query
        api_key (str): Monday.com API key
        api_url (str): Monday.com API endpoint URL (default: "https://api.monday.com/v2")

    Returns:
        Dict[str, Any]: Parsed response from Monday.com API

    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If the response contains errors
    """

    # Construct the GraphQL query
    query = """
    {
        items(ids: %s) {
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
            subitems {
                id
                name
                assets {
                    id
                    public_url
                    name
                }
            }
        }
    }
    """ % json.dumps(
        item_ids
    )  # Properly format the item_ids list for GraphQL

    # Set up the headers for authentication
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    # Make the API request
    try:
        response = requests.post(api_url, json={"query": query}, headers=headers)
        response.raise_for_status()  # Raise exception for bad status codes

        # Parse the response
        data = response.json()

        # Check for errors in the response
        if "errors" in data:
            error_messages = [
                error.get("message", "Unknown error") for error in data["errors"]
            ]
            raise ValueError(f"GraphQL query failed: {'; '.join(error_messages)}")

        return data["data"]

    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(
            f"Failed to query Monday.com API: {str(e)}"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse API response: {str(e)}")


# Example usage function
def process_monday_items(api_key: str, item_ids: List[int]) -> list[Item]:
    """
    Example function showing how to use the query_monday_items function and process the results.

    Args:
        api_key (str): Monday.com API key
        item_ids (List[int]): List of item IDs to query
    """
    try:
        # Query the items
        result = query_monday_items(item_ids, api_key)
        items = result.get("items")
        data = []
        for item in items:
            item_parsed = Item.from_monday_data(item)
            data.append(item_parsed)
        return data
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error: {str(e)}")

def list_boards(api_key: str, api_url: str = "https://api.monday.com/v2") -> Dict[str, Any]:
    """
    List all boards accessible via the Monday.com API.

    Args:
        api_key (str): Monday.com API key
        api_url (str): Monday.com API endpoint URL (default: "https://api.monday.com/v2")

    Returns:
        Dict[str, Any]: Parsed response containing boards data from Monday.com API

    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If the response contains errors
    """
    # GraphQL query to fetch boards
    query = """
    {
        boards {
            id
            name
            description
            state
            board_kind
            board_folder_id
            columns {
                id
                title
                type
            }
        }
    }
    """

    # Set up the headers for authentication
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    # Make the API request
    try:
        response = requests.post(api_url, json={"query": query}, headers=headers)
        response.raise_for_status()

        # Parse the response
        data = response.json()

        # Check for errors in the response
        if "errors" in data:
            error_messages = [
                error.get("message", "Unknown error") for error in data["errors"]
            ]
            raise ValueError(f"GraphQL query failed: {'; '.join(error_messages)}")

        return data["data"]

    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(
            f"Failed to query Monday.com API: {str(e)}"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse API response: {str(e)}")


def list_items(
    board_id: int,
    api_key: str,
    limit: int = 25,
    cursor: str = None,
    api_url: str = "https://api.monday.com/v2"
) -> Dict[str, Any]:
    """
    List items from a specific board in Monday.com with pagination support and subitems.

    Args:
        board_id (int): ID of the Monday.com board to query
        api_key (str): Monday.com API key
        limit (int): Number of items per page (default: 25)
        cursor (str): Cursor for pagination (default: None)
        api_url (str): Monday.com API endpoint URL (default: "https://api.monday.com/v2")

    Returns:
        Dict[str, Any]: Parsed response containing items data from Monday.com API
    """
    query = """
    query ($boardId: ID!, $limit: Int!, $cursor: String) {
        boards(ids: [$boardId]) {
            items_page(limit: $limit, cursor: $cursor) {
                cursor
                items {
                    id
                    name
                    state
                    created_at
                    updated_at
                    column_values {
                        column {
                            id
                            title
                            type
                        }
                        text
                        value
                    }
                    subitems {
                        id
                        name
                        assets {
                            id
                            public_url
                            name
                        }
                    }
                }
            }
        }
    }
    """

    variables = {
        "boardId": str(board_id),
        "limit": limit,
        "cursor": cursor
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            api_url,
            json={"query": query, "variables": variables},
            headers=headers
        )
        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            error_messages = [
                error.get("message", "Unknown error") for error in data["errors"]
            ]
            raise ValueError(f"GraphQL query failed: {'; '.join(error_messages)}")

        return data["data"]

    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(
            f"Failed to query Monday.com API: {str(e)}"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse API response: {str(e)}")

def list_all_items(board_id: int, api_key: str, batch_size: int = 25) -> List[Dict[str, Any]]:
    """
    List all items from a board by handling pagination automatically.

    Args:
        board_id (int): ID of the Monday.com board to query
        api_key (str): Monday.com API key
        batch_size (int): Number of items to fetch per request (default: 25)

    Returns:
        List[Dict[str, Any]]: List of all items from the board
    """
    all_items = []
    cursor = None

    while True:
        result = list_items(board_id, api_key, limit=batch_size, cursor=cursor)

        if not result["boards"] or not result["boards"][0]["items_page"]:
            break

        items_page = result["boards"][0]["items_page"]
        items = items_page["items"]
        cursor = items_page["cursor"]

        all_items.extend(items)

        if not cursor:
            break

    return all_items




def get_asset_urls(
        asset_ids: List[str],
        api_key: str,
        api_url: str = "https://api.monday.com/v2"
) -> Dict[str, Any]:
    """
    Get file URLs for specific asset IDs from Monday.com.

    Args:
        asset_ids (List[str]): List of Monday.com asset IDs to query
        api_key (str): Monday.com API key
        api_url (str): Monday.com API endpoint URL (default: "https://api.monday.com/v2")

    Returns:
        Dict[str, Any]: Parsed response containing assets data from Monday.com API

    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If the response contains errors
    """
    query = """
    query ($ids: [ID!]) {
        assets(ids: $ids) {
            id
            name
            url
            public_url
            file_extension
            file_size
        }
    }
    """

    variables = {
        "ids": asset_ids
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            api_url,
            json={"query": query, "variables": variables},
            headers=headers
        )
        response.raise_for_status()

        data = response.json()

        if "errors" in data:
            error_messages = [
                error.get("message", "Unknown error") for error in data["errors"]
            ]
            raise ValueError(f"GraphQL query failed: {'; '.join(error_messages)}")

        return data["data"]

    except requests.exceptions.RequestException as e:
        raise requests.exceptions.RequestException(
            f"Failed to query Monday.com assets: {str(e)}"
        )
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse API response: {str(e)}")

# asset_ids = ["12345", "67890"]  # Replac/e with actual asset IDs
# result = get_asset_urls(asset_ids, API_KEY)
# for asset in result.get("assets", []):
#     print(f"Asset ID: {asset['id']}")
#     print(f"Name: {asset['name']}")
#     print(f"URL: {asset['url']}")
#     print(f"Public URL: {asset['public_url']}")
#     print(f"Extension: {asset['file_extension']}")
#     print(f"Size: {asset['file_size']}")
#     print("---")
