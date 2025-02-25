import streamlit as st
import pandas as pd
import networkx as nx
from pyvis.network import Network
import tempfile
import matplotlib.pyplot as plt
import re


# Load data
@st.cache_data
def load_data(uploaded_file):
    return pd.read_excel(uploaded_file)


# Extract numeric value from Bonos column
def extract_bonus(value, member_type):
    if value:
        if member_type == 'Socio':
            number = value.replace('Incentivo Monetario: ', '')
            #number.replace(',', '')# Remove commas if necessary
            #number = float(number)  # Convert to float
        else:
            number = value.replace('Cashback: ', '')
            #number.replace(',', '')# Remove commas if necessary
            #number = float(number)  # Convert to float
    else:
        number = 0.00
    return number


# Create network graph with detailed popups
def create_network(df):
    G = nx.DiGraph()

    for _, row in df.iterrows():
        consultant = row['Número de Socio']
        sponsor = row['Número de Patrocinador']
        bp = row['VEP']
        inactive = row['Catálogos Inactivo']
        #recruits = row.get('Reclutado', 0)
        #discount = row.get('Descuento', 0)
        member_type = row['Tipo de Socio']
        #bonus = extract_bonus(str(row['Bonos']), member_type)

        # Set color based on performance and type
        if member_type == 'Member':
            color = 'purple' if bp > 100 else 'orange' if inactive > 3 else 'gray'
        else:
            color = 'green' if bp > 100 else 'red' if inactive > 3 else 'blue'

        title_info = f"""
        {row['Nombre del Socio']}
        {member_type} {row['%']}%
        Puntos personales: {bp}
        Puntos en red: {row['VEP Red Personal:']}
        {row.get('Bonos') if pd.notna(row.get('Bonos')) else 'Sin bono o cashback :('}
        Deuda: {row['Deuda:']}
        """

        G.add_node(consultant, label=row['Nombre del Socio'], color=color, title=title_info)
        if pd.notna(sponsor):
            G.add_edge(sponsor, consultant)

    return G


# Streamlit App
st.title("Reportes de desempeño de tu red Oriflame")

st.markdown("**Carga aquí tu reporte de campaña  (.xlsx)**")
st.markdown("(Primero ve a mx.oriflame.com, Mi Negocio > Reportes > 'New activity Excel report', escoge tu campaña, haz click en **Ver Reporte** y después en **Descargar**)")

uploaded_file = st.file_uploader("", type=["xlsx"])

if uploaded_file:
    df = load_data(uploaded_file)
    #df['Bonos'] = df['Bonos'].apply(extract_bonus)
    G = create_network(df)

    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)
        st.components.v1.html(open(tmpfile.name, "r", encoding="utf-8").read(), height=600)

    # Performance Analytics
    st.subheader("Estadísticas de mi red")

    if 'VEP Red Personal:' in df.columns:
        st.write("### Mi Top 10 de Socios")
        top_performers = df[['Nombre del Socio', 'VEP Red Personal:']].sort_values(by='VEP Red Personal:',
                                                                                   ascending=False).head(10)
        # Reset dataframe indexes to hide them from table
        top_performers = top_performers.reset_index(drop=True)
        # Show table
        st.table(top_performers)

        st.write("### Distribución de Puntos")
        fig, ax = plt.subplots()
        df['VEP Red Personal:'].hist(bins=20, color='skyblue', edgecolor='black', ax=ax)
        ax.set_xlabel("Puntos (BP)")
        ax.set_ylabel("Cantidad de socios")
        st.pyplot(fig)