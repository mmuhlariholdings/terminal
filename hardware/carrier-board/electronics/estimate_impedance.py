#!/usr/bin/env python3
"""Rough differential-impedance estimate for the carrier board's outer-layer pairs (edge-coupled microstrip over the In1 plane).

Run:  python3 estimate_impedance.py
Prints a markdown table, copied into circuit-notes.md.

Stack-up: JLCPCB JLC04161H-7628 (1.6 mm, 4 layers): outer copper 35 um (1 oz finished), 7628 prepreg 0.2104 mm to the inner
plane, relative permittivity 4.4 (JLCPCB's figure for 7628). Formulas: IPC-2141 microstrip
    Z0 = 87 / sqrt(er + 1.41) * ln(5.98 H / (0.8 W + T))
and the usual edge-coupled correction
    Zdiff = 2 Z0 (1 - 0.48 exp(-0.96 S / H)).
Solder mask over the tracks lowers the result by roughly 2-5 %; 3.5 % is assumed below.
These formulas are good to about +/-10 %. THIS IS AN ESTIMATE: confirm the width and gap with JLCPCB's impedance calculator
(jlcpcb.com/pcb-impedance-calculator, stack-up JLC04161H-7628) before ordering, and order with impedance control.
"""
import math

H, T, ER = 0.2104, 0.035, 4.4
MASK = 0.965


def z_single(w):
    return 87.0 / math.sqrt(ER + 1.41) * math.log(5.98 * H / (0.8 * w + T))


def z_diff(w, s):
    return 2.0 * z_single(w) * (1.0 - 0.48 * math.exp(-0.96 * s / H))


CHOICES = [("DSI1 (target 100 ohm)", 0.20, 0.18), ("USB 2.0 (target 90 ohm)", 0.25, 0.18)]

if __name__ == "__main__":
    print("| Pair | Width (mm) | Gap (mm) | Single-ended Z0, bare (ohm) | Zdiff bare (ohm) | Zdiff with mask, est. (ohm) |")
    print("|---|---|---|---|---|---|")
    for name, w, s in CHOICES:
        print(f"| {name} | {w:.2f} | {s:.2f} | {z_single(w):.1f} | {z_diff(w, s):.1f} | {z_diff(w, s) * MASK:.1f} |")
    print()
    print("Sensitivity (bare, gap 0.18 mm): " + ", ".join(f"W {w:.2f} -> {z_diff(w, 0.18):.0f}" for w in (0.18, 0.20, 0.22, 0.25, 0.28)))
