# YACC
Yet Another Castlewars Clone

How to play:

Left-click card to play it, discard it with right-click and then right-click in the green area to confirm.
You can define how many cards may be discarded in each turn in the top section of the code. (there, you can also define various other game constants)

If you enable pass-moves, right-click on player-indicator (top-center of screen) to pass your move.
If computer seemed to not make a move, it either discarded or (if you enabled it) passed a move.

Goal of the game:
Either build your tower to the [goal height] first or crush the opponent's tower completely.

The program automatically creates/updates a scorefile in its current directory.

[Escape] causes the program to save & quit the game.
Upon starting, it checks if there is a savegame and loads it if exists.

The program also creates some simple soundfiles in its current directory. Just some simple beeps for now, as i'm lazy :)
