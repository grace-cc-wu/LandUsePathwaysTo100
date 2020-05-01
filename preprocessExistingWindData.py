# -*- coding: utf-8 -*-
"""
Created on Sat Nov 10 13:57:35 2018

@author: Grace

Purpose: This script preprocesses Ventyx and USGS data and merges the two datasets in a way that
addresses redundancy. It favors USGS turbine data over Ventyx data as the USGS dataset is more recent
and visual inspection using high resolution imagery shows that it is more accurate. 
"""

##--------------------------------Preamble ----------------------------------
import arcpy
import numpy as np
import numpy.lib.recfunctions
import scipy.stats as stats
import math
import time
import os
import csv
import re
import pandas
import collections
start_time = time.time()
print(start_time)
# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
from arcpy import env
from arcpy.sa import *
import arcpy.cartography as CA
arcpy.env.overwriteOutput = True


##---------------------Workspace------------------------

mainDir = "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\"

### Set workspace for saving outputs: create file geodatabase (fgdb) for run session outputs
suitableSitesGDB = os.path.join(mainDir,"siteSuitabilityOutputs\\070618_resourceAssessment.gdb\\") #^^
eInfrastGDB = os.path.join(mainDir,"dataCollection\\existingEnergyInfrastructure\\energyInfrastructure.gdb\\")
intermediateGDB = os.path.join(mainDir, "dataCollection\\existingEnergyInfrastructure\\ventyxUSGS_intermediateFiles.gdb\\")
spDisaggGDB = os.path.join(mainDir,"spatialDisaggregation\\selectedSites.gdb\\") #^^
spDisaggFolder = os.path.join(mainDir,"spatialDisaggregation\\") #^^
genericInputsGDB = os.path.join(mainDir, "dataCollection\siteSuitabilityInputs_nonEnv.gdb\\")
spDisaggGDB_scratch = os.path.join(mainDir,"spatialDisaggregation\\scratch.gdb\\") #^^

env.scratchWorkspace = spDisaggGDB  # sets scratchworkspace to your output workspace 
env.workspace = spDisaggGDB # sets environment workspace to your output workspace

# set input paths:
#stateBounds = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\SRTM_W_250m_proj_cl") ##^^ enter the path to your STATE boundary shapefile
templateRaster = os.path.join(mainDir, "dataCollection\\siteSuitabilityInputs_nonEnv.gdb\\SRTM_W_250m_proj_cl") ##^^ enter path to DEM data

# set environments for raster analyses
arcpy.env.snapRaster = templateRaster
arcpy.env.extent = templateRaster
arcpy.env.mask = templateRaster
arcpy.env.cellSize = templateRaster


##-----------------Load files --------------------------
ventyx = os.path.join(eInfrastGDB, "Ventyx_wind_farms_polygon_existing")
existingWind_MWfield_ventyx = "OP_CAP_MW"
usgs = os.path.join(eInfrastGDB, "uswtdb_v1_1_20180710")
turbineCapField_usgs = "t_cap" ## in kW
states_fc = os.path.join(genericInputsGDB, "stateBound_baja")

'''
Analysis 
'''

''' Copy both feature classes to memory '''
ventyx_mem = arcpy.CopyFeatures_management(ventyx, "in_memory/ventyx")
usgs_mem = arcpy.CopyFeatures_management(usgs, "in_memory/usgs")


'''1. Process USGS dataset'''
## 1a. Clip to WECC states
usgs_mem_wecc = arcpy.Clip_analysis(in_features = usgs_mem, clip_features = states_fc, \
                                         out_feature_class = "in_memory/usgs_mem_wecc")

## 1b. Select only USGS turbines that are >= 1 MW OR (t_cap = -9999 AND p_year >= 2000) <-- unknown capacity, but area likely to be larger because they were built more recently.
usgs_mem_1MW = arcpy.Select_analysis(in_features = usgs_mem_wecc, out_feature_class = "in_memory/usgs_mem_1MW", \
                                               where_clause =  turbineCapField_usgs + " >= 1000 OR (" + turbineCapField_usgs + " = -9999 AND p_year >= 2000)")
