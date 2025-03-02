import streamlit as st
import run  # Importa el módulo run.py
import trm  # Importa el módulo trm.py

def main():
    st.sidebar.title("Navegación")
    seleccion = st.sidebar.radio("Seleccione una sección", ["Registro de Pesaje", "Precio del Oro"])

    if seleccion == "Registro de Pesaje":
        st.title("Registro de Pesaje de Material Mineralizado")
        run.main()  # Ejecuta la función principal de run.py
    elif seleccion == "Precio del Oro":
        st.title("Precio del Oro (London Fix)")
        trm.main()  # Ejecuta la función principal de trm.py

if __name__ == "__main__":
    main()