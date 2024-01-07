import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from shapely.geometry import LineString


# Create a GeoDataFrame with a LineString geometry
gdf = gpd.GeoDataFrame({'geometry': [LineString([(0, 0), (1, 1)])]})

# Create a Point object
point = Point(0.5, 0.5)

# Create a GeoDataFrame with a Point geometry
point_gdf = gpd.GeoDataFrame({'geometry': [point]})

# Create a plot
fig, ax = plt.subplots()

# Plot the line
gdf.plot(ax=ax, color='blue')

# Plot the point
point_gdf.plot(ax=ax, color='red', markersize=50)

# Show the plot
plt.show()