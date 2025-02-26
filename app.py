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
    df = pd.read_excel(uploaded_file)

    # Validate and format numeric values
    df['Deuda:'] = pd.to_numeric(df['Deuda:'], errors='coerce').fillna(0).round(2)
    df['Catálogos Inactivo'] = pd.to_numeric(df['Catálogos Inactivo'], errors='coerce').fillna(0).astype(int)

    # Clean phone numbers
    df['Teléfono'] = df['Teléfono'].astype(str).str.replace('^52', '', regex=True).fillna('No disponible')

    return df


# Create network graph with detailed popups
def create_network(df):
    G = nx.DiGraph()

    for _, row in df.iterrows():
        consultant = row.get('Número de Socio', 'Desconocido')
        sponsor = row.get('Número de Patrocinador', None)
        bp = row.get('VEP', 0)
        inactive = row.get('Catálogos Inactivo', 0)
        member_type = row.get('Tipo de Socio', 'Desconocido')

        # Set color based on performance and type
        if member_type == 'Member':
            color = 'purple' if bp > 100 else 'yellow' if inactive > 3 else 'gray'
        else:
            color = 'green' if bp > 100 else 'red' if inactive > 3 else 'blue'

        title_info = f"""
        {row.get('Nombre del Socio', 'Sin nombre')}
        {member_type} {row.get('%', 0)}%
        Puntos personales: {bp}
        Puntos en red: {row.get('VEP Red Personal:', 0)}
        {row.get('Bonos') if pd.notna(row.get('Bonos')) else 'Sin bono o cashback :('}
        Deuda: {row.get('Deuda:', 0):.2f}
        """

        G.add_node(consultant, label=row.get('Nombre del Socio', 'Sin nombre'), color=color, title=title_info)
        if sponsor:
            G.add_edge(sponsor, consultant)

    return G


# Streamlit App
st.title("Reportes de desempeño de tu red Oriflame")

st.markdown("**Carga aquí tu reporte de campaña  (.xlsx)**")
st.markdown(
    "(Primero ve a mx.oriflame.com, Mi Negocio > Reportes > 'New activity Excel report', escoge tu campaña, haz click en **Ver Reporte** y después en **Descargar**)")

uploaded_file = st.file_uploader("", type=["xlsx"])

if uploaded_file:
    st.markdown("""
    <p style="font-size: 14px;">
    🟢 Socio con más de 100 puntos
    🔵 Socio con menos de 100 puntos
    🔴 Socio inactivo
    </p>
    <p style="font-size: 14px;">
    🟣 Member con más de 100 puntos
    🟡 Member con menos de 100 puntos
    ⚪ Member inactivo
    </p>
    """, unsafe_allow_html=True)

    df = load_data(uploaded_file)
    G = create_network(df)

    net = Network(height="600px", width="100%", directed=True)
    net.from_nx(G)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmpfile:
        net.save_graph(tmpfile.name)
        st.components.v1.html(open(tmpfile.name, "r", encoding="utf-8").read(), height=600)

    if 'VEP Red Personal:' in df.columns:
        st.write("### Mi Top 10 de Socios")
        st.write("*Los puntos de campañas anteriores sólo son puntos personales")
        top_performers = df[
            ['Nombre del Socio', 'VEP Red Personal:', 'VEP Cat -1', 'VEP Cat -2', 'VEP Cat -3']].copy()
        top_performers = top_performers.rename(
            columns={'VEP Red Personal:': 'Puntos (red) esta campaña',
                     'VEP Cat -1': 'Última campaña',
                     'VEP Cat -2': 'Penúltima campaña',
                     'VEP Cat -3': 'Antepenúltima campaña'})
        top_performers['Puntos (red) esta campaña'] = pd.to_numeric(top_performers['Puntos (red) esta campaña'],
                                                                    errors='coerce').fillna(0).round(2)
        top_performers['Puntos (red) esta campaña'] = pd.to_numeric(top_performers['Puntos (red) esta campaña'],
                                                                    errors='coerce').round(
            2)
        top_performers['Puntos (red) esta campaña'].apply(lambda x: f"{x:,.2f}")
        top_performers['Última campaña'].apply(lambda x: f"{x:,.2f}")
        top_performers['Penúltima campaña'].apply(lambda x: f"{x:,.2f}")
        top_performers['Antepenúltima campaña'].apply(lambda x: f"{x:,.2f}")
        top_performers = top_performers.sort_values(by='Puntos (red) esta campaña', ascending=False).head(10)
        top_performers = top_performers.reset_index(drop=True)
        st.dataframe(top_performers)

        # st.write("### Distribución de Puntos")
        # fig, ax = plt.subplots()
        # df['VEP Red Personal:'].hist(bins=20, color='skyblue', edgecolor='black', ax=ax)
        # ax.set_xlabel("Puntos (BP)")
        # ax.set_ylabel("Cantidad de socios")
        # st.pyplot(fig)

    # Tabla de socios inactivos sin deuda
    st.write("### Socios inactivos sin deuda")
    st.write("*Intenta reactivar a estos socios")
    inactive_no_debt = df[(df['Catálogos Inactivo'] > 2) & (df['Deuda:'] == 0)][
        ['Nombre del Socio', 'Teléfono', 'Catálogos Inactivo']].copy()
    inactive_no_debt['Teléfono'] = inactive_no_debt['Teléfono'].astype(str).str.replace('^52', '', regex=True)
    #inactive_no_debt['Teléfono'] = inactive_no_debt['Teléfono'].str.replace('^52', '', regex=True)
    inactive_no_debt['Catálogos Inactivo'] = inactive_no_debt['Catálogos Inactivo'].astype(int)
    inactive_no_debt = inactive_no_debt.sort_values(by='Catálogos Inactivo', ascending=False).reset_index(drop=True)
    st.dataframe(inactive_no_debt)

    # Tabla de socios con deuda. OJO: la columna Nombre del  Sponsor viene con doble espacio en el reporte
    st.write("### Deuda")
    debtors = df[df['Deuda:'] > 0][['Nombre del Socio', 'Deuda:', 'Teléfono', 'Nombre del  Sponsor']]

    # Remove the '52' from the phone numbers
    debtors['Teléfono'] = debtors['Teléfono'].astype(str).str.replace('^52', '', regex=True)

    # Round 'Deuda:' to two decimal places and remove unnecessary zeros
    debtors['Deuda:'] = debtors['Deuda:'].apply(lambda x: round(x, 2))

    # Sort the dataframe by 'Deuda:'
    debtors = debtors.sort_values(by='Deuda:', ascending=False).reset_index(drop=True)

    # Calculate total debt
    total_debt = debtors['Deuda:'].sum()

    # Display total debt with formatting
    st.write(f"Total de deuda en la red: {total_debt:,.2f}")  # Formatting with commas

    # Format the 'Deuda:' and 'Teléfono' columns with commas and two decimals
    debtors['Deuda:'] = debtors['Deuda:'].apply(lambda x: f"{x:,.2f}")
    debtors['Teléfono'] = debtors['Teléfono'].apply(
        lambda x: str(x))  # Ensure 'Teléfono' is a string for consistent display

    # Set the column width using st.dataframe() and apply some styling
    st.dataframe(debtors.style.set_properties(subset=['Deuda:', 'Teléfono'], **{'min-width': '200px'}))