# stt.py (speech-to-text)
#
# purpose: provides a function to send an audio file to the openai whisper api
#          for transcription and returns the resulting text.
#
# dependencies: openai (official python client library)
#               asyncio (for running blocking api calls in executor)
#               os (to retrieve api key from environment variables)
#               functools (for functools.partial)
#               logging (for status/error messages)
#
# key components: transcribe function (async function takes audio path, returns text)
#
# design rationale: uses the official openai library for interacting with the
#                   whisper api. the api call is potentially blocking, so it's
#                   wrapped with loop.run_in_executor to avoid blocking the main
#                   async event loop. api key is securely fetched from environment
#                   variables using dotenv for flexibility during development.
#
import openai
import asyncio
import os
import functools
import logging
from dotenv import load_dotenv

# --- setup ---

# load environment variables from .env file (especially for api key)
load_dotenv()

# configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# initialize openai client
# reads OPENAI_API_KEY automatically from environment variables
try:
    client = openai.OpenAI()
    logging.info("OpenAI client initialized successfully.")
except openai.OpenAIError as e:
    logging.error(
        f"Failed to initialize OpenAI client: {e}. Make sure OPENAI_API_KEY is set."
    )
    client = None  # set client to none to prevent further errors

# --- public functions ---


async def transcribe(path: str) -> str | None:
    """transcribes the audio file at the given path using openai whisper.

    opens the audio file, sends it to the whisper-1 model via the
    openai api, and returns the transcribed text.
    runs the blocking api call in a separate thread using run_in_executor.

    args:
        path (str): the file path to the audio file (expecting .wav).

    returns:
        str | none: the transcribed text, stripped of leading/trailing whitespace,
                    or none if transcription fails or the client isn't initialized.
    """
    if not client:
        logging.error("OpenAI client not initialized. Cannot transcribe.")
        return None
    if not os.path.exists(path):
        logging.error(f"Audio file not found at path: {path}")
        return None

    logging.info(f"Starting transcription for audio file: {path}")
    loop = asyncio.get_event_loop()

    try:
        # open the file in binary read mode
        with open(path, "rb") as audio_file:
            # prepare the function call with arguments for the executor
            # use functools.partial to pass the file handle and other args
            func = functools.partial(
                client.audio.transcriptions.create, model="whisper-1", file=audio_file
            )

            # run the blocking openai api call in the default executor (thread pool)
            logging.info("Sending audio to OpenAI Whisper API...")
            response = await loop.run_in_executor(None, func)
            logging.info("Received transcription response from API.")

        # extract and clean the text
        transcript = response.text.strip()
        logging.info(f"Transcription successful. Length: {len(transcript)} chars.")
        # print(f"Raw transcript: {transcript}") # debug
        return transcript

    except FileNotFoundError:
        logging.error(
            f"Error opening audio file (already checked exists, race condition?): {path}"
        )
        return None
    except openai.APIError as e:
        logging.error(f"OpenAI API error during transcription: {e}")
        return None
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during transcription: {e}", exc_info=True
        )
        return None
    finally:
        # attempt to clean up the temporary audio file after transcription
        try:
            # be cautious about deleting files not created by this specific function
            # only delete if it's confirmed to be a temporary file we should manage
            # for now, assume the caller (e.g., audio.py) manages its temp file
            # if os.path.exists(path) and "tmp" in path: # simple check for temp path
            #     os.remove(path)
            #     logging.info(f"Cleaned up temporary audio file: {path}")
            pass  # let caller handle cleanup
        except OSError as ose:
            logging.warning(f"Could not clean up audio file {path}: {ose}")
