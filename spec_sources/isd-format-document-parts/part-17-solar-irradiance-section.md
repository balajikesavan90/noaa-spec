## Part 17 - Solar Irradiance Section

Solar Irradiance Section

FLD LEN: 3
         Solar Irradiance Section identifier
         The identifier that indicates an observation of solar irradiance data integrated over the specified time period.
         DOM: A specific domain comprised of the characters in the ASCII character set.
               GM1 An indicator of the following items:
                      Solar irradiance data time period
                      Global irradiance
                      Global irradiance data flag
                      Global irradiance quality code
                      Direct beam irradiance
                      Direct beam irradiance data flag
                      Direct beam irradiance quality code


                                                            66


---

                       Diffuse irradiance
                       Diffuse irradiance data flag
                       Diffuse irradiance quality code
                       UVB global irradiance
                       UVB global irradiance data flag
                       UVB global irradiance quality code

FLD LEN: 4
         Time period in minutes, for which the data in this section (GM1) pertains—eg, 0060 = 60 minutes (1 hour).
         MIN: 0001         MAX: 9998        UNITS: Minutes
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.

FLD LEN: 4
         Global irradiance
         Global horizontal irradiance measured using a pyranometer. Unit is watts per square meter
         (W/m2) in whole values. Waveband ranges from 0.4 - 2.3 micrometers.
         MIN: 0000      MAX: 9998        UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.

FLD LEN: 2
         Global irradiance data flag
         The code that provides additional information regarding the global irradiance data.
         DOM: A specific domain comprised of the numeric characters (00-99).
               00 = Untested (raw data)
               01 = Passed one-component test; data fall within max-min limits of Kt, Kn, or Kd
               02 = Passed two-component test; data fall within 0.03 of the Gompertz boundaries
               03 = Passed three-component test; data come within + 0.03 of satisfying Kt = Kn + Kd
               04 = Passed visual inspection: not used by SERI_QC1
               05 = Failed visual inspection: not used by SERI_QC1
               06 = Value estimated; passes all pertinent SERI_QC tests
               07 = Failed one-component test; lower than allowed minimum
               08 = Failed one-component test; higher than allowed maximum
               09 = Passed three-component test but failed two-component test by 0.05
               10-93 = Failed two- or three- component tests in one of four ways.
               94-97 = Data fails into physically impossible region where Kn > Kt by K-space distances of 0.05 to 0.10 (94), 0.10
                       to 0.15 (95), 0.15 to 0.20 (96), and > 0.20 (97).
               98 = Not used
               99 = Missing data

FLD LEN: 1
         Global irradiance quality code
         The code that denotes a quality status of the reported global irradiance value.
         DOM: A specific domain comprised of the numeric characters (0-9).
               0 = Passed gross limits check
               1 = Passed all quality control checks
               2 = Suspect
               3 = Erroneous
               9 = Missing

FLD LEN: 4
         Direct beam irradiance
         Direct beam irradiance measured using a pyrheliometer or other instrument. Unit is watts per square meter (W/m2) in
         whole values. Waveband ranges from 0.4 - 2.3 micrometers.
         MIN: 0000       MAX: 9998     UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
                9999 = Missing.




                                                            67


---

FLD LEN: 2
         Direct beam irradiance data flag
         The code that provides additional information regarding the direct beam irradiance data.
         DOM: A specific domain comprised of the numeric characters (00-99).
               00 = Untested (raw data)
               01 = Passed one-component test; data fall within max-min limits of Kt, Kn, or Kd
               02 = Passed two-component test; data fall within 0.03 of the Gompertz boundaries
               03 = Passed three-component test; data come within + 0.03 of satisfying Kt = Kn + Kd
               04 = Passed visual inspection: not used by SERI_QC1
               05 = Failed visual inspection: not used by SERI_QC1
               06 = Value estimated; passes all pertinent SERI_QC tests
               07 = Failed one-component test; lower than allowed minimum
               08 = Failed one-component test; higher than allowed maximum
               09 = Passed three-component test but failed two-component test by 0.05
               10-93 = Failed two- or three- component tests in one of four ways.
               94-97 = Data fails into physically impossible region where Kn > Kt by K-space distances of 0.05 to 0.10 (94),
                       0.10 to 0.15 (95), 0.15 to 0.20 (96), and > 0.20 (97).
               98 = Not used
               99 = Missing data

