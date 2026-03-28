## Part 8 - CRN Control Section


---

FLD LEN: 3
    CRN Control Section identifier
    The identifier that indicates an occurrence of datalogger program information.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CR1 An indicator of the following items:
    DL_VN identifier
    DL_VN _QC quality code
    DL_VN_FLAG quality code
FLD LEN: 5
    DL_VN identifier
    The version number which uniquely identifies the datalogger program that produced the CRN observation for
    this hour. This section appears once in every ISD record.
    MIN: 00000                    MAX: 99998
    SCALING FACTOR: 1000
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = missing

FLD LEN: 1
    DL_VN_QC quality code
    The code that indicates ISD's evaluation of the quality status of the reported datalogger program version number.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    DL_VN_FLAG quality code
    A flag that indicates the network's internal evaluation of the quality status of the reported datalogger program version
    number. Most users will find the preceding quality code DL_VN_QC to be the simplest and most useful
    quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks
