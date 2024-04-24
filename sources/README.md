- [field_sources_map.csv](field_sources_map.csv): Assigment of sources to fields
- [source_info.csv](source_info.csv): Names and type of sources

# How to update the data

1. Download the file that says "Download the Source title list" from https://www.elsevier.com/products/scopus/content in this folder. Save it as "extlist.xlsx" in this folder.
2. Remove the sheets that contain just the ASJC codes (named "ASJC classification codes" or similar) and the sheet with Medline information (named "More info Medline" or similar). Also drop the sheets with the most recent accepted titles and the sheet with the most recent discontinued titles. There should be only three sheets left: the list of current sources, the list of conference proceedings with profile, and the full list of conference proceedings.
3. In the sheet listing the current sources as well as the serial conference proceedings, the columns need to named like this: "source_id" (the source ID), "title" (the name of the source), "type" (the type of the source), "asjc" (the associated ASJC codes). The other columns can be dropped.
4. In the sheet with the conference proceedings, drop the columns "Title" (inproceeding title), "Year", "Volume", "PUI", and any other unnamed columns.
5. Then execute [generate_sources_definition.py](generate_sources_definition.py).
