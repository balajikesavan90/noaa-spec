## Part 6 - Climate Reference Network Unique Data

Climate Reference Network Unique Data

FLD LEN: 3
    Subhourly Observed Liquid Precipitation Section: Secondary Sensor identifier
    The identifier that indicates the presence of a liquid precipitation measurement made by a secondary precipitation
    sensor.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CB1, CB2 An indicator of the following items:
    PERIOD period quantity
    PRECIPITATION liquid depth
    PRECIP_QC quality code
    PRECIP_FLAG quality code

FLD LEN: 2
    PRECIPITATION period quantity
    The quantity of time for which the gauge depth was measured.
    MIN: 05      MAX: 60        UNITS: Minutes
    DOM: A specific domain comprised of the characters in the ASCII character set
    99 = Missing

FLD LEN: 6
    PRECIPITATION liquid depth
    The observed liquid precipitation measurement from the secondary precipitation sensor.
    MIN: -99999      MAX: +99998        UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +99999 = Missing.

FLD LEN: 1
    QC quality code
    The code that indicates ISD’s evaluation of the quality status of the liquid precipitation measurement from the
    secondary precipitation sensor.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    PRECIP_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the reported LIQUID-PRECIPITATION
    data. Most users will find the preceding quality code DEPTH_QC to be the simplest and most useful quality
    indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    Hourly Fan Speed Section identifier
    The identifier that indicates an hourly observation of the fan speed from an aspirated shield housing the
    temperature sensor. Three instances of this section appear in the last ISD record of the hour.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CF1,CF2,CF3 An indicator of the following items:
    FAN speed rate
    FAN _QC quality code
    FAN _FLAG quality code




    35


---

    FLD LEN: 4
    FAN The average fan speed for the hour.
    MIN: - 0000      MAX: 9998        UNITS: rotations per second
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

    FLD LEN: 1
    FAN_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the average fan speed for the hour.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

    FLD LEN: 1
    FAN_QC_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the average fan speed for the hour. Most
    users will find the preceding quality code FAN_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

    ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

    FLD LEN: 3
    Subhourly Observed Liquid Precipitation Section: Primary Sensor identifier
    The identifier that indicates the presence of three concurrent precipitation depth observations made by co-
    located sensors on the primary precipitation gauge. Three instances of this section (corresponding to the three
    precipitation sensors) appear in each of the twelve 5-minute data stream records.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CG1, CG2, CG3 Three indicators preceding three copies of the following items:
    DEPTH liquid depth
    DEPTH_QC quality code
    DEPTH_FLAG quality code

    FLD LEN: 6
    DEPTH liquid depth
    The observed gauge depth.
    MIN: -99999        MAX: +99998      UNITS: millimeters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +99999 = Missing.

    FLD LEN: 1
    DEPTH_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the observed depth.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

    FLD LEN: 1
    DEPTH_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the observed depth. Most users will find
    the preceding quality code DEPTH_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

    FLD LEN: 3
    Hourly/Sub-Hourly Relative Humidity/Temperature Section identifier
    The identifier that indicates an observation of relative humidity and temperature measured at the relative humidity
    instrutrument. This section appears one or more times per hour.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CH1, CH2 An indicator of the following items:
    RELATIVE HUMIDITY/TEMPERATURE period quantity



    36


---

    AVG_RH_TEMP average air temperature
    AVG_ RH_TEMP_QC quality code
    AVG_ RH_TEMP_FLAG quality code
    AVG_RH average relative humidity
    AVG_RH_QC quality code
    AVG_RH_FLAG quality code

FLD LEN: 2
    RELATIVE HUMIDITY/TEMPERATURE period quantity in minutes
    The quantity of time over which the RELATIVE HUMIDITY/TEMPERATURE was measured.
    MIN: 00      MAX: 60       UNITS: Minutes
    SCALING FACTOR: 1
    DOM: A specific domain comprised of the characters in the ASCII character set
    99 = Missing.

