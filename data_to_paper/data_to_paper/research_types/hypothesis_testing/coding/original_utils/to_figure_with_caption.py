def to_latex_figure_with_caption(figure, filename: str, caption: str, label: str, comment: str = None):
    """
    Save a figure with a caption and label.
    """
    figure.savefig(filename)
    latex = f"""
\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.8\\textwidth]{{{filename}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}
"""
    if comment:
        latex = comment + '\n' + latex
    with open(filename.replace('.pdf', '.tex'), 'w') as f:
        f.write(latex)
    return latex

def get_figure_and_caption_as_html(figure, filename: str, caption: str, label: str, comment: str = None):
    """
    Save a figure with a caption and label.
    """
    figure.savefig(filename)
    html = f"""
<div>
<img src="{filename}" alt="{caption}" />
<p>{caption}</p>
</div>
"""
    if comment:
        html = comment + '\n' + html
    with open(filename.replace('.pdf', '.html'), 'w') as f:
        f.write(html)
    return html
