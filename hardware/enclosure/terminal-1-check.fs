/*
 * Terminal 1 Check: a test feature for hardware/enclosure/terminal-1.fs.
 *
 * How to use: paste this ABOVE the "Terminal 1" feature in a scratch Feature Studio (or send both to the Onshape MCP
 * test_feature tool with this feature first in the file). It builds the model and reports, as an error message:
 * body count, estimated mass, bounding box, and every pair of parts that interfere.
 * Last run 2026-11-16: mass 290.9 g, 1 clash (USB-C socket / keyboard, 0.5 mm). The socket was then shortened to end at
 * Y 7.8 (keyboard base starts at Y 8); the full model regenerated cleanly, but this check has not been re-run since.
 * Note: "type" is a reserved word in FeatureScript, so clash results are read as c["type"], not c.type.
 */

function t1Vec(v) { return "(" ~ roundToPrecision(v[0] / millimeter, 2) ~ "," ~ roundToPrecision(v[1] / millimeter, 2) ~ "," ~ roundToPrecision(v[2] / millimeter, 2) ~ ")"; }

annotation { "Feature Type Name" : "Terminal 1 Check" }
export const terminal1Check = defineFeature(function(context is Context, id is Id, definition is map)
    precondition {}
    {
        terminal1(context, id + "t1", { "explode" : 0 * millimeter, "internals" : true });
        const parts = getVariable(context, "terminal1Parts");
        const names = keys(parts);
        var clashes = "";
        var count = 0;
        for (var i = 0; i < size(names); i += 1)
            for (var j = i + 1; j < size(names); j += 1)
            {
                const found = evCollision(context, { "tools" : parts[names[i]], "targets" : parts[names[j]] });
                for (var c in found)
                    if (c["type"] == ClashType.INTERFERE || c["type"] == ClashType.TARGET_IN_TOOL || c["type"] == ClashType.TOOL_IN_TARGET)
                    {
                        clashes = clashes ~ names[i] ~ "/" ~ names[j] ~ "; ";
                        count += 1;
                        break;
                    }
            }
        const bb = evBox3d(context, { "topology" : qEverything(EntityType.BODY), "tight" : true });
        throw regenError("bodies " ~ size(evaluateQuery(context, qEverything(EntityType.BODY))) ~ " mass " ~
                    roundToPrecision(getVariable(context, "terminal1Mass") / gram, 1) ~ "g box " ~ t1Vec(bb.minCorner) ~
                    t1Vec(bb.maxCorner) ~ " clashes " ~ count ~ ": " ~ clashes);
    }, {});
