## Part 30 - Marine Data

Marine Data

FLD LEN: 3
    WAVE-MEASUREMENT identifier
    The identifier that represents the availability of a WAVE-MEASUREMENT.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    UA1: An indicator of the occurrence of the following data items:
    WAVE-MEASUREMENT method code
    WAVE-MEASUREMENT wave period quantity
    WAVE-MEASUREMENT wave height dimension
    WAVE-MEASUREMENT quality code
    WAVE-MEASUREMENT sea state code
    WAVE-MEASUREMENT sea state code quality code

FLD LEN: 1
    WAVE-MEASUREMENT method code
    A code that represents the method used to obtain a WAVE-MEASUREMENT.
    DOM: A specific domain comprised of the ASCII characters
    M = Manual
    I = Instrumental
    9 = Missing




    106


---

FLD LEN: 2
    WAVE-MEASUREMENT wave period quantity
    The quantity of time required for two successive wave crests to pass a fixed point.
    MIN: 00         MAX: 30         UNITS: Seconds
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing.

FLD LEN: 3
    WAVE-MEASUREMENT wave height dimension
    The height of a wave measured from trough to crest.
    MIN: 000        MAX: 500    UNITS: Meters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing.

FLD LEN: 1
    WAVE-MEASUREMENT quality code
    The code that denotes a quality status of the reported WAVE-MEASUREMENT.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

FLD LEN: 2
    WAVE-MEASUREMENT sea state code
    The code that denotes the roughness of the surface of the sea in terms of average wave height.
    DOM: A specific domain comprised of the ASCII character set.
    00 = Calm, glassy - wave height = 0 meters
    01 = Calm, rippled - wave height = 0-0.1 meters
    02 = Smooth, wavelets - wave height = 0.1-0.5 meters
    03 = Slight, wave height = 0.5-1.25 meters
    04 = Moderate - wave height 1.25-2.5 meters
    05 = Rough - wave height = 2.5-4.0 meters
    06 = Very rough - wave height = 4.0-6.0 meters
    07 = High - wave height = 6.0-9.0 meters
    08 = Very high - wave height 9.0-14.0 meters
    09 = Phenomenal - wave height = over 14.0 meters
    99 = Missing

FLD LEN: 1
    WAVE-MEASUREMENT sea state code quality code
    The code that denotes a quality status of the reported WAVE-MEASUREMENT sea state code.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    WAVE-MEASUREMENT primary swell identifier
    The identifier that denotes the availability of primary swell data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    UG1: An indicator of the occurrence of the following data items:
    WAVE-MEASUREMENT primary swell period quantity
    WAVE-MEASUREMENT primary swell height dimension
    WAVE-MEASUREMENT primary swell direction angle
    WAVE-MEASUREMENT primary swell quality code




    107


---

FLD LEN: 2
    WAVE-MEASUREMENT primary swell period quantity
    The quantity of time required for two successive primary swell wave crests to pass a fixed point.
    MIN: 00         MAX: 14        UNITS: Seconds
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing

FLD LEN: 3
    WAVE-MEASUREMENT primary swell height dimension
    The height of a primary swell wave measured from the trough to the crest.
    MIN: 000        MAX: 500       UNITS: Meters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing

FLD LEN: 3
    WAVE-MEASUREMENT primary swell direction angle
    The angle measured clockwise from true north to the direction from which primary swell waves are coming.
    MIN: 001         MAX: 360      UNITS: Angular Degrees
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing

FLD LEN: 1
    WAVE-MEASUREMENT primary swell quality code
    The code that denotes a quality status of the reported WAVE-MEASUREMENT primary swell.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    WAVE-MEASUREMENT secondary swell identifier
    An indicator that denotes the start of a WAVE-MEASUREMENT secondary swell group.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    Domain Value ID: Domain Value Definition Text
    UG2: An indicator of the occurrence of the following data items:
    WAVE-MEASUREMENT secondary swell period quantity
    WAVE-MEASUREMENT secondary swell height dimension
    WAVE-MEASUREMENT secondary swell direction angle
    WAVE-MEASUREMENT secondary swell quality code

FLD LEN: 2
    WAVE-MEASUREMENT secondary swell period quantity
    The quantity of time required for two successive secondary swell wave crests to pass a fixed point.
    MIN: 00          MAX: 14       UNITS: Seconds
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    99 = Missing

FLD LEN: 3
    WAVE-MEASUREMENT secondary swell height dimension
    The height of a secondary swell wave measured from the trough to the crest.
    MIN: 000        MAX: 500     UNITS: Meters
    SCALING FACTOR: 10
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing




    108


---

FLD LEN: 3
    WAVE-MEASUREMENT secondary swell direction angle
    The angle measured clockwise from true north to the direction from which secondary swell waves are coming.
    MIN: 001         MAX: 360         UNITS: Angular Degrees
    SCALING FACTOR: 1
    DOM: A general domain comprised of the numeric characters (0-9).
    999 = Missing
FLD LEN: 1
    WAVE-MEASUREMENT secondary swell quality code
    The code that denotes a quality status of the reported WAVE-MEASUREMENT secondary swell.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    PLATFORM-ICE-ACCRETION identifier
    The identifier that denotes the availability of PLATFORM-ICE-ACCRETION data.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    WA1: An indicator of the occurrence of the following data items:
    PLATFORM-ICE-ACCRETION source code
    PLATFORM-ICE-ACCRETION thickness dimension
    PLATFORM-ICE-ACCRETION tendency code
    PLATFORM-ICE-ACCRETION quality code

FLD LEN: 1
    PLATFORM-ICE-ACCRETION source code
    The code that denotes the source of the ice that builds up on a marine platform’s structure.
    DOM: A specific domain composed of the following qualitative data values:
    Domain Value ID: Domain Value Definition Text
    1 = Icing from ocean spray
    2 = Icing from fog
    3 = Icing from spray and fog
    4 = Icing from rain
    5 = Icing from spray and rain
    9 = Missing

FLD LEN: 3
    PLATFORM-ICE-ACCRETION thickness dimension
    The thickness of the ice that has accumulated on a marine platform.
    MIN: 000      MAX: 998         UNITS: centimeters
    SCALING FACTOR: 10
    DOM: A specific domain composed of the integer values (0 - 9).
    999 = Missing

