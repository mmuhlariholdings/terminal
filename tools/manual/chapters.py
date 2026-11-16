"""Per-chapter settings for the technical manual (tools/build_manual.py).

Everything else in a chapter is read from the project files; these settings only say WHERE to find it (build-sheet
section titles, plan headings, KiCad paths) and give the few things that exist nowhere else: the key facts shown
"at a glance" and the assembly steps (title, text, and a regex of the 3D model's part names fitted in that step).
Part names are the Onshape part names in the glTF export (see each Feature Studio).
"""
from docparse import REFLECTOR as _R

ONSHAPE = "Onshape document ed20c67d61df76134a585060"

LIGHT_HEAD = {
    "key": "light-head", "title": "Light head", "qty": 2,
    "lead": "A 600 × 600 mm square of high-brightness LEDs that glows green, orange or red, built as one welded steel unit with "
            "handles, feet and visor, battery-powered. One stands beside each lane, off the track.",
    "facts": [("Per kit", "2 (one beside each lane)"), ("Size", "824 × 500 × 1,111 mm (1,011 without antenna)"),
              ("LED face", "600 × 600 mm, green / orange / red"), ("Mass", "~38 kg carried, ~71 kg with 4 ballast plates (estimate)"),
              ("Frame", "25 × 25 × 1.6 mild steel, welded, powder-coated"), ("Battery", "12 V 30 Ah LiFePO4"),
              ("Controller", "ESP32-S3 module on a JLCPCB-assembled board (Rev C)")],
    "model": "hardware/light-head/light-head.glb", "view": {"yaw": 0.6, "pitch": 0.2, "zoom": 1.0},
    "sheet": "hardware/light-head/build-sheet.md",
    "spec_sections": ["1. Conventions", "3. Overall envelope", "4. Parts list with positions", "5. Materials",
                      "5a. Wind and ballast basis", "5b. Heat and battery", "6. Mass summary"],
    "steps": [
        ("Weld and finish the frame",
         "Cut and weld the cage, feet, gussets, ballast tray, equipment shelf and visor to the welder pack. Check the cage is "
         "700 × 700 × 180 outside with equal diagonals, grind the front and rear faces flat, powder-coat matte black, then fit the "
         "rivnuts (28 × M5 in the front face, 8 × M8 in the mid-side posts).",
         "Cage|Foot|Gussets|Ballast tray|Equipment shelf|Visor"),
        ("Panels and handles",
         "Rivet the top and bottom panels onto their rails with sealant, fit the two side panels, then bolt each handle's foot "
         "plates through the side panel into the M8 rivnuts.", "Top panel|Bottom panel|Side panel|Handle"),
        ("LED face",
         "Mount the LED plate on its four steel tabs. Lay the front gasket on the cage face, then the polycarbonate cover, and clamp "
         "it with the cover clamp frame screwed into the M5 rivnuts.",
         "LED plate|LED mount tab|Front gasket|Polycarbonate cover|Cover clamp frame"),
        ("Equipment inside",
         "Strap the 30 Ah battery to the shelf and screw down the electronics box. Fit the charge port, power switch, cable gland, "
         "breather vents and the antenna bulkhead in the top panel, then wire up (see Wiring).",
         "Battery|Electronics|Charge port|Power switch|Cable gland|Breather vent|Antenna bulkhead"),
        ("Back door",
         "Hang the back door on its two hinges (match-drill and rivet the leaves), fit the rear gasket and the two quarter-turn latches.",
         "Back cover|Rear gasket|Door hinge|Door latch"),
        ("On site: ballast and antenna",
         "Stand the head on its four rubber pads beside the lane, slide the four 12 mm ballast plates into the tray (always, on site), "
         "and screw the antenna onto its bulkhead.", "Ballast plate|Pads|Antenna \\("),
    ],
    "assembly_note": "4.14 Fabrication files",
    "block_diagram": ("Electrical schematics", "Light head"),
    "elec_section": "Circuit schematic",
    "schematics": [("Controller and LED driver board", "hardware/light-head/electronics/light-head")],
    "boards_section": "Circuit board (PCB)",
    "boards": [("Controller board, 120 × 80 mm", "hardware/light-head/electronics/renders/light-head")],
    "harness": "hardware/light-head/electronics/harness.md",
    "netlists": [("Controller board", "hardware/light-head/electronics/netlist.md")],
    "bom_heading": "Light head (build 2)", "bom_total_label": "Per head",
    "open_section": "8. Open items",
    "sprint_keywords": r"light head|LED tile|IRLB8721|MOSFET|30 Ah|welder|ballast plate",
    "files": [
        ("Spec", "hardware/light-head/build-sheet.md", "Build sheet (design spec)"),
        ("PDF", "hardware/light-head/fabrication/light-head-welder-pack.pdf", "Welder pack: A3, 5 sheets (cut lists, views, details)"),
        ("DXF", "hardware/light-head/fabrication/dxf", "Cutting files for every flat part (18)"),
        ("Table", "hardware/light-head/fabrication/flat-parts-list.md", "Flat parts list"),
        ("3D", "hardware/light-head/light-head.glb", "Onshape export (glTF): the model in this chapter"),
        ("CAD", None, f"{ONSHAPE}: Feature Studio “Light Head v1 FS”, feature “Light Head”"),
        ("PDF", "hardware/light-head/electronics/light-head.pdf", "Circuit schematic, printable A3"),
        ("PCB", "hardware/light-head/electronics/light-head.kicad_pcb", "Controller board layout (KiCad)"),
        ("Gerber", "hardware/light-head/electronics/fabrication/light-head-gerbers.zip", "Controller board: files for the board house (order 2 oz copper)"),
        ("Table", "hardware/light-head/electronics/harness.md", "Wiring harness"),
    ],
}

