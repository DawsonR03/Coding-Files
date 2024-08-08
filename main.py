from read_data import read_text, read_excel
from plotting import plot_data

def main():
    file_path = r"C:\Users\droach\Downloads\WU-402 processed for test01.txt"  # Path to your data file (using raw string to handle backslashes)
    file_type = "text"  # File type
    columns = "Max,Min,Delta".split(",")  # Column names to analyze

    # If using a text file, specify the delimiter (e.g., ",", "\t", "|")
    delimiter = None
    if file_type == "text":
        delimiter = input("Enter the delimiter used in the text file (e.g., ',', '\\t', '|'): ")

    if file_type == "excel":
        data = read_excel(file_path)  # Read data from Excel file
    elif file_type == "text":
        data = read_text(file_path, delimiter=delimiter)  # Read data from text file with specified delimiter
    else:
        print("Invalid file type")
        return

    if data is not None:
        # Verify the columns exist in the data
        missing_columns = [col for col in columns if col.strip() not in data.columns]
        if missing_columns:
            print(f"Error: Columns {', '.join(missing_columns)} not found in data.")
            return

        data.index.name = "Row Number"  # Set index name for the x-axis

        # Specify the save path for the plot image if needed
        save_path = input("Enter the path to save the plot image (leave blank to display the plot): ")
        if save_path.strip() == "":
            save_path = None

        plot_data(data, [col.strip() for col in columns], save_path)
    else:
        print("Error: Data not available or columns not found.")

if __name__ == "__main__":
    main()
