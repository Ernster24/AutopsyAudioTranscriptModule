# Sample module in the public domain. Feel free to use this as a template
# for your modules (and you can remove this header and take complete credit
# and liability)
#
# Contact: Brian Carrier [carrier <at> sleuthkit [dot] org]
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.
#
# In jurisdictions that recognize copyright laws, the author or authors
# of this software dedicate any and all copyright interest in the
# software to the public domain. We make this dedication for the benefit
# of the public at large and to the detriment of our heirs and
# successors. We intend this dedication to be an overt act of
# relinquishment in perpetuity of all present and future rights to this
# software under copyright law.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.

# Simple data source-level ingest module for Autopsy.
# Search for TODO for the things that you need to change
# See http://sleuthkit.org/autopsy/docs/api-docs/latest/index.html for documentation

import jarray
import inspect
import subprocess
import os
import csv
from java.lang import System
from java.util.logging import Level
from java.io import File
from org.sleuthkit.datamodel import SleuthkitCase
from org.sleuthkit.datamodel import AbstractFile
from org.sleuthkit.datamodel import Score
from org.sleuthkit.datamodel import ReadContentInputStream
from org.sleuthkit.datamodel import BlackboardArtifact
from org.sleuthkit.datamodel import BlackboardAttribute
from org.sleuthkit.datamodel import TskData
from org.sleuthkit.autopsy.datamodel import ContentUtils
from org.sleuthkit.autopsy.ingest import IngestModule
from org.sleuthkit.autopsy.ingest.IngestModule import IngestModuleException
from org.sleuthkit.autopsy.ingest import DataSourceIngestModule
from org.sleuthkit.autopsy.ingest import FileIngestModule
from org.sleuthkit.autopsy.ingest import IngestModuleFactoryAdapter
from org.sleuthkit.autopsy.ingest import IngestMessage
from org.sleuthkit.autopsy.ingest import IngestServices
from org.sleuthkit.autopsy.coreutils import Logger
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.casemodule.services import Services
from org.sleuthkit.autopsy.casemodule.services import FileManager
from org.sleuthkit.autopsy.casemodule.services import Blackboard
from org.sleuthkit.datamodel import Score
from java.util import Arrays
from AudioTranscriptFunctions import *


# Factory that defines the name and details of the module and allows Autopsy
# to create instances of the modules that will do the analysis.
# TODO: Rename this to something more specific. Search and replace for it because it is used a few times
class AudioTranscriptIngestModuleFactory(IngestModuleFactoryAdapter):

    # TODO: give it a unique name.  Will be shown in module list, logs, etc.
    moduleName = "Audio Transcript"

    def getModuleDisplayName(self):
        return self.moduleName

    # TODO: Give it a description
    def getModuleDescription(self):
        return "Audio Transcript module which converts detected speech into text."

    def getModuleVersionNumber(self):
        return "1.0"

    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingestOptions):
        # TODO: Change the class name to the name you'll make below
        return AudioTranscriptIngestModule()


