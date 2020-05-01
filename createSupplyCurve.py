# -*- coding: utf-8 -*-
"""
Created on %(date)s

@author: Grace Wu

This script creates Supply Curves for RESOLVE for Wind, PV, and Geothermal
"""

##--------------------------------Preamble ----------------------------------
import arcpy
import numpy
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
##---------------------Local Parameters and workspace------------------------

## assumptions:
tech = "solar"
minArea = 1 # km2

### Set workspace for saving outputs: create file geodatabase (fgdb) for run session outputs
mainInputFolder = "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\dataCollection\\" #^^
mainOutputFolder = "C:\\Users\\Grace\\Documents\\TNC_beyond50\\PathTo100\\siteSuitabilityOutputs\\" #^^

gdbFileName = "112918_resourceAssessment.gdb"
supplyCurveFolder = "1118_results"

env.scratchWorkspace = os.path.join(mainOutputFolder, "scratch.gdb")  # sets scratchworkspace to your output workspace 
env.workspace = os.path.join(mainOutputFolder, gdbFileName) # sets environment workspace to your output workspace

# set input paths:
#stateBounds = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\SRTM_W_250m_proj_cl") ##^^ enter the path to your STATE boundary shapefile
templateRaster = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\SRTM_W_250m_proj_cl") ##^^ enter path to DEM data

# set environments for raster analyses
arcpy.env.snapRaster = templateRaster
arcpy.env.extent = templateRaster
arcpy.env.mask = templateRaster
arcpy.env.cellSize = templateRaster

#################
## INPUT FILES ##
#################

## resource rasters
solarCF = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\CF_FixedPV_SAM_AC_CF_250m")
windCF = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\CF_WINDtoolkit_NREL_IDW_masked_NoDataVals_250m")

## Existing wind and solar power plants:
existingWind = os.path.join(mainInputFolder, "existingEnergyInfrastructure\\energyInfrastructure.gdb\\Ventyx_USGS_merged_repowering")
existingSolar = os.path.join(mainInputFolder, "existingEnergyInfrastructure\\energyInfrastructure.gdb\\NationalSolarArrays_solarOnly")

## QRAs and SuperCREZs
QRAfilePath = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\QRA_proj")
SuperCREZ = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\SUPERCREZ_proj")
statesFilePath = os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\stateBound_baja")

scratch = os.path.join(mainOutputFolder, "scratch.gdb")

'''
######################################################################################
##-------SITE SUITABILITY USING ALL ENV DATA : ERASE + EXTRACT BY MASK-------------###
######################################################################################
'''

#### ORIGINAL ENV SCREENS

## SOLAR
if tech == "solar":
    Cat1 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat1_solar\\Cat1_u_d_s.shp"), ["", "_cat1a"]),\
                                    (os.path.join(mainInputFolder, "envData\\tnc_lands_cat1_2\\tnc_lands_cat1_easements_proj.shp"), ["_cat1a", "_cat1b"])])
    Cat2 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat2\\both_p1\\Both_p1.shp"), ["_cat1b", "_cat2a"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\both_p2\\Both_p2.shp"), ["_cat2a", "_cat2b"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\solar_p1\\Solar_p1.shp"), ["_cat2b", "_cat2c"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\solar_p2\\Solar_p2.shp"), ["_cat2c", "_cat2d"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\0045_AHPRC_Cat2\\0045_AHPRC\\data\\v101\\nps_identified_high_potential_for_resource_conflict.gdb\\NPS_AHPRC"), ["_cat2d", "_cat2e"]),\
                                    (os.path.join(mainInputFolder, "envData\\tnc_lands_cat1_2\\tnc_lands_cat2_feeAreas_proj.shp"), ["_cat2e", "_cat2f"])])
    Cat3 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat3\\Cat3_solar_excl_base_proj.shp"), ["_cat2f", "_cat3c"])])
    Cat4 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat4\\Cat4_u_d_s_proj.shp"), ["_cat3", "_cat4"])])
    CFraster = solarCF
    #inputNAME = os.path.join(mainOutputFolder, "070618_RPScalcCAresource.gdb\\RPScalc_SolarPV")
    inputNAME = os.path.join(mainOutputFolder, gdbFileName, "solarPV_0_0_nonEnv_r1")

## WIND
if tech == "wind":
    Cat1 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat1_wind\\Cat1_wind_u_d_s.shp"), ["", "_cat1a"]),\
                                    (os.path.join(mainInputFolder, "envData\\tnc_lands_cat1_2\\tnc_lands_cat1_easements_proj.shp"), ["_cat1a", "_cat1b"])])
    Cat2 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat2\\both_p1\\Both_p1.shp"), ["_cat1b", "_cat2aa"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\both_p2\\Both_p2.shp"), ["_cat2aa", "_cat2b"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\wind_p1\\Wind_p1.shp"), ["_cat2b", "_cat2c"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\wind_p2\\Wind_p2.shp"), ["_cat2c", "_cat2d"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat2\\0045_AHPRC_Cat2\\0045_AHPRC\\data\\v101\\nps_identified_high_potential_for_resource_conflict.gdb\\NPS_AHPRC"), ["_cat2d", "_cat2e"]),\
                                    (os.path.join(mainInputFolder, "envData\\tnc_lands_cat1_2\\tnc_lands_cat2_feeAreas_proj.shp"), ["_cat2e", "_cat2f"])])
    Cat3 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat3\\Cat3_solar_excl_base_proj.shp"), ["_cat2f", "_cat3a"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat3\\Cat3_wind_excl_p1_proj.shp"), ["_cat3a", "_cat3b"]),\
                                    (os.path.join(mainInputFolder, "envData\\Cat3\\Cat3_wind_excl_p2_no0147_proj.shp"), ["_cat3b", "_cat3c"])])
    Cat4 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat4\\Cat4_u_d_s_proj.shp"), ["_cat3c", "_cat4"])])
    CFraster = windCF
    #inputNAME = os.path.join(mainOutputFolder, "070618_RPScalcCAresource.gdb\\RPScalc_Wind")
    inputNAME = os.path.join(mainOutputFolder, gdbFileName, "wind_0_03_nonEnv_r3")

selectSuffix = "_gt1km2"
envEx_ls = [Cat1, Cat2, Cat3, Cat4]


## For each category, erase the env data using the previously saved feature class
for cat in envEx_ls:
    for ex in cat:
        ft = inputNAME + cat[ex][0]
        print(ft)
        outputFile = inputNAME + cat[ex][1]
        print(outputFile)
        ## erase
        print("Erasing " + str(ex))
        arcpy.Erase_analysis(ft, ex, outputFile)

    ## Get outputfilename of last element of ordered dictionary for the category
    lastOutput = inputNAME + cat[next(reversed(cat))][1]

    ## convert multipart to singlepart
    print("Converting from multipart to singlepart")
    ft_singlept_file = lastOutput + "_singlepart"
    ft_singlept = arcpy.MultipartToSinglepart_management(in_features = lastOutput, out_feature_class = ft_singlept_file)
    
    ## recalculate area
    fields = arcpy.ListFields(ft_singlept)
    fieldList  = []
    for field in fields:
        fieldList.append(field.name)
    if "Area" not in fieldList:
        print("Adding Area field")
        arcpy.AddField_management(ft_singlept, "Area", "DOUBLE")
    
    arcpy.CalculateField_management(in_table = ft_singlept, field = "Area", \
                                    expression = "!Shape.Area@squarekilometers!", \
                                    expression_type = "PYTHON_9.3")
    
    ## select areas greater than 1 or 2 km2
    print("selecting ")
    ft_singlept_select = arcpy.Select_analysis(ft_singlept,\
                               ft_singlept_file + selectSuffix, \
                               '"Area" >= ' + str(minArea))
    
    ## Create raster of capacity factors for each category
    print("Extracting by mask")
    outExtractByMask = ExtractByMask(CFraster, ft_singlept_select)
    outExtractByMask.save(ft_singlept_file + selectSuffix + "_rast")
    
    print("Done: select min area " + ft_singlept_file + selectSuffix)  

''' ===========================================================================================================

#############################################################################################
##----------RUN SCRIPT TOOL B STAGE 2: CREATE PROJECT OPPORTUNITY AREAS-------------------###
#############################################################################################
'''
# Import custom toolbox
#arcpy.ImportToolbox("F:\\MapRE_misc\\REzoningGIStools_allVersions\\REzoningGIStools_v1_4\\REzoning_models.tbx", "scriptToolBStage2CreateProjectAreas")
## alias: REzoningModels
# Run tool in the custom toolbox.  The tool is identified by
#  the tool name and the toolbox alias for example: arcpy.scriptToolBStage2CreateProjectAreas_REzoningModelss(arguments)

## the above gives a syntax error. dunno why so just copying and pasting the script tool manually here and converting to function


