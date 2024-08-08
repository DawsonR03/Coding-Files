from read_data1 import read_text, read_excel
from process_data1 import process_data

def main():
    file_path = r"C:\Users\droach\Downloads\WU-402 processed for test01.xlsx"  # Hard-coded file path
    file_type = "excel"  # Hard-coded file type
    max_col = "Max"  # Hard-coded column names
    min_col = "Min"
    cycle_col = "Cycles"
    output_path = r"C:\Users\droach\Downloads\MaxMinVsCycle1.txt"  # Path to save the output file

    if file_type == "excel":
        data = read_excel(file_path)  # Read data from Excel file
    elif file_type == "text":
        delimiter = "\t"  # Assuming the text file uses tab as the delimiter
        data = read_text(file_path, delimiter=delimiter)  # Read data from text file with specified delimiter
    else:
        print("Invalid file type")
        return

    if data is not None:
        # Verify the columns exist in the data
        missing_columns = [col for col in [max_col, min_col, cycle_col] if col.strip() not in data.columns]
        if missing_columns:
            print(f"Error: Columns {', '.join(missing_columns)} not found in data.")
            return

        process_data(data, max_col, min_col, cycle_col, output_path)
    else:
        print("Error: Data not available or columns not found.")

if __name__ == "__main__":
    main()
