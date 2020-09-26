from google.cloud import speech
from time import strftime
from time import gmtime
def transcribe_model_selection_gcs(gcs_uri, model, filename):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(    
        language_code="en-US",
        enable_automatic_punctuation=True,
        model=model,
        enable_word_time_offsets=True,
    )

    operation = client.long_running_recognize(
        request={"config": config, "audio": audio}
    )

    print("Waiting for operation to complete...")
    response = operation.result(timeout=1000000)
    res = []
    for i, result in enumerate(response.results):
        for idx in range(len(result.alternatives)):
            if (len(res) <= idx):
                res.append('')
            alternative = result.alternatives[idx]
            print("-" * 20)
            print("First alternative of result {}".format(i))
            print(u"Transcript: {}".format(alternative.transcript))
            sentence_start_time = 99999999.00
            sentence_end_time = 0.00
            for word_info in alternative.words:
                #word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time
                if sentence_start_time >= start_time.total_seconds():
                    sentence_start_time = start_time.total_seconds()
                    sentence_start_time_ms = str(start_time.microseconds // 1000).zfill(3)
                if sentence_end_time <= end_time.total_seconds():
                    sentence_end_time = end_time.total_seconds()
                    sentence_end_time_ms = str(end_time.microseconds // 1000).zfill(3)
            res[idx] += f"{i+1}\n"
            res[idx] += f"{strftime('%H:%M:%S', gmtime(sentence_start_time))},{sentence_start_time_ms} --> {strftime('%H:%M:%S', gmtime(sentence_end_time))},{sentence_end_time_ms}\n"
            res[idx] += f"{alternative.transcript}\n\n"
    for i in range(len(res)):
        f = open(f"{filename}-subtitle-{i}.srt", "w")
        f.write(res[i])
        f.close()

from google.cloud import storage
bucket_name = 'testdata1234'

def upload_to_bucket(blob_name, path_to_file):
    storage_client = storage.Client()

    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)
    return blob.public_url

import wave, os, glob
import subprocess
for filename in glob.glob(os.path.join('', '*.mp4')):
    audio_filename = f"{'.'.join(filename.split('.')[0:-1])}.wav"
    print(f"\nConverting {filename} to {audio_filename}")
    subprocess.Popen(f"ffmpeg -i \"{filename}\" -acodec pcm_s16le -ac 1 -ar 16000 \"{audio_filename}\"", stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    print(f"Uploading {audio_filename}")
    upload_to_bucket(audio_filename, audio_filename)
    print(f"Subtitle Generate Started...")
    transcribe_model_selection_gcs(f"gs://{bucket_name}/{audio_filename}", "default", '.'.join(filename.split('.')[0:-1]))