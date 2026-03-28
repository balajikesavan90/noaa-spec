## Part 5 - Weather Occurrence Data

Weather Occurrence Data
FLD LEN: 3
    PRESENT-WEATHER-OBSERVATION automated occurrence identifier for ASOS/AWOS data
    The identifier that signifies the reporting of present weather.
    DOM: A specific domain comprised of the ASCII characters.
    AT1 – AT8: An indicator of up to 8 repeating fields of the following items:
    DAILY-PRESENT-WEATHER-OBSERVATION source element



    27


---

    DAILY-PRESENT-WEATHER-OBSERVATION weather type
    DAILY-PRESENT-WEATHER-OBSERVATION weather type abbreviation
    DAILY-PRESENT-WEATHER-OBSERVATION quality code

FLD LEN: 2
    DAILY-PRESENT-WEATHER-OBSERVATION source element
    The code that denotes the source of the daily present weather observation.
    DOM: A specific domain comprised of the ASCII characters.
    AU = sourced from automated ASOS/AWOS sensors
    AW = sourced from automated sensors
    MW = sourced from manually reported present weather

FLD LEN: 2
    DAILY-PRESENT-WEATHER-OBSERVATION weather type
    The numeric code that denotes the type of daily present weather being reported.
    DOM: A specific domain comprised of the ASCII characters.
    01 = Fog, ice fog or freezing fog (may include heavy fog)
    02 = Heavy fog or heavy freezing fog (not always distinguished from fog)
    03 = Thunder
    04 = Ice pellets, sleet, snow pellets or small hail
    05 = Hail (may include small hail)
    06 = Glaze or rime
    07 = Dust, volcanic ash, blowing dust, blowing sand or blowing obstruction
    08 = Smoke or haze
    09 = Blowing or drifting snow
    10 = Tornado, water spout or funnel cloud
    11 = High or damaging winds
    12 = Blowing spray
    13 = Mist
    14 = Drizzle
    15 = Freezing drizzle
    16 = Rain
    17 = Freezing rain
    18 = Snow, snow pellets, snow grains or ice crystals
    19 = Unknown precipitation
    21 = Ground fog
    22 = Ice fog or freezing fog

FLD LEN: 4
    DAILY-PRESENT-WEATHER-OBSERVATION weather type abbreviation
    The abbreviation that denotes the type of daily present weather being reported. These abbreviations correspond to the
    Daily Present Weather Observation weather type.
    DOM: A specific domain comprised of the ASCII characters.
    FG = Fog, ice fog or freezing fog (may include heavy fog)
    FG+ = Heavy fog or heavy freezing fog (not always distinguished from fog)
    TS = Thunder
    PL = Ice pellets, sleet, snow pellets or small hail
    GR = Hail (may include small hail)
    GL = Glaze or rime
    DU = Dust, volcanic ash, blowing dust, blowing sand or blowing obstruction
    HZ = Smoke or haze
    BLSN = Blowing or drifting snow
    FC = Tornado, water spout or funnel cloud
    WIND = High or damaging winds
    BLPY = Blowing spray
    BR = Mist
    DZ = Drizzle
    FZDZ = Freezing drizzle
    RA = Rain
    FZRA = Freezing rain
    SN = Snow, snow pellets, snow grains or ice crystals
    UP = Unknown precipitation
    MIFG = Ground fog
    FZFG = Ice fog or freezing fog

FLD LEN: 1
    DAILY-PRESENT-WEATHER-OBSERVATION quality code
    The code that denotes a quality status of the reported DAILY-PRESENT-WEATHER-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.



    28


---

    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    M = Manual change made to value based on information provided by NWS or FAA
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

