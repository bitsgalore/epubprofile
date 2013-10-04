#! /usr/bin/env python
#
# EPUB Automated Quality Assessment Tool
# Wraps around epubcheck and Probatron
# Johan van der Knijff
#
# Requires Python v. 2.7 
#
# Copyright 2013 Johan van der Knijff, KB/National Library of the Netherlands
#
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


__version__= "0.1.0"

import sys
import os
import imp
import shutil
import time
import argparse
import xml.etree.ElementTree as ET
import subprocess as sub


def main_is_frozen():
    return (hasattr(sys, "frozen") or # new py2exe
            hasattr(sys, "importers") # old py2exe
            or imp.is_frozen("__main__")) # tools/freeze
    
def get_main_dir():
    if main_is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(sys.argv[0])

def errorExit(msg):
    msgString=("ERROR: " +msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()
    
def checkFileExists(fileIn):
    # Check if file exists and exit if not
    if os.path.isfile(fileIn)==False:
        msg=fileIn + " does not exist!"
        errorExit(msg)
        
def checkDirExists(pathIn):
    # Check if directory exists and exit if not
    if os.path.isdir(pathIn)==False:
        msg=pathIn + " does not exist!"
        errorExit(msg)
        
def openFileForAppend(file):
    # Opens file for writing in append + binary mode
    try:
        f=open(file,"ab")
        return(f)
    except Exception:
        msg=file + " could not be written"
        errorExit(msg)

def removeFile(file):
    try:
        if os.path.isfile(file)==True:
            os.remove(file)
    except Exception:
        msg= "Could not remove " + file
        errorExit(msg)

def constructFileName(fileIn,pathOut,extOut,suffixOut):
    # Construct filename by replacing path by pathOut,
    # adding suffix and extension
    
    fileInTail=os.path.split(fileIn)[1]

    baseNameIn=os.path.splitext(fileInTail)[0]
    baseNameOut=baseNameIn + suffixOut + "." + extOut
    fileOut=addPath(pathOut,baseNameOut)

    return(fileOut)

def addPath(pathIn,fileIn):
    result=os.path.normpath(pathIn+ "/" + fileIn)
    return(result)
    
def parseCommandLine():
    # Create parser
    parser = argparse.ArgumentParser(description="EPUB profiler",version=__version__)
    
    # Add arguments
    parser.add_argument('batchDir', action="store", help="batch directory")
    parser.add_argument('outDir', action="store", help="output directory")
    parser.add_argument('schema', action="store", help="name of schema")
    #parser.add_argument('--version', '-v', action = 'version', version = __version__)

    # Parse arguments
    args=parser.parse_args()
    
    # Normalise all file paths
    args.batchDir=os.path.normpath(args.batchDir)
    
    return(args)

def getConfiguration(configFile):

    # What is the location of this script?
    appPath=os.path.abspath(get_main_dir())

    # Parse XML tree
    try:
        tree = ET.parse(configFile)
        config = tree.getroot()
    except Exception:
        msg="error parsing " + configFile
        errorExit(msg)
    
    # Locate configuration elements
    javaElement=config.find("java")
    
    # Get corresponding text values
    java=os.path.normpath(javaElement.text)
    epubcheckApp=addPath(appPath + "/epubcheck/","epubcheck-3.0.1.jar") # To config file!
    probatronApp=addPath(appPath + "/probatron/","probatron.jar")
        
    # Check if all files exist, and exit if not
    checkFileExists(java)
    checkFileExists(epubcheckApp)
    checkFileExists(probatronApp)
            
    return(java,epubcheckApp,probatronApp)


def listProfiles(profilesDir):
    profileNames=os.listdir(profilesDir)
    
    for i in range(len(profileNames)):
        print(profileNames[i])
    sys.exit()
    

def readProfile(profile):
       
    # What is the location of this script?
    appPath=os.path.abspath(get_main_dir())
    
    profile=addPath(appPath + "/profiles/",profile)

    # Check if profile exists and exit if not
    checkFileExists(profile)

    # Parse XML tree
    try:
        tree = ET.parse(profile)
        prof = tree.getroot()
    except Exception:
        msg="error parsing " + profile
        errorExit(msg)
    
    # Locate schema elements
    schemaMasterElement=prof.find("schemaMaster")
    schemaAccessElement=prof.find("schemaAccess")
    schemaTargetElement=prof.find("schemaTarget")
    
    # Get corresponding text values
    schemaMaster=addPath(appPath + "/schemas/",schemaMasterElement.text)
    schemaAccess= addPath(appPath + "/schemas/",schemaAccessElement.text)
    schemaTarget= addPath(appPath + "/schemas/",schemaTargetElement.text) 
    
    # Check if all files exist, and exit if not
    checkFileExists(schemaMaster)
    checkFileExists(schemaAccess)
    checkFileExists(schemaTarget)
    
    # HACK: Probatron exits with URL Exception if schema is a  standard (full) file path,
    # this makes it work (at least under Windows)
    schemaMaster="file:///" + schemaMaster
    schemaAccess="file:///" +schemaAccess
    schemaTarget="file:///" +schemaTarget
    
    return(schemaMaster,schemaAccess,schemaTarget)


def launchSubProcess(systemString):
    # Launch subprocess and return exit code, stdout and stderr
    try:
        # Execute command line; stdout + stderr redirected to objects
        # 'output' and 'errors'.
        p = sub.Popen(systemString,stdout=sub.PIPE,stderr=sub.PIPE)
        output, errors = p.communicate()
                
        # Decode to UTF8
        outputAsString=output.decode('utf-8')
        errorsAsString=errors.decode('utf-8')
                
        exitStatus=p.returncode
  
    except Exception:
        # I don't even want to start thinking how one might end up here ...
        exitStatus=-99
        outputAsString=""
        errorsAsString=""
    
    return exitStatus,outputAsString,errorsAsString

def getFilesFromTree(rootDir, extensionString):
    # Walk down whole directory tree (including all subdirectories)
    # and return list of those files whose extension contains user defined string
    # NOTE: directory names are disabled here!!
    # implementation is case insensitive (all search items converted to
    # upper case internally!

    extensionString=extensionString.upper()

    filesList=[]
    for dirname, dirnames, filenames in os.walk(rootDir):
        #Suppress directory names
        for subdirname in dirnames:
            thisDirectory=os.path.join(dirname, subdirname)

        for filename in filenames:
            thisFile=os.path.join(dirname, filename)
            thisExtension=os.path.splitext(thisFile)[1]
            thisExtension=thisExtension.upper()
            if extensionString in thisExtension:
                filesList.append(thisFile)
    return filesList

def getPathComponentsAsList(path):
    
    # Adapted from:
    # http://stackoverflow.com/questions/3167154/how-to-split-a-dos-path-into-its-components-in-python
    
    drive,path_and_file=os.path.splitdrive(path)
    path,file=os.path.split(path_and_file)
    
    folders=[]
    while 1:
        path,folder=os.path.split(path)

        if folder!="":
            folders.append(folder)
        else:
            if path!="":
                folders.append(path)

            break

    folders.reverse()
    return(folders)
                    
def main():
    
    # What is the location of this script/executable
    appPath=os.path.abspath(get_main_dir())
    
    # Configuration file
    configFile=os.path.abspath(appPath + "/config.xml")
    
    # Check if config file exists, and exit if not
    checkFileExists(configFile)
    
    # Get input from command line
    args=parseCommandLine()
    
    batchDir=args.batchDir
    outDir=args.outDir
    schema=args.schema
    
    # Create output dir if it doesn't already exist
    if os.path.isdir(outDir)==False:
        os.makedirs(outDir)
    
    # HACK: Probatron exits with URL Exception if schema is a  standard (full) file path,
    # this makes it work (at least under Windows)
    schema = "file:///" + schema
                   
    # Get Java location from config file 
    java,epubcheckApp,probatronApp=getConfiguration(configFile)
            
    # File names for temporary epubcheck and Probatron output files
    #nameEpubcheck="_epubcheck_temp_.xml"
    nameProbatron="_probatron_temp_.xml"
    
    # Set line separator for output/ log files to OS default
    lineSep=os.linesep
  
    # Open log files for writing (append + binary mode so we don't have to worry
    # about encoding issues).
    # IMPORTANT: files are overwitten for each new session (hence 'removeFile'
    # before opening below!).
    
    # File with summary of quality check status (pass/fail) for each image
    statusLog=os.path.normpath(outDir + "/" + "epubprofile_status.csv")
    removeFile(statusLog)
    fStatus=openFileForAppend(statusLog)
    
    # File that contains detailed results 
    detailsLog=os.path.normpath(outDir + "/" + "epubprofile_details.txt")
    removeFile(detailsLog)
    fDetails=openFileForAppend(detailsLog)
    
    listFiles=getFilesFromTree(batchDir, "epub")

    # start clock for statistics
    start = time.clock()
    print("epubprofile started: " + time.asctime())
    
    for i in range(len(listFiles)):
        myFile=os.path.abspath(listFiles[i])
        
        # Initialise status (pass/fail)
        status="pass"
        schemaMatch=True
        
        # Initialise empty text strings for error log output
        ecOutString=""
        ptOutString=""
        
        # Remove any previous instances of probatron output file
        removeFile(nameProbatron)

        nameEpubcheck=constructFileName(myFile,outDir,"xml","_epubcheck")
        
        # Epubcheck command line
        ecSysString=java + " -jar " + epubcheckApp + " " + '"' + myFile + '"' + " -out " + '"' + nameEpubcheck + '"'
        
        try:
            ecExitStatus,ecStdOut,ecStdErr=launchSubProcess(ecSysString)
        
            with open(nameProbatron, "w") as text_file:
                text_file.write(ptStdOut)
        except:
            status="fail"
            description="Error running Epubcheck"
            ecOutString +=description + lineSep

         
        # Construct Probatron command line according to:
        # %java% -jar %probatron% dpo_colour_00990_master_jp2.xml %schemaMaster% > resultMasterOK.xml
        
        ptSysString=java + " -jar " + probatronApp + " " + '"' + nameEpubcheck + '"' + " " \
                    + schema
        
        # Run Probatron, result to file
        try:
            ptExitStatus,ptStdOut,ptStdErr=launchSubProcess(ptSysString)
        
            with open(nameProbatron, "w") as text_file:
                text_file.write(ptStdOut)
        except:
            status="fail"
            description="Error running Probatron"
            ptOutString +=description + lineSep
        
        # Parse Probatron XML output and extract interesting bits
        try:
            
            tree=ET.parse(nameProbatron)
            root = tree.getroot()
                        
            for elem in root.iter():
                if elem.tag == "{http://purl.oclc.org/dsdl/svrl}failed-assert":
                    
                    status="fail"
                    
                    # Extract test definition
                    test = elem.get('test')
                    ptOutString += 'Test "'+ test + '" failed (' 
                    
                    # Extract text description from text element
                    for subelem in elem.iter():
                        if subelem.tag=="{http://purl.oclc.org/dsdl/svrl}text":
                           description=(subelem.text)
                           ptOutString +=description + ")" + lineSep
        except Exception:
            status="fail"
            description="Error processing Probatron output"
            ptOutString +=description + lineSep
        
        # Parse epubcheck XML output and extract info on failed tests in case
        # image is not valid JP2
        try:
            tree=ET.parse(nameEpubcheck)
            root = tree.getroot()
            repInfo = root.find('{http://hul.harvard.edu/ois/xml/ns/jhove}repInfo')
            validationOutcome=repInfo.find('{http://hul.harvard.edu/ois/xml/ns/jhove}status').text
            epubVersion=repInfo.find('{http://hul.harvard.edu/ois/xml/ns/jhove}version').text
                            
            if validationOutcome != "Well-formed":
            
                # Note: maybe we also want to report warnings for well-formed epubs?
                msgElt=repInfo.find('{http://hul.harvard.edu/ois/xml/ns/jhove}messages')
                ptOutString += "*** Epubcheck validation errors and warnings:" +lineSep
            
                # Iterate over messages element and report text of all child elements
                
                messages = list(msgElt.iter())
                               
                for i in messages:
                    msg=i.text
                    if msg.strip() != "":
                        ptOutString += msg + lineSep
                        
        except:
            #print "Unexpected error:", sys.exc_info()[0]
            pass
                                                        

        fDetails.write("file name: " + myFile + lineSep)
        fDetails.write("epub version: " + epubVersion + lineSep)
        fDetails.write("schema: " + schema + lineSep)
        fDetails.write("validation status: " + validationOutcome + lineSep)
        if ptOutString != "":
            fDetails.write("*** Schema validation errors:"+lineSep)
            fDetails.write(ptOutString)
        fDetails.write("####" + lineSep)
            
        statusLine=myFile +"," + status + lineSep
        
        #f_out.write(bytes(s, 'UTF-8'))
        fStatus.write(statusLine)
    
    end = time.clock()

    # Close output files
    fStatus.close()
    fDetails.close()
    
    # Remove epubcheck/probatron output files
    removeFile(nameEpubcheck)
    removeFile(nameProbatron)
    
    print("epubprofile ended: " + time.asctime())
    
    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = timeElapsed / 60
   
    print("Elapsed time: "+ str(timeInMinutes) + " minutes")
    

if __name__ == "__main__":
    main()
