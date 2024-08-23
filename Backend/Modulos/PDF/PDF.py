import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod
import pdfplumber
from PIL import Image
import PIL
import io
import pytesseract
from Query.Connector import load_Json, Files
import re

# Configuración de pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Carga de información de configuración
Information_app = load_Json(Files['application'])
Information_banck = load_Json(Files['bank_history'])

class ConfigManager:
    def __init__(self):
        self.config = load_Json(Files['bank_history_conf'])
    
    def get_account_info_patterns(self):
        return self.config['account_info']['patterns']
    
    def get_date_range_patterns(self):
        return self.config['date_range']['patterns']
    
    def get_account_summary_fields(self):
        return self.config['account_summary']['fields']
    
    def get_transaction_patterns(self):
        return self.config['transactions']['patterns']
    
    def get_deposit_keywords(self):
        return self.config['deposits']['keywords']
    
    def get_withdrawal_keywords(self):
        return self.config['withdrawals']['keywords']
    
    def get_deposit_criteria(self):
        return self.config['deposits']['analysis']
    
    def get_account_health_criteria(self):
        return self.config['account_health']
    
    def get_business_info_criteria(self):
        return self.config['business_info']['criteria']
    
    def get_funding_criteria(self):
        return self.config['funding_criteria']

class OBJ_PDF(ABC):
    def __init__(self, filename):
        self.filename = filename

        try:
            self.pdf = pdfplumber.open(self.filename)
        except Exception as e:
            raise ValueError(f"Error al abrir el archivo PDF: {e}")
        self.config = ConfigManager()
        self.Pages = []
        self.tables = []
        self.Type = self.determine_pdf_type()
        self.Date = None
        self.PDF_content = ""
        self.initialize_pages()
        self.extract_tables()

    @abstractmethod
    def determine_pdf_type(self):
        return "Estado de Cuenta"

    @abstractmethod
    def load_info_json(self):
        return ""

    def initialize_pages(self):
        for page in self.pdf.pages:
            obj_page = OBJ_PAGE(page.page_number, page, self.Type)
            self.Pages.append(obj_page)
            self.PDF_content += obj_page.Text + "\n"

    def extract_tables(self):
        for page in self.pdf.pages:
            tables = page.extract_tables()
            if tables:
                self.tables.extend(tables)

    def extract_info(self, info_dict, target_dict):
        for key, value in info_dict.items():
            if isinstance(value, dict):
                target_dict[key] = {}
                self.extract_info(value, target_dict[key])
            else:
                for Find in value:
                    for Page in self.Pages:
                        if Find.lower() in Page.Text.lower():
                            escaped_find = re.escape(Find.lower())
                            pattern = rf"{escaped_find}(:|\s|\s+)([^\r\n\t]+)"
                            
                            match = re.search(pattern, Page.Text.lower(), re.IGNORECASE)
                            
                            if match and match.group(1) != '':
                                extracted_value = match.group(2).strip()
                                extracted_value = re.split(r'\s{2,}|\t|\n', extracted_value)[0]
                                target_dict[key] = self.process_value(key, extracted_value)
                            else:
                                target_dict[key] = None
                            break
                    if key in target_dict:
                        break

    def process_value(self, key, value):
        if key in ['funder_deposits', 'overdrafts_returns', 'default_negative_days', 'low_days', 'bounced_payments']:
            return int(value) if value.isdigit() else 0
        elif key in ['avg_monthly', 'min_monthly']:
            return float(value.replace(',', '')) if value.replace(',', '').replace('.', '').isdigit() else 0.0
        elif key == 'recovery_last_month':
            return value.lower() == 'true' or value.lower() == 'yes'
        elif key == 'keywords':
            return [keyword.strip() for keyword in value.split(',') if keyword.strip()]
        else:
            return value

