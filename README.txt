AI PLAN (in rough priority order):
- create a mouse script that does smooth arcs instead of teleports
- accept numpad/joystick input for general direction. When pressed, moves
    that direction except when stopping to attack/etc.
- detects combat situations somehow
X create a "combat button" that cycles through a list of useful actions, e.g.
    raging spirit, resummoning zombies, flesh offering, skeletotem, etc.
    may need to spell totem everything at first due to aiming difficulty
    - CHECK!
- create a "pick stuff up" button that picks up stuff of a certain priority,
    highlighted as a solid color via item filter
- create a "animate equipment" button that animates leftover items
- create tracking of summon status icons, e.g. # zombies, totem presence,
    to make above more efficient

NOTE: looks like reading full screen vs. just life/mana: about 2x time taken
    to read frame. Probably more processing full screen...


hm:
-found closures only store variables defined inside an enclosing fcn that are
    _also_ used inside a nested fcn in that scope, that is returned - meaning
    they would be garbage collected as no references remained. If the name
    is defined in the global scope it won't bother putting it in the closure,
    though, and it can be deleted. So don't let that happen.
-"Don’t directly create Task instances: use the ensure_future() function or the AbstractEventLoop.create_task() method."

note to self:
- make an item filter so items I care about are bright pink.
then just make it so you can press a button and it will click on the nearest
thing to the center that is that exact shade of pink