CENTRE_POD = {
    "key": "centre-pod", "title": "Centre pod", "qty": 1,
    "lead": "The only unit on the track: a low, light, soft pod on the centre line that holds both beam sensors and the one clock "
            "that decides the winner. Non-metal and never anchored, so a car that hits it isn't hurt by it.",
    "facts": [("Per kit", "1, on the centre line"), ("Size", "300 × 220 × 260 mm"), ("Mass", "4 kg incl. about 0.65 kg sand"),
              ("Beam sensors", "2 × Sick W16 polarised, beam 180 mm up"), ("Controller", "ESP32-S3 module, DS3231 clock, microSD log (Rev C board)"),
              ("Battery", "12 V 6 Ah LiFePO4")],
    "model": "hardware/centre-pod/centre-pod.glb", "view": {"yaw": 0.75, "pitch": 0.3, "zoom": 0.62},
    "sheet": "hardware/centre-pod/build-sheet.md",
    "spec_sections": ["1. Conventions", "2. Requirements", "4. Parts", "5. Beam sensor"],
    "steps": [
        ("Mould the shell and wrap it",
         "Lay up the shell in the pod mould taken off the printed plug (section 4c), trim it 252 mm from its outer bottom, bond the "
         "15 mm hi-vis foam wrap round the four sides and fit the rubber base mat.", "Shell|Foam wrap|Base mat"),
        ("Windows and sensor cradles",
         "Cut the Ø40 opening on the beam axis (180 mm up) in each end wall, bond a Ø50 polycarbonate disc inside each, then bond "
         "the printed sensor cradles with their ribs to the end walls.", "Sensor window|Sensor cradle"),
        ("Beam sensors",
         "Seat a W16 sensor on each cradle with its lens 5 mm behind the window, and run the M12 cordsets to the board position.",
         "Beam sensor"),
        ("Battery, clamp deck and board",
         "Bond the four clamp posts to the floor, drop in the 6 Ah battery, screw the deck down over it and mount the 150 × 80 "
         "board on the deck's standoffs. Connect the sensors, lid and buzzer leads (see Wiring).",
         "Battery|Electronics board"),
        ("Lid",
         "Bond the lid ledge inside the rim and lay the EPDM seal on it. Fit the lid items (alignment LEDs, switch, charge port "
         "under its flap, antenna bulkhead) and close the lid with the two quarter-turn fasteners.",
         "Lid|Top panel|Alignment LED|Antenna|Power switch|Charge port"),
        ("Ballast to 4 kg",
         "Put the pod on a scale and fill the two sand pouches in the end bays until it weighs 4.0 kg (about 0.33 kg per pouch).",
         "Sand ballast"),
    ],
    "block_diagram": ("Electrical schematics", "Centre pod"),
    "elec_section": "5a. Circuit schematic",
    "schematics": [("Main board", "hardware/centre-pod/electronics/centre-pod")],
    "boards_section": "5b. Circuit board",
    "boards": [("Main board, 150 × 80 mm", "hardware/centre-pod/electronics/renders/centre-pod")],
    "harness": "hardware/centre-pod/electronics/harness.md",
    "netlists": [("Main board", "hardware/centre-pod/electronics/netlist.md")],
    "bom_heading": "Centre pod (build 1)", "bom_total_label": "Centre pod total",
    "open_section": "6. Open items",
    "sprint_keywords": r"centre pod|W16|DS3231|microSD|6N137|ESP32-S3|plug",
    "files": [
        ("Spec", "hardware/centre-pod/build-sheet.md", "Build sheet (design spec, incl. the mould plug)"),
        ("STL", "hardware/centre-pod/fabrication/pod-shell-plug.stl", "Mould plug for 3D printing (shared with the reflector pods)"),
        ("3D", "hardware/centre-pod/centre-pod.glb", "Onshape export (glTF): the model in this chapter"),
        ("CAD", None, f"{ONSHAPE}: Feature Studio “Centre Pod v1 FS”, features “Centre Pod” and “Centre Pod Plug”"),
        ("PDF", "hardware/centre-pod/electronics/centre-pod.pdf", "Circuit schematic, printable A3"),
        ("PCB", "hardware/centre-pod/electronics/centre-pod.kicad_pcb", "Main board layout (KiCad)"),
        ("Gerber", "hardware/centre-pod/electronics/fabrication/centre-pod-gerbers.zip", "Main board: files for the board house"),
        ("Table", "hardware/centre-pod/electronics/harness.md", "Wiring harness"),
        ("PDF", "hardware/flight-cases/fabrication/flight-case-brief.pdf", "Flight case brief (the pod travels in case C)"),
    ],
}

