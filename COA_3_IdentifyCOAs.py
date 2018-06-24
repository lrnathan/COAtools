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
##                       Identify Patches using specified criteria                         ##
#############################################################################################

## import modules
import arcpy, csv, os, sys

##toolbox input shapefiles
patches=sys.argv[1]
shedsCatch=sys.argv[2]
spaJoinPoly=sys.argv[3]
COAhucs=sys.argv[4]

##SHEDS Data Files
shedsUpLocDAT=sys.argv[5]
shedsRipDAT=sys.argv[6]
dataFiles=[shedsUpLocDAT,shedsRipDAT]

##Classification criteria
##area based on "Percentile" or "Area" (i.e. raw value)?
areaType=sys.argv[7]
areaThresh=float(sys.argv[8])

##riverscape variables
var1Level=sys.argv[9]
var1=sys.argv[10]
var2Level=sys.argv[11]
var2=sys.argv[12]
var3Level=sys.argv[13]
var3=sys.argv[14]
varList=[var1,var2,var3]
varLevels=[var1Level,var2Level,var3Level]

##make lists of input variables
vars=[]
#varLevelSQL=[]
varThresh=[]
for v in range(0,len(varList)):
    if varList[v] != '#':
		vars.append(varList[v].split("AND")[0].strip('"variable" = ').strip('\'"'))
		#varLevelSQL.append(varList[v].split("AND")[1].strip('"zone" = ').strip('\'"'))
		varThresh.append(varList[v].split("AND")[1].strip('"value" '))

##outputs
patchOut=sys.argv[15]
COAout=sys.argv[16]


##working directory
#get directory from input file
outDir=os.path.splitext(os.path.dirname(patches))[0]
arcpy.env.workspace=outDir
## allow outputs to be overwritten
arcpy.env.overwriteOutput = 1

##create new patch layer to modify
arcpy.CopyFeatures_management(patches,patchOut)
##create new COA layer to modify
arcpy.CopyFeatures_management(COAhucs,COAout)

################################################################################################################
##                  Run spatial join to identify SHEDS catchment in each EBTJV patch						  ##
################################################################################################################

##identify SHEDS catchments in each EBTJV patch using spatial join
arcpy.SpatialJoin_analysis(shedsCatch,patches,"patchCatchSpaJoin.shp",match_option="HAVE_THEIR_CENTER_IN")


 
################################################################################################################
##                               Store EBTJV patch and SHEDS catchment IDs                                    ##
################################################################################################################
catchJoinIDs=[]
patchJoinIDs=[]
##create search cursor for spatial join file 
rows=arcpy.SearchCursor("patchCatchSpaJoin.shp")
##for each catchment in spatial join
for row in rows:
	#get catchID and patchID
	catchJoinIDs.append(int(row.getValue("featureid")))
	patchJoinIDs.append(int(row.getValue("Feat_ID")))
del row, rows
		
		
################################################################################################################
##                                             Area Threshold                                                 ##
################################################################################################################

##create list for patches above threshold
patchArea=[]
patchIDs=[]
patchAreas=[]
##create search cursor for patches 
rows=arcpy.SearchCursor(patchOut)

##for each patch in patches shapefile...
for row in rows:
    #get patchID
    patchID=int(row.getValue("Feat_ID"))
    #store in list
    patchIDs.append(patchID)
    #get patch size
    area=row.getValue("Area_HA")
    #store in list
    patchAreas.append(area)
    
##delete cursors
del row, rows

#if area threshold is based on raw value (HA)
if areaType=="Area":
    #print area treshold
    arcpy.AddMessage("Area threshold set at %s HA"%areaThresh)
    for p in range(1,len(patchIDs)):
        #if patch is smaller than threshold
        if patchAreas[p] < float(areaThresh):
            #append patchID to list
            patchArea.append(patchIDs[p])
            