FLD LEN: 1
    PLATFORM-ICE-ACCRETION tendency code
    The code that denotes the rate of change of ice thickness on a marine platform.
    DOM: A specific domain composed of the following qualitative data values:
    Domain Value ID: Domain Value Definition Text
    0 = Ice not building up
    1 = Ice building up slowly
    2 = Ice building up rapidly
    3 = Ice melting or breaking up slowly
    4 = Ice melting or breaking up rapidly
    9 = Missing

FLD LEN: 1
    PLATFORM-ICE-ACCRETION quality code
    The code that denotes a quality status of the reported PLATFORM-ICE-ACCRETION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present




    109


---

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    WATER-SURFACE-ICE-OBSERVATION identifier.
    The identifier that denotes the availability of a WATER-SURFACE-ICE-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    WD1: An indicator of the occurrence of the following data item:
    OCEAN-ICE-OBSERVATION edge bearing code
    WATER-SURFACE-ICE-OBSERVATION uniform concentration rate
    WATER-SURFACE-ICE-OBSERVATION non-uniform concentration code
    WATER-SURFACE-ICE-OBSERVATION ship relative position code
    WATER-SURFACE-ICE-OBSERVATION ship penetrability code
    WATER-SURFACE-ICE-OBSERVATION ice trend code
    WATER-SURFACE-ICE-OBSERVATION development code
    WATER-SURFACE-ICE-OBSERVATION growler-bergy-bit presence code
    WATER-SURFACE-ICE-OBSERVATION growler-bergy-bit quantity
    WATER-SURFACE-ICE-OBSERVATION iceberg quantity
    WATER-SURFACE-ICE-OBSERVATION quality code

Note: If more than one ice, edge can be stated, the nearest or most important shall be reported.

FLD LEN: 2
    OCEAN-ICE-OBSERVATION edge bearing code
    The code that denotes the true bearing, measured from the reporting platform to the closest point of the principal ice
    edge.
    DOM: A specific domain composed of the following qualitative data values:
    00 = Ship in shore or flaw lead
    01 = Principal ice edge towards NE
    02 = Principal ice edge towards E
    03 = Principal ice edge towards SE
    04 = Principal ice edge towards S
    05 = Principal ice edge towards SW
    06 = Principal ice edge towards W
    07 = Principal ice edge towards NW
    08 = Principal ice edge towards N
    09 = Not determined (ship in ice)
    10 = Unable to report, because of darkness, lack of visibility or because only ice of land origin is visible.
    99 = Missing

    COM: 1. If more than one ice edge can be stated, the nearest or most important shall be reported
    2. The bearing shall refer to the true and not to the magnetic north

FLD LEN: 3
    WATER-SURFACE-ICE-OBSERVATION uniform concentration rate
    The percent concentration (surface coverage) of ice on the water surface.
    MIN: 000            MAX: 100            UNITS: percent
    DOM: A general domain comprised of the ASCII characters 0-9.
    999 = Missing

FLD LEN: 2
    WATER-SURFACE-ICE-OBSERVATION non-uniform concentration code
    The code that denotes the coverage arrangement of non-uniformly distributed ice.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    06 = Strips and patches of pack ice with open water between
    07 = Strips and patches of close or very close pack ice with areas of lesser concentration between
    08 = Fast ice with open water, very open or open pack ice to seaward of the ice boundary
    09 = Fast ice with close or very close pack ice to seaward of the ice boundary
    99 = Unable to report, because of darkness, lack of visibility, or because ship is more than 0.5 nautical mile away
    from ice edge

FLD LEN: 1
    WATER-SURFACE-ICE-OBSERVATION ship relative position code
    The code that denotes the relative position of the reporting ship to the ice formation.
    DOM: A specific domain comprised of the ASCII characters
    0 = Ship in open water with floating ice in sight
    1 = In open lead or fast ice
    2 = In ice or within 0.5 nautical miles of ice edge
    9 = Missing




    110


---

FLD LEN: 1
    WATER-SURFACE-ICE-OBSERVATION ship penetrability code
    The code that denotes the degree of ease with which the reporting ship can proceed through the ice.
    DOM: A specific domain comprised of the ASCII characters.
    1 = Easy
    2 = Difficult
    3 = Beset (Surrounded so closely by sea ice that steering control is lost.)
    9 = Missing

FLD LEN: 1
    WATER-SURFACE-ICE-OBSERVATION ice trend code
    The code that denotes the trend of ice conditions.
    DOM: A specific domain comprised of the ASCII characters.
    1 = Conditions improving
    2 = Conditions static
    3 = Conditions worsening
    4 = Conditions worsening; ice forming and floes freezing together
    5 = Conditions worsening; ice under slight pressure
    6 = Conditions worsening; ice under moderate or severe pressure
    9 = Missing

FLD LEN: 2
    WATER-SURFACE-ICE-OBSERVATION development code
    The code that denotes the development stage of the ice.
    DOM: A specific domain comprised of the ASCII characters
    00 = New ice only (frazil ice, grease ice, slush, slugs)
    01 = Nilas or ice rind, less than 10 cm thick
    02 = Young ice (grey ice, grey-white ice), 10 - 30 cm thick
    03 = Predominantly new and/or young ice with some first year ice
    04 = Predominantly thin first year ice with some new and/or young ice
    05 = All thin first year ice (30 - 70 cm thick)
    06 = Predominantly medium first year ice (70 - 120 cm thick) and thick first year ice (> 120 cm thick) with some
    thinner (younger) first year ice
    07 = All medium and thick first year ice
    08 = Predominantly medium and thick first year ice with some old ice (usually more than 2 m thick)
    09 = Predominantly old ice
    99 = Unable to report, because of darkness, lack of visibility or because only ice of land origin is visible or because
    ship is more than .5 NM away from ice

FLD LEN: 1
    WATER-SURFACE-ICE-OBSERVATION growler-bergy-bit presence code
    The code that denotes the existence of growler and/or bergy bits.
    DOM: A specific domain comprised of the ASCII characters
    0 = Not present
    1 = Present
    2 = Unknown
    9 = Missing

FLD LEN: 3
    WATER-SURFACE-ICE-OBSERVATION growler-bergy-bit quantity
    The quantity of growler and bergy bits observed in the area.
    MIN: 000            MAX: 998
    DOM: A general domain comprised of the ASCII characters 0-9.
    999 = Missing

