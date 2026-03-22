## Part 24 - Temperature Data

Temperature Data

FLD LEN: 3
         EXTREME-AIR-TEMPERATURE identifier
         The identifier that denotes the start of an EXTREME-AIR-TEMPERATURE data section.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               KA1-KA4 An indicator of up to 4 repeating fields of the following items:
                            EXTREME-AIR-TEMPERATURE period quantity
                            EXTREME-AIR-TEMPERATURE code
                            EXTREME-AIR-TEMPERATURE air temperature
                            EXTREME-AIR-TEMPERATURE temperature quality code

FLD LEN: 3
          EXTREME-AIR-TEMPERATURE period quantity
          The quantity of time over which temperatures were sampled to determine the
          EXTREME-AIR-TEMPERATURE.
          MIN: 001     MAX: 480      UNITS: Hours
          SCALING FACTOR: 10
          DOM: A general domain comprised of the numeric characters (0-9)
                999 = Missing

FLD LEN: 1
         EXTREME-AIR-TEMPERATURE code
         The code that denotes an EXTREME-AIR-TEMPERATURE as a maximum or a minimum.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               N = Minimum temperature
               M = Maximum temperature
               O = Estimated minimum temperature
               P = Estimated maximum temperature
               9 = Missing



                                                              82


---

FLD LEN: 5
         EXTREME-AIR-TEMPERATURE temperature
         The temperature of the high or low air temperature for a given period.
         MIN: -0932      MAX: +0618       UNITS: Degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus
               sign (-).
               +9999 = Missing

FLD LEN: 1
         EXTREME-AIR-TEMPERATURE temperature quality code
         The code that denotes a quality status of the reported EXTREME-AIR-TEMPERATURE temperature.
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
         AVERAGE-AIR-TEMPERATURE identifier
         The identifier that denotes the start of an AVERAGE-AIR-TEMPERATURE data section.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               KB1-KB3 An indicator of up to 3 repeating fields for the following items:
                            AVERAGE-AIR-TEMPERATURE period quantity
                            AVERAGE-AIR-TEMPERATURE type code
                            AVERAGE-AIR-TEMPERATURE air temperature
                            AVERAGE-AIR-TEMPERATURE temperature quality code

FLD LEN: 3
          AVERAGE-AIR-TEMPERATURE period quantity
          The quantity of time over which temperatures were sampled to determine the
          AVERAGE-AIR-TEMPERATURE.
          MIN: 001     MAX: 744      UNITS: Hours
          SCALING FACTOR: 1
          DOM: A general domain comprised of the numeric characters (0-9)
                999 = Missing

FLD LEN: 1
         AVERAGE-AIR-TEMPERATURE code
         The code that denotes an AVERAGE-AIR-TEMPERATURE as a mean, an average maximum, or an average minimum.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               N = Minimum temperature average
               M = Maximum temperature average
               A = Mean temperature
               9 = Missing

FLD LEN: 5
         AVERAGE-AIR-TEMPERATURE temperature
         The mean air temperature for a given period, typically for the day or month, as reported by the station (ie, not derived
         from other data fields).
         MIN: -9900     MAX: +6300       UNITS: Degrees Celsius
         SCALING FACTOR: 100
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
               +9999 = Missing




                                                                83


---

FLD LEN: 1
         AVERAGE-AIR-TEMPERATURE temperature quality code
         The code that denotes a quality status of the reported AVERAGE-AIR-TEMPERATURE temperature.
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
         EXTREME AIR-TEMPERATURE FOR THE MONTH identifier
         The identifier that denotes the start of an EXTREME AIR-TEMPERATURE data section.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               KC1-KC2 An indicator of up to 2 repeating fields for the following items:
                            EXTREME AIR-TEMPERATURE code
                            EXTREME AIR-TEMPERATURE condition code
                            EXTREME AIR-TEMPERATURE temperature
                            EXTREME AIR-TEMPERATURE date of occurrence
                            EXTREME AIR-TEMPERATURE temperature quality code

FLD LEN: 1
         EXTREME AIR-TEMPERATURE FOR THE MONTH code
         The code that denotes an EXTREME AIR-TEMPERATURE FOR THE MONTH as a maximum or a minimum.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               N = Minimum temperature
               M = Maximum temperature
               9 = Missing

FLD LEN: 1
         EXTREME AIR-TEMPERATURE FOR THE MONTH condition code
         The code for EXTREME AIR-TEMPERATURE FOR THE MONTH
         DOM: A specific domain comprised of the characters in the ASCII character set.
               1 = The value occurred on other dates in addition to those listed
               9 = Missing or not applicable

