## Part 19 - Modeled Solar Irradiance Section

Modeled Solar Irradiance Section

FLD LEN: 3
         Modeled Solar Irradiance Section identifier
         The identifier that indicates modeled broadband solar irradiance data integrated over the specified time period.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               GP1 An indicator of the following items:
                     Modeled solar irradiance data time period
                     Modeled global horizontal
                     Modeled global horizontal source flag
                     Modeled global horizontal uncertainty
                     Modeled direct normal
                     Modeled direct normal source flag
                     Modeled direct normal uncertainty
                     Modeled diffuse horizontal
                     Modeled diffuse horizontal source flag
                     Modeled diffuse horizontal uncertainty

FLD LEN: 4
         Time period in minutes, for which the data in this section pertains—eg, 0060 = 60 minutes (1 hour).
         MAX: 9998      UNITS: Minutes
         DOM: A general domain comprised of the numeric characters (0-9).
              9999 = Missing.

FLD LEN: 4
         Modeled global horizontal
         Total amount of direct and diffuse solar radiation (modeled) received on a horizontal surface. Unit is watts per
         square meter (W/m2) in whole values.
         MIN: 0000      MAX: 9998         UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
                9999 = Missing.

FLD LEN: 2
         Modeled global horizontal source flag
         The code that provides source information regarding the global horizontal data.
         DOM: A specific domain comprised of the numeric characters (00-99).
               01 = Value modeled from METSTAT model
               02 = Value time-shifted from SUNY satellite model
               03 = Value time-shifted from SUNY satellite model, adjusted to a minimum low-diffuse envelope
               99 = Missing data

FLD LEN: 3
         Modeled global horizontal uncertainty
         The uncertainty values are based on model type and quality of input data.
         MIN: 000        MAX: 100       UNITS: Percent
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
              999 = Missing data

FLD LEN: 4
         Modeled direct normal
         The amount of solar radiation (modeled) on a surface normal to the sun. Unit is watts per square meter (W/m2) in
         whole values.
         MIN: 0000     MAX: 9998         UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.



                                                                72


---

FLD LEN: 2
         Modeled direct normal source flag
         The code that provides source information regarding the direct normal data.
         DOM: A specific domain comprised of the numeric characters (00-99).
               01 = Value modeled from METSTAT model
               02 = Value time-shifted from SUNY satellite model
               03 = Value time-shifted from SUNY satellite model, adjusted to a minimum low-diffuse envelope
               99 = Missing data

FLD LEN: 3
         Modeled direct normal uncertainty
         The uncertainty values are based on model type and quality of input data.
         MIN: 000        MAX: 100       UNITS: Percent
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
              999 = Missing data

FLD LEN: 4
         Modeled diffuse horizontal
         The amount of solar radiation (modeled) received from the sky (excluding the solar disk) on a horizontal surface.
         Unit is watts per square meter (W/m2) in whole values. Waveband ranges from 0.4 - 2.3 micrometers.
         MIN: 0000       MAX: 9998       UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
                9999 = Missing.

FLD LEN: 2
         Modeled diffuse horizontal source flag
         The code that provides source information regarding the diffuse horizontal data.
         DOM: A specific domain comprised of the numeric characters (00-99).
               01 = Value modeled from METSTAT model
               02 = Value time-shifted from SUNY satellite model
               03 = Value time-shifted from SUNY satellite model, adjusted to a minimum low-diffuse envelope
               99 = Missing data

FLD LEN: 3
         Modeled diffuse horizontal uncertainty
         The uncertainty values are based on model type and quality of input data.
         MIN: 000        MAX: 100       UNITS: Percent
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9)
              999 = Missing data

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
