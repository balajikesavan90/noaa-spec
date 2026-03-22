## Part 21 - Hourly Extraterrestrial Radiation Section

Hourly Extraterrestrial Radiation Section

FLD LEN: 3
          Hourly Extraterrestrial Radiation Section identifier
          The identifier that denotes the start of the Hourly Extraterrestrial radiation data section.
          DOM: A specific domain comprised of the characters in the ASCII character set.
          GR1 An indicator of the occurrence of the following items:
                Hourly extraterrestrial radiation time period
                Hourly extraterrestrial radiation on a horizontal surface
                Hourly extraterrestrial radiation on a horizontal surface quality code
                Hourly extraterrestrial radiation normal to the sun
                Hourly extraterrestrial radiation normal to the sun quality code

FLD LEN: 4
         Time period in minutes, for which the data in this section pertains—eg, 0060 = 60 minutes (1 hour).
         MIN: 0001         MAX: 9998        UNITS: Minutes
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing data

FLD LEN: 4
          Hourly extraterrestrial radiation on a horizontal surface
          The amount of solar radiation received (modeled) on a horizontal surface at the top of the atmosphere. Unit is watts per
          square meter (W/m2) in whole values.
          MIN: 0000     MAX: 9998         UNITS: watts per square meter
          SCALING FACTOR: 1
          DOM: A general domain comprised of the numeric characters (0-9).
9999 = Missing data

FLD LEN: 1


                                                                  74


---

           Hourly extraterrestrial radiation on a horizontal surface quality code
           The code that denotes a quality status of the hourly extraterrestrial radiation on a horizontal surface value .
           DOM: A specific domain comprised of the numeric characters (0-9).
                 0 = Passed gross limits check
                 1 = Passed all quality control checks
                 2 = Suspect
                 3 = Erroneous
                 9 = Missing

FLD LEN: 4
         Hourly extraterrestrial radiation normal to the sun
         The amount of solar radiation received (modeled) on a surface normal to the sun at the top of the atmosphere. Unit is
         watts per square meter (W/m2) in whole values.
         MIN: 0000      MAX: 9998        UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing data

FLD LEN: 1
         Hourly extraterrestrial radiation normal to the sun quality code
         The code that denotes a quality status of the hourly extraterrestrial radiation normal to the sun value.
         DOM: A specific domain comprised of the numeric characters (0-9).
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               9 = Missing

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
