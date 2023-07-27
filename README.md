## Stream Network from DEM tool
This tool uses a sequence of tools in ArcMap 10.8 to give a network of streams based on a given threshold input and a given digital elevation model (DEM).

The flow of execution of different tools inside this tool is as follows:
1. Fill
2. Flow direction
3. Flow accumulation
4. Thresholding
5. Stream order mapping
6. Stream to feature

You can use this tool to get your desired stream network feature class by simply providing the DEM and the threshold value for flow accumulation.