FLD LEN: 3
    WATER-SURFACE-ICE-OBSERVATION iceberg quantity
    The quantity of icebergs observed in the area.
    MIN: 000             MAX: 998
    DOM: A general domain comprised of the ASCII characters 0-9.
    999 = Missing

FLD LEN: 1
    WATER-SURFACE-ICE-OBSERVATION quality code
    The code that denotes a quality status of the reported WATER-SURFACE-ICE-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect



    111


---

    3 = Erroneous
    9 = Passed gross limits check if element is present

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION identifier.
    The identifier that denotes the availability of a WATER-SURFACE-ICE-HISTORICAL-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    WG1: An indicator of the occurrence of the following data item:
    OCEAN-ICE-OBSERVATION edge bearing code
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION edge distance dimension
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION edge orientation code
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION formation type code
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION navigation effect code
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION quality code

FLD LEN: 2
    OCEAN-ICE-OBSERVATION edge bearing code
    The code that denotes the true bearing, measured from the reporting platform to the closest point of the principle ice
    edge.
    DOM: A specific domain composed of the following qualitative data values:
    00: Ship in shore or flaw lead
    01: Principal ice edge towards NE
    02: Principal ice edge towards E
    03: Principal ice edge towards SE
    04: Principal ice edge towards S
    05: Principal ice edge towards SW
    06: Principal ice edge towards W
    07: Principal ice edge towards NW
    08: Principal ice edge towards N
    09: Not determined (ship in ice)
    10: Unable to report, because of darkness, lack of visibility or because only ice of land origin is visible
    99: Missing

    COM: 1. If more than one ice edge can be stated, the nearest or most important shall be reported
    2. The bearing shall refer to the true and not to the magnetic north

FLD LEN: 2
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION edge distance dimension
    The distance from the reporting ship=s location to the nearest point on the ice edge.
    MIN: 00          MAX: 98              UNITS: Kilometers
    DOM: A general domain comprised of the ASCII characters 0-9
    99 = Missing

FLD LEN: 2
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION edge orientation code
    The code that denotes the orientation of the principal ice edge and the direction relative to which the ice lies.
    DOM: A specific domain comprised of the ASCII characters
    00: Orientation of ice edge impossible to estimate--ship outside the ice
    01: Ice edge lying in a direction NE to SW with ice situated to the NW
    02: Ice edge lying in a direction E to W with ice situated to the N
    03: Ice edge lying in a direction SE to NW with ice situated to the NE
    04: Ice edge lying in a direction S to N with ice situated to the E
    05: Ice edge lying in a direction SW to NE with ice situated to the SE




    112


---

    06: Ice edge lying in a direction W to E with ice situated to the S
    07: Ice edge lying in a direction NW to SE with ice situated to the SW
    08: Ice edge lying in a direction N to S with ice situated to the W
    09: Orientation of ice edge impossible to estimate--ship inside the ice
    99: Missing

FLD LEN: 2
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION formation type code
    The code that denotes the type of ice formation reported in the
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION.
    DOM: A specific domain comprised of the ASCII characters
    00: No ice (0 may be used to report ice blink and then a direction must be reported)
    01: New ice
    02: Fast ice
    03: Pack-ice/drift-ice
    04: Packed (compact) slush or sludge
    05: Shore lead
    06: Heavy fast ice
    07: Heavy pack-ice/drift-ice
    08: Hummocked ice
    09: Icebergs-icebergs can be reported in plain language
    99: Missing

FLD LEN: 2
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION navigation effect code
    The code that denotes the effect of ice on navigation.
    DOM: A specific domain comprised of the ASCII characters
    00: Navigation unobstructed
    01: Navigation unobstructed for steamers, difficult for sailing ships
    02: Navigation difficult for low-powered steamers, closed to sailing
    ships
    03: Navigation possible only for powerful steamers
    04: Navigation possible only for steamers constructed to withstand ice pressure
    05: Navigation possible with the assistance of ice-breakers
    06: Channel open in the solid ice
    07: Navigation temporarily closed
    08: Navigation closed
    09: Navigation conditions unknown, e.g., owing to bad weather
    99: Missing

FLD LEN: 1
    WATER-SURFACE-ICE-HISTORICAL-OBSERVATION quality code
    The code that denotes a quality status of the reported WATER-SURFACE-ICE-HISTORICAL-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Passed gross limits check
    1 = Passed all quality control checks
    2 = Suspect
    3 = Erroneous
    9 = Passed gross limits check if element is present



FLD LEN: 3
    WATER-LEVEL-OBSERVATION identifier.
    The identifier that denotes the availability of a WATER-LEVEL-OBSERVATION.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    WJ1: An indicator of the occurrence of the following data item:
    WATER-LEVEL-OBSERVATION ice thickness
    WATER-LEVEL-OBSERVATION discharge rate
    WATER-LEVEL-OBSERVATION primary ice phenomena
    WATER-LEVEL-OBSERVATION secondary ice phenomena
    WATER-LEVEL-OBSERVATION stage height
    WATER-LEVEL-OBSERVATION under ice slush condition
    WATER-LEVEL-OBSERVATION water level code




    113


---

FLD LEN: 3
    WATER-LEVEL-OBSERVATION ice thickness
    Thickness of ice on water.
    MIN: 000          MAX: 998          UNITS: centimeters
    DOM: A general domain comprised of the ASCII characters 0-9
    999 = Missing

FLD LEN: 5
    WATER-LEVEL-OBSERVATION discharge rate
    The rate of water discharge.
    MIN: 00000            MAX: 99998         UNITS: cubic meters per second
    DOM: A general domain comprised of the ASCII characters 0-9
    99999 = Missing

