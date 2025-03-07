import os
import rest_handler
from https_helper import create_response_body

prefix = os.getenv("Prefix")

import traceback


def lambda_handler(event, context):
    try:
        return rest_handler.handle_rest_req(event, context)
    except Exception as e:
        error_message = f"An error occurred ֿ\n traceback: {traceback.format_exc()}"
        print(traceback.format_exc())
        return create_response_body(500, {"message": error_message})
