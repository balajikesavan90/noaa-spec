## Part 4 - Additional Data Section

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

    Additional Data Section
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

Bold type below indicates that the element may include data originating from NCEI’s NCEI SURFACE
HOURLY/ASOS/AWOS, NCEI HOURLY PRECIPITATION/Hourly Precip, or from AFCCC’s USAF SURFACE HOURLY.
Otherwise, data originated from USAF SURFACE HOURLY.

Note: For the quality code fields with each data element, the following may appear in data which were processed through
NCEI’s Interactive QC system (manual interaction), for selected parameters:
A – Data value flagged as suspect, but accepted as good value.
U – Data value replaced with edited value.
P – Data value not originally flagged as suspect, but replaced by validator.
I – Data value not originally in data, but inserted by validator.
M - Manual change made to value based on information provided by NWS or FAA
C - Temperature and dew point received from Automated Weather Observing Systems (AWOS) are reported in whole
    degrees Celsius. Automated QC flags these values, but they are accepted as valid.
R - Data value replaced with value computed by NCEI software.



FLD LEN: 3
    GEOPHYSICAL-POINT-OBSERVATION additional data identifier
    The identifier that denotes the beginning of the additional data section.
    DOM: A specific domain comprised of the ASCII character set.
    ADD Additional Data Section


### Precipitation Data
FLD LEN: 3
    LIQUID-PRECIPITATION occurrence identifier
    The identifier that represents an episode of LIQUID-PRECIPITATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AA1 - AA4 An indicator of up to 4 repeating fields of the following items:
    LIQUID-PRECIPITATION period quantity
    LIQUID-PRECIPITATION depth dimension
    LIQUID-PRECIPITATION condition code
    LIQUID-PRECIPITATION quality code

FLD LEN: 2
    LIQUID-PRECIPITATION period quantity in hours
    The quantity of time over which the LIQUID-PRECIPITATION was measured.
    MIN: 00      MAX: 98       UNITS: Hours
    SCALING FACTOR: 1
    DOM: A specific domain comprised of the characters in the ASCII character set
    99 = Missing.

FLD LEN: 4
    LIQUID-PRECIPITATION depth dimension
    The depth of LIQUID-PRECIPITATION that is measured at the time of an observation.
    MIN: 0000      MAX: 9998     UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION condition code
    The code that denotes whether a LIQUID-PRECIPITATION depth dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    3 = Begin accumulated period (precipitation amount missing until end of accumulated period)
    4 = End accumulated period
    5 = Begin deleted period (precipitation amount missing due to data problem)
    6 = End deleted period



    13


---

    7 = Begin missing period
    8 = End missing period
    E = Estimated data value (eg, from nearby station)
    I = Incomplete precipitation amount, excludes one or more missing reports, such as one or more 15-minute reports
    not included in the 1-hour precipitation total
    J = Incomplete precipitation amount, excludes one or more erroneous reports, such as one or more 1-hour
    precipitation amounts excluded from the 24-hour total
    9 = Missing

FLD LEN: 1
    LIQUID-PRECIPITATION quality code
    The code that denotes a quality status of the reported LIQUID-PRECIPITATION data.
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    LIQUID-PRECIPITATION MONTHLY TOTAL identifier
    The identifier that represents LIQUID-PRECIPITATION MONTHLY TOTAL data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AB1 An indicator of the following items:
    LIQUID-PRECIPITATION depth dimension
    LIQUID-PRECIPITATION condition code
    LIQUID-PRECIPITATION quality code

FLD LEN: 5
    LIQUID-PRECIPITATION MONTHLY TOTAL depth dimension
    The depth of LIQUID-PRECIPITATION for the month.
    MIN: 00000      MAX: 50000     UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION MONTHLY TOTAL condition code
    The code that denotes whether a LIQUID-PRECIPITATION depth dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    9 = Missing

FLD LEN: 1
    LIQUID-PRECIPITATION MONTHLY TOTAL quality code
    The code that denotes a quality status of the reported LIQUID-PRECIPITATION data.
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



    14


---

    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PRECIPITATION-OBSERVATION-HISTORY identifier
    The identifier that indicates the occurrence of precipitation history information.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AC1 An indicator of the following items:
    PRECIPITATION-OBSERVATION-HISTORY duration code
    PRECIPITATION-OBSERVATION-HISTORY characteristic code
    PRECIPITATION-OBSERVATION-HISTORY quality code