FLD LEN: 5
    AVG_ RH_TEMP average air temperature
    The average air temperature measured at the relative humidity instrument.
    MIN: -9999      MAX: +9998      UNITS: degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-)
    +9999 = Missing.

FLD LEN: 1
    AVG_ RH_TEMP_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the average air temperature measured at
    the relative humidity instrument.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    AVG_ RH_TEMP_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the average air temperature
    measured at the relative humidity instrument. Most users will find the preceding quality code
    AVG_RH_TEMP_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 4
    AVG_RH average relative humidity
    The average relative humidity measured at the relative humidity instrument.
    MIN: 0000     MAX: 1000        UNITS: percent
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    AVG_RH_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the average relative humidity.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    AVG_RH_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the average relative humidity.
    Most users will find the preceding quality code AVG_RH_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀




    37


---

FLD LEN: 3
    Hourly Relative Humidity/Temperature Section identifier
    The identifier that indicates an hourly observation of relative humidity and temperature measured at the relative
    humidity instrument. This section appears in the last ISD record of the hour.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CI1 An indicator of the following items:
    MIN_RH_TEMP hourly air temperature
    MIN_ RH_TEMP_QC quality code
    MIN_ RH_TEMP_FLAG quality code
    MAX_ RH_TEMP hourly air temperature
    MAX_ RH_TEMP_QC quality code
    MAX_ RH_TEMP_FLAG quality code
    STD_RH_TEMP hourly air temperature standard deviation
    STD_RH_TEMP_QC quality code
    STD_RH_TEMP_FLAG quality code
    STD_RH hourly relative humidity standard deviation
    STD_RH_QC quality code
    STD_RH_FLAG quality code

FLD LEN: 5
    MIN_ RH_TEMP hourly air temperature
    The minimum air temperature measured at the relative humidity instrument.
    MIN: -9999     MAX: +9999      UNITS: degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-)
    +9999 = Missing.

FLD LEN: 1
    MIN_ RH_TEMP_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the minimum hourly air temperature measured at
    the relative humidity instrument.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    MIN_ RH_TEMP_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the minimum hourly air temperature
    measured at the relative humidity instrument. Most users will find the preceding quality code
    AVG_RH_TEMP_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 5
    MAX_ RH_TEMP hourly air temperature
    The maximum air temperature measured at the relative humidity instrument.
    MIN: -9999     MAX: +9998     UNITS: degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-)
    +9999 = Missing.

FLD LEN: 1
    MAX_ RH_TEMP_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the maximum hourly air temperature measured at
    the relative humidity instrument.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing




    38


---

FLD LEN: 1
    MAX_ RH_TEMP_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the maximum hourly air temperature
    measured at the relative humidity instrument. Most users will find the preceding quality code
    AVG_RH_TEMP_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 5
    STD_ RH_TEMP hourly air temperature standard deviation
    The standard deviation for the hourly air temperature measured at the relative humidity instrument.
    MIN: 00000     MAX: 99998
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    STD_ RH_TEMP_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the standard deviation for the air temperature
    measured at the relative humidity instrument.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    STD_ RH_TEMP_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the standard deviation for the air
    temperature measured at the relative humidity instrument. Most users will find the preceding quality code
    STD_ RH_TEMP_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 5
    STD_RH hourly relative humidity standard deviation
    The hourly relative humidity standard deviation.
    MIN: 00000       MAX: 99998
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    99999 = Missing.

FLD LEN: 1
    STD_RH_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the hourly relative humidity standard deviation.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    STD_RH_FLAG quality code
    The code that indicates the network’s internal evaluation of the quality status of the hourly relative humidity standard
    deviation. Most users will find the preceding quality code STD_RH_QC to be the simplest and most useful
    quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9).
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀




    39


---

FLD LEN: 3
    Hourly Battery Voltage Section identifier
    The identifier that indicates an hourly observation of battery voltages. This section appears in the last ISD record
    of the hour.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CN1 An indicator of the following items:
    BATVOL average voltage
    BATVOL_QC quality code
    BATVOL_FLAG quality code
    BATVOL_FL average voltage
    BATVOL_FL_QC quality code
    BATVOL_FL_FLAG quality code
    BATVOL_DL average voltage
    BATVOL_DL_QC quality code
    BATVOL_DL_FLAG quality code

