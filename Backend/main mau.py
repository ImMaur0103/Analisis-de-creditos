import pdfplumber
import os
import re
from Modulos.PDF.PDF import OBJ_PDF_Aplicacion, OBJ_PDF_HistorialBancario
import pytesseract
from PIL import Image
import io



pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text_and_images(pdf_path, output_folder, min_size=100000):  # 100000 pixels = 316x316 aproximadamente
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        image_count = 0
        for page_num, page in enumerate(pdf.pages, 1):
            # Extraer texto normal
            text += f"Página {page_num}:\n{page.extract_text()}\n\n"
            
            # Extraer y guardar imágenes
            for img in page.images:
                try:
                    image = Image.open(io.BytesIO(img['stream'].get_data()))
                    
                    # Filtrar por tamaño
                    if image.width * image.height >= min_size:
                        image_count += 1
                        
                        # Convertir la imagen a RGB si está en modo CMYK
                        if image.mode == 'CMYK':
                            image = image.convert('RGB')
                        
                        # Guardar la imagen
                        image_filename = f"image_page{page_num}_{image_count}.png"
                        image_path = os.path.join(output_folder, image_filename)
                        image.save(image_path)
                        
                        
                        text += pytesseract.image_to_string(image) + "\n"
                        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                    else:
                        print(f"Imagen en página {page_num} descartada por tamaño pequeño")
                except Exception as e:
                    print(f"Error al procesar imagen en página {page_num}: {str(e)}")
    
    return text


def extract_text_from_images(pdf_path, output_folder, min_size=100000):  # 100000 pixels = 316x316 aproximadamente
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    Words = []

    with pdfplumber.open(pdf_path) as pdf:
        text = ""
        image_count = 0                        
        Textos = []
        texto = ''
        for page_num, page in enumerate(pdf.pages, 1):
            # Uso de la función
            page_info = get_pdf_coordinate_origin(page)
            # Extraer texto normal
            words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
            data = {'text':[]}
            # Extraer y guardar imágenes
            for img in page.images:
                try:
                    image = Image.open(io.BytesIO(img['stream'].get_data()))
                    
                    # Filtrar por tamaño
                    if image.width * image.height >= min_size:
                        image_count += 1
                        
                        # Convertir la imagen a RGB si está en modo CMYK
                        if image.mode == 'CMYK':
                            image = image.convert('RGB')
                        
                        # Guardar la imagen
                        image_filename = f"image_page{page_num}_{image_count}.png"
                        image_path = os.path.join(output_folder, image_filename)
                        #image.save(image_path)
                        
                        
                        #text += pytesseract.image_to_string(image) + "\n"
                        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

                        for i in range(len(data['text'])):
                            if data['text'][i] == '':
                                if texto != '':
                                    Textos.append([texto, left_original, top_original, width_original, height_original])
                                texto = ''
                                left_anterior = data['left'][i]
                                width_anterior = data['width'][i]
                                continue
                            else:
                                if texto == '':
                                    texto = data['text'][i]
                                    left_original = data['left'][i]
                                    top_original = data['top'][i]
                                    width_original = data['width'][i]
                                    height_original = data['height'][i]
                                elif (data['left'][i] - (left_anterior + width_anterior)) <= 15:
                                    texto += ' ' + data['text'][i]
                                    width_original += data['width'][i] + (data['left'][i] - (left_anterior + width_anterior))
                                else:
                                    Textos.append([texto, left_original, top_original, width_original, height_original])
                                    texto = data['text'][i]
                                left_anterior = data['left'][i]
                                width_anterior = data['width'][i]
                    else:
                        print(f"Imagen en página {page_num} descartada por tamaño pequeño")
                except Exception as e:
                    print(f"Error al procesar imagen en página {page_num}: {str(e)}")

            for word in words:
                pass

    return text

#-------------------------------------------------------------------
def get_pdf_coordinate_origin(page):
    # Analizamos cómo se procesan las coordenadas Y
    test_y = 100
    converted_y = page.point2coord((0, test_y))[1]
    
    if converted_y == page.height - test_y:
        origin = 'bottom_left'
    elif converted_y == test_y:
        origin = 'top_left'
    else:
        raise ValueError("No se puede determinar el origen de coordenadas del PDF")
    
    return {
        'origin': origin,
        'width': page.width,
        'height': page.height
    }

