# Code repository for NYTIMES API example

## Overview

See http://schaunwheeler.github.io/nytimes/ for the live web page.

The nytimes_climate_change.py file in this repository can be run from the command line and will output an index.html file that mirrors the page found at the link above, updated to reflect the most recent 30-day period.

For the script to run, it must be ammended to include a valid NYTIMES API key.

The requirements.txt file lists the Python libraries needed to run the script.

## Suggested Changes

### Basics
* Error handling for the API connection (retry on timeout, etc.)
* Command-line argument parsing to allow feeding of API key, search terms, etc.
* Formal logging rather than simple print commands
* Set up api calls and page builds as separate collections of functions intead of one long script.

### Analysis
* Automate interpretation of LDA topics (use component probilities to decide how many topics to include, etc.)
* More robust analysis of topic contribution to articles (don't just take the one most relevant topic)*[]:
* Define publication peaks more robustly than just maximu within calendar week - allow for peaks that extend across days, multiple peaks within a week, etc.
* Custom stopword removal: words like "said" or "say" don't get pulled out through normal removal of commonly-used words, but in the context of news articles they are too frequently used to be useful for analysis.
* **IMPORTANT** The `bk_section3_text4` object in the script creates the final paragraph of the web page, and includes the interpreation of the topic modeling results. This must be written entirely manually at this point - it's the only part of the page that won't continue to make sense as new time windows are used. This should be reworked to be automated like everything else.

### Formatting
* Polish the date formatting to be more user-friendly.
* Choose a more attractive color pallete for the bar charts than plain gray.
* Include simple hyperlink navigation to different parts of the page.
* Include tooltips in graphs to provide useful contextual information.



