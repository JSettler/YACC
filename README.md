# YACC
Yet Another Castlewars Clone

How to play:

Left-click card to play it, discard it with right-click and then right-click in the green area to confirm.
You can define how many cards may be discarded in each turn in the top section of the code. (there, you can also define various other game constants)

If you enable pass-moves, right-click on player-indicator (top-center of screen) to pass your move.
(If computer seemed to not have made a move, it has (probably) passed a move. This should not happen, if passes are not allowed. Please report any bugs.)

Goal of the game:
Either build your tower to the [goal height] first or crush the opponent's tower completely.
NEW: If you have enabled ZERO_GENERATORS_POSSIBLE flag (set to "True"), then you can also win by reducing your opponent to 0 generators and 0 resources (which renders him unable to recover).
In that mode (only), a new card gets added to the pool of drawable cards: "Grow Crystal", it costs 1 crystal to play and returns 2 crystals back to the player. It was added, to enable players (human/computer) to come back into the game with 0 mages and less than 4 crystals left. All cards appear with the same probability, though.

The program automatically creates/updates a scorefile in its current directory.

[Escape] causes the program to save & quit the game.
Upon starting, it checks if there is a savegame and loads it if exists.

The program also creates some simple soundfiles in its current directory. Just some simple beeps for now, as i'm lazy :)