FLD LEN: 1
    PRECIPITATION-OBSERVATION-HISTORY duration code
    The code that denotes the duration of precipitation.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Lasted less than 1 hour
    1 = Lasted 1 - 3 hours
    2 = Lasted 3 - 6 hours
    3 = Lasted more than 6 hours
    9 = Missing

FLD LEN: 1
    PRECIPITATION-OBSERVATION-HISTORY characteristic code
    The code that denotes whether precipitation is continuous or intermittent.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    C = Continuous
    I = Intermittent
    9 = Missing

FLD LEN: 1
    PRECIPITATION duration/characteristic quality code
    The code that denotes a quality status of the reported PRECIPITATION duration/characteristic.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    LIQUID-PRECIPITATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH identifier
    The identifier that represents LIQUID-PRECIPITATION, GREATEST IN 24 HOURS, data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AD1 An indicator of the following items:
    LIQUID-PRECIPITATION depth dimension
    LIQUID-PRECIPITATION condition code
    LIQUID-PRECIPITATION dates of occurrence (3 fields)
    LIQUID-PRECIPITATION quality code

FLD LEN: 5
    LIQUID-PRECIPITATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH depth dimension
    The depth of LIQUID-PRECIPITATION for the 24-hour period.
    MIN: 00000      MAX: 20000    UNITS: millimeters



    15


---

    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH condition code
    The code that denotes whether a LIQUID-PRECIPITATION depth dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    3 = The amount occurred on other dates in addition to those listed
    4 = Trace amount occurred on other dates in addition to those listed
    9 = Missing or N/A

FLD LEN: 4
    LIQUID-PRECIPITATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH dates of occurrence
    The dates of occurrence of LIQUID-PRECIPITATION, given as the begin-end date for the 24-hour period, for
    up to 3 occurrences; e.g., 0405 indicates 24-hour period on days 04-05.
    MIN: 0101      MAX: 3131
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 4
    LIQUID-PRECIPITATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH dates of occurrence
    The dates of occurrence of LIQUID-PRECIPITATION, given as the begin-end date for the 24-hour period, for
    up to 3 occurrences; e.g., 0405 indicates 24-hour period on days 04-05.
    MIN: 0101      MAX: 3131
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 4
    LIQUID-PRECIPITATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH dates of occurrence
    The dates of occurrence of LIQUID-PRECIPITATION, given as the begin-end date for the 24-hour period, for up to 3
    occurrences; e.g., 0405 indicates 24-hour period on days 04-05.
    MIN: 0101      MAX: 3131
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH quality code
    The code that denotes a quality status of the reported LIQUID-PRECIPITATION data.
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀




    16


---

FLD LEN: 3
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH identifier
    The identifier that represents NUMBER OF DAYS WITH LIQUID-PRECIPITATION data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AE1 An indicator of the following items:
    LIQUID-PRECIPITATION number of days with .01 inch or more
    LIQUID-PRECIPITATION quality code
    LIQUID-PRECIPITATION number of days with .10 inch or more
    LIQUID-PRECIPITATION quality code
    LIQUID-PRECIPITATION number of days with .50 inch or more
    LIQUID-PRECIPITATION quality code
    LIQUID-PRECIPITATION number of days with 1.00 inch or more
    LIQUID-PRECIPITATION quality code

FLD LEN: 2
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH
    The number of days with .01 inch (.25 mm) or more precipitation.
    MIN: 00     MAX: 31
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH quality code
    The code that denotes a quality status of the reported days with .01 or more.
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value


FLD LEN: 2
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH
    The number of days with .10 inch (2.5 mm) or more precipitation.
    MIN: 00     MAX: 31
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH quality code
    The code that denotes a quality status of the reported days with .10 or more.
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value




    17


---

FLD LEN: 2
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH
    The number of days with .50 inch (12.7 mm) or more precipitation.
    MIN: 00     MAX: 31
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH quality code
    The code that denotes a quality status of the reported days with .50 or more.
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value

