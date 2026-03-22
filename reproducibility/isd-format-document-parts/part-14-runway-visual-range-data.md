## Part 14 - Runway Visual Range Data

Runway Visual Range Data

FLD LEN: 3
    RUNWAY-VISUAL-RANGE-OBSERVATION identifier
    The identifier that indicates the occurrence of a runway visibility report.
    DOM: A specific domain comprised of the ASCII characters.
    ED1 An indicator of the following items:
    RUNWAY-VISUAL-RANGE-OBSERVATION direction angle
    RUNWAY-VISUAL-RANGE-OBSERVATION runway designator code
    RUNWAY-VISUAL-RANGE-OBSERVATION visibility dimension
    RUNWAY-VISUAL-RANGE-OBSERVATION quality code

FLD LEN: 2
    RUNWAY-VISUAL-RANGE-OBSERVATION direction angle
    The angle as measured from magnetic north to the runway along which the
    visibility is observed.
    MIN: 01            MAX: 36        UNITS: Tens of degrees
    SCALING FACTOR: 1/10
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing

FLD LEN: 1
    RUNWAY-VISUAL-RANGE-OBSERVATION runway designator code
    The code that denotes the left, right or center runway as the one to which the
    visibility applies.
    DOM: A specific domain comprised of the ASCII characters:
    L = left
    C = center
    R = right
    U = unknown
    9 = missing

FLD LEN: 4
    RUNWAY-VISUAL-RANGE-OBSERVATION visibility dimension
    The dimension of the horizontal distance that can be seen along the runway.
    MIN: 0000           MAX: 5000            UNITS: meters
    DOM: A general domain comprised of the ASCII characters 0-9.
    9999 = Missing

FLD LEN: 1
    RUNWAY-VISUAL-RANGE-OBSERVATION quality code
    The code that denotes a quality status of the reported RUNWAY-VISUAL-RANGE-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀




    53


---
