import streamlit as st
import requests
from lxml import html
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO

def extract_gold_prices():
    url = 'https://www.kitco.com/price/fixes/london-fix'
    response = requests.get(url)
    if response.status_code == 200:
        tree = html.fromstring(response.content)
        dates = []
        gold_pm_prices = []
        for i in range(1, 31):
            date_xpath = f'//*[@id="__next"]/main/div[1]/div/div[4]/div/div/div/div/div[2]/div[{i}]/div[1]/text()'
            gold_pm_xpath = f'//*[@id="__next"]/main/div[1]/div/div[4]/div/div/div/div/div[2]/div[{i}]/div[2]/text()[2]'
            date = tree.xpath(date_xpath)[0].strip() if tree.xpath(date_xpath) else 'N/A'
            gold_pm = tree.xpath(gold_pm_xpath)[0].strip() if tree.xpath(gold_pm_xpath) else 'N/A'
            gold_pm = gold_pm.replace(',', '').replace('.', ',')
            try:
                date_obj = datetime.strptime(date, '%B %d, %Y')
                formatted_date = date_obj.strftime('%d-%m-%Y')
            except ValueError:
                formatted_date = 'N/A'
            dates.append(formatted_date)
            gold_pm_prices.append(gold_pm)
        data = {
            'Fecha': dates,
            'Gold PM': gold_pm_prices
        }
        df = pd.DataFrame(data)
        df.to_excel('precios_oro.xlsx', index=False)
        return df
    else:
        print(f'Error al realizar la solicitud: {response.status_code}')
        return None

