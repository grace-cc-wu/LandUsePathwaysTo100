# Low-impact land use pathways to deep decarbonization of electricity

This repository contains the 1) links to interactively view some spatial results and download the data; 2) additional data tables as part of Supporting Information, 3) Python scripts used to perform project site selection and strategic environmental assessment as well the results from the analysis used to produce the figures in the open access published paper:

> Wu, G.C., Leslie, E., Sawyerr, O., Cameron, D.R., Brand, E., Cohen, B., Allen, D., Ochoa, M., Olson, A., 2020. Low-impact land use pathways to deep decarbonization of electricity. *Environ. Res. Lett.* https://doi.org/10.1088/1748-9326/ab87d1

## Spatial inputs and results
- View the wind and solar site suitability maps via an [**interactive webmap here**](https://tnc.maps.arcgis.com/apps/webappviewer/index.html?id=71b0605e44bf475ea55f6d369e668b2c).
- Download the Environmental Exclusion Categories (used as an input to create Fig. 1 in the paper) and wind, solar, and geothermal resource assessment spatial results (Candidate Project Areas; results shown in Fig. 1 in the paper) as a [**geodatabase**](https://tnc.app.box.com/s/yxyiu8fp6bsqckvmkayqxz5ib1xik7mh) or [**shapefile**](https://tnc.app.box.com/s/votra7kgbdme192z6qlrja7rg4csiflb).
- The selected project areas (SPAs) are not publicly available for download (results shown in Fig. 4 in the paper). These areas associated with a given scenario identify optimal locations for possible new energy generation based on the criteria selected by the authors. This study is based on scenario analysis and is not a siting study capable of making prescriptions or predictions of where which areas will or should be developed. However, many of these lands are privately-owned so the data could easily be mis-interpreted by users or landowners as identifying lands which are targeted or sanctioned for renewable energy development by the organizations involved in the study. These data are not publicly available due to the risk of mis-interpretation and the legal and political risks associated with a possible change in market value associated with this identification. However, the code used to generate these selected project areas (i.e., the site selection methods and process) is available in this repository (step 5 below). 

## Additional data and result tables
The following data tables in Excel workbook format are part of Supporting Information and are located in the [**AdditionalDataTables_forPaper**](/AdditionalDataTables_forPaper) subfolder in this repo. They contain the data that were used to create several of the figures in the main body of the text as well as those in the Supporting Information. 
- Additional data table S1 ([**EnvironmentalExclusionCategoryDataSources.xlsx**](/AdditionalDataTables_forPaper/EnvironmentalExclusionCategoryDataSources.xlsx)): Data sources and links for each Environmental Exclusion Category (Step 1). Extended versions of Tables S9–S12.
- Additional data table S2 ([**ResourceAssessment.xlsx**](/AdditionalDataTables_forPaper/)): Unadjusted resource potential results (capacity in megawatts, MW) from resource assessment for states used in RESOLVE (used to make SI Fig. S4)
- Additional data table S3 ([**ResourceAssessment.xlsx**](/AdditionalDataTables_forPaper/ResourceAssessment.xlsx)): Adjusted resource potential results (capacity in megawatts, MW) from resource assessment for states used in RESOLVE, supply curve inputs for RESOLVE modeling (used to make SI Fig. S3)
- Additional data table S4 ([**CapacityExpansionResults_RESOLVEportfolios.xlsx**](/AdditionalDataTables_forPaper/CapacityExpansionResults_RESOLVEportfolios.xlsx)): Total resource cost of each portfolio
- Additional data table S5 ([**CapacityExpansionResults_RESOLVEportfolios.xlsx**](/AdditionalDataTables_forPaper/CapacityExpansionResults_RESOLVEportfolios.xlsx)): Cost breakdown of each portfolio
- Additional data table S6 ([**CapacityExpansionResults_RESOLVEportfolios.xlsx**](/AdditionalDataTables_forPaper/CapacityExpansionResults_RESOLVEportfolios.xlsx)): Selected capacity (MW) by RESOLVE Zone by 2050 for all portfolios
- Additional data table S7 ([**CapacityExpansionResults_RESOLVEportfolios.xlsx**](/AdditionalDataTables_forPaper/CapacityExpansionResults_RESOLVEportfolios.xlsx)): Generation (MWh) of selected capacity (MW) by RESOLVE Zone by 2050 for all portfolios
- Additional data table S8 ([**CapacityExpansionResults_RESOLVEportfolios.xlsx**](/AdditionalDataTables_forPaper/CapacityExpansionResults_RESOLVEportfolios.xlsx)): Total (selected + existing and contracted) Capacity (MW) across all RESOLVE Zones by 2050 for all portfolios
- Additional data table S9 ([**CapacityExpansionResults_RESOLVEportfolios.xlsx**](/AdditionalDataTables_forPaper/CapacityExpansionResults_RESOLVEportfolios.xlsx)): Selected capacity (MW) across all RESOLVE Zone by 2050 for all portfolios
- Additional data table S10 ([**CapacityExpansionResults_RESOLVEportfolios.xlsx**](/AdditionalDataTables_forPaper/CapacityExpansionResults_RESOLVEportfolios.xlsx)): Generation (MWh) across all RESOLVE Zones by 2050 for all portfolios
- Additional data table S11 ([**StrategicEnvAssessment.xlsx**](/AdditionalDataTables_forPaper/StrategicEnvAssessment.xlsx)): Strategic Environmental Assessment results for generation aggregated across all RESOLVE Zones or regions
- Additional data table S12 ([**StrategicEnvAssessment.xlsx**](/AdditionalDataTables_forPaper/StrategicEnvAssessment.xlsx)): Strategic Environmental Assessment results for generation by RESOLVE Zone or region
- Additional data table S13 ([**StrategicEnvAssessment.xlsx**](/AdditionalDataTables_forPaper/StrategicEnvAssessment.xlsx)): Strategic Environmental Assessment results for transmission aggregated across all RESOLVE Zones or region
- Additional data table S14 ([**StrategicEnvAssessment.xlsx**](/AdditionalDataTables_forPaper/StrategicEnvAssessment.xlsx)): Strategic Environmental Assessment results for transmission by RESOLVE Zone or region

## Methodology and code:
The following are the steps in the main steps in the analysis and the scripts and/or tools to implement them:

1. Conduct site suitability analysis with only non-environmental inputs using Script Tool B, Stage 1 of the [**MapRE GIS zoning tool**](https://mapre.lbl.gov/gis-tools/) (Requires ArcGIS to run). This step uses raster-based geoprocessing.

2. [**createSupplyCurve.py**](/createSupplyCurve.py) (requires arcpy): a) creates renewble resource areas using using vector environmental inputs and results from step 1 above (using vector based processing to retain the native resolution of the environmental spatial datasets), b) creates Candidate Project Areas (CPAs) using output of 2a, c) produces the supply curves in the form of csvs for input into the capacity expansion model, RESOLVE. 

