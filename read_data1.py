import pandas as pd

def read_text(file_path, delimiter="\t"):  # Default delimiter is tab
    try:
        data = pd.read_csv(file_path, delimiter=delimiter)
        return data
    except Exception as e:
        print(f"Error reading text file: {e}")
        return None

def read_excel(file_path):
    try:
        data = pd.read_excel(file_path)
        return data
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None
