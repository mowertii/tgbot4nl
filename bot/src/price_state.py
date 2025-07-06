import json
import os

STATE_FILE = "price_state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def compare_prices(new_products, old_state):
    changes = []
    new_state = {}
    for prod in new_products:
        name = prod.get("name") or prod.get("short_name") or "Без названия"
        price = prod.get("price")
        old_price = old_state.get(name, {}).get("price")
        new_state[name] = {"price": price}
        if old_price is not None and price != old_price:
            changes.append({"name": name, "old_price": old_price, "new_price": price})
    return changes, new_state

