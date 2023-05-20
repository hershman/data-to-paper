import difflib
import colorama

from dataclasses import dataclass
from enum import Enum
from typing import NamedTuple, Optional

from scientistgpt.env import TEXT_WIDTH, MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF, HIDE_INCOMPLETE_CODE
from scientistgpt.base_cast import Agent
from scientistgpt.run_gpt_code.code_runner import CodeRunner
from scientistgpt.run_gpt_code.exceptions import FailedExtractingCode
from scientistgpt.servers.openai_models import OpenaiCallParameters, ModelEngine
from scientistgpt.utils import format_text_with_code_blocks, line_count
from scientistgpt.utils.code_utils import wrap_text_with_triple_quotes

# noinspection PyUnresolvedReferences
colorama.just_fix_windows_console()


class Role(Enum):
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'
    SURROGATE = 'surrogate'
    COMMENTER = 'commenter'

    def is_assistant_or_surrogate(self):
        return self in [Role.ASSISTANT, Role.SURROGATE]

    def is_not_commenter(self):
        return self is not Role.COMMENTER


class ResponseStyle(NamedTuple):
    color: str
    block_color: str
    separator: str


ROLE_TO_STYLE = {
    Role.SYSTEM: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.USER: ResponseStyle(colorama.Fore.GREEN, colorama.Fore.LIGHTGREEN_EX, '-'),
    Role.ASSISTANT: ResponseStyle(colorama.Fore.CYAN, colorama.Fore.LIGHTCYAN_EX, '='),
    Role.SURROGATE: ResponseStyle(colorama.Fore.CYAN, colorama.Fore.LIGHTCYAN_EX, '='),
    Role.COMMENTER: ResponseStyle(colorama.Fore.BLUE, colorama.Fore.LIGHTBLUE_EX, ' '),
}


@dataclass
class Message:
    role: Role
    content: str
    tag: str = ''
    agent: Optional[Agent] = None
    openai_call_parameters: Optional[OpenaiCallParameters] = None
    ignore: bool = False  # if True, this message will be skipped when calling openai
    is_background: bool = False
    # True: message will not be shown in the web conversation
    # False: message will be shown in web conversation
    # None: message will be shown only if not repeated

    index_in_conversation: Optional[int] = None
    # index of the message in the conversation

    effective_index_in_conversation: Optional[int] = None
    # index of the message in the conversation, ignoring commenter and ignored messages

    def to_chatgpt_dict(self):
        return {'role': Role.ASSISTANT.value if self.role.is_assistant_or_surrogate()
                else self.role.value, 'content': self.content}

    def pretty_repr(self, number: Optional[int] = None, conversation_name: str = '', is_color: bool = True) -> str:
        """
        Returns a pretty repr of the message with color and heading.

        number: message sequential number in the conversation.

        Takes care of:
        * Indicating Role with name and color.
        * Adding separation lines
        * Indenting text
        * Highlighting code blocks
        """
        role, content, tag, agent = self.role, self.content, self.tag, self.agent
        tag_text = f' <{tag}> ' if tag else ''
        agent_text = f' {{{agent.value}}}' if agent else ''
        num_text = f'[{number}] ' if number else ''
        style = ROLE_TO_STYLE[role]
        sep = style.separator
        if is_color:
            text_color, block_color, reset_color = style.color, style.block_color, colorama.Style.RESET_ALL
        else:
            text_color = block_color = reset_color = ''
        role_text = role.name + ('' if self.openai_call_parameters is None else f'({self.openai_call_parameters})')
        if role == Role.SYSTEM:
            role_model_agent_conversation_tag = f'{role_text} casting {agent_text} for {conversation_name} '
        else:
            role_model_agent_conversation_tag = f'{role_text}{agent_text} -> {conversation_name}{tag_text} '

        if role == Role.COMMENTER:
            return text_color + num_text + role_model_agent_conversation_tag + ': ' + content + reset_color

        # header:
        s = text_color + num_text + sep * (9 - len(num_text)) + ' ' + role_model_agent_conversation_tag \
            + sep * (TEXT_WIDTH - len(role_model_agent_conversation_tag) - 9 - 1) + '\n'

        # content:
        s += self.pretty_content(text_color, block_color, width=TEXT_WIDTH)
        if s[-1] != '\n':
            s += '\n'

        # footer:
        s += text_color + sep * TEXT_WIDTH + reset_color
        return s

    def get_content_after_hiding_incomplete_code(self) -> (str, bool):
        """
        Detect if the message contains incomplete code.
        """
        content = self.content.strip()
        sections = self.content.split('```')
        is_incomplete_code = HIDE_INCOMPLETE_CODE and len(sections) % 2 == 0
        if is_incomplete_code:
            partial_code = sections[-1]
            content = content.replace(
                partial_code,
                f"\n# NOT SHOWING {line_count(partial_code)} LINES OF INCOMPLETE CODE SENT BY CHATGPT\n```\n")
        return content, is_incomplete_code

    def _get_triple_quote_formatted_content(self, with_header: bool = True) -> (str, bool):
        content, is_incomplete_code = self.get_content_after_hiding_incomplete_code()
        if self.role == Role.SYSTEM:
            content = wrap_text_with_triple_quotes(content, 'system')
        if self.role == Role.COMMENTER:
            content = wrap_text_with_triple_quotes(content, 'comment')
        if with_header:
            chatgpt_parameters = f'({self.openai_call_parameters})' if self.openai_call_parameters else ''
            header = f'#{self.effective_index_in_conversation} {chatgpt_parameters}\n'
            header = wrap_text_with_triple_quotes(header, 'header')
            content = header + content
        return content, is_incomplete_code

    def pretty_content(self, text_color, block_color, width, is_html=False, with_header: bool = True) -> str:
        """
        Returns a pretty repr of just the message content.
        """
        content, _ = self._get_triple_quote_formatted_content(with_header)
        return format_text_with_code_blocks(text=content,
                                            text_color=text_color, block_color=block_color, width=width,
                                            is_html=is_html)

    def convert_to_text(self):
        return f'{self.role.value}<{self.tag}>\n{self.content}'

    @classmethod
    def from_text(cls, text):
        first_break = text.index('\n')
        first_lt = text.index('<')
        role = Role(text[:first_lt])
        tag = text[first_lt + 1: first_break - 1]
        content = text[first_break + 1:]
        return cls(role=role, content=content, tag=tag)


