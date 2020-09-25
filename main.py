from google.cloud import speech
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
            sentence_start_time = 0.00
            sentence_end_time = 0.00
            for word_info in alternative.words:
                #word = word_info.word
                start_time = word_info.start_time
                end_time = word_info.end_time
                sentence_start_time = min(sentence_start_time, start_time.total_seconds())
                sentence_end_time = max(sentence_end_time, end_time.total_seconds())
            res[idx] += f"{sentence_start_time} - {sentence_end_time} : {alternative.transcript}\n"
    for i in range(len(res)):
        f = open(f"{filename}-transcript-{i}.txt", "w")
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
for filename in glob.glob(os.path.join('', '*.wav')):  
    upload_to_bucket(filename, filename)
    transcribe_model_selection_gcs(f"gs://{bucket_name}/{filename}", "default", filename)