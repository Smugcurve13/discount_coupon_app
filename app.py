from flask import Flask, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

SHOP = os.getenv("SHOPIFY_SHOP_NAME")
TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

headers = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json"
}

@app.route("/", methods=["GET"])
def index():   
    return jsonify({"message": "Welcome to the Shopify API integration!"})

@app.route("/collections", methods=["GET"])
def get_collections():
    # You can also try /smart_collections.json
    url = f"https://{SHOP}/admin/api/2023-10/custom_collections.json"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        collections = response.json().get("custom_collections", [])
        result = [
            {
                "id": col["id"],
                "title": col["title"]
            } for col in collections
        ]
        return jsonify(result)
    else:
        return jsonify({"error": "Failed to fetch collections", "details": response.json()}), 400



@app.route("/create_discount", methods=["POST"])
def create_discount():
    # Replace with your collection ID (can be fetched via API)
    target_collection_id = os.getenv("COLLECTION_ID")  # TODO: Replace with actual
    discount_title = "HOLIDAYEDIT2025"

    data = {
        "price_rule": {
            "title": discount_title,
            "target_type": "line_item",
            "target_selection": "entitled",
            "allocation_method": "across",
            "value_type": "fixed_amount",         # ✅ Use fixed amount
            "value": "-1000.0",                   # ✅ Discount of ₹1000
            "customer_selection": "all",
            "starts_at": "2025-06-01T00:00:00Z",
            "entitled_collection_ids": [target_collection_id],
            "prerequisite_quantity_range": {
                "greater_than_or_equal_to": 2
            }
        }
    }

    # 1. Create price rule
    rule_response = requests.post(
        f"https://{SHOP}/admin/api/2023-10/price_rules.json",
        headers=headers,
        json=data
    )
    if rule_response.status_code != 201:
        return jsonify({"error": "Price rule creation failed", "details": rule_response.json()}), 400

    rule_id = rule_response.json()['price_rule']['id']

    # 2. Attach discount code
    code_data = {
        "discount_code": {
            "code": discount_title
        }
    }
    code_response = requests.post(
        f"https://{SHOP}/admin/api/2023-10/price_rules/{rule_id}/discount_codes.json",
        headers=headers,
        json=code_data
    )

    if code_response.status_code == 201:
        return jsonify({"success": True, "discount_code": discount_title})
    else:
        return jsonify({"error": "Discount code creation failed", "details": code_response.json()}), 400


if __name__ == "__main__":
    app.run(debug=True, port=5001)
