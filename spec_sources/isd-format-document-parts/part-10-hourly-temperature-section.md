## Part 10 - Hourly Temperature Section

Hourly Temperature Section

FLD LEN: 3
         Hourly Temperature Section identifier
         The identifier that indicates one of three concurrent air temperature observations made by co-located sensors.
         Three instances of this section (corresponding to the three temperature sensors) appear in the last ISD record
         of the hour.
         DOM: A specific domain comprised of the characters in the ASCII character set.
                CU1, CU2, CU3 Three indicators preceding three copies of the following items:
                                  TEMP_AVG air temperature
                                  TEMP_AVG_QC quality code
                                  TEMP_AVG_FLAG quality code
                                  TEMP_STD air temperature standard deviation
                                  TEMP_STD_QC quality code
                                  TEMP_STD_FLAG quality code

FLD LEN: 5
         TEMP_AVG air temperature
         The average air temperature for an hour.
         MIN: -9999        MAX: +9998        UNITS: degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
               +9999 = Missing.

FLD LEN: 1
         TEMP_AVG_QC quality code
         The code that indicates ISD’s evaluation of the quality status of the hourly temperature average.
         DOM: A specific domain comprised of the numeric characters (0-9).
               1 = Passed all quality control checks
               3 = Failed all quality control checks
               9 = Missing

FLD LEN: 1
         TEMP_AVG_FLAG quality code
         A flag that indicates the network’s internal evaluation of the quality status the hourly temperature average. Most users
         will find the preceding quality code TEMP_AVG_QC to be the simplest and most useful quality indicator.



                                                                47


---

           DOM: A specific domain comprised of the numeric characters (0-9)
                0 = Passed all quality control checks
                1 – 9 = Did not pass all quality checks

FLD LEN: 4
         TEMP_STD air temperature standard deviation
         The temperature standard deviation.
         MIN: 0000        MAX: 9998
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.

FLD LEN: 1
         TEMP_STD_QC quality code
         The code that indicates ISD’s evaluation of the quality status of the hourly temperature standard deviation.
         DOM: A specific domain comprised of the numeric characters (0-9).
               1 = Passed all quality control checks
               3 = Failed all quality control checks
               9 = Missing

FLD LEN: 1
         TEMP_STD_FLAG quality code
         A flag that indicates the network’s internal evaluation of the quality status the hourly temperature standard deviation.
         Most users will find the preceding quality code TEMP_STD_QC to be the simplest and most useful quality
         indicator.
         DOM: A specific domain comprised of the numeric characters (0-9)
                0 = Passed all quality control checks
                1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
