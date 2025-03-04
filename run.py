import streamlit as st
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Image
import os
from datetime import datetime
from reportlab.lib.enums import TA_CENTER, TA_LEFT

def generar_pdf(df_pdf, fecha_form, material_form, encargado_form, lugar_recepcion, nombre_entrega, cargo_entrega, nombre_recibe_formalizacion, cargo_recibe_formalizacion, nombre_recibe_operaciones, cargo_recibe_operaciones, imagen_path, horas_inicio_fin):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    style_centered = ParagraphStyle('centered', parent=styles['Normal'], alignment=TA_CENTER)
    style_left = ParagraphStyle('left', parent=styles['Normal'], alignment=TA_LEFT)
    elements = []

    try:
        if os.path.exists(imagen_path):
            imagen = Image(imagen_path, width=2.5 * inch, height=0.8 * inch)
        else:
            st.error(f"No se encontró la imagen en la ruta: {imagen_path}")
            st.stop()

        table_header = Table([[imagen,
                                Paragraph("REGISTRO DE PESAJE DE MATERIAL MINERALIZADO<br/>RECIBIDO DE LAS FORMALIZACIONES", styles['Heading3'])]],
                                colWidths=[3 * inch, 5 * inch])
        table_header.setStyle(TableStyle([('ALIGN', (0, 0), (0, 0), 'LEFT'),
                                            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                            ('LEFTPADDING', (1, 0), (1, 0), 10)]))
        elements.append(table_header)
        elements.append(Spacer(1, 0.2 * inch))
            
        sociedad = material_form[0] if material_form else "N/A"
            
        info_data = [
            [Paragraph('Fecha:', styles['Normal']), Paragraph(fecha_form.strftime('%d/%m/%Y'), styles['Normal']),
             Paragraph('Sociedad:', styles['Normal']), Paragraph(sociedad, styles['Normal'])],

            [Paragraph('Encargado Pesaje FM:', styles['Normal']), Paragraph(encargado_form, styles['Normal']),
             Paragraph('Frente de explotación:', styles['Normal']), Paragraph('N/A', styles['Normal'])],

            [Paragraph('Hora de inicio:', styles['Normal']), Paragraph(horas_inicio_fin[0], styles['Normal']),
             Paragraph('Lugar del pesaje:', styles['Normal']), Paragraph('Higabra', styles['Normal'])],

            [Paragraph('Hora Fin:', styles['Normal']), Paragraph(horas_inicio_fin[1], styles['Normal']),
             Paragraph('Lugar de recepción y muestreo:', styles['Normal']), Paragraph(lugar_recepcion, styles['Normal'])],
        ]
        num_cols_info = len(info_data[0])
        ancho_columna_info = 7.5 * inch / num_cols_info
        info_table = Table(info_data, colWidths=[ancho_columna_info] * num_cols_info)
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, 'black')
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 0.2 * inch))
            
        # Obtener los totales de la fila "Totales"
        total_vacio = df_pdf.loc[df_pdf['Hora de Pesaje'] == 'Totales', 'Peso Volqueta Vacia'].values[0] / 1000
        total_lleno = df_pdf.loc[df_pdf['Hora de Pesaje'] == 'Totales', 'Peso Volqueta Llena'].values[0] / 1000
        total_neto = df_pdf.loc[df_pdf['Hora de Pesaje'] == 'Totales', 'Total'].values[0] / 1000
            
        # Crear la nueva tabla con los totales en toneladas
        totales_data = [
            [Paragraph('Total peso camiones vacios (Ton)', styles['Normal']), Paragraph(f"{total_vacio:.2f}", style_centered),
             Paragraph('Total peso camiones cargados (Ton)', styles['Normal']), Paragraph(f"{total_lleno:.2f}", style_centered),
             Paragraph('Peso total del material pesado (Ton)', styles['Normal']), Paragraph(f"{total_neto:.2f}", style_centered)],
        ]
        num_cols_totales = len(totales_data[0])
        ancho_columna_totales = 7.5 * inch / num_cols_totales
        totales_table = Table(totales_data, colWidths=[ancho_columna_totales] * num_cols_totales)
        totales_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, 'black')
        ]))
        elements.append(totales_table)
        elements.append(Spacer(1, 0.2 * inch))
            
        table_data = [df_pdf.columns.tolist()] + df_pdf.values.tolist()
        num_cols_data = len(table_data[0])
        ancho_columna_data = 7.5 * inch / num_cols_data
        table = Table(table_data, colWidths=[ancho_columna_data] * num_cols_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#d5d5d5'),
            ('GRID', (0, 0), (-1, -1), 1, 'black'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER')
        ]))
        elements.append(table)

        elements.append(Spacer(1, 0.5 * inch))

        # Secciones de firma
        firma_data = [
            [Paragraph('Nombre de quien entrega (Empresa FM)', styles['Normal']), Paragraph(nombre_entrega, styles['Normal']), Paragraph(cargo_entrega, styles['Normal']), Paragraph('Firma:', styles['Normal'])],
            [Paragraph('Nombre de quien recibe (Formalización)', styles['Normal']), Paragraph(nombre_recibe_formalizacion, styles['Normal']), Paragraph(cargo_recibe_formalizacion, styles['Normal']), Paragraph('Firma:', styles['Normal'])],
            [Paragraph('Nombre de quien recibe (Operaciones)', styles['Normal']), Paragraph(nombre_recibe_operaciones, styles['Normal']), Paragraph(cargo_recibe_operaciones, styles['Normal']), Paragraph('Firma:', styles['Normal'])],
        ]
        num_cols_firma = len(firma_data[0])
        ancho_columna_firma = 7.5 * inch / num_cols_firma
        firma_table = Table(firma_data, colWidths=[ancho_columna_firma] * num_cols_firma)
        firma_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, 'black')
        ]))
        elements.append(firma_table)

        elements.append(Spacer(1, 0.5 * inch))

        # Observaciones
        observaciones_text = """
        <b>Observaciones:</b><br/><br/>
        <b>Para recepción de mineral los días sábados, domingos y festivos:</b><br/><br/>
        • Se tomará el precio del Au segúnla Bolsa de Metde Londres en su versión p.m. correspondiente al ultimo día hábil previo a la entrega de mineral, tomando así para las entregas los días sábados y domingos el precio del Au correspondiente al del día viernes.<br/><br/>
        • El TRM se tomará del día del envió.
        """
        num_cols_observaciones = 1
        ancho_columna_observaciones = 7.5 * inch / num_cols_observaciones
        observaciones_data = [[Paragraph(observaciones_text, style_left)]]
        observaciones_table = Table(observaciones_data, colWidths=[ancho_columna_observaciones] * num_cols_observaciones)
        observaciones_table.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), 1, 'black')]))
        elements.append(observaciones_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Ocurrió un error al generar el PDF: {e}")
        return None

def main(): #Encapsulamiento del código principal dentro de la función main.
    # Cargar los datos
    try:
        data = pd.read_excel(r"Controldepesos.xlsx")
        df = pd.DataFrame(data)
    except FileNotFoundError:
        st.error("No se encontró el archivo Controldepesos.xlsx")
        st.stop()
    except Exception as e:
        st.error(f"Ocurrió un error al cargar el archivo: {e}")
        st.stop()

    # Filtrar por área "Formalizacion"
    df = df[df['Area'] == 'Formalizacion'].copy()

    # Convertir la columna de fecha a tipo datetime
    df['Fecha'] = pd.to_datetime(df['Fecha'])

    # Mostrar el título de la aplicación
    st.title('Base de Datos con Filtrado')

    # Agregar una casilla de selección para el encargado de pesaje
    encargados = ['Jorge Eduardo Cardona Londoño', 'Cesar Camilo Gonzalez','Melissa Rico Rincon']
    encargado_seleccionado = st.selectbox('Encargado Pesaje FM', encargados)

    # Filtrado por fecha
    fecha_inicio = st.date_input('Fecha inicio', min_value=df['Fecha'].min(), max_value=df['Fecha'].max(), value=df['Fecha'].min())
    fecha_fin = st.date_input('Fecha fin', min_value=df['Fecha'].min(), max_value=df['Fecha'].max(), value=df['Fecha'].max())
    df_filtered_fecha = df[(df['Fecha'] >= pd.to_datetime(fecha_inicio)) & (df['Fecha'] <= pd.to_datetime(fecha_fin))]

    # Filtrado por material
    materiales = df_filtered_fecha['Material'].unique()
    material_seleccionado = st.multiselect('Selecciona Material', materiales)

    # Nueva lista desplegable para "Lugar de recepción y muestreo"
    lugares_recepcion = ['Platanal', 'Otro']
    lugar_recepcion_seleccionado = st.selectbox('Lugar de recepción y muestreo', lugares_recepcion)

    if lugar_recepcion_seleccionado == 'Otro':
        lugar_recepcion_seleccionado = st.text_input('Por favor, ingresa el nombre del lugar de recepción y muestreo')

    st.write(f'Has seleccionado: {lugar_recepcion_seleccionado}')

    # Campos para las firmas
    nombre_entrega = 'Luis Fernando Ascencio'
    cargo_entrega = 'Gerente'

    # Display fixed options
    st.write(f'Nombre de quien entrega (Empresa FM): {nombre_entrega}')
    st.write(f'Cargo de quien entrega (Empresa FM): {cargo_entrega}')

    nombres_recibe_formalizacion = [
        'Jorge Eduardo Cardona Londoño',
        'Cesar Camilo Gonzalez',
        'Melissa Rico Rincon'
    ]

    # Dropdown list for names
    nombre_recibe_formalizacion = st.selectbox('Nombre de quien recibe (Formalización)', nombres_recibe_formalizacion)

    # Fixed cargo
    cargo_recibe_formalizacion = 'Servicios Técnicos Formalización'

    # Display selected options
    st.write(f'Nombre: {nombre_recibe_formalizacion}')
    st.write(f'Cargo: {cargo_recibe_formalizacion}')

    nombres_recibe_operaciones = [
        'Jaime Alberto Higuita',
        'Farley Alexander Giron',
        'Daniel Usuga',
        'Sebastian Usuga',
        'Hector Florez',
        'Juliana Valle',
        'Roberto Higuita',
        'Juliana Usuga',
        'Luz Nedy Cossio',
        'Olga Lucia Holguin',
        'Ana Rosa Moreno',
        'Aida Cataño'
    ]

    # Dropdown list for names
    nombre_recibe_operaciones = st.selectbox('Nombre de quien recibe (Operaciones)', nombres_recibe_operaciones)

    # Fixed cargo
    cargo_recibe_operaciones = 'Gerente'

    # Display selected options
    st.write(f'Nombre: {nombre_recibe_operaciones}')
    st.write(f'Cargo: {cargo_recibe_operaciones}')

    # Ruta de la imagen
    imagen_path = "Img/logozcnl.png"

    # Mostrar la tabla filtrada con los datos especificados y los nuevos títulos
    if material_seleccionado:
            df_filtered_material = df_filtered_fecha[df_filtered_fecha['Material'].isin(material_seleccionado)].copy()

            # Seleccionar solo las columnas especificadas y renombrarlas, incluyendo 'Fecha'
            df_filtered_material_display = df_filtered_material[['Fecha', 'Hora', 'Placa', 'Peso Tara (Kg)', 'Peso Bruto (Kg)', 'Peso Neto (Kg)']].copy()
            df_filtered_material_display.columns = ['Fecha', 'Hora de Pesaje', 'Placa', 'Peso Volqueta Vacia', 'Peso Volqueta Llena', 'Total']

            # Formatear la columna 'Fecha' para mostrar solo la fecha (sin la hora)
            df_filtered_material_display['Fecha'] = df_filtered_material_display['Fecha'].dt.strftime('%d/%m/%Y')

            # No se realiza ninguna conversión en la columna "Hora de Pesaje"
            # Los datos se mantienen tal como están en el DataFrame original

            # Calcular los totales de los tres últimos ítems
            totales = df_filtered_material_display[['Peso Volqueta Vacia', 'Peso Volqueta Llena', 'Total']].sum().to_frame().T
            totales['Hora de Pesaje'] = 'Totales'
            totales['Placa'] = ''
            totales['Fecha'] = ''  # Añadir una columna 'Fecha' vacía para la fila de totales
            df_final = pd.concat([df_filtered_material_display, totales], ignore_index=True)

            # Obtener horas de inicio y fin y convertirlas a strings
            horas_inicio_fin = [df_filtered_material['Hora'].iloc[0].strftime('%H:%M:%S'), df_filtered_material['Hora'].iloc[-1].strftime('%H:%M:%S')]

            # Mostrar la tabla final
            st.write(df_final)

            # Botón para generar y descargar el PDF
            if st.button('Generar y Descargar PDF'):
                buffer = generar_pdf(df_final, fecha_inicio, material_seleccionado, encargado_seleccionado, lugar_recepcion_seleccionado, nombre_entrega, cargo_entrega, nombre_recibe_formalizacion, cargo_recibe_formalizacion, nombre_recibe_operaciones, cargo_recibe_operaciones, imagen_path, horas_inicio_fin)
                if buffer:
                    # Generar el nombre del archivo con fecha y nombre de la sociedad
                    fecha_str = fecha_inicio.strftime('%Y%m%d')
                    sociedad = material_seleccionado[0].replace(" ", "_") # Reemplazar espacios por guiones bajos
                    file_name = f'registro_pesaje_{fecha_str}_{sociedad}.pdf'

                    st.download_button('Descargar PDF', data=buffer, file_name=file_name, mime='application/pdf')
    else:
            st.write("Por favor, selecciona al menos un material para filtrar los datos.")

if __name__ == "__main__":
    main()
