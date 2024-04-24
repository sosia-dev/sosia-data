#!/usr/bin/env python3
# Authors:  Michael E. Rose <michael.ernst.rose@gmail.com>
#           Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Compiles up-to-date source information to be downloaded by sosia."""

from pathlib import Path
from tqdm import tqdm
from urllib.parse import parse_qs, urlparse

import pandas as pd
import pybliometrics
from pybliometrics.scopus import AbstractRetrieval
from pybliometrics.scopus.exception import Scopus404Error

FNAME_CONTENT = Path("ext_list_March_2024.xlsx")
pybliometrics.scopus.init()


def clean_string(x):
    """Auxiliary function to clean a string Series."""
    return x.replace(";", " ").replace(",", " ").replace("  ", " ").strip()


def download_source_id(link):
    """Retrieve source ID from abstract given its EID in a link."""
    try:
        eid = parse_qs(urlparse(link).query)["eid"][0]
    except KeyError:
        return None
    try:
        ab = AbstractRetrieval(eid, view="FULL")
        fields = ([f.code for f in ab.subject_areas])
        return {"source_id": ab.source_id, "asjc": fields}
    except (TypeError, Scopus404Error):
        return None
    except:
        print(eid)
        return None


def update_dict(d, lst, key, replacement):
    """Auxiliary function to add keys to a dictionary if a given string is
    included in the key.
    """
    for c in lst:
        if c.lower().startswith(key):
            d[c] = replacement


if __name__ == '__main__':
    print(">>> Reading Excel file...")
    external = pd.read_excel(FNAME_CONTENT, sheet_name=None)

    print(">>> Now parsing sources and fields from sheet:")
    out = []
    for name, df in external.items():
        print(f"... '{name}'")
        if "type" not in df.columns:
            df["type"] = "cp"
        try:
            subset = df
            subset["asjc"] = subset["asjc"].astype(str).apply(clean_string).str.split()
        except KeyError:
            df = df.dropna(subset=["Link"])
            source_info = {idx: download_source_id(link) for idx, link in
                           tqdm(enumerate(df["Link"]), total=df.shape[0], leave=False)}
            source_info = pd.DataFrame.from_dict(source_info).T
            subset = pd.concat([df, source_info], axis=1)
            subset = subset.dropna(subset=["source_id"])
        subset = (subset.set_index(["source_id", "title", "type"])
                        .asjc.apply(pd.Series)
                        .stack()
                        .rename("asjc")
                        .reset_index()
                        .drop(columns="level_3"))
        out.append(subset)
    out = pd.concat(out, axis=0)
    out = out[out["asjc"] != "nan"]
    out["asjc"] = out["asjc"].astype("uint32")

    # Write info
    order = ["source_id", "type", "title"]
    out["type"] = out["type"].str.title().str.strip()
    type_map = {"Journal": "jr", "Conference Proceedings": "cp",
                "Cp": "cp", "Trade Journal": "tr", "Book Series": "bk"}
    out["type"] = out["type"].replace(type_map)
    info = (out.drop_duplicates("source_id")
               .dropna().sort_values(order))
    info[order].to_csv("./source_info.csv", index=False)
    print(f">>> Found {info.shape[0]:,} sources")
    print(out["type"].value_counts())

    # Write list of fields by source
    out = (out.drop(columns=["title", "type"])
              .drop_duplicates()
              .sort_values(["source_id", "asjc"]))
    out.to_csv("./field_sources_map.csv", index=False)
    print(f">>> Found {out.shape[0]:,} sources with ASJC4 information")
    dist = out["source_id"].value_counts().value_counts().sort_index()
    share_one = dist.loc[1]/dist.sum()
    print(f"--- {dist.loc[1]:,} sources w/ one ASJC4 ({share_one:.1%})")