class OBJ_PDF_Aplicacion(OBJ_PDF):
    def __init__(self, filename):
        super().__init__(filename)
        self.personal_json = {}
        self.business_json = {}
        self.load_info_json()

    def determine_pdf_type(self):
        return "Aplicacion"

    def load_info_json(self):
        Business = Information_app["business_info"]
        Personal = Information_app["personal_info"]

        for key, value in Business.items():
            for Find in value:
                for Page in self.Pages:
                    found = False
                    if Find.lower() in Page.Text.lower():
                        found = True
                        escaped_find = Find.lower()
                        # Expresión regular ajustada
                        pattern = rf"{escaped_find}(:|\s|\s+)([^\r\n\t]+)"
                        
                        match = re.search(pattern, Page.Text.lower(), re.IGNORECASE)
                        
                        if match and match.group(1) != '':
                            extracted_value = match.group(2).strip()
                            # Limpiar el valor extraído
                            extracted_value = re.split(r'\s{2,}|\t|\n', extracted_value)[0]
                            self.business_json[key] = extracted_value
                        else:
                            self.business_json[key] = None
                        break
                    else:
                        break
                if found:
                    found = False
                    break

        for key, value in Personal.items():
            for Find in value:
                for Page in self.Pages:
                    found = False
                    if Find.lower() in Page.Text.lower():
                        found = True
                        escaped_find = re.escape(Find)
                        pattern = rf"{escaped_find}(:|\s|\s+)([^\r\n\t]+)"
                        match = re.search(pattern, Page.Text, re.IGNORECASE)
                        
                        if match:
                            extracted_value = match.group(1).strip()
                            # Limpiar el valor extraído
                            extracted_value = re.split(r'\s{2,}|\t|\n', extracted_value)[0]
                            self.personal_json[key] = extracted_value
                        else:
                            self.personal_json[key] = None
                        break
                if found:
                    found = False
                    break

