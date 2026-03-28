## Part 2 - Control Data Section

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
    Control Data Section
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

POS: 1-4
    TOTAL-VARIABLE-CHARACTERS (this includes remarks, additional data, and element quality section)
    The number of characters in the variable data section. The total record length = 105 + the value stored in this field.
    DOM: A general domain comprised of the characters in the ASCII character set.
    MIN: 0000 MAX: 9999

POS: 5-10
    FIXED-WEATHER-STATION USAF MASTER STATION CATALOG identifier
    The identifier that represents a FIXED-WEATHER-STATION.
    DOM: A general domain comprised of the characters in the ASCII character set.
    COMMENT: This field includes all surface reporting stations, including ships, buoys, etc.

POS: 11-15
    FIXED-WEATHER-STATION NCEI WBAN identifier
    The identifier that represents a FIXED-WEATHER-STATION.
    MIN: 00000        MAX: 99999
    DOM: A general domain comprised of the numeric characters (0-9).
    COMMENT: This field includes all surface reporting stations, including ships, buoys, etc.

NOTE:
1) For data files obtained via FTP or from NCEI’s archive, the filename convention uses the USAF identifier and the WBAN identifier
in the filename—eg, 723150-03812-year (such as 2006).
2) As additional data sources are integrated into ISD, the 2 station number fields will be used as an 11-digit ID field, with the first 2
digits representing the WMO block number (if applicable).

POS: 16-23
    GEOPHYSICAL-POINT-OBSERVATION date
    The date of a GEOPHYSICAL-POINT-OBSERVATION.
    MIN: 00000101 MAX: 99991231
    DOM: A general domain comprised of integer values 0-9 in the format YYYYMMDD.
    YYYY can be any positive integer value; MM is restricted to values 01-12; and DD is restricted to values 01-31.

POS: 24-27
    GEOPHYSICAL-POINT-OBSERVATION time
    The time of a GEOPHYSICAL-POINT-OBSERVATION based on
    Coordinated Universal Time Code (UTC).
    MIN: 0000        MAX: 2359
    DOM: A general domain comprised of integer values 0-9 in the format HHMM.
    HH is restricted to values 00-23; MM is restricted to values 00-59.

POS: 28-28
    GEOPHYSICAL-POINT-OBSERVATION data source flag
    The flag of a GEOPHYSICAL-POINT-OBSERVATION showing the source or combination of sources used in creating the
    observation.
    MIN: 1        MAX: Z
    DOM: A general domain comprised of values 1-9 and A-N.
    1 = USAF SURFACE HOURLY observation, candidate for merge with NCEI SURFACE HOURLY (not yet merged,
    element cross-checks)
    2 = NCEI SURFACE HOURLY observation, candidate for merge with USAF SURFACE HOURLY (not yet merged,
    failed element cross-checks)
    3 = USAF SURFACE HOURLY/NCEI SURFACE HOURLY merged observation
    4 = USAF SURFACE HOURLY observation
    5 = NCEI SURFACE HOURLY observation
    6 = ASOS/AWOS observation from NCEI
    7 = ASOS/AWOS observation merged with USAF SURFACE HOURLY observation
    8 = MAPSO observation (NCEI)
    A = USAF SURFACE HOURLY/NCEI HOURLY PRECIPITATION merged observation, candidate for merge with
    NCEI SURFACE HOURLY (not yet merged, failed element cross-checks)
    B = NCEI SURFACE HOURLY/NCEI HOURLY PRECIPITATION merged observation, candidate for merge with
    USAF SURFACE HOURLY (not yet merged, failed element cross-checks)
    C = USAF SURFACE HOURLY/NCEI SURFACE HOURLY/NCEI HOURLY PRECIPITATION merged observation
    D = USAF SURFACE HOURLY/NCEI HOURLY PRECIPITATION merged observation
    E = NCEI SURFACE HOURLY/NCEI HOURLY PRECIPITATION merged observation


    5


---

    F = Form OMR/1001 – Weather Bureau city office (keyed data)
    G = SAO surface airways observation, pre-1949 (keyed data)
    H = SAO surface airways observation, 1965-1981 format/period (keyed data)
    I = Climate Reference Network observation
    J = Cooperative Network observation
    K = Radiation Network observation
    L = Data from Climate Data Modernization Program (CDMP) data source
    M = Data from National Renewable Energy Laboratory (NREL) data source
    N = NCAR / NCEI cooperative effort (various national datasets)
    O = Summary observation created by NCEI using hourly observations that may not share the same data source flag.
    9 = Missing

