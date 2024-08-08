import pandas as pd  # Import pandas

def process_data(data, max_col, min_col, cycle_col, output_path):
    output_lines = []

    max_values = []
    min_values = []

    for _, row in data.iterrows():
        max_val = row[max_col]
        min_val = row[min_col]
        cycles = int(row[cycle_col])
        
        max_values.extend([max_val] * cycles)
        min_values.extend([min_val] * cycles)

        for _ in range(cycles):
            output_lines.append(f"{max_val}\n{min_val}\n")

    max_values_series = pd.Series(max_values)
    min_values_series = pd.Series(min_values)

    highest_max = max_values_series.max()
    lowest_max = max_values_series.min()
    highest_min = min_values_series.max()
    lowest_min = min_values_series.min()
    total_endpoints = len(max_values) + len(min_values)

    summary_lines = [
        f"Endpoints in Output: {total_endpoints}\n",
        f"Highest Value in Max: {highest_max}\n",
        f"Lowest Value in Max: {lowest_max}\n",
        f"Highest Value in Min: {highest_min}\n",
        f"Lowest Value in Min: {lowest_min}\n"
    ]

    try:
        with open(output_path, 'w') as f:
            f.writelines(output_lines)
            f.writelines(summary_lines)
        print(f"Output successfully saved to {output_path}")
    except Exception as e:
        print(f"Error writing to file: {e}")
