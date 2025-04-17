# llm.py (large language model)
#
# purpose: provides a function to send raw transcribed text to an openai gpt
#          model (specifically gpt-4o-mini) for punctuation, capitalization,
#          and general formatting cleanup.
#
# dependencies: openai (official python client library)
#               asyncio (for running blocking api calls in executor)
#               os (to retrieve api key from environment variables)
#               functools (for functools.partial)
#               logging (for status/error messages)
#
# key components: format_text function (async function takes raw text, returns formatted text)
#                 system constant (defines the system prompt for the llm)
#
# design rationale: utilizes the chat completions api for formatting. gpt-4o-mini
#                   is chosen for its balance of speed, cost, and capability for this
#                   task. a system prompt guides the model to perform the desired
#                   cleanup and return only the result. similar to stt.py, the api
#                   call uses run_in_executor for non-blocking async operation.
#                   re-uses the openai client initialized in stt.py for efficiency.
#
import openai
import asyncio
import functools
import logging
import os  # needed if client initialization is moved here
from dotenv import load_dotenv

# --- setup ---

# load environment variables (if not already loaded by another module)
load_dotenv()

# configure logging (ensure it's configured, might be redundant if main sets it up)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# reuse the client initialized in stt.py or initialize if run standalone
# note: in a real app, client initialization is better handled centrally.
# if 'client' not in globals() or client is None:
#     try:
#         client = openai.OpenAI()
#         logging.info("OpenAI client initialized in llm.py.")
#     except openai.OpenAIError as e:
#         logging.error(f"Failed to initialize OpenAI client in llm.py: {e}.")
#         client = None
# else:
#     logging.info("Reusing OpenAI client from another module (presumably stt.py)")
# simplified approach for now, assuming client exists from stt import:
from stt import client  # attempt to import the initialized client

# --- constants ---

# system prompt defining the llm's task
SYSTEM_PROMPT = "You are a helpful assistant that corrects grammar, punctuation, and capitalization in text. Respond with only the corrected text, nothing else. Do not add any introductory phrases like 'Here is the corrected text:'."
# model to use for formatting
FORMATTING_MODEL = "gpt-4o-mini"
# controls randomness, lower values make output more deterministic
TEMPERATURE = 0.2

# --- public functions ---


async def format_text(raw_text: str) -> str | None:
    """formats the raw text using an openai llm (gpt-4o-mini).

    sends the raw text along with a system prompt to the specified model
    and returns the cleaned-up text content from the response.
    runs the blocking api call in a separate thread using run_in_executor.

    args:
        raw_text (str): the raw text transcript to format.

    returns:
        str | none: the formatted text, stripped of leading/trailing whitespace,
                    or none if formatting fails or the client isn't initialized.
    """
    if not client:
        logging.error("OpenAI client not initialized. Cannot format text.")
        return None
    if not raw_text or raw_text.isspace():
        logging.warning("Received empty or whitespace-only text for formatting.")
        return raw_text  # return original if nothing to format

    logging.info(
        f"Starting text formatting for input: '{raw_text[:50]}...' ({len(raw_text)} chars)"
    )
    loop = asyncio.get_event_loop()

    # construct messages for the chat completions api
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": raw_text},
    ]

    try:
        # prepare the function call for the executor
        func = functools.partial(
            client.chat.completions.create,
            model=FORMATTING_MODEL,
            messages=messages,
            temperature=TEMPERATURE,
        )

        # run the blocking api call in the executor
        logging.info(f"Sending text to OpenAI {FORMATTING_MODEL} API...")
        response = await loop.run_in_executor(None, func)
        logging.info("Received formatting response from API.")

        # extract the formatted text content
        if response.choices:
            formatted_text = response.choices[0].message.content.strip()
            logging.info(
                f"Formatting successful. Output: '{formatted_text[:50]}...' ({len(formatted_text)} chars)"
            )
            # print(f"Formatted text: {formatted_text}") # debug
            return formatted_text
        else:
            logging.warning("OpenAI response contained no choices.")
            return None

    except openai.APIError as e:
        logging.error(f"OpenAI API error during text formatting: {e}")
        return None
    except Exception as e:
        logging.error(
            f"An unexpected error occurred during text formatting: {e}", exc_info=True
        )
        return None