FLD LEN: 5
         EXTREME AIR-TEMPERATURE FOR THE MONTH temperature
         The extremes air temperature for the month, as reported by the station (ie, not derived from other data fields).
         MIN: -1100    MAX: +0630        UNITS: Degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
               +9999 = Missing

FLD LEN: 6
         EXTREME AIR-TEMPERATURE FOR THE MONTH dates of occurrence
         The dates of occurrence of EXTREME AIR-TEMPERATURE, given as the date for each occurrence, for up to 3
         occurrences; e.g., 041016 indicates days 04, 10, and 16.
         MIN: 01      MAX: 31
         DOM: A general domain comprised of the numeric characters (0-9).
               99 = missing for each of the 3 sub-fields.

FLD LEN: 1
         EXTREME AIR-TEMPERATURE FOR THE MONTH temperature quality code
         The code that denotes a quality status of the reported EXTREME AIR-TEMPERATURE FOR THE MONTH.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               4 = Passed gross limits check, data originate from an NCEI data source
               5 = Passed all quality control checks, data originate from an NCEI data source
               6 = Suspect, data originate from an NCEI data source



                                                                84


---

                  7 = Erroneous, data originate from an NCEI data source
                  M = Manual change made to value based on information provided by NWS or FAA
                  9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
         HEATING-COOLING-DEGREE-DAYS identifier
         The identifier that denotes the start of an HEATING-COOLING-DEGREE-DAYS data section.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               KD1-KD2 An indicator of up to 2 repeating fields of the following items:
                            HEATING-COOLING-DEGREE-DAYS period quantity
                            HEATING-COOLING-DEGREE-DAYS code
                            HEATING-COOLING-DEGREE-DAYS value
                            HEATING-COOLING-DEGREE-DAYS quality code

FLD LEN: 3
          HEATING-COOLING-DEGREE-DAYS period quantity
          The quantity of time over which temperatures were sampled to determine the HEATING-COOLING-DEGREE-DAYS.
          MIN: 001     MAX: 744      UNITS: Hours
          SCALING FACTOR: 1
          DOM: A general domain comprised of the numeric characters (0-9).
                999 = Missing

FLD LEN: 1
         HEATING-COOLING-DEGREE-DAYS code
         The code that denotes the value as being heating degree days or cooling degree days.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               H = Heating Degree Days
               C = Cooling Degree Days

FLD LEN: 4
         HEATING-COOLING-DEGREE-DAYS value
         The total heating or cooling degree days for a given period, typically for the day or month, as reported by the station (ie,
         not derived from other data fields). These data use the 65-degree Fahrenheit base as raditionally used for degree days.
         MIN: 0000      MAX: 5000        UNITS: Heating or Cooling Degree Days
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing

FLD LEN: 1
         HEATING-COOLING-DEGREE-DAYS quality code
         The code that denotes a quality status of the reported HEATING-COOLING-DEGREE-DAYS data.
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
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH identifier
         The identifier that represents NUMBER OF DAYS EXCEEDING CRITERIA data.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               KE1 An indicator of the following items:
                     EXTREME TEMPERATURE, NUMBER OF DAYS with maximum temperature 32 F or lower
                     EXTREME TEMPERATURE, NUMBER OF DAYS quality code
                     EXTREME TEMPERATURE, NUMBER OF DAYS with maximum temperature 90 F or higher
                     EXTREME TEMPERATURE, NUMBER OF DAYS quality code
                     EXTREME TEMPERATURE, NUMBER OF DAYS with minimum temperature 32 F or lower
                     EXTREME TEMPERATURE, NUMBER OF DAYS quality code
                     EXTREME TEMPERATURE, NUMBER OF DAYS with minimum temperature 0 F or lower
                     EXTREME TEMPERATURE, NUMBER OF DAYS quality code



                                                                 85


---

FLD LEN: 2
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH
         The number of days with maximum temperature 32 F (0.0 C) or lower.
         MIN: 00     MAX: 31
         DOM: A general domain comprised of the numeric characters (0-9).
               99 = Missing.

FLD LEN: 1
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH quality code
         The code that denotes a quality status of the reported days with max temperature 32 F (0.0 C) or lower.
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

FLD LEN: 2
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH
         The number of days with maximum temperature 90 F (32.2 C) or higher, except for Alaska—70 F (21.1 C) or higher.
         MIN: 00     MAX: 31
         DOM: A general domain comprised of the numeric characters (0-9).
               99 = Missing.