FLD LEN: 2
    WATER-LEVEL-OBSERVATION primary ice phenomena
    The code that denotes the primary type of ice phenomena on a river, lake or reservoir.
    DOM: A specific domain comprised of the ASCII characters
    00 = Water surface free of ice
    01 = Ice along banks
    02 = Ice crystals
    03 = Ice slush
    04 = Ice flows from tributaries entering near the river, lake or reservoir station
    10 = Floating slush ice covering approximately 1/3 (up to 30%) of the water surface
    11 = Floating slush ice covering about half (40% - 60%) of the water surface
    12 = Floating slush ice covering more than half (70% - 100%) of the water surface
    20 = Floating ice covering 10% of the water surface
    21 = Floating ice covering 20% of the water surface
    22 = Floating ice covering 30% of the water surface
    23 = Floating ice covering 40% of the water surface
    24 = Floating ice covering 50% of the water surface
    25 = Floating ice covering 60% of the water surface
    26 = Floating ice covering 70% of the water surface
    27 = Floating ice covering 80% of the water surface
    28 = Floating ice covering 90% of the water surface
    29 = Floating ice covering 100% of the water surface
    30 = Water surface frozen at station, free upstream
    31 = Water surface frozen at station, free downstream
    32 = Water surface free at station, free upstream
    33 = Water surface free at station, free downstream
    34 = Ice floes near the station, water surface frozen downstream
    35 = Water surface frozen with breaks
    36 = Water surface completely frozen over
    37 = Water surface frozen over with pile-ups
    40 = Ice melting along the banks
    41 = Some water on the ice
    42 = Ice waterlogged
    43 = Water holes in the ice cover
    44 = Ice moving
    45 = Open water in breaks
    46 = Break up (first day of movement of ice on the entire water surface)
    47 = Ice broken artificially
    50 = Ice jam below the station
    51 = Ice jam at the station
    52 = Ice jam above the station
    53 = Scale and position of jam unchanged
    54 = Jam has frozen solid in the same place
    55 = Jam has solidified and expanded upstream
    56 = Jam has solidified and moved downstream
    57 = Jam is weakening
    58 = Jam broken up by explosives or other methods
    59 = Jam broken
    60 = Fractured ice
    61 = Ice piling up againgst the bank
    62 = Ice carried towards the bank
    63 = Band of ice less than 100 meters wide fixed to banks
    64 = Band of ice less than 100 to 500 meters wide fixed to banks
    65 = Band of ice wider than 500 meters fixed to banks
    70 = Cracks in the ice, mainly across the line of flow



    114


---

    71 = Cracks along the flow line
    72 = Smooth sheet of ice
    73 = Ice sheet with pile-ups
    99 = Missing

FLD LEN: 2
    WATER-LEVEL-OBSERVATION secondary ice phenomena
    The code that denotes the secondary type of ice phenomena on a river, lake or reservoir.
    DOM: A specific domain comprised of the ASCII characters
    00 = Water surface free of ice
    01 = Ice along banks
    02 = Ice crystals
    03 = Ice slush
    04 = Ice flows from tributaries entering near the river, lake or reservoir station
    10 = Floating slush ice covering approximately 1/3 (up to 30%) of the water surface
    11 = Floating slush ice covering about half (40% - 60%) of the water surface
    12 = Floating slush ice covering more than half (70% - 100%) of the water surface
    20 = Floating ice covering 10% of the water surface
    21 = Floating ice covering 20% of the water surface
    22 = Floating ice covering 30% of the water surface
    23 = Floating ice covering 40% of the water surface
    24 = Floating ice covering 50% of the water surface
    25 = Floating ice covering 60% of the water surface
    26 = Floating ice covering 70% of the water surface
    27 = Floating ice covering 80% of the water surface
    28 = Floating ice covering 90% of the water surface
    29 = Floating ice covering 100% of the water surface
    30 = Water surface frozen at station, free upstream
    31 = Water surface frozen at station, free downstream
    32 = Water surface free at station, free upstream
    33 = Water surface free at station, free downstream
    34 = Ice floes near the station, water surface frozen downstream
    35 = Water surface frozen with breaks
    36 = Water surface completely frozen over
    37 = Water surface frozen over with pile-ups
    40 = Ice melting along the banks
    41 = Some water on the ice
    42 = Ice waterlogged
    43 = Water holes in the ice cover
    44 = Ice moving
    45 = Open water in breaks
    46 = Break up (first day of movement of ice on the entire water surface)
    47 = Ice broken artificially
    50 = Ice jam below the station
    51 = Ice jam at the station
    52 = Ice jam above the station
    53 = Scale and position of jam unchanged
    54 = Jam has frozen solid in the same place
    55 = Jam has solidified and expanded upstream
    56 = Jam has solidified and moved downstream
    57 = Jam is weakening
    58 = Jam broken up by explosives or other methods
    59 = Jam broken
    60 = Fractured ice
    61 = Ice piling up againgst the bank
    62 = Ice carried towards the bank
    63 = Band of ice less than 100 meters wide fixed to banks
    64 = Band of ice less than 100 to 500 meters wide fixed to banks
    65 = Band of ice wider than 500 meters fixed to banks
    70 = Cracks in the ice, mainly across the line of flow
    71 = Cracks along the flow line
    72 = Smooth sheet of ice
    73 = Ice sheet with pile-ups
    99 = Missing




    115


---

FLD LEN: 5
    WATER-LEVEL-OBSERVATION stage height
    The height of the stage above zero.
    MIN: -999           MAX: +9998          UNITS: centimeters
    DOM: A general domain comprised of the ASCII characters 0-9
    +9999 = Missing

FLD LEN: 1
    WATER-LEVEL-OBSERVATION under ice slush condition
    The code that denotes the slush condition under an ice layer.
    DOM: A specific domain comprised of the ASCII characters
    0 = No slush ice
    1 = Slush ice to approximately 1/3 of depth of the river, lake or reservoir
    2 = Slush ice from 1/3 to 2/3 of depth of the river, lake or reservoir
    3 = Slush ice to depth of the river, lake or reservoir greater than 2/3.
    9 = Missing

FLD LEN: 1
    WATER-LEVEL-OBSERVATION water level code
    The code that denotes the state of the water level.
    DOM: A specific domain comprised of the ASCII characters
    B = much below normal
    H = high but not overflowing
    N = normal
    O = banks overflowing
    9 = missing




▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

    Remarks Data Section
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    GEOPHYSICAL-POINT-OBSERVATION remarks identifier
    The identifier that denotes the beginning of the remarks data section.
    DOM: A specific domain comprised of the ASCII character set.
    REM = Remarks Data Section

FLD LEN: 3
    GEOPHYSICAL-POINT-OBSERVATION remark identifier
    An indicator of the type of surface remarks data contained in the GEOPHYSICAL-POINT-
    OBSERVATION-REMARK text
    DOM: A specific domain composed of the following qualitative data values.
    Domain Value ID = Domain Value Definition Text
    SYN = Synoptic Remarks


    116