FLD LEN: 1
         Direct beam irradiance quality code
         The code that denotes a quality status of the reported direct beam irradiance value.
         DOM: A specific domain comprised of the numeric characters (0-9).
         0 = Passed gross limits check
         1 = Passed all quality control checks
         2 = Suspect
         3 = Erroneous
         9 = Missing

FLD LEN: 4
         Diffuse irradiance
         Diffuse irradiance measured using a pyranometer under a shading device. Unit is watts per square meter (W/m2) in
         whole values. Waveband ranges from 0.4 - 2.3 micrometers. Instrument is mounted under a shadowband.
         MIN: 0000       MAX: 9998      UNITS: watts per square meter
         SCALING FACTOR: 1
         DOM: A general domain comprised of the numeric characters (0-9).
               9999 = Missing.

FLD LEN: 2
         Diffuse irradiance data flag
         The code that provides additional information regarding the diffuse irradiance data.
         DOM: A specific domain comprised of the numeric characters (00-99).
               00 = Untested (raw data)
               01 = Passed one-component test; data fall within max-min limits of Kt, Kn, or Kd
               02 = Passed two-component test; data fall within 0.03 of the Gompertz boundaries
               03 = Passed three-component test; data come within + 0.03 of satisfying Kt = Kn + Kd
               04 = Passed visual inspection: not used by SERI_QC1
               05 = Failed visual inspection: not used by SERI_QC1
               06 = Value estimated; passes all pertinent SERI_QC tests
               07 = Failed one-component test; lower than allowed minimum
               08 = Failed one-component test; higher than allowed maximum
               09 = Passed three-component test but failed two-component test by 0.05
               10-93 = Failed two- or three- component tests in one of four ways.
               94-97 = Data fails into physically impossible region where Kn > Kt by K-space distances of 0.05 to 0.10 (94), 0.10 to
                       0.15 (95), 0.15 to 0.20 (96), and > 0.20 (97).
               98 = Not used
               99 = Missing data

FLD LEN: 1
         Diffuse irradiance quality code
         The code that denotes a quality status of the reported diffuse irradiance value.
         DOM: A specific domain comprised of the numeric characters (0-9).
         0 = Passed gross limits check
         1 = Passed all quality control checks
         2 = Suspect
         3 = Erroneous
         9 = Missing

FLD LEN: 4
         UVB global irradiance
         Ultra-violet global irradiance measured using a Ultra-violet Biometer (Solar Light). Unit is milli-watts per square


                                                            68


---

              meter (mW/m2) of erythema effective irradiance in whole values. Waveband ranges from 290-320 nanometers.
              MIN: 0000     MAX: 9998      UNITS: milli-watts per square meter
              SCALING FACTOR: 1
              DOM: A general domain comprised of the numeric characters (0-9).
                    9999 = Missing.

   FLD LEN: 1
            UVB global irradiance quality code
            The code that denotes a quality status of the reported UVB global irradiance value.
            DOM: A specific domain comprised of the numeric characters (0-9).
                  0 = Passed gross limits check
                  1 = Passed all quality control checks
                  2 = Suspect
                  3 = Erroneous
                  9 = Missing


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

   FLD LEN: 3
            Solar Radiation Section identifier
            The identifier that indicates an observation of solar radiation data.
            DOM: A specific domain comprised of the characters in the ASCII character set.
                  GN1 An indicator of the following items:
                         Solar radiation data time period
                         Upwelling global solar radiation
                         Upwelling global solar radiation quality code
                         Downwelling thermal infrared radiation
                         Downwelling thermal infrared radiation quality code
                         Upwelling thermal infrared radiation
                         Upwelling thermal infrared radiation quality code
                         Photosynthetically active radiation
                         Photosynthetically active radiation quality code
                         Solar zenith angle
                         Solar zenith angle quality code

   FLD LEN: 4
            Time period in minutes, for which the data in this section (GN1) pertains—eg, 0060 = 60 minutes (1 hour).
            MIN: 0001         MAX: 9998        UNITS: Minutes
            DOM: A general domain comprised of the numeric characters (0-9).
                  9999 = Missing.

   FLD LEN: 4
            Upwelling global solar radiation
            Global radiation measured using an Epply Precision Spectral Pyranometer mounted upside down ten meters above the
            surface on a meteorological tower. Unit is milli-watts per square meter (mW/m2). Waveband ranges from 270 to 3000
            nanometers.
            MIN: 0000       MAX: 9998      UNITS: milli-watts per square meter
            SCALING FACTOR: 1
            DOM: A general domain comprised of the numeric characters (0-9).
                  9999 = Missing.

   FLD LEN: 1
            Upwelling global solar radiation quality code
            The code that denotes a quality status of the reported upwelling global solar radiation value.
            DOM: A specific domain comprised of the numeric characters (0-9).
                  0 = Passed gross limits check
                  1 = Passed all quality control checks
                  2 = Suspect
                  3 = Erroneous
                  9 = Missing




                                                              69


