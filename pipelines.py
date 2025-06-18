import csv
from collections import defaultdict

class BienTypeCsvPipeline:
    def open_spider(self, spider):
        self.houses = []
        self.apartments = []

    def process_item(self, item, spider):
        price = item.get("price")
        surface = item.get("surface")
        if not price or not surface:
            return item

        try:
            loyer_m2 = float(price) / float(surface)
        except (ValueError, ZeroDivisionError):
            return item

        title = item.get("title", "").lower()
        type_bien = "maison" if "maison" in title else "appartement"

        row = {
            "commune": item.get("city"),
            "code_postal": item.get("postal_code"),
            "type": type_bien,
            "loyer_m2": round(loyer_m2, 2)
        }

        if type_bien == "maison":
            self.houses.append(row)
        else:
            self.apartments.append(row)

        return item

    def close_spider(self, spider):
        with open("loyers_appartements.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["commune", "code_postal", "type", "loyer_m2"])
            writer.writeheader()
            writer.writerows(self.apartments)

        with open("loyers_maisons.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["commune", "code_postal", "type", "loyer_m2"])
            writer.writeheader()
            writer.writerows(self.houses)