#if area threshold is based on percentile
elif areaType=="Percentile":
    #sort patch areas and store in new object
	patchAreasSorted=sorted(patchAreas)
    #get total number of patches
	numPatches=len(patchAreasSorted)
	#get the minimum patch area based on ith patch, using the sorted list and percentile
	areaCutoff=patchAreasSorted[numPatches-int(numPatches*float(areaThresh))]
    #print area treshold
	arcpy.AddMessage("Area threshold based on %s percentile: %s HA"%(areaThresh,round(areaCutoff)))
	for p in range(1,len(patchIDs)):
        #if patch is smaller than threshold
		if patchAreas[p] < float(areaCutoff):
			#append patchID to list
			patchArea.append(patchIDs[p])
#if the area treshold specified isn't "area" or "precentile", quit script and print error
else:
    arcpy.AddMessage("ERROR: area threshold specified isn't 'Area' or 'Percentile'.. potential typo in use input")
    quit()

################################################################################################################
##                                         Distance Threshold                                                 ##
################################################################################################################
#arcpy.AddMessage("Distance Threshold = %s meters"%distThresh)


##create blank lists to store pairs of patches that are within threshold
patch1=[]
patch2=[]
patchDist=[]

##create search cursor for patches 
rows=arcpy.SearchCursor(spaJoinPoly)

##for each patch in patches shapefile...
for row in rows:
    #get patchID
	name=row.getValue("Name")
	#split by ':', store in list
	patch1Temp=int(name.split(":")[0])
	patch1.append(patch1Temp)
	#get second patch
	patch2Temp=int(row.getValue("Feat_ID"))
	patch2.append(patch2Temp)
	#if it is two different patches add both to list (i.e. they are within threshold of another patch)
	if patch1Temp != patch2Temp:
		patchDist.append(patch1Temp)
		patchDist.append(patch2Temp)

##delete search cursor
del row, rows



	
################################################################################################################
##                                   Riverscape ("Restore") Variables                                         ##
################################################################################################################
patchVarLists=[]
counter=0
for v in range(0,len(varList)):
	if varList[v] != '#':
		arcpy.AddMessage("Starting Riverscape Classification: %s"%varList[v])
		catchIDvar=[]
		rowCount=0
		NAcount=0
		if (varLevels[v] == "upstream") or (varLevels[v] == "local"):
			#open input SHEDS data file
			infile=open(shedsUpLocDAT,"rb")
			#create csv reader
			reader=csv.reader(infile)
			#loop through SHEDS file
			for row in reader:
				if(rowCount==0):
					catchIDIndex=row.index("featureid")
					variableIndex=row.index("variable")
					zoneIndex=row.index("zone")
					valueIndex=row.index("value")
				else:
					if row[variableIndex]==vars[v]:
						if row[zoneIndex]==varLevels[v]:
							if row[valueIndex]=="NA":
								NAcount=NAcount+1
							else:
								if varThresh[v][0] == ">":
									if float(row[valueIndex]) > float(varThresh[v][1:]): #needs the 1: for double digits numbers!
										catchIDvar.append(int(row[catchIDIndex]))
								elif varThresh[v][0] == "<":
									if float(row[valueIndex]) < float(varThresh[v][1:]): #needs the 1: for double digits numbers!
										catchIDvar.append(int(row[catchIDIndex]))
								
				rowCount=rowCount+1
		if varLevels[v] == "riparian":
			#open input SHEDS data file
			infile=open(shedsRipDAT,"rb")
			#create csv reader
			reader=csv.reader(infile)
			#loop through SHEDS file
			for row in reader:
				if(rowCount==0):
					catchIDIndex=row.index("featureid")
					variableIndex=row.index("variable")
					zoneIndex=row.index("zone")
					valueIndex=row.index("value")
				else:
					if row[variableIndex]==vars[v]:
						#riparian data has "local" and "upstream"-- force to select local here
						if row[zoneIndex]=="local":
							if row[valueIndex] =="NA":
								NAcount=NAcount+1
							else:
								if varThresh[v][0] == ">":
									if float(row[valueIndex]) > float(varThresh[v][1:]): #needs the 1: for double digits numbers!
										catchIDvar.append(int(row[0]))
								elif varThresh[v][0] == "<":
									if float(row[valueIndex]) < float(varThresh[v][1:]): #needs the 1: for double digits numbers!
										catchIDvar.append(int(row[0]))
				rowCount=rowCount+1
		#close files
		infile.close()
		#print number of NAs in file
		if NAcount>0:
			arcpy.AddWarning("%s out of %s values not used (NAs in data file)"%(NAcount,rowCount))
		##use catchVar to find patches with catchments that exceed threshold
		patchVar=[]
		for catch in catchJoinIDs:
			if catch in catchIDvar:
				#append patch to list
				patchVar.append(patchJoinIDs[catchJoinIDs.index(catch)])
				
		patchVarLists.append(patchVar)
			# #sum area above threshold by Patch
			# for p in range(0,len(patchIDs)):
				# totAreaThresh=0
				# #get catchments in patch
				# patchIndex=patchJoinIDs.index(patchIDs[p])
				# arcpy.AddMessage(patchIndex)
				# catches=[catchJoinIDs[patchIndex]]
				# arcpy.AddMessage(catches)
				# for c in catches:
					# if c in catchIDvar:
						# totAreaThresh=totAreaThresh+catchAreas[catchIDvar.index[c]]
				# arcpy.AddMessage(totAreaThresh)


