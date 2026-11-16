"""Parts for the Terminal 1 CM4 carrier board (Rev A): LCSC (JLCPCB) numbers and KiCad footprints.

Used by generate_schematic.py (every part's footprint and LCSC property) and, through the schematic, by generate_pcb.py.

LCSC numbers marked "CHECK" were NOT confirmed on a live LCSC / JLCPCB page while this file was written (2026-11-16):
look each one up, check stock and the footprint match, and replace "CHECK" with the C-number before ordering assembly.
tools/build_jlc_files.py treats "CHECK" as blank (JLCPCB then offers a match by value and footprint at upload).
Numbers without CHECK are JLCPCB basic parts copied from the Finish Line project's checked table (tools/boardblocks.py there);
they are generic 0603 / 0805 / 1206 passives and the USBLC6-2SC6.

Every footprint is from KiCad 10's standard libraries (drawn from the makers' datasheets); none is project-made.
"""

# ---------------------------------------------------------------- active parts and connectors: name -> (LCSC, footprint, note)
PARTS = {
    # Board-to-board: the CM4 plugs into two of these (1.5 mm stacking height, CM4 datasheet section 3.1).
    "DF40C-100DS-0.4V(51)": ("CHECK", "Connector_Hirose_DF40:Hirose_DF40C-100DS-0.4V_2x50_P0.4mm",
                             "Hirose receptacle, 100 way, 0.4 mm, 1.5 mm mated height with the CM4's DF40C-100DP plug"),
    # Display: Raspberry Pi standard 22-way 0.5 mm FPC, as DISP1 on the CM4 IO board (J16 there).
    "FH12-22S-0.5SH(55)": ("CHECK", "Connector_FFC-FPC:Hirose_FH12-22S-0.5SH_1x22-1MP_P0.50mm_Horizontal",
                           "Hirose 22 way 0.5 mm FPC connector, bottom contact, horizontal (a JLCPCB-stocked equivalent with the same land pattern is fine)"),
    # Inter-board cable (system/plan/interfaces.md section 4).
    "FH12-24S-0.5SH(55)": ("CHECK", "Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal",
                           "Hirose 24 way 0.5 mm FPC connector, bottom contact, horizontal (or the JLCPCB-stocked equivalent)"),
    # Real-time clock, as on the CM4 IO board (U8 there).
    "PCF85063AT/AAZ": ("CHECK", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                     "NXP PCF85063AT real-time clock, I2C address 0x51, SO-8 (the part the IO board fits)"),
    "32.768kHz 7pF 3215": ("CHECK", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
                           "32.768 kHz tuning-fork crystal, 3.2 x 1.5 mm, load capacitance 7 pF (PCF85063A default; "
                           "a 12.5 pF part needs quartz-load-femtofarads = <12500> in the device tree)"),
    "BAT54C": ("CHECK", "Package_TO_SOT_SMD:SOT-23",
               "Dual Schottky, common cathode (SOT-23: 1 anode A1, 2 anode A2, 3 common cathode): RTC supply OR, as IO board D3"),
    "Keystone 3034": ("CHECK", "Battery:BatteryHolder_Keystone_3034_1x20mm",
                      "CR2032 holder, surface mount (the board is the negative contact). About 4 mm tall: see build-sheet.md"),
    # LED buffer, as IO board U5.
    "74LVC1G07SE-7": ("CHECK", "Package_TO_SOT_SMD:SOT-353_SC-70-5",
                      "Single buffer, open-drain output (SOT-353: 1 NC, 2 A, 3 GND, 4 Y, 5 VCC)"),
    # USB ESD protection (not on the IO board's CM4 port itself, but standard practice on a cable that leaves the board).
    "USBLC6-2SC6": ("C7519", "Package_TO_SOT_SMD:SOT-23-6",
                    "ST USB ESD protection, 2 lines + VBUS rail (SOT-23-6: 1 IO1, 2 GND, 3 IO2, 4 IO2, 5 VBUS, 6 IO1)"),
    "LED green 0603": ("C72043", "LED_SMD:LED_0603_1608Metric", "Green LED 0603 (activity) [LCSC number from memory: CHECK at order]"),
    "LED red 0603": ("C2286", "LED_SMD:LED_0603_1608Metric", "Red LED 0603 (power) [LCSC number from memory: CHECK at order]"),
}

# ---------------------------------------------------------------- passives (JLCPCB basic parts)
FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
RESISTORS = {"0R": "C21189", "1k": "C21190", "10k": "C25804", "100k": "C25803"}
CAPACITORS = {
    "100nF": ("C14663", "Capacitor_SMD:C_0603_1608Metric"),
    "1uF": ("C15849", "Capacitor_SMD:C_0603_1608Metric"),
    "10uF 25V": ("C15850", "Capacitor_SMD:C_0805_2012Metric"),
    "22uF 25V": ("C12891", "Capacitor_SMD:C_1206_3216Metric"),
}

# ---------------------------------------------------------------- bare copper (nothing to buy)
FP_TEST_PAD = "TestPoint:TestPoint_Pad_D1.5mm"                                   # on the back, for probes and pogo pins
FP_SOLDER_JUMPER = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"       # open as made; bridge with solder to close

# ---------------------------------------------------------------- mechanical
FP_BOARD_HOLE = "MountingHole_2.2mm_M2"        # 4 x M2 board fixings (interfaces.md section 3)
FP_CM4_HOLE = "MountingHole_2.7mm_M2.5"        # 4 x M2.5 CM4 fixings (CM4 datasheet section 3.1), as the IO board


def unconfirmed():
    """Names of parts whose LCSC number still needs checking."""
    return sorted([k for k, v in PARTS.items() if v[0] == "CHECK" or "CHECK" in v[2]])
