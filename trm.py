import streamlit as st
import requests
from lxml import html
import pandas as pd
from datetime import datetime

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
    st.title("Precio del Oro (London Fix)")

    if st.button("Actualizar Precio del Oro"): # Botón para actualizar
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
    else: # Muestra un mensaje inicial antes de la primera actualización
        st.write("Presiona el botón 'Actualizar Precio del Oro' para obtener los datos más recientes.")

if __name__ == "__main__":
    main()