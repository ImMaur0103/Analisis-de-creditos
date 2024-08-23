import os
import sys

import pdfplumber
import re
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)





import re

def is_table_header(line):
    return ("Date".lower() in line.lower() and "Description".lower() in line.lower() and "Amount".lower() in line.lower() or
            "Date".lower() in line.lower() and " Balance ($)".lower() in line.lower())

def return_table_header(line):
    if "Date".lower() in line.lower() and "Description".lower() in line.lower() and "Amount".lower() in line.lower():
        return ["Date", "Description", "Amount"]
    elif "Date".lower() in line.lower() and "Balance ($)".lower() in line.lower():
        return ["Date", "Balance ($)"]

def is_table_title(line):
    titles = ["Deposits and other credits", "Withdrawals and other debits", "Daily ledger balances"]
    return line in titles

def validate_row_with_header(header_columns, row):
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
        row_columns = repair_row(header_columns, row_columns)
    elif len(row_columns) < len(header_columns):
        if not (date_valid and amount_valid):
            return None
    
    for i, column in enumerate(header_columns):
        if column.lower() == "date":
            date_valid = any(re.match(pattern, row_columns[i]) for pattern in date_patterns)
        elif column.lower() == "amount":
            amount_valid = re.match(amount_pattern, row_columns[i]) is not None

    return row_columns

def repair_row(header_columns, row_columns):
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

def parse_pdf_content(pdf_content):
    lines = pdf_content.split('\n')
    tables = []
    current_table = None
    
    for line in lines:
        if is_table_title(line) and current_table is None:
            if current_table is not None:
                tables.append(current_table)
            current_table = {
                "title": line,
                "header": "",
                "rows": [],
                "invalid_rows": []
            }
        elif is_table_header(line):
            if current_table is not None:
                current_table["header"] = return_table_header(line)
        elif current_table is not None and current_table["header"]:
            rows = validate_row_with_header(current_table["header"], line)
            if rows:
                current_table["rows"].append(rows)
            elif 'subtotal' in line.lower() or 'total' in line.lower():
                tables.append(current_table)
                current_table = None

    
    if current_table is not None:
        tables.append(current_table)
    
    return tables



def extract_transactions(pdf_path):
    transactions = []
    account_info = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if not text:
                logger.warning(f"No text extracted from page {page_num} of {pdf_path}")
                continue
            
            lines = text.split('\n')
            
            # Extract account information
            account_info.update(extract_account_info(lines))
            
            # Extract transactions
            page_transactions = extract_page_transactions(lines)
            transactions.extend(page_transactions)
    
    return {"account_info": account_info, "transactions": transactions}

def extract_account_info(lines):
    info = {}
    account_number_pattern = r'Account number:?\s*([A-Z0-9-]+)' # account number INFO
    balance_pattern = r'(Beginning|Ending) balance.*?(\$?[\d,]+\.\d{2})' # account balance INFO
    
    for line in lines:
        if 'Account number' in line:
            match = re.search(account_number_pattern, line)
            if match:
                info['account_number'] = match.group(1)
        
        balance_match = re.search(balance_pattern, line)
        if balance_match:
            balance_type, amount = balance_match.groups()
            info[f'{balance_type.lower()}_balance'] = amount
    
    return info

def extract_page_transactions(lines):
    transactions = []
    date_patterns = [
        r'\d{2}/\d{2}/\d{4}',  # mm/dd/yyyy
        r'\d{2}/\d{2}/\d{2}',  # mm/dd/yy
        r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}'  # dd MMM yyyy
    ]
    amount_pattern = r'-?[\$]?[\d,]+\.\d{1,4}'
    
    for line in lines:
        transaction = {}
        
        # Try to extract date
        for pattern in date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                transaction['date'] = date_match.group()
                line = line.replace(date_match.group(), '', 1)
                break
        
        # Try to extract amount
        amount_matches = re.findall(amount_pattern, line)
        if amount_matches:
            transaction['amount'] = amount_matches[-1]  # Take the last match as amount
            line = line.replace(transaction['amount'], '', 1)
        
        # The rest is the description
        transaction['description'] = line.strip()
        
        if transaction:
            transactions.append(transaction)
    
    return transactions

def process_pdf(pdf_path):
    try:
        result = extract_transactions(pdf_path)
        logger.info(f"Successfully processed {pdf_path}")
        logger.info(f"Account Info: {result['account_info']}")
        logger.info(f"Extracted {len(result['transactions'])} transactions")
        return result
    except Exception as e:
        logger.error(f"Error processing {pdf_path}: {str(e)}")
        return None

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'Backend\\Modulos'))
from PDF.PDF import create_pdf_object

Backdir = 'D:\\Downloads\\G2L (Ultimate)\\Bank Statements (Examples)'
Bancos = os.listdir(Backdir)

archivos = {}
Info = {}
for bank in Bancos:
    archivos[bank] = os.listdir(os.path.join(Backdir, bank))


for bank in Bancos:
    Info[bank] = []
    os.system('cls' if os.name == 'nt' else 'clear')
    for archivo in archivos[bank]:
        print(os.path.join(Backdir, bank, archivo))
        pdf_dir = os.path.join(Backdir, bank, archivo)
        transactions = extract_transactions(pdf_dir)
        
        pdf = create_pdf_object(pdf_dir)
        Info[bank].append(pdf)
        trans = parse_pdf_content(Info[bank][0].PDF_content)
        print("")

os.system('cls' if os.name == 'nt' else 'clear')
for Backinfo in Info:
    for PDFs in Info[Backinfo]:
        print(f'Group: {Backinfo}\nPDF name: {PDFs.fileublication}\nPDF Content: {PDFs.PDF_content}')


pdf = OBJ_PDF('D:\\Downloads\\G2L (Ultimate)\\Bank Statements (Examples)\\FAB Trading Inc\\41a5-Application.pdf', 'Aplicacion')
if pdf.Type == "Estado de Cuenta":
    pdf.set_account_statement_date("2024-05-31")  # Ejemplo de fecha

print(f"Tipo de PDF: {pdf.Type}")
if pdf.Date:
    print(f"Fecha del estado de cuenta: {pdf.Date}")

for page in pdf.Pages:
    print(f"Texto de la página {page.page_num}:")
    print(page.Text)
    print("---")

print("Información JSON:")
print(pdf.info_json)

print("Tablas extraídas:")
for table in pdf.tables:
    print(table)
    print("---")