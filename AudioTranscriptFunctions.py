# Imports
import os
import subprocess
from java.lang import System
from java.util.logging import Level
from java.io import File
from org.sleuthkit.autopsy.datamodel import ContentUtils
from org.sleuthkit.autopsy.casemodule import Case
from org.sleuthkit.autopsy.casemodule.services import FileManager


# Opens a temporary directory and copies the selected file into it
def createTempFile(file):
    dir = Case.getCurrentCase().getTempDirectory()
    filePath = os.path.join(dir, file.getName())
    ContentUtils.writeToFile(file, File(filePath))

    return filePath

# Transcribes an audio file
# The 'command' argument consists of a shell command which runs Transcribe.py using python3 
def transcribeAudioFile(command):
    try:
        transcriptText = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = transcriptText.communicate()
        if transcriptText.returncode != 0:
            result = "Error transcribing file: " + str(stderr.decode('utf-8'))
            return result
        else:
            result = "File transcribed successfully: " + str(stdout.decode('utf-8'))
            return result
    except OSError as e:
        result = "Error transcribing audio file: " + str(e)
        return result

# Converts video file to audio file (.wav) using ffmpeg
def convertVideoFile(fileName, filePath):
    name, extension = os.path.splitext(fileName)
    newAudioFileName = (name + '.wav')
    newAudioFilePath = filePath.replace(fileName, newAudioFileName)
    
    try:
        subprocess.check_call(["ffmpeg", "-i", filePath, "-vn", newAudioFilePath])
        return newAudioFilePath
    except subprocess.CalledProcessError as e:
        return ("Error during ffmpeg conversion: ", e)