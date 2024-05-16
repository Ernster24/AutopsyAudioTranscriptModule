import os
import subprocess
import time
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
        startTime = time.time()
        transcriptText = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = transcriptText.communicate()
        endTime = time.time()   
        timeTaken = endTime - startTime # Calculate time taken to transcribe the file
        if transcriptText.returncode != 0:
            result = "Error transcribing file: " + str(stderr.decode('utf-8'))
            return result, timeTaken
        else:
            result = str(stdout.decode('utf-8'))
            return result, timeTaken
    except OSError as e:
        result = "Error transcribing audio file: " + str(e)
        return result, timeTaken

# Converts files to audio file (.wav) using ffmpeg
def convertFile(fileName, filePath, isVideo):
    name, extension = os.path.splitext(fileName)
    
    if extension == ".wav": # If audio file is already in .wav format, return the original file path
        return filePath
    else:
        newAudioFileName = (name + '.wav')
        newAudioFilePath = filePath.replace(fileName, newAudioFileName)
        
        if isVideo == True: # If file is a video, convert the audio track into a .wav file
            try:
                subprocess.check_call(["ffmpeg", "-i", filePath, "-vn", newAudioFilePath])
                return newAudioFilePath
            except subprocess.CalledProcessError as e:
                return ("Error during ffmpeg conversion: ", e)
        else:   # If file is an audio file, convert to .wav file
            try:
                subprocess.check_call(["ffmpeg", "-i", filePath, newAudioFilePath])
                return newAudioFilePath
            except subprocess.CalledProcessError as e:
                return ("Error during ffmpeg conversion: ", e)
