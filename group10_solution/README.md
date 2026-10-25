> **Note:** This README was generated with the help of generative AI (Claude, by Anthropic).

# Group 10: Assignment #1

Solution to the first mandatory assignment of the course *Data Mining and Machine Learning* (Autumn 2026, Software Design 2026).

The zip contains this folder (code and data) and the project report (PDF), which has the "Work Allocation" as its last page.

## Folder structure

```
Data/
  Raw/                   the original survey files (.tsv, .json, .yaml, .xml)
  Processed/CSV/         the four survey files converted to .csv
  Processed/Clean/       DataCleaning.ipynb and its output dataminers_clean.csv
Q1_Motivation/
  q1_solution.ipynb      Question 1
Q2_WeatherAnalysis/
  weather_correlation.ipynb   Question 2
  daily_entries_with_rainfall.csv
Mandatory_Exercises/     the weekly exercises tagged (Assignment #01)
README.md
```

## Research questions

- **Q1:** Can a student's other reasons for taking the course predict whether they ticked "mandatory"?
- **Q2:** Is it possible to find a correlation between the accumulated precipitation and the number of survey responses on a given day?

## Files

### Data and preprocessing

- `Data/Processed/Clean/DataCleaning.ipynb` reads the four `.csv` files in `Data/Processed/CSV/`, cleans and merges them, and writes **`dataminers_clean.csv`** (222 rows, 15 columns, including the feature-engineered columns). The cleaned file is already included, so this notebook does not have to be run first. Running it recreates the same file.

### Question 1

- `Q1_Motivation/q1_solution.ipynb` reads `dataminers_clean.csv` and classifies whether a student ticked "mandatory" from the four other motives (logistic regression and k-NN, compared with a baseline).

### Question 2

- `Q2_WeatherAnalysis/weather_correlation.ipynb` counts the survey responses per day, fetches the accumulated precipitation for each of those days from DMI, writes `daily_entries_with_rainfall.csv` and fits a linear regression.

### Mandatory exercises

| Exercise | Topic |
|---|---|
| 03.04 | 3D Linear Transformations |
| 03.05 | Solving a System of Linear Equations |
| 03.07 | Bases, Projections and Approximations |
| 05.02 | Descriptive Statistics |
| 05.04 | Categorical Data Exploration |
| 05.06 | Interactive Visualization and Exploratory Data Analysis |
| 06.02 | Simple Linear Regression |
| 06.03 | Multiple Linear Regression |
| 06.04 | Non-Linear Regression |
| 07.02 | The Closest Neighbors Are the Trustful Ones! |

`common.py` is shared by 06.02, 06.03 and 06.04. `Assets/`, `starwars.csv` and `starwarsClean.csv` hold images and data used by the exercises, and `report05.06.html` is the profiling report written by 05.06.

## Data sources

- Survey data provided as part of the assignment description.
- Rainfall: DMI Open Data, Climate Data API (station 06180, Copenhagen Airport), parameter `acc_precip` (accumulated precipitation). Data from DMI, licensed CC BY 4.0.

## How to run

The code is written as Jupyter notebooks (`.ipynb`) and was tested with Python 3.12.

1. Install the packages:

   ```
   pip install pandas numpy scipy scikit-learn statsmodels matplotlib seaborn plotly ydata-profiling ipywidgets requests notebook
   ```

   Versions used when testing: pandas 2.3.3, numpy 2.1.3, scikit-learn 1.9.0, statsmodels 0.14.6, matplotlib 3.10.0, seaborn 0.13.2, plotly 6.9.0, ydata-profiling 4.18.4. Exercise 05.06 needs `ipywidgets`.

2. Open each notebook from its own folder (Jupyter and VS Code do this by default). The notebooks read their data with relative paths, so the folder structure above must stay as it is.

3. An internet connection is needed for two things:
   - `weather_correlation.ipynb` sends one request to the DMI API for every survey day.
   - `Mandatory_Exercises/common.py` downloads the California housing data the first time it is used (exercises 06.02 to 06.04).
