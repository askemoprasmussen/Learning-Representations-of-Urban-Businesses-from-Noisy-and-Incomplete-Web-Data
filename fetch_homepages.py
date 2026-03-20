import requests
from bs4 import BeautifulSoup
import json  
from urllib.parse import urljoin


def fetch_website(url: str) -> str:
    if isinstance(url,dict):
        url = url.get("value")
        if not url:
            return []
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")
    
    links = []
    for a_tag in soup.find_all("a", href=True):
        links.append(urljoin(url, a_tag['href']))
    return links

def load_cafes(path :str) -> list:
    # load cafes_raw.json, return only those with a website tag

    cafes = []
    with open(path) as f:
        data = json.load(f)
    for cafe in data:
        if cafe['TAGS'].get('website') is not None:
            cafes.append(cafe)
    print(len(cafes))
    return cafes


def main():
    homepages = {}
    cafes = load_cafes('/Users/aske/Documents/Thesis/Project/data/cafes_raw.json')

    try:
        with open("data/homepages.json") as f:
            homepages = json.load(f)
        print(f"Resuming")
    except FileNotFoundError:
        homepages = {}

    for cafe in cafes:
        if str(cafe["OSM_ID"]) in homepages:
            continue
        website = cafe["TAGS"]["website"]
        try:
            links = fetch_website(website)
        except Exception as e:
            print(f"Failed on {website}: {e}")
            homepages[str(cafe['OSM_ID'])] = None
            continue

        homepages[str(cafe['OSM_ID'])] = links
        with open("data/homepages.json", "w", encoding="utf-8") as f:
            json.dump(homepages, f, ensure_ascii=False, indent=2)
    
    print(f"Saved {len(homepages)} homepages")
    

if __name__=="__main__":
    main()