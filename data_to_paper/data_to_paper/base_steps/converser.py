from __future__ import annotations

from dataclasses import dataclass, field

from typing import Optional, Any

from data_to_paper import Message
from data_to_paper.conversation.actions_and_conversations import ActionsAndConversations
from data_to_paper.env import COALESCE_WEB_CONVERSATIONS, TEXT_WIDTH
from data_to_paper.conversation.conversation import WEB_CONVERSATION_NAME_PREFIX
from data_to_paper.conversation import ConversationManager, GeneralMessageDesignation
from data_to_paper.interactive import PanelNames
from data_to_paper.interactive.app_interactor import AppInteractor
from data_to_paper.servers.model_engine import ModelEngine
from data_to_paper.utils.copier import Copier
from data_to_paper.utils.replacer import StrOrReplacer, format_value
from data_to_paper.utils.print_to_file import print_and_log_red, print_and_log_magenta
from data_to_paper.base_cast import Agent


@dataclass
class Converser(Copier, AppInteractor):
    """
    A base class for agents interacting with LLMs.
    """
    COPY_ATTRIBUTES = {'actions_and_conversations', 'conversation_name', 'web_conversation_name', 'assistant_agent',
                       'user_agent'}
    LLM_PARAMETERS = {}  # default parameters to pass to the LLM. e.g. {'temperature': 0.0, 'max_tokens': 30}
    actions_and_conversations: ActionsAndConversations = None

    model_engine: ModelEngine = field(default_factory=lambda: ModelEngine.DEFAULT)
    # The openai model engine to use (a call to apply_get_and_append_assistant_message can override this value).

    llm_parameters: dict[str, Any] = None

    system_prompt: str = 'You are a helpful scientist.'

    assistant_agent: Agent = None
    user_agent: Agent = None

    conversation_name: str = 'default'
    is_new_conversation: Optional[bool] = True
    # if True, we assert that no conversation with the same name exists.
    # if False, we assert that a conversation with the same name exists.
    # if None, we make sure the conversation is new by changing the name, if needed.

    web_conversation_name: Optional[str] = True
    # None - do not post to web conversation, True - use default name, str - use given name

    driver: str = ''

    def __post_init__(self):
        conversation_exists = self.conversation_name in self.actions_and_conversations.conversations
        if self.is_new_conversation is False:
            assert conversation_exists, f'Conversation {self.conversation_name} does not exist.'
        elif self.is_new_conversation is True:
            assert not conversation_exists, f'Conversation {self.conversation_name} already exists.'
        else:
            if conversation_exists:
                self.conversation_name = self.actions_and_conversations.conversations.get_new_conversation_name(
                    self.conversation_name)
        if self.llm_parameters is None:
            self.llm_parameters = self.LLM_PARAMETERS

        if self.web_conversation_name is True:
            # we determine an automatic conversation name based on the agent that the main agent is talking to:
            if COALESCE_WEB_CONVERSATIONS:
                web_conversation_name = \
                    self.user_agent.get_conversation_name() or self.assistant_agent.get_conversation_name()
            else:
                web_conversation_name = self.conversation_name
            if web_conversation_name:
                web_conversation_name = WEB_CONVERSATION_NAME_PREFIX + web_conversation_name
            self.web_conversation_name = web_conversation_name
        self.conversation_manager = ConversationManager(
            actions_and_conversations=self.actions_and_conversations,
            conversation_name=self.conversation_name,
            web_conversation_name=self.web_conversation_name,
            driver=self.driver if self.driver is not None else type(self).__name__,
            assistant_agent=self.assistant_agent,
            user_agent=self.user_agent,
        )

    @property
    def user_skin_name(self):
        return None if self.user_agent is None else self.user_agent.skin_name

    @property
    def assistant_skin_name(self):
        return None if self.assistant_agent is None else self.assistant_agent.skin_name

    @property
    def conversation(self):
        return self.conversation_manager.conversation

    def initialize_conversation_if_needed(self, print_header: bool = True):
        if self.conversation_manager.initialize_conversation_if_needed():
            self._app_clear_panels()
            if print_header:
                print_and_log_magenta('==== Starting conversation ' + '=' * (TEXT_WIDTH - 27))
                print_and_log_magenta(self.conversation_name.center(TEXT_WIDTH))
                print_and_log_magenta('=' * TEXT_WIDTH)
        if len(self.conversation) == 0 and self.system_prompt:
            self.apply_append_system_message(self.system_prompt)

    def comment(self, comment: StrOrReplacer, tag: Optional[StrOrReplacer] = None, as_action: bool = True,
                **kwargs):
        """
        Print a comment, either directly, or as an action appending a COMMENTER message to the conversation (default).
        """
        comment = format_value(self, comment)
        if as_action:
            self.conversation_manager.append_commenter_message(
                content=comment,
                tag=tag,
                **kwargs)
        else:
            print_and_log_red(comment)

    def apply_get_and_append_assistant_message(self, tag: Optional[StrOrReplacer] = None,
                                               comment: Optional[StrOrReplacer] = None,
                                               is_code: bool = False, previous_code: Optional[str] = None,
                                               model_engine: Optional[ModelEngine] = None,
                                               hidden_messages: GeneralMessageDesignation = None,
                                               expected_tokens_in_response: int = None,
                                               send_to_app: bool = True,
                                               **kwargs) -> Message:
        message = self.conversation_manager.get_and_append_assistant_message(
            tag=tag,
            comment=comment,
            is_code=is_code, previous_code=previous_code,
            model_engine=model_engine or self.model_engine,
            expected_tokens_in_response=expected_tokens_in_response,
            hidden_messages=hidden_messages,
            **{**self.llm_parameters, **kwargs})
        if send_to_app:
            self._app_send_prompt(PanelNames.RESPONSE, message.content)
        return message

    def apply_append_user_message(self, content: StrOrReplacer, tag: Optional[StrOrReplacer] = None,
                                  comment: Optional[StrOrReplacer] = None,
                                  ignore: bool = False, reverse_roles_for_web: bool = False,
                                  previous_code: Optional[str] = None, is_background: bool = False,
                                  send_to_app: Optional[bool] = None, app_panel: PanelNames = PanelNames.FEEDBACK,
                                  allow_editing: bool = False,
                                  **kwargs):
        content = format_value(self, content)
        if send_to_app is None:
            send_to_app = not is_background and not ignore
        if send_to_app:
            if allow_editing:
                content = self._app_receive_text(app_panel, content)
            self._app_send_prompt(app_panel, content)
        return self.conversation_manager.append_user_message(
            content=content,
            tag=tag,
            comment=comment,
            ignore=ignore, reverse_roles_for_web=reverse_roles_for_web,
            previous_code=previous_code, is_background=is_background, **kwargs)

    def apply_append_system_message(self, content: StrOrReplacer, tag: Optional[StrOrReplacer] = None,
                                    comment: Optional[StrOrReplacer] = None,
                                    ignore: bool = False, reverse_roles_for_web: bool = False,
                                    send_to_app: Optional[bool] = None,
                                    **kwargs):
        if send_to_app is None:
            send_to_app = not ignore
        if send_to_app:
            self._app_send_prompt(PanelNames.SYSTEM_PROMPT, content)
        return self.conversation_manager.append_system_message(
            content=format_value(self, content),
            tag=tag,
            comment=comment,
            ignore=ignore,
            reverse_roles_for_web=reverse_roles_for_web, **kwargs)

    def apply_append_surrogate_message(self, content: StrOrReplacer,
                                       tag: Optional[StrOrReplacer] = None, comment: Optional[StrOrReplacer] = None,
                                       ignore: bool = False, reverse_roles_for_web: bool = False,
                                       previous_code: Optional[str] = None, is_background: bool = False,
                                       send_to_app: Optional[bool] = False,
                                       **kwargs):
        if send_to_app is None:
            send_to_app = not is_background and not ignore
        if send_to_app:
            self._app_send_prompt(PanelNames.RESPONSE, content)
        return self.conversation_manager.append_surrogate_message(
            content=format_value(self, content),
            tag=tag,
            comment=comment,
            ignore=ignore, reverse_roles_for_web=reverse_roles_for_web,
            previous_code=previous_code, is_background=is_background, **kwargs)

    def apply_delete_messages(self, message_designation: GeneralMessageDesignation, comment: Optional[str] = None):
        return self.conversation_manager.delete_messages(message_designation, comment=comment)

    def set(self, **kwargs):
        """
        Set attributes of the class.
        """
        for key, value in kwargs.items():
            setattr(self, key, value)
        return self
