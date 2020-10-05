from google.cloud import speech
from time import strftime
from time import gmtime
from google.cloud import storage
import wave, os, glob
import subprocess

BUCKET_NAME = 'testdata1234'

"""
    Upload Local File to Cloud Storage Bucket

    :param blob_name: Blob FileName
    :param path_to_file: Local path to file
    :return: File path to this resource in Cloud Storage
"""
def upload_to_bucket(blob_name, path_to_file):
    print(f"Uploading {blob_name}")
    storage_client = storage.Client()

    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(path_to_file)
    return f'gs://{BUCKET_NAME}/{blob_name}'


"""
    Speech to Text

    :param gcs_uri: Audio File's Cloud Storage URL
    :param model: Speech to Text Transcription models
    :return: Speech to Text Response
"""
def speech_to_text_conversion(gcs_uri, model):
    print(f"Speech to Text Conversion Started...")
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
    return response

"""
    Generate Subtitile and Save Locally

    :param speech_to_text_response: Speech to Text Response
    :param filename: Video File BaseName
    :return: void
"""
def generate_subtitle(speech_to_text_response, file_basename):
    print(f"Subtitle Generate Started...")
    res = []
    for i, result in enumerate(speech_to_text_response.results):
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
        f = open(f"{file_basename}-subtitle-{i}.srt", "w")
        f.write(res[i])
        f.close()

# Main
for video_filename in glob.glob(os.path.join('', '*.mp4')):
    audio_file_basename = '.'.join(video_filename.split('.')[0:-1])
    audio_filename = f"{audio_file_basename}.wav"

    # Converting MP4 to WAV
    print(f"\nConverting {video_filename} to {audio_filename}")
    subprocess.Popen(f"ffmpeg -i \"{video_filename}\" -acodec pcm_s16le -ac 1 -ar 16000 -y \"{audio_filename}\"", stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    
    # Upload Converted WAV File to Cloud Bucket
    gcs_uri = upload_to_bucket(audio_filename, audio_filename)
    
    # Speech to Text Conversion
    speech_to_text_response = speech_to_text_conversion(gcs_uri, "default")

    # Generate Subtitile
    generate_subtitle(speech_to_text_response, audio_file_basename)