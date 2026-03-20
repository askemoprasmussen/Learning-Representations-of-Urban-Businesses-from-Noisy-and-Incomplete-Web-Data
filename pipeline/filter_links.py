import ollama
import json


def filter_links_for_cafe(links: list) -> list:
    if not links:
        return []

    url_list = "\n".join(links)
    messages = [
        {
            "role": "system",
            "content": (
                "You are a link filter for a café dataset. "
                "Given a list of URLs from a café website, return ONLY the URLs likely to contain "
                "menu, food, drinks, brunch, lunch, dinner, coffee, or pricing information. "
                "Return one URL per line. No explanations, no bullet points."
            )
        },
        {
            "role": "user",
            "content": f"Filter these URLs:\n{url_list}"
        }
    ]

    response = ollama.chat(model="qwen2.5:14b", messages=messages)
    response_text = response.message.content
    filtered = [line.strip() for line in response_text.splitlines() if line.strip().startswith("http")]
    return filtered


def main():
    with open("data/homepages.json") as f:
        homepages = json.load(f)

    try:
        with open("data/relevant_links.json") as f:
            relevant_links = json.load(f)
        print(f"Resuming from {len(relevant_links)} already processed")
    except FileNotFoundError:
        relevant_links = {}

    for osm_id, links in homepages.items():
        if osm_id in relevant_links:
            continue

        if links is None:
            relevant_links[osm_id] = None
            continue

        try:
            filtered = filter_links_for_cafe(links)
            relevant_links[osm_id] = filtered
            print(f"{osm_id}: {len(links)} → {len(filtered)} links")
        except Exception as e:
            print(f"Failed on {osm_id}: {e}")
            relevant_links[osm_id] = None

        with open("data/relevant_links.json", "w", encoding="utf-8") as f:
            json.dump(relevant_links, f, ensure_ascii=False, indent=2)

    print(f"Done. Processed {len(relevant_links)} cafés.")


if __name__ == "__main__":
    main()
