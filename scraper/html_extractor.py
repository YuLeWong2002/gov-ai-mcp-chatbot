from bs4 import BeautifulSoup
import os

# --- Step 1: Define your input and output file paths ---
# The script will read from this HTML file.
input_html_path = 'jpj_page_source.html' 

# The script will create and write the extracted content to this text file.
output_txt_path = 'extracted_content.txt' 

try:
    # --- Step 2: Open and read the HTML file ---
    with open(input_html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # --- Step 3: Parse the HTML with BeautifulSoup ---
    soup = BeautifulSoup(html_content, 'html.parser')

    # --- Step 4: Extract all the text content ---
    # get_text() with separator="\n" and strip=True ensures clean, readable output.
    extracted_text = soup.get_text(separator="\n", strip=True)

    # --- Step 5: Write the extracted text to the output .txt file ---
    # Using 'w' mode will create the file if it doesn't exist,
    # or overwrite it if it already exists.
    with open(output_txt_path, 'w', encoding='utf-8') as output_file:
        output_file.write(extracted_text)

    # --- Step 6: Print a success message to the console ---
    print(f"Success! Content has been extracted and saved to: {os.path.abspath(output_txt_path)}")

except FileNotFoundError:
    print(f"Error: The input file was not found at the path: {os.path.abspath(input_html_path)}")
    print("Please make sure the input_html_path variable is correct and the file exists.")
except Exception as e:
    print(f"An error occurred: {e}")