3. Run RESOLVE, a capacity expansion model, using the newly created supply curve as inputs. You can download the model here for [2017](https://www.cpuc.ca.gov/irp/prelimresults2017/) and for [2019](https://www.cpuc.ca.gov/General.aspx?id=6442462824). If the links are broken, google "CPUC RESOLVE model package". You will need a solver in order to run it. Also, keep in mind that the publicly available version of the model is only for the California Indepdent System Operator footprint for California, i.e., it does not cover the entire state, but a large percentage of the state (>80%).

4. [**preprocessExistingWindData.py**](/preprocessExistingWindData.py) (requires arcpy): combines Ventyx and USWTDB wind location spatial data and produces a single existing wind farms dataset. This dataset will be used to exclude suitable sites from being selected in the spatial disaggregation step.

5. [**spatialDisagg_funct_coLoc.py**](/spatialDisagg_funct_coLoc.py) (requires arcpy): Takes results of steps 2 and 3 to create Selected Project Areas for each RESOLVE portfolio/scenario (this was used to create Figure 4 in the paper). It assumes one could collocate solar and wind power plants within California. 

6. [**zonalStats_envImpact.ipynb**](/zonalStats_envImpact.ipynb): As part of the Strategic Environmental Assessment, this script calculates the impacts on metrics that are in raster data format (requiring zonal stats). E.g., average housing density, area of rangeslands impacted, area of each land cover type impacted for each scenario. 

7. [**envImpactAssess_calcArea_envCat.py**](envImpactAssess_calcArea_envCat.py) (requires arcpy): This script calculates the area impacted for each environmental metric for each scenario. 

7. (alternative) [**envImpactAssess_calcArea.ipynb**](/envImpactAssess_calcArea.ipynb): This script also calculates the area impacted for each environmental metric for each scenario, but does not use arcpy functions. It does, however, take much longer to run for large, complex vectors compared to envImpactAssess_calcArea_envCat.py.

8. [**envImpactAssess_plotting.ipynb**](/envImpactAssess_plotting.ipynb): Creates a large "master" csv that combines the outputs of all environmental impact assessment analyses (Steps 6 and 7 above). The csv output of this script was then used to create Fig. 5 in the paper. 
