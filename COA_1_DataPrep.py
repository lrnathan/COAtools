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


##SHEDS files come in six different zip files (covariates_01-06 and spatial_01-06)
##based on state of interest, download the following:
##Maine: 1
##New Hampshire: 1
##Vermont: 1,2,4
##Massachusets: 1,2
##Connecticut: 1,2
##Rhode Island: 1
##New York: 1,2,4,5
##New Jersey: 2
##Pennsylvania:2,4,5
##Delaware: 2
##Maryland: 2,5
##Virginia: 3,6
##North Carolina: 3,5,6
##Ohio: 4,5
##West Virginia: 5
##Kentucky: 5,6
##Tennessee: 6

#############################################################################################
##                       Step 0: Merge EBTJV and SHEDS datafiles                           ##
#############################################################################################


#############################################################################################
##                         Import modules and specify tool inputs                          ##
#############################################################################################

## import modules
import arcpy, csv, os, sys
from time import time

## allow outputs to be overwritten
arcpy.env.overwriteOutput = 1

##toolbox inputs
patches=sys.argv[1]

##SHEDS catchments
catchments=sys.argv[2]
##SHEDS local/upstream Data Files
shedsFilesLoc=sys.argv[3]
##SHEDS riparian Data Files
shedsFilesRip=sys.argv[4]
##SHEDS truncated flowlines
NHDflow=sys.argv[5]
##huc 8 for flowline clip
huc8poly=sys.argv[6]
##hucs for COAs
hucs=sys.argv[7]

##subset by
byState=sys.argv[8]
state=sys.argv[9]
byPolygon=sys.argv[10]
polygon=sys.argv[11]
selectType=sys.argv[12]
#catchment subset type
selectType2=sys.argv[13]

##output coordinate system
outputCoord=sys.argv[14]
##output Directory
outputDir=sys.argv[15]


#############################################################################################
##           							 EBTJV patches                                     ##
#############################################################################################
##by state
if byState == "true":
	#set file subset name to state
	subsetFileName=state
	arcpy.AddMessage("\nSUBSETTNG BY STATE: %s\nSAVING ALL FILES TO: %s\n\n"%(state,outputDir))
	#project patch layer
	arcpy.Project_management(patches, "patchesProj", outputCoord)
	#create feature layer from EBTJV patch shapefile
	arcpy.MakeFeatureLayer_management("patchesProj", "patchesLyr")
	#specify output file
	patchSub=os.path.join(outputDir,"EBTJV_patches_%s.shp"%state)
	#subset to state and export
	arcpy.Select_analysis("patchesLyr", patchSub,"STATE = '%s'"%state)
	arcpy.AddMessage("EBTJV patch subset saved to: EBTJV_patches_%s.shp"%state)

##by polygon (e.g. watershed or management region)
elif byPolygon== "true":
	#get polygon Name
	subsetFileName=os.path.splitext(os.path.basename(polygon))[0]
	arcpy.AddMessage("\nSUBSETTNG BY POLYGON FILE: %s\nSAVING ALL FILES TO: %s\n\n"%(subsetFileName,outputDir))
	#project patch layer
	arcpy.Project_management(patches, "patchesProj", outputCoord)
	#create feature layer from EBTJV patch shapefile
	arcpy.MakeFeatureLayer_management("patchesProj", "patchesLyr")
	#select patches in polygon-- can specify "within", "completely within", or "have center in"
	arcpy.SelectLayerByLocation_management("patchesLyr",selectType,polygon)
	#specify output file
	patchSub=os.path.join(outputDir,"EBTJV_patches_%s.shp"%subsetFileName)
	#save shapefile
	arcpy.CopyFeatures_management("patchesLyr", patchSub)
	arcpy.AddMessage("EBTJV patch subset saved to: EBTJV_patches_%s.shp"%subsetFileName)

##if neither subset option is selected, return error and quit
else: 
	arcpy.AddError("ERROR: no subset selection indicated. Must select either 'by state' or 'by polygon'")
	quit()


#############################################################################################
##           						SHEDS catchments                                       ##
#############################################################################################
if catchments != "#":
	start = time()
	arcpy.AddMessage("\nStarting SHEDS catchment subset..")
	##merge shapfile
	arcpy.Merge_management(catchments, "SHEDSmerge")  
	#project catchment layer
	arcpy.Project_management("SHEDSmerge", "catchesProj", outputCoord)
	#create feature layer from EBTJV patch shapefile
	arcpy.MakeFeatureLayer_management("catchesProj", "catchLyr")
	#select catchments that intersect patches-- can specify "within", "completely within", or "have center in"
	arcpy.SelectLayerByLocation_management("catchLyr",selectType2,patchSub)
	##specify output file
	SHEDSout=os.path.join(outputDir,"Catchments_"+subsetFileName+".shp")
	#save shapefile
	arcpy.CopyFeatures_management("catchLyr", SHEDSout)
	#print output location
	arcpy.AddMessage("SHEDS Catchment File saved to: Catchments_%s.shp"%subsetFileName)
	
	##get catchment IDs in subsetted file for subsetting SHEDS data files
	catchIDs=[]
	#create search cursor
	rows=arcpy.SearchCursor(SHEDSout)
	##for each catchment in spatial join
	for row in rows:
		#get catchID and patchID
		catchIDs.append(int(float(row.getValue("featureid"))))
	del row, rows
	end = time()
	arcpy.AddMessage("Finished in "+str(round(((end-start)/60),2))+" Minutes")
	
#############################################################################################
##           	                SHEDS local/upstream data files                            ##
#############################################################################################
if shedsFilesLoc != "#":
	arcpy.AddMessage("\nStarting SHEDS local/upstream data subset..")
	#store in list
	shedsFilesList=shedsFilesLoc.split(";")
	#create output file name (SHEDS_DATA_subset.csv)
	outFileName=os.path.join(outputDir,"SHEDS_LocUp_Data_"+subsetFileName+".csv")
	#open output file
	outFile =open(outFileName, "wb")
	#create csv writer
	writer=csv.writer(outFile)
	for s in range(0,len(shedsFilesList)):
		start = time()
		#open input SHEDS data file
		infile=open(shedsFilesList[s],"rb")
		#create csv reader
		reader=csv.reader(infile)
		#start counter
		i=0
		#loop through SHEDS file
		for row in reader:
			#print header only if it's the first file
			if(i==0):
				catchIndex=row.index("featureid")
				if(s==0):
					writer.writerow(row)
			else:
				#if catchment is in subset catchment file, export row to file
				if int(float(row[catchIndex])) in catchIDs:
					writer.writerow(row)
			i=i+1
		#close files
		infile.close()
		end = time()
		timeMinutes=str(round(((end-start)/60),2))
		arcpy.AddMessage("Finished %s in %s Minutes"%(os.path.basename(shedsFilesList[s]),timeMinutes))
	outFile.close()
	#print status
	arcpy.AddMessage("SHEDS local/upstream data saved to: SHEDS_LocUp_Data_%s.csv"%subsetFileName)
	

#############################################################################################
##           	                 SHEDS riparian data files                                 ##
#############################################################################################
if shedsFilesRip != "#":
	arcpy.AddMessage("\nStarting SHEDS riparian data subset..")
	#store in list
	shedsFilesRip=shedsFilesRip.split(";")
	#create output file name
	outFileName=os.path.join(outputDir,"SHEDS_Rip_Data_"+subsetFileName+".csv")
	#open output file
	outFile =open(outFileName, "wb")
	#create csv writer
	writer=csv.writer(outFile)
	for s in range(0,len(shedsFilesRip)):
		start = time()
		#open input SHEDS data file
		infile=open(shedsFilesRip[s],"rb")
		#create csv reader
		reader=csv.reader(infile)
		#start counter
		i=0
		#loop through SHEDS file
		for row in reader:
			#print header only if it's the first file
			if(i==0):
				catchIndex=row.index("featureid")
				if(s==0):
					writer.writerow(row)
			else:
				#if catchment is in subset catchment file, export row to file
				if int(float(row[catchIndex])) in catchIDs:
					writer.writerow(row)
			i=i+1
		#close files
		infile.close()
		end = time()
		timeMinutes=str(round(((end-start)/60),2))
		arcpy.AddMessage("Finished %s in %s Minutes"%(os.path.basename(shedsFilesList[s]),timeMinutes))
	outFile.close()
	#print status
	arcpy.AddMessage("SHEDS riparian data saved to: SHEDS_Rip_Data_%s.csv"%subsetFileName)