# Data Source-level ingest module.  One gets created per data source.
# TODO: Rename this to something more specific. Could just remove "Factory" from above name.
class AudioTranscriptIngestModule(DataSourceIngestModule):
    _logger = Logger.getLogger(AudioTranscriptIngestModuleFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def __init__(self):
        self.context = None

    # Where any setup and configuration is done
    # 'context' is an instance of org.sleuthkit.autopsy.ingest.IngestJobContext.
    # See: http://sleuthkit.org/autopsy/docs/api-docs/latest/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_ingest_job_context.html
    # TODO: Add any setup code that you need here.
    def startUp(self, context):
        
        # Throw an IngestModule.IngestModuleException exception if there was a problem setting up
        # raise IngestModuleException("Oh No!")
        self.context = context

    # Where the analysis is done.
    # The 'dataSource' object being passed in is of type org.sleuthkit.datamodel.Content.
    # See: http://www.sleuthkit.org/sleuthkit/docs/jni-docs/latest/interfaceorg_1_1sleuthkit_1_1datamodel_1_1_content.html
    # 'progressBar' is of type org.sleuthkit.autopsy.ingest.DataSourceIngestModuleProgress
    # See: http://sleuthkit.org/autopsy/docs/api-docs/latest/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_data_source_ingest_module_progress.html
    # TODO: Add your analysis code in here.
    def process(self, dataSource, progressBar):

        # Get all files from case
        fileManager = Case.getCurrentCase().getServices().getFileManager()
        files = fileManager.findFiles(dataSource, "%")

        blackboard = Case.getCurrentCase().getSleuthkitCase().getBlackboard()
        artId = blackboard.getOrAddArtifactType("TSK_TRANSCRIBED_TEXT", "Transcribed Text")
        attrId = blackboard.getOrAddAttributeType("TSK_TRANSCRIPT_ATTR", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Transcription")
        
        # Get Transcribe.py directory
        transcriptPath = os.path.join(os.getenv("APPDATA") + "\\autopsy\\python_modules\\AutopsyAudioTranscriptModule\\Transcribe.py")
        
        dir = Case.getCurrentCase().getTempDirectory()
        csvFileName = os.path.join(dir, 'transcription.csv')
        with open(csvFileName, 'w') as writeCSVFile:
            writer = csv.writer(writeCSVFile)
            field = ["File Number", "Original File", "Transcribed Text"]
            writer.writerow(field)
        
        self.log(Level.INFO, "CSV file created: transcription.csv")

        numFiles = len(files)
        self.log(Level.INFO, "Found " + str(numFiles) + " files")
        progressBar.switchToDeterminate(numFiles)
        fileCount = 0
        for file in files:

            # Check if the user pressed cancel while we were busy
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK

            fileName = file.getName()
            self.log(Level.INFO, "Processing file: " + fileName)

            # Update the progress bar
            progressBar.progress(fileCount)
            
            # Skip unallocated and unused blocks
            if ((file.getMIMEType() is not None) and 
                (file.getType() != TskData.TSK_DB_FILES_TYPE_ENUM.UNALLOC_BLOCKS) and 
                (file.getType() != TskData.TSK_DB_FILES_TYPE_ENUM.UNUSED_BLOCKS)):

                # If audio file is selected, run through transcription program
                if (file.getMIMEType().startswith("audio")):
                    fileCount += 1
                    self.log(Level.INFO, "FILE " + fileName + " IS AN AUDIO FILE")
                    filePath = createTempFile(file)

                    command = ['python3', transcriptPath, str(filePath), str(fileCount)]
                
                # If video file is selected, convert to audio file then run through transcription program
                elif (file.getMIMEType().startswith("video")):
                    fileCount += 1
                    self.log(Level.INFO, "FILE " + fileName + " IS A VIDEO FILE")
                    filePath = createTempFile(file)

                    # Convert video file to audio file
                    newAudioFilePath = convertVideoFile(fileName, filePath)
                    command = ['python3', transcriptPath, str(newAudioFilePath), str(fileCount)]

                else:
                    continue


                self.log(Level.INFO, "Transcribing file: " + fileName)
                result = transcribeAudioFile(command)
                self.log(Level.INFO, "Result: " + str(result))

                artifact = file.newArtifact(artId.getTypeID())
                attribute = BlackboardAttribute(attrId, AudioTranscriptIngestModuleFactory.moduleName, str(result))

                try:
                    artifact.addAttribute(attribute)
                except:
                    self.log(Level.SEVERE, "Error adding attribute to artifact.")
                
                try:
                    blackboard.postArtifact(artifact, AudioTranscriptIngestModuleFactory.moduleName)
                except:
                    self.log(Level.SEVERE, "Error posting artifact to BlackBoard.")

                with open(csvFileName, 'a') as writeCSVFile:
                    writer = csv.writer(writeCSVFile)
                    writer.writerow([fileCount, fileName, result])                

            else:
                continue

        '''
        transcriptionList = []
        with open(csvFileName, 'rb') as readCSVFile:
            reader = csv.reader(readCSVFile)
            for row in reader:
                transcriptionList.append(row)

        self.log(Level.INFO, "TRANSCRIPTION LIST: " + str(transcriptionList))

        
        for n in range (1, fileCount):
            postFileName = transcriptionList[n][1]
            postFileNo = transcriptionList[n][0]
            postFileTranscript = transcriptionList[n]

            attr = BlackboardAttribute(BlackboardAttribute.Type.TSK_TEXT, AudioTranscriptIngestModuleFactory.moduleName, str(postFileTranscript))
            for file in artifactList:
                art = file.newArtifact(BlackboardArtifact.Type.TSK_EXTRACTED_TEXT)
                art.addAttribute(attr)
                try:
                    blackboard.indexArtifact(art)
                    self.log(Level.INFO, "ARTIFACT SUCCESSFULLY INDEXED")
                except:
                    self.log(Level.SEVERE, "ERROR INDEXING ARTIFACT")
        '''

        #Post a message to the ingest messages in box.
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
            "Audio Transcript Ingest Module", "Found %d files" % fileCount)
        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK
