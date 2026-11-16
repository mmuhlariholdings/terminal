FeatureScript 3112;
import(path : "onshape/std/common.fs", version : "3112.0");

/*
 * Terminal 1: enclosure and internal stack, as one Onshape custom feature.
 *
 * Source of every number: system/plan/interfaces.md (v0.2). Change a number there first, then here.
 * Device frame: millimetres; origin at the centre of the bottom (USB-C) edge on the back face;
 * X across the width, Y up the device, Z through the thickness (+Z towards the screen and keys).
 *
 * This file is the source of truth for the Onshape model. It lives in the repository at
 * hardware/enclosure/terminal-1.fs and in the Onshape Feature Studio "Terminal 1 FS".
 * Edit it there, verify with a real regeneration, then paste it here.
 */

const T1_EXPLODE_BOUNDS = { (millimeter) : [0, 0, 100] } as LengthBoundSpec;

// ---------------------------------------------------------------- envelope (interfaces.md section 1)
const T1_W = 84;          // width
const T1_H = 150;         // height
const T1_T = 19;          // thickness
const T1_R_PLAN = 9;      // plan-view corner radius
const T1_WALL = 2;        // frame side wall
const T1_R_INNER = 7;     // inner corner radius (T1_R_PLAN - T1_WALL)
const T1_EDGE_ROUND = 1.2;      // front and back edge round on the frame

// ---------------------------------------------------------------- materials (CM4, screen, keyboard and cell densities are estimates)
const T1_ALUMINIUM = material("Aluminium 6061", 2.70 * gram / centimeter ^ 3);
const T1_CARBON = material("Carbon fibre / epoxy", 1.55 * gram / centimeter ^ 3);
const T1_FIBREGLASS = material("Fibreglass / epoxy", 1.85 * gram / centimeter ^ 3);
const T1_FR4 = material("FR-4 circuit board (populated, estimate)", 2.10 * gram / centimeter ^ 3);
const T1_LIPO = material("Lithium-polymer cell (estimate)", 2.10 * gram / centimeter ^ 3);
const T1_COVER_GLASS = material("Cover glass", 2.50 * gram / centimeter ^ 3);
const T1_DISPLAY = material("IPS display module (estimate)", 2.00 * gram / centimeter ^ 3);
const T1_KEYBOARD = material("Keyboard assembly (estimate)", 1.60 * gram / centimeter ^ 3);
const T1_MODULE = material("Compute module (estimate)", 3.00 * gram / centimeter ^ 3);
const T1_SILICONE = material("Thermal pad", 3.00 * gram / centimeter ^ 3);
const T1_STEEL = material("Stainless steel", 7.90 * gram / centimeter ^ 3);
const T1_NYLON = material("Nylon", 1.15 * gram / centimeter ^ 3);

// ---------------------------------------------------------------- colours
const T1_C_FRAME = color(0.11, 0.11, 0.12);
const T1_C_CARBON = color(0.05, 0.05, 0.06);
const T1_C_WINDOW = color(0.62, 0.64, 0.66);
const T1_C_GLASS = color(0.015, 0.015, 0.02);
const T1_C_SCREEN = color(0.04, 0.05, 0.06);
const T1_C_KEYS = color(0.08, 0.08, 0.09);
const T1_C_FRETS = color(0.74, 0.75, 0.77);
const T1_C_PCB = color(0.05, 0.28, 0.15);
const T1_C_CM4 = color(0.10, 0.42, 0.22);
const T1_C_CELL = color(0.72, 0.74, 0.78);
const T1_C_PAD = color(0.55, 0.66, 0.85);
const T1_C_CONNECTOR = color(0.90, 0.88, 0.80);
const T1_C_METAL = color(0.80, 0.81, 0.83);

/** Box from (x0, y0, z0) to (x1, y1, z1) mm, with its Z-parallel edges rounded: corners "all", "top" (high Y) or "bottom". */
function t1RoundedBox(context is Context, id is Id, x0, y0, z0, x1, y1, z1, r, corners is string)
{
    fCuboid(context, id + "box", { "corner1" : vector(x0, y0, z0) * millimeter, "corner2" : vector(x1, y1, z1) * millimeter });
    if (r > 0)
    {
        const yMid = (y0 + y1) / 2;
        var chosen = [];
        for (var edge in evaluateQuery(context, qParallelEdges(qCreatedBy(id + "box", EntityType.EDGE), Z_DIRECTION)))
        {
            const y = evLine(context, { "edge" : edge }).origin[1] / millimeter;
            if (corners == "all" || (corners == "top" && y > yMid) || (corners == "bottom" && y < yMid))
                chosen = append(chosen, edge);
        }
        opFillet(context, id + "fillet", { "entities" : qUnion(chosen), "radius" : r * millimeter });
    }
}