################################################################################################################
##                             Fill in Binary Threshold Fields in Patch Shapefile                               ##
################################################################################################################
arcpy.AddMessage("Filling in Binary Threshold fields in Patch Shapefile...")

##add fields to patch layer
arcpy.AddField_management(patchOut, "AreaThresh", "short")
arcpy.AddField_management(patchOut, "DistThresh", "short")
##add fields for variables (can be 0-3 of them)
varFieldNames=[]
for v in vars:
	if v != '#':
		varName=v.split(" ")[0].strip('"')
		fieldName="%sThresh"%varName[0:3]
		varFieldNames.append(fieldName)
		arcpy.AddField_management(patchOut, fieldName, "short")
##add remained fields to patch layer
arcpy.AddField_management(patchOut, "Class", "string")
arcpy.AddField_management(patchOut, "ReconArea", "float")

##identify patches that meet thresholds and store binary values in patch output file
##for each patch in patches shapefile...

##create search cursor for patches 
rows=arcpy.UpdateCursor(patchOut)
for row in rows:
	#get patchID
	patchID=int(row.getValue("Feat_ID"))

	#area threshold
	if patchID in patchArea:
		areaTest=1
	else:
		areaTest=0
	row.setValue("AreaThresh",areaTest)
	
	#inter patch distance threshold
	if patchID in patchDist:
		distTest=1
	else:
		distTest=0
	row.setValue("DistThresh",distTest)
	
	#riverscape ("Restore") variables 
	for v in range(0,len(vars)):
		#if the variable isn't blank (i.e. it was entered in the toolbox)
		if vars[v] != '#':
		#for i in range(0,len(patchVarLists)):
			if patchID in patchVarLists[v]:
				varTest=1
			else:
				varTest=0
			row.setValue(varFieldNames[v],varTest)		
	
	
	# Update the cursor
	rows.updateRow(row)
##delete search cursor
del row, rows




################################################################################################################
##                                  Classify Patches based on thresholds                                         ##
################################################################################################################
arcpy.AddMessage("Classifying Patches Based on Thresholds...")

##start counts of each Patch classification
Protect=0
RestoreHigh=0
Reconnect=0
GeneticRest=0
RestoreLow=0

#create list for reconnect patches to be used in prioritization step
reconPatches=[]

##create search cursor for patches 
rows=arcpy.UpdateCursor(patchOut)

##for each patch in patches shapefile...
for row in rows:
	#get patchID
	patchID=int(row.getValue("Feat_ID"))
	#get thresholds
	areaThresh=row.getValue("AreaThresh")
	distThresh=row.getValue("DistThresh")
	varThresh=[]
	for fieldName in varFieldNames:
		varThresh.append(row.getValue(fieldName))
	#classify based on nested threshold criteria
	if areaThresh==0:
		if sum(varThresh)==0:
			row.setValue("Class","Protect")
			Protect=Protect+1
		if sum(varThresh)>0:
			row.setValue("Class","RestoreHigh")
			RestoreHigh=RestoreHigh+1
	if areaThresh==1:
		if sum(varThresh)==0:
			if distThresh==1:
				row.setValue("Class","Reconnect")
				Reconnect=Reconnect+1
				#sotre to list to be used in prioritization step
				reconPatches.append(patchID)
			if distThresh==0:
				row.setValue("Class","GeneticRest")
				GeneticRest=GeneticRest+1
		if sum(varThresh)>0:
			row.setValue("Class","RestoreLow")
			RestoreLow=RestoreLow+1
	# Update the cursor
	rows.updateRow(row)

