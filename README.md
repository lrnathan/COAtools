# COAtools
ArcMAP tools used to classify Brook Trout conservation opportunity areas (COA) using regional databases
See Nathan et al. 20XX for a detailed description of the tools and their application
Contact: lucas.nathan@uconn.edu



Steps to use COA tools:

1)Download necessary input files from SHEDS (http://ecosheds.org/): catchment shapfile*, catchment CSVs*, flowlines, EBTJV patches
 *may need multiple files, depending on region of interest
 
2)Download COA.tbx into connnected folder for use in ArcMAP

3)Navigate to file with COA.tbx and run COA tools
  Step 1) DATAprep: subset input files to state (using drop down menu) or specified region of interest (using polygon shapefile)
 
  Step 2) DistanceBetweenPatches: input subset flowline, patch layer, and flowline network dataset (need to create before running tool;       see http://desktop.arcgis.com/en/arcmap/latest/extensions/network-analyst/creating-a-network-dataset.htm). Specify distance based         thresholod (km) that classifies patches as "reconnect" or "assess for translocation"
  
  Step 3) IdentifyCOAS: input all subset files and specify a) area based threshold and b) riverscape critera to classify patches and           watersheds by their COA classification
