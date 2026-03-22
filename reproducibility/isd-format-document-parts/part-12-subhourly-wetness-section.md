## Part 12 - Subhourly Wetness Section


---

FLD LEN: 3
    Subhourly Wetness Section identifier
    The identifier that indicates a subhourly wetness sensor observation.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CW1 An indicator of the following items:
    WET1 wetness indicator
    WET1_QC quality code
    WET1_FLAG quality code
    WET2 wetness indicator
    WET2_QC quality code
    WET2_FLAG quality code

FLD LEN: 5
    WET1 wetness indicator
    Wetness sensor channel 1 value indicating the existence or non-existence of moisture on the sensor.
    MIN: 00000     MAX: 99999
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    WET1_QC quality code
    The code that indicates ISD's evaluation of the quality status of the wetness sensor channel 1 value.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    WET1_FLAG quality code
    The code that indicates ISD's evaluation of the quality status of the wetness sensor channel 1 value.
    Most users will find the preceding quality code WET1_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks
FLD LEN: 5
    WET2 wetness indicator
    Wetness sensor channel 2 value indicating the existence or non-existence of moisture on the sensor.
    MIN: 00000        MAX: 99999
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    WET2_QC quality code
    The code that indicates ISD's evaluation of the quality status of the wetness sensor channel 2 value.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing




    50


---

FLD LEN: 1
    WET2_FLAG quality code
    The code that indicates ISD's evaluation of the quality status of the wetness sensor channel 2 value.
    Most users will find the preceding quality code WET2_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
