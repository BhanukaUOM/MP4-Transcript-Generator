def transcribe_model_selection_gcs(gcs_uri, model):
    """Transcribe the given audio file asynchronously with
    the selected model."""
    from google.cloud import speech

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
            res[idx] += alternative.transcript + ". "
    for i in range(len(res)):
        f = open("transcript-{}.txt".format(i), "a")
        f.write(res[i])
        f.close()
        
transcribe_model_selection_gcs("gs://sjfnsjfnsjkfnsjfnsj/test.wav", "default")