Note: Latitude, longitude, elevation, and call letters for some locations with data from multiple sources (see data source
flag above) will sometimes vary within a data file due to differences in the metadata from the originating source. This does
not indicate that the station locations differ; only that the metadata have not yet been fully reflected in the data records.

POS: 29-34
    GEOPHYSICAL-POINT-OBSERVATION latitude coordinate
    The latitude coordinate of a GEOPHYSICAL-POINT-OBSERVATION where Southern Hemisphere is negative.
    MIN: -90000       MAX: +90000
    UNITS: Angular Degrees
    SCALING FACTOR: 1000
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +99999 = Missing

POS: 35-41
    GEOPHYSICAL-POINT-OBSERVATION longitude coordinate
    The longitude coordinate of a GEOPHYSICAL-POINT-OBSERVATION where values west from 000000 to 179999 are
    signed negative.
    MIN: -179999      MAX: +180000       UNITS: Angular Degrees
    SCALING FACTOR: 1000
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +999999 = Missing

POS: 42-46
    GEOPHYSICAL-REPORT-TYPE code
    The code that denotes the type of geophysical surface observation.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    AERO = Aerological report
    AUST = Dataset from Australia
    AUTO = Report from an automatic station
    BOGUS = Bogus report
    BRAZ = Dataset from Brazil
    COOPD = US Cooperative Network summary of day report
    COOPS = US Cooperative Network soil temperature report
    CRB = Climate Reference Book data from CDMP
    CRN05 = Climate Reference Network report, with 5-minute reporting interval
    CRN15 = Climate Reference Network report, with 15-minute reporting interval
    FM-12 = SYNOP Report of surface observation form a fixed land station
    FM-13 = SHIP Report of surface observation from a sea station
    FM-14 = SYNOP MOBIL Report of surface observation from a mobile land station
    FM-15 = METAR Aviation routine weather report
    FM-16 = SPECI Aviation selected special weather report
    FM-18 = BUOY Report of a buoy observation
    GREEN = Dataset from Greenland
    MESOH – Hydrological observations from MESONET operated civilian or government agency
    MESOS – MESONET operated civilian or government agency
    MESOW – Snow observations from MESONET operated civilian or government agency
    MEXIC = Dataset from Mexico
    NSRDB = National Solar Radiation Data Base
    PCP15 = US 15-minute precipitation network report
    PCP60 = US 60-minute precipitation network report
    S-S-A = Synoptic, airways, and auto merged report
    SA-AU = Airways and auto merged report
    SAO = Airways report (includes record specials)
    SAOSP = Airways special report (excluding record specials)
    SHEF = Standard Hydrologic Exchange Format
    SMARS = Supplementary airways station report
    SOD = Summary of day report from U.S. ASOS or AWOS station



    6


---

    SOM = Summary of month report from U.S. ASOS or AWOS station
    SURF = Surface Radiation Network report
    SY-AE = Synoptic and aero merged report
    SY-AU = Synoptic and auto merged report
    SY-MT = Synoptic and METAR merged report
    SY-SA = Synoptic and airways merged report
    WBO = Weather Bureau Office
    WNO = Washington Naval Observatory
    99999 = Missing


POS: 47-51
    GEOPHYSICAL-POINT-OBSERVATION elevation dimension
    The elevation of a GEOPHYSICAL-POINT-OBSERVATION relative to Mean Sea Level (MSL).
    MIN: -0400       MAX: +8850   UNITS: Meters
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9), a minus sign (-), and a plus sign (+).
    +9999 = Missing

POS: 52-56
    FIXED-WEATHER-STATION call letter identifier
    The identifier that represents the call letters assigned to a FIXED-WEATHER-STATION.
    DOM: A general domain comprised of the characters in the ASCII character set.
    99999 = Missing.

POS: 57-60
    METEOROLOGICAL-POINT-OBSERVATION quality control process name
    The name of the quality control process applied to a weather observation.
    DOM: A general domain comprised of the ASCII character set.
    V01 = No A or M Quality Control applied
    V02 = Automated Quality Control
    V03 = subjected to Quality Control




    7


---
