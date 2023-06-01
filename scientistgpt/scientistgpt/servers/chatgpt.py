from __future__ import annotations

import time
import openai

from typing import List, Union

import tiktoken

from scientistgpt.env import MAX_MODEL_ENGINE, DEFAULT_MODEL_ENGINE, OPENAI_MODELS_TO_ORGANIZATIONS_AND_API_KEYS

from .base_server import ServerCaller, NoMoreResponsesToMockError
from .openai_models import ModelEngine

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from scientistgpt.conversation.message import Message


MAX_NUM_OPENAI_ATTEMPTS = 5

OPENAI_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS = 'maximum context length'
# a sub-string that indicates that an openai exception was raised due to the message content being too long


class OpenaiSeverCaller(ServerCaller):
    """
    Class to call OpenAI API.
    """
    file_extension = '_openai.txt'

    @staticmethod
    def _get_server_response(messages: List[Message], model_engine: ModelEngine, **kwargs) -> str:
        """
        Connect with openai to get response to conversation.
        """
        model_engine = model_engine or DEFAULT_MODEL_ENGINE
        organization, api_key = OPENAI_MODELS_TO_ORGANIZATIONS_AND_API_KEYS[model_engine] \
            if model_engine in OPENAI_MODELS_TO_ORGANIZATIONS_AND_API_KEYS \
            else OPENAI_MODELS_TO_ORGANIZATIONS_AND_API_KEYS[None]
        openai.api_key = api_key
        openai.organization = organization
        response = openai.ChatCompletion.create(
            model=min(MAX_MODEL_ENGINE, model_engine).value,
            messages=[message.to_chatgpt_dict() for message in messages],
            **kwargs,
        )
        return response['choices'][0]['message']['content']


OPENAI_SERVER_CALLER = OpenaiSeverCaller()


def count_number_of_tokens_in_message(messages: List[Message], model_engine: ModelEngine) -> int:
    """
    Count number of tokens in message using tiktoken.
    """
    model = model_engine.value or DEFAULT_MODEL_ENGINE
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = len(encoding.encode(''.join([message.to_chatgpt_dict() for message in messages])))

    return num_tokens


def try_get_chatgpt_response(messages: List[Message],
                             model_engine: ModelEngine = None,
                             **kwargs) -> Union[str, Exception]:
    """
    Try to get a response from openai to a specified conversation.

    The conversation is sent to openai after removing comment messages and any messages indicated
    in `hidden_messages`.

    If getting a response is successful then return response string.
    If failed due to openai exception, return None.
    """
    for attempt in range(MAX_NUM_OPENAI_ATTEMPTS):
        # TODO: add a check that the number of tokens is not too large before sending to openai, if it is then
        #     we can bump up the model engine before sending
        try:
            return OPENAI_SERVER_CALLER.get_server_response(messages, model_engine=model_engine, **kwargs)
        except openai.error.InvalidRequestError as e:
            # TODO: add here any other exception that can be addressed by changing the number of tokens
            #     or the bump up the model engine
            if OPENAI_MAX_CONTENT_LENGTH_MESSAGE_CONTAINS in str(e):
                return e
            print(f'OPENAI error:\n{type(e)}\n{e}')
        except NoMoreResponsesToMockError:
            raise
        except Exception as e:
            print(f'Unexpected OPENAI error:\n{type(e)}\n{e}')
        time.sleep(1.0 * 2 ** attempt)
    raise Exception(f'Failed to get response from OPENAI after {MAX_NUM_OPENAI_ATTEMPTS} attempts.')
