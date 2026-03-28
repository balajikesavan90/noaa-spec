## Part 29 - Wind Data

Wind Data

FLD LEN: 3
    SUPPLEMENTARY-WIND-OBSERVATION identifier
    The identifier that denotes the start of a SUPPLEMENTARY-WIND-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    OA1 - OA3: An indicator of up to 3 occurrences of the following item:
    SUPPLEMENTARY-WIND-OBSERVATION type code
    SUPPLEMENTARY-WIND-OBSERVATION period quantity
    SUPPLEMENTARY-WIND-OBSERVATION speed rate
    SUPPLEMENTARY-WIND-OBSERVATION speed rate quality code

FLD LEN: 1
    SUPPLEMENTARY-WIND-OBSERVATION type code
    The code that denotes a type of SUPPLEMENTARY-WIND-OBSERVATION.
    DOM: A specific domain comprised of the ASCII characters.
    1 = Average speed of prevailing wind
    2 = Mean wind speed
    3 = Maximum instantaneous wind speed
    4 = Maximum gust speed
    5 = Maximum mean wind speed
    6 = Maximum 1-minute mean wind speed
    9 = Missing

FLD LEN: 2
    SUPPLEMENTARY-WIND-OBSERVATION period quantity
    The quantity of time over which a SUPPLEMENTARY-WIND-OBSERVATION occurred.
    MIN: 01          MAX: 48          UNITS: Hours
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing

FLD LEN: 4
    SUPPLEMENTARY-WIND-OBSERVATION speed rate
    The rate of horizontal speed of air reported in the SUPPLEMENTARY-WIND-OBSERVATION.
    MIN: 0000       MAX: 2000       UNITS: Meters per Second
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing

FLD LEN: 1
    SUPPLEMENTARY-WIND-OBSERVATION speed rate quality code
    The code that denotes a quality status of the reported SUPPLEMENTARY-WIND-OBSERVATION speed rate.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect


    98


---

    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    Hourly/Sub-Hourly Wind Section identifier
    The identifier that indicates an observation of wind speed at a height of 1.5 meters from the ground, typically
    used by Climate Reference Network stations. This section appears one or more time per hour. The wind average value
    in this section is a duplicate of the wind average value in the mandatory data section. It is included in this section so that
    all wind values are conveniently available in a single section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    OB1, OB2: An indicator of the following items:
    WIND_AVG time period
    WIND_MAX maximum gust
    WIND_MAX_QC quality code
    WIND_MAX_FLAG quality code
    WIND_MAX direction of the maximum gust
    WIND_MAX_QC direction quality code
    WIND_MAX_FLAG direction quality code
    WIND_STD wind speed standard deviation
    WIND_STD_QC quality code
    WIND_STD_FLAG quality code
    WIND_DIR_STD wind direction standard deviation
    WIND_DIR_STD_QC quality code
    WIND_DIR_STD_FLAG quality code

FLD LEN: 3
    WIND_AVG Time period in minutes, for which the data in this section (OB1) pertains—eg, 060 = 60 minutes (1
hour).
    MIN: 001       MAX: 998      UNITS: Minutes
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing.

FLD LEN: 4
    WIND_MAX maximum gust
    The maximum 10 second wind speed.
    MIN: 0000       MAX: 9998      UNITS: meters per second
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    WIND_MAX_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the maximum gust.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    WIND_MAX_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the maximum gust. Most users will find the
    preceding quality code WIND_MAX_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 8 = Did not pass all quality checks
    9 = Missing

FLD LEN: 3
    WIND_MAX direction of the maximum gust
    The direction measured in clockwise angular degrees from which the maximum 10 second wind speed occurred.
    MIN: 001        MAX: 360       UNITS: Angular degrees
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing.




    99


---

FLD LEN: 1
    WIND_MAX_QC direction quality code
    The code that indicates ISD’s evaluation of the quality status of the maximum gust direction.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    WIND_MAX_FLAG direction quality code
    A flag that indicates the network’s internal evaluation of the quality status of the maximum gust direction. Most users will
    find the preceding quality code WIND_MAX_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 8 = Did not pass all quality checks
    9 = Missing

FLD LEN: 5
    WIND_STD wind speed standard deviation
    The wind speed standard deviation.
    MIN: 00000        MAX: 99998
    SCALING FACTOR: 100
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    WIND_STD_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the wind speed standard deviation.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    WIND_STD_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the wind speed standard deviation. Most
    users will find the preceding quality code WIND_STD_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 8 = Did not pass all quality checks
    9 = Missing

