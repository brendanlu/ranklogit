"""

Rough Python script to use ranklogit. 

A similar version of this is used at the moment, for commercial research 
purposes.

MS Excel mangles csvs, so grudgingly, we use xlsx config files.

"""

import os
import pandas as pd
import time
from typing import List

import misc
import ranklogit as rl

GLOBALSTART = time.time()
MWIDTHS = 80
R = 3  # rounding
ERRSTRING = "ERROR!!!!!!!!!!!!!!!"

CONFIGPATH = "misc\config.xlsx"
ROWPRIORS = 0
ROWBINOM = 1
ROWRANK = slice(2, None)

BINARYMAP = {2: 1, 1: 0}

OUTPUTNAMEAPPEND = "_LClassLabelling"


def disp_messages(messages: List[str]):
    print(f"Runtime: {round((time.time() - GLOBALSTART), R)}s".center(MWIDTHS, "-"))

    for m in messages:
        print(m.center(MWIDTHS, " "))

    print("-" * MWIDTHS)
    print("\n")

    if ERRSTRING in messages:
        quit()


# MAIN -------------------------------------------------------------------------
print("\n")
disp_messages(
    [
        "Found all necessary libraries; program starts here.",
        "Processing file and column name configurations now...",
    ]
)

config_df = pd.read_excel(
    CONFIGPATH, sheet_name=0, index_col=0, header=0, engine="openpyxl"
)
config_df.astype(str)
config_df.applymap(lambda x: x.strip())  # remove accidental whitespace input

data_file_path = config_df.iloc[0, 0]
if not data_file_path.endswith(".csv"):
    data_file_path += ".csv"

if data_file_path not in os.listdir():
    disp_messages(
        [
            ERRSTRING,
            "Check the input data filename...",
            "The program cannot find it.",
        ]
    )
else:
    data_df = pd.read_csv(data_file_path)
    data_df.columns = data_df.columns.str.strip()

input_col_names = config_df.iloc[1:, 0]
fail_to_find = []
for name in input_col_names:
    if name not in data_df.columns:
        fail_to_find.append(name)

if fail_to_find:
    disp_messages(
        [
            ERRSTRING,
            "Failed to find input columns listed below",
        ]
        + fail_to_find
    )

disp_messages(
    [
        "Data file and input column names have been found.",
        "Reading in model parameter configurations...",
    ]
)

params_df = pd.read_excel(
    CONFIGPATH, sheet_name=1, header=0, index_col=0, engine="openpyxl"
)
try:
    params_df.applymap(lambda x: float(x))
except ValueError:
    disp_messages(
        [
            ERRSTRING,
            "Check the 'params' tab of the config worksheet",
            "There may be some non numeric values",
        ]
    )

if params_df.iloc[:, 0:4].isnull().values.any():
    disp_messages(
        [
            ERRSTRING,
            "Check the 'params' tab of the config worksheet",
            "There may be some blank values",
        ]
    )

disp_messages(
    [
        "Parameter configurations have been read in successfully.",
        "Initializing statistical models now...",
    ]
)

latent_class_models = []
for lclass in params_df.columns:
    latent_class_models.append(
        misc.LatentClassSpecificWrapperModel(
            (
                misc.GeneralMultinoulliModel(
                    (params_df[lclass][ROWBINOM], 1 - params_df[lclass][ROWBINOM])
                ),
                rl.TiedRankingLogitModel(params_df[lclass][ROWRANK]),
            )
        )
    )

mixture_model = misc.LCAMixtureModel(
    models=latent_class_models, weights=params_df.iloc[ROWPRIORS, :]
)

disp_messages(
    [
        "Models have been initialized. Wrangling data file now.",
    ]
)

data_df[config_df.iloc[ROWBINOM, 0]] = data_df.apply(
    lambda line: BINARYMAP[line[config_df.iloc[ROWBINOM, 0]]], axis=1
)

disp_messages(["Creating new column and labelling data..."])

data_df["Latent Class Allocation"] = pd.NA
labelling_start = time.time()
data_df["Latent Class Allocation"] = data_df.apply(
    lambda line: mixture_model.predict(
        (
            line[config_df.iloc[ROWBINOM, 0]],  # binom observation
            (
                line[config_df.loc["1a:"][0]],
                line[config_df.loc["1b:"][0]],
                line[config_df.loc["1c:"][0]],
                line[config_df.loc["1d:"][0]],
                line[config_df.loc["1e:"][0]],
                line[config_df.loc["1f:"][0]],
                line[config_df.loc["1g:"][0]],
                line[config_df.loc["1h:"][0]],
                line[config_df.loc["1i:"][0]],
                line[config_df.loc["1j:"][0]],
                line[config_df.loc["1k:"][0]],
                line[config_df.loc["1l:"][0]],
            ),
        )
    ),
    axis=1,
)
label_time = time.time() - labelling_start

disp_messages(
    [
        f"{len(data_df)} data points successfully labelled in {round(label_time, R)} seconds",
        "Writing into output file now...",
    ]
)

output_path = data_file_path[:-4] + OUTPUTNAMEAPPEND + ".csv"
data_df.to_csv(output_path, index=False)

disp_messages(
    [
        "All done! Look for output file: ",
        f"{output_path}",
        "Press ENTER to close this window.",
    ]
)

# add any other debug stuff here -----------------------------------------------
# print(latent_class_models[0].models[1].cache)
# print("\n\n")
# print(latent_class_models[0].models[1].cache_hits)
# print("\n\n")
# print(len(data_df.loc[data_df["segmentsTPFCT"] != data_df["Latent Class Allocation"]]))
# ------------------------------------------------------------------------------

input()
