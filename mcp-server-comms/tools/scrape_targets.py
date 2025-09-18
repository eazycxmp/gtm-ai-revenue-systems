# tools/scrape_targets.py
def scrape_targets(query: str, region: str):
    """
    STUB: returns sample rows so you can demo end-to-end.
    Swap this with your real Python scraper later.
    """
    data = [
        {
            "name": "Charlotte Rugby Club",
            "email": "info@charlotterugby.com",
            "url": "https://charlotterugby.com",
            "region": region,
            "query": query
        },
        {
            "name": "Raleigh Vipers",
            "email": "contact@raleighvipers.com",
            "url": "https://raleighvipers.com",
            "region": region,
            "query": query
        }
    ]
    return data