class OBJ_PDF_HistorialBancario(OBJ_PDF):
    def __init__(self, filename):
        super().__init__(filename)
        self.extract_transactions()
        self.extract_account_info()
        self.bank_statement_json = {}
        self.load_info_json()

    def determine_pdf_type(self):
        return "Estado de Cuenta"

    def load_info_json(self):
        Bank_Statement = Information_banck["bank_statement_info"]
        self.extract_info(Bank_Statement, self.bank_statement_json)

    def set_account_statement_date(self, date):
        self.Date = date

    def extract_account_info(self):
        patterns = self.config.get_account_info_patterns()
        for pattern in patterns:
            matrch = re.findall(pattern, self.PDF_content)
            if matrch is not None:
                self.account_info = matrch[0]
                break
        pass
        

    def extract_transactions(self):
        patterns = self.config.get_transaction_patterns()
        deposit_keywords = self.config.get_deposit_keywords()
        withdrawal_keywords = self.config.get_withdrawal_keywords()
        lines = self.PDF_content.split('\n')
        tables = []
        current_table = None
        
        for line in lines:
            if self.is_table_title(line) and current_table is None:
                if current_table is not None:
                    tables.append(current_table)
                current_table = {
                    "title": line,
                    "header": "",
                    "rows": [],
                    "invalid_rows": []
                }
            elif self.is_table_header(line):
                if current_table is not None:
                    current_table["header"] = self.return_table_header(line)
            elif current_table is not None and current_table["header"]:
                rows = self.validate_row_with_header(current_table["header"], line)
                if rows:
                    current_table["rows"].append(rows)
                elif 'subtotal' in line.lower() or 'total' in line.lower():
                    tables.append(current_table)
                    current_table = None

        
        if current_table is not None:
            tables.append(current_table)

        pass
        # Usar los patrones y palabras clave para extraer y clasificar las transacciones

    def is_table_header(self, line):
        return ("Date".lower() in line.lower() and "Description".lower() in line.lower() and "Amount".lower() in line.lower() or
                "Date".lower() in line.lower() and " Balance ($)".lower() in line.lower())

    def return_table_header(self, line):
        if "Date".lower() in line.lower() and "Description".lower() in line.lower() and "Amount".lower() in line.lower():
            return ["Date", "Description", "Amount"]
        elif "Date".lower() in line.lower() and "Balance ($)".lower() in line.lower():
            return ["Date", "Balance ($)"]

    def is_table_title(self, line):
        titles = ["Deposits and other credits", "Withdrawals and other debits", "Daily ledger balances"]
        return line in titles

    def validate_row_with_header(self, header_columns, row):
        row_columns = ([elemento for elemento in row.split('\t') if elemento] if '\t' in row else [elemento for elemento in row.split(' ') if elemento])
        

        # Expresiones regulares
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',  # mm/dd/yyyy
            r'\d{2}/\d{2}/\d{2}',  # mm/dd/yy
            r'\d{2}/\d{2}',  # mm/dd
            r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}'  # dd MMM yyyy
        ]
        amount_pattern = r'-?[\$]?[\d,]+\.\d{1,4}'

        date_valid = False
        amount_valid = False
        date_valid = any(re.match(pattern, row) for pattern in date_patterns)
        amount_valid = re.match(amount_pattern, row) is not None

        # Intentar corregir errores comunes
        if len(row_columns) > len(header_columns) and (amount_valid and amount_valid):
            row_columns = self.repair_row(header_columns, row_columns)
        elif len(row_columns) < len(header_columns):
            if not (date_valid and amount_valid):
                return None
        
        for i, column in enumerate(header_columns):
            if column.lower() == "date":
                date_valid = any(re.match(pattern, row_columns[i]) for pattern in date_patterns)
            elif column.lower() == "amount":
                amount_valid = re.match(amount_pattern, row_columns[i]) is not None

        return row_columns

    def repair_row(self, header_columns, row_columns):
        # Expresiones regulares
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',  # mm/dd/yyyy
            r'\d{2}/\d{2}/\d{2}',  # mm/dd/yy
            r'\d{2}/\d{2}',  # mm/dd
            r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}'  # dd MMM yyyy
        ]
        amount_pattern = r'-?[\$]?[\d,]+\.\d{1,4}'
        while len(row_columns) > len(header_columns):
            # Intentar unir columnas rotas basadas en patrones conocidos
            combined_columns = []
            skip = False
            for i in range(len(row_columns)):
                amount_valid = re.match(amount_pattern, row_columns[i]) is not None
                date_valid = any(re.match(pattern, row_columns[i]) for pattern in date_patterns)
                if skip:
                    skip = False
                    continue
                if i < len(row_columns) - 1 and row_columns[i] + " " + row_columns[i + 1] and not (amount_valid or date_valid):
                    combined_columns.append(row_columns[i] + " " + row_columns[i + 1])
                    skip = True
                else:
                    combined_columns.append(row_columns[i])
            row_columns = combined_columns
        return row_columns

    def parse_pdf_content(self, pdf_content):
        lines = pdf_content.split('\n')
        tables = []
        current_table = None
        
        for line in lines:
            if self.is_table_title(line) and current_table is None:
                if current_table is not None:
                    tables.append(current_table)
                current_table = {
                    "title": line,
                    "header": "",
                    "rows": [],
                    "invalid_rows": []
                }
            elif self.is_table_header(line):
                if current_table is not None:
                    current_table["header"] = self.return_table_header(line)
            elif current_table is not None and current_table["header"]:
                rows = self.validate_row_with_header(current_table["header"], line)
                if rows:
                    current_table["rows"].append(rows)
                elif 'subtotal' in line.lower() or 'total' in line.lower():
                    tables.append(current_table)
                    current_table = None

        
        if current_table is not None:
            tables.append(current_table)
        
        return tables