def scriptToolB2 (suitableSites,projectsOut,scratch,templateRaster,countryBounds,geoUnits,fishnetSize,fishnetDirectory,whereClauseMax, whereClauseMin, whereClauseMinContArea):
    '''
    #####################################################################################
    #### --------------------------------GEOPROCESSES--------------------------------####
    #####################################################################################
    
    ############################################
    ## Set environments and scratch workspace ##
    ############################################
    '''   
    # set environments for any raster analyses
    arcpy.env.snapRaster = Raster(templateRaster)
    arcpy.env.extent = countryBounds
    arcpy.env.mask = countryBounds
    arcpy.env.cellSize = Raster(templateRaster)
    
    env.workspace = scratch
    env.scratchWorkspace = scratch
    
    '''
    #################################################
    ## Check for fishnet file and create if needed ##
    #################################################
    '''   
    
    fishnet = "in_memory/fishnet_" + str(fishnetSize) + "km" ## MUST add .shp if not putting file in gdb (for add field function)
    clippedFishnet = fishnetDirectory + "\\"+ "fishnet_" + str(fishnetSize) + "km"
    
    env.outputCoordinateSystem = templateRaster
    if not(arcpy.Exists(clippedFishnet)):
        #Create fishnet if one does not already exist:
        print("Creating fishnet " + str(fishnetSize) + " km in size to file: " + fishnet)
    
        extent = Raster(templateRaster).extent
        
        XMin = extent.XMin ## left
        
        YMin = extent.YMin ## Bottom
        
        origin = str(XMin) + " " + str(YMin)
        
        YMax = extent.YMax ## top
        
        ycoord = str(XMin) + " " + str(YMax)
        
        arcpy.CreateFishnet_management(fishnet, origin, ycoord, \
                                       fishnetSize * 1000,fishnetSize * 1000, '0', '0', "", "NO_LABELS", \
                                       "#", "POLYGON")
                                       
        fields = arcpy.ListFields(fishnet)
        for field in fields:    
            print(field.name)
        # Change fishnet Object ID name:
        arcpy.AddField_management(fishnet, "Text", "Text", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        # Process: Calculate Field to create new alphanumeric OID column
        arcpy.CalculateField_management(fishnet, "Text", "'A' + str(!OID!)", "PYTHON_9.3", "")
    
        print("Creating country-boundary-clipped fishnet " + str(fishnetSize) + " km in size to file: " + clippedFishnet)
        arcpy.Clip_analysis(fishnet, countryBounds, clippedFishnet)
    
    print("Copying fishnet to memory :"  + clippedFishnet)
    fishnetInMemory = arcpy.CopyFeatures_management(clippedFishnet, "in_memory/clipped_fishnet")
    
    # Temporary variables:
    IntermediateIntersect_geoUnits = "in_memory/IntermediateIntersect_geoUnits"
    Intermediate = "in_memory/intermediate_2"
    IntermediateErased = "in_memory/intermediateErased_2"
    IntermediateIntersect = "in_memory/IntermediateIntersect_2"
    IntermediateIntersect_singlept = "in_memory/IntermediateIntersect_singlept"
    #IntermediateAggregatedFeatures = "in_memory/IntermediateAggregatedFeatures_2"
    #IntermediateIntersectErased = "in_memory/IntermediateIntersectErased_2"
    IntermediateEliminated = "in_memory/IntermediateEliminated"
    IntermediateEliminated2 = "in_memory/IntermediateEliminated2"
    #IntermediateSelectedForAggregation1 = "in_memory/IntermediateSelectedForAggregation1_2"
    #IntermediateSelectedForAggregation2 = "in_memory/IntermediateSelectedForAggregation2_2"
    #IntermediateIntersect_geoUnits_2 = "in_memory/IntermediateIntersect_geoUnits_2"
    
    '''
    ###############
    ## Intersect ##
    ###############
    ''' 
    ## COPY SUITABLE SITES FEATURE CLASS TO MEMORY
    sites = arcpy.CopyFeatures_management(suitableSites, "in_memory/suitableSites")
    
    ## INTERSECT Geographic Unit of Analysis, if provided
    if arcpy.Exists(geoUnits):
        print("Intersecting by geographic units of analysis")
        arcpy.Intersect_analysis([sites, geoUnits], IntermediateIntersect_geoUnits, "NO_FID")
    else:
        IntermediateIntersect_geoUnits = sites
            
    # calculate area:
    arcpy.AddField_management(IntermediateIntersect_geoUnits, "Area", "DOUBLE", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
    # Process: Calculate Field
    arcpy.CalculateField_management(IntermediateIntersect_geoUnits, "Area", "!Shape.Area@squarekilometers!", "PYTHON_9.3", "")
    
    # select polygons greater than max area to split
    arcpy.Select_analysis(IntermediateIntersect_geoUnits, Intermediate, whereClauseMax)
    # erase selected areas from potentialSites (isolate all polygons less than max to merge later)
    arcpy.Erase_analysis(IntermediateIntersect_geoUnits, Intermediate, IntermediateErased)
    
    # Intersect regions above max area using fishnet
    print("Intersecting by fishnet")
    arcpy.Intersect_analysis([Intermediate, fishnetInMemory], IntermediateIntersect, "NO_FID")
    print("finished intersecting by fishnet")
    # Process: Calculate Area
    arcpy.CalculateField_management(IntermediateIntersect, "Area", "!Shape.Area@squarekilometers!", "PYTHON_9.3", "")
    
    '''
    ###############
    ## Aggregate ##
    ###############
    
    print("Starting aggregation")
    # select areas under min to aggregate
    arcpy.Select_analysis(IntermediateIntersect, IntermediateSelectedForAggregation1, whereClauseMin)
    # Process: erase small areas from larger areas
    arcpy.Erase_analysis(IntermediateIntersect, IntermediateSelectedForAggregation1, IntermediateIntersectErased)
    # merge those under min area to aggregate
    arcpy.Merge_management([IntermediateSelectedForAggregation1, IntermediateErased],IntermediateSelectedForAggregation2)
    # aggregate smaller abutting areas into one polygon
    CA.AggregatePolygons(IntermediateSelectedForAggregation2, IntermediateAggregatedFeatures, 1, "", 0, "ORTHOGONAL", "", "aggregatedTable")
    print("Finished Aggregation")
    ''' 
    '''
    ################################
    ## Create singlepart polygons ##
    ################################
    '''
    ## Multi-part to single part
    arcpy.MultipartToSinglepart_management(in_features = IntermediateIntersect, out_feature_class = IntermediateIntersect_singlept)
    ## Recalculate area
    arcpy.CalculateField_management(IntermediateIntersect_singlept, "Area", "!Shape.Area@squarekilometers!", "PYTHON_9.3", "")
    '''
    ###############################
    ## Eliminate slivers - twice ##
    ###############################
    ''' 
    print("Starting elimination")
    # Execute MakeFeatureLayer
    tempLayer = arcpy.MakeFeatureLayer_management(IntermediateIntersect_singlept, "tempLayer")
     
    # Execute SelectLayerByAttribute to define features to be eliminated
    arcpy.SelectLayerByAttribute_management(in_layer_or_view = tempLayer, selection_type= "NEW_SELECTION" , where_clause = whereClauseMin)

    # Execute Eliminate
    arcpy.Eliminate_management("tempLayer", IntermediateEliminated, "LENGTH")
    
    ## iteration 2
    
    # Execute MakeFeatureLayer
    IntermediateEliminated_tempLayer = arcpy.MakeFeatureLayer_management(IntermediateEliminated, "IntermediateEliminated")
    
    # Execute SelectLayerByAttribute to define features to be eliminated
    arcpy.SelectLayerByAttribute_management(in_layer_or_view = IntermediateEliminated_tempLayer, selection_type= "NEW_SELECTION" , where_clause = whereClauseMin)

    # Execute Eliminate
    arcpy.Eliminate_management(IntermediateEliminated_tempLayer, IntermediateEliminated2, "LENGTH")
    
    '''
    ################################################
    ## Merge aggregated with intersected features ##
    ################################################
    ''' 
    # Merge aggregated polygons with larger, split polygons
    merged = arcpy.Merge_management([IntermediateErased, IntermediateEliminated2], "in_memory/intermediateProjects")
    
    ## AGAIN, INTERSECT Geographic Unit of Analysis, if provided
    if arcpy.Exists(geoUnits):
        print("Intersecting by geographic units of analysis")
        arcpy.Intersect_analysis([merged, geoUnits], IntermediateIntersect_geoUnits , "NO_FID")
        print("Finished intersecting by geographic units of analysis")
    else:
        IntermediateIntersect_geoUnits = merged
    
    # recalculate area
    arcpy.CalculateField_management(IntermediateIntersect_geoUnits, "Area", "!Shape.Area@squarekilometers!", "PYTHON_9.3", "")
    # select areas above minimum and save ## CREATE PROJECT FEATURE CLASS
    arcpy.Select_analysis(IntermediateIntersect_geoUnits, projectsOut, whereClauseMinContArea)
    ## Process: Summary Statistics
    ## arcpy.Statistics_analysis(selectOut, outputFGDB + filename + '_stats', "Area SUM", "") ## CREATE PROJECT STATS
    print('Finished merging')


## List of inputs to loop over
## SOLAR:
if tech == "solar":
    ft_ls = {"Cat1" : "solarPV_0_0_nonEnv_r1_cat1b_singlepart_gt1km2",\
            "Cat2" : "solarPV_0_0_nonEnv_r1_cat2f_singlepart_gt1km2",\
            "Cat3" : "solarPV_0_0_nonEnv_r1_cat3c_singlepart_gt1km2", \
             "Cat4": "solarPV_0_0_nonEnv_r1_cat4_singlepart_gt1km2"}
    zoneType_ls = {"state": [os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\stateBound_baja"), "_PA_state"], \
                 "OOS_RESOLVEZONE": [os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\QRA_proj_RESOLVE_ZONE_solar"), "_PA_OOS_RESOLVEZONE"], \
                 "CA_RESOLVEZONE": [os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\SUPERCREZ_proj_CA_RESOLVE_ZONE"), "_PA_CA_RESOLVEZONE"]}
    existingPlants = existingSolar
    fishnetWidth = "2"
    maxAreaAgg = "4"
    minAreaAgg = "1"

## WIND:
if tech == "wind":
    ft_ls = {"Cat1" : "wind_0_03_nonEnv_r3_cat1b_singlepart_gt1km2",\
            "Cat2" : "wind_0_03_nonEnv_r3_cat2f_singlepart_gt1km2",\
            "Cat3" : "wind_0_03_nonEnv_r3_cat3c_singlepart_gt1km2", \
             "Cat4": "wind_0_03_nonEnv_r3_cat4_singlepart_gt1km2"}
    zoneType_ls = {"state": [os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\stateBound_baja"), "_PA_state"], \
                 "OOS_RESOLVEZONE": [os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\QRA_proj_RESOLVE_ZONE_Wind"), "_PA_OOS_RESOLVEZONE"], \
                 "CA_RESOLVEZONE": [os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb\\SUPERCREZ_proj_CA_RESOLVE_ZONE"), "_PA_CA_RESOLVEZONE"]}
    existingPlants = existingWind
    fishnetWidth = "3"
    maxAreaAgg = "9"
    minAreaAgg = "1"

## loop through each category and zone type to create PPA feature classes
for cat in ft_ls:
    print("")
    print("")
    print(cat)
    for zoneType in zoneType_ls:
        print("")
        inputNAME = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat])
        outputNAME = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat] + zoneType_ls[zoneType][1])
        ## Erase existing wind and solar projects out ot state
        if zoneType == "OOS_RESOLVEZONE" or zoneType == "state":
            print("  Erasing existing power plants")
            inputNAME_erasedExisting = arcpy.Erase_analysis(inputNAME, existingPlants, "in_memory/erasedExisting")
        ## if it's CA, then don't erase
        else:
            print("  NOT erasing existing plants")
            inputNAME_erasedExisting = inputNAME
            
        print("  Working on " + outputNAME)
        scriptToolB2(suitableSites= inputNAME_erasedExisting, \
                     projectsOut = outputNAME, \
                     scratch = scratch, \
                     templateRaster= os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb/SRTM_W_250m_proj_cl"), \
                     countryBounds= os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb/WECC_USboundaries"), \
                     geoUnits= zoneType_ls[zoneType][0], \
                     fishnetSize=int(fishnetWidth), \
                     fishnetDirectory= os.path.join(mainInputFolder, "siteSuitabilityInputs_nonEnv.gdb"), \
                     whereClauseMax='"Area" > ' + str(maxAreaAgg), \
                     whereClauseMin = 'Area < ' + str(minAreaAgg), \
                     whereClauseMinContArea = '"Area" > ' + str("1"))
        print("  Finished")


