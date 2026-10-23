/* James Pond 2: Codename Robocod (Vectordean for Millennium, 1991;
 * Archimedes conversion by 7th ARM Systems / ARM Designs for Eclipse, 1993,
 * version 1.01): what libroger needs to know about the game.
 *
 * !Run RMLoads GameModes (two screen modes, 48 and 49), sets Robocod$Dir
 * and JamesPond$DataDir and runs PondModule: a Wimp task (RobocodFE) that
 * puts the Robocod icon on the icon bar and, when it is clicked, starts
 * !RunPond2 - WimpSlot 520K, then !RunImage. Here the game starts as that
 * click would start it; the icon bar task isn't run.
 *
 * !RunImage is packed twice (an LZ unpacker, then Acorn's squeeze):
 * ../tools/unpack.py runs both and the program is translated as they leave
 * it (gen/, for &8000). GameModes is translated as a module (genmodes/).
 * The game checks its disc (ADFS_DiscOp): the original's .hfe is the
 * floppy. The check is Files.59, loaded at &22AAC (genprotect/). */
#include <dirent.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <roger.h>

extern const struct roger_image recomp_image, recompM_image, recompD_image;   /* gen{,modes,protect}/entries.c */

#define APP "../game/!RoboCod"
#define FLOPPY "../extracted/disc.hfe"
static const char *const vars[] = {"Robocod$Dir", "!RoboCod", "JamesPond$DataDir", "!RoboCod", NULL};
static const char *const prefixes[] = {"<Obey$Dir>.", NULL};
static struct roger_module modules[] = {{"GameModes", &recompM_image, 0}, {NULL, NULL, 0}};
/* &22AAC-&3B14C is a buffer the files in Files are loaded into (left out
 * of gen/), packed: the program reads them with OS_BGet and unpacks them
 * itself (&3CCC0), so libroger doesn't see them loaded. They are graphics,
 * but for Files.59, the disc check: &3D06C loads it there and calls it
 * (&3D0A0). Its arrival there, its words in place, selects its translation,
 * an overlay. */
#define PROTECT 0x22AAC
static const struct roger_program programs[] = {
    {"Files.59", &recompD_image, 1, 0},
    {NULL, NULL, 0, 0}};

static int dispatch(uint32_t a)
{
    if (a == PROTECT) roger_program_loaded("<Robocod$Dir>.Files.59", PROTECT);
    return 0;
}

/* a file in !RoboCod, whatever ,load-exec suffix the extraction gave it */
static const char *in_app(const char *leaf)
{
    DIR *d = opendir(APP);
    struct dirent *e;
    char *path = NULL;
    while (d && !path && (e = readdir(d)))
        if (strcspn(e->d_name, ",") == strlen(leaf) && !strncasecmp(e->d_name, leaf, strlen(leaf))) {
            path = malloc(strlen(APP) + strlen(e->d_name) + 2);
            sprintf(path, "%s/%s", APP, e->d_name);
        }
    if (d) closedir(d);
    if (!path) { fprintf(stderr, "no %s/%s: build.sh extracts it\n", APP, leaf); exit(1); }
    return path;
}

static struct roger_config config = {
    .title = "James Pond 2: Robocod (recompiled)",
    .image_path = "../unpacked/runimage",       /* unpacked: ../tools/unpack.py */
    .image = &recomp_image,
    .modules = modules,
    .appdir = "../game",
    .dir_prefixes = prefixes,
    .variables = vars,
    .command_line = "<Robocod$Dir>.!RunImage",
    .initial_mode = 12,                         /* the desktop's */
    .wimpslot = 520 * 1024,                     /* !RunPond2's */
    .floppy = FLOPPY,
    /* In MODE 9 the game sets VIDC's timing itself (&50120, the first of
     * its four sets at &50094; the others are taller, for other monitors):
     * its picture is 208 lines from raster line 35 (VDSR-VDER), the border
     * leaving 302 pixels of each line, 113-415 (HBSR, HBER), inside which
     * it scrolls by the pixel (HDSR/HDER, 45-52). A standard mode's window,
     * from line 38 and pixel 131, would cut its top three lines and 18
     * pixels off the left: the window is the game's, the 302 centred. */
    .window_x = 104,
    .window_y = 35,
    /* Colour bars (GAME OPTIONS, F5; on to start with): its vsync handler
     * (&5023C) restarts IOC timer 1, whose handler (&502F0) sets palette
     * entry 6 from a table of 128 colours (&50390), one every 2.25 lines
     * down the frame (latch &120) */
    .raster_palette = 1,
    /* Its frame: the fine scroll for the frame drawn (&3E8A0) - which the
     * vsync handler puts in HDSR/HDER - then the wait for vsync, then the
     * bank flip and display start (&3EE9C, OS_Word 22), in the flyback:
     * both are in the next picture */
    .present_after_flyback = 1,
    .programs = programs,
    .call_addr = dispatch,
};

int main(int argc, char **argv)
{
    modules[0].path = in_app(modules[0].path);
    roger_main(argc, argv, &config);
}
