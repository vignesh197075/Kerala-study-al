import scrapy
import json
from urllib.parse import urldefrag
from pathlib import Path

class HSSLiveSpider(scrapy.Spider):

    name = "hsslive"

    allowed_domains = [
        "hsslive.in",
        "www.hsslive.in"
    ]

    start_urls = [
        "https://www.hsslive.in/"
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS": 1,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 3,
        "AUTOTHROTTLE_MAX_DELAY": 15,
        "FEED_EXPORT_ENCODING": "utf-8",
        "LOG_LEVEL": "INFO",
    }

    visited = set()

    def parse(self, response):

        url = urldefrag(response.url).url

        if url in self.visited:
            return

        self.visited.add(url)

        content_type = response.headers.get(
            "Content-Type", b""
        ).decode("utf-8", errors="ignore")

        if "html" not in content_type.lower():
            return

        title = " ".join(
            response.css("title::text").getall()
        ).strip()

        description = response.css(
            'meta[name="description"]::attr(content)'
        ).get(default="")

        headings = []

        for tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            headings.extend([
                " ".join(h.css("::text").getall()).strip()
                for h in response.css(tag)
            ])

        yield {
            "url": url,
            "title": title,
            "description": description,
            "headings": headings
        }

        for href in response.css("a::attr(href)").getall():

            link = urldefrag(
                response.urljoin(href)
            ).url

            if (
                link.startswith("https://")
                and any(
                    domain in link.split("/")[2]
                    for domain in self.allowed_domains
                )
                and link not in self.visited
            ):
                yield response.follow(
                    link,
                    callback=self.parse
                )


if __name__ == "__main__":

    Path("data").mkdir(exist_ok=True)

    from scrapy.crawler import CrawlerProcess

    process = CrawlerProcess({
        "FEEDS": {
            "data/hsslive_index.jsonl": {
                "format": "jsonlines",
                "overwrite": True
            }
        }
    })

    process.crawl(HSSLiveSpider)
    process.start()