FLD LEN: 5
    WIND_DIR_STD wind direction standard deviation
    The wind direction standard deviation.
    MIN: 00000         MAX: 99998
    SCALING FACTOR: 100
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    WIND_DIR_STD_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the wind direction standard deviation.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    WIND_DIR_STD_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the wind direction standard deviation. Most
    users will find the preceding quality code WIND_STD_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 8 = Did not pass all quality checks
    9 = Missing


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀



    100


---

FLD LEN: 3
    WIND-GUST-OBSERVATION identifier
    The identifier that denotes the start of a WIND-GUST-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    OC1: An indicator of the occurrence of the following item:
    WIND-GUST-OBSERVATION speed rate
    WIND-GUST-OBSERVATION quality code

FLD LEN: 4
    WIND-GUST-OBSERVATION speed rate
    The rate of speed of a wind gust.
    MIN: 0050      MAX: 1100      UNITS: Meters per second
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing

FLD LEN: 1
    WIND-GUST-OBSERVATION quality code
    The code that denotes a quality status of a reported WIND-GUST-OBSERVATION speed rate.
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
    SUPPLEMENTARY-WIND-OBSERVATION identifier
    The identifier that denotes the start of a SUPPLEMENTARY-WIND-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    OD1 - OD3: An indicator of up to 3 occurrences of the following item:
    SUPPLEMENTARY-WIND-OBSERVATION type code
    SUPPLEMENTARY-WIND-OBSERVATION period quantity
    SUPPLEMENTARY-WIND-OBSERVATION direction quantity
    SUPPLEMENTARY-WIND-OBSERVATION speed rate
    SUPPLEMENTARY-WIND-OBSERVATION speed rate quality code

FLD LEN: 1
    SUPPLEMENTARY-WIND-OBSERVATION type code
    The code that denotes a type of SUPPLEMENTARY-WIND-OBSERVATION.
    DOM: A specific domain comprised of the ASCII characters.
    1 = Average speed of prevailing wind
    2 = Mean wind speed
    3 = Maximum instantaneous wind speed
    4 = Maximum gust speed
    5 = Maximum mean wind speed
    6 = Maximum 1-minute mean wind speed
    9 = Missing
FLD LEN: 2
    SUPPLEMENTARY-WIND-OBSERVATION period quantity
    The quantity of time over which a SUPPLEMENTARY-WIND-OBSERVATION occurred.
    MIN: 01          MAX: 48          UNITS: Hours
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing




    101


---

FLD LEN: 4
    SUPPLEMENTARY-WIND-OBSERVATION speed rate
    The rate of horizontal speed of air reported in the SUPPLEMENTARY-WIND-OBSERVATION.
    MIN: 0000       MAX: 2000       UNITS: Meters per Second
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing

FLD LEN: 1
    SUPPLEMENTARY-WIND-OBSERVATION speed rate quality code
    The code that denotes a quality status of the reported SUPPLEMENTARY-WIND-OBSERVATION speed rate.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = missing
 FLD LEN: 3
    SUPPLEMENTARY-WIND-OBSERVATION direction quantity
    The angle, measured in a clockwise direction, between true north and the direction from which the wind is blowing.
    MIN: 001      MAX: 360       UNITS: Angular Degrees
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing
    Note: A direction of 999 with a speed of 0000 indicates calm conditions (0 wind speed).




FLD LEN: 3
    SUMMARY-OF-DAY-WIND-OBSERVATION identifier
    The identifier that denotes the start of a SUMMARY-OF-DAY-WIND-OBSERVATION data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    OE1 - OE3: An indicator of up to 3 occurrences of the following item:
    SUMMARY-OF-DAY-WIND-OBSERVATION type code
    SUMMARY-OF-DAY-WIND-OBSERVATION period quantity
    SUMMARY-OF-DAY-WIND-OBSERVATION speed rate
    SUMMARY-OF-DAY-WIND-OBSERVATION direction
    SUMMARY-OF-DAY-WIND-OBSERVATION time of occurrence
    SUMMARY-OF-DAY-WIND-OBSERVATION quality code

FLD LEN: 1
    SUMMARY-OF-DAY-WIND-OBSERVATION type code
    The code that denotes a type of SUMMARY-OF-DAY-WIND-OBSERVATION.
    DOM: A specific domain comprised of the ASCII characters.
    1 = Peak wind speed for the day
    2 = Fastest 2-minute wind speed for the day
    3 = Average wind speed for the day
    4 = Fastest 5-minute wind speed for the day
    5 = Fastest mile wind speed for the day

