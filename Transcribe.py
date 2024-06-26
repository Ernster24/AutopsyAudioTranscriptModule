import speech_recognition as speech
import os
import sys

modulePath = os.path.join(os.getenv("APPDATA") + "\\autopsy\\python_modules\\AutopsyAudioTranscriptModule")
os.chdir(modulePath)
r = speech.Recognizer()

def transcribe(filePath, fileNo):
    with speech.AudioFile(filePath) as source:
        audio_data = r.record(source)
        try:
            # Vosk Speech API
            text = r.recognize_vosk(audio_data)

            # Format output string to only include the transcribed text
            textStart = text.find(':')
            textEnd = text.rfind('"')
            newText = text[textStart + 3:textEnd]
            print(newText)
            return newText
        except:
            return "Error Transcribing Audio!"

if __name__ == "__main__":
    filePath = sys.argv[1]
    fileNo = sys.argv[2]
    
    transcribe(filePath, fileNo)
