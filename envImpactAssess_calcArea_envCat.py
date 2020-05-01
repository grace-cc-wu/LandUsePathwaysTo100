# -*- coding: utf-8 -*-
"""
Created on Thu Jan 31 16:28:59 2019

@author: Grace

PURPOSE: Calculates the area of selected project areas that overlap with specific environmental metrics
as part of the strategic envrionmental assessment
"""

##--------------------------------Preamble ----------------------------------
import arcpy
import numpy
import time
import os
import pandas as pd
start_time = time.time()
print(start_time)
# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")
from arcpy import env
from arcpy.sa import *
import arcpy.cartography as CA
arcpy.env.overwriteOutput = True

'''
######################################################
################ SET INPUTS FOR RUNS #################
######################################################
'''
## change the infrastructure type with each run: 
infrastructureType = "tx_longHaul" ## "tx" or "selSite" or "tx_longHaul"

## List scenarios
scenList = ["In-State x Capped Basecase",  "Full WECC x Capped Basecase", "Part WECC x Capped Basecase", \
                        "In-State x Capped highDER", "Full WECC x Capped highDER", "Part WECC x Capped highDER", \
                        "In-State x Capped lowBatt", "Full WECC x Capped lowBatt", "Part WECC x Capped lowBatt",\
                        "In-State BaseUsex Basecase", "Full WECC BaseUsex Basecase", "Part WECC BaseUsex Basecase", \
                         "In-State BaseUsex highDER", "Full WECC BaseUsex highDER", "Part WECC BaseUsex highDER", \
                         "In-State BaseUsex lowBatt",  "Full WECC BaseUsex lowBatt", "Part WECC BaseUsex lowBatt",\
                        "In-State xW2W No Cap Basecase", "Full WECC xW2W No Cap Basecase","Part WECC xW2W No Cap Basecase",\
                         "In-State xW2W No Cap highDER", "Full WECC xW2W No Cap highDER", "In-State xW2W No Cap lowBatt", "Full WECC xW2W No Cap lowBatt"]

## technologies
techList = ["Geothermal", "Wind", "Solar"]

mainDir = "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\"
df_RESOLVEscenarios_total = pd.read_csv(os.path.join(mainDir, "RESOLVEoutputs", "Results Summary Workbook_v11_20181214_total.csv"))
CA_superCREZ_fc = os.path.join(mainDir, "dataCollection\\siteSuitabilityInputs_nonEnv.gdb", "SUPERCREZ_proj_CA_RESOLVE_ZONE")
state_fc = os.path.join(mainDir, "dataCollection\\siteSuitabilityInputs_nonEnv.gdb", "stateBound_baja")
QRA_fc = os.path.join(mainDir, "dataCollection\\siteSuitabilityInputs_nonEnv.gdb", "QRA_proj")

## column order of final csv
master_df_col_list = ["tech", "envCat", "scenario", "selSites", "region", "envData","area_envData_km2", "area_allSelSites_km2", "percent_selSites"]

## empty dataframe of results
master_df = pd.DataFrame(columns = master_df_col_list)

if infrastructureType == "selSite":
    ## selected sites folder
    allFCfolder = "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\spatialDisaggregation\\selectedsites_cleaned_shp"
    allFCList = [file for file in os.listdir(allFCfolder) if file.endswith(".shp")]
    suffix = ".shp"
    suffix_solar = ".shp"
    regionField_RESOLVEZONE = "RESOLVE_ZO"
    
if infrastructureType == "tx":
    ## selected sites folder
    spDisaggFolder = os.path.join(mainDir,"spatialDisaggregation\\") #^^
    allFCfolder = os.path.join(spDisaggFolder, "LeastCostPath\\SD_LCP_122018\\SD_LCP_diss")    
    allFCList = [file for file in os.listdir(allFCfolder) if file.endswith(".shp")]
    suffix = "_copy_LCP_erasedBuffLine_diss.shp"
    suffix_solar = "_LCP_erasedBuffLine_diss.shp"
    regionField_RESOLVEZONE = "RESOLVE_ZO"
    
