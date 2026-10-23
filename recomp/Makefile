# Static recompilation of James Pond 2: Codename Robocod: the game (gen/:
# !RunImage as its two unpackers leave it at &8000, ../tools/unpack.py), its
# disc check (genprotect/: Files.59, which it loads at &22AAC), and the
# GameModes module (genmodes/), from SuperSpider's analyse and gen, and
# game.c, linked with libroger (the RISC OS runtime).
ROGER   ?= $(HOME)/stuff/libroger
CC      ?= gcc
CFLAGS  ?= -O2 -g -w -fno-strict-aliasing $(if $(TRACE),-DRECOMP_TRACE)
GEN     := $(wildcard gen/code*.c) gen/entries.c
GENMODES := $(wildcard genmodes/code*.c) genmodes/entries.c
GENPROT := $(wildcard genprotect/code*.c) genprotect/entries.c
OBJ     := $(GEN:.c=.o) $(GENMODES:.c=.o) $(GENPROT:.c=.o) game.o
LIBS    := $(shell pkg-config --libs sdl3) -ljpeg -lm -lpthread
INC     := -I$(ROGER)/include

robocod: $(OBJ) $(ROGER)/libroger.a
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(ROGER)/libroger.a $(LIBS)

$(ROGER)/libroger.a: FORCE
	$(MAKE) -C $(ROGER) libroger.a

%.o: %.c $(ROGER)/include/roger.h $(ROGER)/include/roger_cpu.h
	$(CC) $(CFLAGS) $(INC) -c -o $@ $<

# Code/data analysis: SuperSpider, into ../analysis/<name>.json, then
# superspider gen. ../unpacked/runimage.roots (../tools/unpack.py) has the
# objects' state handlers, which only their types' records reach. Each image's ../analysis/<name>.roots adds entry points
# to the analysis: "make roots" merges the gap entries a --trace-gaps run
# logged (untranslated.log, or LOG=...) into them, so the next "make regen"
# translates them.
SS      ?= $(HOME)/stuff/superspider
SSBIN   := $(SS)/_build/default/bin/main.exe
AN      := ../analysis
APP     := ../game/!RoboCod
GAME    := ../unpacked/runimage
MODES   := $(firstword $(wildcard $(APP)/GameModes,*) $(APP)/GameModes)
LOG     ?= untranslated.log
# !RunImage, less [&22AAC, &3B14C): a buffer (100000 zero bytes) the files
# in Files are loaded into. Files.59 there is code, translated in an image of
# the program with it in place (../unpacked/protect), only its part. To the
# program's analysis the buffer is another image's (--extern): its code map
# leaves it out, so loading the files there isn't storing over its code.
BUFFER  := 22aac-3b14c
GAMERANGES := --range 8000-22aac --range 3b14c-85364
PROTECT := ../unpacked/protect
PROTRANGE := 22aac-22d7c

# --roots for ../analysis/<name>.roots, if there is one
roots = $(if $(wildcard $(AN)/$(1).roots),--roots $(AN)/$(1).roots)

# $(call analyse,name,image,base[,--module])
define analyse
	$(SSBIN) analyse "$(2)" $(3) $(4) --full $(call roots,$(1)) -o $(AN)/$(1).json
endef

regen:
	cd $(SS) && dune build
	python3 -I ../tools/unpack.py
	mkdir -p $(AN)
	$(call analyse,game,$(GAME),8000,--extern $(BUFFER) --roots $(GAME).roots)
	$(call analyse,modes,$(MODES),1800000,--module)
	$(SSBIN) analyse $(PROTECT) 8000 --full --entry 22aac --roots $(GAME).roots $(call roots,game) $(call roots,protect) \
	    -o $(AN)/protect.json
	rm -rf gen genmodes genprotect
	$(SSBIN) gen "$(GAME)" 8000 $(AN)/game.json --c gen --leaders=dispatch $(GAMERANGES)
	$(SSBIN) gen "$(MODES)" 1800000 $(AN)/modes.json --c genmodes --leaders=dispatch \
	    --prefix=M --tabprefix=recompM --files=1 --covtag=M
	$(SSBIN) gen $(PROTECT) 8000 $(AN)/protect.json --c genprotect --range $(PROTRANGE) --leaders=dispatch \
	    --prefix=D --tabprefix=recompD --files=1 --covtag=D

roots:
	python3 -I $(SS)/tools/gap_roots.py "$(GAME)" 8000 $(AN)/game.roots $(LOG)
	python3 -I $(SS)/tools/gap_roots.py "$(MODES)" 1800000 $(AN)/modes.roots $(LOG)
	python3 -I $(SS)/tools/gap_roots.py $(PROTECT) 8000 $(AN)/protect.roots $(LOG)

clean:
	rm -f gen/*.o genmodes/*.o genprotect/*.o game.o robocod

.PHONY: FORCE regen roots clean