class OBJ_PAGE:
    def __init__(self, page_num, page, doc_type):
        self.page = page
        self.page_num = page_num
        self.Text = ''
        self.words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
        self.data = {}
        self.doc_type = doc_type
        self.process_page(page, doc_type)

    def process_page(self, page, doc_type):
        # Procesar el texto normal de la página
        self.Text = page.extract_text()

        # Procesar imágenes si las hay
        for index, img in enumerate(page.images, 1):
            try:
                image = Image.open(io.BytesIO(img['stream'].get_data()))
                if image.mode == 'CMYK':
                    image = image.convert('RGB')
                
                image_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                
                # Filtrar palabras vacías
                non_empty_indices = [i for i, text in enumerate(image_data['text']) if text.strip()]
                
                if non_empty_indices:  # Si hay texto no vacío
                    # Filtrar los datos para incluir solo texto no vacío
                    filtered_image_data = {key: [image_data[key][i] for i in non_empty_indices] for key in image_data.keys()}
                    
                    # Agrupar el texto de la imagen en oraciones
                    image_sentences = group_text(
                        filtered_image_data['text'], 
                        filtered_image_data['left'], 
                        filtered_image_data['top'],
                        filtered_image_data['width'],
                        filtered_image_data['height']
                    )
                    
                    if image_sentences:  # Si hay oraciones después de agrupar
                        self.data[f'Data_{index}'] = {
                            'image_data': filtered_image_data,
                            'image_sentences': image_sentences,
                            'image_info': {
                                'x0': img['x0'],
                                'y0': img['top'],
                                'width': img['width'],
                                'height': img['height'],
                                'image_width': image.width,
                                'image_height': image.height
                            }
                        }
            except PIL.UnidentifiedImageError:
                print(f"Warning: Could not identify image on page {self.page_num}. Skipping this image.")
            except Exception as e:
                print(f"Warning: An error occurred while processing an image on page {self.page_num}: {str(e)}. Skipping this image.")

        # Agrupar las palabras del PDF en oraciones
        self.pdf_sentences = group_words(self.words)

        # Si hay datos de imagen, combinar con el texto de la página
        if self.data:
            self.combine_text_and_image_data()
        elif doc_type == 'Aplicacion':
            self.combine_text_sentences_data()
        

    def combine_text_and_image_data(self):
        combined_text = []
        used_image_sentences = set()

        # Primero, procesamos las oraciones del PDF
        for pdf_sentence in self.pdf_sentences:
            sentence_added = False
            for data_key, data_value in self.data.items():
                image_sentences = data_value['image_sentences']
                image_info = data_value['image_info']
                
                coordinator = PDFOCRCoordinator(
                    pdf_width=self.page.width,
                    pdf_height=self.page.height,
                    image_width=image_info['width'],
                    image_height=image_info['height'],
                    image_x0=image_info['x0'],
                    image_y0=image_info['y0'],
                    ocr_width=image_info['image_width'],
                    ocr_height=image_info['image_height'],
                    pdf_origin='top_left',
                    ocr_origin='top_left'
                )

                for i, image_sentence in enumerate(image_sentences):
                    if coordinator.compare_sentence_locations(
                        pdf_sentence, 
                        image_sentence,
                        threshold=50
                    ):
                        pdf_coords = coordinator.ocr_to_pdf(image_sentence['left'], image_sentence['top'])
                        combined_text.append({
                            'text': image_sentence['text'] + " " + pdf_sentence['text'],
                            'left': pdf_coords[0],
                            'top': pdf_coords[1],
                            'width': max(image_sentence['width'], pdf_sentence['width']),
                            'height': max(image_sentence['height'], pdf_sentence['height'])
                        })
                        used_image_sentences.add((data_key, i))
                        sentence_added = True
                        break
                if sentence_added:
                    break
            if not sentence_added:
                combined_text.append({
                    'text': pdf_sentence['text'],
                    'left': pdf_sentence['x0'],
                    'top': pdf_sentence['top'],
                    'width': pdf_sentence['width'],
                    'height': pdf_sentence['height']
                })

        # Ahora, agregamos las oraciones de las imágenes que no se emparejaron
        for data_key, data_value in self.data.items():
            image_sentences = data_value['image_sentences']
            image_info = data_value['image_info']
            
            coordinator = PDFOCRCoordinator(
                pdf_width=self.page.width,
                pdf_height=self.page.height,
                image_width=image_info['width'],
                image_height=image_info['height'],
                image_x0=image_info['x0'],
                image_y0=image_info['y0'],
                ocr_width=image_info['image_width'],
                ocr_height=image_info['image_height'],
                pdf_origin='top_left',
                ocr_origin='top_left'
            )

            for i, image_sentence in enumerate(image_sentences):
                if (data_key, i) not in used_image_sentences:
                    pdf_coords = coordinator.ocr_to_pdf(image_sentence['left'], image_sentence['top'], image_sentence['width'], image_sentence['height'])
                    combined_text.append({
                        'text': image_sentence['text'],
                        'left': pdf_coords[0],
                        'top': pdf_coords[1],
                        'width': pdf_coords[2],
                        'height': pdf_coords[3]
                    })

        combined_text = sorted(combined_text, key=lambda x: (x['top'], x['left']))
        self.create_final_text(combined_text, self.page.width)        

    def combine_text_sentences_data(self):
        combined_text = []
        used_image_sentences = set()

        # Primero, procesamos las oraciones del PDF
        for pdf_sentence in self.pdf_sentences:
            sentence_added = False
            for data_key, data_value in self.data.items():
                image_sentences = data_value['image_sentences']
                image_info = data_value['image_info']
                
                coordinator = PDFOCRCoordinator(
                    pdf_width=self.page.width,
                    pdf_height=self.page.height,
                    image_width=image_info['width'],
                    image_height=image_info['height'],
                    image_x0=image_info['x0'],
                    image_y0=image_info['y0'],
                    ocr_width=image_info['image_width'],
                    ocr_height=image_info['image_height'],
                    pdf_origin='top_left',
                    ocr_origin='top_left'
                )

                for i, image_sentence in enumerate(image_sentences):
                    if coordinator.compare_sentence_locations(
                        pdf_sentence, 
                        image_sentence,
                        threshold=50
                    ):
                        pdf_coords = coordinator.ocr_to_pdf(image_sentence['left'], image_sentence['top'])
                        combined_text.append({
                            'text': image_sentence['text'] + " " + pdf_sentence['text'],
                            'left': pdf_coords[0],
                            'top': pdf_coords[1],
                            'width': max(image_sentence['width'], pdf_sentence['width']),
                            'height': max(image_sentence['height'], pdf_sentence['height'])
                        })
                        used_image_sentences.add((data_key, i))
                        sentence_added = True
                        break
                if sentence_added:
                    break
            if not sentence_added:
                combined_text.append({
                    'text': pdf_sentence['text'],
                    'left': pdf_sentence['x0'],
                    'top': pdf_sentence['top'],
                    'width': pdf_sentence['width'],
                    'height': pdf_sentence['height']
                })

        combined_text = sorted(combined_text, key=lambda x: (x['top'], x['left']))
        self.create_final_application_text(combined_text, self.page.width)

    def create_final_text(self, sorted_text, page_width, line_height_threshold=14, right_margin_threshold=16):
        self.Text = ""
        current_line_top = None
        current_line_right = 0

        for sentence in sorted_text:
            if current_line_top is None:
                # Primera línea
                self.Text += sentence['text']
                current_line_top = sentence['top']
                current_line_right = sentence['left'] + sentence['width']
            elif abs(sentence['top'] - current_line_top) > line_height_threshold or current_line_right > sentence['left']:
                # Nueva línea detectada
                self.Text += "\n" + sentence['text']
                current_line_top = sentence['top']
                current_line_right = sentence['left'] + sentence['width']
            else:
                # Misma línea
                if sentence['left'] > current_line_right:
                    # Añadir espacios si hay una gran brecha horizontal
                    spaces = "\t" * int((sentence['left'] - current_line_right) / 5)  # Ajusta el divisor según sea necesario
                    self.Text += spaces + sentence['text']
                else:
                    self.Text += "\t" + sentence['text']
                current_line_right = max(current_line_right, sentence['left'] + sentence['width'])

            # Verificar si estamos cerca del margen derecho
            if page_width - current_line_right <= right_margin_threshold:
                self.Text += "\n"
                current_line_top = None
                current_line_right = 0
        pass

        # Eliminar espacios en blanco extra al principio y al final
        self.Text = self.Text.strip()

    def create_final_application_text(self, sorted_text, page_width, line_height_threshold=14, right_margin_threshold=20):
        self.Text = ""
        current_line_top = None
        current_line_right = 0
        current_line_left = 0
        current_line_texts = []

        def finalize_line():
            nonlocal current_line_texts, current_line_top, current_line_right, current_line_left
            if current_line_texts:
                # Ordenar los textos en la línea actual por su posición horizontal (left)
                current_line_texts.sort(key=lambda x: x['left'])
                # Combinar los textos en una sola línea
                line_text = ""
                for text_data in current_line_texts:
                    if line_text:
                        spaces = "\t"
                        line_text += spaces + text_data['text']
                    else:
                        line_text = text_data['text']
                    current_line_right = text_data['left'] + text_data['width']
                self.Text += line_text + "\n"
                current_line_texts = []

        for sentence in sorted_text:
            if current_line_top is None:
                # Primera línea
                current_line_texts.append(sentence)
                current_line_top = sentence['top']
                current_line_right = sentence['left'] + sentence['width']
                current_line_left = sentence['left']
            elif abs(sentence['top'] - current_line_top) > line_height_threshold:
                # Nueva línea detectada
                finalize_line()
                current_line_texts.append(sentence)
                current_line_top = sentence['top']
                current_line_right = sentence['left'] + sentence['width']
                current_line_left = sentence['left']
            else:
                # Misma línea
                current_line_texts.append(sentence)
                current_line_right = max(current_line_right, sentence['left'] + sentence['width'])

            # Verificar si estamos cerca del margen derecho
            if page_width - current_line_right <= right_margin_threshold:
                finalize_line()
                current_line_top = None
                current_line_right = 0
                current_line_left = 0

        # Finalizar la última línea
        finalize_line()

        # Eliminar espacios en blanco extra al principio y al final
        self.Text = self.Text.strip()