''' ===========================================================================================================

#####################################################################################################################################
##----------CALCULATE OOS AVG CF AND TOTAL MW BY RESOLVE ZONE (eg., Wyoming_Wind) AND QRA (e.g., WY_SO, WY_NO) -------------------###
#####################################################################################################################################
'''
def calcSupplyCurve(inFeature, inRaster, inFeatureFileName, category, QRAs, RESOLVE_ZONE_FIELD):
    
    ## Delete Name RESOLVE_ZONE_FIELD if it already exists:
    fields = arcpy.ListFields(inFeature)
    fieldList  = []
    for field in fields:
        fieldList.append(field.name)
    if RESOLVE_ZONE_FIELD in fieldList:
        print("Deleting existing field: " + RESOLVE_ZONE_FIELD)
        arcpy.DeleteField_management(inFeature, RESOLVE_ZONE_FIELD)
    if "Name" in fieldList:
        print("Deleting existing field: " + "Name")
        arcpy.DeleteField_management(inFeature, "Name")
        
    ############ CF CALC ##############
    ## Get average CAPACITY FACTOR per QRA; result only contains the Name field from the QRA feature class
    ## use the resource raster dataset
    CFtable = arcpy.sa.ZonalStatisticsAsTable(in_zone_data = QRAs, zone_field ="Name", \
                                                   in_value_raster = inRaster, \
                                                   out_table = "in_memory/zonalStats_CF", \
                                                   ignore_nodata = "DATA", statistics_type = "MEAN")
    
    # Join zonal statistics table of avg CF to QRA file to add the RESOLVE_ZONE_FIELD to the stats table
    arcpy.JoinField_management(in_data = CFtable, in_field = "Name", join_table = QRAs, \
                               join_field = "Name", fields = [RESOLVE_ZONE_FIELD])
    
    # Rename field MEAN to CF_avg
    arcpy.AlterField_management(in_table = CFtable, field = "MEAN", new_field_name = "CF_avg_" + category)
    
    
    ############ AREA CALC ##############    
    ## calculating the area will require the feature class
    
    ## Clip suitable sites polygons using QRAs 
    QRAclip = arcpy.Clip_analysis(in_features = inFeature, clip_features = QRAs, \
                                       # out_feature_class = inFeature + "_QRAclip") 
                                       out_feature_class = "in_memory/QRAclip") 
    
    print("Finished clipping QRA for " + inFeatureFileName)
    
    ## Calculate Area (geometry) of resources within QRAs
    arcpy.CalculateField_management(in_table = QRAclip, field = "Area", \
                                    expression = "!Shape.Area@squarekilometers!", expression_type = "PYTHON_9.3")
    
    ## Spatial join of clipped polygons with QRAs to add Name and RESOLVE_ZONE_FIELD to clipped polygons
    QRAclip_joined = arcpy.SpatialJoin_analysis(target_features = QRAclip, join_features = QRAs, \
                                               #out_feature_class =  "in_memory/"+ inFeature + "_QRAclip" + "_QRAjoined", \
                                               out_feature_class =  "in_memory/QRAclip" + "_QRAjoined", \
                                               join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_ALL", \
                                               match_option = "INTERSECT")
    
    print("Finished spatial join of QRA fields to feature class for  " + inFeatureFileName)
    
    ## summary statistics to get the total area per QRA ("Name") first; 
    ## the resultant field in the table is automatically named "SUM_Area"
    areaQRAtable = arcpy.Statistics_analysis(in_table = QRAclip_joined, \
                                       out_table = "in_memory/sumStats_Area_QRA", \
                                       statistics_fields = [["Area", "SUM"]], case_field = [RESOLVE_ZONE_FIELD, "Name"])
    
    # Rename field SUM_Area to Area
    arcpy.AlterField_management(in_table = areaQRAtable, field = "SUM_Area", new_field_name = "Area_" + category, \
                                new_field_alias = "Area_" + category)
    
    ## CaCLULATE capacity of each QRA from area
    arcpy.AddField_management(areaQRAtable, "cap_MW_" + category, "DOUBLE")
    
    arcpy.CalculateField_management(in_table = areaQRAtable, field = "cap_MW_" + category, \
                                    expression = "!Area_" + category + "!*" + str(LUF), expression_type = "PYTHON_9.3")
    
    ## Calculate capacity for each RESOLVE_ZONE using summary stats on the QRA table (which has QRA and RESOLVE_ZONE_FIELD fields)
    areaRZ_table = arcpy.Statistics_analysis(in_table = areaQRAtable, \
                                                   out_table = "in_memory/sumStats_Area_RZ", \
                        statistics_fields = [["Area_" + category, "SUM"],["cap_MW_" + category, "SUM"]], case_field = [RESOLVE_ZONE_FIELD])
    
    # Rename field SUM_cap_MW to cap_MW_state
    arcpy.AlterField_management(in_table = areaRZ_table, field = "SUM_cap_MW_" + category, \
                                new_field_name = "cap_MW_RESOLVE_ZONE_" + category, \
                                new_field_alias = "cap_MW_RESOLVE_ZONE_" + category)
    
    arcpy.AlterField_management(in_table = areaRZ_table, field = "SUM_Area_" + category, \
                                new_field_name = "Area_" + category, \
                                new_field_alias = "Area_" + category)
    
    ## join table back to areaQRAtable to add cap_MW_state to the table
    arcpy.JoinField_management(in_data = areaQRAtable, in_field = RESOLVE_ZONE_FIELD, join_table = areaRZ_table, \
                               join_field = RESOLVE_ZONE_FIELD, fields = ["cap_MW_RESOLVE_ZONE_" + category])
    
    ## Calculate capacity averaged CF per RESOLVE ZONE
    ## sum(capacity(QRA)/capacity(State) * CF) for each QRA within each state
    ## join areaQRAtable with solarCFtable using Name to get the CF_avg field in the main table
    arcpy.JoinField_management(in_data = areaQRAtable, in_field = "Name", join_table = CFtable, \
                               join_field = "Name", fields = ["CF_avg_" + category])
    
    ## Calculate new field that is the (capacity(QRA)/capacity(State) * CF)
    arcpy.AddField_management(areaQRAtable, "QRApropMW_" + category, "DOUBLE")
    
    arcpy.CalculateField_management(in_table = areaQRAtable, field = "QRApropMW_" + category, \
                                    expression = "(!cap_MW_" + category + "!/!cap_MW_RESOLVE_ZONE_" + category + "!)*!CF_avg_" + category + "!", \
                                    expression_type = "PYTHON_9.3")
    
    ## sum (capacity(QRA)/capacity(State) * CF) for each state
    avgCF_byQRA_RZ = arcpy.Statistics_analysis(in_table = areaQRAtable, \
                                                  out_table = "in_memory/avgCF_byQRA_RZ", \
                        statistics_fields = [["QRApropMW_" + category, "SUM"]], case_field = [RESOLVE_ZONE_FIELD])
    
    arcpy.AlterField_management(in_table = avgCF_byQRA_RZ, field = "SUM_QRApropMW_" + category, \
                                new_field_name = "CF_avg_RESOLVE_ZONE_" + category, \
                                new_field_alias = "CF_avg_RESOLVE_ZONE_" + category)
    
    ## join RESOLVE_ZONE total MW to state average CF into a single table:
    arcpy.JoinField_management(in_data = avgCF_byQRA_RZ, \
                               in_field = RESOLVE_ZONE_FIELD, join_table = areaRZ_table, \
                               join_field = RESOLVE_ZONE_FIELD, fields = ["Area_" + category, "cap_MW_RESOLVE_ZONE_" + category])#fields = ["CF_avg_RESOLVE_ZONE_" + category])
    
    ############################################
    ## copy tables to hard drive as gdb table ##
    ############################################
    
    ##### RESOLVE ZONE AVERAGES
    #arcpy.TableToTable_conversion(in_rows = avgCF_byQRA_RZ, out_path = os.path.join(mainOutputFolder, gdbFileName),\
    #                              out_name =  inFeatureFileName + "_areaRZ_table_debug")
    ## convert table to pandas df
    # get fields for use in Table to Numpy Array function
    #fields = arcpy.ListFields(os.path.join(mainOutputFolder, outputGDB, inFeatureFileName + "_RESOLVE_ZONE_CFMW"))
    fields = arcpy.ListFields(avgCF_byQRA_RZ)
    fieldList  = []
    for field in fields:
        fieldList.append(field.name)
    #fieldList.remove('FREQUENCY') ## remove extra field
    #fieldList.remove("OBJECTID")
    
    pattern = r'RESOLVE_ZONE_\S|cap_MW_\S|Area_\S|CF_avg_\S'
    fieldList = [x for x in fieldList if re.search(pattern, x)]  
      
    ## convert gdb table to numpy array to Pandas DF (and transpose):
    stateAvgCFMW_df = pandas.DataFrame(arcpy.da.TableToNumPyArray(avgCF_byQRA_RZ, fieldList))
    
    
    ##### QRA AVERAGES
    #arcpy.TableToTable_conversion(in_rows = areaQRAtable, out_path = os.path.join(mainOutputFolder, outputGDB), \
    #                              out_name =  inFeatureFileName + "_QRAavgCFMW_RESOLVE_ZONES_ONLY")
    
    ## convert table to pandas df
    # get fields for use in Table to Numpy Array function
    #fields = arcpy.ListFields(os.path.join(mainOutputFolder, outputGDB, inFeatureFileName + "_QRAavgCFMW_RESOLVE_ZONES_ONLY"))
    fields = arcpy.ListFields(areaQRAtable)
    fieldList  = []
    for field in fields:
        fieldList.append(field.name)
    fieldList.remove("cap_MW_RESOLVE_ZONE_" + category) ## remove extra field
    #fieldList.remove("FREQUENCY")
    #fieldList.remove("OBJECTID")
    
    pattern = r'RESOLVE_ZONE_\S|cap_MW_\S|Area_\S|CF_avg_\S|Name'
    fieldList = [x for x in fieldList if re.search(pattern, x)]
    
    ## convert gdb table to numpy array to Pandas DF (and transpose):
    QRAavgCFMW_df = pandas.DataFrame(arcpy.da.TableToNumPyArray(areaQRAtable, fieldList))
    
    print("Finished processing " + inFeatureFileName)   
    
    return stateAvgCFMW_df, QRAavgCFMW_df



## List of inputs to loop over

## SOLAR:
if tech == "solar":
    ft_ls = {"Cat1" : ["solarPV_0_0_nonEnv_r1_cat1b_singlepart_gt1km2_PA_OOS_RESOLVEZONE", "solarPV_0_0_nonEnv_r1_cat1b_singlepart_gt1km2"],\
            "Cat2" : ["solarPV_0_0_nonEnv_r1_cat2f_singlepart_gt1km2_PA_OOS_RESOLVEZONE", "solarPV_0_0_nonEnv_r1_cat2f_singlepart_gt1km2"],\
            "Cat3" : ["solarPV_0_0_nonEnv_r1_cat3c_singlepart_gt1km2_PA_OOS_RESOLVEZONE", "solarPV_0_0_nonEnv_r1_cat3c_singlepart_gt1km2"], \
             "Cat4": ["solarPV_0_0_nonEnv_r1_cat4_singlepart_gt1km2_PA_OOS_RESOLVEZONE", "solarPV_0_0_nonEnv_r1_cat4_singlepart_gt1km2"]}
    LUF = 30 # MW/km
    RESOLVE_ZONE_FIELD_param = "RESOLVE_ZONE_solar"

## WIND:
if tech == "wind":
    ft_ls = {"Cat1" : ["wind_0_03_nonEnv_r3_cat1b_singlepart_gt1km2_PA_OOS_RESOLVEZONE", "wind_0_03_nonEnv_r3_cat1b_singlepart_gt1km2"],\
            "Cat2" : ["wind_0_03_nonEnv_r3_cat2f_singlepart_gt1km2_PA_OOS_RESOLVEZONE","wind_0_03_nonEnv_r3_cat2f_singlepart_gt1km2"],\
            "Cat3" : ["wind_0_03_nonEnv_r3_cat3c_singlepart_gt1km2_PA_OOS_RESOLVEZONE","wind_0_03_nonEnv_r3_cat3c_singlepart_gt1km2"], \
             "Cat4": ["wind_0_03_nonEnv_r3_cat4_singlepart_gt1km2_PA_OOS_RESOLVEZONE","wind_0_03_nonEnv_r3_cat4_singlepart_gt1km2"]}
    LUF = 6.1 # MW/km
    RESOLVE_ZONE_FIELD_param = "RESOLVE_ZONE_wind"

## output list to append 
stateAvgCFMW_ls = []
QRAavgCFMW_ls = []

## loop function over list of inputs
for cat in ft_ls:
    stateAvgCFMW, QRAavgCFMW = calcSupplyCurve(inFeature = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat][0]), \
                    inRaster = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat][1] + "_rast"), \
                    inFeatureFileName = ft_ls[cat][0], \
                    category = cat, \
                    QRAs = QRAfilePath,\
                    RESOLVE_ZONE_FIELD = RESOLVE_ZONE_FIELD_param) 
    
    ## append output list
    stateAvgCFMW_ls.append(stateAvgCFMW)
    QRAavgCFMW_ls.append(QRAavgCFMW)

