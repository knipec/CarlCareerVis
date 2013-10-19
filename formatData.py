'''
	formatData.py

	Carissa Knipe
	Oct 18, 2013

	Takes data from excel spreadsheet and writes to a json file.
	
	The main idea is that on each row of the spreadsheet, you make a new node if you haven't seen that major before, make a new node if you haven't seen that broad career before, and make a link between node-broad career and between node-specific career. Then those nodes and links are turned into the json.
'''

from xlrd import *

def main() :
# -----------------------------------------------------
	# Figure these out. !!!NOTE!!! that everything is indexed from zero, so you should subtract one from the number you think should go there.
	# For example, if the actual data starts on row 14 on the spreadsheet, dataStartingRow should be 13.

	# Name of the excel file with the data in it
	dataSource = "newData.xlsx"

	# Which sheet (or tab) in the excel file to use
	sheetIndex = 3

	# Which column majors are
	majorCol = 3

	# Which column broad careers are
	broadCareerCol = 5

	# Which column specific careers are
	specificCareerCol = 6

	# Which is the first row with actual data in it
	dataStartingRow = 13
# -----------------------------------------------------

	writeDataTo = "data.json"
	workbook = open_workbook(dataSource)
	sheet = workbook.sheet_by_index(sheetIndex)

	# Entry looks like 
	# {"name_of_major_or_career" : node_number}
	nodeDict = ordered_dict()

	# Entry looks like
	# {(major_number, broad_career_number) : [numPeople, [ordered_dict{spec_career_0:num_0},...]]}
	linkDict = ordered_dict()

	discardedDict = ordered_dict()

	nodeIndex = 0
	for row in range(sheet.nrows):
		majors = getMajor(sheet.cell_value(row, majorCol))
		broadCareerName = sheet.cell_value(row, broadCareerCol)
		specificCareerName = sheet.cell_value(row, specificCareerCol)
		if (row < dataStartingRow or broadCareerName == "Unknown"):
			continue
		if (len(majors) < 1):
			discardedDict[sheet.cell_value(row, majorCol)] = 1
			continue

		for majorIndex in range(len(majors)):
			majorName = majors[majorIndex]
			nodeIndex = addNode(nodeDict, majorName, nodeIndex)
			nodeIndex = addNode(nodeDict, broadCareerName, nodeIndex)
			addLink(linkDict, nodeDict, majorName, broadCareerName, specificCareerName)


	# Sort alphabetically
	[sortedNodes, sortedLinks] = sort(nodeDict, linkDict)

	print "DELETED MAJORS: (", len(discardedDict), ")"
	for major in discardedDict.sort_by_key().order():
		print major

	createJSON(sortedNodes, sortedLinks, writeDataTo)

	print "Done! %d rows" , sheet.nrows

def sort(nodeDict, linkDict):
	sortedNodes = nodeDict.sort_by_key()
	sortedLinks = ordered_dict()
	for link in linkDict:
		oldSourceIndex = link[0]
		oldTargetIndex = link[1]
		newLink = sortedNodes.order().index(nodeDict.order()[oldSourceIndex]), sortedNodes.order().index(nodeDict.order()[oldTargetIndex])
		sortedLinks[newLink] = [linkDict[link][0], linkDict[link][1]]

	return [sortedNodes, sortedLinks]


def addNode(nodeDict, nodeName, curnodeIndex):
	if (nodeName not in nodeDict):
		nodeDict[nodeName] = curnodeIndex
		return curnodeIndex+1
	return curnodeIndex

def addLink(linkDict, nodeDict, majorName, careerName, specificCareerName = ""):
	link = nodeDict[majorName], nodeDict[careerName]
	if (link not in linkDict):
		linkDict[link] = [0,0]
		linkDict[link][0] = 1
		linkDict[link][1] = ordered_dict()
	else:
		linkDict[link][0] += 1

	specificDict = linkDict[link][1]
	if (specificCareerName == ""):
		pass
	elif (specificCareerName not in specificDict):
		specificDict[specificCareerName] = 1
	else:
		specificDict[specificCareerName] += 1


def createJSON(nodes, links, fileName):
	f = open(fileName, 'w')
	f.write("[")

	# Writing the data for majors --> broadCareers
	f.write("\n{\"nodes\":[\n")
	stringToWrite = ""
	for nodeName in nodes.order():
		stringToWrite += "{\"name\":\"" + nodeName + "\"},\n"
	f.write(stringToWrite[:-2])

	f.write("\n],\n\"links\":[\n")

	stringToWrite = ""
	index = 0
	for link in links.order():
		index += 1
		stringToWrite += "{\"source\":" + str(link[0]) + ",\"target\":" + str(link[1]) + ",\"value\":" + str(links[link][0]) + ",\"index\":" + str(index) + "},\n"
	f.write(stringToWrite[:-2])

	f.write("\n]} ")	

	# Writing the data for each link (each will look like majors --> specificCareers)

	for link in links.order():
		newNodeDict = ordered_dict()
		newLinkDict = ordered_dict()
		nodeIndex = 0
		major = nodes.order()[link[0]]
		nodeIndex = addNode(newNodeDict, major, nodeIndex)
		specificCareers = links[link][1]
		for career in specificCareers.order():
			nodeIndex = addNode(newNodeDict, career, nodeIndex)
			# DERP - Inefficient
			for i in range(specificCareers[career]):
				addLink(newLinkDict, newNodeDict, major, career)

		stringToWrite = ""
		f.write(",\n{\"nodes\":[\n")
		for newNode in newNodeDict.order():
			stringToWrite += "{\"name\":\"" + newNode + "\"},\n"
		f.write(stringToWrite[:-2])

		stringToWrite = ""
		f.write("\n],\n\"links\":[\n")

		for newLink in newLinkDict.order():
			stringToWrite += "{\"source\":" + str(newLink[0]) + ",\"target\":" + str(newLink[1]) + ",\"value\":" + str(newLinkDict[newLink][0]) + "},\n"
		f.write(stringToWrite[:-2])
		f.write("\n\n]} ")	


	f.write("]")
	f.close()

