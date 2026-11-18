# Family planning UX revision

The default view must present household choices rather than the scheduling schema. Use dated day tabs, a home/away choice, sleeping room tiles with configured profile choices, recreation tiles, and meal choices. Show a plain-language summary and actual resulting times. Keep calendar input, raw interval/group editing, physical mappings and JSON in a collapsed Advanced setup section.

Preserve existing custom plans: multiple room uses or split home/away windows remain visibly custom rather than silently flattened. Changing home/away does not silently delete room/meal selections. Report resulting contradictions and offer an explicit action to clear that day's selections. Room profile window defaults are optional configuration, never inferred occupancy.

Copy previous day is a staged draft operation. Show copied room/meal choices and times before applying. Copy local wall-clock windows to the new local date, rejecting ambiguous/nonexistent DST times and out-of-period windows; profile rules still resolve from their own target-day candle/sunrise anchors. Existing target choices are replaced only on explicit application. Manual groups remain unchanged.

Expose independent bedroom HVAC and sleep-light candle offsets through optional timing controls with clear scope: these edit reusable profile defaults for all days using that profile. Show the resulting local times for the selected day. No hidden conversion of fixed-time or differently anchored rules.

English/Hebrew and RTL remain supported. Do not claim live calendar calculation: dates are still supplied illustrative inputs. Keep technical details accessible without requiring a family member to edit them during normal planning. Browser verification remains separate from model/HTTP tests.

Approved next iteration: separate overnight wake-up/HVAC-off from bedtime, and offer optional dated bedroom naps with independent preconditioning. Feature 009 US12 is authoritative. Nap defaults are HVAC-only, including nap-only rooms unused overnight; lighting and linked bathroom demand require their own explicit choices. Current Early/Standard/Late bedtime profiles are not a substitute for independent sleep-late and nap controls. This interaction remains unimplemented.
