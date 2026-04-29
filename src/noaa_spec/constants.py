"""Shared constants for NOAA ISD Global Hourly data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

BASE_URL = "https://www.ncei.noaa.gov/data/global-hourly/access"

# Derived from NOAA ISD quality-code tables in the checked-in format docs.
# See `spec_sources/isd-format-document-parts/part-03-mandatory-data-section.md`
# and `part-04-additional-data-section.md`. These constants preserve NOAA code
# vocabulary; interpretation stays visible in cleaned `*_quality_code` columns.
QUALITY_FLAGS = {
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "9",
    "A",
    "C",
    "I",
    "M",
    "P",
    "R",
    "U",
}

DATA_SOURCE_FLAGS = {
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "N",
    "O",
}

REPORT_TYPE_CODES = {
    "AERO",
    "AUST",
    "AUTO",
    "BOGUS",
    "BRAZ",
    "COOPD",
    "COOPS",
    "CRB",
    "CRN05",
    "CRN15",
    "FM-12",
    "FM-13",
    "FM-14",
    "FM-15",
    "FM-16",
    "FM-18",
    "GREEN",
    "MESOH",
    "MESOS",
    "MESOW",
    "MEXIC",
    "NSRDB",
    "PCP15",
    "PCP60",
    "S-S-A",
    "SA-AU",
    "SAO",
    "SAOSP",
    "SHEF",
    "SMARS",
    "SOD",
    "SOM",
    "SURF",
    "SY-AE",
    "SY-AU",
    "SY-MT",
    "SY-SA",
    "WBO",
    "WNO",
}

QC_PROCESS_CODES = {
    "V01",
    "V02",
    "V03",
}

CLOUD_QUALITY_FLAGS = {
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "9",
    "M",
}

CLOUD_SUMMATION_QC_FLAGS = {
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "9",
}

MANDATORY_QUALITY_FLAGS = {"0", "1", "2", "3", "4", "5", "6", "7", "9"}

SOLARAD_QC_FLAGS = {"1", "3", "9"}

SOLAR_IRRADIANCE_QC_FLAGS = {"0", "1", "2", "3", "9"}

SUNSHINE_PERCENT_QC_FLAGS = {"4", "5", "6", "7", "9", "M"}

SKY_COVER_LAYER_CODES = {f"{value:02d}" for value in range(0, 11)} | {"99"}
SKY_COVER_EXTENDED_CODES = {f"{value:02d}" for value in range(0, 20)} | {"99"}
SKY_COVER_OPAQUE_CODES = {
    "00",
    "01",
    "02",
    "03",
    "04",
    "05",
    "06",
    "07",
    "08",
    "09",
    "10",
    "12",
    "13",
    "15",
    "16",
    "18",
    "19",
    "99",
}
SKY_COVER_SUMMATION_CODES = {str(value) for value in range(0, 7)} | {"9"}
SKY_COVER_SUMMATION_CHARACTERISTICS = {"1", "2", "3", "4", "9"}
SKY_COVER_LAYER_TYPE_CODES = {f"{value:02d}" for value in range(0, 24)} | {"99"}
BELOW_STATION_LAYER_TYPE_CODES = {f"{value:02d}" for value in range(0, 11)} | {"99"}
BELOW_STATION_LAYER_TOP_CODES = {f"{value:02d}" for value in range(0, 10)} | {"99"}
CLOUD_GENUS_CODES = {f"{value:02d}" for value in range(0, 10)} | {"99"}

VERTICAL_DATUM_CODES = {
    "AGL",
    "ALAT",
    "AP",
    "CFB",
    "CRD",
    "ESLW",
    "GCLWD",
    "HAT",
    "HHW",
    "HTWW",
    "HW",
    "HWFC",
    "IND",
    "ISLW",
    "LAT",
    "LLW",
    "LNLW",
    "LRLW",
    "LSD",
    "LW",
    "LWD",
    "LWFC",
    "MHHW",
    "MHLW",
    "MHW",
    "MHWN",
    "MHWS",
    "MLHW",
    "MLLW",
    "MLLWS",
    "MLWN",
    "MLW",
    "MLWS",
    "MSL",
    "MTL",
    "NC",
    "NT",
    "ST",
    "SWA",
    "TLLW",
    "UD",
    "UK",
    "WGS84E",
    "WGS84G",
}

EQD_REASON_CODES = {"0", "1", "2", "3", "4", "5", "6", "7"}
EQD_UNIT_CODES = {
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "I",
    "J",
    "K",
    "L",
    "M",
    "O",
    "P",
    "Q",
    "R",
}
EQD_ELEMENT_UNITS_TABLE = {
    "A": "DT",
    "B": "F",
    "C": "HF",
    "D": "HM",
    "E": "IH",
    "F": "IT",
    "G": "KD",
    "H": "KS",
    "I": "MT",
    "J": "NA",
    "K": "N1",
    # `N2` remains a legacy spec alias for `N02` in some tables.
    # Keep the semantic mapping here while parser normalization handles alias resolution.
    "L": "N2",
    "M": "P",
    "O": "TC",
    "P": "TF",
    "Q": "IS",
    "R": "MS",
}
EQD_ELEMENT_NAMES = {
    "ALC",
    "ALM",
    "ALTP",
    "CC51",
    "CLC",
    "CLM",
    "CLHT",
    "CLT",
    "C2C3",
    "DPTC",
    "DPTP",
    "HZVS",
    "PRES",
    "PWTH",
    "PWVC",
    "RHUM",
    "SCH",
    "SLVP",
    "TMCD",
    "TMPD",
    "TMPW",
    "TSCE",
    "TSKC",
    "TSKY",
    "WD16",
    "WIND",
    "WND2",
}
EQD_FLAG1_CODES = {
    "A",
    "C",
    "D",
    "E",
    "G",
    "H",
    "I",
    "K",
    "M",
    "N",
    "P",
    "R",
    "S",
    "U",
    "W",
    "b",
    " ",
}
EQD_FLAG2_CODES = {"0", "1", "2", "3", "4", "5", "6", "E", "M", "S"}
LEGACY_EQD_PARAMETER_CODES = {
    "APC3",
    "ATOLD",
    "WOSPD",
    "WOLSPD",
    "WOLDIR",
    "WODIR",
    "ATOLDS",
    "ATOLT",
    "ATOD",
    "ATOT",
    "APOSP",
    "APOSLP",
    "APOLP",
    "APOLH",
    "APOA",
    "WGOSPD",
    "APCQ24",
    "APCTEN",
    "PRSWOA",
    "PSTWOP",
    "SCOCIG",
    "SCOHCG",
    "SCOLCB",
    "SCOLCG",
    "SCOMCG",
    "SCOTCV",
    "SCOTLC",
    "VODIS",
    "VOVAR",
    "PRCP",
    "ATMM",
    "ATMN",
    "ATMX",
    "SNDP",
    "SNWF",
} | {f"PRSWM{value}" for value in range(1, 8)} | {f"PRSWA{value}" for value in range(1, 5)} | {
    f"PSTWA{value}" for value in range(1, 3)
} | {f"PSTWM{value}" for value in range(1, 3)}
LEGACY_EQD_MSD_PATTERN = re.compile(r"^(?:A|D|T)(?:0[1-9]|1[0-2])(?:00[1-9]|0[1-7][0-9])$")
DDHHMM_PATTERN = re.compile(r"^(0[1-9]|[12][0-9]|3[01])([01][0-9]|2[0-3])[0-5][0-9]$")
HHMM_PATTERN = re.compile(r"^([01][0-9]|2[0-3])[0-5][0-9]$")
DAY_PAIR_PATTERN = re.compile(r"^(0[1-9]|[12][0-9]|3[01]){2}$")
DAY_PAIR_TRIPLE_PATTERN = re.compile(r"^(?:0[1-9]|[12][0-9]|3[01]|99){3}$")

# Doc-backed Domain Value ID tables for the pressure/geopotential/weather code
# families we actively parse. Keeping these as named tables makes the code-list
# validation traceable to the source docs instead of embedding anonymous ranges.
PRESSURE_TENDENCY_CODE_DEFINITIONS = {
    "0": "Increasing then decreasing; now same or higher than 3 hours ago",
    "1": "Increasing then steady or increasing more slowly; now higher than 3 hours ago",
    "2": "Increasing; now higher than 3 hours ago",
    "3": "Decreasing or steady then increasing, or increasing more rapidly; now higher than 3 hours ago",
    "4": "Steady; same as 3 hours ago",
    "5": "Decreasing then increasing; now same or lower than 3 hours ago",
    "6": "Decreasing then steady or decreasing more slowly; now lower than 3 hours ago",
    "7": "Decreasing; now lower than 3 hours ago",
    "8": "Steady or increasing then decreasing, or decreasing more rapidly; now lower than 3 hours ago",
    "9": "Missing",
}
PRESSURE_TENDENCY_CODES = set(PRESSURE_TENDENCY_CODE_DEFINITIONS)

GEOPOTENTIAL_ISOBARIC_LEVEL_DEFINITIONS = {
    "1": "1000 hectopascals",
    "2": "925 hectopascals",
    "3": "850 hectopascals",
    "4": "700 hectopascals",
    "5": "500 hectopascals",
    "9": "Missing",
}
GEOPOTENTIAL_ISOBARIC_LEVEL_CODES = set(GEOPOTENTIAL_ISOBARIC_LEVEL_DEFINITIONS)

DAILY_PRESENT_WEATHER_SOURCE_DEFINITIONS = {
    "AU": "sourced from automated ASOS/AWOS sensors",
    "AW": "sourced from automated sensors",
    "MW": "sourced from manually reported present weather",
}
DAILY_PRESENT_WEATHER_SOURCE_CODES = set(DAILY_PRESENT_WEATHER_SOURCE_DEFINITIONS)

DAILY_PRESENT_WEATHER_TYPE_DEFINITIONS = {
    "01": "Fog, ice fog, or freezing fog",
    "02": "Heavy fog or heavy freezing fog",
    "03": "Thunder",
    "04": "Ice pellets, sleet, snow pellets, or small hail",
    "05": "Hail",
    "06": "Glaze or rime",
    "07": "Dust, ash, blowing dust, blowing sand, or blowing obstruction",
    "08": "Smoke or haze",
    "09": "Blowing or drifting snow",
    "10": "Tornado, water spout, or funnel cloud",
    "11": "High or damaging winds",
    "12": "Blowing spray",
    "13": "Mist",
    "14": "Drizzle",
    "15": "Freezing drizzle",
    "16": "Rain",
    "17": "Freezing rain",
    "18": "Snow, snow pellets, snow grains, or ice crystals",
    "19": "Unknown precipitation",
    "21": "Ground fog",
    "22": "Ice fog or freezing fog",
}
DAILY_PRESENT_WEATHER_TYPE_CODES = set(DAILY_PRESENT_WEATHER_TYPE_DEFINITIONS)

DAILY_PRESENT_WEATHER_ABBREVIATION_DEFINITIONS = {
    "FG": "Fog, ice fog, or freezing fog",
    "FG+": "Heavy fog or heavy freezing fog",
    "TS": "Thunder",
    "PL": "Ice pellets, sleet, snow pellets, or small hail",
    "GR": "Hail",
    "GL": "Glaze or rime",
    "DU": "Dust, ash, blowing dust, blowing sand, or blowing obstruction",
    "HZ": "Smoke or haze",
    "BLSN": "Blowing or drifting snow",
    "FC": "Tornado, water spout, or funnel cloud",
    "WIND": "High or damaging winds",
    "BLPY": "Blowing spray",
    "BR": "Mist",
    "DZ": "Drizzle",
    "FZDZ": "Freezing drizzle",
    "RA": "Rain",
    "FZRA": "Freezing rain",
    "SN": "Snow, snow pellets, snow grains, or ice crystals",
    "UP": "Unknown precipitation",
    "MIFG": "Ground fog",
    "FZFG": "Ice fog or freezing fog",
}
DAILY_PRESENT_WEATHER_ABBREVIATIONS = set(DAILY_PRESENT_WEATHER_ABBREVIATION_DEFINITIONS)

PRESENT_WEATHER_COMPONENT_PRECIPITATION_CODE_DEFINITIONS = {
    "00": "No precipitation",
    "01": "Drizzle",
    "02": "Rain",
    "03": "Snow",
    "04": "Snow grains",
    "05": "Ice crystals",
    "06": "Ice pellets",
    "07": "Hail",
    "08": "Small hail and/or snow pellets",
    "09": "Unknown precipitation",
    "99": "Missing",
}
PRESENT_WEATHER_COMPONENT_PRECIPITATION_CODES = set(
    PRESENT_WEATHER_COMPONENT_PRECIPITATION_CODE_DEFINITIONS
)

AUTOMATED_PRESENT_WEATHER_CODE_DEFINITIONS = {
    "00": "No significant weather observed",
    "01": "Clouds dissolving or becoming less developed",
    "02": "State of sky unchanged during the past hour",
    "03": "Clouds forming or developing during the past hour",
    "04": "Haze, smoke, or dust in suspension with visibility >= 1 km",
    "05": "Smoke",
    "07": "Dust or sand raised by wind at or near the station",
    "10": "Mist",
    "11": "Diamond dust",
    "12": "Distant lightning",
    "18": "Squalls",
    "20": "Fog",
    "21": "Precipitation",
    "22": "Drizzle or snow grains",
    "23": "Rain",
    "24": "Snow",
    "25": "Freezing drizzle or freezing rain",
    "26": "Thunderstorm",
    "27": "Blowing or drifting snow or sand",
    "28": "Blowing or drifting snow or sand with visibility >= 1 km",
    "29": "Blowing or drifting snow or sand with visibility < 1 km",
    "30": "Fog",
    "31": "Fog or ice fog in patches",
    "32": "Fog or ice fog, thinning during the past hour",
    "33": "Fog or ice fog, no appreciable change during the past hour",
    "34": "Fog or ice fog, thickening during the past hour",
    "35": "Fog depositing rime",
    "40": "Precipitation",
    "41": "Precipitation, slight or moderate",
    "42": "Precipitation, heavy",
    "43": "Liquid precipitation, slight or moderate",
    "44": "Liquid precipitation, heavy",
    "45": "Solid precipitation, slight or moderate",
    "46": "Solid precipitation, heavy",
    "47": "Freezing precipitation, slight or moderate",
    "48": "Freezing precipitation, heavy",
    "50": "Drizzle",
    "51": "Drizzle, not freezing, slight",
    "52": "Drizzle, not freezing, moderate",
    "53": "Drizzle, not freezing, heavy",
    "54": "Drizzle, freezing, slight",
    "55": "Drizzle, freezing, moderate",
    "56": "Drizzle, freezing, heavy",
    "57": "Drizzle and rain, slight",
    "58": "Drizzle and rain, moderate or heavy",
    "60": "Rain",
    "61": "Rain, not freezing, slight",
    "62": "Rain, not freezing, moderate",
    "63": "Rain, not freezing, heavy",
    "64": "Rain, freezing, slight",
    "65": "Rain, freezing, moderate",
    "66": "Rain, freezing, heavy",
    "67": "Rain or drizzle and snow, slight",
    "68": "Rain or drizzle and snow, moderate or heavy",
    "70": "Snow",
    "71": "Snow, slight",
    "72": "Snow, moderate",
    "73": "Snow, heavy",
    "74": "Ice pellets, slight",
    "75": "Ice pellets, moderate",
    "76": "Ice pellets, heavy",
    "77": "Snow grains",
    "78": "Ice crystals",
    "80": "Showers or intermittent precipitation",
    "81": "Rain showers or intermittent rain, slight",
    "82": "Rain showers or intermittent rain, moderate",
    "83": "Rain showers or intermittent rain, heavy",
    "84": "Rain showers or intermittent rain, violent",
    "85": "Snow showers or intermittent snow, slight",
    "86": "Snow showers or intermittent snow, moderate",
    "87": "Snow showers or intermittent snow, heavy",
    "89": "Hail",
    "90": "Thunderstorm",
    "91": "Thunderstorm, slight or moderate, with no precipitation",
    "92": "Thunderstorm, slight or moderate, with rain showers and/or snow showers",
    "93": "Thunderstorm, slight or moderate, with hail",
    "94": "Thunderstorm, heavy, with no precipitation",
    "95": "Thunderstorm, heavy, with rain showers and/or snow",
    "96": "Thunderstorm, heavy, with hail",
    "99": "Tornado",
}
AUTOMATED_PRESENT_WEATHER_CODES = set(AUTOMATED_PRESENT_WEATHER_CODE_DEFINITIONS)

SUMMARY_OF_DAY_PAST_WEATHER_CODE_DEFINITIONS = {
    "00": "none to report",
    "01": "fog",
    "02": "fog reducing visibility to 1/4 mile or less",
    "03": "thunder",
    "04": "ice pellets",
    "05": "hail",
    "06": "glaze or rime",
    "07": "blowing dust or sand, visibility 1/2 mile or less",
    "08": "smoke or haze",
    "09": "blowing snow",
    "10": "tornado",
    "11": "high or damaging winds",
    "99": "missing",
}
SUMMARY_OF_DAY_PAST_WEATHER_CODES = set(SUMMARY_OF_DAY_PAST_WEATHER_CODE_DEFINITIONS)

PRESENT_WEATHER_VICINITY_CODE_DEFINITIONS = {
    "00": "No observation",
    "01": "Thunderstorm in vicinity",
    "02": "Showers in vicinity",
    "03": "Sandstorm in vicinity",
    "04": "Sand or dust whirls in vicinity",
    "05": "Duststorm in vicinity",
    "06": "Blowing snow in vicinity",
    "07": "Blowing sand in vicinity",
    "08": "Blowing dust in vicinity",
    "09": "Fog in vicinity",
    "99": "Missing",
}
PRESENT_WEATHER_VICINITY_CODES = set(PRESENT_WEATHER_VICINITY_CODE_DEFINITIONS)

MANUAL_PRESENT_WEATHER_CODE_DEFINITIONS = {
    "00": "Cloud development not observed or not observable",
    "01": "Clouds dissolving or becoming less developed",
    "02": "State of sky unchanged",
    "03": "Clouds forming or developing",
    "04": "Visibility reduced by smoke or volcanic ash",
    "05": "Haze",
    "06": "Widespread dust in suspension",
    "07": "Dust or sand raised by wind at the station",
    "08": "Dust or sand whirls near the station",
    "09": "Duststorm or sandstorm within sight or at the station",
    "10": "Mist",
    "11": "Patches of shallow fog or ice fog",
    "12": "Continuous shallow fog or ice fog",
    "13": "Lightning visible, no thunder heard",
    "14": "Precipitation within sight, not reaching the surface",
    "15": "Precipitation within sight, reaching the surface but distant",
    "16": "Precipitation within sight, reaching the surface near but not at the station",
    "17": "Thunderstorm, no precipitation at observation time",
    "18": "Squalls at or within sight of the station",
    "19": "Funnel cloud or waterspout at or within sight of the station",
    "20": "Drizzle or snow grains, not as showers",
    "21": "Rain, not as showers",
    "22": "Snow, not as showers",
    "23": "Rain and snow or ice pellets, not as showers",
    "24": "Freezing drizzle or freezing rain, not as showers",
    "25": "Rain showers",
    "26": "Snow showers or rain and snow showers",
    "27": "Hail or rain and hail showers",
    "28": "Fog or ice fog",
    "29": "Thunderstorm with or without precipitation",
    "30": "Slight or moderate duststorm/sandstorm, decreasing",
    "31": "Slight or moderate duststorm/sandstorm, no appreciable change",
    "32": "Slight or moderate duststorm/sandstorm, beginning or increasing",
    "33": "Severe duststorm/sandstorm, decreasing",
    "34": "Severe duststorm/sandstorm, no appreciable change",
    "35": "Severe duststorm/sandstorm, beginning or increasing",
    "36": "Slight or moderate drifting snow below eye level",
    "37": "Heavy drifting snow below eye level",
    "38": "Slight or moderate blowing snow above eye level",
    "39": "Heavy blowing snow above eye level",
    "40": "Fog or ice fog at a distance, not at the station during the preceding hour",
    "41": "Fog or ice fog in patches",
    "42": "Fog or ice fog, sky visible, thinning",
    "43": "Fog or ice fog, sky invisible, thinning",
    "44": "Fog or ice fog, sky visible, no appreciable change",
    "45": "Fog or ice fog, sky invisible, no appreciable change",
    "46": "Fog or ice fog, sky visible, thickening",
    "47": "Fog or ice fog, sky invisible, thickening",
    "48": "Fog depositing rime, sky visible",
    "49": "Fog depositing rime, sky invisible",
    "50": "Drizzle, not freezing, intermittent, slight",
    "51": "Drizzle, not freezing, continuous, slight",
    "52": "Drizzle, not freezing, intermittent, moderate",
    "53": "Drizzle, not freezing, continuous, moderate",
    "54": "Drizzle, not freezing, intermittent, heavy",
    "55": "Drizzle, not freezing, continuous, heavy",
    "56": "Drizzle, freezing, slight",
    "57": "Drizzle, freezing, moderate or heavy",
    "58": "Drizzle and rain, slight",
    "59": "Drizzle and rain, moderate or heavy",
    "60": "Rain, not freezing, intermittent, slight",
    "61": "Rain, not freezing, continuous, slight",
    "62": "Rain, not freezing, intermittent, moderate",
    "63": "Rain, not freezing, continuous, moderate",
    "64": "Rain, not freezing, intermittent, heavy",
    "65": "Rain, not freezing, continuous, heavy",
    "66": "Rain, freezing, slight",
    "67": "Rain, freezing, moderate or heavy",
    "68": "Rain or drizzle and snow, slight",
    "69": "Rain or drizzle and snow, moderate or heavy",
    "70": "Intermittent snowfall, slight",
    "71": "Continuous snowfall, slight",
    "72": "Intermittent snowfall, moderate",
    "73": "Continuous snowfall, moderate",
    "74": "Intermittent snowfall, heavy",
    "75": "Continuous snowfall, heavy",
    "76": "Diamond dust",
    "77": "Snow grains",
    "78": "Isolated star-like snow crystals",
    "79": "Ice pellets",
    "80": "Rain showers, slight",
    "81": "Rain showers, moderate or heavy",
    "82": "Rain showers, violent",
    "83": "Rain and snow showers, slight",
    "84": "Rain and snow showers, moderate or heavy",
    "85": "Snow showers, slight",
    "86": "Snow showers, moderate or heavy",
    "87": "Snow pellet or small hail showers, slight",
    "88": "Snow pellet or small hail showers, moderate or heavy",
    "89": "Hail showers, slight, no thunder",
    "90": "Hail showers, moderate or heavy, no thunder",
    "91": "Slight rain with recent thunderstorm but no thunderstorm at observation time",
    "92": "Moderate or heavy rain with recent thunderstorm but no thunderstorm at observation time",
    "93": "Slight snow, mixed precipitation, or hail with recent thunderstorm but no thunderstorm at observation time",
    "94": "Moderate or heavy snow, mixed precipitation, or hail with recent thunderstorm but no thunderstorm at observation time",
    "95": "Thunderstorm, slight or moderate, no hail, with rain and/or snow",
    "96": "Thunderstorm, slight or moderate, with hail",
    "97": "Thunderstorm, heavy, no hail, with rain and/or snow",
    "98": "Thunderstorm with duststorm or sandstorm",
    "99": "Thunderstorm, heavy, with hail",
}
MANUAL_PRESENT_WEATHER_CODES = set(MANUAL_PRESENT_WEATHER_CODE_DEFINITIONS)

MANUAL_PAST_WEATHER_CODE_DEFINITIONS = {
    "0": "Cloud covering 1/2 or less of the sky throughout the period",
    "1": "Cloud covering > 1/2 for part of the period and <= 1/2 for part of the period",
    "2": "Cloud covering > 1/2 of the sky throughout the period",
    "3": "Sandstorm, duststorm, or blowing snow",
    "4": "Fog, ice fog, or thick haze",
    "5": "Drizzle",
    "6": "Rain",
    "7": "Snow, or rain and snow mixed",
    "8": "Showers",
    "9": "Thunderstorms with or without precipitation",
}
MANUAL_PAST_WEATHER_CODES = set(MANUAL_PAST_WEATHER_CODE_DEFINITIONS)

AUTOMATED_PAST_WEATHER_CODE_DEFINITIONS = {
    "0": "No significant weather observed",
    "1": "Visibility reduced",
    "2": "Blowing phenomena with reduced visibility",
    "3": "Fog",
    "4": "Precipitation",
    "5": "Drizzle",
    "6": "Rain",
    "7": "Snow or ice pellets",
    "8": "Showers or intermittent precipitation",
    "9": "Thunderstorm",
}
AUTOMATED_PAST_WEATHER_CODES = set(AUTOMATED_PAST_WEATHER_CODE_DEFINITIONS)

REM_TYPE_CODES = {"SYN", "AWY", "MET", "SOD", "SOM", "HPD"}
QNN_ELEMENT_IDENTIFIERS = {
    "A": "ALC",
    "B": "ALM",
    "C": "ALTP",
    "D": "CC51",
    "E": "CLC",
    "F": "CLM",
    "G": "CLHT",
    "H": "CLT",
    "I": "C2C3",
    "J": "DPTC",
    "K": "DPTP",
    "L": "HZVS",
    "M": "PRES",
    "N": "PWTH",
    "O": "PWVC",
    "P": "RHUM",
    "Q": "SLVP",
    "R": "TMCD",
    "S": "TMPD",
    "T": "TMPW",
    "U": "TSCE",
    "V": "TSKC",
    "W": "WD16",
    "X": "WIND",
    "Y": "WND2",
}

ADDITIONAL_DATA_PREFIXES = {
    "AA",
    "AB",
    "AC",
    "AD",
    "AE",
    "AG",
    "AH",
    "AI",
    "AJ",
    "AK",
    "AL",
    "AM",
    "AN",
    "AO",
    "AP",
}

DEFAULT_START_YEAR = 2000
DEFAULT_END_YEAR = 2019


@dataclass(frozen=True)
class FieldPartRule:
    scale: float | None = None
    missing_values: set[str] | None = None
    quality_part: int | None = None
    allowed_quality: set[str] | None = None
    allowed_values: set[str] | None = None
    allowed_pattern: re.Pattern[str] | None = None
    min_value: float | None = None
    max_value: float | None = None
    kind: str = "numeric"
    agg: str = "mean"  # mean | max | min | mode | sum | drop | circular_mean
    token_width: int | None = None  # Expected fixed width for token validation (A4)
    token_pattern: re.Pattern[str] | None = None  # Token format pattern (A4)


@dataclass(frozen=True)
class FieldRule:
    code: str
    parts: dict[int, FieldPartRule]


@dataclass(frozen=True)
class FieldRegistryEntry:
    code: str
    part: int
    internal_name: str
    name: str
    kind: str
    scale: float | None
    missing_values: set[str] | None
    quality_part: int | None
    agg: str


EQD_REASON_RULE = FieldRule(
    code="EQD",
    parts={
        1: FieldPartRule(kind="categorical", agg="drop", missing_values={"__none__"}),
        2: FieldPartRule(
            kind="categorical",
            agg="drop",
            allowed_values=EQD_REASON_CODES,
            token_width=1,
        ),
        3: FieldPartRule(kind="categorical", agg="drop", missing_values={"__none__"}),
    },
)

EQD_UNIT_RULE = FieldRule(
    code="EQD",
    parts={
        1: FieldPartRule(kind="categorical", agg="drop", missing_values={"__none__"}),
        2: FieldPartRule(
            kind="categorical",
            agg="drop",
            allowed_values=EQD_UNIT_CODES,
            token_width=1,
        ),
        3: FieldPartRule(kind="categorical", agg="drop", missing_values={"__none__"}),
    },
)

# ============================================================================
# QC Signal Constants (Phase 5: Numeric Range Validation & QC Signal Derivation)
# ============================================================================
# These constants drive the emission of __qc_pass, __qc_status, __qc_reason columns
# in clean_noaa_dataframe() and _expand_parsed(). They standardize QC signal outputs
# across all numeric fields and enable row-level usability metrics.
#
# Scope: Initial rollout covers OC1 (wind gust), MA1 (station pressure), GE1/GF1/GG
# (cloud heights/coverage), GH1 (solar radiation), and KA/KB (temperatures), with
# planned expansion to all FieldPartRule-governed numeric fields.
#
# QC Status Values (2-tier, per _compute_qc_signals):
QC_STATUS_VALUES = frozenset({"PASS", "INVALID", "MISSING"})
#   - PASS: All validation checks passed (quality flag OK, not sentinel, in range)
#   - MISSING: Intentional absence (data collected but sentinel value indicates no measurement)
#   - INVALID: Data quality issues (bad quality code, out of range, malformed format)
#
# QC Reason Codes (failures only, None if PASS):
QC_REASON_ENUM = frozenset(
    {"OUT_OF_RANGE", "BAD_QUALITY_CODE", "SENTINEL_MISSING", "MALFORMED_TOKEN", None}
)
#   - OUT_OF_RANGE: Numeric value outside [min_value, max_value] from FieldPartRule
#   - BAD_QUALITY_CODE: Quality flag not in allowed_quality set
#   - SENTINEL_MISSING: Value matched missing_values sentinel (e.g., 9999 for OC1)
#   - MALFORMED_TOKEN: Token width or format validation failed (A4 check)
#
# Row-level Usability Summary Indicators:
# Any field ending with __qc_pass is auto-detected and counted in row summaries:
#   - row_has_any_usable_metric: Boolean - at least one *__qc_pass is True
#   - usable_metric_count: Integer - count of True *__qc_pass values
#   - usable_metric_fraction: Float [0, 1] - usable_metric_count / total *__qc_pass columns
USABILITY_METRIC_INDICATORS = ["qc_pass"]

# NOAA-documented decoded maxima for the mandatory CIG/VIS value fields.
# ISD documents ceiling height as capped at 22000 ("Unlimited = 22000") and
# visibility distance as capped at 160000 ("Values greater than 160000 are
# entered as 160000"). The cleaner preserves that published interpretation in
# decoded public output rather than treating larger encoded values as ordinary
# unconstrained observations.
CIG_PUBLIC_OUTPUT_MAX_M = 22000.0
VIS_PUBLIC_OUTPUT_MAX_M = 160000.0


# Field rules below encode representative NOAA token structure: part arity,
# sentinel values, scales, quality-code parts, and fixed-width checks. The
# mandatory observation groups (`WND`, `CIG`, `VIS`, `TMP`, `DEW`, `SLP`) are
# derived from the NOAA ISD mandatory data section in checked-in source docs:
# `spec_sources/isd-format-document-parts/part-03-mandatory-data-section.md`.
FIELD_RULES: dict[str, FieldRule] = {
    "CONTROL_POS_1_4": FieldRule(
        code="CONTROL_POS_1_4",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                min_value=0,
                max_value=9999,
                token_width=4,
                allowed_pattern=re.compile(r"^\d{4}$"),
            )
        },
    ),
    "CONTROL_POS_5_10": FieldRule(
        code="CONTROL_POS_5_10",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                token_width=6,
                allowed_pattern=re.compile(r"^[\x20-\x7E]{6}$"),
            )
        },
    ),
    "CONTROL_POS_11_15": FieldRule(
        code="CONTROL_POS_11_15",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                min_value=0,
                max_value=99999,
                token_width=5,
                allowed_pattern=re.compile(r"^\d{5}$"),
            )
        },
    ),
    "CONTROL_POS_16_23": FieldRule(
        code="CONTROL_POS_16_23",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                min_value=101,
                max_value=99991231,
                token_width=8,
                allowed_pattern=re.compile(r"^\d{8}$"),
            )
        },
    ),
    "CONTROL_POS_24_27": FieldRule(
        code="CONTROL_POS_24_27",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                min_value=0,
                max_value=2359,
                token_width=4,
                allowed_pattern=HHMM_PATTERN,
            )
        },
    ),
    "CONTROL_POS_28_28": FieldRule(
        code="CONTROL_POS_28_28",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values=DATA_SOURCE_FLAGS,
                token_width=1,
                token_pattern=re.compile(r"^[1-9A-O]$"),
            )
        },
    ),
    "CONTROL_POS_29_34": FieldRule(
        code="CONTROL_POS_29_34",
        parts={
            1: FieldPartRule(
                kind="numeric",
                agg="drop",
                missing_values={"99999"},
                min_value=-90000,
                max_value=90000,
                token_width=6,
                token_pattern=re.compile(r"^[+-]?\d{5}$"),
            )
        },
    ),
    "CONTROL_POS_35_41": FieldRule(
        code="CONTROL_POS_35_41",
        parts={
            1: FieldPartRule(
                kind="numeric",
                agg="drop",
                missing_values={"999999"},
                min_value=-179999,
                max_value=180000,
                token_width=7,
                token_pattern=re.compile(r"^[+-]?\d{6}$"),
            )
        },
    ),
    "CONTROL_POS_42_46": FieldRule(
        code="CONTROL_POS_42_46",
        parts={
            1: FieldPartRule(
                kind="numeric",
                agg="drop",
                missing_values={"9999"},
                min_value=-400,
                max_value=8850,
                token_width=5,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            )
        },
    ),
    "CONTROL_POS_47_51": FieldRule(
        code="CONTROL_POS_47_51",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99999"},
                allowed_values=REPORT_TYPE_CODES,
                token_width=5,
                token_pattern=re.compile(r"^[A-Z0-9-]{5}$"),
            )
        },
    ),
    "CONTROL_POS_52_56": FieldRule(
        code="CONTROL_POS_52_56",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99999"},
                token_width=5,
                allowed_pattern=re.compile(r"^[\x20-\x7E]{5}$"),
            )
        },
    ),
    "CONTROL_POS_57_60": FieldRule(
        code="CONTROL_POS_57_60",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_values={"V01 ", "V02 ", "V03 "},
                token_width=4,
                token_pattern=re.compile(r"^(?:V0[1-3]\s|9999)$"),
            )
        },
    ),
    "DATE": FieldRule(
        code="DATE",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                min_value=101,
                max_value=99991231,
                token_width=8,
                allowed_pattern=re.compile(r"^\d{8}$"),
            )
        },
    ),
    "TIME": FieldRule(
        code="TIME",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                min_value=0,
                max_value=2359,
                token_width=4,
                allowed_pattern=HHMM_PATTERN,
            )
        },
    ),
    "LATITUDE": FieldRule(
        code="LATITUDE",
        parts={
            1: FieldPartRule(
                kind="numeric",
                agg="drop",
                missing_values={"99999"},
                min_value=-90000,
                max_value=90000,
                token_width=6,
                token_pattern=re.compile(r"^[+-]?\d{5}$"),
            )
        },
    ),
    "LONGITUDE": FieldRule(
        code="LONGITUDE",
        parts={
            1: FieldPartRule(
                kind="numeric",
                agg="drop",
                missing_values={"999999"},
                min_value=-179999,
                max_value=180000,
                token_width=7,
                token_pattern=re.compile(r"^[+-]?\d{6}$"),
            )
        },
    ),
    "REPORT_TYPE": FieldRule(
        code="REPORT_TYPE",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99999"},
                allowed_values=REPORT_TYPE_CODES,
                token_width=5,
                token_pattern=re.compile(r"^[A-Z0-9-]{5}$"),
            )
        },
    ),
    "ELEVATION": FieldRule(
        code="ELEVATION",
        parts={
            1: FieldPartRule(
                kind="numeric",
                agg="drop",
                missing_values={"9999"},
                min_value=-400,
                max_value=8850,
                token_width=5,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            )
        },
    ),
    "CALL_SIGN": FieldRule(
        code="CALL_SIGN",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99999"},
                token_width=5,
                token_pattern=re.compile(r"^[A-Z0-9]{5}$"),
            )
        },
    ),
    "QC_PROCESS": FieldRule(
        code="QC_PROCESS",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                allowed_values=QC_PROCESS_CODES,
                token_width=3,
                token_pattern=re.compile(r"^V0[1-3]$"),
            )
        },
    ),
    "WND": FieldRule(
        code="WND",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                quality_part=2,
                agg="circular_mean",
                min_value=1,
                max_value=360,
                token_width=3,  # Wind direction: 3 digits (001-360)
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=MANDATORY_QUALITY_FLAGS,
                token_width=1,  # Direction quality code: 1 char
            ),  # direction quality
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"A", "B", "C", "H", "N", "R", "Q", "T", "V"},
                token_width=1,  # Wind type code: 1 char
            ),  # wind type code
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=900,
                token_width=4,  # Wind speed: 4 digits (0000-0900)
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=MANDATORY_QUALITY_FLAGS,
                token_width=1,  # Speed quality code: 1 char
            ),  # speed quality
        },
    ),
    "CIG": FieldRule(
        code="CIG",
        parts={
            1: FieldPartRule(
                missing_values={"99999"},
                quality_part=2,
                token_width=5,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=MANDATORY_QUALITY_FLAGS,
                token_width=1,
            ),  # height quality
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"A", "B", "C", "D", "E", "M", "P", "R", "S", "U", "V", "W"},
                token_width=1,
            ),  # determination code
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"N", "Y"},
                token_width=1,
            ),  # CAVOK code
        },
    ),
    "VIS": FieldRule(
        code="VIS",
        parts={
            1: FieldPartRule(
                missing_values={"999999"},
                quality_part=2,
                agg="min",
                token_width=6,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=MANDATORY_QUALITY_FLAGS,
                token_width=1,
            ),  # distance quality
            3: FieldPartRule(
                quality_part=4,
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"N", "V"},
                token_width=1,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=MANDATORY_QUALITY_FLAGS,
                token_width=1,
            ),  # variability quality
        },
    ),
    # TMP/DEW are NOAA air-temperature composite fields: value plus quality
    # code. The sentinel `9999` and tenths-degree scale come from the checked-in
    # ISD mandatory data documentation; QC code semantics are preserved rather
    # than collapsed into a boolean.
    "TMP": FieldRule(
        code="TMP",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                allowed_quality=QUALITY_FLAGS,
                min_value=-932,
                max_value=618,
                token_width=4,  # Temperature: 4 digits after sign (+/-NNNN)
            )
        },
    ),
    "DEW": FieldRule(
        code="DEW",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                allowed_quality=QUALITY_FLAGS,
                min_value=-982,
                max_value=368,
                token_width=4,  # Dew point: 4 digits after sign (+/-NNNN)
            )
        },
    ),
    "SLP": FieldRule(
        code="SLP",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                min_value=8600,
                max_value=10900,
                token_width=5,  # Sea level pressure: 5 digits (08600-10900)
            )
        },
    ),
    # Supplemental field families below are representative parser rules from
    # checked-in NOAA ISD part docs (additional data, cloud/solar, temperature,
    # pressure, and related sections). They retain each field's value,
    # condition, and quality parts and expose validation sidecars in output.
    "OC1": FieldRule(
        code="OC1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                agg="max",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                min_value=50,
                max_value=1100,
                token_width=4,
            )
        },
    ),
    "MA1": FieldRule(
        code="MA1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=8635,
                max_value=10904,
                token_width=5,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # altimeter quality
            3: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=4,
                min_value=4500,
                max_value=10900,
                token_width=5,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # station pressure quality
        },
    ),
    "MD1": FieldRule(
        code="MD1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                quality_part=2,
                missing_values={"9"},
                allowed_values=PRESSURE_TENDENCY_CODES - {"9"},
                token_width=1,
            ),  # pressure tendency code
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # tendency quality
            3: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=4,
                min_value=0,
                max_value=500,
                token_width=3,
                token_pattern=re.compile(r"^\d{3}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # 3-hr pressure quality
            5: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=6,
                min_value=-800,
                max_value=800,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # 24-hr pressure quality
        },
    ),
    "SA1": FieldRule(
        code="SA1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=2,
                allowed_quality={"0", "1", "2", "3", "9"},
                min_value=-50,
                max_value=450,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            )
        },
    ),
    "UA1": FieldRule(
        code="UA1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=4,
                allowed_values={"M", "I"},
                token_width=1,
            ),  # method code
            2: FieldPartRule(
                missing_values={"99"},
                quality_part=4,
                allowed_values={f"{value:02d}" for value in range(0, 31)},
                min_value=0,
                max_value=30,
                token_width=2,
            ),  # wave period (seconds)
            3: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=4,
                allowed_values={f"{value:03d}" for value in range(0, 501)},
                min_value=0,
                max_value=500,
                token_width=3,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # wave height quality
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=6,
                allowed_values={f"{value:02d}" for value in range(0, 10)},
                token_width=2,
            ),  # sea state code
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # sea state quality
        },
    ),
    "WA1": FieldRule(
        code="WA1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=4,
                allowed_values={"1", "2", "3", "4", "5"},
                token_width=1,
            ),  # source code
            2: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=4,
                allowed_values={f"{value:03d}" for value in range(0, 999)},
                token_width=3,
            ),  # thickness cm
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=4,
                allowed_values={"0", "1", "2", "3", "4"},
                token_width=1,
            ),  # tendency code
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # quality code
        },
    ),
    "WD1": FieldRule(
        code="WD1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=11,
                allowed_values={f"{value:02d}" for value in range(0, 11)},
                token_width=2,
            ),
            2: FieldPartRule(
                missing_values={"999"},
                quality_part=11,
                allowed_values={f"{value:03d}" for value in range(0, 101)},
                token_width=3,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=11,
                allowed_values={"06", "07", "08", "09"},
                token_width=2,
            ),
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=11,
                allowed_values={"0", "1", "2"},
                token_width=1,
            ),
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=11,
                allowed_values={"1", "2", "3"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=11,
                allowed_values={"1", "2", "3", "4", "5", "6"},
                token_width=1,
            ),
            7: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=11,
                allowed_values={f"{value:02d}" for value in range(0, 10)},
                token_width=2,
            ),
            8: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=11,
                allowed_values={"0", "1", "2"},
                token_width=1,
            ),
            9: FieldPartRule(
                missing_values={"999"},
                quality_part=11,
                allowed_values={f"{value:03d}" for value in range(0, 999)},
                token_width=3,
            ),
            10: FieldPartRule(
                missing_values={"999"},
                quality_part=11,
                allowed_values={f"{value:03d}" for value in range(0, 999)},
                token_width=3,
            ),
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "WG1": FieldRule(
        code="WG1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=6,
                allowed_values={f"{value:02d}" for value in range(0, 11)},
                token_width=2,
            ),
            2: FieldPartRule(
                missing_values={"99"},
                agg="drop",
                quality_part=6,
                allowed_values={f"{value:02d}" for value in range(0, 99)},
                token_width=2,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=6,
                allowed_values={f"{value:02d}" for value in range(0, 10)},
                token_width=2,
            ),
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=6,
                allowed_values={f"{value:02d}" for value in range(0, 10)},
                token_width=2,
            ),
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=6,
                allowed_values={f"{value:02d}" for value in range(0, 10)},
                token_width=2,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "WJ1": FieldRule(
        code="WJ1",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                allowed_values={f"{value:03d}" for value in range(0, 999)},
                token_width=3,
            ),
            2: FieldPartRule(
                missing_values={"99999"},
                allowed_values={f"{value:05d}" for value in range(0, 99999)},
                token_width=5,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={
                    f"{value:02d}" for value in (list(range(0, 5))
                    + list(range(10, 13))
                    + list(range(20, 30))
                    + list(range(30, 38))
                    + list(range(40, 48))
                    + list(range(50, 60))
                    + list(range(60, 66))
                    + list(range(70, 74)))
                },
                token_width=2,
            ),
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={
                    f"{value:02d}" for value in (list(range(0, 5))
                    + list(range(10, 13))
                    + list(range(20, 30))
                    + list(range(30, 38))
                    + list(range(40, 48))
                    + list(range(50, 60))
                    + list(range(60, 66))
                    + list(range(70, 74)))
                },
                token_width=2,
            ),
            5: FieldPartRule(
                missing_values={"9999"},
                allowed_values={
                    f"{value:04d}" for value in range(0, 9999)
                }
                | {f"+{value:04d}" for value in range(0, 9999)}
                | {f"-{value:04d}" for value in range(0, 1000)},
                token_width=4,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"0", "1", "2", "3"},
                token_width=1,
            ),
            7: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"B", "H", "N", "O"},
                token_width=1,
            ),
        },
    ),
    "UG1": FieldRule(
        code="UG1",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                quality_part=4,
                allowed_values={f"{value:02d}" for value in range(0, 15)},
                token_width=2,
            ),  # primary swell period (seconds)
            2: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=4,
                allowed_values={f"{value:03d}" for value in range(0, 501)},
                token_width=3,
            ),
            3: FieldPartRule(
                missing_values={"999"},
                agg="circular_mean",
                quality_part=4,
                allowed_values={f"{value:03d}" for value in range(1, 361)},
                token_width=3,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # swell height quality
        },
    ),
    "UG2": FieldRule(
        code="UG2",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                quality_part=4,
                allowed_values={f"{value:02d}" for value in range(0, 15)},
                token_width=2,
            ),  # secondary swell period (seconds)
            2: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=4,
                allowed_values={f"{value:03d}" for value in range(0, 501)},
                token_width=3,
            ),
            3: FieldPartRule(
                missing_values={"999"},
                agg="circular_mean",
                quality_part=4,
                allowed_values={f"{value:03d}" for value in range(1, 361)},
                token_width=3,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # swell height quality
        },
    ),
    "GE1": FieldRule(
        code="GE1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),  # convective cloud code
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999999"},
                allowed_values=VERTICAL_DATUM_CODES,
            ),  # vertical datum
            # TODO(spec-width): Part 15 documents FLD LEN 6, but observed vertical datum
            # tokens are variable-length enumerations (e.g., AGL, WGS84E). Enforcing an
            # exact fixed width here requires end-to-end preservation/padding of raw tokens.
            3: FieldPartRule(
                missing_values={"99999"},
                min_value=-400,
                max_value=15000,
                token_width=5,
            ),  # base height upper range
            4: FieldPartRule(
                missing_values={"99999"},
                min_value=-400,
                max_value=15000,
                token_width=5,
            ),  # base height lower range
        },
    ),
    "GF1": FieldRule(
        code="GF1",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                quality_part=3,
                agg="mean",
                allowed_values=SKY_COVER_EXTENDED_CODES,
                token_width=2,
            ),
            2: FieldPartRule(
                missing_values={"99"},
                agg="mean",
                allowed_values=SKY_COVER_OPAQUE_CODES,
                token_width=2,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # total coverage quality
            4: FieldPartRule(
                missing_values={"99"},
                quality_part=5,
                agg="mean",
                allowed_values=SKY_COVER_EXTENDED_CODES,
                token_width=2,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # lowest cloud cover quality
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values=CLOUD_GENUS_CODES,
                token_width=2,
            ),  # low cloud genus
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # low cloud genus quality
            8: FieldPartRule(
                missing_values={"99999"},
                quality_part=9,
                min_value=-400,
                max_value=15000,
                token_width=5,
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # lowest base height quality
            10: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values=CLOUD_GENUS_CODES,
                token_width=2,
            ),  # mid cloud genus
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # mid cloud genus quality
            12: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values=CLOUD_GENUS_CODES,
                token_width=2,
            ),  # high cloud genus
            13: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # high cloud genus quality
        },
    ),
    "CO1": FieldRule(
        code="CO1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={f"{value:02d}" for value in range(0, 10)} | {"99"},
                min_value=0,
                max_value=9,
                token_width=2,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={
                    f"{value:02d}" for value in range(0, 13)
                }
                | {f"+{value:02d}" for value in range(0, 13)}
                | {f"-{value:02d}" for value in range(0, 13)},
                token_width=3,
                token_pattern=re.compile(r"^[+-]\d{2}$"),
            ),
        },
    ),
}

FIELD_RULE_PREFIXES: dict[str, FieldRule] = {
    # AA1-AA4: repeated liquid-precipitation fields documented in the NOAA ISD
    # additional data section. Repeated suffixes are intentionally preserved in
    # public names such as `precip_amount_1` and `precip_quality_code_1`.
    "AA": FieldRule(
        code="AA*",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                agg="drop",
                min_value=0,
                max_value=98,
                token_width=2,
            ),  # period hours
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=4,
                agg="sum",
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4", "5", "6", "7", "8", "9", "E", "I", "J"},
                token_width=1,
            ),  # condition code
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AB": FieldRule(
        code="AB*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=3,
                min_value=0,
                max_value=50000,
                token_width=5,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                token_width=1,
            ),  # condition code
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AC": FieldRule(
        code="AC*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"0", "1", "2", "3"},
                quality_part=3,
                token_width=1,
            ),  # duration code
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"C", "I"},
                quality_part=3,
                token_width=1,
            ),  # characteristic code
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AD": FieldRule(
        code="AD*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=6,
                min_value=0,
                max_value=20000,
                token_width=5,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                token_width=1,
            ),  # condition code
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_pattern=DAY_PAIR_PATTERN,
                min_value=101,
                max_value=3131,
                token_width=4,
            ),  # date 1
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_pattern=DAY_PAIR_PATTERN,
                min_value=101,
                max_value=3131,
                token_width=4,
            ),  # date 2
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_pattern=DAY_PAIR_PATTERN,
                min_value=101,
                max_value=3131,
                token_width=4,
            ),  # date 3
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AE": FieldRule(
        code="AE*",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                quality_part=2,
                min_value=0,
                max_value=31,
                token_width=2,
            ),  # days >= .01
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),
            3: FieldPartRule(
                missing_values={"99"},
                quality_part=4,
                min_value=0,
                max_value=31,
                token_width=2,
            ),  # days >= .10
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),
            5: FieldPartRule(
                missing_values={"99"},
                quality_part=6,
                min_value=0,
                max_value=31,
                token_width=2,
            ),  # days >= .50
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),
            7: FieldPartRule(
                missing_values={"99"},
                quality_part=8,
                min_value=0,
                max_value=31,
                token_width=2,
            ),  # days >= 1.00
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),
        },
    ),
    "AG": FieldRule(
        code="AG*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"0", "1", "2", "3", "4", "5"},
                token_width=1,
            ),  # discrepancy code
            2: FieldPartRule(
                missing_values={"999"},
                min_value=0,
                max_value=998,
                token_width=3,
            ),  # estimated depth mm
        },
    ),
    "AH": FieldRule(
        code="AH*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                min_value=5,
                max_value=45,
                token_width=3,
            ),  # period minutes
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=3000,
                token_width=4,
            ),  # depth mm
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2"},
                token_width=1,
            ),  # condition code
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999999"},
                allowed_pattern=DDHHMM_PATTERN,
                token_width=6,
            ),  # end date-time
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AI": FieldRule(
        code="AI*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                min_value=60,
                max_value=180,
                token_width=3,
            ),  # period minutes
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=3000,
                token_width=4,
            ),  # depth mm
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2"},
                token_width=1,
            ),  # condition code
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999999"},
                allowed_pattern=DDHHMM_PATTERN,
                token_width=6,
            ),  # end date-time
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AK": FieldRule(
        code="AK1",
        parts={
            1: FieldPartRule(
                missing_values={"9999"},
                quality_part=4,
                min_value=0,
                max_value=1500,
                token_width=4,
            ),  # depth cm
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4"},
                token_width=1,
            ),  # condition code
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999999"},
                allowed_pattern=DAY_PAIR_TRIPLE_PATTERN,
                token_width=6,
            ),  # dates of occurrence
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AL": FieldRule(
        code="AL*",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                agg="drop",
                min_value=0,
                max_value=72,
                token_width=2,
            ),  # period hours
            2: FieldPartRule(
                missing_values={"999"},
                quality_part=4,
                agg="sum",
                min_value=0,
                max_value=500,
                token_width=3,
            ),  # depth cm
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4", "5", "6", "E"},
                token_width=1,
            ),  # condition code
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AM": FieldRule(
        code="AM1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=6,
                min_value=0,
                max_value=2000,
                token_width=4,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4"},
                token_width=1,
            ),  # condition code
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_pattern=DAY_PAIR_PATTERN,
                token_width=4,
            ),
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_pattern=DAY_PAIR_PATTERN,
                token_width=4,
            ),
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_pattern=DAY_PAIR_PATTERN,
                token_width=4,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AN": FieldRule(
        code="AN1",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                min_value=1,
                max_value=744,
                token_width=3,
            ),  # period hours
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=4,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4", "5", "6", "7", "E"},
                token_width=1,
            ),  # condition code
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AO": FieldRule(
        code="AO*",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                agg="drop",
                min_value=0,
                max_value=98,
                token_width=2,
            ),  # period minutes
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=4,
                agg="sum",
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4", "5", "6", "7", "8", "E", "I", "J"},
                token_width=1,
            ),  # condition code
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AP": FieldRule(
        code="AP*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=3,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"9"},
                token_width=1,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "AJ": FieldRule(
        code="AJ*",
        parts={
            1: FieldPartRule(
                missing_values={"9999"},
                quality_part=3,
                min_value=0,
                max_value=1200,
                token_width=4,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                token_width=1,
            ),  # snow depth condition
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # snow depth quality
            4: FieldPartRule(
                scale=0.1,
                missing_values={"999999"},
                quality_part=6,
                min_value=0,
                max_value=120000,
                token_width=6,
            ),
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                token_width=1,
            ),  # equiv water condition
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=QUALITY_FLAGS - {"C"},
                token_width=1,
            ),  # equiv water quality
        },
    ),
    "AT": FieldRule(
        code="AT*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                quality_part=4,
                allowed_values=DAILY_PRESENT_WEATHER_SOURCE_CODES,
                token_width=2,
            ),  # source element
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                quality_part=4,
                allowed_values=DAILY_PRESENT_WEATHER_TYPE_CODES,
                token_width=2,
            ),  # daily present weather type
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                quality_part=4,
                allowed_values=DAILY_PRESENT_WEATHER_ABBREVIATIONS,
                token_width=4,
            ),  # daily present weather abbreviation
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AU": FieldRule(
        code="AU*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=7,
                allowed_values={"0", "1", "2", "3", "4"},
                token_width=1,
            ),  # intensity
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=7,
                allowed_values={"0", "1", "2", "3", "4", "5", "6", "7", "8"},
                token_width=1,
            ),  # descriptor
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=7,
                allowed_values=PRESENT_WEATHER_COMPONENT_PRECIPITATION_CODES - {"99"},
                token_width=2,
            ),  # precip code
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=7,
                allowed_values={"0", "1", "2", "3", "4", "5", "6", "7", "8"},
                token_width=1,
            ),  # obscuration
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=7,
                allowed_values={"0", "1", "2", "3", "4", "5"},
                token_width=1,
            ),  # other phenomena
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=7,
                allowed_values={"1", "2", "3"},
                token_width=1,
            ),  # combo indicator
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # quality code
        },
    ),
    "AW": FieldRule(
        code="AW*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values=set(),
                quality_part=2,
                allowed_values=AUTOMATED_PRESENT_WEATHER_CODES,
                token_width=2,
            ),  # automated atmospheric condition code
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # automated condition quality
        },
    ),
    "CB": FieldRule(
        code="CB*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={f"{value:02d}" for value in range(5, 61)},
                token_width=2,
            ),
            2: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=3,
                min_value=-99999,
                max_value=99998,
                token_width=5,
            ),
            3: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CF": FieldRule(
        code="CF*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CG": FieldRule(
        code="CG*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=-99999,
                max_value=99998,
                token_width=5,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CH": FieldRule(
        code="CH*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={f"{value:02d}" for value in range(0, 61)},
                token_width=2,
            ),
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=3,
                min_value=-9999,
                max_value=9998,
                token_width=5,
            ),
            3: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            5: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=6,
                min_value=0,
                max_value=1000,
                token_width=4,
            ),
            6: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CI": FieldRule(
        code="CI*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=-9999,
                max_value=9998,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
            7: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=8,
                min_value=0,
                max_value=9998,
            ),
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
            10: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=11,
                min_value=0,
                max_value=1000,
                token_width=5,
                allowed_pattern=re.compile(r"^\d{5}$"),
            ),
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
            ),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
        },
    ),
    "CO": FieldRule(
        code="CO*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999"},
                allowed_pattern=re.compile(r"^[\x20-\x7E]{3}$"),
                token_width=3,
            ),
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                allowed_values={f"{value:04d}" for value in range(0, 9999)}
                | {f"+{value:04d}" for value in range(0, 9999)}
                | {f"-{value:04d}" for value in range(0, 10000)},
                token_width=4,
                token_pattern=re.compile(r"^[+-]\d{4}$"),
            ),
        },
    ),
    "CT": FieldRule(
        code="CT*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^[+-]\d{4}$"),
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
        },
    ),
    "CU": FieldRule(
        code="CU*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^[+-]\d{4}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CV": FieldRule(
        code="CV*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^[+-]\d{4}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                quality_part=5,
                allowed_values={f"{value:02d}{minute:02d}" for value in range(0, 24) for minute in range(0, 60)},
                allowed_pattern=HHMM_PATTERN,
                token_width=4,
                token_pattern=HHMM_PATTERN,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=8,
                min_value=-9999,
                max_value=9999,
                token_width=4,
                token_pattern=re.compile(r"^[+-]\d{4}$"),
            ),
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            10: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                quality_part=11,
                allowed_values={f"{value:02d}{minute:02d}" for value in range(0, 24) for minute in range(0, 60)},
                allowed_pattern=HHMM_PATTERN,
                token_width=4,
                token_pattern=HHMM_PATTERN,
            ),
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CW": FieldRule(
        code="CW*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=0,
                max_value=99999,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=5,
                min_value=0,
                max_value=99999,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CX": FieldRule(
        code="CX*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=-99999,
                max_value=99999,
                token_width=5,
                token_pattern=re.compile(r"^[+-]\d{5}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=9999,
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                missing_values={"9999"},
                quality_part=8,
                min_value=0,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            10: FieldPartRule(
                missing_values={"9999"},
                quality_part=11,
                min_value=0,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    # GA1-GA6: repeated cloud-layer fields. Rules here preserve layer index,
    # value fields, and quality-code parts for reviewer spot-checking against
    # the NOAA additional data/cloud documentation in `spec_sources/`.
    "GA": FieldRule(
        code="GA*",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                quality_part=2,
                agg="mean",
                allowed_values=SKY_COVER_LAYER_CODES,
                min_value=0,
                max_value=100,
                token_width=2,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # coverage quality
            3: FieldPartRule(
                missing_values={"99999"},
                quality_part=4,
                min_value=-400,
                max_value=35000,
                token_width=5,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # base height quality
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=6,
                allowed_values=SKY_COVER_LAYER_TYPE_CODES,
                token_width=2,
            ),  # cloud type
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),  # cloud type quality
        },
    ),
    "GD": FieldRule(
        code="GD*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                quality_part=3,
                allowed_values=SKY_COVER_SUMMATION_CODES,
                token_width=1,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=3,
                allowed_values=SKY_COVER_EXTENDED_CODES,
                token_width=2,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_SUMMATION_QC_FLAGS,
                token_width=1,
            ),
            4: FieldPartRule(
                missing_values={"99999"},
                quality_part=5,
                min_value=-400,
                max_value=35000,
                token_width=5,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_SUMMATION_QC_FLAGS,
                token_width=1,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values=SKY_COVER_SUMMATION_CHARACTERISTICS,
                token_width=1,
            ),
        },
    ),
    "GG": FieldRule(
        code="GG*",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                quality_part=2,
                agg="mean",
                allowed_values=SKY_COVER_LAYER_CODES,
                min_value=0,
                max_value=100,
                token_width=2,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                missing_values={"99999"},
                quality_part=4,
                min_value=0,
                max_value=35000,
                token_width=5,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=6,
                allowed_values=BELOW_STATION_LAYER_TYPE_CODES,
                token_width=2,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=8,
                allowed_values=BELOW_STATION_LAYER_TOP_CODES,
                token_width=2,
            ),
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    # KA1-KA4: repeated extreme-temperature fields. Values are scaled to
    # degrees C and NOAA quality codes remain explicit in `*_quality_code`
    # columns.
    "KA": FieldRule(
        code="KA*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                min_value=1,
                max_value=480,
                token_width=3,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"N", "M", "O", "P"},
                token_width=1,
            ),
            3: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=4,
                min_value=-932,
                max_value=618,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # temperature quality
        },
    ),
    "KB": FieldRule(
        code="KB*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                min_value=1,
                max_value=744,
                token_width=3,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"A", "M", "N"},
                token_width=1,
            ),
            3: FieldPartRule(
                scale=0.01,
                missing_values={"9999"},
                quality_part=4,
                min_value=-9900,
                max_value=6300,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "KC": FieldRule(
        code="KC*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"N", "M"},
                token_width=1,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1"},
                token_width=1,
            ),
            3: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=-1100,
                max_value=630,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999999"},
                allowed_pattern=DAY_PAIR_TRIPLE_PATTERN,
                token_width=6,
                token_pattern=DAY_PAIR_TRIPLE_PATTERN,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
        },
    ),
    "KD": FieldRule(
        code="KD*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                min_value=1,
                max_value=744,
                token_width=3,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"H", "C"},
                token_width=1,
            ),
            3: FieldPartRule(
                missing_values={"9999"},
                quality_part=4,
                min_value=0,
                max_value=5000,
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "KE1": FieldRule(
        code="KE1",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                quality_part=2,
                min_value=0,
                max_value=31,
                token_width=2,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                missing_values={"99"},
                quality_part=4,
                min_value=0,
                max_value=31,
                token_width=2,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
            5: FieldPartRule(
                missing_values={"99"},
                quality_part=6,
                min_value=0,
                max_value=31,
                token_width=2,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                missing_values={"99"},
                quality_part=8,
                min_value=0,
                max_value=31,
                token_width=2,
            ),
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "KF1": FieldRule(
        code="KF1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "KG": FieldRule(
        code="KG*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                min_value=1,
                max_value=744,
                token_width=3,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"D", "W"},
                token_width=1,
            ),
            3: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=-9900,
                max_value=6300,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"D"},
                token_width=1,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "ST1": FieldRule(
        code="ST1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4"},
                min_value=1,
                max_value=9,
                token_width=1,
            ),
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=3,
                min_value=-1100,
                max_value=630,
                token_width=4,
                token_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=9998,
                allowed_pattern=re.compile(r"^\d{4}$"),
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={"01", "02", "03", "04", "05", "06", "07", "08"},
                min_value=1,
                max_value=99,
                token_width=2,
            ),
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
            8: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"0", "1", "2", "3", "4", "5", "6", "7", "8"},
                min_value=0,
                max_value=9,
                token_width=1,
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "ME1": FieldRule(
        code="ME1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values=GEOPOTENTIAL_ISOBARIC_LEVEL_CODES - {"9"},
                token_width=1,
            ),
            2: FieldPartRule(
                missing_values={"9999"},
                quality_part=3,
                min_value=0,
                max_value=9998,
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "MF1": FieldRule(
        code="MF1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=4500,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=4,
                min_value=8600,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "MG1": FieldRule(
        code="MG1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=4500,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
            3: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=4,
                min_value=8600,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
        },
    ),
    "MH1": FieldRule(
        code="MH1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=4500,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
            3: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=4,
                min_value=8600,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
        },
    ),
    "MK1": FieldRule(
        code="MK1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=3,
                min_value=8600,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999999"},
                allowed_pattern=DDHHMM_PATTERN,
                token_width=6,
                token_pattern=DDHHMM_PATTERN,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=6,
                min_value=8600,
                max_value=10900,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            5: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"999999"},
                allowed_pattern=DDHHMM_PATTERN,
                token_width=6,
                token_pattern=DDHHMM_PATTERN,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
        },
    ),
    "GH": FieldRule(
        code="GH*",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=2,
                min_value=0,
                max_value=99998,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLARAD_QC_FLAGS,
                token_width=1,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                allowed_values={str(value) for value in range(0, 10)},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=5,
                min_value=0,
                max_value=99998,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLARAD_QC_FLAGS,
                token_width=1,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                allowed_values={str(value) for value in range(0, 10)},
                token_width=1,
            ),
            7: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=8,
                min_value=0,
                max_value=99998,
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLARAD_QC_FLAGS,
                token_width=1,
            ),
            9: FieldPartRule(
                kind="categorical",
                agg="drop",
                allowed_values={str(value) for value in range(0, 10)},
                token_width=1,
            ),
            10: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=11,
                min_value=0,
                max_value=99998,
                token_width=5,
                allowed_pattern=re.compile(r"^\d{5}$"),
            ),
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLARAD_QC_FLAGS,
                token_width=1,
            ),
            12: FieldPartRule(
                kind="categorical",
                agg="drop",
                allowed_values={str(value) for value in range(0, 10)},
                token_width=1,
            ),
        },
    ),
    "GJ": FieldRule(
        code="GJ*",
        parts={
            1: FieldPartRule(
                missing_values={"9999"},
                quality_part=2,
                min_value=0,
                max_value=6000,
                token_width=4,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_QUALITY_FLAGS,
                token_width=1,
            ),
        },
    ),
    "GK": FieldRule(
        code="GK*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                quality_part=2,
                min_value=0,
                max_value=100,
                token_width=3,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SUNSHINE_PERCENT_QC_FLAGS,
                token_width=1,
            ),
        },
    ),
    "GL": FieldRule(
        code="GL*",
        parts={
            1: FieldPartRule(
                missing_values={"99999"},
                quality_part=2,
                min_value=0,
                max_value=30000,
                token_width=5,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=CLOUD_SUMMATION_QC_FLAGS,
                token_width=1,
            ),
        },
    ),
    "GM": FieldRule(
        code="GM*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_values={f"{value:04d}" for value in range(1, 9999)},
                token_width=4,
            ),
            2: FieldPartRule(
                missing_values={"9999"},
                quality_part=4,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={f"{value:02d}" for value in range(0, 100)},
                token_width=2,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            5: FieldPartRule(
                missing_values={"9999"},
                quality_part=7,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={f"{value:02d}" for value in range(0, 100)},
                token_width=2,
            ),
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            8: FieldPartRule(
                missing_values={"9999"},
                quality_part=10,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            9: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={f"{value:02d}" for value in range(0, 100)},
                token_width=2,
            ),
            10: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            11: FieldPartRule(
                missing_values={"9999"},
                quality_part=12,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
        },
    ),
    "GN": FieldRule(
        code="GN*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_values={f"{value:04d}" for value in range(1, 9999)},
                token_width=4,
            ),
            2: FieldPartRule(
                missing_values={"9999"},
                quality_part=3,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            4: FieldPartRule(
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            6: FieldPartRule(
                missing_values={"9999"},
                quality_part=7,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            8: FieldPartRule(
                missing_values={"9999"},
                quality_part=9,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            10: FieldPartRule(
                missing_values={"999"},
                quality_part=11,
                min_value=0,
                max_value=998,
                token_width=3,
            ),
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
        },
    ),
    "GO": FieldRule(
        code="GO*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_values={f"{value:04d}" for value in range(1, 9999)},
                token_width=4,
            ),
            2: FieldPartRule(
                missing_values={"9999"},
                quality_part=3,
                min_value=-999,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            4: FieldPartRule(
                missing_values={"9999"},
                quality_part=5,
                min_value=-999,
                max_value=9998,
                token_width=4,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
            6: FieldPartRule(
                missing_values={"9999"},
                quality_part=7,
                min_value=-999,
                max_value=9998,
                token_width=4,
            ),
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality=SOLAR_IRRADIANCE_QC_FLAGS,
                token_width=1,
            ),
        },
    ),
    "GP1": FieldRule(
        code="GP1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_values={f"{value:04d}" for value in range(1, 9999)},
                token_width=4,
            ),
            2: FieldPartRule(
                missing_values={"9999"},
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={"01", "02", "03"},
                token_width=2,
            ),
            4: FieldPartRule(
                missing_values={"999"},
                min_value=0,
                max_value=100,
                token_width=3,
            ),
            5: FieldPartRule(
                missing_values={"9999"},
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={"01", "02", "03"},
                token_width=2,
            ),
            7: FieldPartRule(
                missing_values={"999"},
                min_value=0,
                max_value=100,
                token_width=3,
            ),
            8: FieldPartRule(
                missing_values={"9999"},
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            9: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                allowed_values={"01", "02", "03"},
                token_width=2,
            ),
            10: FieldPartRule(
                missing_values={"999"},
                min_value=0,
                max_value=100,
                token_width=3,
            ),
        },
    ),
    "GQ1": FieldRule(
        code="GQ1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_values={f"{value:04d}" for value in range(1, 9999)},
                token_width=4,
            ),
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=3,
                min_value=0,
                max_value=3600,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                missing_values={"9"},
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=3600,
                token_width=4,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                missing_values={"9"},
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "GR1": FieldRule(
        code="GR1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9999"},
                allowed_values={f"{value:04d}" for value in range(1, 9999)},
                token_width=4,
            ),
            2: FieldPartRule(
                missing_values={"9999"},
                quality_part=3,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "HAIL": FieldRule(
        code="HAIL",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=2,
                allowed_quality={"0", "1", "2", "3", "9"},
                min_value=0,
                max_value=200,
                token_width=3,
            )
        },
    ),
    "IA1": FieldRule(
        code="IA1",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=2,
                allowed_values={f"{value:02d}" for value in range(0, 32)},
                token_width=2,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "IA2": FieldRule(
        code="IA2",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=3,
                min_value=1,
                max_value=480,
                token_width=3,
                allowed_pattern=re.compile(r"^\d{3}$"),
            ),
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=3,
                min_value=-1100,
                max_value=1500,
                token_width=4,
                allowed_pattern=re.compile(r"^[+-]?\d{4}$"),
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                allowed_values={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "IB1": FieldRule(
        code="IB1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
                token_width=4,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                missing_values={"9"},
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=-9999,
                max_value=9998,
                token_width=4,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                missing_values={"9"},
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=8,
                min_value=-9999,
                max_value=9998,
                token_width=4,
            ),
            8: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
                token_width=1,
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                missing_values={"9"},
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            10: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=11,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            11: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                allowed_values={"1", "3", "9"},
                token_width=1,
            ),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                missing_values={"9"},
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "IB2": FieldRule(
        code="IB2",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
                token_width=4,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "IC1": FieldRule(
        code="IC1",
        parts={
            1: FieldPartRule(
                missing_values={"99"},
                min_value=1,
                max_value=98,
                token_width=2,
            ),
            2: FieldPartRule(
                missing_values={"9999"},
                quality_part=4,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3"},
                quality_part=4,
                token_width=1,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
            5: FieldPartRule(
                scale=0.01,
                missing_values={"999"},
                quality_part=7,
                min_value=0,
                max_value=998,
                token_width=3,
            ),
            6: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3"},
                quality_part=7,
                token_width=1,
            ),
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
            8: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=10,
                min_value=-100,
                max_value=500,
                token_width=3,
                token_pattern=re.compile(r"^[+-]?\d{3}$"),
            ),
            9: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3"},
                quality_part=10,
                token_width=1,
            ),
            10: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
            11: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=13,
                min_value=-100,
                max_value=500,
                token_width=3,
                token_pattern=re.compile(r"^[+-]?\d{3}$"),
            ),
            12: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3"},
                quality_part=13,
                token_width=1,
            ),
            13: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "OA": FieldRule(
        code="OA*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"1", "2", "3", "4", "5", "6"},
                token_width=1,
            ),
            2: FieldPartRule(
                agg="drop",
                missing_values={"99"},
                allowed_values={f"{value:02d}" for value in range(1, 49)},
                min_value=1,
                max_value=48,
                token_width=2,
            ),
            3: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=4,
                allowed_values={f"{value:04d}" for value in range(0, 2001)},
                min_value=0,
                max_value=2000,
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "OD": FieldRule(
        code="OD*",
        parts={
            1: FieldPartRule(
                missing_values={"9"},
                kind="categorical",
                agg="drop",
                allowed_values={"1", "2", "3", "4", "5", "6"},
                token_width=1,
            ),
            2: FieldPartRule(
                missing_values={"99"},
                agg="drop",
                allowed_values={f"{value:02d}" for value in range(1, 49)},
                min_value=1,
                max_value=48,
                token_width=2,
            ),
            3: FieldPartRule(
                missing_values={"999"},
                agg="circular_mean",
                allowed_values={f"{value:03d}" for value in range(1, 361)},
                min_value=1,
                max_value=360,
                token_width=3,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                allowed_values={f"{value:04d}" for value in range(0, 2001)},
                min_value=0,
                max_value=2000,
                token_width=4,
            ),
            5: FieldPartRule(
                missing_values={"9"},
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "OB": FieldRule(
        code="OB*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                allowed_values={f"{value:03d}" for value in range(1, 999)},
                token_width=3,
                token_pattern=re.compile(r"^\d{3}$"),
            ),  # period minutes
            2: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=3,
                allowed_values={f"{value:04d}" for value in range(0, 9999)},
                token_width=4,
                token_pattern=re.compile(r"^\d{4}$"),
            ),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            5: FieldPartRule(
                missing_values={"999"},
                agg="circular_mean",
                quality_part=6,
                allowed_values={f"{value:03d}" for value in range(1, 361)},
                token_width=3,
                token_pattern=re.compile(r"^\d{3}$"),
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            8: FieldPartRule(
                scale=0.01,
                missing_values={"99999"},
                quality_part=9,
                allowed_values={f"{value:05d}" for value in range(0, 99999)},
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            10: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            11: FieldPartRule(
                scale=0.01,
                missing_values={"99999"},
                quality_part=12,
                allowed_values={f"{value:05d}" for value in range(0, 99999)},
                token_width=5,
                token_pattern=re.compile(r"^\d{5}$"),
            ),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"1", "3", "9"},
                token_width=1,
            ),
            13: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "OE": FieldRule(
        code="OE*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                allowed_values={"1", "2", "3", "4", "5"},
                token_width=1,
            ),  # summary type code
            2: FieldPartRule(
                missing_values={"99"},
                agg="drop",
                allowed_values={"24"},
                min_value=24,
                max_value=24,
                token_width=2,
            ),  # period hours
            3: FieldPartRule(
                scale=0.01,
                missing_values={"99999"},
                quality_part=6,
                allowed_values={f"{value:05d}" for value in range(0, 20001)},
                min_value=0,
                max_value=20000,
                token_width=5,
            ),
            4: FieldPartRule(
                missing_values={"999"},
                agg="circular_mean",
                quality_part=6,
                allowed_values={f"{value:03d}" for value in range(1, 361)},
                min_value=1,
                max_value=360,
                token_width=3,
            ),
            5: FieldPartRule(
                agg="drop",
                missing_values={"9999"},
                quality_part=6,
                allowed_values={f"{value:04d}" for value in range(0, 2360)},
                allowed_pattern=HHMM_PATTERN,
                min_value=0,
                max_value=2359,
                token_width=4,
            ),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),
        },
    ),
    "RH": FieldRule(
        code="RH*",
        parts={
            1: FieldPartRule(
                missing_values={"999"},
                agg="drop",
                min_value=1,
                max_value=744,
                token_width=3,
            ),  # period hours
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"M", "N", "X"},
                token_width=1,
            ),  # relative humidity code
            3: FieldPartRule(
                missing_values={"999"},
                quality_part=5,
                min_value=0,
                max_value=100,
                token_width=3,
            ),  # relative humidity percent
            4: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"D"},
                token_width=1,
            ),  # derived code
            5: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9"},
                token_width=1,
            ),  # quality code
        },
    ),
    "ED1": FieldRule(
        code="ED1",
        parts={
            1: FieldPartRule(
                scale=10.0,
                missing_values={"99"},
                quality_part=4,
                allowed_values={f"{value:02d}" for value in range(1, 37)},
                token_width=2,
            ),
            2: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"L", "C", "R", "U"},
                quality_part=4,
                token_width=1,
            ),
            3: FieldPartRule(
                missing_values={"9999"},
                quality_part=4,
                allowed_values={f"{value:04d}" for value in range(0, 5001)},
                token_width=4,
            ),
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),
        },
    ),
    "MV": FieldRule(
        code="MV*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=2,
                allowed_values=PRESENT_WEATHER_VICINITY_CODES - {"99"},
                token_width=2,
            ),
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),
        },
    ),
    "MW": FieldRule(
        code="MW*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                quality_part=2,
                allowed_values=MANUAL_PRESENT_WEATHER_CODES,
                token_width=2,
            ),  # present-weather code
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "9", "M"},
                token_width=1,
            ),  # present-weather quality
        },
    ),
    "AY": FieldRule(
        code="AY*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                quality_part=2,
                allowed_values=MANUAL_PAST_WEATHER_CODES,
                token_width=1,
            ),  # past-weather condition code
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # past-weather condition quality
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=4,
                allowed_values={f"{value:02d}" for value in range(1, 25)},
                token_width=2,
            ),  # past-weather period
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # past-weather period quality
        },
    ),
    "AX": FieldRule(
        code="AX*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=2,
                allowed_values=SUMMARY_OF_DAY_PAST_WEATHER_CODES - {"99"},
                token_width=2,
            ),  # summary-of-day condition code
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),  # summary-of-day condition quality
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=4,
                allowed_values={"24"},
                token_width=2,
            ),  # summary-of-day period
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"4", "5", "6", "7", "9"},
                token_width=1,
            ),  # summary-of-day period quality
        },
    ),
    "AZ": FieldRule(
        code="AZ*",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                quality_part=2,
                allowed_values=AUTOMATED_PAST_WEATHER_CODES,
                token_width=1,
            ),  # automated past-weather condition code
            2: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # automated past-weather condition quality
            3: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"99"},
                quality_part=4,
                allowed_values={f"{value:02d}" for value in range(1, 25)},
                token_width=2,
            ),  # automated past-weather period
            4: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "9"},
                token_width=1,
            ),  # automated past-weather period quality
        },
    ),
    "CR1": FieldRule(
        code="CR1",
        parts={
            1: FieldPartRule(
                scale=0.001,
                missing_values={"99999"},
                quality_part=2,
                min_value=0,
                max_value=99998,
                token_width=5,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
        },
    ),
    "CI1": FieldRule(
        code="CI1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9999,
                token_width=5,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=-9999,
                max_value=9998,
            ),
            5: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
            7: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=8,
                min_value=0,
                max_value=99998,
            ),
            8: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
            10: FieldPartRule(
                scale=0.1,
                missing_values={"99999"},
                quality_part=11,
                min_value=0,
                max_value=99998,
                token_width=5,
                allowed_pattern=re.compile(r"^\d{5}$"),
            ),
            11: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
            ),
        },
    ),
    "CN1": FieldRule(
        code="CN1",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            5: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=8,
                min_value=0,
                max_value=9998,
                token_width=4,
            ),
            8: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CN2": FieldRule(
        code="CN2",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=2,
                min_value=-9999,
                max_value=9998,
                token_width=4,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"9999"},
                quality_part=5,
                min_value=-9999,
                max_value=9998,
                token_width=4,
            ),
            5: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                missing_values={"99"},
                quality_part=8,
                min_value=0,
                max_value=60,
                token_width=2,
            ),
            8: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CN3": FieldRule(
        code="CN3",
        parts={
            1: FieldPartRule(
                scale=0.1,
                missing_values={"999999"},
                quality_part=2,
                min_value=0,
                max_value=999998,
                token_width=6,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                scale=0.1,
                missing_values={"999999"},
                quality_part=5,
                min_value=0,
                max_value=999998,
                token_width=6,
            ),
            5: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
    "CN4": FieldRule(
        code="CN4",
        parts={
            1: FieldPartRule(
                kind="categorical",
                agg="drop",
                missing_values={"9"},
                allowed_values={"0", "1", "9"},
                quality_part=2,
                token_width=1,
            ),
            2: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            3: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            4: FieldPartRule(
                missing_values={"9999"},
                quality_part=5,
                min_value=0,
                max_value=8192,
                token_width=4,
            ),
            5: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            6: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            7: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=8,
                min_value=0,
                max_value=500,
                token_width=3,
            ),
            8: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            9: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
            10: FieldPartRule(
                scale=0.1,
                missing_values={"999"},
                quality_part=11,
                min_value=0,
                max_value=500,
                token_width=3,
            ),
            11: FieldPartRule(kind="quality", agg="drop", allowed_quality={"1", "3", "9"}, token_width=1),
            12: FieldPartRule(
                kind="quality",
                agg="drop",
                allowed_quality={"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"},
                token_width=1,
            ),
        },
    ),
}

for _prefix in (
    "OA",
    "OD",
    "OB",
    "OE",
    "RH",
    "MV",
    "MW",
    "AY",
    "CI",
    "CO",
    "CT",
    "CU",
    "CV",
    "CW",
    "CX",
    "GH",
    "GJ",
    "GK",
    "GL",
    "GM",
    "GN",
    "GO",
):
    _rule = FIELD_RULES.get(_prefix)
    if _rule is not None:
        FIELD_RULE_PREFIXES[_prefix] = _rule

_EQD_PREFIX_RULES: dict[str, FieldRule] = {}
for _letter in ("Q", "P", "R", "C", "D"):
    _EQD_PREFIX_RULES.update({f"{_letter}{digit}": EQD_REASON_RULE for digit in "0123456789"})
_EQD_PREFIX_RULES.update({f"N{digit}": EQD_UNIT_RULE for digit in "0123456789"})
FIELD_RULE_PREFIXES.update(_EQD_PREFIX_RULES)

# Repeated-identifier families come from NOAA optional/repeated field families.
# This registry keeps parser acceptance legible: e.g., AA1-AA4, GA1-GA6, and
# KA1-KA4 are accepted, while malformed suffixes such as AA01 are rejected.
_REPEATED_IDENTIFIER_RANGES: dict[str, range] = {
    "AA": range(1, 5),
    "AH": range(1, 7),
    "AI": range(1, 7),
    "AL": range(1, 5),
    "AO": range(1, 5),
    "AT": range(1, 9),
    "AU": range(1, 10),
    "AW": range(1, 5),
    "AX": range(1, 7),
    "AY": range(1, 3),
    "AZ": range(1, 3),
    "CO": range(1, 10),
    "CT": range(1, 4),
    "CU": range(1, 4),
    "CV": range(1, 4),
    "CW": range(1, 2),
    "CX": range(1, 4),
    "GA": range(1, 7),
    "GD": range(1, 7),
    "GG": range(1, 7),
    "KA": range(1, 5),
    "KB": range(1, 4),
    "KC": range(1, 3),
    "KD": range(1, 3),
    "KG": range(1, 3),
    "MV": range(1, 8),
    "MW": range(1, 8),
    "OA": range(1, 4),
    "OD": range(1, 4),
    "OB": range(1, 3),
    "OE": range(1, 4),
    "RH": range(1, 4),
}

_IDENTIFIER_ALIASES: dict[str, str] = {
    "N2": "N02",
    "WND2": "WND",
}

# Section/header identifiers tied to spec structural width rules (FLD LEN: 3 / POS 61-63).
# These tokens are expected to be upper-case alphanumeric and fixed width 3,
# except for legacy parser identifier "HAIL" which maps to a 3-char section code in docs.
SECTION_IDENTIFIER_WIDTH_RULE_IDENTIFIERS: set[str] = {
    "ADD",
    "AA1",
    "AT1",
    "CB1",
    "CO1",
    "CR1",
    "CT1",
    "CU1",
    "CV1",
    "CW1",
    "CX1",
    "ED1",
    "GA1",
    "GJ1",
    "GM1",
    "GO1",
    "GP1",
    "GQ1",
    "GR1",
    "HAIL",
    "IA1",
    "KA1",
    "MA1",
    "MV1",
    "OA1",
    "SA1",
    "ST1",
    "UA1",
    "WND",
}
_SECTION_IDENTIFIER_FAMILIES_WITH_NUMERIC_SUFFIX: set[str] = {
    "AA",
    "AT",
    "CB",
    "CO",
    "CR",
    "CT",
    "CU",
    "CV",
    "CW",
    "CX",
    "ED",
    "GA",
    "GJ",
    "GM",
    "GO",
    "GP",
    "GQ",
    "GR",
    "IA",
    "KA",
    "MA",
    "MV",
    "OA",
    "SA",
    "ST",
    "UA",
}


def is_valid_section_identifier_token(identifier: str) -> bool | None:
    """Validate section/header identifier token format for strict parsing.

    Returns:
        True: identifier is a section token and format is valid.
        False: identifier looks like a section token but format is invalid.
        None: identifier is not part of section-header token checks.
    """
    token = _IDENTIFIER_ALIASES.get(identifier, identifier).strip().upper()
    if not token:
        return None

    if token.startswith("HAIL"):
        # Legacy parser token retained for compatibility with existing datasets.
        return token == "HAIL"

    if token.startswith("ADD") or token.startswith("WND"):
        return bool(re.fullmatch(r"[A-Z0-9]{3}", token))

    for family in _SECTION_IDENTIFIER_FAMILIES_WITH_NUMERIC_SUFFIX:
        if token.startswith(family):
            return bool(re.fullmatch(r"[A-Z0-9]{3}", token))

    return None


def is_valid_repeated_identifier(prefix: str) -> bool | None:
    """Validate repeated identifier format with exact suffix digit count.
    
    Returns:
        True if valid repeated identifier (e.g., OA1, CO3, RH2)
        False if malformed (e.g., OA01, CO02, RH0001 - wrong digit count)
        None if not a repeated identifier pattern
    """
    for key, allowed in _REPEATED_IDENTIFIER_RANGES.items():
        if prefix.startswith(key):
            suffix = prefix[len(key):]
            # Must be exactly 1 digit for all current families (A2)
            if not suffix.isdigit() or len(suffix) != 1:
                return False
            return int(suffix) in allowed
    return None


def is_valid_eqd_identifier(prefix: str) -> bool | None:
    """Validate EQD identifier format with strict suffix requirements.
    
    Returns:
        True if valid EQD identifier (e.g., Q01-Q99, N01-N99, C01-C99)
        False if malformed (e.g., Q0, Q100, Q01A, N001 - wrong format)
        None if not an EQD identifier pattern
    """
    # EQD identifiers are exactly: single letter [QPRCDN] + 2 digits.
    # Do not confuse repeated identifiers like CN2/CO1/CR1, where the second
    # character is a letter rather than the first EQD suffix digit.
    if not prefix or prefix[0] not in "QPRCDN":
        return None
    if len(prefix) == 1:
        return None
    if not prefix[1].isdigit():
        return None
    if len(prefix) != 3 or not prefix[2].isdigit():
        return False
    idx = int(prefix[1:])
    return idx != 0


def is_valid_identifier(identifier: str) -> bool:
    """Validate if an identifier is a known, well-formed NOAA field identifier.
    
    Combines all validation checks: allowlist membership, EQD format, repeated format,
    and prefix family matching.
    
    Args:
        identifier: NOAA field identifier to validate
    
    Returns:
        True if identifier is valid and known, False otherwise
    
    Examples:
        >>> is_valid_identifier("WND")  # Static identifier
        True
        >>> is_valid_identifier("Q01")  # Valid EQD
        True
        >>> is_valid_identifier("CO1")  # Valid repeated
        True
        >>> is_valid_identifier("KA1")  # Valid prefix family (KA)
        True
        >>> is_valid_identifier("Q100")  # Malformed EQD (3 digits)
        False
        >>> is_valid_identifier("OA01")  # Malformed repeated (2 digits)
        False
        >>> is_valid_identifier("NAME")  # Unknown identifier
        False
    """
    # Use get_field_rule which already implements all validation logic:
    # - KNOWN_IDENTIFIERS allowlist (A1)
    # - EQD format validation (A2)
    # - Repeated identifier format validation (A2)
    # - Prefix family matching (e.g., KA1 via KA prefix)
    rule = get_field_rule(identifier)
    return rule is not None


@lru_cache(maxsize=4096)
def get_field_rule(prefix: str) -> FieldRule | None:
    prefix = _IDENTIFIER_ALIASES.get(prefix, prefix)
    if prefix in FIELD_RULES:
        return FIELD_RULES[prefix]
    eqd_valid = is_valid_eqd_identifier(prefix)
    if eqd_valid is False:
        return None
    if eqd_valid is True:
        return EQD_UNIT_RULE if prefix.startswith("N") else EQD_REASON_RULE
    repeated_valid = is_valid_repeated_identifier(prefix)
    if repeated_valid is False:
        return None
    best_match_key = ""
    best_rule = None
    for key, rule in FIELD_RULE_PREFIXES.items():
        if not prefix.startswith(key):
            continue
        if len(key) > len(best_match_key):
            best_match_key = key
            best_rule = rule
    return best_rule


def get_expected_part_count(identifier: str) -> int | None:
    """Get expected comma-part count for an identifier.
    
    Args:
        identifier: NOAA field identifier (e.g., 'WND', 'TMP', 'OA1')
    
    Returns:
        Expected number of comma-separated parts, or None if identifier unknown
    """
    rule = get_field_rule(identifier)
    if rule is None:
        return None
    return len(rule.parts)


def get_token_width_rules(identifier: str, part: int) -> dict[str, int | re.Pattern[str]] | None:
    """Get fixed-width validation rules for a specific part of an identifier.
    
    Args:
        identifier: NOAA field identifier (e.g., 'WND', 'TMP')
        part: Part index (1-based)
    
    Returns:
        Dict with 'width' and/or 'pattern' keys, or None if no width rules defined
    """
    rule = get_field_rule(identifier)
    if rule is None or part not in rule.parts:
        return None
    part_rule = rule.parts[part]
    result = {}
    if part_rule.token_width is not None:
        result["width"] = part_rule.token_width
    if part_rule.token_pattern is not None:
        result["pattern"] = part_rule.token_pattern
    return result if result else None


def _build_known_identifiers() -> set[str]:
    """Build comprehensive set of all valid NOAA identifiers for allowlist (A1).
    
    Returns:
        Set containing all valid identifier names that should be expanded
    """
    identifiers = set()
    
    # Static identifiers from FIELD_RULES
    identifiers.update(FIELD_RULES.keys())
    
    # Standalone and prefix identifiers from FIELD_RULE_PREFIXES
    # This includes HAIL, ED1, IA1, IA2, etc.
    identifiers.update(FIELD_RULE_PREFIXES.keys())
    
    # Repeated identifier families (e.g., OA1-OA3, CO1-CO9)
    for prefix, index_range in _REPEATED_IDENTIFIER_RANGES.items():
        for idx in index_range:
            identifiers.add(f"{prefix}{idx}")
    
    # EQD identifiers (Q01-Q99, P01-P99, R01-R99, C01-C99, D01-D99, N01-N99)
    for letter in "QPRCDN":
        for idx in range(1, 100):  # 01-99
            identifiers.add(f"{letter}{idx:02d}")

    # Legacy aliases accepted by parser for compatibility with spec naming.
    identifiers.update(_IDENTIFIER_ALIASES.keys())
    
    return identifiers


# Allowlist of all valid NOAA identifiers (A1)
KNOWN_IDENTIFIERS: set[str] = _build_known_identifiers()


# ── Column classification helpers ────────────────────────────────────────

_EXPANDED_COL_RE = re.compile(r"^(?P<field>[A-Z][A-Z0-9]*)__(?P<suffix>.+)$")

# Public cleaned-column names. These mappings are reviewer-facing schema
# choices over the NOAA tokens: they expose units, keep quality codes explicit,
# and leave NOAA-derived sidecar names (`TMP__qc_reason`, etc.) traceable to the
# source identifier.
FRIENDLY_COLUMN_MAP: dict[str, str] = {
    "WND__part1": "wind_direction_deg",
    "WND__part2": "wind_direction_quality_code",
    "WND__part3": "wind_type_code",
    "WND__part4": "wind_speed_ms",
    "WND__part5": "wind_speed_quality_code",
    "WND__direction_variable": "wind_direction_variable",
    "CIG__part1": "ceiling_height_m",
    "CIG__part2": "ceiling_height_quality_code",
    "CIG__part3": "ceiling_determination_code",
    "CIG__part4": "ceiling_cavok_code",
    "VIS__part1": "visibility_m",
    "VIS__part2": "visibility_quality_code",
    "VIS__part3": "visibility_variability_code",
    "VIS__part4": "visibility_variability_quality_code",
    "TMP__value": "temperature_c",
    "TMP__quality": "temperature_quality_code",
    "DEW__value": "dew_point_c",
    "DEW__quality": "dew_point_quality_code",
    "SLP__value": "sea_level_pressure_hpa",
    "SLP__quality": "sea_level_pressure_quality_code",
    "OC1__value": "wind_gust_ms",
    "OC1__quality": "wind_gust_quality_code",
    "MA1__part1": "altimeter_setting_hpa",
    "MA1__part2": "altimeter_quality_code",
    "MA1__part3": "station_pressure_hpa",
    "MA1__part4": "station_pressure_quality_code",
    "MD1__part1": "pressure_tendency_code",
    "MD1__part2": "pressure_tendency_quality_code",
    "MD1__part3": "pressure_change_3hr_hpa",
    "MD1__part4": "pressure_change_3hr_quality_code",
    "MD1__part5": "pressure_change_24hr_hpa",
    "MD1__part6": "pressure_change_24hr_quality_code",
    "REM__type": "remarks_type_code",
    "REM__text": "remarks_text",
    "REM__types": "remarks_type_codes",
    "REM__texts_json": "remarks_text_blocks_json",
    "QNN__elements": "qnn_element_ids",
    "QNN__source_flags": "qnn_source_flags",
    "QNN__data_values": "qnn_data_values",
    "SA1__value": "sea_surface_temperature_c",
    "SA1__quality": "sea_surface_temperature_quality_code",
    "UA1__part1": "wave_method_code",
    "UA1__part2": "wave_period_seconds",
    "UA1__part3": "wave_height_m",
    "UA1__part4": "wave_height_quality_code",
    "UA1__part5": "sea_state_code",
    "UA1__part6": "sea_state_quality_code",
    "UG1__part1": "swell_period_seconds",
    "UG1__part2": "swell_height_m",
    "UG1__part3": "swell_direction_deg",
    "UG1__part4": "swell_height_quality_code",
    "UG2__part1": "secondary_swell_period_seconds",
    "UG2__part2": "secondary_swell_height_m",
    "UG2__part3": "secondary_swell_direction_deg",
    "UG2__part4": "secondary_swell_height_quality_code",
    "WA1__part1": "platform_ice_source_code",
    "WA1__part2": "platform_ice_thickness_cm",
    "WA1__part3": "platform_ice_tendency_code",
    "WA1__part4": "platform_ice_quality_code",
    "WD1__part1": "water_surface_ice_edge_bearing_code",
    "WD1__part2": "water_surface_ice_concentration_pct",
    "WD1__part3": "water_surface_ice_non_uniform_code",
    "WD1__part4": "water_surface_ice_ship_position_code",
    "WD1__part5": "water_surface_ice_ship_penetrability_code",
    "WD1__part6": "water_surface_ice_trend_code",
    "WD1__part7": "water_surface_ice_development_code",
    "WD1__part8": "water_surface_ice_growler_presence_code",
    "WD1__part9": "water_surface_ice_growler_quantity",
    "WD1__part10": "water_surface_ice_iceberg_quantity",
    "WD1__part11": "water_surface_ice_quality_code",
    "WG1__part1": "water_surface_ice_hist_edge_bearing_code",
    "WG1__part2": "water_surface_ice_hist_edge_distance_km",
    "WG1__part3": "water_surface_ice_hist_edge_orientation_code",
    "WG1__part4": "water_surface_ice_hist_formation_code",
    "WG1__part5": "water_surface_ice_hist_navigation_code",
    "WG1__part6": "water_surface_ice_hist_quality_code",
    "WJ1__part1": "water_level_ice_thickness_cm",
    "WJ1__part2": "water_level_discharge_m3s",
    "WJ1__part3": "water_level_primary_ice_code",
    "WJ1__part4": "water_level_secondary_ice_code",
    "WJ1__part5": "water_level_stage_height_cm",
    "WJ1__part6": "water_level_slush_code",
    "WJ1__part7": "water_level_state_code",
    "GE1__part1": "convective_cloud_code",
    "GE1__part2": "cloud_vertical_datum_code",
    "GE1__part3": "cloud_base_height_upper_m",
    "GE1__part4": "cloud_base_height_lower_m",
    "GF1__part1": "cloud_total_coverage",
    "GF1__part2": "cloud_opaque_coverage",
    "GF1__part3": "cloud_total_coverage_quality_code",
    "GF1__part4": "cloud_lowest_coverage",
    "GF1__part5": "cloud_lowest_coverage_quality_code",
    "GF1__part6": "cloud_low_genus_code",
    "GF1__part7": "cloud_low_genus_quality_code",
    "GF1__part8": "cloud_lowest_base_height_m",
    "GF1__part9": "cloud_lowest_base_height_quality_code",
    "GF1__part10": "cloud_mid_genus_code",
    "GF1__part11": "cloud_mid_genus_quality_code",
    "GF1__part12": "cloud_high_genus_code",
    "GF1__part13": "cloud_high_genus_quality_code",
    "CO1__part1": "climate_division_number",
    "CO1__part2": "utc_lst_offset_hours",
    "CR1__part1": "crn_datalogger_version",
    "CR1__part2": "crn_datalogger_version_qc",
    "CR1__part3": "crn_datalogger_version_flag",
    "ED1__part1": "runway_direction_deg",
    "ED1__part2": "runway_designator_code",
    "ED1__part3": "runway_visibility_m",
    "ED1__part4": "runway_visibility_quality_code",
    "GQ1__part1": "solar_angle_period_minutes",
    "GQ1__part2": "solar_zenith_angle_deg_mean",
    "GQ1__part3": "solar_zenith_angle_quality_code",
    "GQ1__part4": "solar_azimuth_angle_deg_mean",
    "GQ1__part5": "solar_azimuth_angle_quality_code",
    "GR1__part1": "extraterrestrial_radiation_period_minutes",
    "GR1__part2": "extraterrestrial_radiation_horizontal_wm2",
    "GR1__part3": "extraterrestrial_radiation_horizontal_quality_code",
    "GR1__part4": "extraterrestrial_radiation_normal_wm2",
    "GR1__part5": "extraterrestrial_radiation_normal_quality_code",
    "HAIL__value": "hail_size_cm",
    "HAIL__quality": "hail_size_quality_code",
    "IA1__part1": "ground_surface_observation_code",
    "IA1__part2": "ground_surface_observation_quality_code",
    "IA2__part1": "ground_surface_min_temp_period_hours",
    "IA2__part2": "ground_surface_min_temp_c",
    "IA2__part3": "ground_surface_min_temp_quality_code",
    "IB1__part1": "surface_temp_avg_c",
    "IB1__part2": "surface_temp_avg_qc",
    "IB1__part3": "surface_temp_avg_flag",
    "IB1__part4": "surface_temp_min_c",
    "IB1__part5": "surface_temp_min_qc",
    "IB1__part6": "surface_temp_min_flag",
    "IB1__part7": "surface_temp_max_c",
    "IB1__part8": "surface_temp_max_qc",
    "IB1__part9": "surface_temp_max_flag",
    "IB1__part10": "surface_temp_std_c",
    "IB1__part11": "surface_temp_std_qc",
    "IB1__part12": "surface_temp_std_flag",
    "IB2__part1": "surface_temp_sensor_c",
    "IB2__part2": "surface_temp_sensor_qc",
    "IB2__part3": "surface_temp_sensor_flag",
    "IB2__part4": "surface_temp_sensor_std_c",
    "IB2__part5": "surface_temp_sensor_std_qc",
    "IB2__part6": "surface_temp_sensor_std_flag",
    "IC1__part1": "ground_surface_period_hours",
    "IC1__part2": "ground_surface_wind_movement_miles",
    "IC1__part3": "ground_surface_wind_condition_code",
    "IC1__part4": "ground_surface_wind_quality_code",
    "IC1__part5": "ground_surface_evaporation_in",
    "IC1__part6": "ground_surface_evaporation_condition_code",
    "IC1__part7": "ground_surface_evaporation_quality_code",
    "IC1__part8": "ground_surface_pan_temp_max_c",
    "IC1__part9": "ground_surface_pan_temp_max_condition_code",
    "IC1__part10": "ground_surface_pan_temp_max_quality_code",
    "IC1__part11": "ground_surface_pan_temp_min_c",
    "IC1__part12": "ground_surface_pan_temp_min_condition_code",
    "IC1__part13": "ground_surface_pan_temp_min_quality_code",
    "KE1__part1": "extreme_days_max_le_32f",
    "KE1__part2": "extreme_days_max_le_32f_quality_code",
    "KE1__part3": "extreme_days_max_ge_90f",
    "KE1__part4": "extreme_days_max_ge_90f_quality_code",
    "KE1__part5": "extreme_days_min_le_32f",
    "KE1__part6": "extreme_days_min_le_32f_quality_code",
    "KE1__part7": "extreme_days_min_le_0f",
    "KE1__part8": "extreme_days_min_le_0f_quality_code",
    "KF1__part1": "derived_air_temp_c",
    "KF1__part2": "derived_air_temp_quality_code",
    "ST1__part1": "soil_temp_type_code",
    "ST1__part2": "soil_temp_c",
    "ST1__part3": "soil_temp_quality_code",
    "ST1__part4": "soil_temp_depth_cm",
    "ST1__part5": "soil_temp_depth_quality_code",
    "ST1__part6": "soil_temp_cover_code",
    "ST1__part7": "soil_temp_cover_quality_code",
    "ST1__part8": "soil_temp_subplot",
    "ST1__part9": "soil_temp_subplot_quality_code",
    "ME1__part1": "geopotential_isobaric_code",
    "ME1__part2": "geopotential_height_m",
    "ME1__part3": "geopotential_height_quality_code",
    "MF1__part1": "station_pressure_day_avg_hpa",
    "MF1__part2": "station_pressure_day_avg_quality_code",
    "MF1__part3": "sea_level_pressure_day_avg_hpa",
    "MF1__part4": "sea_level_pressure_day_avg_quality_code",
    "MG1__part1": "station_pressure_day_hpa",
    "MG1__part2": "station_pressure_day_quality_code",
    "MG1__part3": "sea_level_pressure_day_min_hpa",
    "MG1__part4": "sea_level_pressure_day_min_quality_code",
    "MH1__part1": "station_pressure_month_avg_hpa",
    "MH1__part2": "station_pressure_month_avg_quality_code",
    "MH1__part3": "sea_level_pressure_month_avg_hpa",
    "MH1__part4": "sea_level_pressure_month_avg_quality_code",
    "MK1__part1": "sea_level_pressure_month_max_hpa",
    "MK1__part2": "sea_level_pressure_month_max_datetime",
    "MK1__part3": "sea_level_pressure_month_max_quality_code",
    "MK1__part4": "sea_level_pressure_month_min_hpa",
    "MK1__part5": "sea_level_pressure_month_min_datetime",
    "MK1__part6": "sea_level_pressure_month_min_quality_code",
}

_FRIENDLY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^MW(?P<idx>\d+)__part1$"), "present_weather_code_{idx}"),
    (re.compile(r"^MV(?P<idx>\d+)__part1$"), "present_weather_vicinity_code_{idx}"),
    (re.compile(r"^MV(?P<idx>\d+)__part2$"), "present_weather_vicinity_quality_code_{idx}"),
    (re.compile(r"^AY(?P<idx>\d+)__part1$"), "past_weather_condition_code_{idx}"),
    (re.compile(r"^AY(?P<idx>\d+)__part3$"), "past_weather_period_hours_{idx}"),
    (re.compile(r"^AX(?P<idx>\d+)__part1$"), "past_weather_summary_condition_code_{idx}"),
    (re.compile(r"^AX(?P<idx>\d+)__part2$"), "past_weather_summary_condition_quality_code_{idx}"),
    (re.compile(r"^AX(?P<idx>\d+)__part3$"), "past_weather_summary_period_hours_{idx}"),
    (re.compile(r"^AX(?P<idx>\d+)__part4$"), "past_weather_summary_period_quality_code_{idx}"),
    (re.compile(r"^AZ(?P<idx>\d+)__part1$"), "past_weather_auto_condition_code_{idx}"),
    (re.compile(r"^AZ(?P<idx>\d+)__part2$"), "past_weather_auto_condition_quality_code_{idx}"),
    (re.compile(r"^AZ(?P<idx>\d+)__part3$"), "past_weather_auto_period_hours_{idx}"),
    (re.compile(r"^AZ(?P<idx>\d+)__part4$"), "past_weather_auto_period_quality_code_{idx}"),
    (re.compile(r"^AA(?P<idx>\d+)__part1$"), "precip_period_hours_{idx}"),
    (re.compile(r"^AA(?P<idx>\d+)__part2$"), "precip_amount_{idx}"),
    (re.compile(r"^AA(?P<idx>\d+)__part3$"), "precip_condition_code_{idx}"),
    (re.compile(r"^AA(?P<idx>\d+)__part4$"), "precip_quality_code_{idx}"),
    (re.compile(r"^AB(?P<idx>\d+)__part1$"), "precip_monthly_total_{idx}"),
    (re.compile(r"^AB(?P<idx>\d+)__part2$"), "precip_monthly_condition_code_{idx}"),
    (re.compile(r"^AB(?P<idx>\d+)__part3$"), "precip_monthly_quality_code_{idx}"),
    (re.compile(r"^AC(?P<idx>\d+)__part1$"), "precip_history_duration_code_{idx}"),
    (re.compile(r"^AC(?P<idx>\d+)__part2$"), "precip_history_characteristic_code_{idx}"),
    (re.compile(r"^AC(?P<idx>\d+)__part3$"), "precip_history_quality_code_{idx}"),
    (re.compile(r"^AD(?P<idx>\d+)__part1$"), "precip_24h_max_{idx}"),
    (re.compile(r"^AD(?P<idx>\d+)__part2$"), "precip_24h_condition_code_{idx}"),
    (re.compile(r"^AD(?P<idx>\d+)__part3$"), "precip_24h_date_1_{idx}"),
    (re.compile(r"^AD(?P<idx>\d+)__part4$"), "precip_24h_date_2_{idx}"),
    (re.compile(r"^AD(?P<idx>\d+)__part5$"), "precip_24h_date_3_{idx}"),
    (re.compile(r"^AD(?P<idx>\d+)__part6$"), "precip_24h_quality_code_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part1$"), "precip_days_ge_001_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part2$"), "precip_days_ge_001_quality_code_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part3$"), "precip_days_ge_010_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part4$"), "precip_days_ge_010_quality_code_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part5$"), "precip_days_ge_050_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part6$"), "precip_days_ge_050_quality_code_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part7$"), "precip_days_ge_100_{idx}"),
    (re.compile(r"^AE(?P<idx>\d+)__part8$"), "precip_days_ge_100_quality_code_{idx}"),
    (re.compile(r"^AG(?P<idx>\d+)__part1$"), "precip_estimated_discrepancy_code_{idx}"),
    (re.compile(r"^AG(?P<idx>\d+)__part2$"), "precip_estimated_depth_mm_{idx}"),
    (re.compile(r"^AH(?P<idx>\d+)__part1$"), "precip_5_to_45_min_period_minutes_{idx}"),
    (re.compile(r"^AH(?P<idx>\d+)__part2$"), "precip_5_to_45_min_amount_mm_{idx}"),
    (re.compile(r"^AH(?P<idx>\d+)__part3$"), "precip_5_to_45_min_condition_code_{idx}"),
    (re.compile(r"^AH(?P<idx>\d+)__part4$"), "precip_5_to_45_min_end_datetime_{idx}"),
    (re.compile(r"^AH(?P<idx>\d+)__part5$"), "precip_5_to_45_min_quality_code_{idx}"),
    (re.compile(r"^AI(?P<idx>\d+)__part1$"), "precip_60_to_180_min_period_minutes_{idx}"),
    (re.compile(r"^AI(?P<idx>\d+)__part2$"), "precip_60_to_180_min_amount_mm_{idx}"),
    (re.compile(r"^AI(?P<idx>\d+)__part3$"), "precip_60_to_180_min_condition_code_{idx}"),
    (re.compile(r"^AI(?P<idx>\d+)__part4$"), "precip_60_to_180_min_end_datetime_{idx}"),
    (re.compile(r"^AI(?P<idx>\d+)__part5$"), "precip_60_to_180_min_quality_code_{idx}"),
    (re.compile(r"^AK(?P<idx>\d+)__part1$"), "snow_depth_monthly_max_{idx}"),
    (re.compile(r"^AK(?P<idx>\d+)__part2$"), "snow_depth_monthly_max_condition_code_{idx}"),
    (re.compile(r"^AK(?P<idx>\d+)__part3$"), "snow_depth_monthly_max_dates_{idx}"),
    (re.compile(r"^AK(?P<idx>\d+)__part4$"), "snow_depth_monthly_max_quality_code_{idx}"),
    (re.compile(r"^AL(?P<idx>\d+)__part1$"), "snow_accum_period_hours_{idx}"),
    (re.compile(r"^AL(?P<idx>\d+)__part2$"), "snow_accum_depth_cm_{idx}"),
    (re.compile(r"^AL(?P<idx>\d+)__part3$"), "snow_accum_condition_code_{idx}"),
    (re.compile(r"^AL(?P<idx>\d+)__part4$"), "snow_accum_quality_code_{idx}"),
    (re.compile(r"^AM(?P<idx>\d+)__part1$"), "snow_accum_24h_max_cm_{idx}"),
    (re.compile(r"^AM(?P<idx>\d+)__part2$"), "snow_accum_24h_max_condition_code_{idx}"),
    (re.compile(r"^AM(?P<idx>\d+)__part3$"), "snow_accum_24h_date_1_{idx}"),
    (re.compile(r"^AM(?P<idx>\d+)__part4$"), "snow_accum_24h_date_2_{idx}"),
    (re.compile(r"^AM(?P<idx>\d+)__part5$"), "snow_accum_24h_date_3_{idx}"),
    (re.compile(r"^AM(?P<idx>\d+)__part6$"), "snow_accum_24h_max_quality_code_{idx}"),
    (re.compile(r"^AN(?P<idx>\d+)__part1$"), "snow_accum_day_month_period_hours_{idx}"),
    (re.compile(r"^AN(?P<idx>\d+)__part2$"), "snow_accum_day_month_depth_cm_{idx}"),
    (re.compile(r"^AN(?P<idx>\d+)__part3$"), "snow_accum_day_month_condition_code_{idx}"),
    (re.compile(r"^AN(?P<idx>\d+)__part4$"), "snow_accum_day_month_quality_code_{idx}"),
    (re.compile(r"^AO(?P<idx>\d+)__part1$"), "precip_minute_period_minutes_{idx}"),
    (re.compile(r"^AO(?P<idx>\d+)__part2$"), "precip_minute_amount_mm_{idx}"),
    (re.compile(r"^AO(?P<idx>\d+)__part3$"), "precip_minute_condition_code_{idx}"),
    (re.compile(r"^AO(?P<idx>\d+)__part4$"), "precip_minute_quality_code_{idx}"),
    (re.compile(r"^AP(?P<idx>\d+)__part1$"), "hpd_gauge_value_mm_{idx}"),
    (re.compile(r"^AP(?P<idx>\d+)__part2$"), "hpd_gauge_condition_code_{idx}"),
    (re.compile(r"^AP(?P<idx>\d+)__part3$"), "hpd_gauge_quality_code_{idx}"),
    (re.compile(r"^AJ(?P<idx>\d+)__part1$"), "snow_depth_{idx}"),
    (re.compile(r"^AJ(?P<idx>\d+)__part2$"), "snow_depth_condition_code_{idx}"),
    (re.compile(r"^AJ(?P<idx>\d+)__part3$"), "snow_depth_quality_code_{idx}"),
    (re.compile(r"^AJ(?P<idx>\d+)__part4$"), "snow_water_equivalent_{idx}"),
    (re.compile(r"^AJ(?P<idx>\d+)__part5$"), "snow_water_condition_code_{idx}"),
    (re.compile(r"^AJ(?P<idx>\d+)__part6$"), "snow_water_quality_code_{idx}"),
    (re.compile(r"^AT(?P<idx>\d+)__part1$"), "daily_present_weather_source_{idx}"),
    (re.compile(r"^AT(?P<idx>\d+)__part2$"), "daily_present_weather_type_code_{idx}"),
    (re.compile(r"^AT(?P<idx>\d+)__part3$"), "daily_present_weather_type_abbr_{idx}"),
    (re.compile(r"^AT(?P<idx>\d+)__part4$"), "daily_present_weather_quality_code_{idx}"),
    (re.compile(r"^AU(?P<idx>\d+)__part1$"), "weather_intensity_code_{idx}"),
    (re.compile(r"^AU(?P<idx>\d+)__part2$"), "weather_descriptor_code_{idx}"),
    (re.compile(r"^AU(?P<idx>\d+)__part3$"), "weather_precip_code_{idx}"),
    (re.compile(r"^AU(?P<idx>\d+)__part4$"), "weather_obscuration_code_{idx}"),
    (re.compile(r"^AU(?P<idx>\d+)__part5$"), "weather_other_code_{idx}"),
    (re.compile(r"^AU(?P<idx>\d+)__part6$"), "weather_combo_indicator_{idx}"),
    (re.compile(r"^AU(?P<idx>\d+)__part7$"), "weather_quality_code_{idx}"),
    (re.compile(r"^AW(?P<idx>\d+)__part1$"), "automated_present_weather_code_{idx}"),
    (re.compile(r"^AW(?P<idx>\d+)__part2$"), "automated_present_weather_quality_code_{idx}"),
    (re.compile(r"^CB(?P<idx>\d+)__part1$"), "secondary_precip_period_minutes_{idx}"),
    (re.compile(r"^CB(?P<idx>\d+)__part2$"), "secondary_precip_depth_mm_{idx}"),
    (re.compile(r"^CB(?P<idx>\d+)__part3$"), "secondary_precip_qc_{idx}"),
    (re.compile(r"^CB(?P<idx>\d+)__part4$"), "secondary_precip_flag_{idx}"),
    (re.compile(r"^CF(?P<idx>\d+)__part1$"), "crn_fan_speed_rps_{idx}"),
    (re.compile(r"^CF(?P<idx>\d+)__part2$"), "crn_fan_speed_qc_{idx}"),
    (re.compile(r"^CF(?P<idx>\d+)__part3$"), "crn_fan_speed_flag_{idx}"),
    (re.compile(r"^CG(?P<idx>\d+)__part1$"), "primary_precip_depth_mm_{idx}"),
    (re.compile(r"^CG(?P<idx>\d+)__part2$"), "primary_precip_qc_{idx}"),
    (re.compile(r"^CG(?P<idx>\d+)__part3$"), "primary_precip_flag_{idx}"),
    (re.compile(r"^CH(?P<idx>\d+)__part1$"), "rh_temp_period_minutes_{idx}"),
    (re.compile(r"^CH(?P<idx>\d+)__part2$"), "rh_temp_avg_c_{idx}"),
    (re.compile(r"^CH(?P<idx>\d+)__part3$"), "rh_temp_avg_qc_{idx}"),
    (re.compile(r"^CH(?P<idx>\d+)__part4$"), "rh_temp_avg_flag_{idx}"),
    (re.compile(r"^CH(?P<idx>\d+)__part5$"), "rh_avg_percent_{idx}"),
    (re.compile(r"^CH(?P<idx>\d+)__part6$"), "rh_avg_qc_{idx}"),
    (re.compile(r"^CH(?P<idx>\d+)__part7$"), "rh_avg_flag_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part1$"), "rh_temp_min_c_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part2$"), "rh_temp_min_qc_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part3$"), "rh_temp_min_flag_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part4$"), "rh_temp_max_c_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part5$"), "rh_temp_max_qc_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part6$"), "rh_temp_max_flag_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part7$"), "rh_temp_std_c_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part8$"), "rh_temp_std_qc_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part9$"), "rh_temp_std_flag_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part10$"), "rh_std_percent_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part11$"), "rh_std_qc_{idx}"),
    (re.compile(r"^CI(?P<idx>\d+)__part12$"), "rh_std_flag_{idx}"),
    (re.compile(r"^CO(?P<idx>[2-9])__part1$"), "coop_element_id_{idx}"),
    (re.compile(r"^CO(?P<idx>[2-9])__part2$"), "coop_time_offset_hours_{idx}"),
    (re.compile(r"^CT(?P<idx>\d+)__part1$"), "subhourly_temp_avg_c_{idx}"),
    (re.compile(r"^CT(?P<idx>\d+)__part2$"), "subhourly_temp_avg_qc_{idx}"),
    (re.compile(r"^CT(?P<idx>\d+)__part3$"), "subhourly_temp_avg_flag_{idx}"),
    (re.compile(r"^CU(?P<idx>\d+)__part1$"), "hourly_temp_avg_c_{idx}"),
    (re.compile(r"^CU(?P<idx>\d+)__part2$"), "hourly_temp_avg_qc_{idx}"),
    (re.compile(r"^CU(?P<idx>\d+)__part3$"), "hourly_temp_avg_flag_{idx}"),
    (re.compile(r"^CU(?P<idx>\d+)__part4$"), "hourly_temp_std_c_{idx}"),
    (re.compile(r"^CU(?P<idx>\d+)__part5$"), "hourly_temp_std_qc_{idx}"),
    (re.compile(r"^CU(?P<idx>\d+)__part6$"), "hourly_temp_std_flag_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part1$"), "hourly_temp_min_c_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part2$"), "hourly_temp_min_qc_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part3$"), "hourly_temp_min_flag_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part4$"), "hourly_temp_min_time_hhmm_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part5$"), "hourly_temp_min_time_qc_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part6$"), "hourly_temp_min_time_flag_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part7$"), "hourly_temp_max_c_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part8$"), "hourly_temp_max_qc_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part9$"), "hourly_temp_max_flag_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part10$"), "hourly_temp_max_time_hhmm_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part11$"), "hourly_temp_max_time_qc_{idx}"),
    (re.compile(r"^CV(?P<idx>\d+)__part12$"), "hourly_temp_max_time_flag_{idx}"),
    (re.compile(r"^CW(?P<idx>\d+)__part1$"), "wetness_channel1_value_{idx}"),
    (re.compile(r"^CW(?P<idx>\d+)__part2$"), "wetness_channel1_qc_{idx}"),
    (re.compile(r"^CW(?P<idx>\d+)__part3$"), "wetness_channel1_flag_{idx}"),
    (re.compile(r"^CW(?P<idx>\d+)__part4$"), "wetness_channel2_value_{idx}"),
    (re.compile(r"^CW(?P<idx>\d+)__part5$"), "wetness_channel2_qc_{idx}"),
    (re.compile(r"^CW(?P<idx>\d+)__part6$"), "wetness_channel2_flag_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part1$"), "geonor_precip_total_mm_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part2$"), "geonor_precip_qc_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part3$"), "geonor_precip_flag_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part4$"), "geonor_freq_avg_hz_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part5$"), "geonor_freq_avg_qc_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part6$"), "geonor_freq_avg_flag_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part7$"), "geonor_freq_min_hz_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part8$"), "geonor_freq_min_qc_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part9$"), "geonor_freq_min_flag_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part10$"), "geonor_freq_max_hz_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part11$"), "geonor_freq_max_qc_{idx}"),
    (re.compile(r"^CX(?P<idx>\d+)__part12$"), "geonor_freq_max_flag_{idx}"),
    (re.compile(r"^CN1__part1$"), "battery_voltage_avg_v_1"),
    (re.compile(r"^CN1__part2$"), "battery_voltage_avg_qc_1"),
    (re.compile(r"^CN1__part3$"), "battery_voltage_avg_flag_1"),
    (re.compile(r"^CN1__part4$"), "battery_voltage_full_load_v_1"),
    (re.compile(r"^CN1__part5$"), "battery_voltage_full_load_qc_1"),
    (re.compile(r"^CN1__part6$"), "battery_voltage_full_load_flag_1"),
    (re.compile(r"^CN1__part7$"), "battery_voltage_datalogger_v_1"),
    (re.compile(r"^CN1__part8$"), "battery_voltage_datalogger_qc_1"),
    (re.compile(r"^CN1__part9$"), "battery_voltage_datalogger_flag_1"),
    (re.compile(r"^CN2__part1$"), "panel_temp_c_1"),
    (re.compile(r"^CN2__part2$"), "panel_temp_qc_1"),
    (re.compile(r"^CN2__part3$"), "panel_temp_flag_1"),
    (re.compile(r"^CN2__part4$"), "inlet_temp_max_c_1"),
    (re.compile(r"^CN2__part5$"), "inlet_temp_max_qc_1"),
    (re.compile(r"^CN2__part6$"), "inlet_temp_max_flag_1"),
    (re.compile(r"^CN2__part7$"), "door_open_minutes_1"),
    (re.compile(r"^CN2__part8$"), "door_open_qc_1"),
    (re.compile(r"^CN2__part9$"), "door_open_flag_1"),
    (re.compile(r"^CN3__part1$"), "reference_resistance_ohm_1"),
    (re.compile(r"^CN3__part2$"), "reference_resistance_qc_1"),
    (re.compile(r"^CN3__part3$"), "reference_resistance_flag_1"),
    (re.compile(r"^CN3__part4$"), "datalogger_signature_1"),
    (re.compile(r"^CN3__part5$"), "datalogger_signature_qc_1"),
    (re.compile(r"^CN3__part6$"), "datalogger_signature_flag_1"),
    (re.compile(r"^CN4__part1$"), "precip_heater_flag_1"),
    (re.compile(r"^CN4__part2$"), "precip_heater_qc_1"),
    (re.compile(r"^CN4__part3$"), "precip_heater_flag_code_1"),
    (re.compile(r"^CN4__part4$"), "datalogger_door_flag_1"),
    (re.compile(r"^CN4__part5$"), "datalogger_door_flag_qc_1"),
    (re.compile(r"^CN4__part6$"), "datalogger_door_flag_code_1"),
    (re.compile(r"^CN4__part7$"), "forward_transmitter_wattage_1"),
    (re.compile(r"^CN4__part8$"), "forward_transmitter_qc_1"),
    (re.compile(r"^CN4__part9$"), "forward_transmitter_flag_1"),
    (re.compile(r"^CN4__part10$"), "reflected_transmitter_wattage_1"),
    (re.compile(r"^CN4__part11$"), "reflected_transmitter_qc_1"),
    (re.compile(r"^CN4__part12$"), "reflected_transmitter_flag_1"),
    (re.compile(r"^GA(?P<idx>\d+)__part1$"), "cloud_layer_coverage_{idx}"),
    (re.compile(r"^GA(?P<idx>\d+)__part2$"), "cloud_layer_coverage_quality_code_{idx}"),
    (re.compile(r"^GA(?P<idx>\d+)__part3$"), "cloud_layer_base_height_m_{idx}"),
    (re.compile(r"^GA(?P<idx>\d+)__part4$"), "cloud_layer_base_height_quality_code_{idx}"),
    (re.compile(r"^GA(?P<idx>\d+)__part5$"), "cloud_layer_type_code_{idx}"),
    (re.compile(r"^GA(?P<idx>\d+)__part6$"), "cloud_layer_type_quality_code_{idx}"),
    (re.compile(r"^KA(?P<idx>\d+)__part3$"), "extreme_temp_c_{idx}"),
    (re.compile(r"^KA(?P<idx>\d+)__part2$"), "extreme_temp_type_{idx}"),
    (re.compile(r"^KA(?P<idx>\d+)__part1$"), "extreme_temp_period_hours_{idx}"),
    (re.compile(r"^KA(?P<idx>\d+)__part4$"), "extreme_temp_quality_code_{idx}"),
    (re.compile(r"^KC(?P<idx>\d+)__part1$"), "extreme_month_temp_type_{idx}"),
    (re.compile(r"^KC(?P<idx>\d+)__part2$"), "extreme_month_temp_condition_{idx}"),
    (re.compile(r"^KC(?P<idx>\d+)__part3$"), "extreme_month_temp_c_{idx}"),
    (re.compile(r"^KC(?P<idx>\d+)__part4$"), "extreme_month_temp_dates_{idx}"),
    (re.compile(r"^KC(?P<idx>\d+)__part5$"), "extreme_month_temp_quality_code_{idx}"),
    (re.compile(r"^KD(?P<idx>\d+)__part1$"), "degree_days_period_hours_{idx}"),
    (re.compile(r"^KD(?P<idx>\d+)__part2$"), "degree_days_type_{idx}"),
    (re.compile(r"^KD(?P<idx>\d+)__part3$"), "degree_days_value_{idx}"),
    (re.compile(r"^KD(?P<idx>\d+)__part4$"), "degree_days_quality_code_{idx}"),
    (re.compile(r"^KG(?P<idx>\d+)__part1$"), "avg_dew_wet_period_hours_{idx}"),
    (re.compile(r"^KG(?P<idx>\d+)__part2$"), "avg_dew_wet_type_{idx}"),
    (re.compile(r"^KG(?P<idx>\d+)__part3$"), "avg_dew_wet_temp_c_{idx}"),
    (re.compile(r"^KG(?P<idx>\d+)__part4$"), "avg_dew_wet_derived_code_{idx}"),
    (re.compile(r"^KG(?P<idx>\d+)__part5$"), "avg_dew_wet_quality_code_{idx}"),
    (re.compile(r"^KB(?P<idx>\d+)__part1$"), "avg_air_temp_period_hours_{idx}"),
    (re.compile(r"^KB(?P<idx>\d+)__part2$"), "avg_air_temp_type_{idx}"),
    (re.compile(r"^KB(?P<idx>\d+)__part3$"), "avg_air_temp_c_{idx}"),
    (re.compile(r"^KB(?P<idx>\d+)__part4$"), "avg_air_temp_quality_code_{idx}"),
    (re.compile(r"^GD(?P<idx>\d+)__part1$"), "sky_cover_summation_code_{idx}"),
    (re.compile(r"^GD(?P<idx>\d+)__part2$"), "sky_cover_summation_okta_code_{idx}"),
    (re.compile(r"^GD(?P<idx>\d+)__part3$"), "sky_cover_summation_quality_code_{idx}"),
    (re.compile(r"^GD(?P<idx>\d+)__part4$"), "sky_cover_summation_height_m_{idx}"),
    (re.compile(r"^GD(?P<idx>\d+)__part5$"), "sky_cover_summation_height_quality_code_{idx}"),
    (re.compile(r"^GD(?P<idx>\d+)__part6$"), "sky_cover_summation_characteristic_code_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part1$"), "below_station_cloud_coverage_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part2$"), "below_station_cloud_coverage_quality_code_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part3$"), "below_station_cloud_top_height_m_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part4$"), "below_station_cloud_top_height_quality_code_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part5$"), "below_station_cloud_type_code_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part6$"), "below_station_cloud_type_quality_code_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part7$"), "below_station_cloud_top_code_{idx}"),
    (re.compile(r"^GG(?P<idx>\d+)__part8$"), "below_station_cloud_top_quality_code_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part1$"), "solar_radiation_avg_wm2_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part2$"), "solar_radiation_avg_qc_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part3$"), "solar_radiation_avg_flag_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part4$"), "solar_radiation_min_wm2_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part5$"), "solar_radiation_min_qc_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part6$"), "solar_radiation_min_flag_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part7$"), "solar_radiation_max_wm2_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part8$"), "solar_radiation_max_qc_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part9$"), "solar_radiation_max_flag_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part10$"), "solar_radiation_std_wm2_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part11$"), "solar_radiation_std_qc_{idx}"),
    (re.compile(r"^GH(?P<idx>\d+)__part12$"), "solar_radiation_std_flag_{idx}"),
    (re.compile(r"^GJ(?P<idx>\d+)__part1$"), "sunshine_duration_minutes_{idx}"),
    (re.compile(r"^GJ(?P<idx>\d+)__part2$"), "sunshine_duration_quality_code_{idx}"),
    (re.compile(r"^GK(?P<idx>\d+)__part1$"), "sunshine_percent_{idx}"),
    (re.compile(r"^GK(?P<idx>\d+)__part2$"), "sunshine_percent_quality_code_{idx}"),
    (re.compile(r"^GL(?P<idx>\d+)__part1$"), "sunshine_month_minutes_{idx}"),
    (re.compile(r"^GL(?P<idx>\d+)__part2$"), "sunshine_month_quality_code_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part1$"), "solar_irradiance_period_minutes_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part2$"), "global_irradiance_wm2_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part3$"), "global_irradiance_flag_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part4$"), "global_irradiance_quality_code_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part5$"), "direct_beam_irradiance_wm2_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part6$"), "direct_beam_irradiance_flag_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part7$"), "direct_beam_irradiance_quality_code_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part8$"), "diffuse_irradiance_wm2_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part9$"), "diffuse_irradiance_flag_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part10$"), "diffuse_irradiance_quality_code_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part11$"), "uvb_global_irradiance_mw_m2_{idx}"),
    (re.compile(r"^GM(?P<idx>\d+)__part12$"), "uvb_global_irradiance_quality_code_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part1$"), "solar_radiation_period_minutes_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part2$"), "upwelling_global_solar_radiation_mw_m2_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part3$"), "upwelling_global_solar_radiation_quality_code_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part4$"), "downwelling_thermal_ir_mw_m2_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part5$"), "downwelling_thermal_ir_quality_code_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part6$"), "upwelling_thermal_ir_mw_m2_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part7$"), "upwelling_thermal_ir_quality_code_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part8$"), "photosynthetic_radiation_mw_m2_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part9$"), "photosynthetic_radiation_quality_code_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part10$"), "solar_zenith_angle_deg_{idx}"),
    (re.compile(r"^GN(?P<idx>\d+)__part11$"), "solar_zenith_angle_quality_code_{idx}"),
    (re.compile(r"^GO(?P<idx>\d+)__part1$"), "net_radiation_period_minutes_{idx}"),
    (re.compile(r"^GO(?P<idx>\d+)__part2$"), "net_solar_radiation_wm2_{idx}"),
    (re.compile(r"^GO(?P<idx>\d+)__part3$"), "net_solar_radiation_quality_code_{idx}"),
    (re.compile(r"^GO(?P<idx>\d+)__part4$"), "net_infrared_radiation_wm2_{idx}"),
    (re.compile(r"^GO(?P<idx>\d+)__part5$"), "net_infrared_radiation_quality_code_{idx}"),
    (re.compile(r"^GO(?P<idx>\d+)__part6$"), "net_radiation_wm2_{idx}"),
    (re.compile(r"^GO(?P<idx>\d+)__part7$"), "net_radiation_quality_code_{idx}"),
    (re.compile(r"^GP1__part1$"), "modeled_solar_period_minutes"),
    (re.compile(r"^GP1__part2$"), "modeled_global_horizontal_wm2"),
    (re.compile(r"^GP1__part3$"), "modeled_global_horizontal_source_flag"),
    (re.compile(r"^GP1__part4$"), "modeled_global_horizontal_uncertainty_pct"),
    (re.compile(r"^GP1__part5$"), "modeled_direct_normal_wm2"),
    (re.compile(r"^GP1__part6$"), "modeled_direct_normal_source_flag"),
    (re.compile(r"^GP1__part7$"), "modeled_direct_normal_uncertainty_pct"),
    (re.compile(r"^GP1__part8$"), "modeled_diffuse_horizontal_wm2"),
    (re.compile(r"^GP1__part9$"), "modeled_diffuse_horizontal_source_flag"),
    (re.compile(r"^GP1__part10$"), "modeled_diffuse_horizontal_uncertainty_pct"),
    (re.compile(r"^OA(?P<idx>\d+)__part1$"), "supp_wind_oa_type_code_{idx}"),
    (re.compile(r"^OA(?P<idx>\d+)__part2$"), "supp_wind_oa_period_hours_{idx}"),
    (re.compile(r"^OA(?P<idx>\d+)__part3$"), "supp_wind_oa_speed_ms_{idx}"),
    (re.compile(r"^OA(?P<idx>\d+)__part4$"), "supp_wind_oa_speed_quality_code_{idx}"),
    (re.compile(r"^OD(?P<idx>\d+)__part1$"), "supp_wind_type_code_{idx}"),
    (re.compile(r"^OD(?P<idx>\d+)__part2$"), "supp_wind_period_hours_{idx}"),
    (re.compile(r"^OD(?P<idx>\d+)__part3$"), "supp_wind_direction_deg_{idx}"),
    (re.compile(r"^OD(?P<idx>\d+)__part4$"), "supp_wind_speed_ms_{idx}"),
    (re.compile(r"^OD(?P<idx>\d+)__part5$"), "supp_wind_speed_quality_code_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part1$"), "wind_avg_period_minutes_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part2$"), "wind_max_gust_ms_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part3$"), "wind_max_gust_qc_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part4$"), "wind_max_gust_flag_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part5$"), "wind_max_direction_deg_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part6$"), "wind_max_direction_qc_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part7$"), "wind_max_direction_flag_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part8$"), "wind_speed_std_ms_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part9$"), "wind_speed_std_qc_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part10$"), "wind_speed_std_flag_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part11$"), "wind_direction_std_deg_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part12$"), "wind_direction_std_qc_{idx}"),
    (re.compile(r"^OB(?P<idx>\d+)__part13$"), "wind_direction_std_flag_{idx}"),
    (re.compile(r"^Q(?P<idx>\d+)__part1$"), "eqd_original_value_q{idx}"),
    (re.compile(r"^Q(?P<idx>\d+)__part2$"), "eqd_reason_code_q{idx}"),
    (re.compile(r"^Q(?P<idx>\d+)__part3$"), "eqd_parameter_code_q{idx}"),
    (re.compile(r"^P(?P<idx>\d+)__part1$"), "eqd_original_value_p{idx}"),
    (re.compile(r"^P(?P<idx>\d+)__part2$"), "eqd_reason_code_p{idx}"),
    (re.compile(r"^P(?P<idx>\d+)__part3$"), "eqd_parameter_code_p{idx}"),
    (re.compile(r"^R(?P<idx>\d+)__part1$"), "eqd_original_value_r{idx}"),
    (re.compile(r"^R(?P<idx>\d+)__part2$"), "eqd_reason_code_r{idx}"),
    (re.compile(r"^R(?P<idx>\d+)__part3$"), "eqd_parameter_code_r{idx}"),
    (re.compile(r"^C(?P<idx>\d+)__part1$"), "eqd_original_value_c{idx}"),
    (re.compile(r"^C(?P<idx>\d+)__part2$"), "eqd_reason_code_c{idx}"),
    (re.compile(r"^C(?P<idx>\d+)__part3$"), "eqd_parameter_code_c{idx}"),
    (re.compile(r"^D(?P<idx>\d+)__part1$"), "eqd_original_value_d{idx}"),
    (re.compile(r"^D(?P<idx>\d+)__part2$"), "eqd_reason_code_d{idx}"),
    (re.compile(r"^D(?P<idx>\d+)__part3$"), "eqd_parameter_code_d{idx}"),
    (re.compile(r"^N(?P<idx>\d+)__part1$"), "eqd_original_value_n{idx}"),
    (re.compile(r"^N(?P<idx>\d+)__part2$"), "eqd_units_code_n{idx}"),
    (re.compile(r"^N(?P<idx>\d+)__part3$"), "eqd_parameter_code_n{idx}"),
    (re.compile(r"^OE(?P<idx>\d+)__part1$"), "summary_wind_type_code_{idx}"),
    (re.compile(r"^OE(?P<idx>\d+)__part2$"), "summary_wind_period_hours_{idx}"),
    (re.compile(r"^OE(?P<idx>\d+)__part3$"), "summary_wind_speed_ms_{idx}"),
    (re.compile(r"^OE(?P<idx>\d+)__part4$"), "summary_wind_direction_deg_{idx}"),
    (re.compile(r"^OE(?P<idx>\d+)__part5$"), "summary_wind_time_hhmm_{idx}"),
    (re.compile(r"^OE(?P<idx>\d+)__part6$"), "summary_wind_quality_code_{idx}"),
    (re.compile(r"^RH(?P<idx>\d+)__part1$"), "relative_humidity_period_hours_{idx}"),
    (re.compile(r"^RH(?P<idx>\d+)__part2$"), "relative_humidity_code_{idx}"),
    (re.compile(r"^RH(?P<idx>\d+)__part3$"), "relative_humidity_percent_{idx}"),
    (re.compile(r"^RH(?P<idx>\d+)__part4$"), "relative_humidity_derived_code_{idx}"),
    (re.compile(r"^RH(?P<idx>\d+)__part5$"), "relative_humidity_quality_code_{idx}"),
]

_INTERNAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"^present_weather_code_(?P<idx>\d+)$"), "MW{idx}__part1"),
    (re.compile(r"^present_weather_vicinity_code_(?P<idx>\d+)$"), "MV{idx}__part1"),
    (re.compile(r"^present_weather_vicinity_quality_code_(?P<idx>\d+)$"), "MV{idx}__part2"),
    (re.compile(r"^automated_present_weather_code_(?P<idx>\d+)$"), "AW{idx}__part1"),
    (re.compile(r"^automated_present_weather_quality_code_(?P<idx>\d+)$"), "AW{idx}__part2"),
    (re.compile(r"^past_weather_condition_code_(?P<idx>\d+)$"), "AY{idx}__part1"),
    (re.compile(r"^past_weather_period_hours_(?P<idx>\d+)$"), "AY{idx}__part3"),
    (re.compile(r"^past_weather_summary_condition_code_(?P<idx>\d+)$"), "AX{idx}__part1"),
    (
        re.compile(r"^past_weather_summary_condition_quality_code_(?P<idx>\d+)$"),
        "AX{idx}__part2",
    ),
    (re.compile(r"^past_weather_summary_period_hours_(?P<idx>\d+)$"), "AX{idx}__part3"),
    (re.compile(r"^past_weather_summary_period_quality_code_(?P<idx>\d+)$"), "AX{idx}__part4"),
    (re.compile(r"^past_weather_auto_condition_code_(?P<idx>\d+)$"), "AZ{idx}__part1"),
    (
        re.compile(r"^past_weather_auto_condition_quality_code_(?P<idx>\d+)$"),
        "AZ{idx}__part2",
    ),
    (re.compile(r"^past_weather_auto_period_hours_(?P<idx>\d+)$"), "AZ{idx}__part3"),
    (re.compile(r"^past_weather_auto_period_quality_code_(?P<idx>\d+)$"), "AZ{idx}__part4"),
    (re.compile(r"^precip_period_hours_(?P<idx>\d+)$"), "AA{idx}__part1"),
    (re.compile(r"^precip_amount_(?P<idx>\d+)$"), "AA{idx}__part2"),
    (re.compile(r"^precip_condition_code_(?P<idx>\d+)$"), "AA{idx}__part3"),
    (re.compile(r"^precip_quality_code_(?P<idx>\d+)$"), "AA{idx}__part4"),
    (re.compile(r"^precip_monthly_total_(?P<idx>\d+)$"), "AB{idx}__part1"),
    (re.compile(r"^precip_monthly_condition_code_(?P<idx>\d+)$"), "AB{idx}__part2"),
    (re.compile(r"^precip_monthly_quality_code_(?P<idx>\d+)$"), "AB{idx}__part3"),
    (re.compile(r"^precip_history_duration_code_(?P<idx>\d+)$"), "AC{idx}__part1"),
    (re.compile(r"^precip_history_characteristic_code_(?P<idx>\d+)$"), "AC{idx}__part2"),
    (re.compile(r"^precip_history_quality_code_(?P<idx>\d+)$"), "AC{idx}__part3"),
    (re.compile(r"^precip_24h_max_(?P<idx>\d+)$"), "AD{idx}__part1"),
    (re.compile(r"^precip_24h_condition_code_(?P<idx>\d+)$"), "AD{idx}__part2"),
    (re.compile(r"^precip_24h_date_1_(?P<idx>\d+)$"), "AD{idx}__part3"),
    (re.compile(r"^precip_24h_date_2_(?P<idx>\d+)$"), "AD{idx}__part4"),
    (re.compile(r"^precip_24h_date_3_(?P<idx>\d+)$"), "AD{idx}__part5"),
    (re.compile(r"^precip_24h_quality_code_(?P<idx>\d+)$"), "AD{idx}__part6"),
    (re.compile(r"^precip_days_ge_001_(?P<idx>\d+)$"), "AE{idx}__part1"),
    (re.compile(r"^precip_days_ge_001_quality_code_(?P<idx>\d+)$"), "AE{idx}__part2"),
    (re.compile(r"^precip_days_ge_010_(?P<idx>\d+)$"), "AE{idx}__part3"),
    (re.compile(r"^precip_days_ge_010_quality_code_(?P<idx>\d+)$"), "AE{idx}__part4"),
    (re.compile(r"^precip_days_ge_050_(?P<idx>\d+)$"), "AE{idx}__part5"),
    (re.compile(r"^precip_days_ge_050_quality_code_(?P<idx>\d+)$"), "AE{idx}__part6"),
    (re.compile(r"^precip_days_ge_100_(?P<idx>\d+)$"), "AE{idx}__part7"),
    (re.compile(r"^precip_days_ge_100_quality_code_(?P<idx>\d+)$"), "AE{idx}__part8"),
    (re.compile(r"^precip_estimated_discrepancy_code_(?P<idx>\d+)$"), "AG{idx}__part1"),
    (re.compile(r"^precip_estimated_depth_mm_(?P<idx>\d+)$"), "AG{idx}__part2"),
    (re.compile(r"^precip_5_to_45_min_period_minutes_(?P<idx>\d+)$"), "AH{idx}__part1"),
    (re.compile(r"^precip_5_to_45_min_amount_mm_(?P<idx>\d+)$"), "AH{idx}__part2"),
    (re.compile(r"^precip_5_to_45_min_condition_code_(?P<idx>\d+)$"), "AH{idx}__part3"),
    (re.compile(r"^precip_5_to_45_min_end_datetime_(?P<idx>\d+)$"), "AH{idx}__part4"),
    (re.compile(r"^precip_5_to_45_min_quality_code_(?P<idx>\d+)$"), "AH{idx}__part5"),
    (re.compile(r"^precip_60_to_180_min_period_minutes_(?P<idx>\d+)$"), "AI{idx}__part1"),
    (re.compile(r"^precip_60_to_180_min_amount_mm_(?P<idx>\d+)$"), "AI{idx}__part2"),
    (re.compile(r"^precip_60_to_180_min_condition_code_(?P<idx>\d+)$"), "AI{idx}__part3"),
    (re.compile(r"^precip_60_to_180_min_end_datetime_(?P<idx>\d+)$"), "AI{idx}__part4"),
    (re.compile(r"^precip_60_to_180_min_quality_code_(?P<idx>\d+)$"), "AI{idx}__part5"),
    # Legacy ambiguous short-duration aliases continue to resolve to AH*.
    (re.compile(r"^precip_short_duration_period_minutes_(?P<idx>\d+)$"), "AH{idx}__part1"),
    (re.compile(r"^precip_short_duration_amount_mm_(?P<idx>\d+)$"), "AH{idx}__part2"),
    (re.compile(r"^precip_short_duration_condition_code_(?P<idx>\d+)$"), "AH{idx}__part3"),
    (re.compile(r"^precip_short_duration_end_datetime_(?P<idx>\d+)$"), "AH{idx}__part4"),
    (re.compile(r"^precip_short_duration_quality_code_(?P<idx>\d+)$"), "AH{idx}__part5"),
    (re.compile(r"^snow_depth_monthly_max_(?P<idx>\d+)$"), "AK{idx}__part1"),
    (re.compile(r"^snow_depth_monthly_max_condition_code_(?P<idx>\d+)$"), "AK{idx}__part2"),
    (re.compile(r"^snow_depth_monthly_max_dates_(?P<idx>\d+)$"), "AK{idx}__part3"),
    (re.compile(r"^snow_depth_monthly_max_quality_code_(?P<idx>\d+)$"), "AK{idx}__part4"),
    (re.compile(r"^snow_accum_period_hours_(?P<idx>\d+)$"), "AL{idx}__part1"),
    (re.compile(r"^snow_accum_depth_cm_(?P<idx>\d+)$"), "AL{idx}__part2"),
    (re.compile(r"^snow_accum_condition_code_(?P<idx>\d+)$"), "AL{idx}__part3"),
    (re.compile(r"^snow_accum_quality_code_(?P<idx>\d+)$"), "AL{idx}__part4"),
    (re.compile(r"^snow_accum_24h_max_cm_(?P<idx>\d+)$"), "AM{idx}__part1"),
    (re.compile(r"^snow_accum_24h_max_condition_code_(?P<idx>\d+)$"), "AM{idx}__part2"),
    (re.compile(r"^snow_accum_24h_date_1_(?P<idx>\d+)$"), "AM{idx}__part3"),
    (re.compile(r"^snow_accum_24h_date_2_(?P<idx>\d+)$"), "AM{idx}__part4"),
    (re.compile(r"^snow_accum_24h_date_3_(?P<idx>\d+)$"), "AM{idx}__part5"),
    (re.compile(r"^snow_accum_24h_max_quality_code_(?P<idx>\d+)$"), "AM{idx}__part6"),
    (re.compile(r"^snow_accum_day_month_period_hours_(?P<idx>\d+)$"), "AN{idx}__part1"),
    (re.compile(r"^snow_accum_day_month_depth_cm_(?P<idx>\d+)$"), "AN{idx}__part2"),
    (re.compile(r"^snow_accum_day_month_condition_code_(?P<idx>\d+)$"), "AN{idx}__part3"),
    (re.compile(r"^snow_accum_day_month_quality_code_(?P<idx>\d+)$"), "AN{idx}__part4"),
    (re.compile(r"^precip_minute_period_minutes_(?P<idx>\d+)$"), "AO{idx}__part1"),
    (re.compile(r"^precip_minute_amount_mm_(?P<idx>\d+)$"), "AO{idx}__part2"),
    (re.compile(r"^precip_minute_condition_code_(?P<idx>\d+)$"), "AO{idx}__part3"),
    (re.compile(r"^precip_minute_quality_code_(?P<idx>\d+)$"), "AO{idx}__part4"),
    (re.compile(r"^hpd_gauge_value_mm_(?P<idx>\d+)$"), "AP{idx}__part1"),
    (re.compile(r"^hpd_gauge_condition_code_(?P<idx>\d+)$"), "AP{idx}__part2"),
    (re.compile(r"^hpd_gauge_quality_code_(?P<idx>\d+)$"), "AP{idx}__part3"),
    (re.compile(r"^snow_depth_(?P<idx>\d+)$"), "AJ{idx}__part1"),
    (re.compile(r"^snow_depth_condition_code_(?P<idx>\d+)$"), "AJ{idx}__part2"),
    (re.compile(r"^snow_depth_quality_code_(?P<idx>\d+)$"), "AJ{idx}__part3"),
    (re.compile(r"^snow_water_equivalent_(?P<idx>\d+)$"), "AJ{idx}__part4"),
    (re.compile(r"^snow_water_condition_code_(?P<idx>\d+)$"), "AJ{idx}__part5"),
    (re.compile(r"^snow_water_quality_code_(?P<idx>\d+)$"), "AJ{idx}__part6"),
    (re.compile(r"^daily_present_weather_source_(?P<idx>\d+)$"), "AT{idx}__part1"),
    (re.compile(r"^daily_present_weather_type_code_(?P<idx>\d+)$"), "AT{idx}__part2"),
    (re.compile(r"^daily_present_weather_type_abbr_(?P<idx>\d+)$"), "AT{idx}__part3"),
    (re.compile(r"^daily_present_weather_quality_code_(?P<idx>\d+)$"), "AT{idx}__part4"),
    (re.compile(r"^weather_intensity_code_(?P<idx>\d+)$"), "AU{idx}__part1"),
    (re.compile(r"^weather_descriptor_code_(?P<idx>\d+)$"), "AU{idx}__part2"),
    (re.compile(r"^weather_precip_code_(?P<idx>\d+)$"), "AU{idx}__part3"),
    (re.compile(r"^weather_obscuration_code_(?P<idx>\d+)$"), "AU{idx}__part4"),
    (re.compile(r"^weather_other_code_(?P<idx>\d+)$"), "AU{idx}__part5"),
    (re.compile(r"^weather_combo_indicator_(?P<idx>\d+)$"), "AU{idx}__part6"),
    (re.compile(r"^weather_quality_code_(?P<idx>\d+)$"), "AU{idx}__part7"),
    (re.compile(r"^secondary_precip_period_minutes_(?P<idx>\d+)$"), "CB{idx}__part1"),
    (re.compile(r"^secondary_precip_depth_mm_(?P<idx>\d+)$"), "CB{idx}__part2"),
    (re.compile(r"^secondary_precip_qc_(?P<idx>\d+)$"), "CB{idx}__part3"),
    (re.compile(r"^secondary_precip_flag_(?P<idx>\d+)$"), "CB{idx}__part4"),
    (re.compile(r"^crn_fan_speed_rps_(?P<idx>\d+)$"), "CF{idx}__part1"),
    (re.compile(r"^crn_fan_speed_qc_(?P<idx>\d+)$"), "CF{idx}__part2"),
    (re.compile(r"^crn_fan_speed_flag_(?P<idx>\d+)$"), "CF{idx}__part3"),
    (re.compile(r"^primary_precip_depth_mm_(?P<idx>\d+)$"), "CG{idx}__part1"),
    (re.compile(r"^primary_precip_qc_(?P<idx>\d+)$"), "CG{idx}__part2"),
    (re.compile(r"^primary_precip_flag_(?P<idx>\d+)$"), "CG{idx}__part3"),
    (re.compile(r"^rh_temp_period_minutes_(?P<idx>\d+)$"), "CH{idx}__part1"),
    (re.compile(r"^rh_temp_avg_c_(?P<idx>\d+)$"), "CH{idx}__part2"),
    (re.compile(r"^rh_temp_avg_qc_(?P<idx>\d+)$"), "CH{idx}__part3"),
    (re.compile(r"^rh_temp_avg_flag_(?P<idx>\d+)$"), "CH{idx}__part4"),
    (re.compile(r"^rh_avg_percent_(?P<idx>\d+)$"), "CH{idx}__part5"),
    (re.compile(r"^rh_avg_qc_(?P<idx>\d+)$"), "CH{idx}__part6"),
    (re.compile(r"^rh_avg_flag_(?P<idx>\d+)$"), "CH{idx}__part7"),
    (re.compile(r"^rh_temp_min_c_(?P<idx>\d+)$"), "CI{idx}__part1"),
    (re.compile(r"^rh_temp_min_qc_(?P<idx>\d+)$"), "CI{idx}__part2"),
    (re.compile(r"^rh_temp_min_flag_(?P<idx>\d+)$"), "CI{idx}__part3"),
    (re.compile(r"^rh_temp_max_c_(?P<idx>\d+)$"), "CI{idx}__part4"),
    (re.compile(r"^rh_temp_max_qc_(?P<idx>\d+)$"), "CI{idx}__part5"),
    (re.compile(r"^rh_temp_max_flag_(?P<idx>\d+)$"), "CI{idx}__part6"),
    (re.compile(r"^rh_temp_std_c_(?P<idx>\d+)$"), "CI{idx}__part7"),
    (re.compile(r"^rh_temp_std_qc_(?P<idx>\d+)$"), "CI{idx}__part8"),
    (re.compile(r"^rh_temp_std_flag_(?P<idx>\d+)$"), "CI{idx}__part9"),
    (re.compile(r"^rh_std_percent_(?P<idx>\d+)$"), "CI{idx}__part10"),
    (re.compile(r"^rh_std_qc_(?P<idx>\d+)$"), "CI{idx}__part11"),
    (re.compile(r"^rh_std_flag_(?P<idx>\d+)$"), "CI{idx}__part12"),
    (re.compile(r"^climate_division_number$"), "CO1__part1"),
    (re.compile(r"^utc_lst_offset_hours$"), "CO1__part2"),
    (re.compile(r"^coop_element_id_(?P<idx>[2-9])$"), "CO{idx}__part1"),
    (re.compile(r"^coop_time_offset_hours_(?P<idx>[2-9])$"), "CO{idx}__part2"),
    (re.compile(r"^crn_datalogger_version$"), "CR1__part1"),
    (re.compile(r"^crn_datalogger_version_qc$"), "CR1__part2"),
    (re.compile(r"^crn_datalogger_version_flag$"), "CR1__part3"),
    (re.compile(r"^subhourly_temp_avg_c_(?P<idx>\d+)$"), "CT{idx}__part1"),
    (re.compile(r"^subhourly_temp_avg_qc_(?P<idx>\d+)$"), "CT{idx}__part2"),
    (re.compile(r"^subhourly_temp_avg_flag_(?P<idx>\d+)$"), "CT{idx}__part3"),
    (re.compile(r"^hourly_temp_avg_c_(?P<idx>\d+)$"), "CU{idx}__part1"),
    (re.compile(r"^hourly_temp_avg_qc_(?P<idx>\d+)$"), "CU{idx}__part2"),
    (re.compile(r"^hourly_temp_avg_flag_(?P<idx>\d+)$"), "CU{idx}__part3"),
    (re.compile(r"^hourly_temp_std_c_(?P<idx>\d+)$"), "CU{idx}__part4"),
    (re.compile(r"^hourly_temp_std_qc_(?P<idx>\d+)$"), "CU{idx}__part5"),
    (re.compile(r"^hourly_temp_std_flag_(?P<idx>\d+)$"), "CU{idx}__part6"),
    (re.compile(r"^hourly_temp_min_c_(?P<idx>\d+)$"), "CV{idx}__part1"),
    (re.compile(r"^hourly_temp_min_qc_(?P<idx>\d+)$"), "CV{idx}__part2"),
    (re.compile(r"^hourly_temp_min_flag_(?P<idx>\d+)$"), "CV{idx}__part3"),
    (re.compile(r"^hourly_temp_min_time_hhmm_(?P<idx>\d+)$"), "CV{idx}__part4"),
    (re.compile(r"^hourly_temp_min_time_qc_(?P<idx>\d+)$"), "CV{idx}__part5"),
    (re.compile(r"^hourly_temp_min_time_flag_(?P<idx>\d+)$"), "CV{idx}__part6"),
    (re.compile(r"^hourly_temp_max_c_(?P<idx>\d+)$"), "CV{idx}__part7"),
    (re.compile(r"^hourly_temp_max_qc_(?P<idx>\d+)$"), "CV{idx}__part8"),
    (re.compile(r"^hourly_temp_max_flag_(?P<idx>\d+)$"), "CV{idx}__part9"),
    (re.compile(r"^hourly_temp_max_time_hhmm_(?P<idx>\d+)$"), "CV{idx}__part10"),
    (re.compile(r"^hourly_temp_max_time_qc_(?P<idx>\d+)$"), "CV{idx}__part11"),
    (re.compile(r"^hourly_temp_max_time_flag_(?P<idx>\d+)$"), "CV{idx}__part12"),
    (re.compile(r"^wetness_channel1_value_(?P<idx>\d+)$"), "CW{idx}__part1"),
    (re.compile(r"^wetness_channel1_qc_(?P<idx>\d+)$"), "CW{idx}__part2"),
    (re.compile(r"^wetness_channel1_flag_(?P<idx>\d+)$"), "CW{idx}__part3"),
    (re.compile(r"^wetness_channel2_value_(?P<idx>\d+)$"), "CW{idx}__part4"),
    (re.compile(r"^wetness_channel2_qc_(?P<idx>\d+)$"), "CW{idx}__part5"),
    (re.compile(r"^wetness_channel2_flag_(?P<idx>\d+)$"), "CW{idx}__part6"),
    (re.compile(r"^geonor_precip_total_mm_(?P<idx>\d+)$"), "CX{idx}__part1"),
    (re.compile(r"^geonor_precip_qc_(?P<idx>\d+)$"), "CX{idx}__part2"),
    (re.compile(r"^geonor_precip_flag_(?P<idx>\d+)$"), "CX{idx}__part3"),
    (re.compile(r"^geonor_freq_avg_hz_(?P<idx>\d+)$"), "CX{idx}__part4"),
    (re.compile(r"^geonor_freq_avg_qc_(?P<idx>\d+)$"), "CX{idx}__part5"),
    (re.compile(r"^geonor_freq_avg_flag_(?P<idx>\d+)$"), "CX{idx}__part6"),
    (re.compile(r"^geonor_freq_min_hz_(?P<idx>\d+)$"), "CX{idx}__part7"),
    (re.compile(r"^geonor_freq_min_qc_(?P<idx>\d+)$"), "CX{idx}__part8"),
    (re.compile(r"^geonor_freq_min_flag_(?P<idx>\d+)$"), "CX{idx}__part9"),
    (re.compile(r"^geonor_freq_max_hz_(?P<idx>\d+)$"), "CX{idx}__part10"),
    (re.compile(r"^geonor_freq_max_qc_(?P<idx>\d+)$"), "CX{idx}__part11"),
    (re.compile(r"^geonor_freq_max_flag_(?P<idx>\d+)$"), "CX{idx}__part12"),
    (re.compile(r"^battery_voltage_avg_v_1$"), "CN1__part1"),
    (re.compile(r"^battery_voltage_avg_qc_1$"), "CN1__part2"),
    (re.compile(r"^battery_voltage_avg_flag_1$"), "CN1__part3"),
    (re.compile(r"^battery_voltage_full_load_v_1$"), "CN1__part4"),
    (re.compile(r"^battery_voltage_full_load_qc_1$"), "CN1__part5"),
    (re.compile(r"^battery_voltage_full_load_flag_1$"), "CN1__part6"),
    (re.compile(r"^battery_voltage_datalogger_v_1$"), "CN1__part7"),
    (re.compile(r"^battery_voltage_datalogger_qc_1$"), "CN1__part8"),
    (re.compile(r"^battery_voltage_datalogger_flag_1$"), "CN1__part9"),
    (re.compile(r"^panel_temp_c_1$"), "CN2__part1"),
    (re.compile(r"^panel_temp_qc_1$"), "CN2__part2"),
    (re.compile(r"^panel_temp_flag_1$"), "CN2__part3"),
    (re.compile(r"^inlet_temp_max_c_1$"), "CN2__part4"),
    (re.compile(r"^inlet_temp_max_qc_1$"), "CN2__part5"),
    (re.compile(r"^inlet_temp_max_flag_1$"), "CN2__part6"),
    (re.compile(r"^door_open_minutes_1$"), "CN2__part7"),
    (re.compile(r"^door_open_qc_1$"), "CN2__part8"),
    (re.compile(r"^door_open_flag_1$"), "CN2__part9"),
    (re.compile(r"^reference_resistance_ohm_1$"), "CN3__part1"),
    (re.compile(r"^reference_resistance_qc_1$"), "CN3__part2"),
    (re.compile(r"^reference_resistance_flag_1$"), "CN3__part3"),
    (re.compile(r"^datalogger_signature_1$"), "CN3__part4"),
    (re.compile(r"^datalogger_signature_qc_1$"), "CN3__part5"),
    (re.compile(r"^datalogger_signature_flag_1$"), "CN3__part6"),
    (re.compile(r"^precip_heater_flag_1$"), "CN4__part1"),
    (re.compile(r"^precip_heater_qc_1$"), "CN4__part2"),
    (re.compile(r"^precip_heater_flag_code_1$"), "CN4__part3"),
    (re.compile(r"^datalogger_door_flag_1$"), "CN4__part4"),
    (re.compile(r"^datalogger_door_flag_qc_1$"), "CN4__part5"),
    (re.compile(r"^datalogger_door_flag_code_1$"), "CN4__part6"),
    (re.compile(r"^forward_transmitter_wattage_1$"), "CN4__part7"),
    (re.compile(r"^forward_transmitter_qc_1$"), "CN4__part8"),
    (re.compile(r"^forward_transmitter_flag_1$"), "CN4__part9"),
    (re.compile(r"^reflected_transmitter_wattage_1$"), "CN4__part10"),
    (re.compile(r"^reflected_transmitter_qc_1$"), "CN4__part11"),
    (re.compile(r"^reflected_transmitter_flag_1$"), "CN4__part12"),
    (re.compile(r"^cloud_layer_coverage_(?P<idx>\d+)$"), "GA{idx}__part1"),
    (re.compile(r"^cloud_layer_coverage_quality_code_(?P<idx>\d+)$"), "GA{idx}__part2"),
    (re.compile(r"^cloud_layer_base_height_m_(?P<idx>\d+)$"), "GA{idx}__part3"),
    (re.compile(r"^cloud_layer_base_height_quality_code_(?P<idx>\d+)$"), "GA{idx}__part4"),
    (re.compile(r"^cloud_layer_type_code_(?P<idx>\d+)$"), "GA{idx}__part5"),
    (re.compile(r"^cloud_layer_type_quality_code_(?P<idx>\d+)$"), "GA{idx}__part6"),
    (re.compile(r"^extreme_temp_c_(?P<idx>\d+)$"), "KA{idx}__part3"),
    (re.compile(r"^extreme_temp_type_(?P<idx>\d+)$"), "KA{idx}__part2"),
    (re.compile(r"^extreme_temp_period_hours_(?P<idx>\d+)$"), "KA{idx}__part1"),
    (re.compile(r"^extreme_temp_quality_code_(?P<idx>\d+)$"), "KA{idx}__part4"),
    (re.compile(r"^avg_air_temp_period_hours_(?P<idx>\d+)$"), "KB{idx}__part1"),
    (re.compile(r"^avg_air_temp_type_(?P<idx>\d+)$"), "KB{idx}__part2"),
    (re.compile(r"^avg_air_temp_c_(?P<idx>\d+)$"), "KB{idx}__part3"),
    (re.compile(r"^avg_air_temp_quality_code_(?P<idx>\d+)$"), "KB{idx}__part4"),
    (re.compile(r"^extreme_month_temp_type_(?P<idx>\d+)$"), "KC{idx}__part1"),
    (re.compile(r"^extreme_month_temp_condition_(?P<idx>\d+)$"), "KC{idx}__part2"),
    (re.compile(r"^extreme_month_temp_c_(?P<idx>\d+)$"), "KC{idx}__part3"),
    (re.compile(r"^extreme_month_temp_dates_(?P<idx>\d+)$"), "KC{idx}__part4"),
    (re.compile(r"^extreme_month_temp_quality_code_(?P<idx>\d+)$"), "KC{idx}__part5"),
    (re.compile(r"^degree_days_period_hours_(?P<idx>\d+)$"), "KD{idx}__part1"),
    (re.compile(r"^degree_days_type_(?P<idx>\d+)$"), "KD{idx}__part2"),
    (re.compile(r"^degree_days_value_(?P<idx>\d+)$"), "KD{idx}__part3"),
    (re.compile(r"^degree_days_quality_code_(?P<idx>\d+)$"), "KD{idx}__part4"),
    (re.compile(r"^avg_dew_wet_period_hours_(?P<idx>\d+)$"), "KG{idx}__part1"),
    (re.compile(r"^avg_dew_wet_type_(?P<idx>\d+)$"), "KG{idx}__part2"),
    (re.compile(r"^avg_dew_wet_temp_c_(?P<idx>\d+)$"), "KG{idx}__part3"),
    (re.compile(r"^avg_dew_wet_derived_code_(?P<idx>\d+)$"), "KG{idx}__part4"),
    (re.compile(r"^avg_dew_wet_quality_code_(?P<idx>\d+)$"), "KG{idx}__part5"),
    (re.compile(r"^soil_temp_type_code$"), "ST1__part1"),
    (re.compile(r"^soil_temp_c$"), "ST1__part2"),
    (re.compile(r"^soil_temp_quality_code$"), "ST1__part3"),
    (re.compile(r"^soil_temp_depth_cm$"), "ST1__part4"),
    (re.compile(r"^soil_temp_depth_quality_code$"), "ST1__part5"),
    (re.compile(r"^soil_temp_cover_code$"), "ST1__part6"),
    (re.compile(r"^soil_temp_cover_quality_code$"), "ST1__part7"),
    (re.compile(r"^soil_temp_subplot$"), "ST1__part8"),
    (re.compile(r"^soil_temp_subplot_quality_code$"), "ST1__part9"),
    (re.compile(r"^geopotential_isobaric_code$"), "ME1__part1"),
    (re.compile(r"^geopotential_height_m$"), "ME1__part2"),
    (re.compile(r"^geopotential_height_quality_code$"), "ME1__part3"),
    (re.compile(r"^station_pressure_day_avg_hpa$"), "MF1__part1"),
    (re.compile(r"^station_pressure_day_avg_quality_code$"), "MF1__part2"),
    (re.compile(r"^sea_level_pressure_day_avg_hpa$"), "MF1__part3"),
    (re.compile(r"^sea_level_pressure_day_avg_quality_code$"), "MF1__part4"),
    (re.compile(r"^station_pressure_day_hpa$"), "MG1__part1"),
    (re.compile(r"^station_pressure_day_quality_code$"), "MG1__part2"),
    (re.compile(r"^sea_level_pressure_day_min_hpa$"), "MG1__part3"),
    (re.compile(r"^sea_level_pressure_day_min_quality_code$"), "MG1__part4"),
    (re.compile(r"^station_pressure_month_avg_hpa$"), "MH1__part1"),
    (re.compile(r"^station_pressure_month_avg_quality_code$"), "MH1__part2"),
    (re.compile(r"^sea_level_pressure_month_avg_hpa$"), "MH1__part3"),
    (re.compile(r"^sea_level_pressure_month_avg_quality_code$"), "MH1__part4"),
    (re.compile(r"^sea_level_pressure_month_max_hpa$"), "MK1__part1"),
    (re.compile(r"^sea_level_pressure_month_max_datetime$"), "MK1__part2"),
    (re.compile(r"^sea_level_pressure_month_max_quality_code$"), "MK1__part3"),
    (re.compile(r"^sea_level_pressure_month_min_hpa$"), "MK1__part4"),
    (re.compile(r"^sea_level_pressure_month_min_datetime$"), "MK1__part5"),
    (re.compile(r"^sea_level_pressure_month_min_quality_code$"), "MK1__part6"),
    (re.compile(r"^sky_cover_summation_code_(?P<idx>\d+)$"), "GD{idx}__part1"),
    (re.compile(r"^sky_cover_summation_okta_code_(?P<idx>\d+)$"), "GD{idx}__part2"),
    (re.compile(r"^sky_cover_summation_quality_code_(?P<idx>\d+)$"), "GD{idx}__part3"),
    (re.compile(r"^sky_cover_summation_height_m_(?P<idx>\d+)$"), "GD{idx}__part4"),
    (re.compile(r"^sky_cover_summation_height_quality_code_(?P<idx>\d+)$"), "GD{idx}__part5"),
    (re.compile(r"^sky_cover_summation_characteristic_code_(?P<idx>\d+)$"), "GD{idx}__part6"),
    (re.compile(r"^below_station_cloud_coverage_(?P<idx>\d+)$"), "GG{idx}__part1"),
    (re.compile(r"^below_station_cloud_coverage_quality_code_(?P<idx>\d+)$"), "GG{idx}__part2"),
    (re.compile(r"^below_station_cloud_top_height_m_(?P<idx>\d+)$"), "GG{idx}__part3"),
    (re.compile(r"^below_station_cloud_top_height_quality_code_(?P<idx>\d+)$"), "GG{idx}__part4"),
    (re.compile(r"^below_station_cloud_type_code_(?P<idx>\d+)$"), "GG{idx}__part5"),
    (re.compile(r"^below_station_cloud_type_quality_code_(?P<idx>\d+)$"), "GG{idx}__part6"),
    (re.compile(r"^below_station_cloud_top_code_(?P<idx>\d+)$"), "GG{idx}__part7"),
    (re.compile(r"^below_station_cloud_top_quality_code_(?P<idx>\d+)$"), "GG{idx}__part8"),
    (re.compile(r"^solar_radiation_avg_wm2_(?P<idx>\d+)$"), "GH{idx}__part1"),
    (re.compile(r"^solar_radiation_avg_qc_(?P<idx>\d+)$"), "GH{idx}__part2"),
    (re.compile(r"^solar_radiation_avg_flag_(?P<idx>\d+)$"), "GH{idx}__part3"),
    (re.compile(r"^solar_radiation_min_wm2_(?P<idx>\d+)$"), "GH{idx}__part4"),
    (re.compile(r"^solar_radiation_min_qc_(?P<idx>\d+)$"), "GH{idx}__part5"),
    (re.compile(r"^solar_radiation_min_flag_(?P<idx>\d+)$"), "GH{idx}__part6"),
    (re.compile(r"^solar_radiation_max_wm2_(?P<idx>\d+)$"), "GH{idx}__part7"),
    (re.compile(r"^solar_radiation_max_qc_(?P<idx>\d+)$"), "GH{idx}__part8"),
    (re.compile(r"^solar_radiation_max_flag_(?P<idx>\d+)$"), "GH{idx}__part9"),
    (re.compile(r"^solar_radiation_std_wm2_(?P<idx>\d+)$"), "GH{idx}__part10"),
    (re.compile(r"^solar_radiation_std_qc_(?P<idx>\d+)$"), "GH{idx}__part11"),
    (re.compile(r"^solar_radiation_std_flag_(?P<idx>\d+)$"), "GH{idx}__part12"),
    (re.compile(r"^sunshine_duration_minutes_(?P<idx>\d+)$"), "GJ{idx}__part1"),
    (re.compile(r"^sunshine_duration_quality_code_(?P<idx>\d+)$"), "GJ{idx}__part2"),
    (re.compile(r"^sunshine_percent_(?P<idx>\d+)$"), "GK{idx}__part1"),
    (re.compile(r"^sunshine_percent_quality_code_(?P<idx>\d+)$"), "GK{idx}__part2"),
    (re.compile(r"^sunshine_month_minutes_(?P<idx>\d+)$"), "GL{idx}__part1"),
    (re.compile(r"^sunshine_month_quality_code_(?P<idx>\d+)$"), "GL{idx}__part2"),
    (re.compile(r"^solar_irradiance_period_minutes_(?P<idx>\d+)$"), "GM{idx}__part1"),
    (re.compile(r"^global_irradiance_wm2_(?P<idx>\d+)$"), "GM{idx}__part2"),
    (re.compile(r"^global_irradiance_flag_(?P<idx>\d+)$"), "GM{idx}__part3"),
    (re.compile(r"^global_irradiance_quality_code_(?P<idx>\d+)$"), "GM{idx}__part4"),
    (re.compile(r"^direct_beam_irradiance_wm2_(?P<idx>\d+)$"), "GM{idx}__part5"),
    (re.compile(r"^direct_beam_irradiance_flag_(?P<idx>\d+)$"), "GM{idx}__part6"),
    (re.compile(r"^direct_beam_irradiance_quality_code_(?P<idx>\d+)$"), "GM{idx}__part7"),
    (re.compile(r"^diffuse_irradiance_wm2_(?P<idx>\d+)$"), "GM{idx}__part8"),
    (re.compile(r"^diffuse_irradiance_flag_(?P<idx>\d+)$"), "GM{idx}__part9"),
    (re.compile(r"^diffuse_irradiance_quality_code_(?P<idx>\d+)$"), "GM{idx}__part10"),
    (re.compile(r"^uvb_global_irradiance_mw_m2_(?P<idx>\d+)$"), "GM{idx}__part11"),
    (re.compile(r"^uvb_global_irradiance_quality_code_(?P<idx>\d+)$"), "GM{idx}__part12"),
    (re.compile(r"^solar_radiation_period_minutes_(?P<idx>\d+)$"), "GN{idx}__part1"),
    (re.compile(r"^upwelling_global_solar_radiation_mw_m2_(?P<idx>\d+)$"), "GN{idx}__part2"),
    (re.compile(r"^upwelling_global_solar_radiation_quality_code_(?P<idx>\d+)$"), "GN{idx}__part3"),
    (re.compile(r"^downwelling_thermal_ir_mw_m2_(?P<idx>\d+)$"), "GN{idx}__part4"),
    (re.compile(r"^downwelling_thermal_ir_quality_code_(?P<idx>\d+)$"), "GN{idx}__part5"),
    (re.compile(r"^upwelling_thermal_ir_mw_m2_(?P<idx>\d+)$"), "GN{idx}__part6"),
    (re.compile(r"^upwelling_thermal_ir_quality_code_(?P<idx>\d+)$"), "GN{idx}__part7"),
    (re.compile(r"^photosynthetic_radiation_mw_m2_(?P<idx>\d+)$"), "GN{idx}__part8"),
    (re.compile(r"^photosynthetic_radiation_quality_code_(?P<idx>\d+)$"), "GN{idx}__part9"),
    (re.compile(r"^solar_zenith_angle_deg_(?P<idx>\d+)$"), "GN{idx}__part10"),
    (re.compile(r"^solar_zenith_angle_quality_code_(?P<idx>\d+)$"), "GN{idx}__part11"),
    (re.compile(r"^net_radiation_period_minutes_(?P<idx>\d+)$"), "GO{idx}__part1"),
    (re.compile(r"^net_solar_radiation_wm2_(?P<idx>\d+)$"), "GO{idx}__part2"),
    (re.compile(r"^net_solar_radiation_quality_code_(?P<idx>\d+)$"), "GO{idx}__part3"),
    (re.compile(r"^net_infrared_radiation_wm2_(?P<idx>\d+)$"), "GO{idx}__part4"),
    (re.compile(r"^net_infrared_radiation_quality_code_(?P<idx>\d+)$"), "GO{idx}__part5"),
    (re.compile(r"^net_radiation_wm2_(?P<idx>\d+)$"), "GO{idx}__part6"),
    (re.compile(r"^net_radiation_quality_code_(?P<idx>\d+)$"), "GO{idx}__part7"),
    (re.compile(r"^modeled_solar_period_minutes$"), "GP1__part1"),
    (re.compile(r"^modeled_global_horizontal_wm2$"), "GP1__part2"),
    (re.compile(r"^modeled_global_horizontal_source_flag$"), "GP1__part3"),
    (re.compile(r"^modeled_global_horizontal_uncertainty_pct$"), "GP1__part4"),
    (re.compile(r"^modeled_direct_normal_wm2$"), "GP1__part5"),
    (re.compile(r"^modeled_direct_normal_source_flag$"), "GP1__part6"),
    (re.compile(r"^modeled_direct_normal_uncertainty_pct$"), "GP1__part7"),
    (re.compile(r"^modeled_diffuse_horizontal_wm2$"), "GP1__part8"),
    (re.compile(r"^modeled_diffuse_horizontal_source_flag$"), "GP1__part9"),
    (re.compile(r"^modeled_diffuse_horizontal_uncertainty_pct$"), "GP1__part10"),
    (re.compile(r"^extraterrestrial_radiation_period_minutes$"), "GR1__part1"),
    (re.compile(r"^extraterrestrial_radiation_horizontal_wm2$"), "GR1__part2"),
    (re.compile(r"^extraterrestrial_radiation_horizontal_quality_code$"), "GR1__part3"),
    (re.compile(r"^extraterrestrial_radiation_normal_wm2$"), "GR1__part4"),
    (re.compile(r"^extraterrestrial_radiation_normal_quality_code$"), "GR1__part5"),
    (re.compile(r"^supp_wind_oa_type_code_(?P<idx>\d+)$"), "OA{idx}__part1"),
    (re.compile(r"^supp_wind_oa_period_hours_(?P<idx>\d+)$"), "OA{idx}__part2"),
    (re.compile(r"^supp_wind_oa_speed_ms_(?P<idx>\d+)$"), "OA{idx}__part3"),
    (re.compile(r"^supp_wind_oa_speed_quality_code_(?P<idx>\d+)$"), "OA{idx}__part4"),
    (re.compile(r"^supp_wind_type_code_(?P<idx>\d+)$"), "OD{idx}__part1"),
    (re.compile(r"^supp_wind_period_hours_(?P<idx>\d+)$"), "OD{idx}__part2"),
    (re.compile(r"^supp_wind_direction_deg_(?P<idx>\d+)$"), "OD{idx}__part3"),
    (re.compile(r"^supp_wind_speed_ms_(?P<idx>\d+)$"), "OD{idx}__part4"),
    (re.compile(r"^supp_wind_speed_quality_code_(?P<idx>\d+)$"), "OD{idx}__part5"),
    (re.compile(r"^wind_avg_period_minutes_(?P<idx>\d+)$"), "OB{idx}__part1"),
    (re.compile(r"^wind_max_gust_ms_(?P<idx>\d+)$"), "OB{idx}__part2"),
    (re.compile(r"^wind_max_gust_qc_(?P<idx>\d+)$"), "OB{idx}__part3"),
    (re.compile(r"^wind_max_gust_flag_(?P<idx>\d+)$"), "OB{idx}__part4"),
    (re.compile(r"^wind_max_direction_deg_(?P<idx>\d+)$"), "OB{idx}__part5"),
    (re.compile(r"^wind_max_direction_qc_(?P<idx>\d+)$"), "OB{idx}__part6"),
    (re.compile(r"^wind_max_direction_flag_(?P<idx>\d+)$"), "OB{idx}__part7"),
    (re.compile(r"^wind_speed_std_ms_(?P<idx>\d+)$"), "OB{idx}__part8"),
    (re.compile(r"^wind_speed_std_qc_(?P<idx>\d+)$"), "OB{idx}__part9"),
    (re.compile(r"^wind_speed_std_flag_(?P<idx>\d+)$"), "OB{idx}__part10"),
    (re.compile(r"^wind_direction_std_deg_(?P<idx>\d+)$"), "OB{idx}__part11"),
    (re.compile(r"^wind_direction_std_qc_(?P<idx>\d+)$"), "OB{idx}__part12"),
    (re.compile(r"^wind_direction_std_flag_(?P<idx>\d+)$"), "OB{idx}__part13"),
    (re.compile(r"^eqd_original_value_q(?P<idx>\d+)$"), "Q{idx}__part1"),
    (re.compile(r"^eqd_reason_code_q(?P<idx>\d+)$"), "Q{idx}__part2"),
    (re.compile(r"^eqd_parameter_code_q(?P<idx>\d+)$"), "Q{idx}__part3"),
    (re.compile(r"^eqd_original_value_p(?P<idx>\d+)$"), "P{idx}__part1"),
    (re.compile(r"^eqd_reason_code_p(?P<idx>\d+)$"), "P{idx}__part2"),
    (re.compile(r"^eqd_parameter_code_p(?P<idx>\d+)$"), "P{idx}__part3"),
    (re.compile(r"^eqd_original_value_r(?P<idx>\d+)$"), "R{idx}__part1"),
    (re.compile(r"^eqd_reason_code_r(?P<idx>\d+)$"), "R{idx}__part2"),
    (re.compile(r"^eqd_parameter_code_r(?P<idx>\d+)$"), "R{idx}__part3"),
    (re.compile(r"^eqd_original_value_c(?P<idx>\d+)$"), "C{idx}__part1"),
    (re.compile(r"^eqd_reason_code_c(?P<idx>\d+)$"), "C{idx}__part2"),
    (re.compile(r"^eqd_parameter_code_c(?P<idx>\d+)$"), "C{idx}__part3"),
    (re.compile(r"^eqd_original_value_d(?P<idx>\d+)$"), "D{idx}__part1"),
    (re.compile(r"^eqd_reason_code_d(?P<idx>\d+)$"), "D{idx}__part2"),
    (re.compile(r"^eqd_parameter_code_d(?P<idx>\d+)$"), "D{idx}__part3"),
    (re.compile(r"^eqd_original_value_n(?P<idx>\d+)$"), "N{idx}__part1"),
    (re.compile(r"^eqd_units_code_n(?P<idx>\d+)$"), "N{idx}__part2"),
    (re.compile(r"^eqd_parameter_code_n(?P<idx>\d+)$"), "N{idx}__part3"),
    (re.compile(r"^summary_wind_type_code_(?P<idx>\d+)$"), "OE{idx}__part1"),
    (re.compile(r"^summary_wind_period_hours_(?P<idx>\d+)$"), "OE{idx}__part2"),
    (re.compile(r"^summary_wind_speed_ms_(?P<idx>\d+)$"), "OE{idx}__part3"),
    (re.compile(r"^summary_wind_direction_deg_(?P<idx>\d+)$"), "OE{idx}__part4"),
    (re.compile(r"^summary_wind_time_hhmm_(?P<idx>\d+)$"), "OE{idx}__part5"),
    (re.compile(r"^summary_wind_quality_code_(?P<idx>\d+)$"), "OE{idx}__part6"),
    (re.compile(r"^relative_humidity_period_hours_(?P<idx>\d+)$"), "RH{idx}__part1"),
    (re.compile(r"^relative_humidity_code_(?P<idx>\d+)$"), "RH{idx}__part2"),
    (re.compile(r"^relative_humidity_percent_(?P<idx>\d+)$"), "RH{idx}__part3"),
    (re.compile(r"^relative_humidity_derived_code_(?P<idx>\d+)$"), "RH{idx}__part4"),
    (re.compile(r"^relative_humidity_quality_code_(?P<idx>\d+)$"), "RH{idx}__part5"),
]

_INTERNAL_COLUMN_MAP = {v: k for k, v in FRIENDLY_COLUMN_MAP.items()}

FIELD_REGISTRY: dict[str, FieldRegistryEntry] = {}


def _parse_expanded_col(col: str) -> tuple[str, str] | None:
    """Return (field_prefix, suffix) for an expanded column, or None."""
    m = _EXPANDED_COL_RE.match(col)
    if m:
        return m.group("field"), m.group("suffix")
    return None


def to_friendly_column(col: str) -> str:
    mapped = FRIENDLY_COLUMN_MAP.get(col)
    if mapped:
        return mapped
    for pattern, template in _FRIENDLY_PATTERNS:
        match = pattern.match(col)
        if match:
            return template.format(**match.groupdict())
    return col


def to_internal_column(col: str) -> str:
    mapped = _INTERNAL_COLUMN_MAP.get(col)
    if mapped:
        return mapped
    for pattern, template in _INTERNAL_PATTERNS:
        match = pattern.match(col)
        if match:
            return template.format(**match.groupdict())
    return col


def _internal_name(prefix: str, part_idx: int, suffix: str) -> str:
    if suffix == "value":
        return f"{prefix}__value"
    return f"{prefix}__part{part_idx}"


def get_field_registry_entry(
    prefix: str,
    part_idx: int,
    suffix: str = "part",
) -> FieldRegistryEntry | None:
    internal_name = _internal_name(prefix, part_idx, suffix)
    entry = FIELD_REGISTRY.get(internal_name)
    if entry is not None:
        return entry
    rule = get_field_rule(prefix)
    if rule is None:
        return None
    part_rule = rule.parts.get(part_idx)
    if part_rule is None:
        return None
    entry = FieldRegistryEntry(
        code=prefix,
        part=part_idx,
        internal_name=internal_name,
        name=to_friendly_column(internal_name),
        kind=part_rule.kind,
        scale=part_rule.scale,
        missing_values=part_rule.missing_values,
        quality_part=part_rule.quality_part,
        agg=part_rule.agg,
    )
    FIELD_REGISTRY[internal_name] = entry
    return entry


def is_quality_column(col: str) -> bool:
    """True for observation-level quality columns (e.g. WND__quality)."""
    internal = to_internal_column(col)
    return internal.endswith("__quality") or internal.endswith("__qc")


def is_categorical_column(col: str) -> bool:
    """True if the column is a WMO/ISD category code that must not be averaged."""
    parsed = _parse_expanded_col(to_internal_column(col))
    if parsed is None:
        return False
    field_prefix, suffix = parsed
    rule = get_field_rule(field_prefix)
    if rule is None:
        return False
    # Match suffix like "part3" or "value"
    if suffix == "value":
        part_idx = 1
    elif suffix.startswith("part"):
        try:
            part_idx = int(suffix[4:])
        except ValueError:
            return False
    else:
        return False
    part_rule = rule.parts.get(part_idx)
    if part_rule and part_rule.kind in {"categorical", "quality"}:
        return True
    return False


def get_agg_func(col: str) -> str:
    """Return the preferred aggregation function name for *col*.

    Returns one of: ``"mean"``, ``"max"``, ``"min"``, ``"mode"``,
    ``"sum"``, ``"drop"``, ``"circular_mean"``.  Defaults to ``"mean"`` for columns that
    have no explicit rule.
    """
    if is_quality_column(col):
        return "drop"
    parsed = _parse_expanded_col(to_internal_column(col))
    if parsed is None:
        return "mean"
    field_prefix, suffix = parsed
    rule = get_field_rule(field_prefix)
    if rule is None:
        return "mean"
    if suffix == "value":
        part_idx = 1
    elif suffix.startswith("part"):
        try:
            part_idx = int(suffix[4:])
        except ValueError:
            return "mean"
    else:
        return "mean"
    part_rule = rule.parts.get(part_idx)
    if part_rule:
        return part_rule.agg
    return "mean"
