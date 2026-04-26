# VCT Data Analysis 

A data analysis and visualization toolkit for the Valorant Champions Tour (VCT).
Scrapes match statistics from vlr.gg and visualizes player kill/death positions
from official Riot Games VCT match data. Utilizes Amazon Bedrock's AI models to 
advise coaches on possible team selection and strategies.

## Features

- Scrapes player performance stats from [vlr.gg](https://www.vlr.gg) across all events
- Exports match results and event stats to CSV for further analysis
- Visualizes kill and death positions per player on interactive scatter plots
- Generates kill and death density heatmaps across all players in a match
- Tracks time-in-round and round number for every kill/death event
- Downloads official VCT game JSON files from AWS S3

## Tech Stack

- **Language:** Python
- **Scraping:** `requests`, `BeautifulSoup`
- **Data Processing:** `pandas`, `ijson`, `json`
- **Visualization:** `matplotlib`, `seaborn`, `mplcursors`
- **Data Source:** vlr.gg + Riot Games official VCT match data (S3)
