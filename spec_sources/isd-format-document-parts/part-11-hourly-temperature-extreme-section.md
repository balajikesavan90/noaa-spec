## Part 11 - Hourly Temperature Extreme Section

Hourly Temperature Extreme Section

FLD LEN: 3
         Hourly Temperature Extreme Section identifier
         The identifier that indicates one of three concurrent air temperature observations made by co-located sensors.
         Three instances of this section (corresponding to the three temperature sensors) appear in the last ISD record
         of the hour.
         DOM: A specific domain comprised of the characters in the ASCII character set.
                CV1, CV2, CV3 Three indicators preceding three copies of the following items:
                                  TEMP_MIN minimum air temperature
                                  TEMP_MIN_QC quality code
                                  TEMP_MIN_FLAG quality code
                                  TEMP_MIN_TIME time of minimum air temperature
                                  TEMP_MIN_TIME_QC quality code
                                  TEMP_MIN_TIME_FLAG quality code
                                  TEMP_MAX maximum air temperature
                                  TEMP_MAX_QC quality code
                                  TEMP_MAX_FLAG quality code
                                  TEMP_MAX_TIME time of maximum air temperature
                                  TEMP_MAX_TIME_QC quality code
                                        TEMP_MAX_TIME_FLAG quality code

FLD LEN: 5
         TEMP_MIN minimum air temperature
         The minimum air temperature for the hour.
         MIN: -9999        MAX: +9998        UNITS: degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
               +9999 = Missing.

FLD LEN: 1
         TEMP_MIN_QC quality code
         The code that indicates ISD’s evaluation of the quality status of the minimum hourly temperature.
         DOM: A specific domain comprised of the numeric characters (0-9).
               1 = Passed all quality control checks
               3 = Failed all quality control checks
               9 = Missing




                                                                 48


---

FLD LEN: 1
         TEMP_MIN_FLAG quality code
         A flag that indicates the network’s internal evaluation of the quality status the minimum hourly. Most users will find the
         preceding quality code TEMP_MIN_QC to be the simplest and most useful quality indicator.
         DOM: A specific domain comprised of the numeric characters (0-9)
                0 = Passed all quality control checks
                1 – 9 = Did not pass all quality checks

FLD LEN: 4
         TEMP_MIN_TIME time of minimum air temperature
         The time at which the minimum temperature occurred, in z-time HHMM format
         MIN: 0000        MAX: 2359
         DOM: A specific domain comprised of the numeric characters (0-9)
               9999 = Missing.

FLD LEN: 1
         TEMP_MIN_TIME_QC quality code
         The code that indicates ISD’s evaluation of the quality status of the time of minimum hourly temperature.
         DOM: A specific domain comprised of the numeric characters (0-9).
               1 = Passed all quality control checks
               3 = Failed all quality control checks
               9 = Missing

FLD LEN: 1
         TEMP_MIN_TIME_FLAG quality code
         A flag that indicates the network’s internal evaluation of the quality status of the time of minimum hourly temperature.
         Most users will find the preceding quality code TEMP_MIN_TIME_QC to be the simplest and most useful quality
         indicator.
         DOM: A specific domain comprised of the numeric characters (0-9)
                0 = Passed all quality control checks
                1 – 9 = Did not pass all quality checks

FLD LEN: 5
         TEMP_MAX maximum air temperature
         The maximum air temperature for an hour.
         MIN: -9999       MAX: +9999       UNITS: degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
               +9999 = Missing.

FLD LEN: 1
         TEMP_MAX_QC quality code
         The code that indicates ISD’s evaluation of the quality status of the maximum hourly.
         DOM: A specific domain comprised of the numeric characters (0-9).
               1 = Passed all quality control checks
               3 = Failed all quality control checks
               9 = Missing

FLD LEN: 1
         TEMP_MAX_FLAG quality code
         A flag that indicates the network’s internal evaluation of the quality status the maximum hourly. Most users will find the
         preceding quality code TEMP_MAX_QC to be the simplest and most useful quality indicator.
         DOM: A specific domain comprised of the numeric characters (0-9)
                0 = Passed all quality control checks
                1 – 9 = Did not pass all quality checks

FLD LEN: 4
         TEMP_MAX_TIME time of maximum air temperature
         The time at which the maximum temperature occurred, in z-time HHMM format
         MIN: 0000        MAX: 2359
         DOM: A specific domain comprised of the numeric characters (0-9)
               9999 = Missing.

FLD LEN: 1
         TEMP_MAX_TIME_QC quality code
         The code that indicates ISD’s evaluation of the quality status of the time of maximum hourly temperature.
         DOM: A specific domain comprised of the numeric characters (0-9).
               1 = Passed all quality control checks
               3 = Failed all quality control checks



                                                                 49


---

     9 = Missing

FLD LEN: 1
         TEMP_MAX_TIME_FLAG quality code
         A flag that indicates the network’s internal evaluation of the quality status of the time of maximum hourly temperature.
         Most users will find the preceding quality code TEMP_MAX_TIME_QC to be the simplest and most useful quality
         indicator.
         DOM: A specific domain comprised of the numeric characters (0-9)
                0 = Passed all quality control checks
                1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
