import xmltodict
import xml.etree.cElementTree as ElementTree
import os
import urllib
import subprocess
import time
import json


def downloadfile(url, fname):
    urllib.urlretrieve(url, fname)

basedir = "/Users/swheeler/Downloads/CompIQ_DataScience_TakeHome_1/"

print
print "========================"
print time.strftime("%c")
print "========================"

if os.path.exists(basedir + "jobdump.xml.gz"):
    os.remove(basedir + "jobdump.xml.gz")

if os.path.exists(basedir + "jobdump.xml"):
    os.remove(basedir + "jobdump.xml")

print "Downloading job dump..."
downloadfile("https://dl.dropboxusercontent.com/u/70278264/jobdump.xml.gz", basedir + "jobdump.xml.gz")

print "Unzipping dump..."
subprocess.call(["gzip", "-d", basedir + "jobdump.xml.gz"])

print "Writing to file..."
counter = 0
with open(basedir + "jobs.output", "w") as outfile:
    for event, elem in ElementTree.iterparse(basedir+"jobdump.xml"):
        if elem.tag == "job":
            job = xmltodict.parse(ElementTree.tostring(elem))
            elem.clear()

            # remove nesting level
            job = job["job"]

            # transform into json object and write to file (one object per line) --- TBD
            outfile.write(json.dumps(job)+"\n")

            counter += 1

print " %i jobs written." % counter

os.remove(basedir + "jobdump.xml")