if infrastructureType == "tx_longHaul":
    ## selected sites folder
    #spDisaggFolder = os.path.join(mainDir,"spatialDisaggregation\\") #^^ C:\Users\Grace\Documents\TNC_beyond50\PathTo100\dataCollection\existingEnergyInfrastructure\BLMRecentlyApprovedProjects
    allFCList = [file for file in os.listdir(allFCfolder) if file.endswith(".shp")]
    suffix = "_copy_LCP_erasedBuffLine_diss.shp"
    suffix_solar = "_LCP_erasedBuffLine_diss.shp"
    regionField_RESOLVEZONE = "RESOLVE_ZO"
    scenList = ["placeholder"]
    
    
## Environmental data GDB
envDataGDB = "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envImpactAssessment\\EnvImpactUnionSubgroups.gdb"

## Create list of inputs and outputs to use for each env metric:
envDataLayerList = [{"envDataLayerName": "criticalHabitat_Union_sg5", "envDataGDB": envDataGDB, "envDataLabel": "criticalHabitat_SG05",\
      "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG05_df.csv", "catSubList" : ["Cat1", "Cat2"],\
      "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "WIND_SageGrouse_Union_sg6", "envDataGDB": envDataGDB, "envDataLabel": "sageGrouse_SG06",\
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG06_df.csv", "catSubList" : ["Cat1", "Cat2"], \
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "esri_justprime_250m_0267_sg7", "envDataGDB": envDataGDB, "envDataLabel": "primeFarmland_SG07",\
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG07_df.csv", "catSubList" : ["Cat1", "Cat2"], \
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "IBAs_April2018_Recognized_0110_sg8", "envDataGDB": envDataGDB, "envDataLabel": "IBAs_SG08", \
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG08_df.csv",  "catSubList" : ["Cat1", "Cat2"],
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "allWetlands_unioned_sg9", "envDataGDB": envDataGDB, "envDataLabel": "wetlands_SG09", \
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG09_df.csv", "catSubList" : ["Cat1", "Cat2"],\
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "BigGame_Union_sg10", "envDataGDB": envDataGDB, "envDataLabel": "bigGame_SG10", \
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG10_df.csv", "catSubList" : ["Cat1", "Cat2"],
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "Intactness_Union_dissolved_sg11", "envDataGDB": envDataGDB, "envDataLabel": "intactness_SG11", \
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG11_df.csv",  "catSubList" : ["Cat1", "Cat2", "Cat3"],\
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "Cat4_u_d_s_proj_dissolved.shp", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\Cat4\\", \
        "envDataLabel": "Cat4_SG04", "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG04_Cat4_df.csv", "catSubList" : ["Cat1", "Cat2", "Cat3"], \
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "Cat3_geotherm_excl_base_proj_dissolved.shp", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\Cat3\\", \
        "envDataLabel": "Cat3_SG03", "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG03_Cat3_Geothermal_df.csv", "catSubList" : ["Cat1", "Cat2"], \
        "techList": ["Geothermal"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "Cat3_solar_excl_base_proj_dissolved.shp", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\Cat3\\", \
        "envDataLabel": "Cat3_SG03", "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG03_Cat3_Solar_df.csv", "catSubList" : ["Cat1", "Cat2"], \
        "techList": ["Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "Cat3_wind", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\envCat_merged.gdb", \
        "envDataLabel": "Cat3_SG03", "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG03_Cat3_Wind_df.csv", "catSubList" : ["Cat1", "Cat2"], \
        "techList": ["Wind"],\
        "functionType": "erase"},\
   {"envDataLayerName": "Cat2_geo", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\envCat_merged.gdb", \
        "envDataLabel": "Cat2_SG02", "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG02_Cat2_Geothermal_df.csv", "catSubList" : ["Cat1"], \
        "techList": ["Geothermal"],\
        "functionType": "erase"},\
   {"envDataLayerName": "Cat2_solar", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\envCat_merged.gdb", \
        "envDataLabel": "Cat2_SG02", "resultsFileName" : "areaImpacted_"+ infrastructureType + "_SG02_Cat2_Solar_df.csv", "catSubList" : ["Cat1"], \
        "techList": ["Solar"],\
        "functionType": "erase"},\
   {"envDataLayerName": "Cat2_wind", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\envCat_merged.gdb", \
        "envDataLabel": "Cat2_SG02", "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG02_Cat2_Wind_df.csv", "catSubList" : ["Cat1"], \
        "techList": ["Wind"],\
        "functionType": "erase"},\
   {"envDataLayerName": "Cat1_wind", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\envCat_merged.gdb", \
        "envDataLabel": "Cat1_SG01", "resultsFileName" : "areaImpacted_"+ infrastructureType +"_SG01_Cat1_Wind_df.csv", "catSubList" : ["Cat1"], \
        "techList": ["Wind"],\
        "functionType": "erase"},\
   {"envDataLayerName": "Cat1_solar", "envDataGDB": "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\envData\\envCat_merged.gdb", \
        "envDataLabel": "Cat1_SG01", "resultsFileName" : "areaImpacted_"+ infrastructureType + "_SG01_Cat1_Solar_df.csv", "catSubList" : ["Cat1"], \
        "techList": ["Solar", "Geothermal"],\
        "functionType": "erase"},\
   {"envDataLayerName": "Belote_Corridors_34pt4528_0172_sg14", "envDataGDB": envDataGDB, "envDataLabel": "corridors_SG14", \
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG14_df.csv", "catSubList" : ["Cat1", "Cat2", "Cat3"],\
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "eagles_unioned_sg15", "envDataGDB": envDataGDB, "envDataLabel": "eagles_SG16", \
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG16_df.csv", "catSubList" : ["Cat1"],\
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"},\
   {"envDataLayerName": "tribalLands_unioned_sg15", "envDataGDB": envDataGDB, "envDataLabel": "tribal_SG15", \
        "resultsFileName" : "areaImpacted_" + infrastructureType + "_SG15_df.csv", "catSubList" : ["Cat1"],\
        "techList": ["Geothermal", "Wind", "Solar"],\
        "functionType": "intersect"}]

'''
#####################################################
####### FUNCTIONS FOR PERFORMING ANALYSIS  ##########
#####################################################

PURPOSE: Calculate the area of overlap between the selected project areas (SPAs)
and the environmental metric using one of two different approaches

A) Erase: erases the environmental metric feature class from the selected project areas
then calculates the difference between the original SPA extent and the result of the 
erase function to get the area of overlap. This method is faster for complex polygons

B) Intersect: creates a feature class that is the intersection of the SPA and the
envrionmental metric feature class, and thus directly calculates the overlapping area. 
This method is slower for complex polygons. 
'''

##################################################
## ------------ ERASE FUNCTION -----------------##
##################################################
def calcArea_erase_arcpy(selectSites_gdf, envData_gdf, areaField, regionField, envDataField, envDataName, selectedSitesField, selectedSitesFilename):
    
    ## Erase merged env category data
    sp_erased = arcpy.Erase_analysis(selectSites_gdf, envData_gdf, "in_memory/temp_erased")
    elapsed_time = (time.time() - start_time)/(60)
    print("Total time for completion: " + str(elapsed_time) + " minutes")
    ## Calculate new Area field 
    arcpy.AddField_management(sp_erased, "Area_remaining", "FLOAT")
    arcpy.CalculateField_management(in_table = sp_erased, field = "Area_remaining", \
                                    expression = "!Shape.Area@squarekilometers!", \
                                    expression_type = "PYTHON_9.3")
    
    ## convert erased gdb table to numpy array to Pandas DF:
    sp_erased_df = pd.DataFrame(arcpy.da.FeatureClassToNumPyArray(sp_erased, \
                                                                      [regionField, areaField, 'Area_remaining']))
    
    area_erased_regionSum_df = sp_erased_df.groupby([regionField])['Area_remaining'].sum().reset_index()
    
    ##### use the original (unerased selectedSites_gdf) feature/shapefile, convert to pd df and calculate the area_allSelSites_km2
    area_orig_df = pd.DataFrame(arcpy.da.FeatureClassToNumPyArray(selectSites_gdf,[regionField, areaField]))
    ## Calculate the sum by region
    area_orig_regionSum_df = area_orig_df.groupby([regionField])[areaField].sum().reset_index()
    
    ## merge the erased and original regionSum_df
    area_merged_df = area_erased_regionSum_df.merge(area_orig_regionSum_df, how = "outer", on = regionField)
    
    ## subtract Area_remaining from Area (original)
    area_merged_df["area_envData_km2"] = area_merged_df["Area"] - area_merged_df["Area_remaining"]
    
    ## rename fields as needed
    area_merged_df.rename(columns = {areaField: 'area_allSelSites_km2', regionField: 'region'}, inplace=True)
    ## assign new fields
    area_merged_df[envDataField] = envDataName
    area_merged_df[selectedSitesField] = selectedSitesFilename
    ## remove "Area_remaining" column
    area_merged_df.drop(["Area_remaining"], axis =1)
    
    area_merged_df["percent_selSites"] = area_merged_df["area_envData_km2"]/area_merged_df['area_allSelSites_km2']
    
    return area_merged_df

######################################################
## ------------ INTERSECT FUNCTION -----------------##
######################################################

def calcArea_intersect_arcpy(selectSites_gdf, envData_gdf, areaField, regionField, envDataField, envDataName, selectedSitesField, selectedSitesFilename):
    
    ## 1. Intersect
    sp_intersect = arcpy.Intersect_analysis(in_features = [selectSites_gdf, envData_gdf], \
                                         out_feature_class = "in_memory/temp_intersect")

    ## recalculate area after intersection
    arcpy.CalculateField_management(in_table = sp_intersect, field = areaField, \
                                    expression = "!Shape.Area@squarekilometers!", \
                                    expression_type = "PYTHON_9.3")
    
    ## convert gdb table to numpy array to Pandas DF:
    sp_intersect_df = pd.DataFrame(arcpy.da.FeatureClassToNumPyArray(sp_intersect, \
                                                                      [regionField, areaField]))

    intersect_sumByZone = sp_intersect_df.groupby([regionField])[areaField].sum().reset_index()
    
    selectSites_df = pd.DataFrame(arcpy.da.FeatureClassToNumPyArray(selectSites_gdf, \
                                                                      [regionField, areaField]))
    allZones = selectSites_df[regionField].unique()

    for zone in allZones:
        if zone not in intersect_sumByZone[regionField].tolist():
            intersect_sumByZone = pd.concat([intersect_sumByZone, pd.DataFrame(data = {regionField : [zone], areaField: [0]})], axis=0)
            
    ## 2. Create table of area sums of all selected sites
    area_df = selectSites_df.groupby([regionField])[[areaField]].sum().reset_index()
    
    area_df.rename(columns = {areaField: 'area_allSelSites_km2'}, inplace=True)
    
    ## 3. merge the two df
    intersect_sumByZone = intersect_sumByZone.merge(area_df, how = "inner", left_on=regionField, right_on=regionField)
            
    intersect_sumByZone[envDataField] = envDataName
    intersect_sumByZone[selectedSitesField] = selectedSitesFilename
    
    intersect_sumByZone.rename(columns = {areaField: 'area_envData_km2', regionField: "region" }, inplace=True)
    
    intersect_sumByZone["percent_selSites"] = intersect_sumByZone["area_envData_km2"]/intersect_sumByZone['area_allSelSites_km2']
    
    return intersect_sumByZone

'''
######################################################
############# APPLY FUNCTIONS IN LOOP ################
######################################################
'''
start_time = time.time()
print(start_time)

for envData in envDataLayerList:
    print("")
    print("========>> Env Data: " +  envData["envDataLayerName"])
    ## read envData as geodataframe
    envData_gdf = arcpy.CopyFeatures_management(os.path.join(envData["envDataGDB"], envData["envDataLayerName"]), "in_memory/envData")
    print(str((time.time() - start_time)/(60)) + " minutes")
    ## Create empty dataframe of results
    master_df = pd.DataFrame(columns = master_df_col_list)
    ## Save master_df to csv                
    resultsFileName = os.path.join("C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\envImpactAssessment\\", envData["resultsFileName"])
    functionType = envData["functionType"]
    
    if infrastructureType == "tx_longHaul":
        print("tx_longHaul")
        for line in allFCList:
            ## read selected sites (shp) as geodataframe
            sp = arcpy.CopyFeatures_management(os.path.join(allFCfolder, line), "in_memory/featureClasses")
            nrows = arcpy.GetCount_management(sp)[0]
            print("sp contains " + str(nrows) + " rows")
            
            if int(nrows) >0:
                
                if functionType == "intersect":
                    ## apply CalcArea function by zone
                    print("Intersecting")
                    area_df = calcArea_intersect_arcpy(selectSites_gdf = sp, envData_gdf =envData_gdf, areaField = "Area", \
                                                       regionField = "STATE", \
                                                       envDataField = "envData", envDataName = envData["envDataLabel"], \
                                                       selectedSitesField = "selSites", selectedSitesFilename = line)
                if functionType == "erase":
                    print("Erasing")
                    area_df = calcArea_erase_arcpy(selectSites_gdf = sp, envData_gdf = envData_gdf, areaField = "Area", \
                                                   regionField = "STATE", \
                                                   envDataField = "envData", envDataName = envData["envDataLabel"], \
                                                   selectedSitesField = "selSites", selectedSitesFilename = line)
    
                ## add technology
                area_df["tech"] = "tx_longHaul"
                ## add scenario name
                area_df["scenario"] = "none"
                ## add env cat
                area_df["envCat"] = "none"
                ## reorder fields:
                area_df = area_df[master_df_col_list]
                ## append area_df to master df
                master_df = pd.concat([master_df, area_df], axis = 0)
    
                print("Completed " + line)
                print(str((time.time() - start_time)/(60)) + " minutes")
    else:        
        for tech in envData["techList"]:
            ## categories
            if tech == "Geothermal":
                catList = {"Cat1" : "geothermal_cat1b", "Cat2" : "geothermal_cat2f",\
                            "Cat3" : "geothermal_cat3", "Cat4": "geothermal_cat4"}
                suffixFinal = suffix
    
            if tech == "Wind":
                catList = {"Cat1" : "wind_0_03_nonEnv_r3_cat1b_singlepart_gt1km2","Cat2" : "wind_0_03_nonEnv_r3_cat2f_singlepart_gt1km2",\
                            "Cat3" : "wind_0_03_nonEnv_r3_cat3c_singlepart_gt1km2", "Cat4": "wind_0_03_nonEnv_r3_cat4_singlepart_gt1km2"}
                suffixFinal = suffix
    
            if tech == "Solar":
                catList = {"Cat1" : "solarPV_0_0_nonEnv_r1_cat1b_singlepart_gt1km2","Cat2" : "solarPV_0_0_nonEnv_r1_cat2f_singlepart_gt1km2",\
                            "Cat3" : "solarPV_0_0_nonEnv_r1_cat3c_singlepart_gt1km2", "Cat4": "solarPV_0_0_nonEnv_r1_cat4_singlepart_gt1km2"}
                suffixFinal = suffix_solar
            
            print(tech)
            
            for cat in catList: 
                if cat in envData["catSubList"]:
                    print("============> Working on " + cat)
                    for scen in scenList:
                        scen = scen.replace("x", cat)
                        if scen in df_RESOLVEscenarios_total.columns: 
                            scenName_field = scen.replace(" ", "_").replace("-", "")                
                            print("")
                            geographyList = []
                            separator = "_" 
                            oos_RESOLVE_filename = separator.join([catList[cat], "PA", "OOS_RESOLVEZONE", "net", scenName_field, "selected"]) + suffixFinal
                            oos_STATE_filename = separator.join([catList[cat], "PA", "state", "net", scenName_field, "selected"]) + suffixFinal
                            instate_filename = separator.join([catList[cat], "PA", "CA_RESOLVEZONE", "net", scenName_field, "selected"]) + suffixFinal
        
                            if "W2W" in scenName_field and "InState" not in scenName_field:
                                ## append both state and in-state filenames to geoList
                                geographyList.append({"file": oos_STATE_filename, "regionField": "STATE"})
                                geographyList.append({"file": instate_filename, "regionField": regionField_RESOLVEZONE})
                                print("W2W scenario for " + oos_STATE_filename + " and " + instate_filename)
        
                            if "InState" in scenName_field:
                                ## append only state filename to geoList
                                geographyList.append({"file": instate_filename, "regionField": regionField_RESOLVEZONE})
                                print("InState scenario for " + instate_filename)
        
                            if any(txt in scenName_field for txt in ["Capped","BaseUseCat1"]) and "InState" not in scenName_field:
                                ## append both OOS RESOLVE ZONES and in-state filenames to geoList
                                geographyList.append({"file": oos_RESOLVE_filename, "regionField": regionField_RESOLVEZONE})
                                geographyList.append({"file": instate_filename, "regionField": regionField_RESOLVEZONE})
                                print("OOS RESOLVE scenario for " + oos_RESOLVE_filename + " and " + instate_filename)
        
                            ## loop through each element of geoList
                            for geography in geographyList:
                                ## if file is in the geodatabase and it has not already been analyzed
                                ## ex: "geothermal_cat1b_PA_CA_RESOLVEZONE_net_Part_WECC_Cat1_Capped_highDER_selectedcriticalHabitat_SG05" not in list of these in the master_df
                                if geography['file'] in allFCList: #and geography['file']+envData["envDataLabel"] not in (master_df["selSites"]+master_df['envData']).tolist():
                                    
                                    ## read selected sites (shp) as geodataframe
                                    sp = arcpy.CopyFeatures_management(os.path.join(allFCfolder, geography['file']), "in_memory/featureClasses")
                                    nrows = arcpy.GetCount_management(sp)[0]
                                    print("sp contains " + str(nrows) + " rows")
                                    
                                    if int(nrows) >0:
                                        
                                        if functionType == "intersect":
                                            ## apply CalcArea function by zone
                                            area_df = calcArea_intersect_arcpy(selectSites_gdf = sp, envData_gdf =envData_gdf, areaField = "Area", \
                                                                               regionField = geography['regionField'], \
                                                                               envDataField = "envData", envDataName = envData["envDataLabel"], \
                                                                               selectedSitesField = "selSites", selectedSitesFilename = geography['file'])
                                        if functionType == "erase":
                                            print("Erasing")
                                            area_df = calcArea_erase_arcpy(selectSites_gdf = sp, envData_gdf = envData_gdf, areaField = "Area", \
                                                                           regionField = geography['regionField'], \
                                                                           envDataField = "envData", envDataName = envData["envDataLabel"], \
                                                                           selectedSitesField = "selSites", selectedSitesFilename = geography['file'])
            
                                        ## add technology
                                        area_df["tech"] = tech
                                        ## add scenario name
                                        area_df["scenario"] = scenName_field
                                        ## add env cat
                                        area_df["envCat"] = cat
                                        ## reorder fields:
                                        area_df = area_df[master_df_col_list]
                                        ## append area_df to master df
                                        master_df = pd.concat([master_df, area_df], axis = 0)
        
                                        print("Completed " + geography["file"])
                                        print(str((time.time() - start_time)/(60)) + " minutes")
        
                                    ## if there are no rows in this feature class, then create an dummy row for the output file
                                    else:
                                        ## Create single row dataframe with NA for region and area_km2 to indicate that there are no selected sites for that scenario/geography
                                        area_df = pd.DataFrame(data = {"tech": [tech], "envCat": [cat], "scenario": [scenName_field], \
                                                                       "selSites": [geography['file']], "region": ["NA"], "envData": [envData["envDataLabel"]], \
                                                                       "area_envData_km2": ["NA"], "area_allSelSites_km2" : ["NA"], "percent_selSites": ["NA"]})
        
                                        ## append area_df to master df
                                        master_df = pd.concat([master_df, area_df], axis = 0)
        
                                        print("***There are no selected sites for empty " + geography["file"])
                                else:
                                    print("Not in gdb or already analyzed and in master_df: " + geography['file'])
                                    
                            print(str((time.time() - start_time)/(60)) + " minutes")
        
                            #print("Writing to csv")
                            #master_df.to_csv(path_or_buf = resultsFileName, index = False)
    
    master_df_reorder = master_df[master_df_col_list]
    master_df_reorder.to_csv(path_or_buf = resultsFileName, index = False)
    ## print time
    elapsed_time = (time.time() - start_time)/(60)
    print("^^^^ Total time for completion for " + envData["envDataLayerName"] + " :  " + str(elapsed_time) + " minutes")
                            
elapsed_time = (time.time() - start_time)/(60)
print("^^^^ Total time for completion: " + str(elapsed_time) + " minutes")