class PDFOCRCoordinator:
    def __init__(self, pdf_width, pdf_height, image_width, image_height, 
                 image_x0, image_y0, ocr_width, ocr_height,
                 pdf_origin='top_left', ocr_origin='top_left'):
        self.pdf_width = pdf_width
        self.pdf_height = pdf_height
        self.image_width = image_width
        self.image_height = image_height
        self.image_x0 = image_x0
        self.image_y0 = image_y0
        self.ocr_width = ocr_width
        self.ocr_height = ocr_height
        self.pdf_origin = pdf_origin
        self.ocr_origin = ocr_origin
        
        self.scale_x = ocr_width / image_width
        self.scale_y = ocr_height / image_height

    def pdf_to_ocr_coords(self, x, y):
        # Ajustar coordenadas relativas a la posición de la imagen en el PDF
        x_rel = x - self.image_x0
        y_rel = y - self.image_y0

        # Escalar a coordenadas OCR
        x_scaled = x_rel * self.scale_x
        y_scaled = y_rel * self.scale_y

        return x_scaled, y_scaled

    def ocr_to_pdf(self, x, y, width=None, height=None):
        # Ajustar coordenadas relativas a la posición de la imagen en el PDF
        x_rel = x / self.scale_x
        y_rel = y / self.scale_y

        # Escalar a coordenadas PDF
        x_scaled = x_rel + self.image_x0
        y_scaled = y_rel + self.image_y0

        # Si se proporcionan ancho y alto, convertirlos también
        if width is not None and height is not None:
            width_scaled = width / self.scale_x
            height_scaled = height / self.scale_y
            return x_scaled, y_scaled, width_scaled, height_scaled
        
        return x_scaled, y_scaled

    def compare_text_locations(self, pdf_text, ocr_text, threshold=50):
        pdf_x, pdf_y = pdf_text['x0'], pdf_text['top']
        ocr_x, ocr_y = ocr_text[1], ocr_text[2]

        # Verificar si el texto del PDF está dentro de los límites de la imagen
        if (self.image_x0 <= pdf_x <= self.image_x0 + self.image_width and
            self.image_y0 <= pdf_y <= self.image_y0 + self.image_height):
            
            pdf_ocr_x, pdf_ocr_y = self.pdf_to_ocr_coords(pdf_x, pdf_y)
            
            distance = ((pdf_ocr_x - ocr_x)**2 + (pdf_ocr_y - ocr_y)**2)**0.5
            
            return distance < threshold
        
        return False

    def compare_sentence_locations(self, pdf_sentence, ocr_sentence, threshold=50):
        # Asumimos que pdf_sentence es un diccionario con 'text', 'x0', y 'top'
        if isinstance(pdf_sentence, dict) and 'text' in pdf_sentence and 'x0' in pdf_sentence and 'top' in pdf_sentence:
            pdf_text = pdf_sentence['text']
            pdf_x0 = pdf_sentence['x0']
            pdf_top = pdf_sentence['top']
        else:
            # Si no es un diccionario con la estructura esperada, no podemos comparar
            return False

        # Asumimos que ocr_sentence es un diccionario con 'text', 'left', y 'top'
        if isinstance(ocr_sentence, dict) and 'text' in ocr_sentence and 'left' in ocr_sentence and 'top' in ocr_sentence:
            ocr_text = ocr_sentence['text']
            ocr_left = ocr_sentence['left']
            ocr_top = ocr_sentence['top']
        else:
            # Si no es un diccionario con la estructura esperada, no podemos comparar
            return False

        if pdf_text and ocr_text:
            # Comparamos la posición del pdf_sentence con la posición del ocr_sentence
            return self.compare_text_locations(
                {'x0': pdf_x0, 'top': pdf_top},
                (ocr_text, ocr_left, ocr_top),
                threshold
            )
        
        return False