FLD LEN: 2
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH
    The number of days with 1.00 inch (25 mm) or more precipitation.
    MIN: 00     MAX: 31
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION, NUMBER OF DAYS WITH SPECIFIC AMOUNTS, FOR THE MONTH quality code
    The code that denotes a quality status of the reported days with 1.00 or more.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PRECIPITATION-ESTIMATED-OBSERVATION identifier
    The identifier that represents a PRECIPITATION-ESTIMATED-OBSERVATION, from AFCCC.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AG1 An indicator of the occurrence of the following items:
    PRECIPITATION-OBSERVATION discrepancy code
    PRECIPITATION-OBSERVATION estimated water depth dimension




    18


---

FLD LEN: 1
    PRECIPITATION-ESTIMATED-OBSERVATION discrepancy code
    The code that denotes the type of discrepancy between a PRECIPITATION-OBSERVATION and other related
    observations at the same location.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Reported amount of precipitation and reported weather agree
    1 = Precipitation missing or not reported and none inferred by weather
    2 = Precipitation missing, but precipitation inferred by weather
    3 = Precipitation reported, but none inferred by weather
    4 = Zero precipitation reported, but precipitation inferred by weather
    5 = Zero precipitation reported, no precipitation inferred and precipitation not occurring at the reporting station
    9 = Missing

FLD LEN: 3
    PRECIPITATION-ESTIMATED-OBSERVATION estimated water depth dimension
    The estimated depth of precipitation in water depth for a 3-hour synoptic period.
    MIN: 000     MAX: 998      UNITS: millimeters
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing.

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH identifier
    The identifier that represents MAXIMUM SHORT DURATION PRECIPITATION data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AH1-AH6: An indicator of up to 6 repeating fields for the following items:
    LIQUID-PRECIPITATION period quantity
    LIQUID-PRECIPITATION depth dimension
    LIQUID-PRECIPITATION condition code
    LIQUID-PRECIPITATION end date
    LIQUID-PRECIPITATION end time
    LIQUID-PRECIPITATION quality code

FLD LEN: 3
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH period quantity
    The quantity of time over which the LIQUID-PRECIPITATION was measured.
    MIN: 005      MAX: 045       UNITS: Minutes
    SCALING FACTOR: 1
    DOM: A specific domain comprised of the characters in the ASCII character set
    999 = Missing.

FLD LEN: 4
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH depth dimension
    The depth of LIQUID-PRECIPITATION for the defined time period.
    MIN: 0000      MAX: 3000     UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH condition code
    The code that denotes whether a LIQUID-PRECIPITATION depth dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    9 = Missing

FLD LEN: 6
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH ending date-time
    The ending date of occurrence of the event , given as the date-time in GMT; e.g., 051010 indicates
    1010 Z-time on day 05 of the month.
    MIN: 010000      MAX: 312359
    DOM: A general domain comprised of the numeric characters (0-9).
    999999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH quality code



    19


---

    The code that denotes a quality status of the reported LIQUID-PRECIPITATION data.
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH identifier
    The identifier that represents MAXIMUM SHORT DURATION PRECIPITATION data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    NOTE: This data group is identical to the AH1-6 group above, for the purpose of allowing up to 12 occurrences of
    these reports.
    AI1-AI6: An indicator of up to 6 repeating fields for the following items:
    LIQUID-PRECIPITATION period quantity
    LIQUID-PRECIPITATION depth dimension
    LIQUID-PRECIPITATION condition code
    LIQUID-PRECIPITATION end date
    LIQUID-PRECIPITATION end time
    LIQUID-PRECIPITATION quality code

FLD LEN: 3
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH period quantity
    The quantity of time over which the LIQUID-PRECIPITATION was measured.
    MIN: 060      MAX: 180       UNITS: Minutes
    SCALING FACTOR: 1
    DOM: A specific domain comprised of the characters in the ASCII character set
    999 = Missing.

FLD LEN: 4
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH depth dimension
    The depth of LIQUID-PRECIPITATION for the defined time period.
    MIN: 0000      MAX: 3000     UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH condition code
    The code that denotes whether a LIQUID-PRECIPITATION depth dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    9 = Missing

