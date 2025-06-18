import json
import scrapy
import random
import time

class LeboncoinSpider(scrapy.Spider):
    name = "leboncoin_locations"
    allowed_domains = ["leboncoin.fr"]

    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_2) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0",
    ]

    # Ton cookie datadome ici
    cookies = {
        'datadome': 'ryLX3fxq99PlNCmOv~xKtcm5lJqMzuGaSZTgMI96DncM0z_aLM0bGQIWUOwuuhRwV5sTOv0AZZnb0eRCzu7unfG3~YPL_xuU8cFKcJJPS~Dp2vF4ud81VpCPDjuL0B32',
    }

    # Paramètres de la recherche Lyon, maison + appart, 500-5000€
    locations = "Lyon__45.76053450713997_4.835562580016857_7308_10000"
    real_estate_type = "2,1"
    price = "500-5000"

    def random_headers(self):
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.leboncoin.fr/",
        }

    def start_requests(self):
        url = (
            f"https://www.leboncoin.fr/recherche?"
            f"category=10"
            f"&locations={self.locations}"
            f"&real_estate_type={self.real_estate_type}"
            f"&price={self.price}"
            f"&page=1"
        )
        yield scrapy.Request(
            url=url,
            headers=self.random_headers(),
            cookies=self.cookies,
            callback=self.parse,
            cb_kwargs={"page": 1},
        )

    def parse(self, response, page):
        if response.status == 403:
            self.logger.error(f"❌ BLOQUÉ 403 sur page {page} ! Change de cookie/user-agent/proxy.")
            return

        script_data = response.xpath("//script[@id='__NEXT_DATA__']/text()").get()
        if not script_data:
            self.logger.warning(f"⚠️ Script __NEXT_DATA__ manquant page {page}")
            return

        data = json.loads(script_data)
        ads = data.get("props", {}).get("pageProps", {}).get("searchData", {}).get("ads", [])
        if not ads:
            self.logger.info(f"Fin de pagination page {page}")
            return

        for ad in ads:
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
            f"https://www.leboncoin.fr/recherche?"
            f"category=10"
            f"&locations={self.locations}"
            f"&real_estate_type={self.real_estate_type}"
            f"&price={self.price}"
            f"&page={next_page}"
        )
        time.sleep(random.uniform(2.5, 5.0))
        yield scrapy.Request(
            url=next_url,
            headers=self.random_headers(),
            cookies=self.cookies,
            callback=self.parse,
            cb_kwargs={"page": next_page},
        )