AU1 – AU9 An indicator of up to 9 repeating fields of the following items:
    PRESENT-WEATHER-OBSERVATION intensity code
    PRESENT-WEATHER-OBSERVATION descriptor code
    PRESENT-WEATHER-OBSERVATION precipitation code
    PRESENT-WEATHER-OBSERVATION obscuration code
    PRESENT-WEATHER-OBSERVATION other weather phenomena code
    PRESENT-WEATHER-OBSERVATION combination indicator code
    PRESENT-WEATHER-OBSERVATION quality code

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION intensity and proximity code
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Not Reported
    1 = Light (-)
    2 = Moderate or Not Reported (no entry in original observation)
    3 = Heavy (+)
    4 = Vicinity (VC)
    9 = Missing

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION descriptor code
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = No Descriptor
    1 = Shallow (MI)
    2 = Partial (PR)
    3 = Patches (BC)
    4 = Low Drifting (DR)
    5 = Blowing (BL)
    6 = Shower(s) (SH)
    7 = Thunderstorm (TS)
    8 = Freezing (FZ)
    9 = Missing

FLD LEN: 2
    PRESENT-WEATHER-OBSERVATION precipitation code
    DOM: A specific domain comprised of the characters in the ASCII character set.
    00 = No Precipitation
    01 = Drizzle (DZ)
    02 = Rain (RA)
    03 = Snow (SN)
    04 = Snow Grains (SG)
    05 = Ice Crystals (IC)
    06 = Ice Pellets (PL)
    07 = Hail (GR)
    08 = Small Hail and/or Snow Pellets (GS)
    09 = Unknown Precipitation (UP)
    99 = Missing




    29


---

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION obscuration code
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = No Obscuration
    1 = Mist (BR)
    2 = Fog (FG)
    3 = Smoke (FU)
    4 = Volcanic Ash (VA)
    5 = Widespread Dust (DU)
    6 = Sand (SA)
    7 = Haze (HZ)
    8 = Spray (PY)
    9 = Missing

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION other weather phenomena code
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = None Reported
    1 = Well-Developed Dust/Sand Whirls (PO)
    2 = Squalls (SQ)
    3 = Funnel Cloud, Tornado, Waterspout (FC)
    4 = Sandstorm (SS)
    5 = Duststorm (DS)
    9 = Missing

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION combination indicator code
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Not part of combined weather elements
    2 = Beginning element of combined weather elements
    3 = Combined with previous weather element to form a single weather report
    9 = Missing

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION quality code
    The code that denotes a quality status of the reported PRESENT-WEATHER-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    M = Manual change made to value based on information provided by NWS or FAA
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PRESENT-WEATHER-OBSERVATION automated occurrence identifier
    The identifier that signifies the reporting of present weather.
    DOM: A specific domain comprised of the ASCII character
    AW1 First automated weather report
    AW2 Second automated weather report
    AW3 Third automated weather report
    AW4 Fourth automated weather report
    PRESENT-WEATHER-OBSERVATION automated atmospheric condition code
    PRESENT-WEATHER-OBSERVATION quality automated atmospheric condition code

FLD LEN: 2
    PRESENT-WEATHER-OBSERVATION automated atmospheric condition code
    The code that denotes a specific type of weather reported by an automated device.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    00 = No significant weather observed
    01 = Clouds generally dissolving or becoming less developed
    02 = State of sky on the whole unchanged during the past hour
    03 = Clouds generally forming or developing during the past hour



    30


---

04 = Haze, smoke, or dust in suspension in the air, visibility equal to or greater than 1km
05 = Smoke
07 = Dust or sand raised by wind at or near the station at the time of observation, but no well-developed dust irl(s)
    whirls(s) or sand whirl(s), and no duststorm or sandstorm seen or, in the case of ships, blowing spray at the
   station
10 = Mist
11 = Diamond dust
12 = Distant lightning
18 = Squalls

(Code figures 20-26 are used to report precipitation, fog, thunderstorm at the station during the preceding hour,
but not at the time of observation.)