---

    AWY = Airways Remarks
    MET = METAR Remarks
    SOD = Summary of Day Remarks
    SOM = Summary of Month Remarks
    HPD = Hourly Precipitation Data Remarks
    Indicate the occurrence of the following data items:
    GEOPHYSICAL-POINT-OBSERVATION remark length quantity
    GEOPHYSICAL-POINT-OBSERVATION remark text

FLD LEN: 3
    GEOPHYSICAL-POINT-OBSERVATION remark length quantity
    A quantity that indicates the length of an individual GEOPHYSICAL-POINT-OBSERVATION-REMARK text.
    MIN: 001             MAX: 999
    DOM: A general domain composed of the ASCII characters (001-999).

FLD LEN: 999 (maximum)
    GEOPHYSICAL-POINT-OBSERVATION remark text
    The text of a GEOPHYSICAL-POINT-OBSERVATION-REMARK.
    DOM: A general domain comprised of the characters in the ASCII character set.




    117


---

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

    Element Quality Data Section
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    GEOPHYSICAL-POINT-OBSERVATION quality data identifier
    The identifier that denotes the beginning of the element quality data section.
    DOM: A specific domain comprised of the ASCII character set.
    EQD = Element Quality Data

FLD LEN: 3
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY identifier
    The identifier that denotes the existence of ORIGINAL-OBSERVATION-ELEMENT-QUALITY data.
    DOM: A specific domain comprised of the ASCII character set.
    Q01 – Q99: The following may be occur from 0 to 99 times, for AFAW USAF SURFACE HOURLY and for I
    ISD Version 2, and
    P01 – P99: The following may be occur from 0 to 99 times, for ISD Version 2 (P denotes data originated
    from historical NCEI HOURLY PRECIPITATION or NCEI SURFACE HOURLY data), and
    R01 – R99: The following may be occur from 0 to 99 times, for ISD Version 2 and 3 (R denotes data
    originated from an NCEI data source from 2006 forward)
    C01 – C99: The original value failed due to a table constraint
    D01 – D99: The original value was replaced using a temporary quality control process after the data was
    originally loaded to the table
    N01 – N99: (see subsection below for details)
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY original value text
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY reason code
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY parameter code

FLD LEN: 6
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY original value text
    The original value text for elements which was rejected or recomputed during validation.
    DOM: A general domain comprised of the characters in the ASCII character set

FLD LEN: 1
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY reason code
    The code that denotes the reason an element was identified as suspect, erroneous or recomputed, or in the case of data
    originating from NCEI SURFACE HOURLY, the units code for the data are stored in this position, and the data quality
    flag is stored with the parameter code.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    0 = Original value missing or corrupted
    1 = Gross error checks (range and/or domain check)
    2 = Geophysical checks (checking the validity against other parameters)
    3 = Consistency checks (checking the validity against the same type of parameter)
    4 = Gross error checks and geophysical checks
    5 = Gross error checks and consistency checks
    6 = Geophysical checks and consistency checks
    7 = Gross error checks and geophysical checks and consistency checks

FLD LEN: 6
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY parameter code
    The code that denotes the type of parameter that the supplemental-level-element-quality applies to.
    DOM: A specific domain comprised of the characters in the ASCII character set.
    Comment Text:
    APC3 = ATMOSPHERIC-PRESSURE-CHANGE THREE HOUR CHANGE QUANTITY
    ATOLD = AIR-TEMPERATURE-OBSERVATION-LEVEL DEWPOINT TEMPERATURE
    WOSPD = WIND-OBSERVATION SPEED RATE
    WOLSPD = WIND-OBSERVATION-LEVEL SPEED RATE
    WOLDIR = WIND-OBSERVATION-LEVEL DIRECTION ANGLE
    WODIR = WIND-OBSERVATION DIRECTION ANGLE
    ATOLDS = AIR-TEMPERATURE-OBSERVATION-LEVEL DENSITY RATE
    ATOLT = AIR-TEMPERATURE-OBSERVATION-LEVEL AIR TEMPERATURE
    ATOD = AIR-TEMPERATURE-OBSERVATION DEW POINT TEMPERATURE
    ATOT = AIR-TEMPERATURE-OBSERVATION AIR TEMPERATURE
    APOSP = ATMOSPHERIC-PRESSURE-OBSERVATION STATION PRESSURE RATE
    APOSLP = ATMOSPHERIC-PRESSURE-OBSERVATION SEA LEVEL PRESSURE
    APOLP = ATMOSPHERIC-PRESSURE-OBSERVATION-LEVEL PRESSURE RATE


    118


