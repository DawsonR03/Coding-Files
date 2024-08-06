import matplotlib.pyplot as plt

def plot_data(data, columns, save_path=None):
    plt.figure(figsize=(10, 5))
    for column in columns:
        plt.plot(data[column], label=column)
    plt.title(f"Plot of {', '.join(columns)}")
    plt.xlabel("Index")
    plt.ylabel("Values")
    plt.legend()
    
    if save_path:  # If a save path is provided, save the plot as an image
        plt.savefig(save_path)
        print(f"Plot saved as {save_path}")
    else:  # Otherwise, display the plot
        plt.show()
