FEDERAL CLIMATE COMPLEX
    DATA DOCUMENTATION
    FOR
   INTEGRATED SURFACE DATA
    (ISD)

    January 12, 2018

NOAA - National Centers for Environmental Information
    US Air Force - 14th Weather Squadron
    151 Patton Avenue
    Asheville, NC 28801-5001 USA


## Table of Contents
- [Part 1 - Preface and Dataset Overview](#part-1---preface-and-dataset-overview)
- [Part 2 - Control Data Section](#part-2---control-data-section)
- [Part 3 - Mandatory Data Section](#part-3---mandatory-data-section)
- [Part 4 - Additional Data Section](#part-4---additional-data-section)
- [Precipitation Data](#precipitation-data)
- [Part 5 - Weather Occurrence Data](#part-5---weather-occurrence-data)
- [Part 6 - Climate Reference Network Unique Data](#part-6---climate-reference-network-unique-data)
- [Part 7 - Network Metadata](#part-7---network-metadata)
- [Part 8 - CRN Control Section](#part-8---crn-control-section)
- [Part 9 - Subhourly Temperature Section](#part-9---subhourly-temperature-section)
- [Part 10 - Hourly Temperature Section](#part-10---hourly-temperature-section)
- [Part 11 - Hourly Temperature Extreme Section](#part-11---hourly-temperature-extreme-section)
- [Part 12 - Subhourly Wetness Section](#part-12---subhourly-wetness-section)
- [Part 13 - Hourly Geonor Vibrating Wire Summary Section](#part-13---hourly-geonor-vibrating-wire-summary-section)
- [Part 14 - Runway Visual Range Data](#part-14---runway-visual-range-data)
- [Part 15 - Cloud and Solar Data](#part-15---cloud-and-solar-data)
- [Part 16 - Sunshine Observation Data](#part-16---sunshine-observation-data)
- [Part 17 - Solar Irradiance Section](#part-17---solar-irradiance-section)
- [Part 18 - Net Solar Radiation Section](#part-18---net-solar-radiation-section)
- [Part 19 - Modeled Solar Irradiance Section](#part-19---modeled-solar-irradiance-section)
- [Part 20 - Hourly Solar Angle Section](#part-20---hourly-solar-angle-section)
- [Part 21 - Hourly Extraterrestrial Radiation Section](#part-21---hourly-extraterrestrial-radiation-section)
- [Part 22 - Hail Data](#part-22---hail-data)
- [Part 23 - Ground Surface Data](#part-23---ground-surface-data)
- [Part 24 - Temperature Data](#part-24---temperature-data)
- [Part 25 - Sea Surface Temperature Data](#part-25---sea-surface-temperature-data)
- [Part 26 - Soil Temperature Data](#part-26---soil-temperature-data)
- [Part 27 - Pressure Data](#part-27---pressure-data)
- [Part 28 - Weather Occurrence Data (Extended)](#part-28---weather-occurrence-data-extended)
- [Part 29 - Wind Data](#part-29---wind-data)
- [Part 30 - Marine Data](#part-30---marine-data)

## Part 1 - Preface and Dataset Overview

---

Important notice: In order to accommodate a growing number of stations in the
Integrated Surface Data (ISD), a new methodology for the assignment of
station identifiers is being implemented by approximately January 2013.
Station identifiers which currently appear as an 11-digit numerical field in
positions 5 – 15 of each ISD record in the archive format described in this
document will soon include stations that contain an alphabetic character (A–
Z)for the leading digit (position 5). These assignments will not affect
existing stations unless it becomes necessary to reassign new identifiers to
them. This is occasionally necessary due to station moves or various other
reasons. It will affect most new stations coming into existence after this
implementation occurs. At some point in the future, NCEI will be moving
toward a longer station identifier for ISD. This will extend the current
record layout of the data files and influence all existing station
identifiers which will be reassigned. NCEI will provide further information
on these pending changes as the details are established. You may also keep
abreast of these or other changes by referring to the most recent edition of
the ISD documentation.




1.    Data Set ID:

    DS3505

2.    Data Set Name:

    INTEGRATED SURFACE DATA (ISD)

3.    Data Set Aliases:

    N/A

4.    Access Method and Sort for Archived Data:

The data files are derived from surface observational data, and are stored in
ASCII character format. Data field definitions for elements transmitted are
provided after this preface, providing definition of data fields, position
number for mandatory data fields, field lengths for variable data fields,
minimum/maximum values of transmitted data, and values for missing data
fields. Data are accessible via NCEI’s Climate Data Online system
(cdo.NCEI.noaa.gov), FTP (ftp://ftp.NCEI.noaa.gov/pub/data/noaa/), GIS
services (gis.NCEI.noaa.gov), and by calling NCEI for off-line servicing (see
section 12 below).

Data Sequence - Data will be sequenced using the following data item order:

 1. FIXED-WEATHER-STATION identifier
 2. GEOPHYSICAL-POINT-OBSERVATION date
 3. GEOPHYSICAL-POINT-OBSERVATION time
 4. GEOPHYSICAL-POINT-OBSERVATION latitude coordinates
 5. GEOPHYSICAL-POINT-OBSERVATION longitude coordinates
 6. GEOPHYSICAL-POINT-OBSERVATION type surface report code


    2

  7. GEOPHYSICAL-REPORT-TYPE code

Record Structure - Each record is of variable length and is comprised of a
control and mandatory data section and may also contain additional, remarks,
and element quality data sections.

Maximum record size: 2,844 characters

Maximum block length: 8,192 characters for data provided on tape

Control Data Section - The beginning of each record provides information
about the report including date, time, and station location information. Data
fields will be in positions identified in the applicable data definition.
control data section is fixed length and is 60 characters long.

Mandatory Data Section - The mandatory data section contains meteorological
information on the basic elements such as winds, visibility, and temperature.
These are the most commonly reported parameters and are available most of the
time. The mandatory data section is fixed length and is 45 characters long.

Additional Data Section - Variable length data are provided after the
mandatory data. These additional data contain information of significance
and/or which are received with varying degrees of frequency. Identifiers are
used to note when data are present in the record. If all data fields in a
group are missing, the entire group is usually not reported. If no groups are
reported the section will be omitted. The additional data section is variable
in length with a minimum of 0 characters and a maximum of 637 (634 characters
plus a 3 character section identifier) characters.

Note: Specific information (where applicable) pertaining to each variable
group of data elements is provided in the data item definition.

Remarks Data - The numeric and character (plain language) remarks are
provided if they exist. The data will vary in length and are identified in
the applicable data definition. The remarks section has a maximum length of
515 (512 characters plus a 3 character section identifier) characters.

Element Quality Data Section - The element quality data section contains
information on data that have been determined erroneous or suspect during
quality control procedures. Also, some of the original data source codes and
flags are stored here. This section is variable in length and contains 16
characters for each erroneous or suspect parameter. The section has a minimum
length of 0 characters and a maximum length of 1587 (1584 plus a 3 character
section identifier) characters.

Missing Values - Missing values for any non-signed item are filled (i.e.,
999). Missing values for any signed item are positive filled (i.e., +99999).

Longitude and Latitude Coordinates - Longitudes will be reported with
negative values representing longitudes west of 0 degrees, and latiudes will
be negative south of the equator. Although the data field allows for values
to a thousandth of a degree, the values are often only computed to the
hundredth of a degree with a 0 entered in the thousandth position.



    3

5.   Access Method and Sort for Supplied Data: See #4 above.

6.   Element Names and Definitions: See documentation below.