## MERGE TABLES 
# StateAvg: this table reports the average CF and total MW of resources within all QRAs in each state, or otherwise RESOLVE ZONE, e.g., "Wyoming_Wind"
stateAvgCFMW_merged = pandas.merge(stateAvgCFMW_ls[0], stateAvgCFMW_ls[1], how= 'outer', on = RESOLVE_ZONE_FIELD_param)
for tab in [stateAvgCFMW_ls[2], stateAvgCFMW_ls[3]]:
    stateAvgCFMW_merged = pandas.merge(stateAvgCFMW_merged, tab, how= 'outer', on = RESOLVE_ZONE_FIELD_param)

# QRAavg: this table reports the average CF and total MW of resources within each QRA, e.g., WY_NO or WY_SO
QRAavgCFMW_merged = pandas.merge(QRAavgCFMW_ls[0], QRAavgCFMW_ls[1], how= 'outer',on = "Name")
for tab in [QRAavgCFMW_ls[2],QRAavgCFMW_ls[3]]:
    QRAavgCFMW_merged = pandas.merge(QRAavgCFMW_merged, tab, how= 'outer',on = "Name")
    

## SAVE TO CSV
# This one will be used in the supply curve
stateAvgCFMW_merged.to_csv(os.path.join(mainOutputFolder, supplyCurveFolder, tech + "_OOS_RESOLVEZONE_avgCFMW_PA.csv"))
# This one will will not be used (just informational)
QRAavgCFMW_merged.to_csv(os.path.join(mainOutputFolder, supplyCurveFolder, tech + "_OOS_QRA_avgCFMW_PA.csv"))


''' ===========================================================================================================

############################################################################################
## Create supply curves for state-wide (outside of QRAs) or CA RESOLVE ZONE MW and Avg CF ##
############################################################################################
'''

    ## Same method for getting average CF and total MW per SuperCREZ 

