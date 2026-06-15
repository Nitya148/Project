"""Folium map helper for RePlate."""
import folium
from streamlit_folium import st_folium


def render_map(listings, origin=None, height=480, zoom=12, key="map"):
    """Render a Folium map with listing pins. Returns clicked listing id or None."""
    center = None
    if origin and origin.get("lat") is not None:
        center = [origin["lat"], origin["lng"]]
    elif listings:
        for l in listings:
            if l.get("lat") is not None:
                center = [l["lat"], l["lng"]]
                break
    if center is None:
        center = [17.4239, 78.4738]  # Hyderabad default

    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
        attr='&copy; OpenStreetMap &copy; CARTO',
    )

    # Origin (recipient) marker
    if origin and origin.get("lat") is not None:
        folium.Marker(
            location=[origin["lat"], origin["lng"]],
            tooltip=origin.get("label", "You are here"),
            icon=folium.Icon(color="darkpurple", icon="user", prefix="fa"),
        ).add_to(m)

    bounds = []
    if origin and origin.get("lat") is not None:
        bounds.append([origin["lat"], origin["lng"]])

    for idx, l in enumerate(listings, start=1):
        if l.get("lat") is None:
            continue
        bounds.append([l["lat"], l["lng"]])
        popup_html = f"""
        <div style="font-family:'Outfit',sans-serif;min-width:200px;">
            <div style="font-size:11px;letter-spacing:0.14em;text-transform:uppercase;color:#695A62;">{l.get('donor_name','')}</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:18px;color:#2A1B24;margin-top:4px;">{l['name']}</div>
            <div style="font-size:12px;color:#695A62;margin-top:6px;">{l.get('remaining_quantity', l.get('quantity'))} {l['unit']} · {l['category'].replace('_',' ')}</div>
            {f'<div style="font-size:11px;color:#C85A40;margin-top:6px;font-weight:600;">{l["distance_km"]} km away</div>' if l.get('distance_km') is not None else ''}
        </div>
        """
        folium.Marker(
            location=[l["lat"], l["lng"]],
            tooltip=f"#{idx} · {l['name']}",
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color="red", icon="cutlery", prefix="fa"),
        ).add_to(m)

    if len(bounds) > 1:
        m.fit_bounds(bounds, padding=(30, 30))

    out = st_folium(m, height=height, width=None, returned_objects=["last_object_clicked_tooltip"], key=key)
    return out