def main():
    st.title("Precio del Oro (London Fix) y Formulario")

    if st.button("Actualizar Precio del Oro"):
        df = extract_gold_prices()

        if df is not None and not df.empty:
            latest_date = df['Fecha'].iloc[0]
            latest_price = df['Gold PM'].iloc[0]

            st.markdown(
                f"""
                <div style="border: 2px solid #4CAF50; padding: 20px; border-radius: 10px; text-align: center;">
                    <h2>Último Precio del Oro (Gold PM)</h2>
                    <p style="font-size: 24px; font-weight: bold;">{latest_price} USD</p>
                    <p>Fecha: {latest_date}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.error("No se pudieron obtener los datos del precio del oro.")
    else:
        st.write("Presiona el botón 'Actualizar Precio del Oro' para obtener los datos más recientes.")

    st.header("Formulario de Registro")

    fecha_seleccionada = st.date_input("Fecha")
    encargados = ['Jorge Eduardo Cardona Londoño', 'Cesar Camilo Gonzalez', 'Melissa Rico Rincon']
    hecho_por = st.selectbox("Hecho por", encargados)
    revisado_por = st.selectbox("Revisado por", encargados)
    humedad = st.number_input("Humedad (%)", min_value=0.0, step=0.01)
    remision_laboratorio = st.text_input("Remisión Laboratorio")
    tenor_gt = st.number_input("Tenor (g/t)", min_value=0.0, step=0.01)
    trm = st.number_input("TRM (/US)", min_value=0.0, step=0.01)

    try:
        df_pesos = pd.read_excel("Controldepesos.xlsx")
        df_pesos['Fecha'] = pd.to_datetime(df_pesos['Fecha'])
    except FileNotFoundError:
        st.error("No se encontró el archivo Controldepesos.xlsx")
        df_pesos = None
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo: {e}")
        df_pesos = None

    if df_pesos is not None:
        fecha_inicio_filtro = st.date_input("Fecha de inicio del filtro", value=df_pesos['Fecha'].min())
        fecha_fin_filtro = st.date_input("Fecha de fin del filtro", value=df_pesos['Fecha'].max())

        fecha_inicio_filtro_dt = datetime.combine(fecha_inicio_filtro, datetime.min.time())
        fecha_fin_filtro_dt = datetime.combine(fecha_fin_filtro, datetime.max.time())

        df_filtrado_rango = df_pesos[
            (df_pesos['Fecha'] >= fecha_inicio_filtro_dt) &
            (df_pesos['Fecha'] <= fecha_fin_filtro_dt) &
            (df_pesos['Area'] == 'Formalizacion')
        ]

        materiales_disponibles = df_filtrado_rango['Material'].unique().tolist()
        material_filtro = st.selectbox("Filtrar por material (opcional)", ['Todos'] + materiales_disponibles)

        if material_filtro != 'Todos':
            df_filtrado_rango = df_filtrado_rango[df_filtrado_rango['Material'] == material_filtro]

        st.subheader("Datos filtrados por rango de fechas y área (Formalizacion)")
        st.dataframe(df_filtrado_rango)

        numero_volquetas = len(df_filtrado_rango['Placa'])

        st.write(f"Número de volquetas filtradas: {numero_volquetas}")

        peso_total_humedo = df_filtrado_rango['Peso Neto (Kg)'].sum() / 1000
        total_peso_agua = peso_total_humedo * humedad / 100
        total_toneladas_recibidas = peso_total_humedo - total_peso_agua

        tenor_ozt = tenor_gt / 31.1035
        tenor_ozt_recuperacion = tenor_ozt * 0.87
        onzas_totales = total_toneladas_recibidas * tenor_ozt_recuperacion

        precio_lme = None
        if fecha_seleccionada:
            fecha_seleccionada_str = fecha_seleccionada.strftime('%d-%m-%Y')
            df_precios_oro = pd.read_excel('precios_oro.xlsx', decimal=',')
            precio_lme_fila = df_precios_oro[df_precios_oro['Fecha'] == fecha_seleccionada_str]
            if not precio_lme_fila.empty:
                precio_lme = float(precio_lme_fila['Gold PM'].iloc[0])

        porcentaje_tenor = 0.55 if tenor_gt <= 7.5 else \
            0.51 if 7.5 < tenor_gt <= 15 else \
            0.48 if 15 < tenor_gt <= 20 else \
            0.45 if 20 < tenor_gt <= 30 else \
            0.43 if 30 < tenor_gt <= 40 else \
            0.42 if 40 < tenor_gt <= 60 else 0.41

        if precio_lme is not None:
            limite_superior_120 = 2460.7 * 1.2
            limite_superior_110 = 2460.7 * 1.1
            limite_inferior_95 = 2460.7 * 0.95

            if precio_lme >= limite_superior_120:
                porcentaje_final = porcentaje_tenor - 0.04
            elif limite_superior_110 <= precio_lme < limite_superior_120:
                porcentaje_final = porcentaje_tenor - 0.01
            elif limite_inferior_95 <= precio_lme < limite_superior_110:
                porcentaje_final = porcentaje_tenor
            else:
                porcentaje_final = porcentaje_tenor + 0.01
        else:
            st.error("No se encontró el precio del oro para la fecha seleccionada.")
            porcentaje_final = porcentaje_tenor

        subtotal_usd = onzas_totales * precio_lme * porcentaje_final if precio_lme is not None else 0
        total_bruto = subtotal_usd * trm
        iva = total_bruto * 0.19
        total_neto = total_bruto + iva

        st.write(f"Peso total del material húmedo (t): {peso_total_humedo:.2f}")
        st.write(f"Total peso de agua (t): {total_peso_agua:.2f}")
        st.write(f"Total toneladas recibidas: {total_toneladas_recibidas:.2f}")
        st.write(f"Tenor (oz/t): {tenor_ozt:.4f}")
        st.write(f"Tenor (oz/t) con 87% de recuperación: {tenor_ozt_recuperacion:.4f}")
        st.write(f"Onzas Totales: {onzas_totales:.2f}")
        if precio_lme is not None:
            st.write(f"Precio LME (US$/oz): {precio_lme:.2f}")
        else:
            st.write("Precio LME (US$/oz): No disponible")
        st.write(f"Porcentaje acorde al tenor: {porcentaje_tenor:.2f}")
        st.write(f"Porcentaje final ajustado con el precio del Dólar: {porcentaje_final:.2f}")
        st.write(f"Subtotal US$: {subtotal_usd:.2f}")
        st.write(f"TRM ($/US$): {trm:.2f}")
        st.write(f"Total Bruto ($): {total_bruto:.2f}")
        st.write(f"IVA ($): {iva:.2f}")
        st.write(f"Total Neto ($): {total_neto:.2f}")

    if st.button("Generar PDF"):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        data = [
            ["Campo", "Valor"],
            ["Fecha", str(fecha_seleccionada)],
            ["Hecho por", hecho_por],
            ["Revisado por", revisado_por],
            ["Humedad (%)", str(humedad)],
            ["Remisión Laboratorio", remision_laboratorio],
            ["Tenor (g/t)", str(tenor_gt)],
            ["TRM ($/US$)", str(trm)]
        ]
        if df_pesos is not None:
            precio_lme_str = f"{precio_lme:.2f}" if precio_lme is not None else "No disponible"
            data.extend([
                ["Número de volquetas", str(numero_volquetas)],
                ["Peso total del material húmedo (t)", f"{peso_total_humedo:.2f}"],
                ["Total peso de agua (t)", f"{total_peso_agua:.2f}"],
                ["Total toneladas recibidas", f"{total_toneladas_recibidas:.2f}"],
                ["Tenor (oz/t)", f"{tenor_ozt:.4f}"],
                ["Tenor (oz/t) con 87% de recuperación", f"{tenor_ozt_recuperacion:.4f}"],
                ["Onzas Totales", f"{onzas_totales:.2f}"],
                ["Precio LME (US$/oz)", precio_lme_str],
                ["Porcentaje acorde al tenor", f"{porcentaje_tenor:.2f}"],
                ["Porcentaje final ajustado con el precio del Dólar", f"{porcentaje_final:.2f}"],
                ["Subtotal US$", f"{subtotal_usd:.2f}"],
                ["Total Bruto ($)", f"{total_bruto:.2f}"],
                ["IVA ($)", f"{iva:.2f}"],
                ["Total Neto ($)", f"{total_neto:.2f}"]
            ])

        table = Table(data)
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        table.setStyle(style)
        elements = [table]
        doc.build(elements)
        buffer.seek(0)
        st.download_button(
            label="Descargar PDF",
            data=buffer,
            file_name="formulario.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main()
