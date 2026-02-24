import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

merged_df = pd.read_csv("C:\\Users\\tmnfn\\OneDrive\\Desktop\\python shit\\hdac\\AvgMME_v_ODD.csv")

# 1. Set the visual style
sns.set_theme(style="whitegrid")

# 2. Create the scatter plot
# Replace 'column_x' and 'column_y' with your actual column names
# Based on your previous error, maybe: x='county_code', y='Average MME'
plt.figure(figsize=(10, 6))
sns.scatterplot(data=merged_df, x='Deaths', y='Average MME', alpha=0.6)

# 3. Add labels and title
plt.title('Relationship between County Code and Average MME', fontsize=15)
plt.xlabel('Deaths')
plt.ylabel('Average MME')

# 4. Save the plot as an image
#  plt.savefig('my_scatter_plot.png', dpi=300)

# 5. Display the plot (if in a notebook)
plt.show()