# AutopsyAudioTranscriptModule
## By u2039563

Software requirements:
- Python version 3+
    - Speech Recognition library
- ffmpeg

Vosk Model - vosk-model-en-us-0.22
The model should be placed in a folder named "model" located in "AutopsyAudioTranscriptModule"

The ingest module folder "AutopsyAudioTranscriptModule" should be placed in the folder: "AppData\Roaming\autopsy\python_modules"

To Run Ingest Module:
1. Open a case in Autopsy,
2. Select 'Run Ingest Modules', then select 'Audio Transcript' and press 'Finish',
3. Once the ingest module has been run, the results will appear under Data Artifacts/Transcribed Text,
4. For Keyword Search to work, select 'Run Ingest Modules', then select 'Keyword Search', then press 'Finish',
5. The transcription results can now be queried using the 'Keyword Search' option in the top-right corner of Autopsy.