---

     FLD LEN: 4
              Downwelling thermal infrared radiation
              Infrared radiation measured using an Epply Precision Infrared Radiometer mounted upright ten meters above the surface
              on a meteorological tower. Unit is milli-watts per square meter (mW/m2). Waveband ranges from 3000 to 50,000
              nanometers.
              MIN: 0000        MAX: 9998       UNITS: milli-watts per square meter
              SCALING FACTOR: 1
              DOM: A general domain comprised of the numeric characters (0-9).
                     9999 = Missing.

     FLD LEN: 1
              Downwelling thermal infrared radiation quality code
              The code that denotes a quality status of the reported downwelling thermal infrared radiation value.
              DOM: A specific domain comprised of the numeric characters (0-9).
                    0 = Passed gross limits check
                    1 = Passed all quality control checks
                    2 = Suspect
                    3 = Erroneous
                    9 = Missing

     FLD LEN: 4
              Upwelling thermal infrared radiation
              Infrared radiation measured using an Epply Precision Infrared Radiometer mounted upside-down ten meters above the
              surface on a meteorological tower. Unit is Watts per meter per meter (mW/m2). Waveband ranges from 3000 to 50,000
              nanometers.
              MIN: 0000        MAX: 9998      UNITS: watts per square meter
              SCALING FACTOR: 1
              DOM: A general domain comprised of the numeric characters (0-9).
                     9999 = Missing.

     FLD LEN: 1
              Upwelling thermal infrared radiation quality code
              The code that denotes a quality status of the reported upwelling thermal infrared radiation value.
              DOM: A specific domain comprised of the numeric characters (0-9).
                    0 = Passed gross limits check
                    1 = Passed all quality control checks
                    2 = Suspect
                    3 = Erroneous
                    9 = Missing

     FLD LEN: 4
              Photosynthetically active radiation
              The PAR sensor measures global solar radiation from 400 to 700 nm in Watts per square meter (mW/m2), which
              approximates the spectral band active in photosynthesis.
              MIN: 0000      MAX: 9998       UNITS: watts per square meter
              SCALING FACTOR: 1
              DOM: A general domain comprised of the numeric characters (0-9).
                    9999 = Missing.

     FLD LEN: 1
              Photosynthetically active radiation quality code
              The code that denotes a quality status of the reported photosynthetically active radiation value.
              DOM: A specific domain comprised of the numeric characters (0-9).
                    0 = Passed gross limits check
                    1 = Passed all quality control checks
                    2 = Suspect
                    3 = Erroneous
                    9 = Missing

     FLD LEN: 3
              Solar zenith angle
              The Solar Zenith Angle is the angle in degrees between the sun and the perpendicular to the earth’s surface. At sunrise it is
              90 degrees, at noon it is a function of latitude, and at sunset it is again 90 degrees. Below the horizon value is 100. Values
              are reported to the nearest tens of degrees (eg, 090).
              MIN: 000       MAX: 998        UNITS: angular degrees
              SCALING FACTOR: 1
              DOM: A general domain comprised of the numeric characters (0-9).
                    999 = Missing.

FLD LEN: 1
         Solar zenith angle quality code
         The code that denotes a quality status of the reported solar zenith angle value.


                                                                70


---

           DOM: A specific domain comprised of the numeric characters (0-9).
                0 = Passed gross limits check
                1 = Passed all quality control checks
                2 = Suspect
                3 = Erroneous
                9 = Missing


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
