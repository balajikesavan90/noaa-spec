## Part 13 - Hourly Geonor Vibrating Wire Summary Section


---

FLD LEN: 3
    Hourly Geonor Vibrating Wire Summary Section identifier
    The identifier that indicates the presence of summary data for three concurrent precipitation observations made
    by co-located sensors. It appears in the last ISD record of the hour for the 15-minute data stream only. This
    section is not present for the 5-minute data stream.
    Note: This section contains the frequencies which are the fundamental output from a vibrating wire transducer. They
    were transmitted as part of datastream versions which held 15 minute precipitation values. When the 5 minute
    datastream was defined, the decision was made to transmit engineering units such as millimeters which could be
    reversed to the fundamental output values using the formulas and coefficients found in the metadata.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CX1, CX2, CX3 An indicator of the following items:
    PRECIPITATION total hourly precipitation
    PRECIP_QC quality code
    PRECIP_FLAG quality code
    FREQ_AVG hourly average frequency
    FREQ_AVG_QC quality code
    FREQ_AVG_FLAG
    FREQ_MIN hourly minimum frequency
    FREQ_MIN_QC quality code
    FREQ_MIN_FLAG quality code
    FREQ_MAX hourly maximum frequency
    FREQ_MAX_QC quality code
    FREQ_MAX_FLAG quality code

FLD LEN: 6
    PRECIPITATION total hourly precipitation
    The total hourly precipitation amount for the sensor.
    MIN: -99999       MAX: +99999          UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-)
    +99999 = Missing.

FLD LEN: 1
    PRECIP_QC quality code
    The code that indicates ISD's evaluation of the quality status of the hourly precipitation amount.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing
FLD LEN: 1
    PRECIP_FLAG quality code
    The code that indicates the network's internal evaluation of the quality status of the hourly precipitation amount. Most
    users will find the preceding quality code PRECIP_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 4
    FREQ_AVG hourly average frequency
    The hourly average frequency for the sensor.
    MIN: 0000      MAX: 9999       UNITS: Hertz
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.




    51


---

FLD LEN: 1
    FREQ_AVG_QC quality code
    The code that indicates ISD's evaluation of the quality status of the hourly average frequency.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    FREQ_AVG_FLAG quality code
    The code that indicates the network's internal evaluation of the quality status of the hourly average frequency. Most
    users will find the preceding quality code FREQ_AVG_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 4
    FREQ_MIN hourly minimum frequency
    The minimum frequency during the hour for the sensor.
    MIN: 0000     MAX: 9998        UNITS: Hertz
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    FREQ_MIN_QC quality code
    The code that indicates ISD's evaluation of the quality status of the hourly minimum frequency.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    FREQ_MIN_FLAG quality code
    The code that indicates the network's internal evaluation of the quality status of the hourly minimum frequency. Most
    users will find the preceding quality code FREQ_MIN_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 4
    FREQ_MAX hourly maximum frequency
    The minimum frequency during the hour for the sensor.
    MIN: 0000     MAX: 9998       UNITS: Hertz
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    FREQ_MAX_QC quality code
    The code that indicates ISD's evaluation of the quality status of the hourly maximum frequency.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    FREQ_MAX_FLAG quality code
    The code that indicates the network's internal evaluation of the quality status of the hourly maximum frequency. Most
    users will find the preceding quality code FREQ_MAX_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
