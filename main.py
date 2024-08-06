from read_data import read_excel, read_text
from calculations import calculate_max, calculate_min, calculate_average, calculate_delta, calculate_endpoints
from plotting import plot_data

def main():
    file_path = input("Enter the file path: ")  # Path to your data file
    file_type = input("Enter the file type (excel/text): ")  # File type
    columns = input("Enter the column names to analyze (comma separated): ").split(",")  # Column names to analyze

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
        try:
            for column in columns:
                column = column.strip()
                print(f"Maximum value in {column}: {calculate_max(data, column)}")
                print(f"Minimum value in {column}: {calculate_min(data, column)}")
                print(f"Average value in {column}: {calculate_average(data, column)}")
                print(f"Delta value in {column}: {calculate_delta(data, column)}")
                first, last = calculate_endpoints(data, column)
                print(f"First value in {column}: {first}")
                print(f"Last value in {column}: {last}")

            # Specify the save path for the plot image if needed
            save_path = input("Enter the path to save the plot image (leave blank to display the plot): ")
            if save_path.strip() == "":
                save_path = None

            plot_data(data, columns, save_path)
        except ValueError as e:
            print(e)  # Print error if column is not found
    else:
        print("Error: Data not available or column not found.")

if __name__ == "__main__":
    main()
