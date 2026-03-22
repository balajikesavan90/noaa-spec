## Part 18 - Net Solar Radiation Section

Net Solar Radiation Section

FLD LEN: 3
         Net Solar Radiation Section identifier
         The identifier that indicates an observation of net solar radiation data.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               GO1 An indicator of the following items:
                     Net solar radiation data time period
                     Net solar radiation
                     Net solar radiation quality code
                     Net infrared radiation
                     Net infrared radiation quality code
                     Net radiation
                     Net radiation quality code

FLD LEN: 4
         Time period in minutes, for which the data in this section (GO1) pertains—eg, 0060 = 60 minutes (1 hour).
         MIN: 0001         MAX: 9998        UNITS: Minutes
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.

FLD LEN: 4
         Net solar radiation
         The difference between global radiation and upwelling global radiation measured in Watts per square meter (W/m2). If
         negative, left most position contains a "-" sign.
         MIN: -999       MAX: 9998        UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.

FLD LEN: 1
         Net solar radiation quality code
         The code that denotes a quality status of the reported net solar radiation value.
         DOM: A specific domain comprised of the numeric characters (0-9).
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               9 = Missing

FLD LEN: 4
         Net infrared radiation
         The difference between downwelling infrared and upwelling infrared measured in Watts per square meter (W/m2). If
         negative, left most position contains a "-" sign.
         MIN: -999       MAX: 9998        UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.

FLD LEN: 1
         Net infrared radiation quality code
         The code that denotes a quality status of the reported net infrared radiation value.
         DOM: A specific domain comprised of the numeric characters (0-9).
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               9 = Missing

FLD LEN: 4
         Net radiation
         The total of Net Solar and Net Infrared radiation measured in Watts per square meter (W/m2).
         MIN: -999      MAX: 9998        UNITS: watts per square meter
         SCALING FACTOR: 1


                                                                71


---

           DOM: A general domain comprised of the numeric characters (0-9).
                9999 = Missing.

FLD LEN: 1
         Net radiation quality code
         The code that denotes a quality status of the reported net radiation value.
         DOM: A specific domain comprised of the numeric characters (0-9).
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               9 = Missing

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