FLD LEN: 4
    BATVOL average voltage
    The hourly average voltage for the batteries powering the sensors and the transmitter.
    MIN: 0000        MAX: 9998          UNITS: volts
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    BATVOL_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the hourly average station battery voltage.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    BATVOL_QC_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the hourly average station battery voltage.
    Most users will find the preceding quality code BATVOL_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 4
    BATVOL_FL average voltage
    The voltage for the batteries powering the observing station while the station is transmitting (“full load”).
    MIN: 0000          MAX: 9998         UNITS: volts
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    BATVOL_FL_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the battery voltage under full load.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    BATVOL_FL_QC_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of battery voltage under full load. Most users
    will find the preceding quality code BATVOL_FL_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks




    40


---

FLD LEN: 4
    BATVOL_DL average voltage
    The voltage for the batteries powering the datalogger.
    MIN: 0000          MAX: 9998         UNITS: volts
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    9999 = Missing.

FLD LEN: 1
    BATVOL_DL_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the datalogger battery voltage.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    BATVOL_DL_QC_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the datalogger battery voltage. Most users
    will find the preceding quality code BATVOL_DL_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    Hourly Diagnostic Section identifier
    The identifier that indicates an hourly observation of miscellaneous diagnostic data. This section appears in the
    last ISD record of the hour
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CN2 An indicator of the following items:
    TPANEL equipment temperature
    TPANEL_QC quality code
    TPANEL_FLAG quality code
    TINLET_MAX equipment temperature
    TINLET_MAX_QC quality code
    TINLET_MAX_FLAG quality code
    OPENDOOR_TM equipment status
    OPENDOOR_TM_QC quality code
    OPENDOOR_TM_FLAG quality code

FLD LEN: 5
    TPANEL equipment temperature
    The temperature of the datalogger panel.
    MIN: -9999       MAX: +9998         UNITS: degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +9999 = Missing.

FLD LEN: 1
    TPANEL_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the datalogger panel temperature.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    TPANEL_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the datalogger panel temperature. Most
    users will find the preceding quality code TPANEL_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks




    41


---

FLD LEN: 5
    TINLET_MAX equipment temperature
    The maximum temperature of the Geonor inlet for the hour.
    MIN: -9999       MAX: +9998       UNITS: degrees Celsius
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9), a plus sign (+), and a minus sign (-).
    +9999 = Missing.

FLD LEN: 1
    TINLET_MAX_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the maximum temperature of the Geonor inlet for
    the hour.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    TINLET_MAX_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the maximum temperature of the Geonor
    inlet for the hour. Most users will find the preceding quality code TINLET_QC to be the simplest and most useful
    quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 2
    OPENDOOR_TM equipment status
    The time in minutes the datalogger door was open during the hour.
    MIN: 00        MAX: 60        UNITS: minutes
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing.

FLD LEN: 1
    OPENDOOR_TM_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the time the datalogger door was open.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    OPENDOOR_TM_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the time the datalogger door was open.
    Most users will find the preceding quality code OPENDOOR_TM_QC to be the simplest and most useful quality
    indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    Secondary Hourly Diagnostic Section identifier
    The identifier that indicates an hourly observation of miscellaneous diagnostic data. This section appears in the
    Last ISD record of the hour
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CN3 An indicator of the following items:
    REFRESAVG resistance
    REFRESAVG_QC quality code
    REFRESAVG_FLAG quality code
    DSIGNATURE identifier
    DSIGNATURE_QC quality code
    DSIGNATURE_FLAG quality code




    42


---

FLD LEN: 6
    REFRESAVG resistance
    The reference resistor average.
    MIN: 000000         MAX: 999998      UNITS: ohms
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999999 = Missing.

