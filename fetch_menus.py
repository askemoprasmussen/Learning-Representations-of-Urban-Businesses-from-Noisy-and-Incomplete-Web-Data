import requests
from bs4 import BeautifulSoup
import json  

def fetch_menu(urls: list) -> dict:
    pages = {}
    for url in urls:
        try:
            response = requests.get(url, verify=False)
            if response.status_code != 200:
                continue
            soup = BeautifulSoup(response.text, "html.parser")
            pages[url] = soup.get_text(separator="\n", strip = True)
        except Exception as e:
            print(f"Failed on {url}: {e}")
            continue
    return pages



def main():
    with open("data/relevant_links.json") as f:
        relevant_links = json.load(f)

    try:
        with open("data/pages.json") as f:
            pages = json.load(f)
        print(f"Resuming from {len(pages)} already processed")
    except FileNotFoundError:
        pages = {}

    for osm_id, urls in relevant_links.items():
        if not urls or osm_id in pages:
            continue
        pages[osm_id] = fetch_menu(urls)
        print(f"{osm_id}: fetched {len(pages[osm_id])} pages")

        with open("data/pages.json", "w", encoding="utf-8") as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"Done. Processed {len(pages)} cafés.")



if __name__=="__main__":
    main()