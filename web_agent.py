import ollama
import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin


# 1. The actual function
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
    

def process_cafe(cafe: dict) -> dict:

    website = cafe["TAGS"]["website"]
    urls = get_menu_urls(website)
    pages = fetch_menu(urls)
    result = extract_attributes(pages)
    merged = merge_result(result)
    with open("data/cafe_attr.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(merged)} cafés")

    # takes a single cafe dict, runs the full pipeline
    # (fetch links → filter menu URLs → fetch pages → LLM → merge)
    # returns the merged result, or None if something fails
    # print()

SCHEMA_FIELDS = [
    "serves_food",
    "serves_brunch",
    "serves_lunch",
    "serves_dinner",
    "alcohol_served",
    "specialty_coffee_signals",
    "bakery_focus",
    "takeaway_focus",
    "price_level",
]

def merge_result(results: list) -> dict:
    merged = {f: None for f in SCHEMA_FIELDS}
    merged["evidence"] = {f: [] for f in SCHEMA_FIELDS}

    for result in results:
        if result is None:
            continue
        for field in SCHEMA_FIELDS:
            value = result.get(field)
            if field == "price_level":
                if value is not None and merged[field] is None:
                    merged[field] = value
            else:
                if value is True:
                    merged[field] = True
                elif value is False and merged[field] is None:
                    merged[field] = False
            evidence = result.get("evidence", {}).get(field)
            if evidence is not None:
                merged["evidence"][field].append(evidence)

    non_null = sum(1 for f in SCHEMA_FIELDS if merged[f] is not None)
    merged["confidence"] = non_null / len(SCHEMA_FIELDS)

    return merged

def get_menu_urls(website_url: str) -> list:
    # 2. The schema describing it to the model
    tools = [
        {
            "type": "function",
            "function": {
                "name": "fetch_website",
                "description": "Fetches the content of a website",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to fetch"
                        }
                    },
                    "required": ["url"]
                }
            }
        }
    ]

    # 3. Send message + tools to the model
    messages = [
        {
            "role": "system",
            "content" : "You must return ONLY URLs, one per line. No numbers, no bullet points, no extra text. Each line must start with https://"
        },
        {
            "role": "user", "content": f"Fetch {website_url}"

        }
        ]

    response = ollama.chat(
        model="qwen2.5:7b",
        messages=messages,
        tools=tools
    )
    # 4. Check if the model wants to call a tool
    if response.message.tool_calls:
        tool_call = response.message.tool_calls[0]
        
        # Get the arguments it wants to use
        url = tool_call.function.arguments["url"]
        
        # Actually run the function
        result = fetch_website(url)
        
        print("Function ran! Got this many characters:", len(result))

    # Add the assistant's tool request to history
    messages.append(response.message)

    # Add the tool result
    messages.append({
        "role": "tool",
        "content": "\n".join(result)
    })

    # Ask the model again now that it has the result
    final_response = ollama.chat(
        model="qwen2.5:7b",
        messages=messages,
        tools=tools
    )

    # print(final_response.message.content)
    response_text = final_response.message.content
    urls = [line.strip() for line in response_text.splitlines() if line.strip().startswith("http")]
    urls = [url for url in urls if "#" not in url and website_url in url]

    # Filter urls further within python (we sacrifice precision for speed when choosing a less complex model)
    menu_keywords = ["menu", "morgenmad", "frokost", "aften", "drikkevarer", "drink", "kaffe", "brunch", "mad"]

    urls = list(set([
        url for url in urls
        if any(keyword in url.lower() for keyword in menu_keywords)
    ]))
    return urls


def extract_attributes(pages: dict) -> list:
    results = []
    for url, content in pages.items():
        messages = [{
            "role": "system",
            "content" : """
    You are an information extraction system.
    Return only valid JSON. No markdown. No explanations.

    Rules:
    - Use true/false only if supported by the text.
    - If unclear, use null.
    - Evidence must be a short exact quote from the text (max 20 words).
    - For price_level: use "budget" (<80 DKK main dish), "mid" (80-150 DKK), "upscale" (>150 DKK), or null if no prices found.

    Schema:
    {
    "serves_food": true|false|null,
    "serves_brunch": true|false|null,
    "serves_lunch": true|false|null,
    "serves_dinner": true|false|null,
    "alcohol_served": true|false|null,
    "specialty_coffee_signals": true|false|null,
    "bakery_focus": true|false|null,
    "takeaway_focus": true|false|null,
    "price_level": "budget"|"mid"|"upscale"|null,
    "evidence": {
        "serves_food": "string"|null,
        "serves_brunch": "string"|null,
        "serves_lunch": "string"|null,
        "serves_dinner": "string"|null,
        "alcohol_served": "string"|null,
        "specialty_coffee_signals": "string"|null,
        "bakery_focus": "string"|null,
        "takeaway_focus": "string"|null,
        "price_level": "string"|null
    }
    }

    """
        },
        {
            "role": "user",
            "content": content
        }
        ]
        menu_response = ollama.chat(
            model="qwen2.5:14b",
            messages=messages
        )
        try:
            parsed = json.loads(menu_response.message.content)
            results.append(parsed)
        except json.JSONDecodeError:
            print(f"Failed to parse JSON for {url}")
            results.append(None)
        # print(menu_response.message.content)
    return results    





def main():
    cafes = load_cafes('/Users/aske/Documents/Thesis/Project/data/cafes_raw.json')
    for cafe in cafes:
        process_cafe(cafe)

if __name__=="__main__":
    main()