import os
import json
import requests

STATE_FILE = "state.json"
API_URL = "https://ng.nlstar.com/api/v1/catalog/products"  # примерный эндпоинт, уточните по факту

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def fetch_products(x_auth_token):
    headers = {
        "x-auth-token": x_auth_token,
        "Accept": "application/json",
    }
    # Параметры запроса могут отличаться, проверьте через DevTools
    resp = requests.get(API_URL, headers=headers)
    resp.raise_for_status()
    return resp.json()["data"]["products"]  # структура может отличаться!

def detect_price_changes(products, prev_state):
    changes = []
    new_state = {}
    for product in products:
        pid = str(product["id"])
        name = product["name"]
        price = product["price"]
        old_price = prev_state.get(pid, {}).get("price")
        new_state[pid] = {"name": name, "price": price}
        if old_price is not None and price != old_price:
            changes.append((name, old_price, price))
    return changes, new_state

def get_price_changes(x_auth_token):
    prev_state = load_state()
    products = fetch_products(x_auth_token)
    changes, new_state = detect_price_changes(products, prev_state)
    save_state(new_state)
    return changes