def calcSupplyCurve_state(inFeature, inRaster, inFeatureFileName, category, zonesFile, zoneField):
    
    ## Delete Name RESOLVE_ZONE_FIELD if it already exists:
    fields = arcpy.ListFields(inFeature)
    fieldList  = []
    for field in fields:
        fieldList.append(field.name)
    if zoneField in fieldList:
        print("Deleting existing field: " + zoneField)
        arcpy.DeleteField_management(inFeature, zoneField)
    if "Name" in fieldList:
        print("Deleting existing field: " + "Name")
        arcpy.DeleteField_management(inFeature, "Name")
        
    #############################
    ## CALC TOTAL MW PER STATE ##
    #############################

    ## intersect to break up the features by state
    inFeature_stateInt = arcpy.Intersect_analysis(in_features = [inFeature, zonesFile], out_feature_class = "in_memory/stateInt")
    
    print("Finished intersect for " + inFeatureFileName)
    
    ## ReCalculate Area (geometry)
    arcpy.CalculateField_management(in_table = inFeature_stateInt, field = "Area", \
                                    expression = "!Shape.Area@squarekilometers!", expression_type = "PYTHON_9.3")
    
    ## summary statistics to get the total area per state; the resultant field in the table is "SUM_Area"
    areaTable = arcpy.Statistics_analysis(in_table = inFeature_stateInt, \
                                       out_table = "in_memory/inFeature_stateInt_AreaCalc", \
                                       statistics_fields = [["Area", "SUM"]], case_field = [zoneField])
    
    ## Rename field from SUM_Area to Area
    arcpy.AlterField_management(in_table = areaTable, field = "SUM_Area", new_field_name = "Area_" + category, \
                                new_field_alias = "Area_" + category)
        
    ## Calcuylate capacity from area
    arcpy.AddField_management(areaTable, "cap_MW_" + category, "DOUBLE")
    
    arcpy.CalculateField_management(in_table = areaTable, field = "cap_MW_" + category, \
                                    expression = "!Area_" + category + "!*" + str(LUF), expression_type = "PYTHON_9.3")
    
    ###########################
    ## CALC AVG CF PER STATE ##
    ###########################
    
    ## Get average CAPACITY FACTOR per state
    ## use the resource raster dataset
    CFtable = arcpy.sa.ZonalStatisticsAsTable(in_zone_data = zonesFile, zone_field = zoneField, \
                                                   in_value_raster = inRaster, \
                                                   out_table = "in_memory/zonalStats_CF", \
                                                   ignore_nodata = "DATA", statistics_type = "MEAN")
    
    # Join zonal statistics table of avg CF to QRA file to get the name of the state in the stats table
    #arcpy.JoinField_management(in_data = CFtable, in_field = "Name", join_table = QRAs, \
    #                           join_field = "Name", fields = ["STATE"])
    
    # Rename field MEAN to CF_avg
    arcpy.AlterField_management(in_table = CFtable, field = "MEAN", new_field_name = "CF_avg_" + category)
    
    #####################################
    ## Join MW, Area and CF_avg fields ##
    #####################################
    arcpy.JoinField_management(in_data = CFtable, in_field = zoneField, join_table = areaTable, \
                               join_field = zoneField, fields = ["Area_" + category, "cap_MW_" + category])
    
    
    ############################################
    ## copy tables to hard drive as gdb table ##
    ############################################
    
    ## SAVE STATE AVERAGES to GDB table
    #arcpy.TableToTable_conversion(in_rows = CFtable, out_path = os.path.join(mainOutputFolder, outputGDB),\
    #                              out_name =  inFeatureFileName + csv_suffix)
    
    ## convert table to pandas df
    # get fields for use in Table to Numpy Array function
    #fields = arcpy.ListFields(os.path.join(mainOutputFolder, outputGDB, inFeatureFileName + csv_suffix))
    fields = arcpy.ListFields(CFtable)
    fieldList  = []
    for field in fields:
        fieldList.append(field.name)
    #fieldList.remove('COUNT') ## remove extra field
    #fieldList.remove("OBJECTID")
    #fieldList.remove("ZONE_CODE")
    #fieldList.remove("AREA")
    
    pattern = r'CF_avg_\S|Area_\S|cap_MW_\S|NAME|RESOLVE_ZONE|STPOSTAL'
    fieldList = [x for x in fieldList if re.search(pattern, x)]
      
    ## convert gdb table to numpy array to Pandas DF:
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(CFtable, fieldList))
    
    print("FINISHED processing " + inFeatureFileName )  
    
    return df


## List of inputs to loop over
if tech == "solar":
    ft_ls = {"Cat1" : "solarPV_0_0_nonEnv_r1_cat1b_singlepart_gt1km2",\
            "Cat2" : "solarPV_0_0_nonEnv_r1_cat2f_singlepart_gt1km2",\
            "Cat3" : "solarPV_0_0_nonEnv_r1_cat3c_singlepart_gt1km2", \
             "Cat4": "solarPV_0_0_nonEnv_r1_cat4_singlepart_gt1km2"}
    LUF = 30 # MW/km
    statesFileFieldName = "RESOLVE_ZONE_solar"

if tech == "wind":
    ft_ls = {"Cat1" : "wind_0_03_nonEnv_r3_cat1b_singlepart_gt1km2",\
            "Cat2" : "wind_0_03_nonEnv_r3_cat2f_singlepart_gt1km2",\
            "Cat3" : "wind_0_03_nonEnv_r3_cat3c_singlepart_gt1km2", \
             "Cat4": "wind_0_03_nonEnv_r3_cat4_singlepart_gt1km2"}
    LUF = 6.1 # MW/km
    statesFileFieldName = "RESOLVE_ZONE_wind"

zoneType_ls = {"_PA_state": [statesFilePath, statesFileFieldName, "_OOS_state_avgCFMW_PA.csv"], \
                 "_PA_CA_RESOLVEZONE": [SuperCREZ, "RESOLVE_ZONE","_CA_RESOLVEZONE_avgCFMW_PA.csv"]}

## for each zone type (california RESOLVE Zones or OOS wall-to-wall/state)
for zone in zoneType_ls:
    ## output list to append 
    stateAvgCFMW_w2w_ls = []
    inFeatureSuffix = zone ## "_PA_CA_RESOLVEZONE" or "_PA_state"
    zonesFileName = zoneType_ls[zone][0]  ## feature class with boundaries: statesFilePath (for states) or SuperCREZ (for superCREZ or RESOLVE_ZONES in CA)
    zoneFieldName = zoneType_ls[zone][1] ## fieldname with the zone attribute: NAME (aggregate by superCREZ) or RESOLVE_ZONE (aggregate by RESOLVE_ZONE) or "STPOSTAL" (for states)
    csvSuffix = zoneType_ls[zone][2] ## "_CA_RESOLVEZONE_avgCFMW.csv" (superCREZ) or "_CA_superCREZ_avgCFMW.csv" (superCREZ) or "_OOS_state_avgCFMW.csv" (state averages)
    
    ## loop function over list of inputs
    for cat in ft_ls:
        stateAvgCFMW_w2w = calcSupplyCurve_state(inFeature = os.path.join(mainOutputFolder,gdbFileName, ft_ls[cat] + inFeatureSuffix), \
                        inRaster = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat] + "_rast"), \
                        inFeatureFileName = ft_ls[cat] + inFeatureSuffix, \
                        category = cat, \
                        zonesFile = zonesFileName,\
                        zoneField = zoneFieldName) 
        
        ## append output list
        stateAvgCFMW_w2w_ls.append(stateAvgCFMW_w2w)
        
    ## MERGE TABLES 
    # StateAvg
    stateAvgCFMW_w2w_merged = pandas.merge(stateAvgCFMW_w2w_ls[0], stateAvgCFMW_w2w_ls[1], how= 'outer', on = zoneFieldName)
    for tab in [stateAvgCFMW_w2w_ls[2], stateAvgCFMW_w2w_ls[3]]:
        stateAvgCFMW_w2w_merged = pandas.merge(stateAvgCFMW_w2w_merged, tab, how= 'outer', on = zoneFieldName)
    
    ## SAVE TO CSV
    stateAvgCFMW_w2w_merged.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, tech + csvSuffix), index = False)

''' ===========================================================================================================
##############################
## COMPARE WITH ORB RESULTS ##
##############################
'''

## append column with RESOLVE_ZONE
fields = arcpy.ListFields(os.path.join(SuperCREZ))
fieldList  = []
for field in fields:
    fieldList.append(field.name)
pattern = r'NAME|RESOLVE_ZONE' 
fieldList = [x for x in fieldList if re.search(pattern, x)]
      
## convert gdb table to numpy array to Pandas DF:
df_superCREZ = pandas.DataFrame(arcpy.da.TableToNumPyArray(SuperCREZ, fieldList))
stateAvgCFMW_w2w_merged2 = pandas.merge(df_superCREZ, stateAvgCFMW_w2w_merged, how= 'outer', on = zoneFieldName)

df_ORB = pandas.read_csv(r"C:\Users\Grace\Documents\TNC_beyond50\ORBvisualization\RPSCalculator6_relatedMaterials\allTech_PotentialAreas_RPScalc_withFreshwater_copiedForPTOcomparison.csv")
df_PV = df_ORB.filter(regex=('\SPV\S|\SPV|PV\S|NAME'), axis =1)
df_wind = df_ORB.filter(regex=('\Swind\S|\Swind|Wind\S|NAME'), axis =1)

