def calculate_max(data, column):
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data.")
    return data[column].max()  # Calculate maximum value

def calculate_min(data, column):
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data.")
    return data[column].min()  # Calculate minimum value

def calculate_average(data, column):
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data.")
    return data[column].mean()  # Calculate average value

def calculate_delta(data, column):
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data.")
    return data[column].max() - data[column].min()  # Calculate delta value

def calculate_endpoints(data, column):
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data.")
    return data[column].iloc[0], data[column].iloc[-1]  # Get the first and last values (endpoints)