#-------------------------------------------------------------------
def extract_info(text):
    # Diccionario para almacenar la información extraída
    info = {}
    
    # Patrones para buscar la información específica
    patterns = {
        'BUSINESS LEGAL NAME': r'BUSINESS LEGAL NAME:.*?(\w+(?:\s+\w+)*)',
        'OWN OR RENT BUSINESS LOCATION': r'OWN OR RENT BUSINESS LOCATION:\s*(\w+)',
        'BUSINESS DBA NAME': r'BUSINESS DBA NAME:.*?(\w+(?:\s+\w+)*)',
        'TYPE OF BUSINESS ENTITY': r'TYPE OF BUSINESS ENTITY:\s*(\w+(?:\s+\w+)*)',
        'STATE OF INCORPORATION': r'STATE OF INCORPORATION:\s*\[(\w+)\]',
        'INDUSTRY': r'INDUSTRY:\s*(\w+(?:\s+\w+)*)',
        'GROSS ANNUAL SALES': r'GROSS ANNUAL SALES:.*?(\d+)',
        'BUSINESS START DATE': r'BUSINESS START DATE:.*?(\d{2}/\d{2}/\d{4})',
        'BUSINESS FEDERAL TAX ID': r'BUSINESS FEDERAL TAX ID #:\s*(\d+-\d+)',
        'AMOUNT REQUESTED': r'AMOUNT REQUESTED:\s*(\d+)',
        'LEGAL FIRST NAME': r'LEGAL FIRST NAME:\s*(\w+)',
        'LEGAL LAST NAME': r'LEGAL LAST NAME:\s*(\w+)',
        'SSN': r'SSN:\s*(\d+-\d+-\d+)',
        'DATE OF BIRTH': r'DATE OF BIRTH:.*?(\d{2}/\d{2}/\d{4})',
        'EMAIL': r'EMAIL:\s*(\S+@\S+)'
    }
    
    # Buscar cada patrón en el texto
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            info[key] = match.group(1).strip()
    
    return info


def read_pdf_structured(file_path):
    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
            
            # Ordenar las palabras por su posición vertical, luego horizontal
            words.sort(key=lambda w: (w['top'], w['x0']))
            
            current_y = None
            line = ""
            for word in words:
                if current_y is None:
                    current_y = word['top']
                
                # Si cambiamos de línea, añadimos la línea actual al texto completo
                if abs(word['top'] - current_y) > 2:  # Ajusta este valor según sea necesario
                    full_text += line.strip() + "\n"
                    line = ""
                    current_y = word['top']
                
                # Añadimos la palabra a la línea actual
                line += word['text'] + " "
            
            # Añadimos la última línea
            full_text += line.strip() + "\n\n"
    
    return full_text


def read_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        full_text = ""
        full_text_table = ""
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=3, y_tolerance=3)
            full_text += text + "\n\n"
            
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    full_text_table += " | ".join(str(cell) for cell in row if cell) + "\n"
            full_text += "\n"
            
            words = page.extract_words()
            full_text += " ".join(word["text"] for word in words) + "\n\n"
    
    with pdfplumber.open(file_path) as pdf:
        full_texto = ""
        for page in pdf.pages:
            words = page.extract_words()
            full_texto += " ".join(word["text"] for word in words) + "\n\n"
    
    return full_text



def TestReadPDF():
    Examples_path = 'D:\Downloads\G2L (Ultimate)\Bank Statements (Examples)'
    Banks = ['BELLILEY TRAVEL LLC', 'FAB Trading Inc', 'Lupfer Equipment LLC', 'SANTA FE NEWS AND ESPRESSO DESIGN DISTRICT CORP', 'TARO GROUP LLC']

    for Example in Banks:
        Bank_path = os.path.join(Examples_path, Example)
        for PDF in os.listdir(Bank_path):
            print(PDF)
            if PDF == 'Rok App - Manuel Arvelo - FULL.pdf' or PDF == '41a5-Application.pdf' or PDF == 'Lupfer-Equipment-LLC.pdf' or PDF == 'Sub App(Jan-29-2024 0301 AM).kRdY.pdf' or PDF == 'CARE 1 - TORO GROUP LLC (1).pdf':
                Pdf = OBJ_PDF_Aplicacion(os.path.join(Bank_path, PDF))
            else:
                Pdf = OBJ_PDF_HistorialBancario(os.path.join(Bank_path, PDF))
            text_content = read_pdf_structured(os.path.join(Bank_path, PDF))

            extracted_info = extract_info(text_content)
            for key, value in extracted_info.items():
                print(f"{key}: {value}")




TestReadPDF()