---

    APOLH = ATMOSPHERIC-PRESSURE-OBSERVATION-LEVEL HEIGHT DIMENSION
    APOA = ATMOSPHERIC-PRESSURE-OBSERVATION ALTIMETER RATE
    WGOSPD = WIND-GUST-OBSERVATION SPEED RATE
    APCQ24 = ATMOSPHERIC-PRESSURE-CHANGE TWENTY FOUR HOUR QUANTITY
    APCTEN = ATMOSPHERIC-PRESSURE-CHANGE TENDENCY CODE
    PRSWOA = PRESENT-WEATHER-OBSERVATION AUTOMATED ATMOSPHERIC CONDITION CODE
    PRSWM1 = PRESENT-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PRSWM2 = PRESENT-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PRSWM3 = PRESENT-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PRSWM4 = PRESENT-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PRSWM5 = PRESENT-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PRSWM6 = PRESENT-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PRSWM7 = PRESENT-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PRSWA1 = PRESENT-WEATHER-OBSERVATION AUTOMATED ATMOSPHERIC CONDITION CODE
    PRSWA2 = PRESENT-WEATHER-OBSERVATION AUTOMATED ATMOSPHERIC CONDITION CODE
    PRSWA3 = PRESENT-WEATHER-OBSERVATION AUTOMATED ATMOSPHERIC CONDITION CODE
    PRSWA4 = PRESENT-WEATHER-OBSERVATION AUTOMATED ATMOSPHERIC CONDITION CODE
    PSTWA1 = PAST-WEATHER-OBSERVATION AUTOMATED ATMOSPHERIC CONDITION CODE
    PSTWA2 = PAST-WEATHER-OBSERVATION AUTOMATED ATMOSPHERIC CONDITION CODE
    PSTWM1 = PAST-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PSTWM2 = PAST-WEATHER-OBSERVATION MANUAL ATMOSPHERIC CONDITION CODE
    PSTWOP = PAST-WEATHER-OBSERVATION PERIOD QUANTITY
    SCOCIG = SKY-CONDITION-OBSERVATION CEILING HEIGHT DIMENSION
    SCOHCG = SKY-CONDITION-OBSERVATION HIGH CLOUD GENUS CODE
    SCOLCB = SKY-CONDITION-OBSERVATION LOWEST CLOUD BASE HEIGHT DIMENSION
    SCOLCG = SKY-CONDITION-OBSERVATION LOW CLOUD GENUS CODE
    SCOMCG = SKY-CONDITION-OBSERVATION MID CLOUD GENUS CODE
    SCOTCV = SKY-CONDITION-OBSERVATION TOTAL COVERAGE CODE
    SCOTLC = SKY-CONDITION-OBSERVATION TOTAL LOWEST CLOUD COVER CODE
    VODIS = VISIBILITY-OBSERVATION DISTANCE DIMENSION
    VOVAR = VISIBILITY-OBSERVATION VARIABILITY CODE
    PRCP = LIQUID PRECIPITATION DEPTH DIMENSION
    ATMM = EXTREME AIR TEMPERATURE, MAXIMUM AND MINIMUM
    ATMN = EXTREME AIR TEMPERATURE, MINIMUM
    ATMX = EXTREME AIR TEMPERATURE, MAXIMUM
    SNDP = SNOW DEPTH DIMENSION
    SNWF = SNOW ACCUMULATION DEPTH DIMENSION

The following parameter codes may occur with the R01 – R99 identifier. They pertain to QC of the Max Short Duration
Precipitation fields AH1 - AH6 and AI1 – AI6. The 6 character field will be represented as follows:

First 3 characters:
A01 – A12 -- indicates this pertains to a precipitation amount, which is stored as the EQD original value
D01 – D12 -- indicates this pertains to the ending day field, which is stored as the EQD original value
T01 – T12 -- indicates this pertains to the ending time field, which is stored as the EQD original value
Note: Values of 01-06 indicate that AH1 – AH6, respectively, are flagged. Values of 07-12 indicate that AI1 – AI6,
respectively, are flagged.
These codes will be followed by the 3 character flag description number to complete the 6 character definition. These
codes are as follows:
001 INVALID MSDP 5 MIN AMT
002 MSDP 5 MIN AMT OUT OF RANGE
003 INVALID MSDP 5 MIN DATE
004 MSDP 5 MIN DATE OUT OF RANGE
005 INVALID MSDP 5 MIN TIME
006 MSDP 5 MIN TIME OUT OF RANGE
007 INVALID MSDP 10 MIN AMT
008 MSDP 10 MIN AMT > 2 X 5 MIN AMT
009 INVALID MSDP 10 MIN DATE
010 MSDP 10 MIN DATE OUT OF RANGE
011 INVALID MSDP 10 MIN TIME
012 MSDP 10 MIN TIME OUT OF RANGE
013 INVALID MSDP 15 MIN AMT
014 MSDP 15 MIN AMT > 5 + 10 MIN AMT
015 INVALID MSDP 15 MIN DATE
016 MDSP 15 MIN DATE OUT OF RANGE
017 INVALID MSDP 15 MIN TIME
018 MSDP 15 MIN TIME OUT OF RANGE
019 INVALID MSDP 20 MIN AMT
020 MSDP 20 MIN AMT > 5 + 15 MIN AMT



    119


---

    021   MSDP 20 MIN AMT > 2 X 10 MIN AMT
    022   INVALID MSDP 20 MIN DATE
    023   MSDP 20 MIN DATE OUT OF RANGE
    024   INVALID MSDP 20 MIN TIME
    025   MSDP 20 MIN TIME OUT OF RANGE
    026   INVALID MSDP 30 MIN AMT
    027   MSDP 30 MIN AMT > 10 + 20 MIN AMT
    028   MSDP 30 MIN AMT > 2 X 15 MIN AMT
    029   INVALID MSDP 30 MIN DATE
    030   MSDP 30 MIN DATE OUT OF RANGE
    031   INVALID MSDP 30 MIN TIME
    032   MSDP 30 MIN TIME OUT OF RANGE
    033   INVALID MSDP 45 MIN AMT
    034   MSDP 45 MIN AMT > 15 + 30 MIN AMT
    035   INVALID MSDP 45 MIN DATE
    036   MSDP 45 MIN DATE OUT OF RANGE
    037   INVALID MSDP 45 MIN TIME
    038   MSDP 45 MIN TIME OUT OF RANGE
    039   INVALID MSDP 60 MIN AMT
    040   MSDP 60 MIN AMT > 15 + 45 MIN AMT
    041   MSDP 60 MIN AMT > 2 X 30 MIN AMT
    042   INVALID MSDP 60 MIN DATE
    043   MSDP 60 MIN DATE OUT OF RANGE
    044   INVALID MSDP 60 MIN TIME
    045   MSDP 60 MIN TIME OUT OF RANGE
    046   INVALID MSDP 80 MIN AMT
    047   MSDP 80 MIN AMT > 20 + 60 MIN AMT
    048   INVALID MSDP 80 MIN DATE
    049   MSDP 80 MIN DATE OUT OF RANGE
    050   INVALID MSDP 80 MIN TIME
    051   MSDP 80 MIN TIME OUT OF RANGE
    052   INVALID MSDP 100 MIN AMT
    053   MSDP 100 MIN AMT > 20 + 80 MIN AMT
    054   INVALID MSDP 100 MIN DATE
    055   MSDP 100 MIN DATE OUT OF RANGE
    056   INVALID MSDP 100 MIN TIME
    057   MSDP 100 MIN TIME OUT OF RANGE
    058   INVALID MSDP 120 MIN AMT
    059   MSDP 120 MIN AMT > 20 + 100 MIN AMT
    060   MSDP 120 MIN AMT > 2 X 60 MIN AMT
    061   INVALID MSDP 120 MIN DATE
    062   MSDP 120 MIN DATE OUT OF RANGE
    063   INVALID MSDP 120 MIN TIME
    064   MSDP 120 MIN TIME OUT OF RANGE
    065   INVALID MSDP 150 MIN AMT
    066   MSDP 150 MIN AMT > 30 + 120 MIN AMT
    067   INVALID MSDP 150 MIN DATE
    068   MSDP 150 MIN DATE OUT OF RANGE
    069   INVALID MSDP 150 MIN TIME
    070   MSDP 150 MIN TIME OUT OF RANGE
    071   INVALID MSDP 180 MIN AMT
    072   MSDP 180 MIN AMT > 60 + 120 MIN AMT
    073   INVALID MSDP 180 MIN DATE
    074   MSDP 180 MIN DATE OUT OF RANGE
    075   INVALID MSDP 180 MIN TIME
    076   MSDP 180 MIN TIME OUT OF RANGE
    077   MSDP 60 MIN VAL DISAGREES W/HR
    078   MSDP 120 MIN VAL DISAGREES W/HR
    079   MSDP 180 MIN VAL DISAGREES W/HR




