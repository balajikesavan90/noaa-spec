## Part 9 - Subhourly Temperature Section


---

FLD LEN: 3
    Subhourly Temperature Section identifier
    The identifier that indicates one of three concurrent air temperature observations made by co-located sensors.
    Three instances of this section (corresponding to the three temperature sensors) appear in each of the twelve



    46


---

    5-minute data stream records. In the 15-minute data stream, the three instances of this section appear in the
    last record of the hour, and contain the average temperature for the last 5 minutes of the hour.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CT1, CT2, CT3 Three indicators preceding three copies of the following items:
    AVG_TEMP air temperature
    AVG_TEMP_QC quality code
    AVG_TEMP_FLAG quality code

FLD LEN: 5
    AVG_TEMP air temperature
    The average air temperature for a 5-minute period.
    MIN: -9999       MAX: +9998       UNITS: degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus
    sign (-).
    +9999 = Missing.

FLD LEN: 1
    AVG_TEMP_QC quality code
    The code that indicates ISD's evaluation of the quality status of the 5-minute air temperature average.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    AVG_TEMP_FLAG quality code
    A flag that indicates the network's internal evaluation of the quality status of the 5-minute air temperature average.
    Most users will find the preceding quality code AVG_TEMP_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