20 = Fog
21 = Precipitation
22 = Drizzle (not freezing) or snow grains
23 = Rain (not freezing)
24 = Snow
25 = Freezing drizzle or freezing rain
26 = Thunderstorm (with or without precipitation)
27 = Blowing or drifting snow or sand
28 = Blowing or drifting snow or sand, visibility equal to or greater than 1 km
29 = Blowing or drifting snow or sand, visibility less than 1 km
30 = Fog
31 = Fog or ice fog in patches
32 = Fog or ice fog, has become thinner during the past hour
33 = Fog or ice fog, no appreciable change during the past hour
34 = Fog or ice fog, has begun or become thicker during the past hour
35 = Fog, depositing rime
40 = Precipitation
41 = Precipitation, slight or moderate
42 = Precipitation, heavy
43 = Liquid precipitation, slight or moderate
44 = Liquid precipitation, heavy
45 = Solid precipitation, slight or moderate
46 = Solid precipitation, heavy
47 = Freezing precipitation, slight or moderate
48 = Freezing precipitation, heavy
50 = Drizzle
51 = Drizzle, not freezing, slight
52 = Drizzle, not freezing, moderate
53 = Drizzle, not freezing, heavy
54 = Drizzle, freezing, slight
55 = Drizzle, freezing, moderate
56 = Drizzle, freezing, heavy
57 = Drizzle and rain, slight
58 = Drizzle and rain, moderate or heavy
60 = Rain
61 = Rain, not freezing, slight
62 = Rain, not freezing, moderate
63 = Rain, not freezing, heavy
64 = Rain, freezing, slight
65 = Rain, freezing, moderate
66 = Rain, freezing, heavy
67 = Rain or drizzle and snow, slight
68 = Rain or drizzle and snow, moderate or heavy
70 = Snow
71 = Snow, slight
72 = Snow, moderate
73 = Snow, heavy
74 = Ice pellets, slight
75 = Ice pellets, moderate
76 = Ice pellets, heavy
77 = Snow grains
78 = Ice crystals
80 = Showers or intermittent precipitation
81 = Rain showers or intermittent rain, slight
82 = Rain showers or intermittent rain, moderate
83 = Rain showers or intermittent rain, heavy



    31


---

    84 = Rain showers or intermittent rain, violent
    85 = Snow showers or intermittent snow, slight
    86 = Snow showers or intermittent snow, moderate
    87 = Snow showers or intermittent snow, heavy
    89 = Hail
    90 = Thunderstorm
    91 = Thunderstorm, slight or moderate, with no precipitation
    92 = Thunderstorm, slight or moderate, with rain showers and/or snow showers
    93 = Thunderstorm, slight or moderate, with hail
    94 = Thunderstorm, heavy, with no precipitation
    95 = Thunderstorm, heavy, with rain showers and/or snow
    96 = Thunderstorm, heavy, with hail
    99 = Tornado

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION quality automated atmospheric condition code
    The code that denotes a quality status of a reported present weather observation from an automated station.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    M = Manual change made to value based on information provided by NWS or FAA
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PAST-WEATHER-OBSERVATION summary of day occurrence identifier
    The identifier that signifies the reporting of past weather as summarized for the calendar day.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AX1 – AX6 An indicator of up to 6 repeating fields of the following item:
    PAST-WEATHER-OBSERVATION atmospheric condition code
    PAST-WEATHER-OBSERVATION quality atmospheric condition code
    PAST-WEATHER-OBSERVATION period quantity
    PAST-WEATHER-OBSERVATION period quality code

FLD LEN: 2
    PAST-WEATHER-OBSERVATION atmospheric condition code
    The code that denotes a specific type of past weather observed.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    00 = none to report
    01 = fog
    02 = fog reducing visibility to ¼ mile or less
    03 = thunder
    04 = ice pellets
    05 = hail
    06 = glaze or rime
    07 = blowing dust or sand, visibility ½ mile or less
    08 = smoke or haze
    09 = blowing snow
    10 = tornado
    11 = high or damaging winds
    99 = missing




    32


---

FLD LEN: 1
    PAST-WEATHER-OBSERVATION quality manual atmospheric condition code
    The code that denotes a quality status of a reported past weather observation from a manual station.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