/** Plain box. */
function t1Box(context is Context, id is Id, x0, y0, z0, x1, y1, z1)
{
    fCuboid(context, id, { "corner1" : vector(x0, y0, z0) * millimeter, "corner2" : vector(x1, y1, z1) * millimeter });
}

/** Box with its edges parallel to the given axis rounded (USB-C opening, side button). */
function t1SlotBox(context is Context, id is Id, x0, y0, z0, x1, y1, z1, r, axis is Vector)
{
    t1Box(context, id + "box", x0, y0, z0, x1, y1, z1);
    opFillet(context, id + "fillet", { "entities" : qParallelEdges(qCreatedBy(id + "box", EntityType.EDGE), axis), "radius" : r * millimeter });
}

/** Vertical hole cutter (cylinder through z0..z1) at (x, y). */
function t1Hole(context is Context, id is Id, x, y, z0, z1, diameter)
{
    fCylinder(context, id, { "bottomCenter" : vector(x, y, z0) * millimeter, "topCenter" : vector(x, y, z1) * millimeter,
                "radius" : diameter / 2 * millimeter });
}

function t1Subtract(context is Context, id is Id, target is Query, tools is Query)
{
    opBoolean(context, id, { "tools" : tools, "targets" : target, "operationType" : BooleanOperationType.SUBTRACTION });
}

function t1Unite(context is Context, id is Id, bodies is Query)
{
    if (size(evaluateQuery(context, bodies)) > 1)
        opBoolean(context, id, { "tools" : bodies, "operationType" : BooleanOperationType.UNION });
}

/** Name, colour and material for a part; move it out along Z for the exploded view. Returns the part's mass. */
function t1FinishPart(context is Context, partId is Id, name is string, appearance is Color, mat is Material, layer is number,
    explode is ValueWithUnits)
{
    const bodies = qCreatedBy(partId, EntityType.BODY);
    setProperty(context, { "entities" : bodies, "propertyType" : PropertyType.NAME, "value" : name });
    setProperty(context, { "entities" : bodies, "propertyType" : PropertyType.APPEARANCE, "value" : appearance });
    setProperty(context, { "entities" : bodies, "propertyType" : PropertyType.MATERIAL, "value" : mat });
    const mass = evVolume(context, { "entities" : bodies }) * mat.density;
    if (explode > 0 * millimeter && layer != 0)
        opTransform(context, partId + "explode", { "bodies" : bodies, "transform" : transform(vector(0, 0, layer) * explode) });
    return mass;
}

// Onshape rule: every sub-operation of one part (id + "frame" + ...) must be contiguous, so each part's cutting tools are
// created BEFORE the part's own operations, under a sibling id (id + "frameCut" ...).

annotation { "Feature Type Name" : "Terminal 1",
        "Feature Type Description" : "Terminal 1 pocket Linux terminal: enclosure and internal stack (numbers from system/plan/interfaces.md)" }