stateAvgCFMW_w2w_merged_wind = pandas.merge(stateAvgCFMW_w2w_merged2, df_wind, how= 'outer', on = zoneFieldName)
## SAVE TO CSV
stateAvgCFMW_w2w_merged_wind.to_csv(path_or_buf = os.path.join(mainOutputFolder, tech + "__CAavgCFMW_w2w_superCREZ_allCat_withORB.csv"), index = False)

stateAvgCFMW_w2w_merged_PV = pandas.merge(stateAvgCFMW_w2w_merged2, df_PV, how= 'outer', on = zoneFieldName)
## SAVE TO CSV
stateAvgCFMW_w2w_merged_PV.to_csv(path_or_buf = os.path.join(mainOutputFolder, tech + "__CAavgCFMW_w2w_superCREZ_allCat_withORB.csv"), index = False)




''' ===========================================================================================================
###########################################################
## Get state-wide MW for GEOTHERMAL within RESOLVE ZONES ##
###########################################################
'''
## Geothermal
Cat1 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat1_solar\\Cat1_u_d_s.shp"), ["", "_cat1a"]),\
                                (os.path.join(mainInputFolder, "envData\\tnc_lands_cat1_2\\tnc_lands_cat1_easements_proj.shp"), ["_cat1a", "_cat1b"])])
Cat2 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat2\\both_p1\\Both_p1.shp"), ["_cat1b", "_cat2aa"]),\
                                (os.path.join(mainInputFolder, "envData\\Cat2\\both_p2\\Both_p2.shp"), ["_cat2aa", "_cat2b"]),\
                                (os.path.join(mainInputFolder, "envData\\Cat2\\geothermal_p1_p2\\Geothermal_p1.shp"), ["_cat2b", "_cat2c"]),\
                                (os.path.join(mainInputFolder, "envData\\Cat2\\geothermal_p1_p2\\Geothermal_p2.shp"), ["_cat2c", "_cat2d"]),\
                                (os.path.join(mainInputFolder, "envData\\Cat2\\0045_AHPRC_Cat2\\0045_AHPRC\\data\\v101\\nps_identified_high_potential_for_resource_conflict.gdb\\NPS_AHPRC"), ["_cat2d", "_cat2e"]),\
                                (os.path.join(mainInputFolder, "envData\\tnc_lands_cat1_2\\tnc_lands_cat2_feeAreas_proj.shp"), ["_cat2e", "_cat2f"])])
Cat3 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat3\\Cat3_geotherm_excl_base_proj.shp"), ["_cat2f", "_cat3"])])
Cat4 = collections.OrderedDict([(os.path.join(mainInputFolder, "envData\\Cat4\\Cat4_u_d_s_proj.shp"), ["_cat3", "_cat4"])])

gdbFileName = "070618_resourceAssessment.gdb"
inputNAME = os.path.join(mainOutputFolder, gdbFileName, "geothermal")

envEx_ls = [Cat1, Cat2, Cat3, Cat4]

## loop over each set of environmental exclusions for each category   
for cat in envEx_ls:
    for ex in cat:
        ft = inputNAME + cat[ex][0]
        print(ft)
        outputFile = inputNAME + cat[ex][1]
        print(outputFile)
        ## erase
        print("Erasing " + str(ex))
        arcpy.Erase_analysis(ft, ex, outputFile)

    ## Get outputfilename of last element of ordered dictionary
    #lastOutput = inputNAME + cat[next(reversed(cat))][1]


def calcSupplyCurve_geothermal(inFeature, inFeatureFileName, category, zonesFile, zonesToSelect, zonesType, zoneField):
        
    #############################
    ## CALC TOTAL MW PER STATE ##
    #############################
    
    ## Spatial join of points with zones (QRAs or SuperCREZs)
    inFeature_joined = arcpy.SpatialJoin_analysis(target_features = inFeature, join_features = zonesFile, \
                                               out_feature_class = inFeature + "_" + zonesType + "Joined", \
                                               join_operation = "JOIN_ONE_TO_ONE", join_type = "KEEP_ALL", match_option = "INTERSECT")
    
    
    print("Finished spatial join for " + inFeatureFileName)
    
    ## select zones to aggregate
    #inFeature_joined_select = arcpy.Select_analysis(in_features = inFeature_joined, \
    #                      out_feature_class = inFeature + "_resolveSelect", \
    #                      where_clause = zonesToSelect)
    
    ## summary statistics to get the total area per QRA; the resultant field in the table is "SUM_Area"
    MWtable = arcpy.Statistics_analysis(in_table = inFeature_joined, \
                                       out_table = "in_memory/inFeature_MWCalc", \
                                       statistics_fields = [["MW", "SUM"]], case_field = [zoneField])
    
    ## Rename field from SUM_Area to Area
    arcpy.AlterField_management(in_table = MWtable, field = "SUM_MW", new_field_name = "cap_MW_" + category, \
                                new_field_alias = "cap_MW_" + category)
    
    ############################################
    ## copy tables to hard drive as gdb table ##
    ############################################
    
    ## SAVE STATE AVERAGES to GDB table
    #arcpy.TableToTable_conversion(in_rows = MWtable, out_path = os.path.join(mainOutputFolder, outputGDB),\
    #                              out_name =  inFeatureFileName + csv_suffix)
    ## convert table to pandas df
    # get fields for use in Table to Numpy Array function
    #fields = arcpy.ListFields(os.path.join(mainOutputFolder, outputGDB, inFeatureFileName + csv_suffix))
    fields = arcpy.ListFields(MWtable)
    fieldList  = []
    for field in fields:
        fieldList.append(field.name)
        
    print(fieldList)
    
    pattern = r'cap_MW_\S|' + zoneField
    fieldList = [x for x in fieldList if re.search(pattern, x)]
    print("after selection: ")
    print(fieldList)
    
    ## convert gdb table to numpy array to Pandas DF:
    df = pandas.DataFrame(arcpy.da.TableToNumPyArray(MWtable, fieldList))
    
    print("FINISHED processing " + inFeatureFileName)   
    
    return df

###################
## APPLY TO QRAs ##
###################
    
## List of inputs to loop over
ft_ls = {"Cat1" : "geothermal_cat1b",\
        "Cat2" : "geothermal_cat2f",\
        "Cat3" : "geothermal_cat3", \
         "Cat4": "geothermal_cat4"}
tech = "geothermal"

## output list to append 
resolveZone_MW_ls = []
gdbFileName = "070618_resourceAssessment.gdb"
zoneFieldName = "RESOLVE_ZONE_geothermal"

## loop function over list of inputs
for cat in ft_ls:
    resolveZone_MW = calcSupplyCurve_geothermal(inFeature = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat]), \
                                  inFeatureFileName = ft_ls[cat], \
                                  category = cat, \
                                  zonesFile = QRAfilePath, \
                                  zonesType = "QRA", \
                                  ## zoneField = "State"
                                  zoneField = zoneFieldName, \
                                  zonesToSelect = "Name In ('NV_EA', 'NV_WE', 'OR_SO', 'OR_WE')")
    
    ## append output list
    resolveZone_MW_ls.append(resolveZone_MW)
    
## MERGE TABLES 
# StateAvg
resolveZone_MW_merged = pandas.merge(resolveZone_MW_ls[0], resolveZone_MW_ls[1], how= 'outer',  on = zoneFieldName)
for tab in [resolveZone_MW_ls[2], resolveZone_MW_ls[3]]:
    resolveZone_MW_merged = pandas.merge(resolveZone_MW_merged, tab, how= 'outer', on = zoneFieldName)

## SAVE TO CSV
resolveZone_MW_merged.to_csv(path_or_buf = os.path.join(mainOutputFolder, "0718_results", tech + "_OOS_RESOLVEZONE_MW.csv"), index = False)

#########################
## APPLY TO SuperCREZs ##
#########################

## output list to append 
resolveZone_MW_ls = []
gdbFileName = "070618_resourceAssessment.gdb"
zoneFieldName = "RESOLVE_ZONE"

## loop function over list of inputs
for cat in ft_ls:
    resolveZone_MW = calcSupplyCurve_geothermal(inFeature = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat]), \
                                  inFeatureFileName = ft_ls[cat], \
                                  category = cat, \
                                  zonesFile = SuperCREZ, \
                                  zonesType = "SuperCREZ", \
                                  zoneField = zoneFieldName, \
                                  zonesToSelect = "NAME In ('Imperial North', 'Imperial South', 'Round Mountain - A', 'Lassen North')")#,\
                                  #csv_suffix = "_RESOLVEzonesMW_SuperCREZ")
    
    ## append output list
    resolveZone_MW_ls.append(resolveZone_MW)
    
## MERGE TABLES 
# StateAvg
resolveZone_MW_merged = pandas.merge(resolveZone_MW_ls[0], resolveZone_MW_ls[1], how= 'outer',  on = zoneFieldName)
for tab in [resolveZone_MW_ls[2], resolveZone_MW_ls[3]]:
    resolveZone_MW_merged = pandas.merge(resolveZone_MW_merged, tab, how= 'outer', on = zoneFieldName)

## SAVE TO CSV
resolveZone_MW_merged.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, tech + "_CA_RESOLVEZONE_MW.csv"), index = False)


