## Part 28 - Weather Occurrence Data (Extended)

Weather Occurrence Data

FLD LEN: 3
    PRESENT-WEATHER-IN-VICINITY-OBSERVATION occurrence identifier
    The identifier that signifies the reporting of present weather.
    DOM: A specific domain comprised of the ASCII characters.
    MV1 = first weather reported
    MV2 = second weather reported
    MV3 = third weather reported
    MV4 = fourth weather reported
    MV5 = fifth weather reported
    MV6 = sixth weather reported
    MV7 = seventh weather reported
    An indicator of up to 7 repeating fields of the following items:
    PRESENT-WEATHER-OBSERVATION atmospheric condition code.
    PRESENT-WEATHER-OBSERVATION quality manual atmospheric condition code

FLD LEN: 2
    PRESENT-WEATHER-IN-VICINITY-OBSERVATION atmospheric condition code
    The code that denotes a specific type of weather observed between 5 and 10 statute miles of the station at the time of
    Observation. Observed at selected statons from July 1, 1996 to present.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    00 = No observation
    01 = Thunderstorm in vicinity
    02 = Showers in vicinity
    03 = Sandstorm in vicinity
    04 = Sand / dust whirls in vicinity
    05 = Duststorm in vicinity
    06 = Blowing snow in vicinity
    07 = Blowing sand in vicinity
    08 = Blowing dust in vicinity
    09 = Fog in vicinity
    99 = Missing

FLD LEN: 1
    PRESENT-WEATHER-IN-VICINITY-OBSERVATION quality atmospheric condition code
    The code that denotes a quality status of a reported present weather in vicinity observation from a station.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

  ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PRESENT-WEATHER-OBSERVATION manual occurrence identifier
    The identifier that signifies the reporting of present weather.
    DOM: A specific domain comprised of the ASCII characters.
    MW1 = first weather reported
    MW2 = second weather reported
    MW3 = third weather reported
    MW4 = fourth weather reported
    MW5 = fifth weather reported
    MW6 = sixth weather reported
    MW7 = seventh weather reported
    An indicator of up to 7 repeating fields of the following items:
    PRESENT-WEATHER-OBSERVATION manual atmospheric condition code.
    PRESENT-WEATHER-OBSERVATION quality manual atmospheric condition code




    95


---

FLD LEN: 2
    PRESENT-WEATHER-OBSERVATION manual atmospheric condition code
    The code that denotes a specific type of weather observed manually.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    Note: Lack of an MW1 report normally indicates that the station did not report any present weather data.
    ------------------------------------------------------------------------
    No precipitation, fog, ice fog (except for 11 and 12), duststorm, sandstorm, drifting or blowing snow at the
    station at the time of observation or, except for 09 and 17, during the preceding hour.
    ------------------------------------------------------------------------
    00 = Cloud development not observed or not observable
    01 = Clouds generally dissolving or becoming less developed
    02 = State of sky on the whole unchanged
    03 = Clouds generally forming or developing
    04 = Visibility reduced by smoke, e.g. veldt or forest fires, industrial smoke or volcanic ashes
    05 = Haze
    06 = Widespread dust in suspension in the air, not raised by wind at or near the station at the time of observation
    07 = Dust or sand raised by wind at or near the station at the time of observation, but no well-developed dust
    whirl(s) sand whirl(s), and no duststorm or sandstorm seen or, in the case of ships, blowing spray at the
    station
    08 = Well developed dust whirl(s) or sand whirl(s) seen at or near the station during the preceding hour or at the
    time of observation, but no duststorm or sandstorm
    09 = Duststorm or sandstorm within sight at the time of observation, or at the station during the preceding hour
    10 = Mist
    11 = Patches of shallow fog or ice fog at the station, whether on land or sea, not deeper than about 2 meters on
    land or 10 meters at sea
    12 = More or less continuous shallow fog or ice fog at the station, whether on land or sea, not deeper than about 2
    meters on land or 10 meters at sea
    13 = Lightning visible, no thunder heard
    14 = Precipitation within sight, not reaching the ground or the surface of the sea
    15 = Precipitation within sight, reaching the ground or the surface of the sea, but distant, i.e., estimated to be more
    than 5 km from the station
    16 = Precipitation within sight, reaching the ground or the surface of the sea, near to, but not at the station
    17 = Thunderstorm, but no precipitation at the time of observation
    18 = Squalls at or within sight of the station during the preceding hour or at the time of observation
    19 = Funnel cloud(s) (Tornado cloud or waterspout) at or within sight of the station during the preceding hour or at
    the time of observation
    -----------------------------------------------------------------------
    Precipitation, fog, ice fog or thunderstorm at the station during the preceding hour, but not at the time
    Observation
    ----------------------------------------------------------------------
    20 = Drizzle (not freezing) or snow grains not falling as shower(s)
    21 = Rain (not freezing) not falling as shower(s)
    22 = Snow not falling as shower(s)
    23 = Rain and snow or ice pellets not falling as shower(s)
    24 = Freezing drizzle or freezing rain not falling as shower(s)
    25 = Shower(s) of rain
    26 = Shower(s) of snow or of rain and snow
    27 = Shower(s) of hail (Hail, small hail, snow pellets), or rain and hail
    28 = Fog or ice fog
    29 = Thunderstorm (with or without precipitation)
    -----------------------------------------------------------------------
    Dust, sand, or blowing snow in the air, but no precipitation at the time of observation.
    -----------------------------------------------------------------------
    30 = Slight or moderate duststorm or sandstorm has decreased during the preceding hour
    31 = Slight or moderate duststorm or sandstorm no appreciable change during the preceding hour
    32 = Slight or moderate duststorm or sandstorm has begun or has increased during the preceding hour
    33 = Severe duststorm or sandstorm has decreased during the preceding hour
    34 = Severe duststorm or sandstorm no appreciable change during the preceding hour
    35 = Severe duststorm or sandstorm has begun or has increased during the preceding hour
    36 = Slight or moderate drifting snow generally low (below eye level)
    37 = Heavy drifting snow generally low (below eye level)
    38 = Slight or moderate blowing snow generally high (above eye level)
    39 = Heavy blowing snow generally high (above eye level)
    -----------------------------------------------------------------------
    Fog or ice fog at the time of observation
    -----------------------------------------------------------------------
    40 = Fog or ice fog at a distance at the time of observation, but not at the station during the preceding
    hour, the fog or ice fog extending to a level above that of the observer
    41 = Fog or ice fog in patches



    96


