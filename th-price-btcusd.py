def get_btcusd_price_tool(params):
    import requests
    import json

    url = "https://api.coindesk.com/v1/bpi/currentprice.json"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        btc_price_usd = data['bpi']['USD']['rate_float']
        return {"price": f"${btc_price_usd:,.2f}"}
    except requests.RequestException as e:
        return {"error": f"An error occurred while fetching the BTC price: {str(e)}"}

# Tool metadata
tool_metadata = {
    "name": "get_btcusd_price",
    "description": "Fetches the current price of BTC in USD from CoinDesk API",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": []
    }
}