#########################
## APPLY TO STATES ##
#########################

## output list to append 
resolveZone_MW_ls = []
zoneFieldName = "State"

## loop function over list of inputs
for cat in ft_ls:
    resolveZone_MW = calcSupplyCurve_geothermal(inFeature = os.path.join(mainOutputFolder, gdbFileName, ft_ls[cat]), \
                                  inFeatureFileName = ft_ls[cat], \
                                  category = cat, \
                                  zonesFile = statesFilePath, \
                                  zonesType = "state", \
                                  zoneField = zoneFieldName,\
                                  zonesToSelect = "NAME In ('Imperial North', 'Imperial South', 'Round Mountain - A', 'Lassen North')")
    
    ## append output list
    resolveZone_MW_ls.append(resolveZone_MW)
    
## MERGE TABLES 
# StateAvg
resolveZone_MW_merged = pandas.merge(resolveZone_MW_ls[0], resolveZone_MW_ls[1], how= 'outer',  on = zoneFieldName)
for tab in [resolveZone_MW_ls[2], resolveZone_MW_ls[3]]:
    resolveZone_MW_merged = pandas.merge(resolveZone_MW_merged, tab, how= 'outer', on = zoneFieldName)

## SAVE TO CSV
resolveZone_MW_merged.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, tech + "_state_MW.csv"), index = False)


elapsed_time = (time.time() - start_time)/(60)
print(str(elapsed_time) + " minutes")


''' ==============================================================
############################################
## SUM BASELINE RESOURCES BY RESOLVE_ZONE ##
############################################
'''
df_baseline = pandas.read_csv(r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\RESOLVE_related_data\RESOLVE-CPUCRPS_listComparison_AllTechSum_EL_noBaselineOOS.csv")

#df_baseline_melt = pandas.melt(df_baseline, id_vars=["RESOLVE_ZONE", "Row Labels"], var_name="Technology", value_name="MW")
#df_baseline_melt = df_baseline_melt.drop(columns=["Row Labels"])
#df_baseline_melt['MW'] = df_baseline_melt['MW'].convert_objects(convert_numeric=True)
#df_baseline_RESOLVEZONE_sum = df_baseline_melt.groupby(['RESOLVE_ZONE', "Technology"]).sum()


df_baseline['Geothermal'] = df_baseline['Geothermal'].convert_objects(convert_numeric=True) 
df_geo =df_baseline[["RESOLVE_ZONE","Geothermal"]].groupby(['RESOLVE_ZONE']).sum()
df_geo.reset_index(inplace=True)
df_geo.to_csv(path_or_buf = r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\RESOLVE_related_data\geothermal_baseline_noBaselineOOS.csv", index = True)

df_baseline['Solar PV'] = df_baseline['Solar PV'].convert_objects(convert_numeric=True) 
df_PV =df_baseline[["RESOLVE_ZONE","Solar PV"]].groupby(['RESOLVE_ZONE']).sum()
df_PV.reset_index(inplace=True)
df_PV.to_csv(path_or_buf = r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\RESOLVE_related_data\PV_baseline_noBaselineOOS.csv", index = True)

df_baseline['Wind'] = df_baseline['Wind'].convert_objects(convert_numeric=True) 
df_wind =df_baseline[["RESOLVE_ZONE","Wind"]].groupby(['RESOLVE_ZONE']).sum()
df_wind.reset_index(inplace=True)
df_wind.to_csv(path_or_buf = r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\RESOLVE_related_data\wind_baseline_noBaselineOOS.csv", index = True)

''' ==============================================================
####################################################
## SUBTRACT BASELINE RESOURCES FROM MW ESTIMATES ##
###################################################
'''
## import RESOLVE supply curve values:
resolveSupplyCurve = pandas.read_csv(r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\siteSuitabilityOutputs\0618_results_archived\summaryResults_061818.csv")

## import STPOSTAL_RESOLVEZONE_key csv:
stpostalKey = pandas.read_csv(r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\RESOLVE_related_data\STPOSTAL_RESOLVEZONE_key.csv")


def subtractBaseline (df_merged, baselineColName):
    pattern = r'cap_MW_\S'
    MWcolList = [x for x in list(df_merged) if re.search(pattern, x)]
    
    for col in df_merged:
        if col in MWcolList:
            df_merged[col + "_net"] = df_merged[col].sub(df_merged[baselineColName],fill_value=0)
    
    return df_merged

###########
## WIND ##
###########
    
## Updates on 11/30/18: No longer subtracting baseline resources from site suitability results for OOS RESOLVE ZONE or State-wide because we erased 
## wind and solar existing power plants when creating the potential project area feature classes
## instead, subtract 500 MW from NM and 1500 MW from PNW
    
extTxMW = pandas.DataFrame(data = {'RESOLVE_ZONE_wind': ["New_Mexico_Wind", "Pacific_Northwest_Wind"], 'extTxZones' : [500, 1500]})
    
## import wind zones - OOS
df_wind_OOS_RESOLVE = pandas.read_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "wind_OOS_RESOLVEZONE_avgCFMW_PA.csv"))
## subtract 500 MW from NM and 1500 MW from PNW
df_wind_OOS_RESOLVE_merged = pandas.merge(df_wind_OOS_RESOLVE, extTxMW, how= 'left', left_on = "RESOLVE_ZONE_wind", right_on = "RESOLVE_ZONE_wind")
df_wind_OOS_RESOLVE_merged_sub = subtractBaseline(df_merged= df_wind_OOS_RESOLVE_merged, baselineColName = "extTxZones")
## rename columns:
newColNames =[name.replace('_RESOLVE_ZONE',"") for name in df_wind_OOS_RESOLVE_merged_sub.columns]
df_wind_OOS_RESOLVE_merged_sub.columns = newColNames
## save to csv:
df_wind_OOS_RESOLVE_merged_sub.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "wind_OOS_RESOLVEZONE_avgCFMW_PA_net.csv"), index = False)

## import wind zones - CA
df_wind_CA_RESOLVE = pandas.read_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "wind_CA_RESOLVEZONE_avgCFMW_PA.csv"))
## join the df_baseline table using RESOLVE_ZONE
df_wind_CA_RESOLVE_merged = pandas.merge(df_wind, df_wind_CA_RESOLVE, how= 'right', left_on = "RESOLVE_ZONE", right_on = "RESOLVE_ZONE")
## apply substractBaseline function 
df_wind_CA_RESOLVE_merged_sub = subtractBaseline(df_merged= df_wind_CA_RESOLVE_merged, baselineColName = "Wind")
## Append "_Wind" to end of RESOLVE_ZONE name:
df_wind_CA_RESOLVE_merged_sub["RESOLVE_ZONE"] =  df_wind_CA_RESOLVE_merged_sub['RESOLVE_ZONE'].astype(str) + "_Wind"
df_wind_CA_RESOLVE_merged_sub.rename(columns={'RESOLVE_ZONE':'RESOLVE_ZONE_wind'}, inplace=True)
## merge with RESOLVE supply curve values
#df_wind_CA_RESOLVE_merged_sub_compare = pandas.merge(resolveSupplyCurve, df_wind_CA_RESOLVE_merged_sub, how = "outer", left_on = "RESOLVE Resource Name",right_on = "RESOLVE_ZONE")
## save to csv:
df_wind_CA_RESOLVE_merged_sub.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "wind_CA_RESOLVEZONE_avgCFMW_PA_net.csv"), index = False)



## import wind zones - WALL TO WALL
df_wind_state = pandas.read_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "wind_OOS_state_avgCFMW_PA.csv"))
## merge STPOSTAL key to get RESOLVEZONE names
#df_wind_state = pandas.merge(stpostalKey[["STPOSTAL", "RESOLVE_ZONE_wind"]], df_wind_state, how = "outer", left_on = "STPOSTAL",right_on = "STPOSTAL")
#df_wind_state.groupby(["RESOLVE_ZONE_wind"])[]
## subtract 500 MW from NM and 1500 MW from PNW
df_wind_state_merged = pandas.merge(df_wind_state, extTxMW, how= 'left', left_on = "RESOLVE_ZONE_wind", right_on = "RESOLVE_ZONE_wind")

df_wind_state_merged_sub = subtractBaseline(df_merged= df_wind_state_merged, baselineColName = "extTxZones")
## save to csv:
df_wind_state_merged_sub.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "wind_OOS_state_avgCFMW_PA_net.csv"), index = False)


###########
## SOLAR ##
###########