@dataclass
class CodeMessage(Message):
    """
    A message that contains code that needs to be compared to some previous code.
    """

    previous_code: str = None
    "The code from the previous response, to which this code should be compared"

    @property
    def extracted_code(self) -> Optional[str]:
        """
        Extract the code from the response.
        """
        try:
            return CodeRunner(response=self.content).extract_code()
        except FailedExtractingCode:
            return None

    def get_code_diff(self) -> str:
        """
        Get the difference between the code from the previous response and the code from this response.
        """
        diff = difflib.unified_diff(self.previous_code.strip().splitlines(),
                                    self.extracted_code.strip().splitlines(),
                                    lineterm='', n=0)
        # we remove the first 3 lines, which are the header of the diff:
        diff = list(diff)[3:]
        return '\n'.join(diff)

    def pretty_content(self, text_color, block_color, width, is_html=False, with_header: bool = True) -> str:
        """
        We override this method to replace the code within the message with the diff.
        """
        content, is_incomplete_code = self._get_triple_quote_formatted_content(with_header)
        if self.extracted_code and not is_incomplete_code and self.previous_code:
            diff = self.get_code_diff()
            if line_count(self.extracted_code) - line_count(diff) > MINIMAL_COMPACTION_TO_SHOW_CODE_DIFF:
                # if the code diff is substantially shorter than the code, we replace the code with the diff:
                content = content.replace(
                    self.extracted_code,
                    "# FULL CODE SENT BY CHATGPT IS SHOWN AS A DIFF WITH PREVIOUS CODE\n" + diff if diff
                    else "# CHATGPT SENT THE SAME CODE AS BEFORE\n")
        return format_text_with_code_blocks(content, text_color, block_color, width, is_html=is_html)


def create_message(role: Role, content: str, tag: str = '', agent: Optional[Agent] = None, ignore: bool = False,
                   openai_call_parameters: OpenaiCallParameters = None,
                   previous_code: str = None,
                   is_background: bool = False) -> Message:
    if previous_code:
        return CodeMessage(role=role, content=content, tag=tag, agent=agent, ignore=ignore,
                           openai_call_parameters=openai_call_parameters,
                           previous_code=previous_code,
                           is_background=is_background)
    else:
        return Message(role=role, content=content, tag=tag, agent=agent, ignore=ignore,
                       openai_call_parameters=openai_call_parameters,
                       is_background=is_background)


def create_message_from_other_message(other_message: Message,
                                      content: Optional[str] = None,
                                      agent: Optional[Agent] = None) -> Message:
    return create_message(role=other_message.role,
                          content=content if content else other_message.content,
                          tag=other_message.tag,
                          agent=agent if agent else other_message.agent,
                          ignore=other_message.ignore,
                          openai_call_parameters=other_message.openai_call_parameters,
                          previous_code=other_message.previous_code if isinstance(other_message, CodeMessage) else None,
                          is_background=other_message.is_background)
