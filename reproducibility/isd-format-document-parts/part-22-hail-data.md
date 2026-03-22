## Part 22 - Hail Data

Hail Data

FLD LEN: 3
          HAIL identifier
          The identifier that denotes the start of a HAIL data section.
          DOM: A specific domain comprised of the characters in the ASCII character set.
                An indicator of the occurrence of the following item:
                  Hail size
                  Hail size quality code

FLD LEN: 3
         HAIL size
         The diameter of the largest hailstone observed.
         MIN: 000      MAX: 200         UNITS: Centimeters
         SCALING FACTOR: 10
         DOM: A general domain comprised of the numeric characters (0-9)
               999 = missing

FLD LEN: 1
         HAIL size quality code
         The code that denotes a quality status of the reported HAIL size.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

