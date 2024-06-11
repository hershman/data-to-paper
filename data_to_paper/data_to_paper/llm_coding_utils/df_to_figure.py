from typing import Optional, Dict

import pandas as pd
from matplotlib import pyplot as plt

from data_to_paper.latex.clean_latex import process_latex_text_and_math, replace_special_latex_chars
from data_to_paper.run_gpt_code.overrides.pvalue import OnStrPValue, OnStr, PValueToStars, convert_p_values_to_floats
from data_to_paper.utils.text_formatting import escape_html
from data_to_paper.utils.check_type import raise_on_wrong_func_argument_types_decorator
from data_to_paper.env import FOLDER_FOR_RUN

from .df_plot_with_pvalue import df_plot_with_pvalue, get_description_of_plot_creation
from .matplotlib_utils import rotate_xticklabels_if_not_numeric, \
    raise_if_numeric_axes_do_not_have_labels
from .note_and_legend import convert_note_and_glossary_to_html, convert_note_and_glossary_to_latex_figure_caption
from .utils import convert_to_latex_comment
from ..utils import format_text_with_code_blocks
from memory_profiler import profile


@raise_on_wrong_func_argument_types_decorator
def df_to_figure(df: pd.DataFrame, filename: Optional[str],
                 caption: Optional[str] = None,
                 label: Optional[str] = None,
                 note: Optional[str] = None,
                 glossary: Optional[Dict[str, str]] = None,
                 save_fig: bool = True,
                 raise_formatting_errors: bool = True,
                 is_html: bool = False,
                 **kwargs):
    """
    Create a matplotlib figure embedded in a LaTeX figure with a caption and label.
    """
    fig_filename = filename + '.png'
    if save_fig:
        fig, ax = plt.subplots()
        fig.set_size_inches(4, 3)
        df_with_p_values_replaced = convert_p_values_to_floats(df.copy())
        df_plot_with_pvalue(df_with_p_values_replaced, ax=ax, **kwargs)
        rotate_xticklabels_if_not_numeric(ax)
        if raise_formatting_errors:
            raise_if_numeric_axes_do_not_have_labels(ax)
        fig.tight_layout()  # Adjusts subplot parameters to give the plot more room
        fig.savefig(fig_filename)
        ax.clear()
        fig.clear()
        plt.close(fig)
        plt.close('all')

    index = kwargs.get('use_index', True)

    label = label or ''

    glossary = {} if glossary is None else glossary
    if 'x_p_value' in kwargs or 'y_p_value' in kwargs:
        glossary['Significance'] = PValueToStars().get_conversion_legend_text()

    caption = caption or ''

    if is_html:
        note_and_glossary = convert_note_and_glossary_to_html(df, note, glossary, index)
        caption_note_and_glossary = escape_html(caption) + '<br>' + note_and_glossary
        with OnStrPValue(OnStr.SMALLER_THAN):
            description = get_description_of_plot_creation(df, fig_filename, kwargs, is_html=True)
        s = get_figure_and_caption_as_html(fig_filename, caption_note_and_glossary.strip())
        s += description
    else:
        note_and_glossary = convert_note_and_glossary_to_latex_figure_caption(df, note, glossary, index)
        caption_note_and_glossary = replace_special_latex_chars(caption) + '\n' + note_and_glossary
        with OnStrPValue(OnStr.LATEX_SMALLER_THAN):
            description = get_description_of_plot_creation(df, fig_filename, kwargs, is_html=False)
        s = get_figure_and_caption_as_latex(fig_filename, caption_note_and_glossary.strip(), label)
        s += '\n' + convert_to_latex_comment(description)
    return s


def get_figure_and_caption_as_latex(filename: str, caption: str, label: str) -> str:
    """
    Save a figure with a caption and label.
    """
    caption = process_latex_text_and_math(caption)
    latex = f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.8\\textwidth]{{{filename}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}
"""
    return latex.strip()


def get_figure_and_caption_as_html(filename: str, caption: str, width: int = None):
    """
    Save a figure with a caption and label.
    """
    if width is None:
        width_str = ''
    else:
        width_str = f'width="{width}"'
    html = f"""
        <div>
        <img src="{FOLDER_FOR_RUN / filename}" alt="{caption}" {width_str} />
        <p>{caption}</p>
        </div>
    """
    return html