FLD LEN: 6
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH ending date-time
    The ending date of occurrence of the event, given as the date-time in GMT; e.g., 051010 indicates
    1010 Z-time on day 05 of the month.
    MIN: 010000      MAX: 312359
    DOM: A general domain comprised of the numeric characters (0-9).
    999999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION MAXIMUM SHORT DURATION, FOR THE MONTH quality code
    The code that denotes a quality status of the reported LIQUID-PRECIPITATION data



    20


---

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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    SNOW-DEPTH identifier
    The identifier that denotes the start of a SNOW-DEPTH data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AJ1 An indicator of the occurrence of the following items:
    SNOW-DEPTH dimension
    SNOW-DEPTH condition code
    SNOW-DEPTH quality code
    SNOW-DEPTH equivalent water depth dimension
    SNOW-DEPTH equivalent water condition code
    SNOW-DEPTH equivalent water condition quality code

FLD LEN: 4
    SNOW-DEPTH dimension
    The depth of snow and ice on the ground.
    MIN: 0000     MAX: 1200     UNITS: centimeters
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    SNOW-DEPTH condition code
    The code that denotes specific conditions associated with the measurement of snow in a PRECIPITATION-
    OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Snow cover not continuous
    3 = Trace
    4 = End accumulated period (data include more than one day)
    5 = End deleted period (data eliminated due to quality problems)
    6 = End missing period
    E = Estimated data value (eg, from nearby station)
    9 = Missing

FLD LEN: 1
    SNOW-DEPTH quality code
    The code that denotes a quality status of the reported SNOW-DEPTH data.
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator



    21


---

    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value


FLD LEN: 6
    SNOW-DEPTH equivalent water depth dimension
    The depth of the liquid content of solid precipitation that has accumulated on the ground.
    MIN: 000000      MAX: 120000        UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999999 = Missing.

FLD LEN: 1
    SNOW-DEPTH equivalent water condition code
    The code that denotes specific conditions associated with the measurement of the SNOW-DEPTH.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    9 = Missing (no special code to report)

FLD LEN: 1
    SNOW-DEPTH equivalent water condition quality code
    The code that denotes a quality status of the reported SNOW-DEPTH equivalent water condition
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
    A = Data value flagged as suspect, but accepted as good value
    I = Data value not originally in data, but inserted by validator
    M = Manual change made to value based on information provided by NWS or FAA
    P = Data value not originally flagged as suspect, but replaced by validator
    R = Data value replaced with value computed by NCEI software
    U = Data value replaced with edited value


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    SNOW-DEPTH GREATEST DEPTH ON THE GROUND, FOR THE MONTH identifier
    The identifier that represents SNOW-DEPTH GREATEST SNOW DEPTH ON THE GROUND, data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AK1 An indicator of the following items:
    SNOW-DEPTH depth dimension
    SNOW-DEPTH condition code
    SNOW-DEPTH dates of occurrence
    SNOW-DEPTH quality code

FLD LEN: 4
    SNOW-DEPTH GREATEST DEPTH ON THE GROUND, FOR THE MONTH depth dimension
    The depth of GREATEST SNOW DEPTH FOR THE MONTH.
    MIN: 0000     MAX: 1500      UNITS: centimeters
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    SNOW-DEPTH GREATEST DEPTH ON THE GROUND, FOR THE MONTH condition code
    The code that denotes whether a SNOW-DEPTH dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace



    22


---

    3 = The amount occurred on other dates in addition to those listed
    4 = Trace amount occurred on other dates in addition to those listed
    9 = Missing or N/A

FLD LEN: 6
    SNOW-DEPTH GREATEST DEPTH ON THE GROUND, FOR THE MONTH dates of occurrence
    The dates of occurrence of SNOW-DEPTH, given as the date for each occurrence, for up to 3
    occurrences; e.g., 041016 indicates days 04, 10, and 16.
    MIN: 01      MAX: 31
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = missing for each of the 3 sub-fields.

FLD LEN: 1
    SNOW-DEPTH GREATEST DEPTH ON THE GROUND, FOR THE MONTH quality code
    The code that denotes a quality status of the reported SNOW-DEPTH data.
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

FLD LEN: 3
    SNOW-ACCUMULATION occurrence identifier
    The identifier that represents an episode of SNOW-ACCUMULATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AL1 - AL4 An indicator of up to 4 repeating fields of the following items:
    SNOW-ACCUMULATION period quantity
    SNOW-ACCUMULATION depth dimension
    SNOW-ACCUMULATION condition code
    SNOW-ACCUMULATION quality code