FLD LEN: 3
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY identifier
    The identifier that denotes the existence of ORIGINAL-OBSERVATION-ELEMENT-QUALITY data. These data will
    appear after the Q## data described above.
    DOM: A specific domain comprised of the ASCII character set.
    N01 - N99: The following may be occur from 0 to 99 times, for NCEI NCEI SURFACE HOURLY:
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY original value text


    120


---

    ORIGINAL-OBSERVATION-ELEMENT-QUALITY units code
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY parameter code

FLD LEN: 6
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY original value text
    The original value text for elements which were rejected or recomputed during validation.
    DOM: A general domain comprised of the characters in the ASCII character set

FLD LEN: 1
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY units code
    The code that denotes the units code for the data are stored in this position,
    and the data quality flag is stored with the parameter code below.
    DOM: A specific domain comprised of the characters in the ASCII character set.

    ELEMENT-UNITS TABLE
    Value        Equates to this value from original NCEI SURFACE HOURLY
    A          DT Wind direction in tens of degrees
    B             F        Whole degrees Fahrenheit
    C             HF    Hundreds of feet
    D             HM Miles and hundredths
    E             IH   Inches and hundredths of mercury
    F             IT   Inches and thousandths of mercury
    G             KD knots and direction in tens of degrees
    H             KS Knots and direction in 16 point WBAN Code
    I             MT Millibars and tenths
    J             NA No units applicable (non-dimensional)
    K             N1 No units applicable - element to tenths
    L             N2 No units applicable - element to hundredths
    M              P   Whole percent
    O              TC Degrees Celsius in tenths
    P             TF Degrees Fahrenheit in tenths
    Q              IS   Miles per hour and sixteen-point wind compass
    R             MS Meters per second and sixteen-point wind compass

FLD LEN: 6
    ORIGINAL-OBSERVATION-ELEMENT-QUALITY parameter code
    The code that denotes the type of parameter that the supplemental-level-element-quality applies to.
    DOM: A specific domain comprised of the characters in the ASCII character set.

    First 4 characters = the element name as defined below.
    Position 5 = the Flag 1 value as defined below.
    Position 6 = Flag 2 value as defined below.

    Element names and definitions:

    ALC Sky condition in tenths from ASOS
    ALM Sky condition in eighths from ASOS
    ALTP Altimeter setting
    CC51 Sky condition prior to 1951
    CLC Sky condition in tenths
    CLM Sky condition in eighths
    CLHT Ceiling height
    CLT Cloud type and height by layer
    C2C3 Total cloud cover by first 2 and first 3 layers
    DPTC Dew point temperature in celsius
    DPTP Dew point temperature in fahrenheit
    HZVS Horizontal visibility
    PRES Station pressure
    PWTH Present weather
    PWVC Present weather in vicinity
    RHUM Relative humidity
    SCH Sky condition (amount and modifier, e.g., thin broken) and height by layer
    SLVP Sea level pressure
    TMCD Dry bulb temperature in celsius
    TMPD Dry bulb temperature in fahrenheit
    TMPW Wet bulb temperature in fahrenheit
    TSCE Total sky cover in eighths
    TSKC Total sky cover in tenths
    TSKY Same as TSKC but expressed in terms of amount and modifier, e.g., thin broken.



    121


---

WD16 Wind direction and speed in 16 point code
WIND Wind direction and speed
WND2 Wind direction and speed from ASOS

FLAG-1 (Measurement Value):

    A        Wind speed expressed in Beaufort scale, different from the day's given units
    C        Ceiling of cirroform clouds at unknown height (Sep 56 - Mar 70)
    D        Derived value
    E        Estimated value
    G        Visibility > or = 100 miles (data value = 10000)
    H        Hundredths precision only is indicated in the original observation (except as when found in SLVP with
    units code MT, this flag means original value is expressed in inches to hundredths, not hundredths of
    millibars)
    I        Wind speed in miles per hour, different from the day's given units
    K        Wind speed in knots, different from the day's given units
    M        Visibility missing (data value = 99999)
    N         Unlimited visibility (data value = 99999)
    P        Wind speed in pounds per square foot perpendicular to the wind
    R         Dew Point and/or Relative Humidity, originally calculated with respect to ice have been recomputed
    with respect to water. (DPTP, RHUM)
    S        Wind speed in meters per second, different from the day's given units
    W        Whole precision only is indicated in the original observation
    U         Unlimited ceiling height (DATA-VALUE = 99999). (CLHT)
    b         (blank) Flag not needed. (All elements except CC51)


 FLAG-2 (Data Quality Flag Value):

    0        Observed data has passed all internal consistency checks.
    1        Validity indeterminable (primarily for pre-1984 data).
    2        Observed data has failed an internal consistency check - subsequent edited value follows observed
    value.
    3        Data beginning January 1,1984 - observed data has failed a consistency check - No edited value
    follows.
    Data prior to 1 Jan 84 - observed data exceeded preselected climatological limits during conversion
    from historic TD-1440 files. No edited value follows.
    4        Observed data value invalid - no edited value follows.
    5        Data converted from historic TD-1440 exceeded known climatological extremes - no edited value
    follows.
    6        Complex QA indicates data are erroneous, and an edited value follows.
    E        Edited data value passes all system checks - no observed value present.
    M        Manually edited data value added to data set after original archival. Automated edit not performed on
    this item.
    S        Manually edited data passes all system checks.




    122


