#
# Imports
#

import pandas as pd


def format_selic_expectations(data) -> pd.DataFrame:
    """Format the latest COPOM expectations as a dated time series."""
    dataframe = pd.DataFrame(data)
    latest_date = dataframe["Data"].iloc[-1]
    dataframe = dataframe[dataframe["Data"] == latest_date].copy()
    dataframe[["ReuniaoNumber", "ReuniaoYear"]] = dataframe["Reuniao"].str.split("/", expand=True)
    dataframe["ReuniaoNumber"] = dataframe["ReuniaoNumber"].str.replace("R", "").astype(int)
    dataframe["DataReferencia"] = pd.to_datetime(dataframe["ReuniaoYear"] + "-01-31") + pd.to_timedelta(
        (dataframe["ReuniaoNumber"] - 1) * 45,
        unit="D",
    )

    next_meeting = dataframe.copy()
    next_meeting["DataReferencia"] += pd.to_timedelta(45, unit="D")
    next_meeting["DataReferencia"] = next_meeting["DataReferencia"].apply(lambda value: value.replace(day=31) if value.month == 1 else value)
    dataframe.index = dataframe.index * 2
    next_meeting.index = next_meeting.index * 2 + 1
    dataframe = pd.concat([dataframe, next_meeting]).sort_index().set_index("DataReferencia")
    return dataframe.drop(columns=["Data", "Reuniao", "ReuniaoNumber", "ReuniaoYear"])


def format_expectations(data, frequency: str) -> pd.DataFrame:
    """Format the latest monthly or annual market expectations."""
    formats = {"monthly": "%m/%Y", "annual": "%Y"}
    if frequency not in formats:
        raise ValueError("frequency must be 'monthly' or 'annual'")

    dataframe = pd.DataFrame(data)
    latest_date = dataframe["Data"].iloc[-1]
    dataframe = dataframe[dataframe["Data"] == latest_date].copy()
    dataframe["DataReferencia"] = pd.to_datetime(dataframe["DataReferencia"], format=formats[frequency])
    return dataframe.set_index("DataReferencia").drop(columns=["Data"])