FLD LEN: 1
    REFRESAVG_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the datalogger reference resistor average.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    REFRESAVG_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the reference resistor average. Most users
    will find the preceding quality code REFRESAVG_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 6
    DSIGNATURE identifier
    A signature generated by the datalogger which changes if there is a content or sequence change in the
    datalogger programs.
    MIN: 000000         MAX: 999998
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999999 = Missing.

FLD LEN: 1
    DSIGNATURE_QC quality code
    The code that indicates ISD’s evaluation of the quality status of the datalogger signature.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    DSIGNATURE_FLAG quality code
    A flag that indicates the network’s internal evaluation of the quality status of the datalogger signature. Most users
    will find the preceding quality code DSIGNATURE_QC to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    Secondary Hourly Diagnostic Section identifier
    The identifier that indicates another hourly observation of miscellaneous diagnostic data. This section appears in the
    last ISD record of the hour
    DOM: A specific domain comprised of the characters in the ASCII character set.
    CN4 An indicator of the following items:
    LIQUID-PRECIPITATION gauge heater flag bit field
    LIQUID-PRECIPITATION gauge flag quality code
    LIQUID-PRECIPITATION gauge flag quality code
    DOORFLAG field
    DOORFLAG quality code
    DOORFLAG quality code
    FORTRANS wattage
    FORTRANS wattage quality code
    FORTRANS wattage quality code
    REFLTRANS wattage
    REFLTRANS wattage quality code
    REFLTRANS wattage quality code



    43


---

FLD LEN: 1
    LIQUID-PRECIPITATION gauge heater flag bit field
    The code that indicates the gauge heater flag bit field setting.
    DOM: A specific domain comprised of the numeric characters (0-1).
    0 = Off
    1 = On
    9 = Missing
    MIN: 0 MAX: 9

FLD LEN: 1
    LIQUID-PRECIPITATION gauge heater flag quality code
    The code that indicates ISD’s evaluation of the quality status of the gauge heater flag code.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    LIQUID-PRECIPITATION gauge heater flag quality code
    A flag that indicates the network’s internal evaluation of the quality status of the gauge heater flag code. Most users
    will find the preceding quality code to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 4
    DOORFLAG field
    The code that indicates the datalogger door bit field setting.
    DOM: A specific domain comprised of the numeric characters (0-1).
    0000 = Closed
    0001 – 8192 = Open
    9999 = Missing
    MIN: 0000 MAX: 9999

FLD LEN: 1
    DOORFLAG field quality code
    The code that indicates ISD’s evaluation of the quality status of the datalogger door bit field setting.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

FLD LEN: 1
    DOORFLAG field quality code
    A flag that indicates the network’s internal evaluation of the quality status of the datalogger door bit field setting code.
    Most users will find the preceding quality code to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 3
    FORTRANS wattage
    Forward transmitter RF power in tenths of watts
    MIN: 000     MAX: 500     UNITS: Watts
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing

FLD LEN: 1
    FORTRANS wattage quality code
    The code that indicates ISD’s evaluation of the quality status of the forward transmitter RF power.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing




    44


---

FLD LEN: 1
    FORTRANS wattage quality code
    A flag that indicates the network’s internal evaluation of the quality status of the forward transmitter RF power. Most
    users will find the preceding quality code to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks

FLD LEN: 3
    REFLTRANS wattage
    Reflected transmitter RF power in tenths of watts
    MIN: 000      MAX: 500      UNITS: Watts
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing

FLD LEN: 1
    REFLTRANS wattage quality code
    The code that indicates ISD’s evaluation of the quality status of the reflected transmitter RF power.
    DOM: A specific domain comprised of the numeric characters (0-9).
    1 = Passed all quality control checks
    3 = Failed all quality control checks
    9 = Missing

 FLD LEN: 1
    REFLTRANS wattage quality code
    A flag that indicates the network’s internal evaluation of the quality status of the reflected transmitter RF power. Most
    users will find the preceding quality code to be the simplest and most useful quality indicator.
    DOM: A specific domain comprised of the numeric characters (0-9)
    0 = Passed all quality control checks
    1 – 9 = Did not pass all quality checks


▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
