import urllib.request
import json

def test_api():
    # 1. Test Products API
    with urllib.request.urlopen("http://127.0.0.1:8000/api/products") as resp:
        products_data = json.loads(resp.read().decode())
        print(f"Products API Success: {products_data['count']} items found.")

    # 2. Test Recommendation for Maggi (p9)
    payload = json.dumps({"ordered_ids": ["p9"], "top_k": 4}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/recommend",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        rec_data = json.loads(resp.read().decode())
        print("\nTest: Recommendations for Maggi (p9):")
        for r in rec_data["data"]["recommendations"]:
            print(f" - {r['name']} ({r['match_percentage']}% match, cos: {r['similarity_score']}) -> {r['primary_reason']}")

    # 3. Test Order Simulation
    order_payload = json.dumps({"items": ["p2", "p1"]}).encode("utf-8") # Bread + Milk
    order_req = urllib.request.Request(
        "http://127.0.0.1:8000/api/order/simulate",
        data=order_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(order_req) as resp:
        order_data = json.loads(resp.read().decode())
        print(f"\nTest: Order Simulation Success: {order_data['order_id']}")
        print(f"Total Amount: Rs {order_data['total_amount']}, Delivery: {order_data['delivery_time']}")
        print("Post-order suggestions:")
        for r in order_data["post_order_recommendations"]:
            print(f" - {r['name']} ({r['match_percentage']}%)")

    # 4. Test Index HTML
    with urllib.request.urlopen("http://127.0.0.1:8000/") as resp:
        html = resp.read().decode()
        print(f"\nFrontend HTML Served Success: {len(html)} bytes, Title in page: {'Blinkit' in html}")

if __name__ == "__main__":
    test_api()
