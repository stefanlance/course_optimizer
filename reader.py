#! /usr/bin/python

import re
import sys
import httplib
import urllib

def get_classes(dept, quarter, year):
	classes = { }
	params = urllib.urlencode({ "TermName": "%s %d" % (quarter, year) })
	connection = httplib.HTTPSConnection("classes.uchicago.edu")
	connection.request("POST", "/search.php?CourseLevel=All&search=SEARCH&Department={0}".format(dept), params)
	response = connection.getresponse()
	classfinder = re.compile(r'.*courseName=([^&]*)&.*')
	if response.status == 200:
		data = response.read()
		for line in data.split('\n'):
			matches = classfinder.match(line)
			if matches != None:
				klass = matches.group(1)
				if klass not in classes:
					classes[klass] = 0
				classes[klass] += 1
	else:
		print "OH NO!"
	connection.close()
	return classes.keys()

def retrieve_departments():
	departments = { }
	with open("departments", "r") as fp:
		for line in fp:
			line = re.sub(r'\n','', line)
			code, description = line.split('\t')
			departments[code] = {
				'description': description,
				'classes': { }
			}
	return departments

def populate_classinfo(klass, quarter, year, hr):
# https://classes.uchicago.edu/courseDetail.php?courseName=PHYS%2023500
	params = urllib.urlencode({ "TermName": "%s %d" % (quarter, year) })
	connection = httplib.HTTPSConnection("classes.uchicago.edu")
	connection.request("POST", "/courseDetail.php?courseName={0}".format(urllib.quote(klass)), params)
	response = connection.getresponse()
	additionalnotes = re.compile(r'.*<strong>Additional notes:</strong>(.*?)</div>.*', re.DOTALL)
	if response.status == 200:
		data = response.read()
		matches = additionalnotes.match(data)
		if matches != None:
			note = matches.group(1)
			sys.stderr.write("%s\n" % (note))
			hr["additional_notes"] += [note]
	else:
		print "OH NO!"
	connection.close()

def dumpit(fn, departments):
	with open(fn, "w") as fp:
		fp.write("%s\n" % (departments))

def main():
	departments = retrieve_departments()
	for code, classinfo in sorted(departments.iteritems(), key=lambda x: x[0]):
		if code == "PHYS" or True:
			for year in xrange(2013,2014):
				for quarter in ['Autumn', 'Winter', 'Spring' ]:
					cc = get_classes(code, quarter, year)
					for c in cc:
						if c not in classinfo["classes"]:
							classinfo["classes"][c] = {
								"quarters": [ ],
								"additional_notes": []
							}
						classinfo["classes"][c]["quarters"] += ["%s %d" % (quarter, year)]
						additional = populate_classinfo(c, quarter, year, classinfo["classes"][c])
						sys.stderr.write("%s %d %s %s\n" % (code, year, quarter, c))
				dumpit("classinfo.json", departments)

if __name__ == "__main__":
	main()
