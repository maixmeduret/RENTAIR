import json
import scrapy
import random
import time

class LeboncoinSpider(scrapy.Spider):
    name = "leboncoin_locations"
    allowed_domains = ["leboncoin.fr"]

    # User agents rotation (améliore l’anti-bot)
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
        # Ajoute-en d'autres si tu veux
    ]

    def start_requests(self):
        url = (
            "https://www.leboncoin.fr/recherche?"
            "category=10"  # Locations immobilières
            "&real_estate_type=1,2"  # 1=appartement, 2=maison
            "&price=500-5000"
            "&page=1"
        )
        yield scrapy.Request(
            url=url,
            headers=self.random_headers(),
            callback=self.parse,
            cb_kwargs={"page": 1},
        )

    def random_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept-Language": "fr-FR,fr;q=0.9",
        }

    def parse(self, response, page):
        # Récupérer le JSON principal dans le script __NEXT_DATA__
        script_data = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
        if not script_data:
            self.logger.warning(f"Script __NEXT_DATA__ manquant page {page}")
            return

        data = json.loads(script_data)
        ads = data.get("props", {}).get("pageProps", {}).get("searchData", {}).get("ads", [])
        if not ads:
            self.logger.info(f"Fin de pagination page {page}")
            return

        for ad in ads:
            # Extraction commune, code postal, loyer, surface, type de bien
            location = ad.get("location", {})
            attributes = {attr["key"]: attr.get("value") for attr in ad.get("attributes", [])}

            yield {
                "commune": location.get("city"),
                "code_postal": location.get("zipcode"),
                "loyer": ad.get("price", [None])[0] if isinstance(ad.get("price"), list) else ad.get("price"),
                "surface": attributes.get("square"),
                "type_bien": "maison" if ad.get("real_estate_type") == 2 else "appartement",
                "url": f"https://www.leboncoin.fr/vi/{ad.get('list_id')}.htm"
            }

        # Pagination suivante
        next_page = page + 1
        next_url = (
            "https://www.leboncoin.fr/recherche?"
            "category=10"
            "&real_estate_type=1,2"
            "&price=500-5000"
            f"&page={next_page}"
        )
        # Délai random pour anti-bot (important !)
        time.sleep(random.uniform(2, 4))
        yield scrapy.Request(
            url=next_url,
            headers=self.random_headers(),
            callback=self.parse,
            cb_kwargs={"page": next_page},
        )