---

▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

    Original Observation Data Section
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀

FLD LEN: 3
    ORIGINAL-OBSERVATION-NCEI SURFACE HOURLY identifier
    The identifier that denotes the existence of ORIGINAL-OBSERVATION-NCEI SURFACE HOURLY information. This is
    used in specific instances where the original data from a previous format is stored for quality control purposes. In most
    cases, this section is not included, since original input data sources are always maintained/archived at NCEI.
    DOM: A specific domain comprised of the ASCII character set.
    QNN: The following may be occur from 0 to 99 times, for NCEI NCEI SURFACE HOURLY:
    ORIGINAL-OBSERVATION-NCEI SURFACE HOURLY original source codes and flags

FLD LEN: 5
    ORIGINAL-OBSERVATION-NCEI SURFACE HOURLY source codes and flags
    The original source codes and flags from NCEI SURFACE HOURLY, for possible future use in ISD dataset quality
    control.
    DOM: A specific domain comprised of the ASCII character set.
    For each original NCEI SURFACE HOURLY data record, the source code 1 and 2, and flag 1 and 2 original values are
    stored as follows:

    QNN@1234@1234@1234 where:
    QNN = indicator for section
    @ = element identifier (see below)
    1234 = source code 1, source code 2, flag 1, and flag 2 sequentially, for each element as defined in original DSI-
    3280.

    Element Identifiers (@) as mentioned above, with the original DS3280 element that it refers to (eg, A = element ALC):
    A   ALC
    B   ALM
    C   ALTP
    D   CC51
    E   CLC
    F   CLM
    G   CLHT
    H   CLT
    I   C2C3
    J   DPTC
    K   DPTP
    L   HZVS
    M   PRES
    N   PWTH
    O   PWVC
    P   RHUM
    Q   SLVP
    R   TMCD
    S   TMPD
    T   TMPW
    U   TSCE
    V   TSKC
    W   WD16
    X   WIND
    Y   WND2

FLD LEN: 6
    ORIGINAL-OBSERVATION-NCEI SURFACE HOURLY data value
    The original data value from NCEI SURFACE HOURLY, as defined for the element above, for possible future use in ISD
    dataset quality control.
    DOM: A specific domain comprised of the ASCII character set.




    123


---

7.     Start Date:

    1900, but the date will vary greatly by station.

8.     Stop Date: Present

9.     Coverage:

    a.   Southernmost Latitude: 9000S
    b.   Northernmost Latitude: 9000N
    c.   Westernmost Longitude: 18000W
    d.   Easternmost Longitude: 18000E

10.    Location: Global

11.    Keywords:

  a.   Temperature
    b.   Dew Point
    c.   Wind Speed
    d.   Wind Gust
    e.   Wind Direction
    f.   Ceiling
    g.   Sky Cover
    h.   Cloud Layer Data
    i.   Visibility
    j.   Present Weather
    k.   Past Weather
    l.   Sea Level Pressure
    m.   Altimeter Setting
    n.   Station Pressure
    o.   3-hour Pressure Change
    p.   Precipitation Amount
    q.   Snowfall
    r.   Snow Depth
    s.   Maximum Temperature
    t.   Minimum Temperature
    u.     US Air Force
    v.   Clouds
    w.   Surface

12.    How to Order Data:

    Order from:
    National Centers for Environmental Information
    Federal Building
    151 Patton Avenue
    Asheville, NC 28801-5001
    phone: (828) 271-4800
    email: NCEI.orders@noaa.gov

13.    Archiving Data Centers:

    Air Force Combat Climatology Center (AFCCC)
    Federal Building


    124


---

    151 Patton Avenue
    Asheville, NC 28801-5001

14.   Technical Contact:

    National Centers for Environmental Information
    Climate Access Branch
    Federal Building
    151 Patton Avenue
    Asheville, NC 28801-5001
    phone: (828) 271-4800
    email: ncei.orders@noaa.gov

15.   Known Uncorrected Problems:

    Minimal number of random errors, decode errors, and reporting errors
    (by station)--less than .1% of observations affected overall.
    Most errors corrected/eliminated by quality control software.

16.   Quality Statement:

    Data have undergone extensive automated quality control, and additional
    manual quality control for US Air Force stations, US Navy stations, and
    US National Weather Service stations.

17.   Revision Date: N/A

18.   Source Data Sets:

    AFCCC USAF SURFACE HOURLY Surface Hourly, NCEI DS3280 Surface Hourly,
    NCEI DS3240
    Hourly Precipitation. AFCCC USAF SURFACE HOURLY includes over 100
    source datasets, while NCEI DS3280 includes several original input
    sources; so over 100 original input sources are included in the current
    ISD archive.
    Beginning in 2006, additional data sources are being added, and will be
    documented here as they become available online.

19.   Essential Companion Data Sets: N/A

20.   Derived Data Sets: Global summary of day for 1929-present

21.   References: N/A

22.   Summary:

    The Integrated Surface Data (ISD) is composed of worldwide surface
    weather observations from over 20,000 stations, collected and stored
    from sources such as the Automated Weather Network (AWN), the Global
    Telecommunications System (GTS), the Automated Surface Observing System
    (ASOS), and data keyed from paper forms. Most digital observations are
    decoded either at operational centers and forwarded to the Federal
    Climate Complex (FCC) in Asheville, NC, or decoded at the FCC. NOAA’s
    National Centers for Enviornmental Information (NCEI) and the US Air
    Force’s 14th Weather Squadron (14WS) make up the FCC in Asheville, NC.
    Each agency is responsible for data ingest, quality control, and
    customer support for surface climatological data. All data are now
    stored in a single ASCII format. The dataset is used in climatological
    applications by numerous DOD and civilian customers.

    125


---

ISD (formerly known as ISH) refers to the digital dataset and format in
which hourly, synoptic (3-hourly), daily, monthly, and various other
weather/climate observations are stored. The format conforms to Federal
Information Processing Standards (FIPS). The dataset includes data
originating from various codes such as synoptic, airways, METAR
(Meteorological Routine Weather Report), and SMARS (Supplementary
Marine Reporting Station), as well as observations from automatic
weather stations. The data are sorted by station, year-month-day-hour-
minute, report type, and data source flag. This document provides
complete documentation for the dataset and its format.




    126


---
