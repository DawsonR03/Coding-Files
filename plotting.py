import matplotlib.pyplot as plt
import numpy as np

def plot_data(data, columns, save_path=None):
    plt.figure(figsize=(20, 10))  # Adjust figure size for better clarity
    
    for column in columns:
        sorted_data = np.sort(data[column])[::-1]  # Sort data in descending order for exceedance plotting
        plt.plot(np.arange(1, len(sorted_data) + 1), sorted_data, label=f"{column} Values")  # Plot each column against the sorted index
    
    plt.title("Exceedance Plot")
    plt.xlabel("Count/Row#")
    plt.ylabel("Max & Min")
    plt.legend()
    plt.grid(True)  # Add grid for better readability

    # Manually set x-axis ticks to increment by 50,000 for better readability
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(50000))
    plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(10000))
    plt.xticks(rotation=45)  # Rotate x-axis tick labels
    
    # Set y-axis ticks to increment by 2
    plt.gca().yaxis.set_major_locator(plt.MultipleLocator(2))
    
    if save_path:  # If a save path is provided, save the plot as an image
        plt.savefig(save_path)
        print(f"Plot saved as {save_path}")
    else:  # Otherwise, display the plot
        plt.show()