##delete search cursor
del row, rows


################################################################################################################
##                                      Prioritize Connectivty Restoration                                    ##
################################################################################################################
arcpy.AddMessage("Prioritizing Connectivity Restoration...")

#function for finding unique values in list
def unique(list1):
    # intilize a null list
    unique_list = []
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    # print list
    return unique_list
	    
##create blank list for potential future patch sizes
newAreas=[]
for p in reconPatches:
  #get index for the patch in the list of all distances
  patchIndex=[i for i,val in enumerate(patch1) if val== p]
  #get unique paired destinations-- will also include itself
  patchesConnected=unique([patch2[i] for i in patchIndex])
  #get area for the patches in list from the original patchIDs list
  areas=[]
  for i in patchesConnected:
    areas.append(patchAreas[patchIDs.index(i)])
  #sum areas to get hypothetical new patch area if reconnected
  newArea=sum(areas)
  #append to newAreas list
  newAreas.append(newArea)


##add new potetnial size to patches shapefile
##create search cursor for patches 
rows=arcpy.UpdateCursor(patchOut)

##for each patch in patches shapefile...
for row in rows:
    #get patchID
	patchID=int(row.getValue("Feat_ID"))
	if patchID in reconPatches:
	    #patch index
		patchIndex=reconPatches.index(patchID)
		#get area of new patch
		newArea=newAreas[patchIndex]
		#store new area in patches shapefile
		row.setValue("ReconArea",newArea)
	else:
		#if not a reconnect patch then fill in with a zero
	    row.setValue("ReconArea",0)
	# Update the cursor
	rows.updateRow(row)

##delete search cursor
del row, rows



################################################################################################################
##                                        Print Out Patch Results                                             ##
################################################################################################################

arcpy.AddMessage("\n\
Patch CLASSIFICATION COMPLETE\n\
%s 'Protect' patches\n\
%s 'Reconnect' patches\n\
%s 'RestoreHigh' patches\n\
%s 'RestoreLow' patches\n\
%s 'GeneticRest' patches"%(Protect,Reconnect,RestoreHigh,RestoreLow,GeneticRest))
print("Ouput patch shapfile saved to:\n\
%s"%patchOut)


#############################################################################################
##                             Classify COAs based on patches                              ##
#############################################################################################

##join patches with COA hucs
#create point layer from patches to use in select by location
arcpy.FeatureToPoint_management(patchOut, "patchCentroids.shp", point_location="INSIDE")
#join huc watersheds with patch centroids
arcpy.SpatialJoin_analysis(COAhucs,"patchCentroids.shp","COAspaJoin.shp",match_option="CONTAINS",join_operation="JOIN_ONE_TO_MANY")

#arcpy.AddMessage([f.name for f in arcpy.ListFields("COAspaJoin.shp")])
##create new fields in COA output
arcpy.AddField_management(COAout, "Protect", "float")
arcpy.AddField_management(COAout, "Reconnect", "float")
arcpy.AddField_management(COAout, "RestoreHi", "float")
arcpy.AddField_management(COAout, "RestoreLow", "float")
arcpy.AddField_management(COAout, "GenRest", "float")
arcpy.AddField_management(COAout, "NOBKT", "float")
arcpy.AddField_management(COAout, "Class", "string")


##start counts of each COA classification
ProtectCOA=0
RestoreHighCOA=0
RestoreLowCOA=0
ReconnectCOA=0
GeneticRestCOA=0




##create search cursor for COA-patch join
rows=arcpy.SearchCursor("COAspaJoin.shp")
##loop through and store HUC ID, patch Class, and patch Area
HUCids=[]
patchClasses=[]
patchAreas=[]

for row in rows:
	HUCids.append(int(row.getValue("TARGET_FID")))
	patchClasses.append(row.getValue("Class"))
	patchAreas.append(float(row.getValue("Area_HA_1")))