FLD LEN: 1
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH quality code
         The code that denotes a quality status of the reported days with max temperature 90 F (32.2 C) or higher (70 F for
         Alaska).
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

FLD LEN: 2
         TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH
         The number of days with minimum temperature 32 F (0.0 C) or lower.
         MIN: 00     MAX: 31
         DOM: A general domain comprised of the numeric characters (0-9).
               99 = Missing.

FLD LEN: 1
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH quality code
         The code that denotes a quality status of the reported days with min temperature 32 F (0.0 C) or lower.
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

FLD LEN: 2
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH
         The number of days with minimum temperature 0 F (-17.8 C) or lower.
         MIN: 00     MAX: 31
         DOM: A general domain comprised of the numeric characters (0-9).
               99 = Missing.



                                                               86


---

FLD LEN: 1
         EXTREME TEMPERATURES, NUMBER OF DAYS EXCEEDING CRITERIA, FOR THE MONTH quality code
         The code that denotes a quality status of the reported days with min temperature 0 F (-17.8 C) or lower.
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
         Hourly Calculated Temperature Section identifier
         The identifier that indicates a calculated hourly average air temperature derived by an algorithm whose inputs
         are hourly temperature averages from each of the 3 co-located temperature sensors. This section appears in the
         last ISD record of the hour for the 15-minute data stream only. Unlike the temperature value found in the
         mandatory data section which is produced using 5-minute values, this value is calculated using an hourly average.
         DOM: A specific domain comprised of the characters in the ASCII character set.
                KF1 An indicator of the following items:
                    TEMP derived air temperature
                    TEMP_QC quality code

FLD LEN: 5
         TEMP derived air temperature
         The calculated hourly average air temperature.
         MIN: -9999        MAX: +9998        UNITS: degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
               +9999 = Missing.

FLD LEN: 1
         TEMP_QC quality code
         The code that indicates ISD’s evaluation of the quality status of the calculated hourly average air temperature.
         DOM: A specific domain comprised of the numeric characters (0-9).
               1 = Passed all quality control checks
               3 = Failed all quality control checks
               9 = missing

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
         AVERAGE DEW POINT AND WET BULB TEMPERATURE occurrence identifier
         The identifier that denotes the start of an AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               KG1-KG2 An indicator of up to two repeating fields of the following items:
                            AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE period quantity
                            AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE code
                            AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE temperature
                            AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE derived code
                            AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE quality code


FLD LEN: 3
         AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE period quantity
         The quantity of time over which temperature were averaged to determine the AVERAGE-DEW-POINT-AND-WET-BULB-
         TEMPERATURE
          MIN: 001         MAX: 744       UNITS: hours
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               999 = Missing.




                                                                87


---

FLD LEN: 1
         AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE code
         The code that denotes an AVERAGE-DEW-POINT-AND-AVERAGE-WET-BULB-TEMPERATURE as an average
         DOM: A specific domain comprised of the characters in the ASCII character set.
               D = Average dew point temperature
               W = Average wet bulb temperature
               9 = missing

FLD LEN: 5
         AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE temperature
         The average dew point or average wet bulb temperature for a given period, typically for the day or month, derived from
         other data fields
         MIN: -9900        MAX: +6300      UNITS: degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign ( - ).
               +9999 = missing

FLD LEN: 1
         AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE derived code
         The code that denotes a quality status of the reported AVERAGE-DEW-POINT-AND-AVERAGE-WET-BULB-
         TEMPERATURE
         DOM: A specific domain comprised of the characters in the ASCII character set.
               D = Derived from hourly values
               9 = missing


FLD LEN: 1
         AVERAGE-DEW-POINT-AND-WET-BULB-TEMPERATURE quality code
         The code that denotes a quality status of the reported AVERAGE-DEW-POINT-AND-AVERAGE-WET-BULB-
         TEMPERATURE
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


---

> **Note:** In the source ISD format document, the following sections appear after Part 24 content but have been extracted into their own part files to avoid duplication:
> - **Part 27** — [Pressure Data](part-27-pressure-data.md) (MA1, ME1, MF1, MG1, MH1, MK1)
> - **Part 28** — [Weather Occurrence Data (Extended)](part-28-weather-occurrence-data-extended.md) (MV1–MV7, MW1–MW7)
> - **Part 29** — [Wind Data](part-29-wind-data.md) (OA1–OA3, OB1–OB2, OC1, OD1–OD3, OE1–OE3, RH1–RH3)
