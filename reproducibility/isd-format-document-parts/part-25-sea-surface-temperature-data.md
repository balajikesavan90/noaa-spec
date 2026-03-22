## Part 25 - Sea Surface Temperature Data

Sea Surface Temperature Data

FLD LEN: 3
         SEA-SURFACE-TEMPERATURE-OBSERVATION identifier
         The identifier that denotes the start of a SEA-SURFACE-TEMPERATURE-OBSERVATION temperature data section.
         DOM: A specific domain comprised of the characters in the ASCII character.
               SA1: An indicator of the occurrence of the following item:
                       SEA-SURFACE-TEMPERATURE-OBSERVATION temperature
                       SEA-SURFACE-TEMPERATURE-OBSERVATION temperature quality code

FLD LEN: 4
         SEA-SURFACE-TEMPERATURE-OBSERVATION temperature
         The temperature of the water at the surface.
         MIN: -050     MAX: +450        UNITS: Degrees Celsius
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters(0-9), a plus sign (+), and a minus sign (-).
               +999 = Missing

FLD LEN: 1
         SEA-SURFACE-TEMPERATURE-OBSERVATION temperature quality code
         The code that denotes a quality status of the reported SEA-SURFACE-TEMPERATURE-OBSERVATION temperature
         DOM: A specific domain comprised of the characters in the ASCII character set.
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