arcpy.CopyFeatures_management(usgs_mem_1MW, os.path.join(intermediateGDB, "usgs_mem_1MW"))

## 1c. Buffer selected USGS wind turbines
usgs_mem_1MW_buff = arcpy.Buffer_analysis(in_features = usgs_mem_1MW, out_feature_class = "in_memory/usgs_mem_1MW_buff", \
                              buffer_distance_or_field = 1200)
arcpy.CopyFeatures_management(usgs_mem_1MW_buff, os.path.join(intermediateGDB, "usgs_mem_1MW_buff"))

'''2. Create Ventyx later to use: It represents the polygons of windfarms that are shared between Ventyx and USGS datasets.
It removes areas in Ventyx polgyons that do not have existing wind turbines.'''

## 2a. Clip the the Ventyx existing farm polygon file using the USGS buffered turbines. 
ventyx_mem_clipped = arcpy.Clip_analysis(in_features = ventyx_mem, clip_features = usgs_mem_1MW_buff, \
                                         out_feature_class = "in_memory/ventyx" + "_clipped")
arcpy.CopyFeatures_management(ventyx_mem_clipped, os.path.join(intermediateGDB, "ventyx_mem_clipped"))
print("finished with clipping the Ventyx data")

'''3. Create USGS layer to use: usgs polygons that are in addition to the ventyx polygons'''
## 3a. Erase the newly created Ventyx layer from the USGS selected turbines (point data).
usgs_mem_1MW_unique = arcpy.Erase_analysis(in_features = usgs_mem_1MW, erase_features = ventyx_mem_clipped, \
                                           out_feature_class = "in_memory/usgs_mem_1MW" + "_unique")
arcpy.CopyFeatures_management(usgs_mem_1MW_unique, os.path.join(intermediateGDB, "usgs_mem_1MW_unique"))

## 3b. Buffer the resulting, erased USGS points using 500 m radius. Make sure that the dissolved field is summing the turbine capacity column (t_cap) so that the MW for each row is correct 
usgs_mem_1MW_unique_buff = arcpy.Buffer_analysis(in_features = usgs_mem_1MW_unique, \
                                                 out_feature_class = "in_memory/usgs_mem_1MW_unique_buff", \
                              buffer_distance_or_field = 750)

## 3c. Dissolve the overlappying polygons and sums the t_cap field
usgs_mem_1MW_unique_buff_diss = arcpy.Dissolve_management(in_features = usgs_mem_1MW_unique_buff, \
                                                          out_feature_class = "in_memory/usgs_mem_1MW_unique_buff_diss", \
                           dissolve_field = turbineCapField_usgs, statistics_fields = [[turbineCapField_usgs,"SUM"]])
## Calculate a new field to convert kW to MW for the USGS areas
arcpy.AddField_management(usgs_mem_1MW_unique_buff_diss, "SUM_t_cap_MW", "FLOAT")
arcpy.CalculateField_management(in_table = usgs_mem_1MW_unique_buff_diss, field = "SUM_t_cap_MW", \
                                    expression = "!SUM_t_cap!/1000", expression_type = "PYTHON_9.3")

## rename the summed, dissolved MW capacity field the same field name as Ventyx's 
arcpy.AlterField_management(in_table = usgs_mem_1MW_unique_buff_diss, field = "SUM_t_cap_MW", new_field_name = existingWind_MWfield_ventyx, \
                            new_field_alias = existingWind_MWfield_ventyx)

arcpy.CopyFeatures_management(usgs_mem_1MW_unique_buff_diss, os.path.join(intermediateGDB, "usgs_mem_1MW_unique_buff_diss"))


''' 4. Merge the newly created ventyx clipped and usgs unique buffered dissvoled polygons '''
merged = arcpy.Merge_management(inputs = [ventyx_mem_clipped, usgs_mem_1MW_unique_buff_diss], output= "in_memory/merged")

## copy back to the directory
arcpy.CopyFeatures_management(merged, os.path.join(eInfrastGDB, "Ventyx_USGS_merged_repowering"))

print("finished with process")