FLD LEN: 2
    SNOW-ACCUMULATION period quantity
    The quantity of time over which the SNOW-ACCUMULATION occurred.
    MIN: 00      MAX: 72       UNITS: Hours
    SCALING FACTOR: 1
    DOM: A general domain comprised of the characters in the ASCII character set.
    99 = Missing.

FLD LEN: 3
    SNOW-ACCUMULATION depth dimension
    The depth of a SNOW-ACCUMULATION.
    MIN: 000      MAX: 500   UNITS: centimeters
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing.

FLD LEN: 1
    SNOW-ACCUMULATION condition code
    The code that denotes specific conditions associated with the measurement of the depth of a SNOW-ACCUMULATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Snow cover not continuous
    3 = Trace
    4 = End accumulated period (data include more than one day)
    5 = End deleted period (data eliminated due to quality problems)
    6 = End missing period
    E = Estimated data value (eg, from nearby station)
    9 = Missing

FLD LEN: 1
    SNOW-ACCUMULATION quality code



    23


---

    The code that denotes a quality status of the reported SNOW-ACCUMULATION.
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
    SNOW-ACCUMULATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH identifier
    The identifier that represents SNOW-ACCUMULATION, GREATEST IN 24 HOURS, data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AM1: An indicator of the following items:
    SNOW-ACCUMULATION depth dimension
    SNOW-ACCUMULATION condition code
    SNOW-ACCUMULATION dates of occurrence (3 fields)
    SNOW-ACCUMULATION quality code

FLD LEN: 4
    SNOW-ACCUMULATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH depth dimension
    The depth of SNOW-ACCUMULATION for the 24-hour period.
    MIN: 0000     MAX: 2000      UNITS: centimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    SNOW-ACCUMULATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH condition code
    The code that denotes whether a SNOW-ACCUMULATION depth dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    3 = The amount occurred on other dates in addition to those listed
    4 = Trace amount occurred on other dates in addition to those listed
    9 = Missing

FLD LEN: 4
    SNOW-ACCUMULATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH dates of occurrence
    The dates of occurrence of SNOW-ACCUMULATION, given as the begin-end date for the 24-hour period, for up to 3
    occurrences; e.g., 0405 indicates 24-hour period on days 04-05.
    MIN: 0101      MAX: 3131
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 4
    SNOW-ACCUMULATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH dates of occurrence
    The dates of occurrence of SNOW-ACCUMULATION, given as the begin-end date for the 24-hour period, for up to 3
    occurrences; e.g., 0405 indicates 24-hour period on days 04-05.
    MIN: 0101      MAX: 3131
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 4
    SNOW-ACCUMULATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH dates of occurrence
    The dates of occurrence of SNOW-ACCUMULATION, given as the begin-end date for the 24-hour period, for up to 3
    occurrences; e.g., 0405 indicates 24-hour period on days 04-05.
    MIN: 0101      MAX: 3131
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.




    24


---

FLD LEN: 1
    SNOW-ACCUMULATION GREATEST AMOUNT IN 24 HOURS, FOR THE MONTH quality code
    The code that denotes a quality status of the reported SNOW-ACCUMULATION data.
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

FLD LEN: 3
    SNOW-ACCUMULATION FOR THE DAY/MONTH occurrence identifier
    The identifier that represents SNOW-ACCUMULATION MONTHLY TOTAL.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AN1: An indicator for the occurrence of the following items:
    SNOW-ACCUMULATION period quantity
    SNOW-ACCUMULATION depth dimension
    SNOW-ACCUMULATION condition code
    SNOW-ACCUMULATION quality code

FLD LEN: 3
    SNOW-ACCUMULATION period quantity
    The quantity of time over which the SNOW-ACCUMULATION occurred (usually 024 for daily, 744 for monthly)
    MIN: 001       MAX: 744       UNITS: Hours
    SCALING FACTOR: 1
    DOM: A general domain comprised of the characters in the ASCII character set.
    999 = Missing.