export const terminal1 = defineFeature(function(context is Context, id is Id, definition is map)
    precondition
    {
        annotation { "Name" : "Exploded view spacing" }
        isLength(definition.explode, T1_EXPLODE_BOUNDS);

        annotation { "Name" : "Show internal parts" }
        definition.internals is boolean;
    }
    {
        const ex = definition.explode;
        var parts = {};
        var mass = 0 * gram;

        // ------------------------------------------------ mid-frame (aluminium): side band + internal plates, one part
        const frame = id + "frame";
        t1RoundedBox(context, id + "frameHole", -T1_W / 2 + T1_WALL, T1_WALL, -1, T1_W / 2 - T1_WALL, T1_H - T1_WALL, T1_T + 1, T1_R_INNER, "all");
        // openings: inter-board cable slot, USB-C port (bottom edge), power button (right side)
        t1Box(context, id + "frameCut" + "cable", -14, 64.5, 10, 14, 68.5, 13);
        t1SlotBox(context, id + "frameCut" + "usb", -4.7, -1, 13.5, 4.7, 3, 16.9, 1.6, Y_DIRECTION);
        t1SlotBox(context, id + "frameCut" + "button", T1_W / 2 - 3, 46, 13.6, T1_W / 2 + 1, 54, 16.8, 1.2, X_DIRECTION);
        t1RoundedBox(context, frame + "outer", -T1_W / 2, 0, 0, T1_W / 2, T1_H, T1_T, T1_R_PLAN, "all");
        const outerEdges = qCreatedBy(frame + "outer", EntityType.EDGE);
        opFillet(context, frame + "edges", { "radius" : T1_EDGE_ROUND * millimeter, "entities" : qUnion([
                            qCoincidesWithPlane(outerEdges, plane(vector(0, 0, 0) * millimeter, Z_DIRECTION)),
                            qCoincidesWithPlane(outerEdges, plane(vector(0, 0, T1_T) * millimeter, Z_DIRECTION))]) });
        t1Subtract(context, frame + "hollow", qCreatedBy(frame + "outer", EntityType.BODY), qCreatedBy(id + "frameHole", EntityType.BODY));
        // plate behind the screen (thermal path from the CM4) and plate in front of the battery
        t1RoundedBox(context, frame + "plateScreen", -T1_W / 2 + T1_WALL, 70, 14.2, T1_W / 2 - T1_WALL, T1_H - T1_WALL, 15.4, T1_R_INNER, "top");
        t1RoundedBox(context, frame + "plateKeyboard", -T1_W / 2 + T1_WALL, T1_WALL, 11.2, T1_W / 2 - T1_WALL, 70, 12.4, T1_R_INNER, "bottom");
        t1Box(context, frame + "step", -T1_W / 2 + T1_WALL, 69, 11.2, T1_W / 2 - T1_WALL, 70, 15.4);
        t1Unite(context, frame + "join", qCreatedBy(frame, EntityType.BODY));
        t1Subtract(context, frame + "openings", qCreatedBy(frame, EntityType.BODY), qCreatedBy(id + "frameCut", EntityType.BODY));
        mass += t1FinishPart(context, frame, "Mid-frame", T1_C_FRAME, T1_ALUMINIUM, 0, ex);
        parts["Mid-frame"] = qCreatedBy(frame, EntityType.BODY);

        // ------------------------------------------------ carbon back with the fibreglass radio window at the top
        const back = id + "back";
        t1Box(context, id + "backCut", -T1_W / 2, 134, -1, T1_W / 2, T1_H, 2);
        t1RoundedBox(context, back + "panel", -T1_W / 2 + T1_WALL, T1_WALL, 0, T1_W / 2 - T1_WALL, T1_H - T1_WALL, 1.2, T1_R_INNER, "all");
        t1Subtract(context, back + "window", qCreatedBy(back, EntityType.BODY), qCreatedBy(id + "backCut", EntityType.BODY));
        mass += t1FinishPart(context, back, "Carbon back", T1_C_CARBON, T1_CARBON, -4, ex);
        parts["Carbon back"] = qCreatedBy(back, EntityType.BODY);

        const window = id + "radioWindow";
        t1RoundedBox(context, window, -T1_W / 2 + T1_WALL, 134, 0, T1_W / 2 - T1_WALL, T1_H - T1_WALL, 1.2, T1_R_INNER, "top");
        mass += t1FinishPart(context, window, "Radio window", T1_C_WINDOW, T1_FIBREGLASS, -4, ex);
        parts["Radio window"] = qCreatedBy(window, EntityType.BODY);

        if (definition.internals)
        {
            // ------------------------------------------------ battery: 855570 LiPo, behind the keyboard
            const cell = id + "battery";
            t1RoundedBox(context, cell, -35, 6, 2.2, 35, 61, 10.7, 1.5, "all");
            mass += t1FinishPart(context, cell, "Battery 855570", T1_C_CELL, T1_LIPO, -3, ex);
            parts["Battery"] = qCreatedBy(cell, EntityType.BODY);

            // ------------------------------------------------ carrier board (4 layers), CM4 on its front side
            const carrier = id + "carrier";
            t1Hole(context, id + "carrierHole" + "a", -33.5, 77.5, 6, 9.5, 2.2);
            t1Hole(context, id + "carrierHole" + "b", 33.5, 77.5, 6, 9.5, 2.2);
            t1Hole(context, id + "carrierHole" + "c", -33.5, 142.5, 6, 9.5, 2.2);
            t1Hole(context, id + "carrierHole" + "d", 33.5, 142.5, 6, 9.5, 2.2);
            t1RoundedBox(context, carrier + "board", -37, 74, 6.9, 37, 146, 8.5, 1, "all");
            t1Subtract(context, carrier + "holes", qCreatedBy(carrier, EntityType.BODY), qCreatedBy(id + "carrierHole", EntityType.BODY));
            mass += t1FinishPart(context, carrier, "Carrier board", T1_C_PCB, T1_FR4, -2, ex);
            parts["Carrier board"] = qCreatedBy(carrier, EntityType.BODY);

            // board-to-board connectors (positions approximate until the carrier layout fixes them)
            const b2b = id + "boardToBoard";
            t1Box(context, b2b + "a", -11, 96, 8.5, 11, 100.5, 10.0);
            t1Box(context, b2b + "b", -11, 123.5, 8.5, 11, 128, 10.0);
            mass += t1FinishPart(context, b2b, "CM4 connectors (DF40)", T1_C_CONNECTOR, T1_NYLON, -2, ex);
            parts["CM4 connectors"] = qCreatedBy(b2b, EntityType.BODY);

            const cm4 = id + "cm4";
            t1RoundedBox(context, cm4 + "board", -27.5, 92, 10.0, 27.5, 132, 11.2, 1, "all");
            t1RoundedBox(context, cm4 + "parts", -12, 100, 11.2, 12, 124, 13.2, 1, "all");
            t1Unite(context, cm4 + "join", qCreatedBy(cm4, EntityType.BODY));
            mass += t1FinishPart(context, cm4, "Raspberry Pi CM4", T1_C_CM4, T1_MODULE, -1, ex);
            parts["CM4"] = qCreatedBy(cm4, EntityType.BODY);

            const pad = id + "thermalPad";
            t1Box(context, pad, -12, 100, 13.2, 12, 124, 14.2);
            mass += t1FinishPart(context, pad, "Thermal pad", T1_C_PAD, T1_SILICONE, -0.5, ex);
            parts["Thermal pad"] = qCreatedBy(pad, EntityType.BODY);

            // ------------------------------------------------ keyboard board (2 layers), USB-C at its bottom edge
            const kb = id + "keyboardBoard";
            t1Hole(context, id + "keyboardHole" + "a", -33.5, 7.5, 14, 16.5, 2.2);
            t1Hole(context, id + "keyboardHole" + "b", 33.5, 7.5, 14, 16.5, 2.2);
            t1Hole(context, id + "keyboardHole" + "c", -33.5, 60.5, 14, 16.5, 2.2);
            t1Hole(context, id + "keyboardHole" + "d", 33.5, 60.5, 14, 16.5, 2.2);
            t1Box(context, id + "keyboardHole" + "usb", -4.6, 3, 14, 4.6, 8.6, 16.5);   // slot for the mid-mount USB-C socket
            t1RoundedBox(context, kb + "board", -37, 4, 14.4, 37, 64, 16.0, 1, "all");
            t1Subtract(context, kb + "holes", qCreatedBy(kb, EntityType.BODY), qCreatedBy(id + "keyboardHole", EntityType.BODY));
            mass += t1FinishPart(context, kb, "Keyboard board", T1_C_PCB, T1_FR4, 1, ex);
            parts["Keyboard board"] = qCreatedBy(kb, EntityType.BODY);

            const usb = id + "usbC";
            t1SlotBox(context, usb, -4.47, 0.8, 13.6, 4.47, 7.8, 16.8, 1.5, Y_DIRECTION);   // mid-mount socket, clear of the keyboard base (Y 8)
            mass += t1FinishPart(context, usb, "USB-C socket", T1_C_METAL, T1_STEEL, 1, ex);
            parts["USB-C socket"] = qCreatedBy(usb, EntityType.BODY);
        }

        // ------------------------------------------------ power button (right side)
        const button = id + "powerButton";
        t1SlotBox(context, button, T1_W / 2 - 2.6, 46.5, 14.0, T1_W / 2 + 0.6, 53.5, 16.4, 1.0, X_DIRECTION);
        mass += t1FinishPart(context, button, "Power button", T1_C_FRAME, T1_ALUMINIUM, 0, ex);
        parts["Power button"] = qCreatedBy(button, EntityType.BODY);

        // ------------------------------------------------ screen module and cover glass
        const screen = id + "screen";
        t1Box(context, screen, -38, 64.4, 15.7, 38, 145, 18.3);
        mass += t1FinishPart(context, screen, "Display 4-inch 720x720", T1_C_SCREEN, T1_DISPLAY, 2, ex);
        parts["Display"] = qCreatedBy(screen, EntityType.BODY);

        const glass = id + "coverGlass";
        t1RoundedBox(context, glass, -T1_W / 2 + T1_WALL, 63, 18.3, T1_W / 2 - T1_WALL, T1_H - T1_WALL, T1_T, T1_R_INNER, "top");
        mass += t1FinishPart(context, glass, "Cover glass", T1_C_GLASS, T1_COVER_GLASS, 3, ex);
        parts["Cover glass"] = qCreatedBy(glass, EntityType.BODY);

        // ------------------------------------------------ keyboard deck: front plate around the keyboard and the navigation row
        const deck = id + "deck";
        t1RoundedBox(context, id + "deckCut" + "keys", -33.3, 7.7, 17, 33.3, 44.3, T1_T + 1, 1.8, "all");
        t1RoundedBox(context, id + "deckCut" + "nav", -33.3, 46.7, 17, 33.3, 60.3, T1_T + 1, 1.8, "all");
        t1RoundedBox(context, deck + "plate", -T1_W / 2 + T1_WALL, T1_WALL, 17.4, T1_W / 2 - T1_WALL, 63, T1_T, T1_R_INNER, "bottom");
        t1Subtract(context, deck + "openings", qCreatedBy(deck, EntityType.BODY), qCreatedBy(id + "deckCut", EntityType.BODY));
        mass += t1FinishPart(context, deck, "Keyboard deck", T1_C_FRAME, T1_ALUMINIUM, 3, ex);
        parts["Keyboard deck"] = qCreatedBy(deck, EntityType.BODY);

        // ------------------------------------------------ BlackBerry Q20 keyboard: 4 rows on a base, keys stand 1.0 proud of the front
        const keyboard = id + "keyboard";
        t1RoundedBox(context, keyboard + "base", -33, 8, 16.0, 33, 44, 18.8, 1.5, "all");
        const pitch = 6.5;
        for (var row = 0; row < 4; row += 1)
        {
            const yc = 12.5 + 9 * row;
            for (var slot = 0; slot < 10; slot += 1)
            {
                if (row == 0 && (slot == 0 || slot == 9 || (slot > 3 && slot < 7)))
                    continue;                                   // bottom row: 2 keys, space bar, 2 keys
                var x0 = -29.25 + pitch * slot - 2.95;
                var x1 = -29.25 + pitch * slot + 2.95;
                if (row == 0 && slot == 3)
                    x1 = -29.25 + pitch * 6 + 2.95;             // space bar spans slots 3 to 6
                t1RoundedBox(context, keyboard + ("key" ~ row ~ "_" ~ slot), x0, yc - 3.7, 18.8, x1, yc + 3.7, 20.0, 1.2, "all");
            }
        }
        t1Unite(context, keyboard + "join", qCreatedBy(keyboard, EntityType.BODY));
        mass += t1FinishPart(context, keyboard, "Keyboard (Q20)", T1_C_KEYS, T1_KEYBOARD, 2, ex);
        parts["Keyboard"] = qCreatedBy(keyboard, EntityType.BODY);

        const frets = id + "frets";
        for (var f = 1; f < 4; f += 1)
            t1Box(context, frets + ("fret" ~ f), -32.5, 8 + 9 * f - 0.45, 18.8, 32.5, 8 + 9 * f + 0.45, 19.25);
        mass += t1FinishPart(context, frets, "Keyboard frets", T1_C_FRETS, T1_STEEL, 2, ex);
        parts["Keyboard frets"] = qCreatedBy(frets, EntityType.BODY);

        // navigation row: Ctrl, Esc | trackpad | Tab, Fn
        const nav = id + "navigation";
        t1RoundedBox(context, nav + "base", -33, 47, 16.0, 33, 60, 18.8, 1.5, "all");
        const navKeys = [-26.5, -14.5, 14.5, 26.5];
        for (var k = 0; k < size(navKeys); k += 1)
            t1RoundedBox(context, nav + ("key" ~ k), navKeys[k] - 5.2, 50, 18.8, navKeys[k] + 5.2, 57, 20.0, 1.5, "all");
        t1Unite(context, nav + "join", qCreatedBy(nav, EntityType.BODY));
        mass += t1FinishPart(context, nav, "Navigation keys", T1_C_KEYS, T1_KEYBOARD, 2, ex);
        parts["Navigation keys"] = qCreatedBy(nav, EntityType.BODY);

        const pad2 = id + "trackpad";
        t1RoundedBox(context, pad2, -5, 49.5, 18.8, 5, 57.5, 19.8, 2.0, "all");
        mass += t1FinishPart(context, pad2, "Trackpad", T1_C_FRETS, T1_STEEL, 2, ex);
        parts["Trackpad"] = qCreatedBy(pad2, EntityType.BODY);

        setVariable(context, "terminal1Parts", parts);
        setVariable(context, "terminal1Mass", mass);
        reportFeatureInfo(context, id, "Terminal 1: " ~ size(keys(parts)) ~ " parts, estimated mass " ~
                    roundToPrecision(mass / gram, 0) ~ " g (densities are estimates; weigh the real parts)");
    }, { "explode" : 0 * millimeter, "internals" : true });