---

    42 = Fog or ice fog, sky visible, has become thinner during the preceding hour
    43 = Fog or ice fog, sky invisible, has become thinner during the preceding hour
    44 = Fog or ice fog, sky visible, no appreciable change during the preceding hour
    45 = Fog or ice fog, sky invisible, no appreciable change during the preceding hour
    46 = Fog or ice fog, sky visible, has begun or has become thicker during the preceding hour
    47 = Fog or ice fog, sky invisible, has begun or has become thicker during the preceding hour
    48 = Fog, depositing rime, sky visible
    49 = Fog, depositing rime, sky invisible
-----------------------------------------------------------------------
Precipitation at the station at the time of observation – including Drizzle, Rain, Solid Precipitation, and
    Precipitation with current or recent Thunder
-----------------------------------------------------------------------
    50 = Drizzle, not freezing, intermittent, slight at time of observation
    51 = Drizzle, not freezing, continuous, slight at time of observation
    52 = Drizzle, not freezing, intermittent, moderate at time of observation
    53 = Drizzle, not freezing, continuous, moderate at time of observation
    54 = Drizzle, not freezing, intermittent, heavy (dense) at time of observation
    55 = Drizzle, not freezing, continuous, heavy (dense) at time of observation
    56 = Drizzle, freezing, slight
    57 = Drizzle, freezing, moderate or heavy (dense)
    58 = Drizzle and rain, slight
    59 = Drizzle and rain, moderate or heavy
    60 = Rain, not freezing, intermittent, slight at time of observation
    61 = Rain, not freezing, continuous, slight at time of observation
    62 = Rain, not freezing, intermittent, moderate at time of observation
    63 = Rain, not freezing, continuous, moderate at time of observation
    64 = Rain, not freezing, intermittent, heavy at time of observation
    65 = Rain, not freezing, continuous, heavy at time of observation
    66 = Rain, freezing, slight
    67 = Rain, freezing, moderate or heavy
    68 = Rain or drizzle and snow, slight
    69 = Rain or drizzle and snow, moderate or heavy
    70 = Intermittent fall of snowflakes, slight at time of observation
    71 = Continuous fall of snowflakes, slight at time of observation
    72 = Intermittent fall of snowflakes, moderate at time of observation
    73 = Continuous fall of snowflakes, moderate at time of observation
    74 = Intermittent fall of snowflakes, heavy at time of observation
    75 = Continuous fall of snowflakes, heavy at time of observation
    76 = Diamond dust (with or without fog)
    77 = Snow grains (with or without fog)
    78 = Isolated star-like snow crystals (with or without fog)
    79 = Ice pellets
    80 = Rain shower(s), slight
    81 = Rain shower(s), moderate or heavy
    82 = Rain shower(s), violent
    83 = Shower(s) of rain and snow mixed, slight
    84 = Shower(s) of rain and snow mixed, moderate or heavy
    85 = Show shower(s), slight
    86 = Snow shower(s), moderate or heavy
    87 = Shower(s) of snow pellets or small hail, with or without rain or rain and snow mixed, slight
    88 = Shower(s) of snow pellets or small hail, with or without rain or rain and snow mixed, moderate or heavy
    89 = Shower(s) of hail (hail, small hail, snow pellets), with or without rain or rain and snow mixed, not associated
    with thunder, slight
    90 = Shower(s) of hail (hail, small hail, snow pellets), with or without rain or rain and snow mixed, not associated
    with thunder, moderate or heavy
    91 = Slight rain at time of observation, thunderstorm during the preceding hour but not at time of observation
    92 = Moderate or heavy rain at time of observation, thunderstorm during the preceding hour but not at time of
    observation
    93 = Slight snow, or rain and snow mixed or hail (Hail, small hail, snow pellets), at time of observation,
    thunderstorm during the preceding hour but not at time of observation
    94 = Moderate or heavy snow, or rain and snow mixed or hail(Hail, small hail, snow pellets) at time of observation,
    thunderstorm during the preceding hour but not at time of observation
    95 = Thunderstorm, slight or moderate, without hail (Hail, small hail, snow pellets), but with rain and/or snow at time
    of observation, thunderstorm at time of observation
    96 = Thunderstorm, slight or moderate, with hail (hail, small hail, snow pellets) at time of observation, thunderstorm
    at time of observation
    97 = Thunderstorm, heavy, without hail (Hail, small hail, snow pellets), but with rain and/or snow at time of
    observation, thunderstorm at time of observation




    97


---

    98 = Thunderstorm combined with duststorm or sandstorm at time of observation, thunderstorm at time of
    observation
    99 = Thunderstorm, heavy, with hail (Hail, small hail, snow pellets) at time of observation, thunderstorm at time of
    observation

FLD LEN: 1
    PRESENT-WEATHER-OBSERVATION quality manual atmospheric condition code
    The code that denotes a quality status of a reported present weather observation from a manual station.
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
