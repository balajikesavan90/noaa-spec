## Part 27 - Pressure Data

Pressure Data
FLD LEN: 3
    ATMOSPHERIC-PRESSURE-OBSERVATION identifier
    The identifier that denotes the start of an ATMOSPHERIC-PRESSURE-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    MA1 An indicator of the occurrence of the following items:
    ATMOSPHERIC-PRESSURE-OBSERVATION altimeter setting rate
    ATMOSPHERIC-PRESSURE-OBSERVATION altimeter quality code
    ATMOSPHERIC-PRESSURE-OBSERVATION station pressure rate
    ATMOSPHERIC-PRESSURE-OBSERVATION station pressure quality code

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION altimeter setting rate
    The pressure value to which an aircraft altimeter is set so that it will indicate the altitude relative to mean sea level of an
    aircraft on the ground at the location for which the value was determined.
    MIN: 08635        MAX: 10904       UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    Missing = 99999




    88


---

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION altimeter quality code
    The code that denotes a quality status of an altimeter setting rate.
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

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION station pressure rate
    The atmospheric pressure at the observation point.
    MIN: 04500     MAX: 10900 UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION station pressure quality code
    The code that denotes a quality status of the station pressure of an ATMOSPHERIC-PRESSURE-OBSERVATION.
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
    ATMOSPHERIC-PRESSURE-CHANGE identifier
    The identifier that denotes the start of an ATMOSPHERIC-PRESSURE-CHANGE data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    Domain Value ID: Domain Value Definition Text
    MD1 An indicator of the occurrence of the following items:
    ATMOSPHERIC-PRESSURE-CHANGE tendency code
    ATMOSPHERIC-PRESSURE-CHANGE quality tendency code
    ATMOSPHERIC-PRESSURE-CHANGE three hour quantity
    ATMOSPHERIC-PRESSURE-CHANGE quality three hour code
    ATMOSPHERIC-PRESSURE-CHANGE twenty four hour quantity
    ATMOSPHERIC-PRESSURE-CHANGE quality twenty four hour code

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-CHANGE tendency code
    The code that denotes the characteristics of an ATMOSPHERIC-PRESSURE-CHANGE that occurs over a period of
    three hours.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    Domain Value ID: Domain Value Definition Text
    0 = Increasing, then decreasing; atmospheric pressure the same or higher than 3 hours ago
    1 = Increasing then steady; or increasing, then increasing more slowly; atmospheric pressure now higher than 3
    hours ago
    2 = Increasing (steadily or unsteadily); atmospheric pressure now higher than 3 hours ago
    3 = Decreasing or steady, then increasing; or increasing, then increasing more rapidly; atmospheric pressure now
    higher than 3 hours ago
    4 = Steady; atmospheric pressure the same as 3 hours ago
    5 = Decreasing, then increasing; atmospheric pressure the same or lower than 3 hours ago
    6 = Decreasing, then steady; or decreasing, then decreasing more slowly; atmospheric pressure now lower than 3
    hours ago
    7 = Decreasing (steadily or unsteadily); atmospheric pressure now lower than 3 hours ago




    89


---

    8 = Steady or increasing, then decreasing; or decreasing, then decreasing more rapidly; atmospheric pressure
    now lower than 3 hours ago
    9 = Missing
FLD LEN: 1
    ATMOSPHERIC-PRESSURE-CHANGE quality tendency code
    The code that denotes a quality status of the tendency of an ATMOSPHERIC-PRESSURE-CHANGE.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present


FLD LEN: 3
    ATMOSPHERIC-PRESSURE-CHANGE three hour quantity
    The absolute value of the quantity of change in atmospheric pressure measured at the
    beginning and end of a three hour period.
    MIN: 000      MAX: 500       UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    Missing = 999

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-CHANGE quality three hour code
    The code that denotes the quality status of the three hour quantity for an ATMOPSHERIC-
    PRESSURE-CHANGE.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

FLD LEN: 4
    ATMOSPHERIC-PRESSURE-CHANGE twenty four hour quantity
    The quantity of change in atmospheric pressure measured at the beginning and end of a twenty four
    hour period.
    MIN: -800        MAX: +800    UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters(0-9), a plus sign (+), and a minus
    sign (-).
    +999 = Missing

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-CHANGE quality twenty four hour code
    The code that denotes a quality status of a reported twenty four hour ATMOSPHERIC-PRESSURE-
    CHANGE.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL identifier
    The identifier that denotes the availability of GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    ME1: An indicator of the occurrence of the following data items:
    GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL code
    GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL height dimension
    GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL height dimension quality code




    90


---

FLD LEN: 1
    GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL code
    The code that denotes the isobaric surface used to represent geopotential height.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    Domain Value ID: Domain Value Definition Text
    1 = 1000 hectopascals
    2 = 925 hectopascals
    3 = 850 hectopascals
    4 = 700 hectopascals
    5 = 500 hectopascals
    9 = Missing

FLD LEN: 4
    GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL height dimension
    The height of a GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL
    MIN: 0000       MAX: 9998    UNITS: Geopotential Meters
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing

FLD LEN: 1
    GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL height dimension quality code
    The code that denotes a quality status of the reported GEOPOTENTIAL-HEIGHT-ISOBARIC-LEVEL height dimension.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) occurrence identifier
    The identifier that denotes the start of an ATMOSPHERIC-PRESSURE-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    MF1 An indicator of the following items:
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) average station pressure for the day (derived)
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) average station pressure quality code
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) average sea level pressure for the day (derived)
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) average sea level pressure quality code



FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) average station pressure for the day
    The average pressure at the observed point for the day derived computationally from other QC’ed elements
    MIN: 04500       MAX: 10900        UNITS: hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) quality code
    The code that denotes a quality status of an average station pressure
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, from NCEI ASOS/AWOS
    5 = Passed all quality control checks, from NCEI ASOS/AWOS
    6 = Suspect, from NCEI ASOS/AWOS
    7 = Erroneous, from NCEI ASOS/AWOS
    9 = Missing




    91


---

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) average sea level pressure for the day
    The average sea level pressure at the observed point for the day derived computationally from other QC’ed elements
    MIN: 08600        MAX: 10900         UNITS: hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION (STP/SLP) quality code
    The code that denotes a quality status of an average station pressure
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, from NCEI ASOS/AWOS
    9 = Missing


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    ATMOSPHERIC-PRESSURE-OBSERVATION identifier
    The identifier that denotes the start of an ATMOSPHERIC-PRESSURE-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    MG1 An indicator of the occurrence of the following items:
    ATMOSPHERIC-PRESSURE-OBSERVATION average station pressure for the day
    ATMOSPHERIC-PRESSURE-OBSERVATION average station pressure quality code
    ATMOSPHERIC-PRESSURE-OBSERVATION minimum sea level pressure for the day
    ATMOSPHERIC-PRESSURE-OBSERVATION minimum sea level pressure quality code

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION average station pressure for the day
    The average pressure at the observation point for the day.
    MIN: 04500     MAX: 10900      UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION average station pressure quality code
    The code that denotes the quality status of an average station pressure.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    M = Manual change made to value based on information provided by NWS or FAA
    9 = Passed gross limits check if element is present

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION minimum sea level pressure for the day
    The minimum sea level pressure for the day at the observation point.
    MIN: 08600     MAX: 10900 UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION minimum sea level pressure for the day quality code
    The code that denotes the quality status of the minimum sea level pressure for the day.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source



    92


---

    7 = Erroneous, data originate from an NCEI data source
    M = Manual change made to value based on information provided by NWS or FAA
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH identifier
    The identifier that denotes the start of an ATMOSPHERIC-PRESSURE-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    MH1 An indicator of the occurrence of the following items:
    ATMOSPHERIC-PRESSURE-OBSERVATION average station pressure for the month
    ATMOSPHERIC-PRESSURE-OBSERVATION average station pressure quality code
    ATMOSPHERIC-PRESSURE-OBSERVATION average sea level pressure for the month
    ATMOSPHERIC-PRESSURE-OBSERVATION average sea level pressure quality code

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH average station pressure for the month
    The average pressure at the observation point for the month.
    MIN: 04500     MAX: 10900      UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH average station pressure quality code
    The code that denotes the quality status of an average station pressure.
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

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH average sea level pressure for the month
    The average sea level pressure for the month at the observation point.
    MIN: 08600     MAX: 10900 UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH average sea level pressure for the month quality
    code
    The code that denotes the quality status of the average sea level pressure for the month.
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




    93


---

FLD LEN: 3
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH identifier
    The identifier that denotes the start of an ATMOSPHERIC-PRESSURE-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    MK1 An indicator of the occurrence of the following items:
    ATMOSPHERIC-PRESSURE-OBSERVATION maximum sea level pressure for the month
    ATMOSPHERIC-PRESSURE-OBSERVATION maximum sea level pressure date-time
    ATMOSPHERIC-PRESSURE-OBSERVATION maximum sea level pressure quality code
    ATMOSPHERIC-PRESSURE-OBSERVATION minimum sea level pressure for the month
    ATMOSPHERIC-PRESSURE-OBSERVATION minimum sea level pressure date-time
    ATMOSPHERIC-PRESSURE-OBSERVATION minimum sea level pressure quality code

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH maximum sea level pressure for the month
    The maximum sea level pressure at the observation point for the month.
    MIN: 08600     MAX: 10900     UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing

FLD LEN: 6
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH maximum sea level pressure, date-time
    The date-time of occurrence of the pressure value, given as the date-time; e.g., 051500 indicates day 05, time 1500.
    MIN: 010000       MAX: 312359
    DOM: A general domain comprised of the numeric characters (0-9).
    999999 = Missing

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH maximum sea level pressure quality code
    The code that denotes the quality status of a maximum sea level pressure.
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

FLD LEN: 5
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH minimum sea level pressure for the month
    The minimum sea level pressure at the observation point for the month.
    MIN: 08600     MAX: 10900     UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing

FLD LEN: 6
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH minimum sea level pressure, date-time
    The date-time of occurrence of the pressure value, given as the date-time; e.g., 051500 indicates day 05, time 1500.
    MIN: 010000       MAX: 312359
    DOM: A general domain comprised of the numeric characters (0-9).
    999999 = Missing

FLD LEN: 1
    ATMOSPHERIC-PRESSURE-OBSERVATION FOR THE MONTH minimum sea level pressure quality code
    The code that denotes the quality status of a minimum sea level pressure.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source



    94


---

    M = Manual change made to value based on information provided by NWS or FAA
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
