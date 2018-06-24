## Part of Conservation Opportunity Area (COA) toolbox V1.0
##
## Uses Eastern Brook Trout Joint Venture (EBTJV) patch layer and SHEDS catchment data
## to identify conservation opporunitiy areas (COA) based on:
##1) patch characteristics (sourced from SHEDS)
##2) area of patch 
##3) distance between patches
##
##Author: Lucas Nathan
##Contact: lucas.nathan@uconn.edu
##

##**Be sure to download the most updated versions of both layers**
##All data available from: http://www.ecosheds.org/




#############################################################################################
##             Step 2: Measure Distance between patches using Network Analyst              ##
#############################################################################################

## import modules
import arcpy,os

## Check out any necessary licenses
arcpy.CheckOutExtension("Network")

## allow outputs to be overwritten
arcpy.env.overwriteOutput = 1

##toolbox inputs
patches=sys.argv[1]
streams=sys.argv[2]
streamNetwork=sys.argv[3]
distThresh=sys.argv[4] # in KM

#get directory from input file
outDir=os.path.splitext(os.path.dirname(patches))[0]

##create points at the intersections of streams and patch edges for use in distance calculation
patchPointTemp=os.path.join(outDir,"patchPointTemp.shp")
arcpy.Intersect_analysis([streams,patches],patchPointTemp,output_type="POINT")

##explode multipoint objects
patchPoints=os.path.join(outDir,"patchPoints.shp")
arcpy.MultipartToSinglepart_management(patchPointTemp, patchPoints)



arcpy.AddMessage("Starting Distance Measurements Between Patches...")

##make new service area analysis
distThreshMeters=float(distThresh)*1000
arcpy.MakeServiceAreaLayer_na(streamNetwork,"ServiceArea","Length",default_break_values=distThreshMeters)

##Process: Add Locations, using PatchID (Feat_ID) as name
arcpy.AddMessage("Adding Points to Network Dataset...")
arcpy.AddLocations_na("ServiceArea", "Facilities", patchPoints,"Name Feat_ID #",append="CLEAR")

##Solve
arcpy.AddMessage("Solving Network Analysis (longest step)...")
arcpy.Solve_na("ServiceArea", "SKIP", "TERMINATE", "")


##save polygons
distPoly=os.path.join(outDir,"distPoly"+distThresh+"km.shp")
arcpy.CopyFeatures_management(r"ServiceArea\Polygons",distPoly)

##spatial join with patch points (i.e. what other patches are within the polygon/service area?)
spaJoinPoly=os.path.join(outDir,"spaJoinPoly"+distThresh+"km.shp")
arcpy.SpatialJoin_analysis(distPoly,patches,spaJoinPoly,"JOIN_ONE_TO_MANY",match_option="INTERSECT")
arcpy.AddMessage("Spatil Joinn File saved as %s"%spaJoinPoly)

##delete intermediate files
arcpy.Delete_management(patchPointTemp)
arcpy.Delete_management(patchPoints)
arcpy.Delete_management(distPoly)