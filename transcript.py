import speech_recognition as speech
import sys

r = speech.Recognizer()

def transcribe(audio_file, file_no):
    with speech.AudioFile(audio_file) as source:
        audio_data = r.record(source)

        try:
            text = r.recognize_google(audio_data)
            print("Writing '" + text + "' to file...")
            return text
        except:
            return "!!!!Error Transcribing Audio!!!!"
            

        
        #transcript = open("transcript.txt", "a")
        #transcript.write("[" + str(file_no) + "] " + text + "\n")
        #transcript.close()
        


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python transcript.py <audio_file> <file_no>")
        
    audio_file = sys.argv[1]
    file_no = sys.argv[2]
    
    transcribe(audio_file, file_no)
  
