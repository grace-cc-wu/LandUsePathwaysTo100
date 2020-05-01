# -*- coding: utf-8 -*-
"""
Created on Wed Aug 29 15:28:02 2018

@author: Grace

PURPOSE: This script takes the outputs of createSupplyCurve.py and RESOLVE portfolios
to create spatially-explicit maps of the build-out for each RESOLVE portfolio 
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

'''
################################################################################
##---------------------Local Parameters and workspace------------------------###
################################################################################
'''
##---------------------Set assumptions below for each technology------------------------
netPPAsuffix = "_net"
supplyCurvePrefix = "supplyCurve_"
txMultiplier = 1.3
tech = "Solar"
netRENthreshold_m = 2500
annualHrs = 8760
txWidth_km = 0.076 ## km Width of tx corridor
#**** UPDATE THIS AS PER THE TECHOLOGY: 
largestZoneArea_km2 = 9 ## area of the largest possible zone in km2

##---------------------Set paths ------------------------
mainDir = "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\"

### Set workspace for saving outputs: create file geodatabase (fgdb) for run session outputs
suitableSitesGDB = os.path.join(mainDir,"siteSuitabilityOutputs\\112918_resourceAssessment.gdb\\") #^^
eInfrastGDB = os.path.join(mainDir,"dataCollection\\existingEnergyInfrastructure\\energyInfrastructure.gdb\\")
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

## Csvs:
df_CFadj = pandas.read_csv(os.path.join(mainDir, "RESOLVEoutputs", "E3_Output of Environmental Screens_v2_CFadjustmentsForSpatialDisagg_constant.csv"))
df_CFadj_w2w = pandas.read_csv(os.path.join(mainDir, "RESOLVEoutputs", "E3_Output of Environmental Screens_v2_CFadjustmentsForSpatialDisagg_w2w.csv"))
df_RESOLVEscenarios_total = pandas.read_csv(os.path.join(mainDir, "RESOLVEoutputs", "Results Summary Workbook_v11_20181214_total.csv"))
df_RESOLVEscenarios_selected = pandas.read_csv(os.path.join(mainDir, "RESOLVEoutputs", "Results Summary Workbook_v11_20181214_selected.csv"))

##### Import csv of correction factors
## select relevant columns (CF adjustment values and name of RESOLVE Zone)
## adjustment factors are in columns called CF_adj_Cat%n%; RESOLVE_ZONE column contains zone names specific to wind and solar
## Subset to technology of interest
df_CFadj_select = df_CFadj.filter(regex=('CF_adj_\S|RESOLVE_ZONE|Technology|STATE'), axis =1)
df_CFadj_select_w2w = df_CFadj_w2w.filter(regex=('CF_adj_\S|RESOLVE_ZONE|Technology|STATE'), axis =1)

RESOLVE_ZONES_CA_fc = os.path.join(genericInputsGDB, "SUPERCREZ_proj_CA_RESOLVE_ZONE")
RESOLVE_ZONES_OOS_PV_fc = os.path.join(genericInputsGDB, "QRA_proj_RESOLVE_ZONE_solar")
RESOLVE_ZONES_OOS_wind_fc = os.path.join(genericInputsGDB, "QRA_proj_RESOLVE_ZONE_Wind")
states_fc = os.path.join(genericInputsGDB, "stateBound_baja")

existingPV_CA = os.path.join(eInfrastGDB, "CA_Solar_Footprints_2018_CA_RESOLVEZONE_dissolvedByPlant") 
existingPV_OOS = os.path.join(eInfrastGDB, "NationalSolarArrays_solarOnly")
existingPV_REN_pts = os.path.join(eInfrastGDB, "REN_ExistingResources_latlongAdded_PV_gte5MW")

existingWind = os.path.join(eInfrastGDB, "Ventyx_USGS_merged_repowering")
existingWind_MWfield = "OP_CAP_MW"
existingWind_REN_pts = os.path.join(eInfrastGDB, "REN_ExistingResources_latlongAdded_wind")

## Lists of created netREN files 
## netREN_wind + Ventyx wind planned = planned and commercial wind projects WECC wide
netREN_wind_list = [os.path.join(eInfrastGDB, "REN_ExistingResources_latlongAdded_wind_net"), \
                   os.path.join(eInfrastGDB, "Ventyx_wind_farms_polygon_planned")]
netREN_PV = os.path.join(eInfrastGDB, "REN_ExistingResources_latlongAdded_PV_gte5MW_net")


## List of existing transmission and susbtation data to use
existingTxSubList = [os.path.join(eInfrastGDB, "Ventyx_e_substn_point_existing_WECC_gte68kV"), \
                     os.path.join(eInfrastGDB, "Ventyx_e_transln_polyline_existing_gte69kV"),\
                     os.path.join(eInfrastGDB, "CEC_Transmission_Line_gte69kV"),\
                     os.path.join(eInfrastGDB, "CEC_Substation_gte69kV"),\
                     os.path.join(eInfrastGDB, "BLM_transmission_line_pref_route_energy_b2h"), \
                     os.path.join(eInfrastGDB, "BLM_transmission_line_pref_route_energy_gateway_south_v2"),\
                     os.path.join(eInfrastGDB, "BLM_transmission_line_pref_route_energy_gateway_west_v2"), \
                     os.path.join(eInfrastGDB, "BLM_transmission_line_pref_route_energy_southline"),\
                     os.path.join(eInfrastGDB, "BLM_transmission_line_pref_route_energy_sunzia"), \
                     os.path.join(eInfrastGDB, "BLM_transmission_line_pref_route_energy_transwest_express")]

catFileDict_windSolar = {"Cat1" : "cat1b",\
            "Cat2" : "cat2f",\
            "Cat3" : "cat3c", \
             "Cat4": "cat4"}

catFileDict_geothermal = {"Cat1" : "cat1b",\
            "Cat2" : "cat2f",\
            "Cat3" : "cat3", \
             "Cat4": "cat4"}

##--------------------- SET INPUT FILES FOR EACH TECHNOLOGY ----------------------------
## List of inputs to loop over
zoneType_ls = {"state": "_PA_state", \
            "OOS_RESOLVEZONE": "_PA_OOS_RESOLVEZONE", \
             "CA_RESOLVEZONE": "_PA_CA_RESOLVEZONE"}
scratch = "C:/Users/Grace/Documents/TNC_beyond50/PathTo100/siteSuitabilityOutputs/scratch.gdb"
df_CFadj_select_tech = df_CFadj_select.loc[df_CFadj_select['Technology'] == tech]
df_CFadj_select_w2w_tech = df_CFadj_select_w2w.loc[df_CFadj_select_w2w['Technology'] == tech]

if tech == "Geothermal":
    ft_ls = {"Cat1" : "geothermal_cat1b",\
            "Cat2" : "geothermal_cat2f",\
            "Cat3" : "geothermal_cat3", \
             "Cat4": "geothermal_cat4"}
    zoneFieldName_RESOLVE = "RESOLVE_ZONE"
    lue = 25.5 ## MW/km2
    df_CFadj_select_tech = df_CFadj_select.loc[df_CFadj_select['Technology'] == tech]
    df_CFadj_select_w2w_tech = df_CFadj_select_w2w.loc[df_CFadj_select_w2w['Technology'] == tech]

    geoZoneType_ls = {"_QRAJoined" : "RESOLVE_ZONE", "_stateJoined" : "STATE", "_SuperCREZJoined": "RESOLVE_ZONE"}
    
if tech == "Wind":
    ## WIND:
    ft_ls = {"Cat1" : "wind_0_03_nonEnv_r3_cat1b_singlepart_gt1km2",\
            "Cat2" : "wind_0_03_nonEnv_r3_cat2f_singlepart_gt1km2",\
            "Cat3" : "wind_0_03_nonEnv_r3_cat3c_singlepart_gt1km2", \
             "Cat4": "wind_0_03_nonEnv_r3_cat4_singlepart_gt1km2"}
    CF = os.path.join(mainDir, "dataCollection", "siteSuitabilityInputs_nonEnv.gdb\\CF_WINDtoolkit_NREL_IDW_masked_NoDataVals_250m")
    zoneFieldName_RESOLVE = "RESOLVE_ZONE_wind_1"
    lue = 6.1 ## MW/km2
    df_CFadj_select_tech = df_CFadj_select.loc[df_CFadj_select['Technology'] == tech]
    df_CFadj_select_w2w_tech = df_CFadj_select_w2w.loc[df_CFadj_select_w2w['Technology'] == tech]

if tech == "Solar":
    ## SOLAR:
    ft_ls = {"Cat1" : "solarPV_0_0_nonEnv_r1_cat1b_singlepart_gt1km2",\
            "Cat2" : "solarPV_0_0_nonEnv_r1_cat2f_singlepart_gt1km2",\
            "Cat3" : "solarPV_0_0_nonEnv_r1_cat3c_singlepart_gt1km2", \
             "Cat4": "solarPV_0_0_nonEnv_r1_cat4_singlepart_gt1km2"}
    CF = os.path.join(mainDir, "dataCollection", "siteSuitabilityInputs_nonEnv.gdb\\CF_FixedPV_SAM_AC_CF_250m")
    zoneFieldName_RESOLVE = "RESOLVE_ZONE_solar_1"
    lue = 30 ## MW/km2
    df_CFadj_select_tech = df_CFadj_select.loc[df_CFadj_select['Technology'] == tech]
    df_CFadj_select_w2w_tech = df_CFadj_select_w2w.loc[df_CFadj_select_w2w['Technology'] == tech]
    
##--------------------- SET OUTPUT paths  ----------------------------

existingMWh_wind_RESOLVEZONE_csv = os.path.join(spDisaggFolder, "intermedInputs", "existingMWh_wind_RESOLVEZONE.csv")
existingMWh_wind_states_csv = os.path.join(spDisaggFolder, "intermedInputs", "existingMWh_wind_states.csv")

existingMWh_PV_RESOLVEZONE_csv = os.path.join(spDisaggFolder, "intermedInputs", "existingMWh_PV_RESOLVEZONE.csv")
existingMWh_PV_states_csv = os.path.join(spDisaggFolder, "intermedInputs", "existingMWh_PV_states.csv")

''' 
#######################################################################################
## ------------------------ I. Preprocess necessary inputs ----------------------------
#######################################################################################

PURPOSE: A) create netREN point locations (baseline projects for which we do not have areal footprints)
    B) Estimate MWh of existing power plants using CF from resource maps
    C) Create buffers around geothermal point locations based on land use efficiency (i.e.,
    convert points to polygons)
'''

#######################################################################################
## A. Create netREN wind and solar locations/points and save as points
#######################################################################################

## Note: "_net" = point locations for which we have no polygon footprint data for "baseline projects", 
## so we will treat as "planned or commercial" projects and prioritize these when creating the supply curve by "tagging" them

#### WIND:
## erase Ventyx+USGS wind existing from REN_wind = netREN_wind
netREN_wind = arcpy.Erase_analysis(in_features = existingWind_REN_pts, \
                     erase_features = existingWind, \
                     out_feature_class = os.path.join(eInfrastGDB, "REN_ExistingResources_latlongAdded_wind_net"))

#### PV:
## erase TNC solar footprints and USGS footprints from REN_solar = netREN_PV (planned and commercial PV projects) in CA (none WECC wide)
netREN_PV_intermed = arcpy.Erase_analysis(in_features = existingPV_REN_pts, \
                     erase_features = existingPV_CA, \
                     out_feature_class = "in_memory/netREN_PV_intermed")

netREN_PV = arcpy.Erase_analysis(in_features = netREN_PV_intermed, \
                     erase_features = existingPV_OOS, \
                     out_feature_class = os.path.join(eInfrastGDB, "REN_ExistingResources_latlongAdded_PV_gte5MW_net"))
print("Finished creating planned and commercial project locations")


#######################################################################################
## B. Calculate MWh of existing powerplants using attribute MW and RESOLVE CFs and save as csvs 
#######################################################################################

##### select columns from RESOLVE OUTPUTS to get CF
df_CFadj_select_CF = df_CFadj.filter(regex=('SupplyCurveCF_used|RESOLVE_ZONE|Technology|STATE'), axis =1)

zoneList_wind = {"CA_RESOLVEZONE": [RESOLVE_ZONES_CA_fc, "RESOLVE_ZONE"], \
                 "OOS_RESOLVEZONE": [RESOLVE_ZONES_OOS_wind_fc, "RESOLVE_ZONE_wind"], \
                 "state" : [states_fc, "STATE_1"]}

zoneList_PV = {"CA_RESOLVEZONE": [RESOLVE_ZONES_CA_fc, "RESOLVE_ZONE", existingPV_CA, "MW_estFrmAcres"], \
                 "OOS_RESOLVEZONE": [RESOLVE_ZONES_OOS_PV_fc, "RESOLVE_ZONE_solar", existingPV_OOS, "total_cap"], \
                 "state" : [states_fc, "STATE_1", existingPV_OOS, "total_cap"]}
##### WIND

## create a list to hold the RESOLVE zone MW aggregates 
RESOLVEZONE_wind_df_dict = {}

## subset the RESOLVE supply curve to only wind rows
df_CFadj_select_wind = df_CFadj_select_CF.loc[df_CFadj_select_CF['Technology'] == "Wind"]

## for each existing wind feature class
for zone in zoneList_wind:
    arcpy.SpatialJoin_analysis(target_features = existingWind, join_features = zoneList_wind[zone][0], \
                           out_feature_class = existingWind + "_" + zone, join_operation = "JOIN_ONE_TO_ONE", join_type= "KEEP_ALL", \
                           match_option = "HAVE_THEIR_CENTER_IN")
    
    ## convert gdb table to numpy array to Pandas DF:
    fieldList = [field.name for field in arcpy.ListFields(existingWind + "_" + zone)]
    pattern = r'RESOLVE_ZONE\S|OP_CAP_MW|STATE|RESOLVE_ZONE'
    fieldList = [x for x in fieldList if re.search(pattern, x)] 
    
    df_windFC = pandas.DataFrame(arcpy.da.TableToNumPyArray(existingWind + "_" + zone, fieldList))
    
    ## sum the MW per Zone:
    df_windFC_sums = df_windFC.groupby(zoneList_wind[zone][1])[[existingWind_MWfield]].sum().reset_index()
    
    ## if CA RESOLVE ZONES, then append _%tech% to the names of the zones:
    if zone == "CA_RESOLVEZONE":
        df_windFC_sums[zoneList_wind[zone][1]] =  df_windFC_sums[zoneList_wind[zone][1]].astype(str) + "_Wind"
        RESOLVEjoinField = "RESOLVE_ZONE"
    if zone == "OOS_RESOLVEZONE":
        RESOLVEjoinField = "RESOLVE_ZONE"    
    if zone == "state":
        RESOLVEjoinField = "STATE"
    
    ## merge with the RESOLVE supply curve CFs
    df_windFC_sums_merged = pandas.merge(df_windFC_sums, df_CFadj_select_wind, how= 'left', left_on = zoneList_wind[zone][1], right_on = RESOLVEjoinField)
    
    ## Calculate MWh from CF and MW
    df_windFC_sums_merged["MWh"] =  df_windFC_sums_merged[existingWind_MWfield]*df_windFC_sums_merged["SupplyCurveCF_used"]*8760
    
    ## Remove CA rows if state aggregated
    if zone == "state":
        df_windFC_sums_merged = df_windFC_sums_merged.loc[df_windFC_sums_merged['STATE_1'] != "California"]
    
    
    RESOLVEZONE_wind_df_dict[zone] = df_windFC_sums_merged
    
    print("Spatial join complete for " + existingWind + " " + zone)

## merge the CA and OOS 
RESOLVEZONE_wind_existingMWh_df = pandas.concat([RESOLVEZONE_wind_df_dict["CA_RESOLVEZONE"], RESOLVEZONE_wind_df_dict["OOS_RESOLVEZONE"]], axis = 0)
## save to csv
RESOLVEZONE_wind_existingMWh_df.to_csv(existingMWh_wind_RESOLVEZONE_csv)


## merge the CA and States 
w2s_wind_existingMWh_df = pandas.concat([RESOLVEZONE_wind_df_dict["CA_RESOLVEZONE"], RESOLVEZONE_wind_df_dict["state"]], axis = 0)
## save states MWh to csv
w2s_wind_existingMWh_df.to_csv(existingMWh_wind_states_csv)


#### SOLAR
## create a list to hold the RESOLVE zone MW aggregates 
RESOLVEZONE_solar_df_dict = {}

## subset the RESOLVE supply curve to only wind rows
df_CFadj_select_solar = df_CFadj_select_CF.loc[df_CFadj_select_CF['Technology'] == "Solar"]

for zone in zoneList_PV:
    arcpy.SpatialJoin_analysis(target_features = zoneList_PV[zone][2], join_features = zoneList_PV[zone][0], \
                           out_feature_class = zoneList_PV[zone][2] + "_" + zone, join_operation = "JOIN_ONE_TO_ONE", join_type= "KEEP_ALL", \
                           match_option = "HAVE_THEIR_CENTER_IN")
    
    ## convert gdb table to numpy array to Pandas DF:
    fieldList = [field.name for field in arcpy.ListFields(zoneList_PV[zone][2] + "_" + zone)]
    pattern = r'RESOLVE_ZONE\S|STATE|RESOLVE_ZONE|\A' + zoneList_PV[zone][3]
    fieldList = [x for x in fieldList if re.search(pattern, x)] 
    
    df_solarFC = pandas.DataFrame(arcpy.da.TableToNumPyArray(zoneList_PV[zone][2] + "_" + zone, fieldList))
    
    ## sum the MW per Zone:
    df_solarFC_sums = df_solarFC.groupby(zoneList_PV[zone][1]).sum().reset_index()
    
    ## if CA RESOLVE ZONES, then append _%tech% to the names of the zones:
    if zone == "CA_RESOLVEZONE":
        df_solarFC_sums[zoneList_PV[zone][1]] =  df_solarFC_sums[zoneList_PV[zone][1]].astype(str) + "_Solar"
        RESOLVEjoinField = "RESOLVE_ZONE"
    if zone == "OOS_RESOLVEZONE":
        RESOLVEjoinField = "RESOLVE_ZONE"    
    if zone == "state":
        RESOLVEjoinField = "STATE"
    
    ## merge with the RESOLVE supply curve CFs
    df_solarFC_sums_merged = pandas.merge(df_solarFC_sums, df_CFadj_select_solar, how= 'left', left_on = zoneList_PV[zone][1], right_on = RESOLVEjoinField)
    
    ## Calculate MWh from CF and MW
    df_solarFC_sums_merged["MWh"] =  df_solarFC_sums_merged[zoneList_PV[zone][3]]*df_solarFC_sums_merged["SupplyCurveCF_used"]*8760
    
    ## Remove CA rows if state aggregated
    if zone == "state":
        df_solarFC_sums_merged = df_solarFC_sums_merged.loc[df_solarFC_sums_merged['STATE_1'] != "California"]
    
    RESOLVEZONE_solar_df_dict[zone] = df_solarFC_sums_merged
    
    print("Spatial join complete for " + zoneList_PV[zone][2] + " " + zone)
    
## merge the CA and OOS 
RESOLVEZONE_PV_existingMWh_df = pandas.concat([RESOLVEZONE_solar_df_dict["CA_RESOLVEZONE"], RESOLVEZONE_solar_df_dict["OOS_RESOLVEZONE"]], axis = 0)
## save to csv
RESOLVEZONE_PV_existingMWh_df.to_csv(existingMWh_PV_RESOLVEZONE_csv)

## save states MWh to csv

## merge the CA and States 
w2w_PV_existingMWh_df = pandas.concat([RESOLVEZONE_solar_df_dict["CA_RESOLVEZONE"], RESOLVEZONE_solar_df_dict["state"]], axis = 0)
## save states MWh to csv
w2w_PV_existingMWh_df.to_csv(existingMWh_PV_states_csv)

#######################################################################################
## C. Geothermal: select the suitable points for each env and geography, create buffers that will represent area
#######################################################################################

## Remove STATE field and rename actual state field as STATE -- do this only once!
for cat in ft_ls:
    geo_pt = os.path.join(suitableSitesGDB, ft_ls[cat] + "_stateJoined")
    arcpy.DeleteField_management(geo_pt, "State")
    arcpy.AddField_management(geo_pt, "STATE", "Text")
    arcpy.CalculateField_management(in_table = geo_pt, field = "STATE", \
                                    expression = "!STATE_12!", expression_type = "PYTHON_9.3")
    print("finished with " + geo_pt)
    
## RENAME RESOLVE_ZONE_geothermal as RESOLVE_ZONE in _QRAJoined feature classes -- only do this once!
for cat in ft_ls:
    geo_pt = os.path.join(suitableSitesGDB, ft_ls[cat] + "_QRAJoined")
    arcpy.AlterField_management(in_table = geo_pt, field = "RESOLVE_ZONE_geothermal", new_field_name = "RESOLVE_ZONE", new_field_alias = "RESOLVE_ZONE")
    print("finished with " + geo_pt)

for cat in ft_ls:
    for zoneType in geoZoneType_ls:
        geo_pt = os.path.join(suitableSitesGDB, ft_ls[cat] + zoneType)
        print(geo_pt)
        ## For each geo_pt, select points where fields for zone are not null
        zoneFieldName = geoZoneType_ls[zoneType]
        geo_pt_select_mem = arcpy.Select_analysis(in_features = geo_pt, out_feature_class = "in_memory/geo_pt", \
                                           where_clause= zoneFieldName + " <> 'NULL'") 
        if zoneType == "_stateJoined":
            geo_pt_select_mem = arcpy.Select_analysis(in_features = geo_pt, out_feature_class = "in_memory/geo_pt", \
                                           where_clause= zoneFieldName + "<> 'California'")
        
        ## Create buffers for each of the points with radii calculated based on capacity 
        arcpy.AddField_management(geo_pt_select_mem, "buffRad_m", "FLOAT")
        arcpy.CalculateField_management(geo_pt_select_mem, "buffRad_m", "math.sqrt(!MW!/(25.5*math.pi))*1000", "PYTHON_9.3")
        geo_pt_select_buff_mem = arcpy.Buffer_analysis(in_features = geo_pt_select_mem, out_feature_class = "in_memory/geo_pt_buff", \
                              buffer_distance_or_field = "buffRad_m")
        
        ## Calculate area of the buffers
        arcpy.AddField_management(geo_pt_select_buff_mem, "Area", "FLOAT")
        arcpy.CalculateField_management(in_table = geo_pt_select_buff_mem, field = "Area", \
                                    expression = "!Shape.Area@squarekilometers!", expression_type = "PYTHON_9.3")
        
        ## Copy back to HD
        ## rename using standard zoneType_ls names
        zoneDict = {"_QRAJoined" : "OOS_RESOLVEZONE", "_stateJoined" : "state", "_SuperCREZJoined": "CA_RESOLVEZONE"}
        arcpy.CopyFeatures_management(geo_pt_select_buff_mem, geo_pt.replace(zoneType, "") + "_" + zoneDict[zoneType])
            
'''
#######################################################################################
## ---------------------- II. Site selection FUNCTIONS --------------------------------
#######################################################################################

PURPOSE: write functions for each step in the site selection process:
    A) Erase wind and PV existing power plants from all categories; erase selected wind sites from PV PPAs
    B) Calculate distance to netREN and "tag" PPAs within distance threshold
    C) Calculate tx distance, average CF, apply CF correction, and create supply curve as Pandas DF and feature class
    D) FOR GEOTHERMAL: Calculate tx distance, average CF, apply CF correction, and create supply curve as Pandas DF and feature class
    E) Sort supply curve and select CPAs for each Zone or state for each scenario
'''

#######################################################################################
## A. Erase wind and PV existing power plants from all categories; erase selected wind sites from PV PPAs
#######################################################################################
        
def eraseExistingPP(tech, cat, zoneType, scen, in_existingWind, in_existingPV_CA, in_existingPV_OOS, in_selectedSitesList, calcArea):
    ## construct path of input potential project area
    PPA = os.path.join(suitableSitesGDB, ft_ls[cat] + zoneType_ls[zoneType])
    #print(PPA)
    
    ## Copy to memory
    PPA_mem = arcpy.CopyFeatures_management(PPA, "in_memory/PPAcopy")
    
    ## Erase wind and solar footprints if supplied an input
    if in_existingWind:
        PPA_erWind = arcpy.Erase_analysis(in_features = PPA_mem, erase_features = in_existingWind, \
                                    out_feature_class = "in_memory/PPA_wind")
        print("Erased existing wind plants from " + "in_existingWind")
    else:
        PPA_erWind = PPA_mem
    
    ## Then, erase solar footprints and save to spDisaggGDB
    if zoneType == "CA_RESOLVEZONE" and in_existingPV_CA:
        PPA_erWindPVCA = arcpy.Erase_analysis(in_features = PPA_erWind, erase_features = in_existingPV_CA, \
                                              out_feature_class = "in_memory/PPA_wind_solar")
        print("Erased existing PV plants from " + "in_existingPV_CA")
    else:
        PPA_erWindPVCA = PPA_erWind
        
    if zoneType != "CA_RESOLVEZONE" and in_existingPV_OOS:
        PPA_erWindPVOOS = arcpy.Erase_analysis(in_features = PPA_erWindPVCA, erase_features = in_existingPV_OOS, \
                                              out_feature_class = "in_memory/PPA_wind_solar")
        print("Erased existing PV plants from " + "in_existingPV_OOS")
    else:
        PPA_erWindPVOOS = PPA_erWind       
    
    ## If there are selected sites to also erase:
    if in_selectedSitesList: 
        if len(in_selectedSitesList) > 1:
            #windPPA = os.path.join(spDisaggGDB, "wind_0_03_nonEnv_r3_" + catFileDict[cat] + "_singlepart_gt1km2_PA_" + zoneType + "_net")
            
            #windPPA_select = arcpy.Select_analysis(in_features = windPPA, out_feature_class = "in_memory/windPPA_select", \
            #                                       where_clause=  scen + " = 'True'") 
            
            mergedSites = arcpy.Merge_management(inputs = in_selectedSitesList, output= "in_memory/merged")

            PPA_erWindPVselectedSites = arcpy.Erase_analysis(in_features = PPA_erWindPVOOS, erase_features = mergedSites, \
                                            out_feature_class = "in_memory/PPA_erWindPVselectedSites")
        else:
            PPA_erWindPVselectedSites = arcpy.Erase_analysis(in_features = PPA_erWindPVOOS, erase_features = in_selectedSitesList[0], \
                                            out_feature_class = "in_memory/PPA_erWindPVselectedSites")
        print("Erased selected sites")
        
    else:
        PPA_erWindPVselectedSites = PPA_erWindPVOOS
            
    ##### Recalculate area
    if calcArea:
        arcpy.CalculateField_management(in_table = PPA_erWindPVselectedSites, field = "Area", \
                                    expression = "!Shape.Area@squarekilometers!", expression_type = "PYTHON_9.3")
        print("Recalculated area")
        
    out = arcpy.CopyFeatures_management(PPA_erWindPVselectedSites, os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scen))
    
    print("Finished erasing existing power plants for " + ft_ls[cat] + zoneType_ls[zoneType])
    return out

##################################################################################
## B. Calculate distance to netREN and "tag" PPAs within distance threshold
##################################################################################

##### TAG PPAs if overlapping or very close to planned and commercial projects locations
#### Calculate distance to the nearest netREN plant and apply threshold cutoff 

def tagPPAnearNetREN(tech, cat, zoneType, scen, in_netREN_wind_list, in_netREN_PV, in_netRENthreshold_m):
    #if tech == "Wind":    
        ## construct path of input potential project areas
       # netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix)
    #if tech == "Solar":
    ## construct path of input potential project areas
    netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scen)
    
    ## copy to memory
    netPPA_mem = arcpy.CopyFeatures_management(netPPA, "in_memory/netPPA_mem")
    
    ## if the fields already exist, delete them first
    if "NEAR_DIST_netPPA" in [field.name for field in arcpy.ListFields(netPPA_mem)]:  
        arcpy.DeleteField_management(netPPA_mem, "NEAR_DIST_netPPA")
        arcpy.DeleteField_management(netPPA_mem, "NEAR_FID_netPPA")
    if "NEAR_FC_netPPA" in [field.name for field in arcpy.ListFields(netPPA_mem)]:      
        arcpy.DeleteField_management(netPPA_mem, "NEAR_FC_netPPA")
    if "NEAR_DIST" in [field.name for field in arcpy.ListFields(netPPA_mem)]:      
        arcpy.DeleteField_management(netPPA_mem, "NEAR_DIST")
        arcpy.DeleteField_management(netPPA_mem, "NEAR_FID")
        print("Deleting existing NEAR_DIST fields")
        
    ## Calculate distance
    if tech == "Wind":
        arcpy.Near_analysis(in_features = netPPA_mem, near_features = in_netREN_wind_list)
        arcpy.AlterField_management(in_table = netPPA_mem, field = "NEAR_FC", new_field_name = "NEAR_FC_netPPA") 
        
    if tech == "Solar":
        arcpy.Near_analysis(in_features = netPPA_mem, near_features = in_netREN_PV)
    
    ## Rename newly calculated NEAR fields (netPPA distance)
    arcpy.AlterField_management(in_table = netPPA_mem, field = "NEAR_DIST", new_field_name = "NEAR_DIST_netPPA")
    arcpy.AlterField_management(in_table = netPPA_mem, field = "NEAR_FID", new_field_name = "NEAR_FID_netPPA")      
    
    #### Create new column ("netREN" == 1 or 0) by applying cutoff threshold (5 km?) 
    codeblock = """def thresh(distField, threshold):
        if (distField >= threshold):
            return 0
        else:
            return 1"""
    
    if "netREN" not in [field.name for field in arcpy.ListFields(netPPA_mem)]:
        arcpy.AddField_management(netPPA_mem, "netREN", "SHORT")
        
    arcpy.CalculateField_management(netPPA_mem, "netREN", "thresh(!NEAR_DIST_netPPA!," + str(in_netRENthreshold_m) + ")", "PYTHON_9.3", codeblock)
    
    ## Copy back to HD
    arcpy.CopyFeatures_management(netPPA_mem, netPPA)
    
    print("Finished tagging " + ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + scen)
    
    return netPPA

##################################################################################
## C. Calculate tx distance, average CF, apply CF correction, and create supply curve as Pandas DF and feature class
##################################################################################

def calcAttributes(tech, cat, zoneType, scen, in_existingTxSubList, in_CF, in_df_CFadj_select_tech, in_lue, in_txWidth_km, in_largestZoneArea_km2):
    ## construct path of input potential project areas
    #if tech == "Wind":    
    #    ## construct path of input potential project areas
    #        netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix)
    #if tech == "Solar":
    #    ## construct path of input potential project areas
    netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scen)
        
    
    ## Select only those PPAs that are outside of CA (e.g., OOS)
    if zoneType == "state":
        
        netPPA_mem = arcpy.Select_analysis(in_features = netPPA, out_feature_class = "in_memory/netPPA_mem", \
                                           where_clause= "STATE_1 <> 'California'")
        print("Removing all California rows for w2w feature class")
    else:
        ## copy to memory
        netPPA_mem = arcpy.CopyFeatures_management(netPPA, "in_memory/netPPA_mem")
        
    ##################################################
    ### Calculate distance to nearest Tx or substation
    
    ## Calculate distance: output fields include "NEAR_FID", "NEAR_DIST", "NEAR_FC" when more than one feature class is provided
    netPPA_mem_dist = arcpy.Near_analysis(in_features = netPPA_mem, near_features = in_existingTxSubList)
    
    ## rename the distance fields
    if "NEAR_DIST" in [field.name for field in arcpy.ListFields(netPPA_mem)]:  
        ## Rename previous NEAR fields (transmission distance)
        arcpy.AlterField_management(in_table = netPPA_mem_dist, field = "NEAR_DIST", new_field_name = "NEAR_DIST_Tx")
        arcpy.AlterField_management(in_table = netPPA_mem_dist, field = "NEAR_FID", new_field_name = "NEAR_FID_Tx")
        arcpy.AlterField_management(in_table = netPPA_mem_dist, field = "NEAR_FC", new_field_name = "NEAR_FC_Tx")
        
    print("Finished calculating tx distance for " + ft_ls[cat] + zoneType_ls[zoneType])


    ##################################################
    ### Calculate average CF
        
    ## Get average CF per project
    table = arcpy.sa.ZonalStatisticsAsTable(in_zone_data = netPPA_mem_dist, zone_field = "OBJECTID", in_value_raster = in_CF, \
                                            out_table = "in_memory/avgCF", ignore_nodata = "DATA", statistics_type = "MEAN")
    
    ## Delete Name CF_avg_catx field if it already exists:
    fieldList = [field.name for field in arcpy.ListFields(netPPA_mem_dist)]
    if "CF_avg_" + cat in fieldList:
        print("Deleting existing field: " + "CF_avg_" + cat)
        arcpy.DeleteField_management(netPPA_mem_dist, "CF_avg_" + cat)
    
    ## Join zonal statistics table of "MEAN" RQ values to target project polygon; "OBJECTID_1" field is the name of the "zone"
    arcpy.JoinField_management(netPPA_mem_dist, "OBJECTID", table, "OBJECTID_1", "MEAN")
    ## Change field name from MEAN to avgCF
    arcpy.AlterField_management(in_table = netPPA_mem_dist, field = "MEAN", new_field_name = "CF_avg_" + cat)
    
    ## Change field name from RESOLVE_ZONE_%tech% or RESOLVE_ZONE_1 to RESOLVE_ZONE or STATE_1 to "STATE"
    p=re.compile(".*(RESOLVE_ZONE).*")
    fieldList = [field.name for field in arcpy.ListFields(netPPA_mem_dist)]
    zoneFieldName = [m.group(0) for l in fieldList for m in [p.search(l)] if m]
    
    if zoneType != "state" and zoneFieldName:    
        arcpy.AlterField_management(in_table = netPPA_mem_dist, field = zoneFieldName[0], new_field_name = "RESOLVE_ZONE")
        print("Renamed RESOLVE_ZONE field")
    
    if zoneType == "state":
        arcpy.CalculateField_management(netPPA_mem_dist, "STATE", "!STATE_1!", "PYTHON_9.3")
        arcpy.DeleteField_management(netPPA_mem_dist, "STATE_1")
        print("Renamed STATE field")
        if zoneFieldName:
            for field in zoneFieldName:
                print("Deleted RESOLVE_ZONE field: " + field +  " from state site suitability feature classes")
                arcpy.DeleteField_management(netPPA_mem_dist, field)
        
    print("Finished calculating average CF for " + ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scen)


    ##################################################
    ### apply CF correction, and create supply curve as Pandas DF and feature class
        
    ## convert gdb table to numpy array to Pandas DF:
    fieldList = [field.name for field in arcpy.ListFields(netPPA_mem_dist)]
    pattern = r'OBJECTID|RESOLVE_ZONE|CF_avg_\S|Area|NEAR_DIST\S|STATE|netREN'
    fieldList = [x for x in fieldList if re.search(pattern, x)] 
    
    df_netPPA = pandas.DataFrame(arcpy.da.TableToNumPyArray(netPPA_mem_dist, fieldList))
    
    ## Use the correct zone field for each scenario (RESOLVE_ZONE or wall to wall-state)
    if zoneType == "state":
        zoneFieldName_loop = "STATE"
    else:
        zoneFieldName_loop = "RESOLVE_ZONE"
        ## IF RESOLVE ZONE scenarios, append technology to end of RESOLVE_ZONE name:
        if zoneType == "CA_RESOLVEZONE":
            df_netPPA["RESOLVE_ZONE"] =  df_netPPA['RESOLVE_ZONE'].astype(str) + "_" + tech
    
    ## merge adjustment factor df and potential project area df--keep only zones that are in the RESOLVE supply curve
    ## drop duplicate rows (because there are two Pacific_Northwest_Wind columns due to Oregon and Washington are two rows;
    ## this causes the inner join to result in duplicated rows; however, these rows will be kept when the zone is state)
    #in_df_CFadj_select_tech = in_df_CFadj_select_tech[[zoneFieldName_loop, 'CF_adj_Cat1', 'CF_adj_Cat2', 'CF_adj_Cat3', 'CF_adj_Cat4']]
    in_df_CFadj_select_tech = in_df_CFadj_select_tech.drop_duplicates(zoneFieldName_loop)
    
    ## join the CF adjustments table with the df_netPPA--this also joins the RESOLVE_ZONE field
    df_netPPA_adj = pandas.merge(df_netPPA, in_df_CFadj_select_tech, how= 'inner', on = zoneFieldName_loop)
    
    ## Calculate corrected CF for each PPA for each scenario 
    df_netPPA_adj["CF_avg_adj"] =  df_netPPA_adj['CF_avg_' + cat]*df_netPPA_adj['CF_adj_' + cat]
    
    ## Calculate the MW from the area = Area * land use efficiency(lue)
    df_netPPA_adj["MW"] =  df_netPPA_adj["Area"]*in_lue
    
    ## Calculate the Mwh from the MW and CF_avg_adj_Cat%n%
    df_netPPA_adj["MWh"] =  df_netPPA_adj["MW"]*df_netPPA_adj["CF_avg_adj"]*annualHrs
    
    ## Calculate the transmission area using tx distance and line width = 0.076 km; 
    df_netPPA_adj["txArea"] =  df_netPPA_adj["NEAR_DIST_Tx"]/1000*in_txWidth_km
    
    ## Calculate total tx area adjusted by the size of generation ()
    ## To avoid systematically reducing the total land use efficiency (MWh km-2) of smaller development zones 
    ## as a result of a fixed interconnection area, we applied a correction factor to the interconnection area 
    ## using the ratio of the development zone area (as small as 2 km2) to the largest possible development 
    ## zone area (25 km2).”) e.g., if a potential project area is 10 km and the largest is 25, then the total \
    ## tx area was multiplied by 10/25 or ⅖. 
    
    in_largestZoneArea_km2 = max(df_netPPA_adj["Area"])
    df_netPPA_adj["txAreaAdj"] =  df_netPPA_adj["txArea"]*(df_netPPA_adj["Area"]/in_largestZoneArea_km2)

    ## Calculate average MWh/km2 (total area = tx + gen)
    df_netPPA_adj["totArea"] =  df_netPPA_adj["txAreaAdj"] + df_netPPA_adj["Area"]
    df_netPPA_adj["avgMWhperKm2"] =  df_netPPA_adj["MWh"]/df_netPPA_adj["totArea"]
    
    ## sort the df by ranking potential project areas by 1) Whether netREN == 1 (ranked first), 
    ## (2) by highest to lowest MWh/km2
    #sort by df_netPPA_adj["netREN"] first, then df_netPPA_adj["avgMWhperKm2" + cat] second. 
    
    ## Add column with unique zone ID
    df_netPPA_adj["zoneID_num"] = df_netPPA_adj.index + 1
    df_netPPA_adj["zoneID"] = zoneType + "_" + df_netPPA_adj["zoneID_num"].map(str)
    
    ## save unsorted supply curve to csv 
    ## csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_supplyCurve.csv")
    ## if tech == "Solar":
    csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_" + scen + "_supplyCurve.csv")
        
    df_netPPA_adj.to_csv(csvFileName, index = False)
    
    ## join this df back to feature class attribute table
    arcpy.TableToTable_conversion(in_rows = csvFileName, out_path = spDisaggGDB_scratch, out_name = "tempTable")
    
    arcpy.CopyFeatures_management(in_features = netPPA_mem_dist, \
                                  out_feature_class = netPPA)
    
    fieldList = ["CF_adj_" + cat, "CF_avg_adj", "MW", \
         "MWh", "txArea", "txAreaAdj", "totArea", "avgMWhperKm2", "zoneID"]
    
    ## join attribute calculations back to the feature class
    arcpy.JoinField_management(in_data = netPPA, in_field = "OBJECTID" , \
                             join_table = os.path.join(spDisaggGDB_scratch, "tempTable"), join_field = "OBJECTID",\
                             fields = fieldList )
    print("finished with " + netPPA)
    print("")
    
    return netPPA

##################################################################################
## D. FOR GEOTHERMAL: Calculate tx distance, average CF, apply CF correction, and create supply curve as Pandas DF and feature class
##################################################################################

def calcAttributes_geothermal(tech, cat, zoneType, scen, in_existingTxSubList, in_df_CFadj_select_tech, in_lue, in_txWidth_km, in_largestZoneArea_km2):
    ## construct path of input potential project areas
    netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scen)
    
    netPPA_mem = arcpy.CopyFeatures_management(netPPA, "in_memory/netPPA_mem")
        
    ##################################################
    ### Calculate distance to nearest Tx or substation
    
    ## Calculate distance: output fields include "NEAR_FID", "NEAR_DIST", "NEAR_FC" when more than one feature class is provided
    netPPA_mem_dist = arcpy.Near_analysis(in_features = netPPA_mem, near_features = in_existingTxSubList)
    
    ## rename the distance fields
    if "NEAR_DIST" in [field.name for field in arcpy.ListFields(netPPA_mem)]:  
        ## Rename previous NEAR fields (transmission distance)
        arcpy.AlterField_management(in_table = netPPA_mem_dist, field = "NEAR_DIST", new_field_name = "NEAR_DIST_Tx")
        arcpy.AlterField_management(in_table = netPPA_mem_dist, field = "NEAR_FID", new_field_name = "NEAR_FID_Tx")
        arcpy.AlterField_management(in_table = netPPA_mem_dist, field = "NEAR_FC", new_field_name = "NEAR_FC_Tx")
        
    print("Finished calculating tx distance for " + netPPA)


    ##################################################
    ### Retrieve CF from E3_Output of Environmental Screens_v2_CFadjustmentsForSpatialDisagg and create supply curve as Pandas DF and feature class
        
    ## convert gdb table to numpy array to Pandas DF:
    fieldList = [field.name for field in arcpy.ListFields(netPPA_mem_dist)]
    pattern = r'OBJECTID|RESOLVE_ZONE|Area|NEAR_DIST\S|STATE|MW'
    fieldList = [x for x in fieldList if re.search(pattern, x)] 
    
    ## convert to pandas dataframe
    df_netPPA = pandas.DataFrame(arcpy.da.TableToNumPyArray(netPPA_mem_dist, fieldList))
    
    ## Use the correct zone field for each scenario (RESOLVE_ZONE or wall to wall-state)
    if zoneType == "state":
        zoneFieldName_loop = "STATE"
    elif zoneType == "OOS_RESOLVEZONE":
        zoneFieldName_loop = "RESOLVE_ZONE"
        ## IF California RESOLVE_ZONE field, then append technology to end of RESOLVE_ZONE name:
    elif zoneType == "CA_RESOLVEZONE":
        zoneFieldName_loop = "RESOLVE_ZONE"
        df_netPPA["RESOLVE_ZONE"] =  df_netPPA['RESOLVE_ZONE'].astype(str) + "_" + tech
    
    ## merge adjustment factor df and potential project area df--keep only zones that are in the RESOLVE supply curve
    ## drop duplicate rows (because there are two Pacific_Northwest_Wind columns due to Oregon and Washington are two rows;
    ## this causes the inner join to result in duplicated rows; however, these rows will be kept when the zone is state)
    #in_df_CFadj_select_tech = in_df_CFadj_select_tech[[zoneFieldName_loop, 'CF_adj_Cat1', 'CF_adj_Cat2', 'CF_adj_Cat3', 'CF_adj_Cat4']]
    in_df_CFadj_select_tech = in_df_CFadj_select_tech.drop_duplicates(zoneFieldName_loop)
    
    df_netPPA_adj = pandas.merge(df_netPPA, in_df_CFadj_select_tech, how= 'inner', on = zoneFieldName_loop)
    
    ## Calculate corrected CF for each PPA for each scenario 
    #df_netPPA_adj["CF_avg_adj"] =  df_netPPA_adj['CF_avg_' + cat]*df_netPPA_adj['CF_adj_' + cat]

    ## Calculate the Mwh from the MW and CF_adj_Cat1 (any of the CF_adj_Cat%% fields work because they are all the same capacity factors for geothermal)
    df_netPPA_adj["MWh"] =  df_netPPA_adj["MW"]*df_netPPA_adj["CF_adj_Cat1"]*annualHrs
    
    ## Calculate the transmission area using tx distance and line width = 0.076 km; 
    df_netPPA_adj["txArea"] =  df_netPPA_adj["NEAR_DIST_Tx"]/1000*in_txWidth_km
    
    ## Calculate total tx area adjusted by the size of generation ()
    ## To avoid systematically reducing the total land use efficiency (MWh km-2) of smaller development zones 
    ## as a result of a fixed interconnection area, we applied a correction factor to the interconnection area 
    ## using the ratio of the development zone area (as small as 2 km2) to the largest possible development 
    ## zone area (25 km2).”) e.g., if a potential project area is 10 km and the largest is 25, then the total \
    ## tx area was multiplied by 10/25 or ⅖. 
    
    in_largestZoneArea_km2 = max(df_netPPA_adj["Area"])
    df_netPPA_adj["txAreaAdj"] =  df_netPPA_adj["txArea"]*(df_netPPA_adj["Area"]/in_largestZoneArea_km2)

    ## Calculate average MWh/km2 (total area = tx + gen)
    df_netPPA_adj["totArea"] =  df_netPPA_adj["txAreaAdj"] + df_netPPA_adj["Area"]
    df_netPPA_adj["avgMWhperKm2"] =  df_netPPA_adj["MWh"]/df_netPPA_adj["totArea"]
    
    ## sort the df by ranking potential project areas by 1) Whether netREN == 1 (ranked first), 
    ## (2) by highest to lowest MWh/km2
    #sort by df_netPPA_adj["netREN"] first, then df_netPPA_adj["avgMWhperKm2" + cat] second. 
    
    ## Add column with unique zone ID
    df_netPPA_adj["zoneID_num"] = df_netPPA_adj.index + 1
    df_netPPA_adj["zoneID"] = zoneType + "_" + df_netPPA_adj["zoneID_num"].map(str)
    
    ## save unsorted supply curve to csv 
    csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_" + scen + "_supplyCurve.csv")
    df_netPPA_adj.to_csv(csvFileName, index = False)
    
    ## join this df back to feature class attribute table
    arcpy.TableToTable_conversion(in_rows = csvFileName, out_path = spDisaggGDB_scratch, out_name = "tempTable")
    
    arcpy.CopyFeatures_management(in_features = netPPA_mem_dist, \
                                  out_feature_class = netPPA)
    
    fieldList = ["CF_adj_" + cat, "MW", \
         "MWh", "txArea", "txAreaAdj", "totArea", "avgMWhperKm2", "zoneID"]
    
    ## join attribute calculations back to the feature class
    arcpy.JoinField_management(in_data = netPPA, in_field = "OBJECTID" , \
                             join_table = os.path.join(spDisaggGDB_scratch, "tempTable"), join_field = "OBJECTID",\
                             fields = fieldList )
    print("finished with " + netPPA)
    print("")
    
    return netPPA

#######################################################################################################
## E. Sort supply curve and select CPAs for each Zone or state for each scenario
#######################################################################################################

def selectSites(zoneType, siteSuit, zoneName, sortingCol_ls, scenarioName, scenarioName_nospaces, in_existingMWh_df, df_RESOLVE_targets, ssList, QA_df):
    
    ## for each Zone rank the siteSuit table 
    ## Get the unique zone names
    zoneList = set(siteSuit[zoneName])
    for zone in zoneList:
        print(" " + zone)
        siteSuitZone = siteSuit.loc[siteSuit[zoneName] == zone]
        
        ## sort the zone by avgMWhperKm2 + cat
        siteSuitZone_sorted = siteSuitZone.sort_values(by = sortingCol_ls, axis=0, ascending=False)
        
        siteSuitZone_sorted = siteSuitZone_sorted.reset_index(drop=True)
        
        ## Calculate the cumulative MWh 
        siteSuitZone_sorted["MWh_cum"] = siteSuitZone_sorted.MWh.cumsum()
        
        ## retrieve the MWh target (either total or selected) from the RESOLVE outputs CSV
        target = df_RESOLVE_targets.loc[df_RESOLVE_targets["RESOLVE Resource"] == zone, scenarioName].iloc[0]
        
        if np.isnan(target) or target == 0:
            ## skip site selection if there is no target for this zone
            print("  No target for " + zone)
            totalMWh = "NaN"
            diff = "NaN"
            perDiff = "NaN"
            netTarget = target
        else:
            ## if it's CA's then the target is total, so subtract the existing MWh from total
            ## does not apply to geothermal, the input for this argument for geothermal will be = ""
            if zoneType == "CA_RESOLVEZONE": 
                ## retrieve the existing MWh from saved CSV calculated earlier
                existingMWh_series = in_existingMWh_df.loc[in_existingMWh_df["RESOLVE_ZONE"] == zone, "MWh"]
                
                if len(existingMWh_series.index) == 0:
                    existingMWh = 0
                elif len(existingMWh_series.index) > 1:
                    existingMWh = existingMWh_series.sum()
                else:
                    existingMWh = existingMWh_series.iloc[0]
                    
                ## subtract the calculated existing MWh (from footprints) from the target
                netTarget = target - existingMWh
                
            ## if it's OOS (QRA or w2w), then the target is selected Mwh from RESOLVE outputs 
            else:
                netTarget = target
        
            ## Select the sites that meet the MWh target
            if netTarget >0:
                siteSuitZone_sorted[scenarioName_nospaces] = siteSuitZone_sorted["MWh_cum"] < netTarget
                ## select the marginal project area to ensure that the target is met: 
                ## the below line finds the id of the maximum selected project area and selects the next project area (index + 1) by assigning it true
                
                if siteSuitZone_sorted.loc[siteSuitZone_sorted[scenarioName_nospaces] == True]["MWh_cum"].empty:
                    indexMax_selected = -1
                else:
                    indexMax_selected = siteSuitZone_sorted.loc[siteSuitZone_sorted[scenarioName_nospaces] == True]["MWh_cum"].idxmax()
                indexMax_total = siteSuitZone_sorted["MWh_cum"].idxmax()
                
                if indexMax_selected < indexMax_total:
                    siteSuitZone_sorted.at[indexMax_selected + 1, scenarioName_nospaces] = True
                else:
                    print("  * Maximum number of sites was selected or there is no potential resource")
                    
                print("  Total number of rows is ", str(len(siteSuitZone_sorted.index)))
                print("  selected number of rows is ", str(siteSuitZone_sorted.loc[siteSuitZone_sorted[scenarioName_nospaces] == True]["MWh_cum"].idxmax() + 1))
                
                ## add to list of selected PPAs for each zone
                ssList.append(siteSuitZone_sorted)
                
                ## Calculate the sum and then add the sum to the table 
                print("  Net target is " + str(netTarget))
                totalMWh = siteSuitZone_sorted.loc[siteSuitZone_sorted[scenarioName_nospaces] == True]["MWh_cum"].max()
                print("  Selected MWh is " + str(totalMWh))
                ## calculate the difference between the target and the selected; negative value means the site selection process didn't choose enough sites
                diff = totalMWh - netTarget
                ## Calculate the percentage difference using target as denominator/base
                perDiff = diff/netTarget
                print("  Percentage difference is " + str(perDiff))
            else:
                totalMWh = "NaN"
                diff = "NaN"
                perDiff = "NaN"
                print("The existing generation exceeds the total generation from RESOLVE")
        
        ## Calculate Quality Assessment data frame (QA_df), which allows the selected sites total to be compared against the RESOLVE portfolio outputs
        ## This ensures that the site selection was performed accurately (not over or under selecting generation)
        ## assign to QA df using the following procuedure: .loc[row_indexer,col_indexer] = value
        QA_df.loc[QA_df["RESOLVE Resource"]==zone, scen] = netTarget
        QA_df.loc[QA_df["RESOLVE Resource"]==zone, scen + "_selected"] = totalMWh
        ## assign to QA df using the following procuedure: .loc[row_indexer,col_indexer] = value
        QA_df.loc[QA_df["RESOLVE Resource"]==zone, scen + "_diff"] = diff
        ## assign to QA df using the following procuedure: .loc[row_indexer,col_indexer] = value
        QA_df.loc[QA_df["RESOLVE Resource"]==zone, scen + "_perDiff"] = perDiff
            
    return ssList, QA_df

'''
#######################################################################################################
## --------------------- III. RUN SITE SELECTION FUNCTIONS FOR EACH TECHNOLOGY ------------------------
#######################################################################################################

PURPOSE: Apply functions from PART II to each technology and RESOLVE portfolio/sceanrio
'''
## Create scenario list for constrained and unconstrained (OOS = constrained; state = unconstrained; CA = CA only)
state_scenList = ["Full WECC xW2W No Cap Basecase",\
                "Part WECC xW2W No Cap Basecase",\
                 "Full WECC xW2W No Cap highDER", "Full WECC xW2W No Cap lowBatt"]
        
CA_scenList = ["In-State x Capped Basecase",  "Full WECC x Capped Basecase", "Part WECC x Capped Basecase", \
                        "In-State x Capped highDER", "Full WECC x Capped highDER", "Part WECC x Capped highDER", \
                        "In-State x Capped lowBatt", "Full WECC x Capped lowBatt", "Part WECC x Capped lowBatt",\
                        "In-State BaseUsex Basecase", "Full WECC BaseUsex Basecase", "Part WECC BaseUsex Basecase", \
                         "In-State BaseUsex highDER", "Full WECC BaseUsex highDER", "Part WECC BaseUsex highDER", \
                         "In-State BaseUsex lowBatt",  "Full WECC BaseUsex lowBatt", "Part WECC BaseUsex lowBatt",\
                        "In-State xW2W No Cap Basecase",\
                        "Full WECC xW2W No Cap Basecase",\
                        "Part WECC xW2W No Cap Basecase",\
                         "In-State xW2W No Cap highDER", "Full WECC xW2W No Cap highDER", \
                         "In-State xW2W No Cap lowBatt", "Full WECC xW2W No Cap lowBatt"]

OOS_scenList = ["Full WECC x Capped Basecase", "Part WECC x Capped Basecase", \
                        "Full WECC x Capped highDER", "Part WECC x Capped highDER", \
                        "Full WECC x Capped lowBatt", "Part WECC x Capped lowBatt",\
                       "Full WECC BaseUsex Basecase", "Part WECC BaseUsex Basecase", \
                             "Full WECC BaseUsex highDER", "Part WECC BaseUsex highDER", \
                             "Full WECC BaseUsex lowBatt", "Part WECC BaseUsex lowBatt"]

#######################################################################################################
## A. Implement site selection functions for Geothermal
#######################################################################################################

## for Quality assessment data frame: create an empty pandas df with the RESOLVE ZONE names in the rows and the scenario names in the columns
## Quality assessment values are calculated in the selectSites function.
QA_df_output = pandas.DataFrame(columns = df_RESOLVEscenarios_selected.columns, index = df_RESOLVEscenarios_selected.index)
QA_df_output["RESOLVE Resource"] = df_RESOLVEscenarios_selected["RESOLVE Resource"]
   
# Loop over all the environmental categories and loop over each region (CA, OOS, Statewide) to get full suite of scenarios
for cat in ft_ls:
    for zoneType in zoneType_ls:
        print("")
        print("*****Technology: " + tech)
        print("**** Working on " + cat + " and " + zoneType)       
        df_RESOLVEscenarios_type = df_RESOLVEscenarios_selected
        
        if zoneType == "state":
            scenList = state_scenList
        
        if zoneType == "CA_RESOLVEZONE":
            scenList = CA_scenList

        if zoneType == "OOS_RESOLVEZONE":
            scenList = OOS_scenList
        
        for scen in scenList:
            
            scen = scen.replace("x", cat)
            print("")
            print(scen)
                
            ## only if the scenario is found in the RESOLVE output csv (only to control for the fact that not cateogires were run with sensivities under the w2w geography)
            if scen in df_RESOLVEscenarios_total.columns: 

                scenName_field = scen.replace(" ", "_").replace("-", "")
                
                '''## FUNCTION A: erase existing power plants '''
                outErase = eraseExistingPP(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field,\
                                           in_existingWind = "", in_existingPV_CA = "",\
                                           in_existingPV_OOS = "", in_selectedSitesList = [], calcArea ="")
                
                '''## FUNCTION C-E: calc tx distance and other attributes '''        
                calcAttributes_geothermal(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field, \
                               in_existingTxSubList = existingTxSubList, \
                               in_df_CFadj_select_tech = df_CFadj_select_tech, in_lue = lue, \
                               in_txWidth_km = txWidth_km, in_largestZoneArea_km2 = largestZoneArea_km2)
                
                #### retreive the supply curve saved as csv into a pandas df:
                df_netPPA = pandas.read_csv(os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] +"_" + scenName_field +  "_supplyCurve.csv"))
               
                ## select zones
                selectedSitesList, QA_df_output = selectSites(zoneType = "", siteSuit = df_netPPA, zoneName  = "RESOLVE_ZONE", sortingCol_ls = ["avgMWhperKm2"], scenarioName = scen, \
                                            scenarioName_nospaces = scenName_field, in_existingMWh_df = "", \
                                            df_RESOLVE_targets = df_RESOLVEscenarios_type, ssList = list(), QA_df = QA_df_output)
        
                ## combine list elements into one df                
                if selectedSitesList:
                    selectedSites_df = pandas.concat(selectedSitesList)                    
                else:
                    selectedSites_df = pandas.DataFrame(columns= ["zoneID", scenName_field])
                    print(" NO TARGETS FOR THIS GEOGRAPHY FOR THIS SCENARIO")
                    
                ## save selected sites to csv in the supplyCurves folder and named using the scenario 
                csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_" + scenName_field + "_selectedSites.csv")
                selectedSites_df.to_csv(csvFileName, index = False)
                
                ## join this df back to feature class attribute table
                arcpy.TableToTable_conversion(in_rows = csvFileName, out_path = spDisaggGDB_scratch, out_name = "tempTable")
                
                ## select these sites from the feature class by joining the scenario field and then and then save it to a  feature class
                
                ## Select sites from CA PPAs
                netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field)
                
                ## if the scenName_field  already exists, delete before joining fields
                netPPA_fieldList = [field.name for field in arcpy.ListFields(netPPA)]
                if scenName_field in netPPA_fieldList:
                    print(" Deleting existing field: " + scenName_field)
                    arcpy.DeleteField_management(netPPA, scenName_field)
                    
                arcpy.JoinField_management(in_data = netPPA, in_field = "zoneID" , \
                                         join_table = os.path.join(spDisaggGDB_scratch, "tempTable"), join_field = "zoneID",\
                                         fields = [scenName_field])
                
                ## select the sites that have True 
                arcpy.Select_analysis(in_features = netPPA, out_feature_class = netPPA + "_selected", \
                                               where_clause=  scenName_field + " = 'True'") 
                
                ## copy the netPPA to another GDB
                arcpy.CopyFeatures_management(netPPA, os.path.join(spDisaggGDB_scratch, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field))
                
                ## Delete the netPPA feature class
                arcpy.Delete_management(in_data = netPPA)   

## Save QA to csv for checking:
QA_df_output.to_csv(os.path.join(spDisaggFolder, "supplyCurves", "QA_df_output.csv")) ## originally named QA_geothermal.csv


#######################################################################################################
## B. Implement site selection functions for WIND
#######################################################################################################

## Read the QA_df_output file that was saved to disc and append to it
QA_df_output = pandas.read_csv(os.path.join(spDisaggFolder, "supplyCurves", "QA_df_output.csv"))
tech = "Wind"

if tech == "Wind":
    ## Set WIND CPA paths:
    ft_ls = {"Cat1" : "wind_0_03_nonEnv_r3_cat1b_singlepart_gt1km2",\
            "Cat2" : "wind_0_03_nonEnv_r3_cat2f_singlepart_gt1km2",\
            "Cat3" : "wind_0_03_nonEnv_r3_cat3c_singlepart_gt1km2", \
             "Cat4": "wind_0_03_nonEnv_r3_cat4_singlepart_gt1km2"}
    CF = os.path.join(mainDir, "dataCollection", "siteSuitabilityInputs_nonEnv.gdb\\CF_WINDtoolkit_NREL_IDW_masked_NoDataVals_250m")
    zoneFieldName_RESOLVE = "RESOLVE_ZONE_wind_1"
    lue = 6.1 ## MW/km2
    df_CFadj_select_tech = df_CFadj_select.loc[df_CFadj_select['Technology'] == tech]
    df_CFadj_select_w2w_tech = df_CFadj_select_w2w.loc[df_CFadj_select_w2w['Technology'] == tech]

# Loop over all the categories and loop over each region (CA, OOS, Statewide)
for cat in ft_ls:
    for zoneType in zoneType_ls:
        print("")
        print("*****Technology: " + tech)
        print("**** Working on " + cat + " and " + zoneType)        
        
        if zoneType == "state":
            scenList = state_scenList
            existingMWh_df = pandas.read_csv(existingMWh_wind_states_csv)
            df_RESOLVEscenarios_type = df_RESOLVEscenarios_selected
            df_CFadj_select_tech_scen = df_CFadj_select_w2w_tech
        
        if zoneType == "CA_RESOLVEZONE":
            scenList = CA_scenList
            existingMWh_df = pandas.read_csv(existingMWh_wind_RESOLVEZONE_csv)
            df_RESOLVEscenarios_type = df_RESOLVEscenarios_total
            df_CFadj_select_tech_scen = df_CFadj_select_tech

        if zoneType == "OOS_RESOLVEZONE":
            scenList = OOS_scenList
            existingMWh_df = pandas.read_csv(existingMWh_wind_RESOLVEZONE_csv)
            df_RESOLVEscenarios_type = df_RESOLVEscenarios_selected
            df_CFadj_select_tech_scen = df_CFadj_select_tech
        
        for scen in scenList:
            
            scen = scen.replace("x", cat)
            print("")
            print(scen)
            scenName_field = scen.replace(" ", "_").replace("-", "")
            
            csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_" + scenName_field + "_selectedSites.csv")
        
            ## only if the scenario is found in the RESOLVE output csv (only to control for the fact that not cateogires were run with sensivities under the w2w geography)
            if scen in df_RESOLVEscenarios_total.columns and not(os.path.isfile(csvFileName)): 
            #if scen in df_RESOLVEscenarios_total.columns: 
                
                '''## FUNCTION A: erase existing power plants '''
                ## Identify the selected geothermal resources feature class
                geothermalSelectedSites = os.path.join(spDisaggGDB, "geothermal_" + catFileDict_geothermal[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field + "_selected")
                
                if arcpy.Exists(geothermalSelectedSites):
                    selectedSitesList = [geothermalSelectedSites]
                ## if not geothermal resources were selected in this scenario, then set the variable to an empty list
                else:
                    selectedSitesList = []
                
                outErase = eraseExistingPP(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field,\
                                           in_existingWind = existingWind, in_existingPV_CA = existingPV_CA,\
                                           in_existingPV_OOS = existingPV_OOS, in_selectedSitesList = selectedSitesList, calcArea = "Yes")
                
                '''## FUNCTION B: tag PPAs close to netREN (point locations) '''
                tagPPAnearNetREN(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field, \
                                 in_netREN_wind_list = netREN_wind_list, in_netREN_PV = netREN_PV, \
                                 in_netRENthreshold_m = netRENthreshold_m)
                
                '''## FUNCTION C: calc tx distance and other attributes'''        
                calcAttributes(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field, \
                               in_existingTxSubList = existingTxSubList, in_CF = CF, \
                               in_df_CFadj_select_tech = df_CFadj_select_tech_scen, in_lue = lue, \
                               in_txWidth_km = txWidth_km, in_largestZoneArea_km2 = largestZoneArea_km2)
                
                #### retrieve the supply curve saved as csv into a pandas df:
                df_netPPA = pandas.read_csv(os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] +"_" + scenName_field +  "_supplyCurve.csv"))
               
                '''## FUNCTION E: select sites'''        
                ## select zones
                selectedSitesList, QA_df_output = selectSites(zoneType = zoneType, siteSuit = df_netPPA, zoneName  = "RESOLVE_ZONE", \
                                                               sortingCol_ls = ["netREN", "avgMWhperKm2"], scenarioName = scen, \
                                            scenarioName_nospaces = scenName_field, in_existingMWh_df = existingMWh_df, \
                                            df_RESOLVE_targets = df_RESOLVEscenarios_type, ssList = list(), QA_df = QA_df_output)
        
                ## combine list elements into one df                
                if selectedSitesList:
                    selectedSites_df = pandas.concat(selectedSitesList)                    
                else:
                    selectedSites_df = pandas.DataFrame(columns= ["zoneID", scenName_field])
                    print(" NO TARGETS FOR THIS GEOGRAPHY FOR THIS SCENARIO")
                    
                ## save selected sites to csv in the supplyCruves folder and named using the scenario 
                csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_" + scenName_field + "_selectedSites.csv")
                selectedSites_df.to_csv(csvFileName, index = False)
                
                ## join this df back to feature class attribute table
                arcpy.TableToTable_conversion(in_rows = csvFileName, out_path = spDisaggGDB_scratch, out_name = "tempTable")
                
                ## select these sites from the feature class by joining the scenario field and then and then save it to a  feature class
                
                ## Select sites from CA PPAs
                netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field)
                
                ## if the scenName_field already exists, delete before joining fields
                netPPA_fieldList = [field.name for field in arcpy.ListFields(netPPA)]
                if scenName_field in netPPA_fieldList:
                    print(" Deleting existing field: " + scenName_field)
                    arcpy.DeleteField_management(netPPA, scenName_field)
                    
                arcpy.JoinField_management(in_data = netPPA, in_field = "zoneID" , \
                                         join_table = os.path.join(spDisaggGDB_scratch, "tempTable"), join_field = "zoneID",\
                                         fields = [scenName_field])
                
                ## select the sites that have True 
                arcpy.Select_analysis(in_features = netPPA, out_feature_class = netPPA + "_selected", \
                                               where_clause=  scenName_field + " = 'True'") 
                
                ## copy the netPPA to another GDB
                arcpy.CopyFeatures_management(netPPA, os.path.join(spDisaggGDB_scratch, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field))
                
                ## Delete the netPPA feature class
                arcpy.Delete_management(in_data = netPPA)   

## write updated QA file to disc, now with wind results appended
QA_df_output.to_csv(os.path.join(spDisaggFolder, "supplyCurves", "QA_df_output.csv")) ## originally named QA_geothermal.csv

#######################################################################################################
## C. Implement site selection functions for SOLAR
#######################################################################################################

QA_df_output = pandas.read_csv(os.path.join(spDisaggFolder, "supplyCurves", "QA_df_output.csv"))

tech = "Solar"
if tech == "Solar":
    ## SOLAR:
    ft_ls = {"Cat1" : "solarPV_0_0_nonEnv_r1_cat1b_singlepart_gt1km2",\
            "Cat2" : "solarPV_0_0_nonEnv_r1_cat2f_singlepart_gt1km2",\
            "Cat3" : "solarPV_0_0_nonEnv_r1_cat3c_singlepart_gt1km2", \
             "Cat4": "solarPV_0_0_nonEnv_r1_cat4_singlepart_gt1km2"}
    CF = os.path.join(mainDir, "dataCollection", "siteSuitabilityInputs_nonEnv.gdb\\CF_FixedPV_SAM_AC_CF_250m")
    zoneFieldName_RESOLVE = "RESOLVE_ZONE_solar_1"
    lue = 30 ## MW/km2
    df_CFadj_select_tech = df_CFadj_select.loc[df_CFadj_select['Technology'] == tech]
    df_CFadj_select_w2w_tech = df_CFadj_select_w2w.loc[df_CFadj_select_w2w['Technology'] == tech]
    
    
# Loop over all the categories and loop over each region (CA, OOS, Statewide)
for cat in ft_ls:
    for zoneType in zoneType_ls:
        print("")
        print("*****Technology: " + tech)
        print("**** Working on " + cat + " and " + zoneType)       
        
        if zoneType == "state":
            scenList = state_scenList
            existingMWh_df = pandas.read_csv(existingMWh_PV_states_csv)
            df_RESOLVEscenarios_type = df_RESOLVEscenarios_selected
            df_CFadj_select_tech_scen = df_CFadj_select_w2w_tech
        
        if zoneType == "CA_RESOLVEZONE":
            scenList = CA_scenList
            existingMWh_df = pandas.read_csv(existingMWh_PV_RESOLVEZONE_csv)
            df_RESOLVEscenarios_type = df_RESOLVEscenarios_total
            df_CFadj_select_tech_scen = df_CFadj_select_tech

        if zoneType == "OOS_RESOLVEZONE":
            scenList = OOS_scenList
            existingMWh_df = pandas.read_csv(existingMWh_PV_RESOLVEZONE_csv)
            df_RESOLVEscenarios_type = df_RESOLVEscenarios_selected
            df_CFadj_select_tech_scen = df_CFadj_select_tech
        
        for scen in scenList:
            
            scen = scen.replace("x", cat)
            print("")
            print(scen)
                
            scenName_field = scen.replace(" ", "_").replace("-", "")
            
            csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_" + scenName_field + "_selectedSites.csv")

            
            ## only if the scenario is found in the RESOLVE output csv (only to control for the fact that not cateogires were run with sensivities under the w2w geography)
            if scen in df_RESOLVEscenarios_total.columns and not(os.path.isfile(csvFileName)): 
            #if scen in df_RESOLVEscenarios_total.columns: 
                
                '''## FUNCTION A: erase existing power plants '''
                ## Identify the selected geothermal resources feature class
                geothermalSelectedSites = os.path.join(spDisaggGDB, "geothermal_" + catFileDict_geothermal[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field + "_selected")
                windSelectedSites = os.path.join(spDisaggGDB, "wind_0_03_nonEnv_r3_" + catFileDict_windSolar[cat] + "_singlepart_gt1km2" + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field + "_selected")
                
                coLocScen = "W2W"
                if coLocScen in scen:
                    windSelectedSites = ""
                
                if arcpy.Exists(geothermalSelectedSites):
                    if arcpy.Exists(windSelectedSites):
                        selectedSitesList = [geothermalSelectedSites, windSelectedSites]
                        print(" Erasing selected wind and geothermal sites")
                    else:
                        selectedSitesList = [geothermalSelectedSites]
                        print(" Erasing selected geothermal sites")
                elif arcpy.Exists(windSelectedSites):
                    selectedSitesList = [windSelectedSites]       
                    print(" Erasing selected wind sites")
                
                outErase = eraseExistingPP(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field,\
                                           in_existingWind = existingWind, in_existingPV_CA = existingPV_CA,\
                                           in_existingPV_OOS = existingPV_OOS, in_selectedSitesList = selectedSitesList, calcArea = "Yes")
                
                '''## FUNCTION B: tag PPAs close to netREN (point locations) '''
                tagPPAnearNetREN(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field, \
                                 in_netREN_wind_list = netREN_wind_list, in_netREN_PV = netREN_PV, \
                                 in_netRENthreshold_m = netRENthreshold_m)
                
                '''## FUNCTION C: calc tx distance and other attributes '''        
                calcAttributes(tech = tech, cat = cat, zoneType = zoneType, scen = scenName_field, \
                               in_existingTxSubList = existingTxSubList, in_CF = CF, \
                               in_df_CFadj_select_tech = df_CFadj_select_tech_scen, in_lue = lue, \
                               in_txWidth_km = txWidth_km, in_largestZoneArea_km2 = largestZoneArea_km2)
                
                #### retreive the supply curve saved as csv into a pandas df:
                df_netPPA = pandas.read_csv(os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] +"_" + scenName_field +  "_supplyCurve.csv"))
               
                '''## FUNCTION E: select sites'''    
                ## select zones
                selectedSitesList, QA_df_output = selectSites(zoneType = zoneType, siteSuit = df_netPPA, zoneName  = "RESOLVE_ZONE", \
                                                               sortingCol_ls = ["netREN", "avgMWhperKm2"], scenarioName = scen, \
                                            scenarioName_nospaces = scenName_field, in_existingMWh_df = existingMWh_df, \
                                            df_RESOLVE_targets = df_RESOLVEscenarios_type, ssList = list(), QA_df = QA_df_output)
        
                ## combine list elements into one df                
                if selectedSitesList:
                    selectedSites_df = pandas.concat(selectedSitesList)                    
                else:
                    selectedSites_df = pandas.DataFrame(columns= ["zoneID", scenName_field])
                    print(" NO TARGETS FOR THIS GEOGRAPHY FOR THIS SCENARIO")
                    
                ## save selected sites to csv in the supplyCruves folder and named using the scenario 
                csvFileName = os.path.join(spDisaggFolder, "supplyCurves", ft_ls[cat] + zoneType_ls[zoneType] + "_" + scenName_field + "_selectedSites.csv")
                selectedSites_df.to_csv(csvFileName, index = False)
                
                ## join this df back to feature class attribute table
                arcpy.TableToTable_conversion(in_rows = csvFileName, out_path = spDisaggGDB_scratch, out_name = "tempTable")
                
                ## select these sites from the feature class by joining the scenario field and then and then save it to a  feature class
                
                ## Select sites from CA PPAs
                netPPA = os.path.join(spDisaggGDB, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field)
                
                ## if the scenName_field  already exists, delete before joining fields
                netPPA_fieldList = [field.name for field in arcpy.ListFields(netPPA)]
                if scenName_field in netPPA_fieldList:
                    print(" Deleting existing field: " + scenName_field)
                    arcpy.DeleteField_management(netPPA, scenName_field)
                    
                arcpy.JoinField_management(in_data = netPPA, in_field = "zoneID" , \
                                         join_table = os.path.join(spDisaggGDB_scratch, "tempTable"), join_field = "zoneID",\
                                         fields = [scenName_field])
                
                ## select the sites that have True 
                arcpy.Select_analysis(in_features = netPPA, out_feature_class = netPPA + "_selected", \
                                               where_clause=  scenName_field + " = 'True'") 
                
                ## copy the netPPA to another GDB
                arcpy.CopyFeatures_management(netPPA, os.path.join(spDisaggGDB_scratch, ft_ls[cat] + zoneType_ls[zoneType] + netPPAsuffix + "_" + scenName_field))
                
                ## Delete the netPPA feature class
                arcpy.Delete_management(in_data = netPPA)   

## write updated QA file to disc, now with solar results appended        
QA_df_output.to_csv(os.path.join(spDisaggFolder, "supplyCurves", "QA_df_output.csv")) ## originally named QA_geothermal.csv

