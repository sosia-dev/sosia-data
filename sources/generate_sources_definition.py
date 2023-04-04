# Authors:  Michael E. Rose <michael.ernst.rose@gmail.com>
#           Stefano H. Baruffaldi <ste.baruffaldi@gmail.com>
"""Compiles up-to-date source information to be downloaded by sosia."""

from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

# if empty, will download file from URL_SOURCES
FNAME_SOURCES = Path("")
URL_SOURCES = "https://elsevier.com/?a=734751"

# if empty, will search and download file from URL_CONTENT
FNAME_CONTENT = Path("")
URL_CONTENT = "https://www.elsevier.com/solutions/scopus/how-scopus-works/content"


def clean_string(x):
    """Auxiliary function to clean a string Series."""
    return x.replace(";", " ").replace(",", " ").replace("  ", " ").strip()


def drop_sheets_from_excel(sheets, drops):
    """Auxiliary function to drop sheets from an Excel DataFrame."""
    for drop in drops:
        try:
            sheets.pop(drop)
        except KeyError:
            continue


def get_source_title_url():
    """Extract the link to the most recent Scopus sources list."""
    resp = requests.get(URL_CONTENT)
    soup = BeautifulSoup(resp.text, "lxml")
    try:
        return soup.find("a", {"title": "source list"})["href"]
    except AttributeError:
        raise ValueError("Link to sources list not found.")


def read_sources(content, col_map):
    """Read Excel file containing sheets with source coverage information."""
    excel = pd.read_excel(resp, sheet_name=None, engine='pyxlsb')
    drop_sheets_from_excel(df, ["About CiteScore", "ASJC codes"])
    dfs = [df.rename(columns=col_map)[keeps].dropna() for df in excel.values()]
    return pd.concat(dfs).drop_duplicates()


def update_dict(d, lst, key, replacement):
    """Auxiliary function to add keys to a dictionary if a given string is
    included in the key.
    """
    for c in lst:
        if c.lower().startswith(key):
            d[c] = replacement


def main():
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
    type_map = {"j": "Journal", "p": "Conference Proceedings",
                "d": "Trade Journal", "k": "Book Series"}

    # Get Information from Scopus Sources list
    if FNAME_SOURCES:
        resp = FNAME_SOURCES
    else:
        resp = requests.get(URL_SOURCES).content
    out = read_sources(resp, col_map)
    out["type"] = out["type"].replace(type_map)

    # Add information from list of external publication titles
    if FNAME_CONTENT:
        resp = FNAME_CONTENT
    else:
        resp = requests.get(get_source_title_url()).content
    external = pd.read_excel(resp, sheet_name=None)
    drops = ["Accepted titles Nov. 2021", "Discontinued titles Nov. 2021",
             "More info Medline", "ASJC classification codes"]
    drop_sheets_from_excel(external, drops)

    for df in external.values():
        update_dict(col_map, df.columns, "source title", "title")
        if "Source Type" not in df.columns:
            df["type"] = "Conference Proceedings"
        subset = df.rename(columns=col_map)[keeps].dropna()
        subset["asjc"] = subset["asjc"].astype(str).apply(_clean).str.split()
        subset = (subset.set_index(["source_id", "title", "type"])
                        .asjc.apply(pd.Series)
                        .stack()
                        .rename("asjc")
                        .reset_index()
                        .drop(columns="level_3"))
        out = pd.concat([out, subset], sort=True)

    # Write list of names
    order = ["source_id", "title"]
    names = out[order].sort_values(order).drop_duplicates(subset="source_id")
    names.to_csv(Path("./sources_names.csv"), index=False)

    # Write list of fields by source
    out["type"] = out["type"].str.title().str.strip()
    out["asjc"] = out["asjc"].astype(int)
    out = (out.drop(columns="title").sort_values(["type", "source_id", "asjc"])
              .drop_duplicates())
    out.to_csv(Path("./field_sources_list.csv"), index=False)


if __name__ == '__main__':
    main()
