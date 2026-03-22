## Part 20 - Hourly Solar Angle Section


FLD LEN: 3
    Hourly Solar Angle Section identifier
    The identifier that denotes the start of the Hourly Solar angle data section.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    GQ1 An indicator of the occurrence of the following items:
    Hourly solar angle time period
    Hourly mean zenith angle
    Hourly mean zenith angle quality code
    Hourly mean azimuth angle
    Hourly mean azimuth angle quality code




    73


---

FLD LEN: 4
    Time period in minutes, for which the data in this section pertains—eg, 0060 = 60 minutes (1 hour).
    MIN: 0001         MAX: 9998        UNITS: Minutes
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing data

FLD LEN: 4
    Hourly mean zenith angle (for sunup periods)
    The angle between sun and the zenith as the mean of all 1-minute sunup zenith angle values.
    MIN: 0000      MAX: 3600       UNITS: Angular Degrees
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing data

FLD LEN: 1
    Hourly mean zenith angle quality code
    The code that denotes a quality status of the hourly mean zenith angle.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Missing

FLD LEN: 4
    Hourly mean azimuth angle (for sunup periods)
    The angle between sun and north as the mean of all 1-minute sunup azimuth angle values.
    MIN: 0000      MAX: 3600      UNITS: Angular Degrees
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing data

FLD LEN: 1
    Hourly mean azimuth angle quality code
    The code that denotes a quality status of the hourly mean azimuth angle.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Missing

---

> **Note:** In the source ISD format document, the following subsections appear within Part 20 but have been extracted into their own part files to avoid duplication:
> - **Part 21** — [Hourly Extraterrestrial Radiation Section](part-21-hourly-extraterrestrial-radiation-section.md) (GR1)
> - **Part 22** — [Hail Data](part-22-hail-data.md)
