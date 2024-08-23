import pdfplumber
import argparse
import pandas as pd
from openai import OpenAI

def extract_text_from_pdf(filename):
    all_text = []
    all_tables = []

    with pdfplumber.open(filename) as pdf:
        # iterate over each page
        for page in pdf.pages:
            # extract text
            text = page.extract_text()
            all_text.append(text)
            # table = page.extract_tables()
            # all_tables.extend(table)

    return all_text


def extract_tables_from_pdf(filename): # need a better table extractor 
    all_tables = [] 
    with pdfplumber.open(filename) as pdf: 
        for page in pdf.pages: 
            tables = page.extract_tables()
            all_tables.extend(tables)
    return all_tables

def save_tables_to_excel(all_tables, output_filename): 
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer: 
        for i, table in enumerate(all_tables):
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                df.to_excel(writer, sheet_name=f'Table_{i+1}', index=False)


def call_chatgpt(pdf_text, user_prompt): 
    client = OpenAI()
    content = f"{pdf_text}\n\n{user_prompt}"
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
            "role": "user", 
            "content": content,
            }
        ]
    )
    print(response.choices[0].message.content.strip())
    

def process_text_with_chatgpt(all_text): 
    combined_text = "\n".join(all_text)

    while True: 
        user_prompt = input("Enter your prompt (or type 'quit' to exit): ")
        if user_prompt.lower() == 'quit': 
            break 

        response = call_chatgpt(combined_text, user_prompt) 
        print("Response: ", response)


def main():
    parser = argparse.ArgumentParser(
        prog="pdf_extractor", 
        description="This program is used to extract relevant information from a PDF"        
    )

    parser.add_argument("filename")
    parser.add_argument("-t", "-text", action="store_true") # extracts text from PDF
    parser.add_argument("-p", "-photo", action="store_true") # extracts photos from PDF 
    parser.add_argument("-tb", "-table", action="store_true") # extracts tables from PDF 
    parser.add_argument("-o", "--output", type=str, help="Output filename for extracted tables")

    args = parser.parse_args() 
    filename = args.filename
    text = args.t
    table = args.tb
    photo = args.p
    output_filename = args.output

    if text:
        all_text = extract_text_from_pdf(filename)
        process_text_with_chatgpt(all_text)
    
    if table: 
        all_tables = extract_tables_from_pdf(filename)
        if output_filename:
            save_tables_to_excel(all_tables, output_filename)
        else:
            print("Please provide an output filename using the -o option to save the tables to an Excel file.")

    if photo:
        pass 

if __name__ == "__main__":
    main()