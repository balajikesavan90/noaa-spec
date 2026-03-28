## Part 7 - Network Metadata

Network Metadata

FLD LEN: 3
    US-NETWORK-METADATA identifier
    The identifier that indicates the occurrence of US Network metadata, used in NCEI data processing.
    DOM: A specific domain comprised of the ASCII characters.
    CO1 An indicator of the following item:
    NETWORK-METADATA climate division number
    NETWORK-METADATA UTC-LST time conversion

FLD LEN: 2
    NETWORK-METADATA climate division number
    The climate division number, for this station, within the US state that it resides.
    MIN: 00          MAX: 09              UNITS: N/A
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing

FLD LEN: 3
    NETWORK-METADATA UTC-LST time conversion
    The UTC to LST time conversion for this station.
    MIN: -12        MAX: +12            UNITS: hours
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-)
    +99 = Missing

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀




    45


---

FLD LEN: 3
    US-COOPERATIVE-NETWORK-ELEMENT-TIME-OFFSET identifier
    The identifier that indicates a specified element's observation time differs from the time listed in "Control Section".
    DOM: A specific domain comprised of the ASCII characters.
    CO2 - CO9 An indicator of up to 8 repeating fields of the following item:
    COOPERATIVE-NETWORK-ELEMENT-ID
    COOPERATIVE-NETWORK-TIME-OFFSET

FLD LEN: 3
    COOPERATIVE-NETWORK-ELEMENT-ID
    The element identifier to be offset, based on the identifier as shown in this document.
    DOM: A general domain comprised of the characters in the ASCII character set.
    999 = Missing

FLD LEN: 5
    COOPERATIVE-NETWORK-TIME-OFFSET
    The offset in hours. To obtain the actual observation time of the element/parameter indicated, add the value in this field
    to the date-time value in the “Control Section.”
    MIN: -9999        MAX: +9998            UNITS: Hours
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +9999 = Missing



