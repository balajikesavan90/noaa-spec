## Part 3 - Mandatory Data Section

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

    Mandatory Data Section
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
Bold type below indicates that the element may include data originating from NCEI’s NCEI SURFACE
HOURLY/ASOS/AWOS or from AFCCC’s USAF SURFACE HOURLY. Otherwise, data originated from USAF SURFACE
HOURLY.

Note: For the quality code fields with each data element, the following may appear in data which were processed through
NCEI’s Interactive QC system (manual interaction), for selected parameters:
    A – Data value flagged as suspect, but accepted as good value.
    U – Data value replaced with edited value.
    P – Data value not originally flagged as suspect, but replaced by validator.
    I – Data value not originally in data, but inserted by validator.
    M – Manual change made to value based on information provided by NWS or FAA.
    C – Temperature and dew point received from Automated Weather Observing Systems (AWOS) are reported in
    whole degrees Celsius. Automated QC flags these values, but they are accepted as valid.
    R – Data value replaced with value computed by NCEI software.

POS: 61-63
    WIND-OBSERVATION direction angle
    The angle, measured in a clockwise direction, between true north and the direction from which the wind is blowing.
    MIN: 001      MAX: 360         UNITS: Angular Degrees
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing. If type code (below) = V, then 999 indicates variable wind direction.

POS: 64-64
    WIND-OBSERVATION direction quality code
    The code that denotes a quality status of a reported WIND-OBSERVATION direction angle.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

POS: 65-65
    WIND-OBSERVATION type code
    The code that denotes the character of the WIND-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    A = Abridged Beaufort
    B = Beaufort
    C = Calm
    H = 5-Minute Average Speed
    N = Normal
    R = 60-Minute Average Speed
    Q = Squall
    T = 180 Minute Average Speed
    V = Variable
    9 = Missing
    NOTE: If a value of 9 appears with a wind speed of 0000, this indicates calm winds.

POS: 66-69
    WIND-OBSERVATION speed rate
    The rate of horizontal travel of air past a fixed point.
    MIN: 0000       MAX: 0900        UNITS: meters per second
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.




    8


---

POS: 70-70
    WIND-OBSERVATION speed quality code
    The code that denotes a quality status of a reported WIND-OBSERVATION speed rate.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

POS: 71-75
    SKY-CONDITION-OBSERVATION ceiling height dimension
The height above ground level (AGL) of the lowest cloud or obscuring phenomena layer aloft with 5/8 or more summation total sky
cover, which may be predominantly opaque, or the vertical visibility into a surface-based obstruction. Unlimited = 22000.
    MIN: 00000     MAX: 22000 UNITS: Meters
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

POS: 76-76
    SKY-CONDTION-OBSERVATION ceiling quality code
    The code that denotes a quality status of a reported ceiling height dimension.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

POS: 77-77
    SKY-CONDITION-OBSERVATION ceiling determination code
    The code that denotes the method used to determine the ceiling.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    A = Aircraft
    B = Balloon
    C = Statistically derived
    D = Persistent cirriform ceiling (pre-1950 data)
    E = Estimated
    M = Measured
    P = Precipitation ceiling (pre-1950 data)
    R = Radar
    S = ASOS augmented
    U = Unknown ceiling (pre-1950 data)
    V = Variable ceiling (pre-1950 data)
    W = Obscured
    9 = Missing

POS: 78-78
    SKY-CONDITION-OBSERVATION CAVOK code
    The code that represents whether the 'Ceiling and Visibility Okay' (CAVOK) condition has been reported.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    N = No
    Y = Yes
    9 = Missing




    9


---

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

POS: 79-84
    VISIBILITY-OBSERVATION distance dimension
    The horizontal distance at which an object can be seen and identified.
    MIN: 000000       MAX: 160000      UNITS: Meters
    DOM: A general domain comprised of the numeric characters (0-9).
    Missing = 999999
    NOTE: Values greater than 160000 are entered as 160000

POS: 85-85
    VISIBILITY-OBSERVATION distance quality code
    The code that denotes a quality status of a reported distance of a visibility observation.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

POS: 86-86
    VISIBILITY-OBSERVATION variability code
    The code that denotes whether or not the reported visibility is variable.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    N = Not variable
    V = Variable
    9 = Missing

POS: 87-87
    VISIBILITY-OBSERVATION quality variability code
    The code that denotes a quality status of a reported VISIBILITY-OBSERVATION variability code.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

POS: 88-92
    AIR-TEMPERATURE-OBSERVATION air temperature
    The temperature of the air.
    MIN: -0932    MAX: +0618     UNITS: Degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +9999 = Missing.

POS: 93-93
    AIR-TEMPERATURE-OBSERVATION air temperature quality code
    The code that denotes a quality status of an AIR-TEMPERATURE-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present
    A = Data value flagged as suspect, but accepted as a good value
    C = Temperature and dew point received from Automated Weather Observing System (AWOS) are reported in
    whole degrees Celsius. Automated QC flags these values, but they are accepted as valid.
    I = Data value not originally in data, but inserted by validator
    M = Manual changes made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

POS: 94-98
    AIR-TEMPERATURE-OBSERVATION dew point temperature
    The temperature to which a given parcel of air must be cooled at constant pressure and water vapor
    content in order for saturation to occur.
    MIN: -0982      MAX: +0368         UNITS: Degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +9999 = Missing.


POS: 99-99
    AIR-TEMPERATURE-OBSERVATION dew point quality code
    The code that denotes a quality status of the reported dew point temperature.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present
    A = Data value flagged as suspect, but accepted as a good value
    C = Temperature and dew point received from Automated Weather Observing System (AWOS) are reported in
    whole degrees Celsius. Automated QC flags these values, but they are accepted as valid.
    I = Data value not originally in data, but inserted by validator
    M = Manual changes made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀




    11


---

POS: 100-104
    ATMOSPHERIC-PRESSURE-OBSERVATION sea level pressure
    The air pressure relative to Mean Sea Level (MSL).
    MIN: 08600      MAX: 10900      UNITS: Hectopascals
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

POS: 105-105
    ATMOSPHERIC-PRESSURE-OBSERVATION sea level pressure quality code
    The code that denotes a quality status of the sea level pressure of an
    ATMOSPHERIC-PRESSURE-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    9 = Passed gross limits check if element is present




    12