## import PV zones - OOS : no need to subtract baseline
df_PV_OOS_RESOLVE = pandas.read_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "solar_OOS_RESOLVEZONE_avgCFMW_PA.csv"))
## rename columns:
newColNames =[name.replace('_RESOLVE_ZONE',"") for name in df_PV_OOS_RESOLVE.columns]
df_PV_OOS_RESOLVE.columns = newColNames
## join the df_baseline table using RESOLVE_ZONE
df_PV_OOS_RESOLVE_merged = pandas.merge(df_PV, df_PV_OOS_RESOLVE, how= 'right', left_on = "RESOLVE_ZONE", right_on = "RESOLVE_ZONE_solar")
## Delete first RESOLVE_ZONE Column in df_PV:
df_PV_OOS_RESOLVE_merged = df_PV_OOS_RESOLVE_merged.drop(["RESOLVE_ZONE"], axis = 1)
## apply substractBaseline function 
df_PV_OOS_RESOLVE_merged = subtractBaseline(df_merged= df_PV_OOS_RESOLVE_merged, baselineColName = "Solar PV")
## join the df_baseline table using RESOLVE_ZONE
#df_PV_OOS_RESOLVE_merged = pandas.merge(df_PV, df_PV_OOS_RESOLVE, how= 'right', left_on = "RESOLVE_ZONE", right_on = "RESOLVE_ZONE_solar")
## apply substractBaseline function 
#df_PV_OOS_RESOLVE_merged_sub = subtractBaseline(df_merged= df_PV_OOS_RESOLVE_merged, baselineColName = "Solar PV")
## merge with RESOLVE supply curve values
#df_PV_OOS_RESOLVE_merged_sub_compare = pandas.merge(resolveSupplyCurve, df_PV_OOS_RESOLVE_merged_sub, how = "outer", left_on = "RESOLVE Resource Name", right_on = "RESOLVE_ZONE_solar")
## save to csv:
df_PV_OOS_RESOLVE_merged.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "solar_OOS_RESOLVEZONE_avgCFMW_PA_renamedCol.csv"), index = False)

## import PV zones - CA
df_PV_CA_RESOLVE = pandas.read_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "solar_CA_RESOLVEZONE_avgCFMW_PA.csv"))
## join the df_baseline table using RESOLVE_ZONE
df_PV_CA_RESOLVE_merged = pandas.merge(df_PV, df_PV_CA_RESOLVE, how= 'right', left_on = "RESOLVE_ZONE", right_on = "RESOLVE_ZONE")
## apply substractBaseline function 
df_PV_CA_RESOLVE_merged_sub = subtractBaseline(df_merged= df_PV_CA_RESOLVE_merged, baselineColName = "Solar PV")
## Append "_Solar" to end of RESOLVE_ZONE name:
df_PV_CA_RESOLVE_merged_sub["RESOLVE_ZONE"] =  df_PV_CA_RESOLVE_merged_sub['RESOLVE_ZONE'].astype(str) + "_Solar"
df_PV_CA_RESOLVE_merged_sub.rename(columns={'RESOLVE_ZONE':'RESOLVE_ZONE_solar'}, inplace=True)
## merge with RESOLVE supply curve values
df_PV_CA_RESOLVE_merged_sub_compare = pandas.merge(resolveSupplyCurve, df_PV_CA_RESOLVE_merged_sub, how = "outer", left_on = "RESOLVE Resource Name",right_on = "RESOLVE_ZONE_solar")
## save to csv:
df_PV_CA_RESOLVE_merged_sub_compare.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "solar_CA_RESOLVEZONE_avgCFMW_PA_net.csv"), index = False)


## import PV zones - State
df_PV_state = pandas.read_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "solar_OOS_state_avgCFMW_PA.csv"))
## join the df_baseline table using RESOLVE_ZONE
df_PV_state_merged = pandas.merge(df_PV, df_PV_state, how= 'right', left_on = "RESOLVE_ZONE", right_on = "RESOLVE_ZONE_solar")
## Delete first RESOLVE_ZONE Column in df_PV:
df_PV_state_merged = df_PV_state_merged.drop(["RESOLVE_ZONE"], axis = 1)
## apply substractBaseline function 
df_PV_state_merged_sub = subtractBaseline(df_merged= df_PV_state_merged, baselineColName = "Solar PV")
## merge with RESOLVE supply curve values
#df_PV_state_merged_sub_compare = pandas.merge(resolveSupplyCurve, df_PV_state_merged, how = "outer", left_on = "RESOLVE Resource Name", right_on = "RESOLVE_ZONE_solar")
## save to csv:
df_PV_state_merged_sub.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "solar_OOS_state_avgCFMW_PA_net.csv"), index = False)


########################################
## MERGE SOLAR AND WIND SUPPLY CURVES ##
########################################

####### RESOLVE ZONES:

## WIND: concat OOS and CA RESOLVE ZONE supply curves and then merge with original RESOLVE supply curve values
RESOLVE_ZONES_wind_merged = pandas.concat([df_wind_OOS_RESOLVE_merged_sub, df_wind_CA_RESOLVE_merged_sub], axis = 0)
RESOLVE_ZONES_wind_merged.rename(columns={"RESOLVE_ZONE_wind": "RESOLVE_ZONE"}, inplace=True)

## SOLAR: concat OOS and CA RESOLVE ZONE supply curves and then merge with original RESOLVE supply curve values
RESOLVE_ZONES_solar_merged = pandas.concat([df_PV_OOS_RESOLVE_merged, df_PV_CA_RESOLVE_merged_sub], axis = 0)
RESOLVE_ZONES_solar_merged.rename(columns={"RESOLVE_ZONE_solar": "RESOLVE_ZONE"}, inplace=True)

## merge WIND AND SOLAR
RESOLVE_ZONES_merged = pandas.concat([RESOLVE_ZONES_solar_merged, RESOLVE_ZONES_wind_merged], axis = 0)

## merge with RESOLVE supply curve values
RESOLVE_ZONES_merged_compare = pandas.merge(resolveSupplyCurve, RESOLVE_ZONES_merged, how = "outer", left_on = "RESOLVE Resource Name",right_on = "RESOLVE_ZONE")
RESOLVE_ZONES_merged_compare= RESOLVE_ZONES_merged_compare.drop(["Unnamed: 0"], axis = 1)

## save to csv
RESOLVE_ZONES_merged_compare.to_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "supplyCurvesForRESOLVE", "envSupplyCurves_RESOLVEZONES.csv"), index=False)

####### WALL TO WALL:
## merge WIND AND SOLAR
df_wind_state_merged_sub.rename(columns={"RESOLVE_ZONE_wind": "RESOLVE_ZONE"}, inplace=True)
        
w2w_merged = pandas.concat([df_PV_state_merged_sub, \
                            df_wind_state_merged_sub], axis =0)

## merge with RESOLVE supply curve values
w2w_merged_compare = pandas.merge(resolveSupplyCurve, w2w_merged, how = "outer", left_on = "RESOLVE Resource Name",right_on = "RESOLVE_ZONE")
## save to csv
w2w_merged_compare.to_csv(os.path.join(mainOutputFolder, supplyCurveFolder, "supplyCurvesForRESOLVE", "envSupplyCurves_w2w.csv"), index=False)


################
## GEOTHERMAL ##
################

## import geothermal zones - OOS
df_geo_OOS_RESOLVE = pandas.read_csv(r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\siteSuitabilityOutputs\0718_results\geothermal_OOS_RESOLVEZONE_MW.csv")
## join the df_baseline table using RESOLVE_ZONE
df_geo_OOS_RESOLVE_merged = pandas.merge(df_geo, df_geo_OOS_RESOLVE, how= 'right', left_on = "RESOLVE_ZONE", right_on = "RESOLVE_ZONE_geothermal")
## apply substractBaseline function 
df_geo_OOS_RESOLVE_merged_sub = subtractBaseline(df_merged= df_geo_OOS_RESOLVE_merged, baselineColName = "Geothermal")
## merge with RESOLVE supply curve values
df_geo_OOS_RESOLVE_merged_sub_compare = pandas.merge(resolveSupplyCurve, df_geo_OOS_RESOLVE_merged_sub, how = "outer", left_on = "RESOLVE Resource Name", right_on = "RESOLVE_ZONE_geothermal")
## save to csv:
df_geo_OOS_RESOLVE_merged_sub_compare.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "geothermal_OOS_RESOLVEZONE_MW_net.csv"), index = False)

## import geothermal zones - CA
df_geo_CA_RESOLVE = pandas.read_csv(r"C:\Users\Grace\Documents\TNC_beyond50\PathTo100\siteSuitabilityOutputs\0718_results\geothermal_CA_RESOLVEZONE_MW.csv")
## join the df_baseline table using RESOLVE_ZONE
df_geo_CA_RESOLVE_merged = pandas.merge(df_geo, df_geo_CA_RESOLVE, how= 'right', left_on = "RESOLVE_ZONE", right_on = "RESOLVE_ZONE")
## apply substractBaseline function 
df_geo_CA_RESOLVE_merged_sub = subtractBaseline(df_merged= df_geo_CA_RESOLVE_merged, baselineColName = "Geothermal")
## Append "_Solar" to end of RESOLVE_ZONE name:
df_geo_CA_RESOLVE_merged_sub["RESOLVE_ZONE"] =  df_geo_CA_RESOLVE_merged_sub['RESOLVE_ZONE'].astype(str) + "_Geothermal"
## merge with RESOLVE supply curve values
df_geo_CA_RESOLVE_merged_sub_compare = pandas.merge(resolveSupplyCurve, df_geo_CA_RESOLVE_merged_sub, how = "outer", left_on = "RESOLVE Resource Name",right_on = "RESOLVE_ZONE")
## save to csv:
df_geo_CA_RESOLVE_merged_sub_compare.to_csv(path_or_buf = os.path.join(mainOutputFolder, supplyCurveFolder, "geothermal_CA_RESOLVEZONE_MW_net.csv"), index = False)
