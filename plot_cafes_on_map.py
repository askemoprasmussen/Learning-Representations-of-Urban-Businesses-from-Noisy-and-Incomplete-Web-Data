import folium


def plot_map(cafes: dict):
    # Draw the bounding box
    print("Generating map...")
    m = folium.Map(location=[55.677, 12.575], zoom_start=12)

    # Add the bounding box rectangle
    folium.Rectangle(
        bounds=[[55.594, 12.450], [55.760, 12.700]],
        color="red",
        fill=False
    ).add_to(m)

    # Plot each café as a dot
    for cafe in cafes:
        if cafe["LAT"] and cafe["LON"]:
            folium.CircleMarker(
                location=[cafe["LAT"], cafe["LON"]],
                radius=3,
                color="blue",
                fill=True
            ).add_to(m)

    m.save("data/cafes_map.html")