REFLECTOR_POD = dict(_R)
REFLECTOR_POD.update({
    "model": "hardware/reflector-pod/reflector-pod.glb", "view": {"yaw": 0.75, "pitch": 0.3, "zoom": 0.62}, "rename": {},
    "spec_sections": ["2. Requirements", "4. Parts", "5. Design decisions"],
    "assembly_note": "6. Build notes",
    "block_diagram": ("Electrical schematics", "Reflector pods"),
    "schematics": [("Main board", "hardware/reflector-pod/electronics/reflector-pod"),
                   ("Alignment ring board", "hardware/reflector-pod/electronics/ring/reflector-ring")],
    "boards_section": "6b. Circuit boards",
    "boards": [("Main board, 100 × 70 mm", "hardware/reflector-pod/electronics/renders/reflector-pod"),
               ("Alignment ring board, 124 × 124 mm", "hardware/reflector-pod/electronics/ring/renders/reflector-ring")],
    "netlists": [("Main board", "hardware/reflector-pod/electronics/netlist.md"), ("Alignment ring board", "hardware/reflector-pod/electronics/ring/netlist.md")],
    "files": [f for f in _R["files"] if f[0] != "3D"] + [
        ("3D", "hardware/reflector-pod/reflector-pod.glb", "Onshape export (glTF): the model in this chapter"),
        ("PCB", "hardware/reflector-pod/electronics/reflector-pod.kicad_pcb", "Main board layout (KiCad)"),
        ("Gerber", "hardware/reflector-pod/electronics/fabrication/reflector-pod-gerbers.zip", "Main board: files for the board house"),
        ("PCB", "hardware/reflector-pod/electronics/ring/reflector-ring.kicad_pcb", "Alignment ring board layout (KiCad)"),
        ("Gerber", "hardware/reflector-pod/electronics/ring/fabrication/reflector-ring-gerbers.zip", "Ring board: files for the board house"),
    ],
})