FLD LEN: 4
    SNOW ACCUMULATION FOR THE MONTH depth dimension
    The depth of a SNOW-ACCUMULATION.
    MIN: 0000      MAX: 9998   UNITS: centimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    SNOW-ACCUMULATION FOR THE MONTH condition code
    The code that denotes specific conditions associated with the measurement of the depth of a SNOW-ACCUMULATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Snow cover not continuous
    3 = Trace
    4 = End accumulated period (data may include more than one month)
    5 = End deleted period (data eliminated due to quality problems)
    6 = End missing period
    7 = Data will be included in subsequent observation
    E = Estimated data value (eg, from nearby station)
    9 = Missing




    25


---

FLD LEN: 1
    SNOW-ACCUMULATION FOR THE MONTH quality code
    The code that denotes a quality status of the reported SNOW-ACCUMULATION FOR THE MONTH.
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
    LIQUID-PRECIPITATION occurrence identifier
    The identifier that represents an episode of LIQUID-PRECIPITATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AO1 - AO4: An indicator of up to 4 repeating fields of the following items:
    LIQUID-PRECIPITATION period quantity
    LIQUID-PRECIPITATION depth dimension
    LIQUID-PRECIPITATION condition code
    LIQUID-PRECIPITATION quality code

FLD LEN: 2
    LIQUID-PRECIPITATION period quantity in minutes
    The quantity of time over which the LIQUID-PRECIPITATION was measured.
    MIN: 00      MAX: 98       UNITS: Minutes
    SCALING FACTOR: 1
    DOM: A specific domain comprised of the characters in the ASCII character set
    99 = Missing.

FLD LEN: 4
    LIQUID-PRECIPITATION depth dimension
    The depth of LIQUID-PRECIPITATION that is measured at the time of an observation.
    MIN: 0000      MAX: 9998     UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    LIQUID-PRECIPITATION condition code
    The code that denotes whether a LIQUID-PRECIPITATION depth dimension was a trace value.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    1 = Measurement impossible or inaccurate
    2 = Trace
    3 = Begin accumulated period (precipitation amount missing until end of accumulated period)
    4 = End accumulated period
    5 = Begin deleted period (precipitation amount missing due to data problem)
    6 = End deleted period
    7 = Begin missing period
    8 = End missing period
    E = Estimated data value (eg, from nearby station)
    I = Incomplete precipitation amount, excludes one or more missing reports, such as one or more minute reports
    not included in the 1-hour precipitation total
    J = Incomplete precipitation amount, excludes one or more erroneous reports, such as one or more 1-hour
    precipitation amounts excluded from the 24-hour total
    9 = Missing




    26


---

FLD LEN: 1
    LIQUID-PRECIPITATION quality code
    The code that denotes a quality status of the reported LIQUID-PRECIPITATION data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    4 = Passed gross limits check, from DSI-3260 or NCEI ASOS/AWOS
    5 = Passed all quality control checks, from DSI-3260 or NCEI ASOS/AWOS
    6 = Suspect, from DSI-3260 or NCEI ASOS/AWOS
    7 = Erroneous, from DSI-3260 or NCEI ASOS/AWOS
    9 = Passed gross limits check if element is present


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
FLD LEN: 3
    15 Minute LIQUID-PRECIPITATION occurrence identifier
    The identifier that represents an episode of LIQUID-PRECIPITATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    IMPORTANT NOTE: These data are also provided in the AAx section for typical use in applications. The APx data are mainly
    intended for quality control processing.
    AP1 Indicates HPD gauge value 45 minutes prior to observation time
    AP2 Indicates HPD gauge value 30 minutes prior to observation time
    AP3 Indicates HPD gauge value 15 minutes prior to observation time
    AP4 Indicates HPD gauge value at observation time
    LIQUID-PRECIPITATION depth dimension
    LIQUID-PRECIPITATION condition code
    LIQUID-PRECIPITATION quality code

FLD LEN: 4
    HPD (Hourly Precipitation Data network) gauge value
    The HPD Gauge value that is measured at the time indicated.
    MIN: 0000 MAX: 9998 UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing

FLD LEN: 1
    HPD gauge value condition code
    Not used at this time. Value set to missing.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    9=Missing

FLD LEN: 1
    HPD gauge value quality code
    The code that denotes a quality status of the reported gauge value.
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
