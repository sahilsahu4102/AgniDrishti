from html import escape

import folium
import streamlit as st
from streamlit_folium import st_folium

import store

st.set_page_config(page_title='AgniDrishti', layout='wide')
st.title('AgniDrishti: forest fire alert triage')
df = store.load()
if df.empty:
    st.warning('No scored alerts yet. Run: python score.py')
    st.stop()

a, b, c = st.columns(3)
a.metric('Alerts in', len(df))
b.metric('DISPATCH', int((df.tier == 'DISPATCH').sum()))
c.metric('VERIFY', int((df.tier == 'VERIFY').sum()))

tiers = st.multiselect('Tiers on the map', ['DISPATCH', 'VERIFY', 'LOG'], default=['DISPATCH', 'VERIFY'])
view = df[df.tier.isin(tiers)]
colour = {'DISPATCH': 'red', 'VERIFY': 'orange', 'LOG': 'gray'}
m = folium.Map(location=[30.1, 79.2], zoom_start=8, tiles='CartoDB positron', prefer_canvas=True)  # canvas copes with ~10k markers
if len(view):  # one GeoJSON layer: per-marker folium objects took ~1 min for 10k alerts
    pts = {'type': 'FeatureCollection', 'features': [
        {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [x.longitude, x.latitude]},
         'properties': {'tier': x.tier, 'p': round(x.p, 2), 'risk': int(x.r), 'why': escape(str(x.why))}}
        for x in view.itertuples()]}
    folium.GeoJson(pts, marker=folium.CircleMarker(radius=4, fill=True, fill_opacity=0.8),
                   style_function=lambda f: {'color': colour[f['properties']['tier']], 'fillColor': colour[f['properties']['tier']]},
                   popup=folium.GeoJsonPopup(fields=['tier', 'p', 'risk', 'why'])).add_to(m)
st_folium(m, height=520, use_container_width=True, returned_objects=[])

rank = view.tier.map({'DISPATCH': 0, 'VERIFY': 1, 'LOG': 2})
st.dataframe(view.assign(rank=rank).sort_values(['rank', 'p'], ascending=[True, False])[['id', 'tier', 'p', 'r', 'why']],
             hide_index=True)
