from google.cloud import speech
def transcribe_model_selection_gcs(gcs_uri, model):
    client = speech.SpeechClient()

    audio = speech.RecognitionAudio(uri=gcs_uri)

    config = speech.RecognitionConfig(    
        language_code="en-US",
        model=model,
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
            res[idx] += f"{alternative.transcript}. "
    for i in range(len(res)):
        f = open("transcript-{}.txt".format(i), "a")
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
    transcribe_model_selection_gcs(f"gs://{bucket_name}/{filename}", "default")