#delete search cursor
del row,rows	

# #do a test with one COA
# #index items in list that match the HUC ID
# HUCindices=[i for i, value in enumerate(HUCids) if value == 8]
# #subset the patch class and area lists based on HUC index
# subPatchClasses=[patchClasses[i] for i in HUCindices]
# subPatchAreas=[patchAreas[i] for i in HUCindices]

# ##add area to specified patch
# protect=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "Protect")]
# reconnect=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "Reconnect")]
# restoreHigh=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "RestoreHigh")]
# restoreLow=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "RestoreLow")]
# genetRestor=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "GeneticRest")]
	
	
##create search cursor for COA hucs 
rows=arcpy.UpdateCursor(COAout)

##for each HUC in COA shapefile...
for row in rows:
    ##get hucID
	hucID=int(row.getValue("FID"))
	##get huc area
	hucArea=float(row.getValue("AREA_GEO"))
	#index items in list that match the HUC ID
	HUCindices=[i for i, value in enumerate(HUCids) if value == hucID]
	#subset the patch class and area lists based on HUC index
	subPatchClasses=[patchClasses[i] for i in HUCindices]
	subPatchAreas=[patchAreas[i] for i in HUCindices]

	##add area to specified patch
	protect=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "Protect")]
	reconnect=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "Reconnect")]
	restoreHigh=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "RestoreHigh")]
	restoreLow=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "RestoreLow")]
	genetRestor=[subPatchAreas[z] for z in (i for i, x in enumerate(subPatchClasses) if x == "GeneticRest")]

	##convert areas to percentages
	protectPerc=round((sum(protect)/hucArea)*100,2)
	reconnectPerc=round((sum(reconnect)/hucArea)*100,2)
	restoreHiPerc=round((sum(restoreHigh)/hucArea)*100,2)
	restoreLowPerc=round((sum(restoreLow)/hucArea)*100,2)
	geneticRestPerc=round((sum(genetRestor)/hucArea)*100,2)
	noBKTPerc=round(float(100)-float(protectPerc+reconnectPerc+restoreHiPerc+restoreLowPerc+geneticRestPerc),2)
	
	##store values in COA output as percentage of total HUC area
	row.setValue("Protect",protectPerc)
	row.setValue("Reconnect",reconnectPerc)
	row.setValue("RestoreHi",restoreHiPerc)
	row.setValue("RestoreLow",restoreLowPerc)
	row.setValue("GenRest",geneticRestPerc)
	row.setValue("NOBKT",noBKTPerc)
	
	##get largest percentage
	labels=["Protect","Reconnect","RestoreHigh","RestoreLow","GeneticRest"]
	values=[protectPerc,reconnectPerc,restoreHiPerc,restoreLowPerc,geneticRestPerc]
	maxClass=labels[values.index(max(values))]
	
	#tally number of COAs in each classification
	if maxClass=="Protect":
		ProtectCOA=ProtectCOA+1
	if maxClass=="Reconnect":
		ReconnectCOA=ReconnectCOA+1
	if maxClass=="RestoreLow":
		RestoreLowCOA=RestoreLowCOA+1
	if maxClass=="RestoreHigh":
		RestoreHighCOA=RestoreHighCOA+1
	if maxClass=="GeneticRest":
		GeneticRestCOA=GeneticRestCOA+1

		
	##set HUC COA class
	row.setValue("Class",maxClass)
	
	##Update the cursor
	rows.updateRow(row)


##delete search cursor
del row, rows
		
arcpy.AddMessage("\n\
HUC COA CLASSIFICATION COMPLETE\n\
%s 'ProtectCOA' HUCs\n\
%s 'ReconnectCOA' HUCs\n\
%s 'RestoreHighCOA' HUCs\n\
%s 'RestoreLowCOA' HUCs\n\
%s 'GeneticRestCOA' HUCs"%(ProtectCOA,ReconnectCOA,RestoreHighCOA,RestoreLowCOA,GeneticRestCOA))
print("Ouput COA shapfile saved to:\n\
%s"%COAout)

#delete intermediate files
arcpy.Delete_management("COAspaJoin.shp")
arcpy.Delete_management("patchCentroids.shp")

		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
		
