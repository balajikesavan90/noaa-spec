## Part 26 - Soil Temperature Data

Soil Temperature Data

FLD LEN: 3
    SOIL-TEMPERATURE identifier
    The identifier that denotes the start of a SOIL TEMPERATURE data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    ST1: An indicator of fields of the following items:
    SOIL-TEMPERATURE Temperature Type
    SOIL-TEMPERATURE Soil Temperature
    SOIL-TEMPERATURE quality code
    SOIL-TEMPERATURE Depth
    SOIL-TEMPERATURE quality code
    SOIL-TEMPERATURE Soil Cover
    SOIL-TEMPERATURE quality code
    SOIL-TEMPERATURE Sub Plot
    SOIL-TEMPERATURE quality code

FLD LEN: 1
    SOIL-TEMPERATURE temperature type
    The type of temperature reported.
    MIN: 1 MAX: 9
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Maximum Temperature
    2 = Minimum Temperature
    3 = AM or Noon Temperature
    4 = PM or Midnight Temperature
    9 = Missing

FLD LEN: 5
    SOIL-TEMPERATURE soil temperature
    The temperature of the soil for the previous 24 hours.
    MIN: -1100 MAX: +0630 UNITS: Degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +9999 = Missing

FLD LEN: 1
    SOIL-TEMPERATURE quality code
    The code that denotes a quality status of the reported temperature data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, from NCEI Data source
    5 = Passed all quality control checks, from NCEI Data source
    6 = Suspect, from NCEI Data source
    7 = Erroneous, from NCEI Data source
    9 = Passed gross limits check if element is present

FLD LEN: 4
    SOIL-TEMPERATURE temperature depth
    The depth below ground level of the temperature reported.
    MIN: 0000 MAX: 9998 UNITS: Centimeters
    SCALING FACTOR: 10
    DOM: A specific domain comprised of the characters in the ASCII character set.
    9999 = Missing

FLD LEN: 1
    SOIL-TEMPERATURE depth quality code
    The code that denotes a quality status of the reported temperature depth data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, from NCEI Data source
    5 = Passed all quality control checks, from NCEI Data source
    6 = Suspect, from NCEI Data source
    7 = Erroneous, from NCEI Data source
    9 = Passed gross limits check if element is present




    105


---

FLD LEN: 2
    SOIL-TEMPERATURE soil cover
    The type of soil cover.
    MIN: 01 MAX: 99
    DOM: A specific domain comprised of the characters in the ASCII character set.
    01 = Grass
    02 = Fallow
    03 = Bare Ground
    04 = Brome Grass
    05 = Sod
    06 = Straw Mulch
    07 = Grass Muck
    08 = Bare Muck
    99 = Missing

FLD LEN: 1
    SOIL-TEMPERATURE soil cover quality code
    The code that denotes a quality status of the reported soil cover data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, from NCEI Data source
    5 = Passed all quality control checks, from NCEI Data source
    6 = Suspect, from NCEI Data source
    7 = Erroneous, from NCEI Data source
    9 = Passed gross limits check if element is present

FLD LEN: 1
    SOIL-TEMPERATURE sub plot
    The sub plot number for the reported temperature.
    MIN: 0 MAX: 9
    DOM: A specific domain comprised of the characters in the ASCII character set.
    9=Missing

FLD LEN: 1
    SOIL-TEMPERATURE sub plot quality code
    The code that denotes a quality status of the reported sub plot data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, from NCEI Data source
    5 = Passed all quality control checks, from NCEI Data source
    6 = Suspect, from NCEI Data source
    7 = Erroneous, from NCEI Data source
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
