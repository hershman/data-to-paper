from typing import Dict, Any

from pathlib import Path

from data_to_paper.run_gpt_code.overrides.contexts import OverrideStatisticsPackages
from data_to_paper.run_gpt_code.overrides.dataframes import TrackDataFrames


def create_pandas_and_stats_contexts(allow_dataframes_to_change_existing_series: bool = False,
                                     enforce_saving_altered_dataframes: bool = False,
                                     issue_if_statistics_test_not_called: bool = False,
                                     ) -> Dict[str, Any]:
    return {
        'TrackDataFrames': TrackDataFrames(
            allow_dataframes_to_change_existing_series=allow_dataframes_to_change_existing_series,
            enforce_saving_altered_dataframes=enforce_saving_altered_dataframes,
        ),
        'OverrideStatisticsPackages': OverrideStatisticsPackages(
            issue_if_statistics_test_not_called=issue_if_statistics_test_not_called),
    }


def convert_filename_to_label(filename) -> str:
    """
    Convert a filename to a label.
    """
    label = Path(filename).stem

    # check if the label is valid:
    if not label.isidentifier():
        raise ValueError(f'Invalid filename: "{filename}". The filename must be a valid identifier.')
    return label