REMOTE = {
    "key": "remote", "title": "Handheld remote", "qty": 1,
    "lead": "Optional, because the system arms itself. Hold pauses the system (both lights red), Reset clears a result early, "
            "and the display shows the last winning gap in milliseconds and the battery levels.",
    "facts": [("Per kit", "1 (optional)"), ("Size", "70 × 185 × 40 mm"), ("Mass", "about 210 g as printed (estimate)"),
              ("Buttons", "Red Hold/Resume; black Reset behind a guard ring"), ("Display", "0.96 in OLED, 128 × 64"),
              ("Controller", "ESP32-S3-MINI on a 56 × 36 carrier board with its charger (Rev C)"), ("Battery", "1 × 18650, USB-C charging")],
    "model": "hardware/remote/remote.glb", "view": {"yaw": 0.5, "pitch": 0.75, "zoom": 0.95},
    "sheet": "hardware/remote/build-sheet.md",
    "spec_sections": ["1. Conventions", "2. Requirements", "4. Layout and parts", "5. Design decisions"],
    "steps": [
        ("Print the case",
         "Print the front shell face down and the back cover flat in ASA (0.2 mm layers, 4 walls, 30% infill), then fit M3 heat-set "
         "inserts in the four bosses.", "Front shell|Back cover"),
        ("Buttons and display",
         "Fit the two 22 mm buttons (black Reset inside the guard ring), bond the acrylic window inside the display opening and "
         "mount the OLED behind it.", "button|Display window|OLED"),
        ("Carrier board",
         "Screw the assembled carrier board (from JLCPCB, Rev C: controller, charger and USB-C on it) onto its four nylon "
         "standoffs above the battery holder.", "Carrier|XIAO"),
        ("Power",
         "Fit the 18650 holder on the back cover, check the board's USB-C port lines up with the opening at the bottom end, fit the slide switch in "
         "the right wall. Solder the leads to the carrier's pads (see Wiring).", "18650|charger|Slide switch"),
        ("Antenna and close",
         "Stick the FPC antenna inside the top end, plug it into the controller module's U.FL socket, lay the gasket and screw the back cover on.",
         "antenna|Case gasket"),
    ],
    "assembly_note": "6. Printing and export",
    "block_diagram": ("Electrical schematics", "Handheld remote"),
    "elec_section": "6a. Circuit schematic",
    "schematics": [("Carrier board", "hardware/remote/electronics/remote")],
    "boards_section": "6b. Circuit board",
    "boards": [("Carrier board, 56 × 36 mm", "hardware/remote/electronics/renders/remote")],
    "harness": "hardware/remote/electronics/harness.md",
    "netlists": [("Carrier board", "hardware/remote/electronics/netlist.md")],
    "bom_heading": "Handheld remote (build 1)", "bom_total_label": "Remote total",
    "open_section": "7. Open items",
    "sprint_keywords": r"remote|OLED|18650",
    "files": [
        ("Spec", "hardware/remote/build-sheet.md", "Build sheet (design spec)"),
        ("3D", "hardware/remote/remote.glb", "Onshape export (glTF): the model in this chapter"),
        ("CAD", None, f"{ONSHAPE}: Feature Studio “Remote v1 FS”, feature “Remote”"),
        ("STL", "hardware/remote/fabrication/remote-front-shell.stl", "Front shell for printing (export from Onshape, section 6)"),
        ("STL", "hardware/remote/fabrication/remote-back-cover.stl", "Back cover for printing (export from Onshape, section 6)"),
        ("PDF", "hardware/remote/electronics/remote.pdf", "Circuit schematic, printable A3"),
        ("PCB", "hardware/remote/electronics/remote.kicad_pcb", "Carrier board layout (KiCad)"),
        ("Gerber", "hardware/remote/electronics/fabrication/remote-gerbers.zip", "Carrier board: files for the board house"),
        ("Table", "hardware/remote/electronics/harness.md", "Wiring harness"),
    ],
}

FLIGHT_CASES = {
    "key": "flight-cases", "title": "Flight cases", "qty": 3,
    "lead": "The kit travels in three foam-lined cases on castors (one per light head, one for the pods, remote and "
            "accessories) plus two ballast crates for the steel plates.",
    "facts": [("Cases A and B", "One light head each, 880 × 560 × 1,060 mm inside"), ("Case C", "Pods, remote, accessories, 780 × 570 × 320 mm inside"),
              ("Ballast crates", "2, 310 × 300 × 60 mm inside, 4 plates each"), ("Made by", "Local flight-case maker, to the case brief")],
    "sheet": "hardware/flight-cases/build-sheet.md",
    "spec_sections": ["1. Sizes the cases must hold", "2. Cases A and B", "3. Case C", "4. Ballast plates"],
    "open_section": "5. Open items",
    "sprint_keywords": r"flight case|case maker|ballast crate",
    "files": [
        ("Spec", "hardware/flight-cases/build-sheet.md", "Build sheet (case sizes and fittings)"),
        ("PDF", "hardware/flight-cases/fabrication/flight-case-brief.pdf", "Case maker's brief, 2 sheets: send this for quotes"),
    ],
}

CHAPTERS = [LIGHT_HEAD, CENTRE_POD, REFLECTOR_POD, REMOTE, FLIGHT_CASES]

# Kit-wide chapter: plan sections printed whole, in this order (heading in the plan, title in the manual)
KIT_WIDE = [
    ("Kit-wide", "Kit-wide parts and kit cost"),
    ("Acceptance tests and safety", "Acceptance tests"),
    ("Safety rules", "Safety rules"),
    ("8-week build plan", "Build plan"),
    ("Work packages", "Work packages"),
    ("Risk log", "Risk log"),
    ("Open decisions", "Open decisions"),
]

# Service chapters, printed after the unit chapters: Markdown sources in docs/manual/ (tokens explained in build_manual.py)
SERVICE = ["docs/manual/bring-up.md", "docs/manual/end-of-line-test.md", "docs/manual/troubleshooting.md"]