#############################################################################################
##           				         NHD Truncated Flowline                                ##
#############################################################################################
if NHDflow != "#":
	start = time()
	arcpy.AddMessage("\nStarting flowline shapefile subset..")


	##subset HUC8 based on subsetted EBTJV patches
	#project HUC layer
	arcpy.Project_management(huc8poly, "huc8Proj", outputCoord)
	#create feature layer
	arcpy.MakeFeatureLayer_management("huc8Proj", "huc8Lyr")
	#create point layer from patches to use in select by location
	arcpy.FeatureToPoint_management(patchSub, "patchCentroids", point_location="INSIDE")
	#select huc watersheds that have patch centroids in them
	arcpy.SelectLayerByLocation_management("huc8Lyr","INTERSECT","patchCentroids")
	#specify output file
	huc8subset=os.path.join(outputDir,os.path.splitext(os.path.basename(huc8poly))[0]+"_"+subsetFileName+".shp")
	#save shapefile
	arcpy.CopyFeatures_management("huc8Lyr", huc8subset)
	#calculate area; stored as "AREA_GEO"
	arcpy.AddGeometryAttributes_management(huc8subset,Geometry_Properties="AREA_GEODESIC",Area_Unit="SQUARE_KILOMETERS")	
	#print status
	arcpy.AddMessage("HUC8 Watershed subset saved to: %s"%(os.path.splitext(os.path.basename(huc8poly))[0]+"_"+subsetFileName+".shp"))

	##merge flowline shapfiles
	arcpy.Merge_management(NHDflow, "flowMerge") 
	#project flowline layer
	arcpy.Project_management("flowMerge", "flowProj", outputCoord)
	#create feature layer from merged flowline shapefile
	arcpy.MakeFeatureLayer_management("flowProj", "flowLyr")
	#select catchments that intersect patches
	arcpy.SelectLayerByLocation_management("flowLyr","WITHIN",huc8subset)
	##specify output file
	flowOut=os.path.join(outputDir,"Flowline_"+subsetFileName+".shp")
	#save shapefile
	arcpy.CopyFeatures_management("flowLyr", flowOut)
	arcpy.AddMessage("Flowline File saved to: Flowline_%s.shp"%flowOut)
	end = time()
	timeMinutes=str(round(((end-start)/60),2))
	arcpy.AddMessage("Finished in %s Minutes"%timeMinutes)
	
#############################################################################################
##           				               COA HUCs                                        ##
#############################################################################################
##subset HUC based on subsetted EBTJV patches
if hucs != "#":
	start = time()
	arcpy.AddMessage("\nStarting HUC shapefile subset..")
	#store in list
	hucs=hucs.split(";")
	for huc in hucs:
		#project HUC layer
		arcpy.Project_management(huc, "hucProj", outputCoord)
		#create feature layer
		arcpy.MakeFeatureLayer_management("hucProj", "hucLyr")
		#create point layer from patches to use in select by location
		arcpy.FeatureToPoint_management(patchSub, "patchCentroids", point_location="INSIDE")
		#select huc watersheds that have patch centroids in them
		arcpy.SelectLayerByLocation_management("hucLyr","INTERSECT","patchCentroids")
		#specify output file
		hucSubset=os.path.join(outputDir,os.path.splitext(os.path.basename(huc))[0]+"_"+subsetFileName+".shp")
		#save shapefile
		arcpy.CopyFeatures_management("hucLyr", hucSubset)
		#calculate area; stored as "AREA_GEO"
		arcpy.AddGeometryAttributes_management(hucSubset,Geometry_Properties="AREA_GEODESIC",Area_Unit="SQUARE_KILOMETERS")
		#print status
		arcpy.AddMessage("HUC Watershed subset saved to: %s"%(os.path.splitext(os.path.basename(huc))[0]+"_"+subsetFileName+".shp"))
	end = time()
	timeMinutes=str(round(((end-start)/60),2))
	arcpy.AddMessage("Finished in %s Minutes"%timeMinutes)