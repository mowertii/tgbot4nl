import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import os

URL = "https://ng.nlstar.com/ru/api/store/city/2214/all-products/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
}

def fetch_products():
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    # Проверьте структуру ответа! Если не data["products"], то print(data) и исправьте
    return data["products"]

def fetch_and_save_prices(filename="novelty_prices.csv"):
    response = requests.get(URL, headers=HEADERS)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    products = []
    for card in soup.select("div.catalog__item"):  # проверьте селектор!
        name = card.select_one(".catalog__item-title")
        price = card.select_one(".catalog__item-price")
        old_price = card.select_one(".catalog__item-oldprice")
        products.append({
            "name": name.text.strip() if name else "Нет названия",
            "price": price.text.strip() if price else "Нет цены",
            "old_price": old_price.text.strip() if old_price else "",
        })
    is_new = not os.path.exists(filename)
    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if is_new:
            writer.writerow(["datetime", "name", "price", "old_price"])
        for prod in products:
            writer.writerow([datetime.now().isoformat(), prod["name"], prod["price"], prod["old_price"]])
    return products