FLD LEN: 2
    SUMMARY-OF-DAY-WIND-OBSERVATION period quantity
    The quantity of time over which a SUMMARY-OF-DAY-WIND-OBSERVATION occurred.
    MIN: 24          MAX: 24          UNITS: Hours
    DOM: A general domain comprised of the ASCII characters.
    99 = Missing

FLD LEN: 5
    SUMMARY-OF-DAY-WIND-OBSERVATION speed
    The rate of horizontal wind speed of air reported in the SUMMARY-OF-DAY-WIND-OBSERVATION.
    MIN: 00000       MAX: 20000      UNITS: Meters per Second
    SCALING FACTOR: 100
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing




    102


---

FLD LEN: 3
    SUMMARY-OF-DAY-WIND-OBSERVATION direction of wind
    The angle, measured in a clockwise direction, between true north and the direction from which the wind is blowing, for
    the summary of day wind report.
    MIN: 001      MAX: 360       UNITS: Angular Degrees
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing
    Note: A direction of 999 with a speed of 00000 indicates calm conditions (0 wind speed).

FLD LEN: 4
    SUMMARY-OF-DAY-WIND-OBSERVATION time of occurrence in Z-time (UTC)
    The time of occurrence of the wind reported in the SUMMARY-OF-DAY-WIND-OBSERVATION.
    MIN: 0000      MAX: 2359       UNITS: hours-minutes
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing

FLD LEN: 1
    SUMMARY-OF-DAY-WIND-OBSERVATION quality code
    The code that denotes a quality status of the reported SUMMARY-OF-DAY-WIND-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    4 = Passed gross limits check, data originate from an NCEI data source
    5 = Passed all quality control checks, data originate from an NCEI data source
    6 = Suspect, data originate from an NCEI data source
    7 = Erroneous, data originate from an NCEI data source
    M = Manual change made to value based on information provided by NWS or FAA
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    RELATIVE HUMIDITY occurrence identifier
    The identifier that denotes the start of a RELATIVE-HUMIDITY data section
    DOM: A specific domain comprised of the characters in the ASCII character set
    RH1 – RH3: An indicator of up to 3 occurrences of the following items
    RELATIVE HUMIDITY period quantity
    RELATIVE HUMIDITY code
    RELATIVE HUMIDITY percentage
    RELATIVE HUMIDITY derived code
    RELATIVE HUMIDITY quality code

FLD LEN: 3
    RELATIVE HUMIDITY period quantity
    The quantity of time over which relative humidity percentages were averaged to determine the RELATIVE HUMIDITY
    MIN: 001 MAX: 744 UNITS: Hours
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9)
    999 = missing

FLD LEN: 1
    RELATIVE HUMIDITY code
    The code that denotes the RELATIVE HUMIDITY as an average, maximum or minimum
    DOM: A specific domain comprised of the characters in the ASCII character set
    M = Mean relative humidity
    N = Minimum relative humidity
    X = Maximum relative humidity
    9 = missing

FLD LEN: 3
    RELATIVE HUMIDITY percentage
    The average maximum or minimum relative humidity for a given period, typically for the day or month, derived from
    other data fields. Note: Values only take into account hourly observations (not specials or other unscheduled
    observations).
    MIN: 000          MAX: 100       UNITS: percent
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = missing




    103


---

FLD LEN: 1
    RELATIVE HUMIDITY derived code
    The code that denotes a derived code of the reported RELATIVE HUMIDITY percentage.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    D = Derived from hourly values
    9 = missing


FLD LEN: 1
    RELATIVE HUMIDITY quality code
    The code that denotes a quality status of the reported RELATIVE HUMIDITY percentage
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

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀


Sea Surface Temperature Data

FLD LEN: 3
    SEA-SURFACE-TEMPERATURE-OBSERVATION identifier
    The identifier that denotes the start of a SEA-SURFACE-TEMPERATURE-OBSERVATION temperature data section.
    DOM: A specific domain comprised of the characters in the ASCII character.
    SA1: An indicator of the occurrence of the following item:
    SEA-SURFACE-TEMPERATURE-OBSERVATION temperature
    SEA-SURFACE-TEMPERATURE-OBSERVATION temperature quality code

FLD LEN: 4
    SEA-SURFACE-TEMPERATURE-OBSERVATION temperature
    The temperature of the water at the surface.
    MIN: -050     MAX: +450        UNITS: Degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters(0-9), a plus sign (+), and a minus sign (-).
    +999 = Missing

FLD LEN: 1
    SEA-SURFACE-TEMPERATURE-OBSERVATION temperature quality code
    The code that denotes a quality status of the reported SEA-SURFACE-TEMPERATURE-OBSERVATION temperature
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀




    104


---
