import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import matplotlib.pyplot as plt


# Load data
@st.cache_data
def load_data(uploaded_file):
    return pd.read_excel(uploaded_file)


# Create network graph with detailed popups
def create_network(df):
    G = nx.DiGraph()

    for _, row in df.iterrows():
        consultant = row['Número de Socio']
        sponsor = row['Número de Patrocinador']
        bp = row['VEP']
        inactive = row['Catálogos Inactivo']
        recruits = row.get('Reclutas', 0)
        discount = row.get('Descuento', 0)
        last_order = row.get('Última Compra', 'N/A')

        # Set color based on performance
        color = 'green' if bp > 1000 else 'red' if inactive > 3 else 'blue'

        title_info = f"""
        <b>{row['Nombre del Socio']}</b><br>
        BP: {bp}<br>
        Reclutas: {recruits}<br>
        Descuento: {discount}%<br>
        Última Compra: {last_order}
        """

        G.add_node(consultant, label=row['Nombre del Socio'], color=color, title=title_info)
        if pd.notna(sponsor):
            G.add_edge(sponsor, consultant)

    return G


# Streamlit App
st.title("MLM Network Performance Dashboard")

uploaded_file = st.file_uploader("Upload your MLM data (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = load_data(uploaded_file)
    G = create_network(df)

    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)
        st.components.v1.html(open(tmpfile.name, "r", encoding="utf-8").read(), height=600)

    # Performance Analytics
    st.subheader("Performance Analysis")

    if 'VEP' in df.columns:
        #st.write("### BP Distribution")
        #fig, ax = plt.subplots()
        #df['VEP'].hist(bins=20, color='skyblue', edgecolor='black', ax=ax)
        #ax.set_xlabel("Bonus Points (BP)")
        #ax.set_ylabel("Number of Consultants")
        #st.pyplot(fig)

        st.write("### Top 10 Consultants by BP")
        top_performers = df[['Nombre del Socio', 'VEP']].sort_values(by='VEP', ascending=False).head(10)
        st.table(top_performers)