class ordered_dict(dict):
    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self._order = self.keys()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        if key in self._order:
            self._order.remove(key)
        self._order.append(key)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._order.remove(key)

    def order(self):
        return self._order[:]

    def ordered_items(self):
        return [(key,self[key]) for key in self._order]

    def sort_by_key(self):
    	sortedList = sorted(self._order)
    	sortedDict = ordered_dict()
    	for key in sortedList:
    		sortedDict[key] = self[key]
    	return sortedDict

    def indexOf(self, key):
    	return self._order.index(key)

    def getByIndex(self, index):
    	return self._order[index]

# Puts the listed majors into the decided upon major categories
def getMajor(major):
	validMajorsList = ["Area Studies","Art/Art History","Biology","Chemistry","Cinema and Media Studies","Classics","Computer Science","Economics","English","Environmental Studies","Geology","History","Linguistics","Mathematics","Modern Languages","Music","Philosophy","Physics","Political Science","Psychology","Religion","Sociology/Anthropology","Theater/Dance","Women's and Gender Studies"]

	majorCategories = []

	if (major == "Biology-Geology"):
		majorCategories.append("Biology")
		majorCategories.append("Geology")

	elif (major == "Theater" or major == "Dance"):
		majorCategories.append("Theater/Dance")

	elif (major == "Studio Art" or major == "Art History"):
		majorCategories.append("Art/Art History")

	elif (major == "French" or major == "Romance Langs." or major == "French Studies" or major == "Russian" or major == "German" or major == "Romance Languages & Literature" or major == "German Studies" or major == "Spanish" or major == "French and Francophone Studies"):
		majorCategories.append("Modern Languages")

	elif (major == "Economics & Math"):
		majorCategories.append("Economics")
		majorCategories.append("Mathematics")

	elif (major == "Women's Studies"):
		majorCategories.append("Women's and Gender Studies")

	elif (major == "Latin American Studies" or major == "American Image" or major == "American Studies" or major == "Chicano Studies" or major == "African/Afr American" or major == "Asian Studies"):
		majorCategories.append("Area Studies")

	elif (major == "Dramatic Arts" or major == "Theater Arts" or major == "Theatre Studies" or major == "Musical Theater"):
		majorCategories.append("Theater/Dance")

	elif (major == "Intl Relations" or major == "Political Science/Intl Relatns"or major == "Political Philosophy" or major == "Political Science/IR" or major == "Internat'l Relations"):
		majorCategories.append("Political Science")

	elif (major == "Anthropological Linguistics"):
		majorCategories.append("Linguistics")

	elif (major == "Black Culturl Identity & Dance"):
		majorCategories.append("Theater/Dance")

	elif (major == "Mathematics/Statistics"):
		majorCategories.append("Mathematics")

	elif (major == "Social Psychlgy"):
		majorCategories.append("Psychology")
	
	elif (major == "Linguistics/Computer Science"):
		majorCategories.append("Linguistics")
		majorCategories.append("Computer Science")

	elif (major == "Human-Computer Interaction"):
		majorCategories.append("Computer Science")

	elif (major == "Art&Literature"):
		majorCategories.append("Art/Art History")
		majorCategories.append("English")

	elif (major == "Hermeneutics"):
		majorCategories.append("English")

	elif (major == "Environmntl St" or major == "Earth System Science" or major == "Environmental Science" or major == "Envirn Geo-Chem" or major == "Ecosystem Science"):
		majorCategories.append("Environmental Studies")

	elif (major == "Media Studies"):
		majorCategories.append("Cinema and Media Studies")

	elif (major == "Media/Theater"):
		majorCategories.append("Cinema and Media Studies")
		majorCategories.append("Theater/Dance")

	elif (major == "Dance,Mus&Educ"):
		majorCategories.append("Theater/Dance")
		majorCategories.append("Music")

	elif (major == "Ethnomusicology"):
		majorCategories.append("Music")

	elif (major == "Classical Studies" or major == "Classical Languages" or major == "Latin" or major == "Greek"):
		majorCategories.append("Classics")

	elif (major not in validMajorsList):
		return majorCategories

	else:
		majorCategories.append(major)

	return majorCategories

if __name__ == "__main__":
	main()