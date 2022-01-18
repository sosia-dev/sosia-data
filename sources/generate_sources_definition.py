#!/usr/bin/env python3
# Authors:  Michael E. Rose <michael.ernst.rose@gmail.com>
#           Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Compiles up-to-date source information to be downloaded by sosia."""

import pandas as pd
import requests
from bs4 import BeautifulSoup

URL_SOURCES = "https://elsevier.com/?a=734751"
URL_CONTENT = "https://www.elsevier.com/solutions/scopus/how-scopus-works/content"


def create_fields_sources_list():
    """Download Scopus files with information on covered sources and create
    one list of all sources with ids and one with field information.
    """
    # Set up
    col_map = {
        "All Science Journal Classification Codes (ASJC)": "asjc",
        "Scopus ASJC Code (Sub-subject Area)": "asjc",
        "ASJC code": "asjc",
        "Source Type": "type",
        "ASJC Code": "asjc",
        "Type": "type",
        "Sourcerecord id": "source_id",
        "Sourcerecord ID": "source_id",
        "Scopus Source ID": "source_id",
        "Scopus SourceID": "source_id",
        "Scopus Source ID": "source_id",
        "Title": "title",
        "Source title": "title",
        "Source Title (Medline-sourced journals are indicated in Green)": "title",
        "Conference Title": "title"
    }
    keeps = list(set(col_map.values()))
    type_map = {"j": "journal", "p": "conference proceedings",
                "d": "trade journal", "k": "book series"}

    # Get Information from Scopus Sources list
    resp = requests.get(URL_SOURCES).content
    sources = pd.read_excel(resp, sheet_name=None, engine='pyxlsb')
    _drop_sheets(sources, ["About CiteScore", "ASJC codes"])
    dfs = [df.rename(columns=col_map)[keeps].dropna() for df in sources.values()]
    out = pd.concat(dfs).drop_duplicates()
    out["type"] = out["type"].replace(type_map)

    # Add information from list of external publication titles
    resp = requests.get(_get_source_title_url()).content
    external = pd.read_excel(resp, sheet_name=None)
    drops = ["Accepted titles Nov. 2021", "Discontinued titles Nov. 2021",
             "More info Medline", "ASJC classification codes"]
    _drop_sheets(external, drops)

    for df in external.values():
        _update_dict(col_map, df.columns, "source title", "title")
        if "Source Type" not in df.columns:
            df["type"] = "conference proceedings"
        subset = df.rename(columns=col_map)[keeps].dropna()
        subset["asjc"] = subset["asjc"].astype(str).apply(_clean).str.split()
        subset = (subset.set_index(["source_id", "title", "type"])
                        .asjc.apply(pd.Series)
                        .stack()
                        .rename("asjc")
                        .reset_index()
                        .drop("level_3", axis=1))
        out = pd.concat([out, subset], sort=True)

    # Write list of names
    order = ["source_id", "title"]
    names = out[order].drop_duplicates().sort_values("source_id")
    names.to_csv("./sources_names.csv", index=False)

    # Write list of fields by source
    out["type"] = out["type"].str.title().str.strip()
    print(out["type"].value_counts())
    out["asjc"] = out["asjc"].astype(int)
    out.drop("title", axis=1).to_csv("./field_sources_list.csv", index=False)


def _clean(x):
    """Auxiliary function to clean a string Series."""
    return x.replace(";", " ").replace(",", " ").replace("  ", " ").strip()


def _drop_sheets(sheets, drops):
    """Auxiliary function to drop sheets from an Excel DataFrame."""
    for drop in drops:
        try:
            sheets.pop(drop)
        except KeyError:
            continue


def _get_source_title_url():
    """Extract the link to the most recent Scopus sources list."""
    resp = requests.get(URL_CONTENT)
    soup = BeautifulSoup(resp.text, "lxml")
    try:
        return soup.find("a", {"title": "source list"})["href"]
    except AttributeError:
        raise ValueError("Link to sources list not found.")


def _update_dict(d, lst, key, replacement):
    """Auxiliary function to add keys to a dictionary if a given string is
    included in the key.
    """
    for c in lst:
        if c.lower().startswith(key):
            d[c] = replacement


if __name__ == '__main__':
    create_fields_sources_list()
