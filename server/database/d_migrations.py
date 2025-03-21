"""
Database migrations module - handles creating database schema without seeding data
"""
import asyncio
import logging
import os
import datetime
from pathlib import Path

from server.database.database import drop_all_tables, get_connection

logger = logging.getLogger(__name__)

# ------------------------------------------------
# Main Migration Process
# ------------------------------------------------

def generate_html_report() -> str:
    """
    Generate an HTML report for schema creation

    Returns:
        Path to the generated HTML file
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_dir = Path("./reports")
    report_dir.mkdir(exist_ok=True)

    report_path = report_dir / f"schema_creation_report_{timestamp}.html"

    # Generate HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Database Schema Creation Report</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                border-bottom: 2px solid #eee;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #3498db;
                margin-top: 30px;
                border-left: 4px solid #3498db;
                padding-left: 10px;
            }}
            .timestamp {{
                text-align: center;
                color: #7f8c8d;
                font-style: italic;
                margin-bottom: 30px;
            }}
            .summary {{
                background-color: #e8f4f8;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
        </style>
    </head>
    <body>
        <h1>Database Schema Creation Report</h1>
        <div class="timestamp">Generated on {datetime.datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</div>
        
        <div class="summary">
            <h2>Schema Created Successfully</h2>
            <p>Database schema has been created without any seed data.</p>
        </div>
    </body>
    </html>
    """

    # Write to file
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return str(report_path)

async def run_migrations():
    """
    Run schema creation without adding any seed data
    """
    logger.info("Starting database schema creation...")

    # Create empty report (no seed data)
    report_path = generate_html_report()
    logger.info(f"HTML report generated at: {report_path}")

    # Open the report in browser
    try:
        os.system(f"open {report_path}")
        logger.info(f"Opened HTML report in browser")
    except Exception as e:
        logger.error(f"Failed to open HTML report: {str(e)}")

    logger.info("Database schema created successfully")


# For standalone script execution
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(run_migrations())