# Low-impact land use pathways to deep decarbonization of electricity

This repository contains the Python scripts used to perform project site selection and strategic environmental assessment as well the results from the analysis used to produce the figures in the published paper:

> Wu, G.C., Leslie, E., Sawyerr, O., Cameron, D.R., Brand, E., Cohen, B., Allen, D., Ochoa, M., Olson, A., 2020. Low-impact land use pathways to deep decarbonization of electricity. Environ. Res. Lett. https://doi.org/10.1088/1748-9326/ab87d1

The following are the steps in the analysis and the scripts and/or tools to implement them:

1. Conduct site suitability analysis with only non-environmental inputs using Script Tool B, Stage 1 of the [MapRE GIS zoning tool](https://mapre.lbl.gov/gis-tools/) (Requires ArcGIS to run). This step uses raster-based geo-processing.

2. createSupplyCurve (requires arcpy): a) creates renewble resource areas using using vector environmental inputs and results from step 1 above, b) creates Candidate Project Areas (CPAs) using output of 2a, c) produces the supply curves in the form of csvs for input into the capacity expansion model, RESOLVE. 

3. Run RESOLVE, a capacity expansion model. You can download it here for [2017](https://www.cpuc.ca.gov/irp/prelimresults2017/) and for [2019](https://www.cpuc.ca.gov/General.aspx?id=6442462824). If the links are broken, google "CPUC RESOLVE model package" 

4. preprocessExistingWindData.py (requires arcpy): combines Ventyx and USWTDB wind location spatial data and produces a single existing wind farms dataset

5. spatialDisagg_funct_coLoc.py (requires arcpy): Takes results of steps 2 and 3 to create 
