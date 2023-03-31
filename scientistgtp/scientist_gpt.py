from typing import Optional, List, Callable, Any, Tuple, NamedTuple, Dict
from textwrap import dedent

from .conversation import Conversation, Role
from .code_runner import CodeRunner
from .proceed_retract import ProceedRetract, FuncAndRetractions, RunPlan
from .exceptions import RunCodeException

OUTPUT_FILENAME = 'results.txt'


def format_str(s: str):
    """
    Format a triple-quote string to remove extra indentation and leading newline.
    """
    return dedent(s).lstrip()


class ScientistGTP(ProceedRetract):
    STATE_ATTRS: List[str] = ['conversation']

    def __init__(self,
                 run_plan: List[FuncAndRetractions] = None,
                 saved_states: List[Dict] = None,
                 current_step: int = -1,
                 data_description: Optional[str] = None,
                 goal_description: Optional[str] = None,
                 ):
        super().__init__(run_plan, saved_states, current_step)
        self.data_description = data_description
        self.goal_description = goal_description
        self.conversation: Optional[Conversation] = None

    def initialize_conversation(self):
        prompt = 'You are a helpful scientist.'
        self.conversation = Conversation()
        self.conversation.append_message(Role.SYSTEM, prompt)

    def add_data_description(self):
        prompt = format_str(f"""
            We have the following data files:

            {self.data_description}
            """)
        self.conversation.append_user_message(prompt)
        self.conversation.append_assistant_message('ok')

    def add_goal_description(self):
        prompt = format_str(f"""
            {self.goal_description}
            """)
        self.conversation.append_user_message(prompt)
        self.conversation.append_assistant_message('ok')

    def request_analysis_plan(self):
        prompt = format_str(f"""
            Suggest a data analysis plan to achieve the specified goal.
            """)
        self.conversation.append_user_message(prompt)
        return self.conversation.get_response_from_chatgpt()

    def request_analysis_code(self):
        prompt = format_str(f"""
            Write a complete Python code to perform the analysis you suggested.'
            The output of the code should be a text file named `{OUTPUT_FILENAME}`.
            """)
        self.conversation.append_user_message(prompt)
        return self.conversation.get_response_from_chatgpt()

    def run_analysis_code(self):
        analysis_code_response = self.conversation.get_last_response()
        result = CodeRunner(response=analysis_code_response, output_file=OUTPUT_FILENAME).run_code()
        prompt = format_str(f"""
            I ran your code. Here are the results:
            {result}
            
            Does it look ok?
            
            If not, please refine/correct the code you gave above and send me a new full compete code to 
            correctly do the analysis.
            """)
        self.conversation.append_user_message(prompt)


ANALYSIS_PLAN: RunPlan = [
    FuncAndRetractions('initialize_conversation', (), []),
    FuncAndRetractions('add_data_description', (), []),
    FuncAndRetractions('add_goal_description', (), []),
    FuncAndRetractions('request_analysis_plan', (), []),
    FuncAndRetractions('request_analysis_code', (), []),
    FuncAndRetractions('run_analysis_code', RunCodeException, [1, 1, 2, 1, 1, 2]),
]