FLD LEN: 2
    PAST-WEATHER-OBSERVATION period quantity
    The quantity of time over which a PAST-WEATHER-OBSERVATION occurred.
    MIN: 24            MAX: 24          UNITS: hours
    DOM: A general domain comprised of the ASCII characters 0-9.
    99 = Missing

FLD LEN: 1
    PAST-WEATHER-OBSERVATION period quality code
    The code that denotes a quality status of a reported past weather period.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PAST-WEATHER-OBSERVATION manual occurrence identifier
    The identifier that signifies the reporting of past weather.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AY1 - AY2 An indicator of up to 2 repeating fields of the following item:
    PAST-WEATHER-OBSERVATION manual atmospheric condition code
    PAST-WEATHER-OBSERVATION quality manual atmospheric condition code
    PAST-WEATHER-OBSERVATION period quantity
    PAST-WEATHER-OBSERVATION period quality code

FLD LEN: 1
    PAST-WEATHER-OBSERVATION manual atmospheric condition code
    The code that denotes a specific type of past weather observed manually.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    Domain Value ID: Domain Value Definition Text
    0 = Cloud covering 1/2 or less of the sky throughout the appropriate period
    1 = Cloud covering more than ½ of the sky duringpart of the appropriate period and covering ½ or less during
    part of the period
    2 = Cloud covering more than 1/2 of the sky throughout the appropriate period
    3 = Sandstorm, duststorm or blowing snow
    4 = Fog or ice fog or thick haze
    5 = Drizzle
    6 = Rain
    7 = Snow, or rain and snow mixed
    8 = Shower(s)
    9 = Thunderstorm(s) with or without precipitation

FLD LEN: 1
    PAST-WEATHER-OBSERVATION quality manual atmospheric condition code
    The code that denotes a quality status of a reported past weather observation from a manual station.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present




    33


---

FLD LEN: 2
    PAST-WEATHER-OBSERVATION period quantity
    The quantity of time over which a PAST-WEATHER-OBSERVATION occurred.
    MIN: 01            MAX: 24          UNITS: hours
    DOM: A general domain comprised of the ASCII characters 0-9.
    99 = Missing

FLD LEN: 1
    PAST-WEATHER-OBSERVATION period quality code
    The code that denotes a quality status of a reported past weather period.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PAST-WEATHER-OBSERVATION automated occurrence identifier
    The identifier that signifies the reporting of present weather.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AZ1- AZ2 An indicator of the following item: (this may occur 0 - 2 times)
    PAST-WEATHER-OBSERVATION automated atmospheric condition code
    PAST-WEATHER-OBSERVATION quality automated atmospheric condition code
    PAST-WEATHER-OBSERVATION period quantity
    PAST-WEATHER-OBSERVATION period quality code

FLD LEN: 1
    PAST-WEATHER-OBSERVATION automated atmospheric condition code
    The code that denotes a specific type of past weather reported by an automated device.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = No significant weather observed
    1 = Visibility reduced
    2 = Blowing phenomena, visibility reduced
    3 = Fog
    4 = Precipitation
    5 = Drizzle
    6 = Rain
    7 = Snow or ice pellets
    8 = Showers or intermittent precipitation
    9 = Thunderstorm

FLD LEN: 1
    PAST-WEATHER-OBSERVATION quality automated atmospheric condition code
    The code that denotes a quality status of a reported past weather observation from an automated station.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

FLD LEN: 2
    PAST-WEATHER-OBSERVATION period quantity
    The quantity of time over which a PAST-WEATHER-OBSERVATION occurred.
    MIN: 01            MAX: 24          UNITS: hours
    DOM: A general domain comprised of the ASCII characters 0-9.
    99 = Missing

FLD LEN: 1
    PAST-WEATHER-OBSERVATION period quality code
    The code that denotes a quality status of a reported past weather period.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous



    34


---

    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
