/*
This header is to set the difficulties of all the rolls in the game, for ease of balancing the game. This will include
repair rolls, lockpick rolls, science rolls, etc. Naming conventions are to sort by roll type first, and city name second.
For instance, the repair roll done when the PC tries to repair the jukebox in CotC looks like this:
*/

//REPAIR

#define REPAIR_COTC_Jukebox				(0)
#define Generator_skill_roll				(0)

/* Generic roll modifiers: */

#define Roll_Very_Easy				        (-10)
#define Roll_Easy					(0)
#define Roll_Moderate				        (10)
#define Roll_Hard					(20)
#define Roll_Very_Hard				        (30)
#define Roll_Impossible				        (50)

/* End of Generic roll modifiers */


/* Generic Intimidation roll modifiers: */

#define Intimidate_Very_Easy				(-10)
#define Intimidate_Easy					(0)
#define Intimidate_Moderate				(10)
#define Intimidate_Hard					(20)
#define Intimidate_Very_Hard				(30)
#define Intimidate_Impossible				(50)


/* End of Generic Intimidation roll modifiers */

#ifndef ROLLS_H
#define ROLLS_H