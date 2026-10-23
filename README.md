James Pond 2: Codename Robocod (Vectordean for Millennium, 1991; Archimedes conversion by 7th ARM Systems / ARM Designs for Eclipse, 1993) - static recompilation
======================================================================================

A recipe: this repository holds no game data. It rebuilds the game as a
native executable from your own copy, recognised by content (recipe.json),
so it can be shared without distributing the game.

    ./build.sh DISC.hfe          (the disc, as an HxC .hfe)
    cd recomp && ./robocod

build.sh runs recipe.json's steps with SuperSpider's tools/weave.py
(~/stuff/superspider, or $SUPERSPIDER; $SS below): it extracts the disc,
runs !RunImage's own two unpackers (tools/unpack.py), analyses and
translates everything, and links it with libroger (~/stuff/libroger, or
make ROGER=...). Needs python3, OCaml/dune, gcc and SDL3.

The input is the one disc of Eclipse's release (RobocodFE 1.01, 26 Oct
1993), as an HxC .hfe. The game checks its disc sector by sector
(ADFS_DiscOp), so the image is kept raw: it is libroger's floppy
(game.c's FLOPPY, ../extracted/disc.hfe).

    extracted/disc.hfe       the disc, via weave.py
    game/!RoboCod            libroger's appdir (../game)
    unpacked/runimage        tools/unpack.py: !RunImage as it runs, at &8000
    unpacked/runimage.roots  ...the objects' state handlers (below)
    unpacked/protect         ...with Files.59 (the disc check) in place
    analysis/                SuperSpider's analyses; *.roots: gap entries (make roots)
    recomp/gen*/             the C translations
    recomp/robocod           the game

Committed: recipe.json, build.sh, tools/unpack.py, recomp/Makefile,
recomp/game.c, recomp/robocod.ini, analysis/*.roots, this file.

How the game is put together
----------------------------

!Run RMLoads GameModes (modes 48 and 49, for the monitors it answers
Service_ModeExtension for: not a TV, so here the game runs in MODE 9),
sets Robocod$Dir and JamesPond$DataDir, and runs PondModule: RobocodFE, a
Wimp task that puts Robocod on the icon bar and, clicked, runs !RunPond2
(WimpSlot 520K, then !RunImage). game.c starts the game as that click
would; the icon bar task isn't run.

- !RunImage is packed twice: an LZ unpacker, then Acorn's squeeze.
  tools/unpack.py runs both under $SS/tools/arm2.py, until the program
  arrives at &8000 the second time; the squeeze header gives its length
  (&8000-&85364).
- &22AAC-&3B14C is a 100000-byte buffer, zeros on disc, that the files in
  Files are loaded into, packed: the program opens them (OS_Find), reads
  them with OS_BGet and unpacks them itself (&3CCC0: LZ, a 4-byte header,
  16 flag bits at a time). &3CE80 loads, for each object type a level
  uses, its graphics there, one after another, and records where in the
  types' records. They are graphics (4bpp, pixels and masks), but for
  Files.59: code, the disc check, which &3D06C loads at &22AAC and calls
  (&3D0A0) whenever the level changes.
- The objects' types have records of &70 bytes at &3F1EC (types 0-&4E):
  word 0 the graphics, words 1-4 the handlers of an object's four states,
  which &47C74 calls through the record (&47CB4: mov pc, r12, lr set to
  return to &47CB8).
- The game sets VIDC's timing itself (&50120, the first of four sets at
  &50094; the others are taller, for other monitors): its picture is 208
  lines from raster line 35, with a border leaving 302 pixels of each line
  (raster pixels 113-415), inside which it scrolls by the pixel with
  HDSR/HDER, set by its vsync handler (&5023C) from the fine scroll the
  main loop leaves (&3E8A0). After its vsync wait the main loop flips the
  banks and sets the display start (&3EE9C, OS_Word 22): in the flyback,
  so on the machine both make the next picture.
- Colour bars (GAME OPTIONS, F5; on to start with): the vsync handler
  restarts IOC timer 1, whose handler (&502F0) sets palette entry 6 from
  a table of 128 colours (&50390), one every 2.25 lines down the frame.

What's translated (recomp/Makefile, make regen):

- !RunImage (gen/), less the buffer: its analysis has &22AAC-&3B14C as
  another image's (--extern), so loading the files there isn't storing over
  its code, and gen leaves it out (--range).
- Files.59 (genprotect/): unpacked/protect, the program with it at &22AAC,
  analysed as one image, and only &22AAC-&22D7C translated (gen --range).
  The program reads it with OS_BGet, which libroger doesn't see as a load:
  game.c selects the overlay (roger_program_loaded) when control first
  reaches &22AAC, its words in place.
- The objects' state handlers are roots (unpacked/runimage.roots, written
  by tools/unpack.py from the types' records, with their return &47CB8):
  52 handlers the analysis can't reach, as only the records point at them.
- GameModes (genmodes/, as a module at &1800000).

Headless and interactive runs through the title, the first level (walking,
jumping, scrolling, dying) and back to the title reach no untranslated
code.

What SuperSpider and libroger needed
------------------------------------

All in libroger, each off by default (roger_config):

- roger_program_loaded(): a program that loads a file its own way
  (OS_Find and OS_BGet, its own unpacker) selects a roger_program as
  OS_File loading it would - once its words are in place, or the stores
  putting them there would leave the translation stale.
- window_x, window_y: where on the raster the window shown starts. A
  standard mode's (pixel 131, line 38) cut the game's top three lines and
  18 pixels off its left; game.c centres its 302 pixels (104, 35).
- raster_palette: timer 1 fires all the way down the frame, its handler
  run each time and the palette it leaves shown from that line (without
  it, only the first: one palette change a frame). The colour bars.
- present_after_flyback: the picture is taken where the next frame's
  display starts (VCR - VDER + VDSR lines after vsync), not at vsync, so
  the display start the main loop sets after its vsync wait shows with the
  fine scroll the vsync handler set. Without it the scroll jumped 16 pixels
  back and forth as the fine scroll wrapped.

Running it
----------

    ./robocod                   as clicking RobocodFE's icon would
    ./robocod --crop            only the game's 208 lines (robocod.ini)

Keys: Z left, X right, K up, M down, Space extend (the game's own; its
key-definition screen asks for LEFT, RIGHT, UP, DOWN and EXTEND). The
GAME OPTIONS screen: F5 colour bars, F6 TV single height / VGA double
height, F7 VGA fill, F8 sound. The game also reads a joystick
(Joystick_Read), which libroger doesn't provide here, so it uses the keys.

Not yet: the score's digits are drawn as boxes.
