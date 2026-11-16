"""Parts table for the keyboard and power board (Rev A): LCSC / JLCPCB part numbers and KiCad footprints.

Same pattern as the reference project's tools/boardblocks.py: generate_schematic.py builds every part from this table, so the
LCSC number and footprint live in one place and flow into the schematic ("LCSC" property), the board and the JLCPCB BOM.

How sure each number is (column "source"):
  reference   used on an earlier board of the reference project (finish-line, tools/boardblocks.py)
  search      found by a web search on 2026-11-16 (LCSC / JLCPCB product page in the results); stock and price NOT checked
  memory      a widely used number recalled from memory, not looked up this time
  CHECK       not looked up: the LCSC field is left empty, so JLCPCB matches the part by value and footprint at upload.
              Look the number up and fill it in before ordering.
Nothing here was checked against a live JLCPCB stock page. Confirm every line (and Basic / Extended status) at order time.

Footprints are KiCad 10's own libraries unless they start with "terminal-1:" (project footprints written by
generate_pcb.py into terminal-1.pretty: only the Q20 keyboard connector, see keyboard_connector_footprint() there).
"""

# name: (LCSC number or "", KiCad footprint, source, note)
PARTS = {
    # ---- controller ----
    "RP2040": ("C2040", "Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP3.2x3.2mm", "memory",
               "Raspberry Pi RP2040, QFN-56 7 x 7"),
    "W25Q128JVPIQ": ("C190862", "Package_SON:WSON-8-1EP_6x5mm_P1.27mm_EP3.4x4.3mm", "search",
                     "16 MB QSPI flash, WSON-8 6 x 5 x 0.8 (the SOIC-8 208 mil version is up to 2.16 mm tall: over the 2.0 mm limit)"),
    "X322512MSB4SI": ("C9002", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "search",
                      "12 MHz crystal, 3225, load capacitance 20 pF (JLCPCB Basic)"),
    # ---- power ----
    "BQ25895RTWR": ("C80200", "Package_DFN_QFN:Texas_RTW_WQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm", "search",
                    "1-cell 5 A charger with power path, I2C, WQFN-24 (one listing marks it NRND: check lifecycle)"),
    "TPS61089RNRR": ("C165129", "Package_DFN_QFN:Texas_VQFN-RNR0011A-11", "search",
                     "7 A synchronous boost, VQFN-11 2 x 2.5 (replaces the TPS61088 named in the plan: see circuit-notes.md)"),
    "MAX17048G+T10": ("C2682616", "Package_DFN_QFN:TDFN-8-1EP_2x2mm_P0.5mm_EP0.8x1.2mm", "search",
                      "fuel gauge, TDFN-8 2 x 2 (footprint exposed-pad size CHECK against Maxim's T822 land pattern)"),
    "ME6211C33M5G-N": ("C82942", "Package_TO_SOT_SMD:SOT-23-5", "reference", "3.3 V LDO 500 mA, about 40 uA quiescent"),
    "ME6211C28M5G-N": ("C53099", "Package_TO_SOT_SMD:SOT-23-5", "search", "2.8 V LDO for the trackpad"),
    "ME6211C18M5G-N": ("C236671", "Package_TO_SOT_SMD:SOT-23-5", "search", "1.8 V LDO for the trackpad I/O"),
    "FXL0420-1R0-M": ("C167203", "Inductor_SMD:L_Changjiang_FXL0420", "search",
                      "1 uH charger inductor, 4.4 x 4.2 x 2.0, about 6 A (rating definition CHECK)"),
    "FXL0630-2R2-M": ("C167218", "Inductor_SMD:L_Changjiang_FXL0630", "search",
                      "2.2 uH boost inductor, 7 x 6.6 x 3.0, Isat 10 A, 15 mOhm (datasheet table); 3.0 mm tall: frame cut-out"),
    # ---- USB ----
    "TYPE-C-31-M-12": ("C165948", "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "reference",
                       "USB-C receptacle, top mount, 3.2 mm tall: frame cut-out (mid-mount is an open item)"),
    "USBLC6-2SC6": ("C7519", "Package_TO_SOT_SMD:SOT-23-6", "reference", "USB ESD protection"),
    "TS3USB221DRCR": ("C324071", "Package_SON:VSON-10-1EP_3x3mm_P0.5mm_EP1.65x2.4mm", "search",
                      "USB 2.0 1:2 switch, VSON-10 3 x 3 (exposed-pad size CHECK against TI's DRC land pattern)"),
    # ---- connectors and switches ----
    "BM20B(0.8)-40DS-0.4V(51)": ("C424543", "terminal-1:Hirose_BM20B-0.8-40DS-0.4V", "search",
                                 "Q20 keyboard + trackpad board-to-board receptacle, 40 pins 0.4 mm (as BBQ20KBD U4)"),
    "FH12-24S-0.5SH(55)": ("C202112", "Connector_FFC-FPC:Hirose_FH12-24S-0.5SH_1x24-1MP_P0.50mm_Horizontal", "search",
                           "24-way 0.5 mm FFC connector to the carrier board, bottom contact, 2.0 mm tall"),
    "SKRTLAE010": ("C110293", "Button_Switch_SMD:SW_Push_1P1T-MP_NO_Horizontal_Alps_SKRTLAE010", "search",
                   "side-push power button on the right edge"),
    "TS-1187A-B-A-B": ("C318884", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", "reference", "BOOTSEL button"),
    # ---- small semiconductors ----
    "BSS138": ("C78284", "Package_TO_SOT_SMD:SOT-23", "search", "N-MOSFET, low threshold: 1.8 V level shifters (as BBQ20KBD)"),
    "2N7002": ("C8545", "Package_TO_SOT_SMD:SOT-23", "memory", "N-MOSFET: open-drain drivers to the CM4"),
    "AO3400A": ("C20917", "Package_TO_SOT_SMD:SOT-23", "memory", "N-MOSFET 5.7 A: keyboard backlight low-side switch"),
    "B5819W": ("C8598", "Diode_SMD:D_SOD-123", "reference", "Schottky: power button to BQ25895 /QON"),
}

# 0603 resistors. reference = used in the finish-line boards; "" = CHECK (JLCPCB matches by value at upload)
RESISTOR_0603 = {"10k": "C25804", "100k": "C25803", "4k7": "C23162", "1k": "C21190", "5k1": "C23186", "100R": "C22775",
                 "27R": "", "120R": "", "30k": "", "47k": "", "150k": "", "127k": "", "301k": "", "6k8": ""}
# capacitors: value -> (LCSC, footprint). reference values from finish-line; "" = CHECK
CAPACITOR = {"100nF": ("C14663", "Capacitor_SMD:C_0603_1608Metric"),
             "1uF": ("C15849", "Capacitor_SMD:C_0603_1608Metric"),
             "10uF 25V": ("C15850", "Capacitor_SMD:C_0805_2012Metric"),
             "22uF 25V": ("C12891", "Capacitor_SMD:C_1206_3216Metric"),
             "1nF": ("C1588", "Capacitor_SMD:C_0603_1608Metric"),
             "4.7uF 10V": ("", "Capacitor_SMD:C_0603_1608Metric"),
             "2.2uF": ("", "Capacitor_SMD:C_0603_1608Metric"),
             "47nF": ("", "Capacitor_SMD:C_0603_1608Metric"),
             "4.7nF": ("", "Capacitor_SMD:C_0603_1608Metric"),
             "33pF": ("", "Capacitor_SMD:C_0603_1608Metric")}
FOOTPRINT_RESISTOR = "Resistor_SMD:R_0603_1608Metric"
FOOTPRINT_TEST_PAD = "TestPoint:TestPoint_Pad_D1.5mm"          # bare copper pads on the back (nothing to buy)
FOOTPRINT_SOLDER_PAD = "Connector_Wire:SolderWire-0.5sqmm_1x03_P4.6mm_D0.9mm_OD2.1mm"   # battery wires: 0.5 mm² (20 AWG), soldered from the back
FOOTPRINT_JUMPER = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"


def lookup(name):
    lcsc, footprint, _source, _note = PARTS[name]
    return lcsc, footprint


def check_list():
    """Lines for the build sheet: every part whose LCSC number is not from the reference project."""
    rows = [(n, l or "CHECK", s) for n, (l, f, s, _) in PARTS.items() if s != "reference"]
    rows += [(f"resistor {v}", l or "CHECK", "reference" if l else "CHECK") for v, l in RESISTOR_0603.items()]
    rows += [(f"capacitor {v}", l or "CHECK", "reference" if l else "CHECK") for v, (l, f) in CAPACITOR.items()]
    return rows
