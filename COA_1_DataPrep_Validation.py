import arcpy
class ToolValidator(object):
	"""Class for validating a tool's parameter values and controlling
	the behavior of the tool's dialog."""
	def __init__(self):
		"""Setup arcpy and the list of tool parameters."""
		self.params = arcpy.GetParameterInfo()
	def initializeParameters(self):
		self.params[7].filter.list = ["Connecticut","Georgia","Maine","Maryland","Massachusetts","New Hampshire",
		"New Jersey","New York","North Carolina","Ohio","Pennsylvania","Rhode Island","South Carolina","Tennessee",
		"Vermont","Virginia","West Virginia"]
		"""Refine the properties of a tool's parameters.  This method is
		called when the tool is opened."""
		return
	def updateParameters(self):
		"""Modify the values and properties of parameters before internal validation is performed.  This method is called whenever a parameter has been changed."""
		if self.params[1].value: #if there is a SHEDS catchment shapefile
			self.params[2].enabled = True #then allow input of SHEDS data files
			self.params[3].enabled = True
		else:
			self.params[2].enabled = False
			self.params[3].enabled = False
		
		if self.params[4].value: #if there is a NHD flowline shapefile
			self.params[5].enabled = True #then require a HUC8 watershed
		else:
			self.params[5].enabled = False
			
		if self.params[7].value == True : #if the "by state" checkmark box is checked
			self.params[8].enabled = True #must specify State
			self.params[9].enabled = False #can't use polygon
		else:
			self.params[8].enabled = False
			self.params[9].enabled = True
		
		if self.params[9].value == True: #if the "by polygon" checkmark box is checked
			self.params[10].enabled = True #must specify polygon
			self.params[7].enabled = False #can't use State
		else:
			self.params[10].enabled = False
			self.params[7].enabled = True
		 
		return
	def updateMessages(self):
		"""Modify the messages created by internal validation for each tool
		parameter.  This method is called after internal validation."""
		return