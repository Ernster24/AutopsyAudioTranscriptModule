# Audio Transcript Ingest Module for Autopsy
# By u2039563
# Based on the data source-level ingest module template by Brian Carrier

import jarray
import inspect
import os
import time
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
class AudioTranscriptIngestModuleFactory(IngestModuleFactoryAdapter):

    moduleName = "Audio Transcript"

    def getModuleDisplayName(self):
        return self.moduleName

    def getModuleDescription(self):
        return "Audio Transcript module which converts speech detected from audio and video files into text."

    def getModuleVersionNumber(self):
        return "1.0"

    def isDataSourceIngestModuleFactory(self):
        return True

    def createDataSourceIngestModule(self, ingestOptions):
        # TODO: Change the class name to the name you'll make below
        return AudioTranscriptIngestModule()


# Data Source-level ingest module.  One gets created per data source.
class AudioTranscriptIngestModule(DataSourceIngestModule):
    _logger = Logger.getLogger(AudioTranscriptIngestModuleFactory.moduleName)

    def log(self, level, msg):
        self._logger.logp(level, self.__class__.__name__, inspect.stack()[1][3], msg)

    def __init__(self):
        self.context = None

    # Where any setup and configuration is done
    # 'context' is an instance of org.sleuthkit.autopsy.ingest.IngestJobContext.
    # See: http://sleuthkit.org/autopsy/docs/api-docs/latest/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_ingest_job_context.html
    def startUp(self, context):
        
        # Throw an IngestModule.IngestModuleException exception if there was a problem setting up
        # raise IngestModuleException("Oh No!")
        self.context = context

    # Where the analysis is done.
    # The 'dataSource' object being passed in is of type org.sleuthkit.datamodel.Content.
    # See: http://www.sleuthkit.org/sleuthkit/docs/jni-docs/latest/interfaceorg_1_1sleuthkit_1_1datamodel_1_1_content.html
    # 'progressBar' is of type org.sleuthkit.autopsy.ingest.DataSourceIngestModuleProgress
    # See: http://sleuthkit.org/autopsy/docs/api-docs/latest/classorg_1_1sleuthkit_1_1autopsy_1_1ingest_1_1_data_source_ingest_module_progress.html
    def process(self, dataSource, progressBar):

        progressBar.switchToIndeterminate()

        # Get all files from case
        fileManager = Case.getCurrentCase().getServices().getFileManager()
        files = fileManager.findFiles(dataSource, "%")

        blackboard = Case.getCurrentCase().getSleuthkitCase().getBlackboard()
        artId = blackboard.getOrAddArtifactType("TSK_TRANSCRIBED_TEXT", "Transcribed Text")
        attrId = blackboard.getOrAddAttributeType("TSK_TRANSCRIPT_ATTR", BlackboardAttribute.TSK_BLACKBOARD_ATTRIBUTE_VALUE_TYPE.STRING, "Transcription")
        
        # Get Transcribe.py directory
        transcriptPath = os.path.join(os.getenv("APPDATA") + "\\autopsy\\python_modules\\AutopsyAudioTranscriptModule\\Transcribe.py")

        numFiles = len(files)
        self.log(Level.INFO, "Found " + str(numFiles) + " files")
        progressBar.switchToDeterminate(numFiles)
        fileCount = 0   # Incremented for audio and video files
        transcriptionTimes = [] # Store the times taken to transcribe each file

        for file in files:

            # Check if the user pressed cancel while we were busy
            if self.context.isJobCancelled():
                return IngestModule.ProcessResult.OK

            fileName = file.getName()
            self.log(Level.INFO, "Processing file: " + fileName)
            
            # Skip unallocated and unused blocks
            if ((file.getMIMEType() is not None) and 
                (file.getType() != TskData.TSK_DB_FILES_TYPE_ENUM.UNALLOC_BLOCKS) and 
                (file.getType() != TskData.TSK_DB_FILES_TYPE_ENUM.UNUSED_BLOCKS)):

                # If audio file is selected, run through transcription program
                if (file.getMIMEType().startswith("audio")):
                    startTime = time.time()
                    fileCount += 1

                    self.log(Level.INFO, "FILE " + fileName + " IS AN AUDIO FILE")
                    filePath = createTempFile(file)

                    command = ['python3', transcriptPath, str(filePath), str(fileCount)]

                # If video file is selected, convert to audio file then run through transcription program
                elif (file.getMIMEType().startswith("video")):
                    startTime = time.time()
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
                
                # Calculate time taken to transcribe the file
                endTime = time.time()
                timeTaken = endTime - startTime
                self.log(Level.INFO, "TRANSCRIPTION TIME FOR " + fileName + " WAS " + str(timeTaken) + " SECONDS")
                transcriptionTimes.append(timeTaken)
                self.log(Level.INFO, "Result: " + str(result))

                # Post the transcribed file as an artifact to the Blackboard
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

            else:
                continue
            
            # Update the progress bar
            progressBar.progress(files.index(file))

        totalTime = sum(transcriptionTimes)
        self.log(Level.INFO, "Number of files transcribed: " + str(fileCount))
        self.log(Level.INFO, "Total Transcription time was " + str(totalTime) + " seconds.")
        
        #Post a message to the ingest messages in box.
        message = IngestMessage.createMessage(IngestMessage.MessageType.DATA,
            "Audio Transcript Ingest Module", "Found %d files" % fileCount)
        IngestServices.getInstance().postMessage(message)

        return IngestModule.ProcessResult.OK