def group_text(text_data, left_data, top_data, width_data, height_data, threshold=15):
    sentences = []
    current_sentence = []
    last_right = None
    last_bottom = None
    sentence_left = None
    sentence_top = None

    for text, left, top, width, height in zip(text_data, left_data, top_data, width_data, height_data):
        if text == '':
            continue

        right = left + width
        bottom = top + height

        if current_sentence:
            horizontal_gap = left - last_right if last_right is not None else 0
            vertical_gap = abs(top - last_top) if last_top is not None else 0
            
            new_line = vertical_gap > (height + last_height) / 2
            too_far = horizontal_gap > max(threshold, width / 2, last_width / 2)

            if new_line or too_far:
                sentences.append({
                    'text': ' '.join(current_sentence),
                    'left': sentence_left,
                    'top': sentence_top,
                    'width': last_right - sentence_left,
                    'height': height
                })
                current_sentence = []
                sentence_left = None
                sentence_top = None

        if not current_sentence:
            sentence_left = left
            sentence_top = top

        current_sentence.append(text)
        last_right = right
        last_top = top
        last_width = width
        last_height = height

    if current_sentence:
        sentences.append({
            'text': ' '.join(current_sentence),
            'left': sentence_left,
            'top': sentence_top,
            'width': last_right - sentence_left,
            'height': height
        })

    return sentences

def group_words(words, threshold=15):
    sentences = []
    current_sentence = []
    last_right = None
    last_bottom = None

    for word in words:
        if current_sentence and (abs(word['x0'] - last_right) > threshold or abs(word['top'] - last_bottom) > threshold):
            sentences.append({
                'text': ' '.join([w['text'] for w in current_sentence]),
                'x0': current_sentence[0]['x0'],
                'top': current_sentence[0]['top'],
                'width': current_sentence[-1]['x1'] - current_sentence[0]['x0'],
                'height': current_sentence[-1]['bottom'] - current_sentence[0]['top']
            })
            current_sentence = []

        current_sentence.append(word)
        last_right = word['x1']
        last_bottom = word['bottom']

    if current_sentence:
        sentences.append({
            'text': ' '.join([w['text'] for w in current_sentence]),
            'x0': current_sentence[0]['x0'],
            'top': current_sentence[0]['top'],
            'width': current_sentence[-1]['x1'] - current_sentence[0]['x0'],
            'height': current_sentence[-1]['bottom'] - current_sentence[0]['top']
        })

    return sentences

def create_pdf_object(filename):
    # Lista de palabras clave para aplicaciones
    application_keywords = ['application', 'aplicacion', 'app', 'form', 'formulario']
    
    # Lista de palabras clave para estados de cuenta
    bank_statement_keywords = [
        'bank', 'statement', 'account', 'cuenta', 'balance', 'summary', 
        'january', 'jan', 'february', 'feb', 'march', 'mar', 'april', 'apr', 
        'may', 'june', 'jun', 'july', 'jul', 'august', 'aug', 
        'september', 'sep', 'october', 'oct', 'november', 'nov', 'december', 'dec'
    ]

    # Comprobar si el nombre del archivo contiene palabras clave de aplicación
    if any(keyword in filename.lower() for keyword in application_keywords):
        return OBJ_PDF_Aplicacion(filename)
    
    # Comprobar si el nombre del archivo contiene palabras clave de estado de cuenta
    elif any(keyword in filename.lower() for keyword in bank_statement_keywords):
        return OBJ_PDF_HistorialBancario(filename)
    
    # Si no se puede determinar por el nombre del archivo, analizar el contenido
    else:
        with pdfplumber.open(filename) as pdf:
                first_page_text = pdf.pages[0].extract_text().lower()
                
                # Lista de palabras clave para aplicaciones
                application_keywords = ['application', 'aplicacion', 'app', 'form', 'formulario']
                
                # Lista de palabras clave para estados de cuenta
                bank_statement_keywords = [
                    'bank', 'statement', 'account', 'cuenta', 'balance', 'summary', 
                    'january', 'jan', 'february', 'feb', 'march', 'mar', 'april', 'apr', 
                    'may', 'june', 'jun', 'july', 'jul', 'august', 'aug', 
                    'september', 'sep', 'october', 'oct', 'november', 'nov', 'december', 'dec'
                ]
                
                if any(keyword in first_page_text for keyword in application_keywords):
                    return OBJ_PDF_Aplicacion(filename)
                elif any(keyword in first_page_text for keyword in bank_statement_keywords):
                    return OBJ_PDF_HistorialBancario(filename)
                else:
                    raise ValueError("Tipo de PDF no reconocido")

def scan_files(directory):
    results = []

    for filename in os.listdir(directory):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(directory, filename)
            pdf_obj = OBJ_PDF(pdf_path)
            result = {
                "filename": filename,
                "type": pdf_obj.Type,
                "personal_info": pdf_obj.personal_json,
                "business_info": pdf_obj.business_json,
                "tables": pdf_obj.tables,
                "date": pdf_obj.Date
            }
            results.append(result)
    return results

def main(directory):
    try:
        results = scan_files(directory)
        for result in results:
            print(f"Archivo: {result['filename']}")
            print(f"Tipo: {result['type']}")
            print("Información Personal:")
            for key, value in result['personal_info'].items():
                print(f"  {key}: {value}")
            print("Información de Negocios:")
            for key, value in result['business_info'].items():
                print(f"  {key}: {value}")
            print(f"Fecha: {result['date']}")
            print(f"Tablas: {result['tables']}")
            print("\n")
    except Exception as e:
        print(f"Error: {str(e)}")

# Ejemplo de uso
# if __name__ == '__main__':
#     main(r"C:\ruta\del\directorio\con\pdfs")
