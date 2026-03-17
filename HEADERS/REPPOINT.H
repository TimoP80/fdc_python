/*
	Copyright 1998-2003 Interplay Entertainment Corp.  All rights reserved.
*/

#ifndef REPPOINT_H
#define REPPOINT_H

/*********************************************************
 Here is all of the reputation defines for the game
*********************************************************/


/*-----------------9/16/97 7:41:M-------------------
 General format for this file is:

 I. General reputations and modifiers which need to be read by scripts and the
        engine
    A. Increase and decrease general reputation
    B. Add/remove champion/berserker reputation
    C. Increment good/evil kill counter

 II. Reputation for Enemy of Towns

 III. Reputation for Champion of Towns

 IV. Reputaion for completing seeds
--------------------------------------------------*/


/*********************************************************
 General Reputation
*********************************************************/
// macros for general town status
// good
#define town_rep_is_idolized                       (global_var(TOWN_REP_VAR) >= 30)
#define town_rep_is_liked                          (global_var(TOWN_REP_VAR) >= 15)
#define town_rep_is_accepted                       (global_var(TOWN_REP_VAR) >= 1)
// neutral
#define town_rep_is_neutral                        (global_var(TOWN_REP_VAR) == 0)
// bad
#define town_rep_is_antipaty                       (global_var(TOWN_REP_VAR) <= -1)
#define town_rep_is_hated                          (global_var(TOWN_REP_VAR) <= -15)
#define town_rep_is_vilified                       (global_var(TOWN_REP_VAR) <= -30)

#define REP_BONUS_KILLED_GOOD_CRITTER       (-10)
#define REP_BONUS_KILLED_CHILD              (-15)
#define REP_BONUS_KILLED_EVIL_CRITTER       (5)
#define REP_BONUS_KILLED_NEUTRAL_CRITTER    (0)

// General Town Rep
#define REP_TOWN_KILL_GOOD                      (-5)
#define REP_TOWN_KILL_CHILD                     (-8)
#define REP_TOWN_KILL_EVIL                      (2)

#define inc_general_rep(x)      set_global_var(GVAR_PLAYER_REPUTATION, (global_var(GVAR_PLAYER_REPUTATION) + x));               \
                                debug_msg("Player gains "+x+" Karma Points.");                                                  \
                                CheckKarma

#define dec_general_rep(x)      set_global_var(GVAR_PLAYER_REPUTATION, (global_var(GVAR_PLAYER_REPUTATION) - x));               \
                                CheckKarma

#define check_general_rep       global_var(GVAR_PLAYER_REPUTATION)


#ifdef TOWN_REP_VAR
#define inc_childkiller         if (source_obj == dude_obj) then begin                                                               \
                                    remove_champion;                                                                                 \
                                    set_global_var(GVAR_CHILDKILLER_REPUTATION, (global_var(GVAR_CHILDKILLER_REPUTATION) +1));       \
                                    inc_general_rep(REP_BONUS_KILLED_CHILD);                                                         \
                                    set_global_var(TOWN_REP_VAR,(global_var(TOWN_REP_VAR)+REP_TOWN_KILL_CHILD));                     \
                                    debug_msg("Added "+REP_TOWN_KILL_CHILD+" to Town Rep");                                          \
                                end
#else
#define inc_childkiller         if (source_obj == dude_obj) then begin                                                               \
                                    remove_champion;                                                                                 \
                                    set_global_var(GVAR_CHILDKILLER_REPUTATION, (global_var(GVAR_CHILDKILLER_REPUTATION) +1));       \
                                    dec_general_rep(REP_BONUS_KILLED_CHILD);                                                         \
                                end
#endif

/*-----------------9/16/97 7:40:M-------------------
 The following check to see if the player has the particular reputations as per design
--------------------------------------------------*/

/* Karma Levels */
#define KARMA_HOLY_WARRIOR                  (1000)
#define KARMA_GUARDIAN_OF_THE_WASTES        (750)
#define KARMA_SHIELD_OF_HOPE                (500)
#define KARMA_DEFENDER                      (250)
#define KARMA_WANDERER                      (0)
#define KARMA_BETRAYER                      (-250)
#define KARMA_SWORD_OF_DESPAIR              (-500)
#define KARMA_SCOURGE_OF_THE_WASTES         (-750)
#define KARMA_DEMON_SPAWN                   (-1000)

/* Reputation Checks */
#define has_rep_childkiller     (global_var(GVAR_CHILDKILLER_REPUTATION) >= 2)

#define has_rep_champion        (((global_var(GVAR_BAD_MONSTER) + global_var(GVAR_GOOD_MONSTER)) >= 25) and                          \
                                ((global_var(GVAR_BAD_MONSTER) > (3 * global_var(GVAR_GOOD_MONSTER))) or                             \
                                (global_var(GVAR_CHAMPION_REPUTATION) == 1)) and (global_var(GVAR_CHILDKILLER_REPUTATION) == 0))

#define has_rep_berserker       ((global_var(GVAR_BAD_MONSTER) + global_var(GVAR_GOOD_MONSTER) >= 25) and                            \
                                ((global_var(GVAR_GOOD_MONSTER) > (2 * global_var(GVAR_BAD_MONSTER))) or                             \
                                (global_var(GVAR_BERSERKER_REPUTATION) == 1)))

#define has_rep_slaver          (global_var(GVAR_REPUTATION_SLAVER) == 1)

#define has_rep_slave_owner     (global_var(GVAR_REPUTATION_SLAVE_OWNER) == 1)

#define ClearReps               set_global_var(GVAR_KARMA_HOLY_WARRIOR,0);                                      \
                                set_global_var(GVAR_KARMA_GUARDIAN_OF_THE_WASTES,0);                            \
                                set_global_var(GVAR_KARMA_SHIELD_OF_HOPE,0);                                    \
                                set_global_var(GVAR_KARMA_DEFENDER,0);                                          \
                                set_global_var(GVAR_KARMA_WANDERER,0);                                          \
                                set_global_var(GVAR_KARMA_BETRAYER,0);                                          \
                                set_global_var(GVAR_KARMA_SWORD_OF_DESPAIR,0);                                  \
                                set_global_var(GVAR_KARMA_SCOURGE_OF_THE_WASTES,0);                              \
                                set_global_var(GVAR_KARMA_DEMON_SPAWN,0)

#define CheckKarma              ClearReps;                                                                      \
                                if (check_general_rep >= KARMA_HOLY_WARRIOR) then                               \
                                    set_global_var(GVAR_KARMA_HOLY_WARRIOR,1);                                  \
                                else if (check_general_rep >= KARMA_GUARDIAN_OF_THE_WASTES) then                \
                                    set_global_var(GVAR_KARMA_GUARDIAN_OF_THE_WASTES,1);                        \
                                else if (check_general_rep >= KARMA_SHIELD_OF_HOPE) then                        \
                                    set_global_var(GVAR_KARMA_SHIELD_OF_HOPE,1);                                \
                                else if (check_general_rep >= KARMA_DEFENDER) then                              \
                                    set_global_var(GVAR_KARMA_DEFENDER,1);                                      \
                                else if (check_general_rep > KARMA_BETRAYER) then                               \
                                    set_global_var(GVAR_KARMA_WANDERER,1);                                      \
                                else if (check_general_rep > KARMA_SWORD_OF_DESPAIR) then                       \
                                    set_global_var(GVAR_KARMA_BETRAYER,1);                                      \
                                else if (check_general_rep > KARMA_SCOURGE_OF_THE_WASTES) then                  \
                                    set_global_var(GVAR_KARMA_SWORD_OF_DESPAIR,1);                              \
                                else if (check_general_rep > KARMA_DEMON_SPAWN) then                            \
                                    set_global_var(GVAR_KARMA_SCOURGE_OF_THE_WASTES,1);                         \
                                else                                                                            \
                                    set_global_var(GVAR_KARMA_DEMON_SPAWN,1)

#define has_rep_holy_warrior    (global_var(GVAR_KARMA_HOLY_WARRIOR) == 1)
#define has_rep_guardian        (global_var(GVAR_KARMA_GUARDIAN_OF_THE_WASTES) == 1)
#define has_rep_shield          (global_var(GVAR_KARMA_SHIELD_OF_HOPE) == 1)
#define has_rep_defender        (global_var(GVAR_KARMA_DEFENDER) == 1)
#define has_rep_wanderer        (global_var(GVAR_KARMA_WANDERER) == 1)
#define has_rep_betrayer        (global_var(GVAR_KARMA_BETRAYER) == 1)
#define has_rep_sword           (global_var(GVAR_KARMA_SWORD_OF_DESPAIR) == 1)
#define has_rep_scourge         (global_var(GVAR_KARMA_SCOURGE_OF_THE_WASTES) == 1)
#define has_rep_demon_spawn     (global_var(GVAR_KARMA_DEMON_SPAWN) == 1)

/*-----------------9/16/97 7:40:M-------------------
 The following will add or remove the reputations of champion or berserker
--------------------------------------------------*/

#define give_champion           set_global_var(GVAR_CHAMPION_REPUTATION,1)
#define give_berserker          set_global_var(GVAR_BERSERKER_REPUTATION,1)
#define remove_champion         set_global_var(GVAR_CHAMPION_REPUTATION,0)
#define remove_berserker        set_global_var(GVAR_BERSERKER_REPUTATION,0)


/*-----------------9/16/97 7:38:M-------------------
 This will check to see if the player has killed enough bad people to be
 considered a champion of the world. it will remove the berserker reputation
 and give the champion reputation
--------------------------------------------------*/

#define CHECK_REP_CHAMPION      if (has_rep_champion) then begin      \
                                        give_champion;                \
                                        remove_berserker;             \
                                end


/*-----------------9/16/97 7:38:M-------------------
 This will check to see if the player has killed too many people and will
 remove the reputation of champion to give the reputation berserker
--------------------------------------------------*/

#define CHECK_REP_BERSERKER     if (has_rep_berserker) then begin     \
                                        give_berserker;               \
                                        remove_champion;              \
                                end


/**************************************************************************
 Every time that an good critter dies, it will increase the number of good
 critters killed. inc_good_critter will keep track of the kills and give or
 remove reputatins based on what has been killed
**************************************************************************/

#ifdef TOWN_REP_VAR
#define inc_good_critter        if (source_obj == dude_obj) then begin                                          \
                                    set_global_var(GVAR_GOOD_MONSTER, (global_var(GVAR_GOOD_MONSTER) + 1));     \
                                    CHECK_REP_CHAMPION                                                          \
                                    if (critter_kill_type(self_obj) == KILL_TYPE_children_kills) then           \
                                        inc_childkiller                                                         \
                                    CHECK_REP_BERSERKER                                                         \
                                    inc_general_rep(REP_BONUS_KILLED_GOOD_CRITTER);                             \
                                    set_global_var(TOWN_REP_VAR,(global_var(TOWN_REP_VAR)+REP_TOWN_KILL_GOOD)); \
                                    debug_msg("Added "+REP_TOWN_KILL_GOOD+" to Town Rep");                      \
                                end

#define inc_inv_good_crit       if (source_obj == dude_obj) then begin                                          \
                                    set_global_var(GVAR_GOOD_MONSTER, (global_var(GVAR_GOOD_MONSTER) + 1));     \
                                    CHECK_REP_CHAMPION                                                          \
                                    if (critter_kill_type(self_obj) == KILL_TYPE_children_kills) then           \
                                        inc_childkiller                                                         \
                                    CHECK_REP_BERSERKER                                                         \
                                    inc_general_rep(REP_BONUS_KILLED_GOOD_CRITTER);                             \
                                    set_global_var(TOWN_REP_VAR,(global_var(TOWN_REP_VAR)+REP_TOWN_KILL_EVIL)); \
                                    debug_msg("Added "+REP_TOWN_KILL_GOOD+" to Town Rep");                      \
                                end

#else
#define inc_good_critter        if (source_obj == dude_obj) then begin                                          \
                                    set_global_var(GVAR_GOOD_MONSTER, (global_var(GVAR_GOOD_MONSTER) + 1));     \
                                    if (critter_kill_type(self_obj) == KILL_TYPE_children_kills) then           \
                                        inc_childkiller                                                         \
                                    CHECK_REP_CHAMPION                                                          \
                                    CHECK_REP_BERSERKER                                                         \
                                    inc_general_rep(REP_BONUS_KILLED_GOOD_CRITTER);                             \
                                end
#endif

#define inc_neutral_critter     if (source_obj == dude_obj) then begin                                          \
                                    CHECK_REP_CHAMPION                                                          \
                                    if (critter_kill_type(self_obj) == KILL_TYPE_children_kills) then           \
                                        inc_childkiller                                                         \
                                    CHECK_REP_BERSERKER                                                         \
                                    inc_general_rep(REP_BONUS_KILLED_NEUTRAL_CRITTER);                          \
                                end

/**************************************************************************
 Every time that an evil critter dies, it will increase the number of evil
 critters killed. inc_evil_critter will keep track of the kills and give or
 remove reputations based on what has been killed
**************************************************************************/

#ifdef TOWN_REP_VAR
#define inc_evil_critter        if (source_obj == dude_obj) then begin                                          \
                                    set_global_var(GVAR_BAD_MONSTER, (global_var(GVAR_BAD_MONSTER) + 1));       \
                                    if (critter_kill_type(self_obj) == KILL_TYPE_children_kills) then           \
                                        inc_childkiller                                                         \
                                    CHECK_REP_BERSERKER                                                         \
                                    CHECK_REP_CHAMPION                                                          \
                                    inc_general_rep(REP_BONUS_KILLED_EVIL_CRITTER);                             \
                                    set_global_var(TOWN_REP_VAR,(global_var(TOWN_REP_VAR)+REP_TOWN_KILL_EVIL)); \
                                    debug_msg("Added "+REP_TOWN_KILL_EVIL+" to Town Rep");                      \
                                end

#define inc_inv_evil_crit       if (source_obj == dude_obj) then begin                                          \
                                    set_global_var(GVAR_BAD_MONSTER, (global_var(GVAR_BAD_MONSTER) + 1));       \
                                    if (critter_kill_type(self_obj) == KILL_TYPE_children_kills) then           \
                                        inc_childkiller                                                         \
                                    CHECK_REP_BERSERKER                                                         \
                                    CHECK_REP_CHAMPION                                                          \
                                    inc_general_rep(REP_BONUS_KILLED_EVIL_CRITTER);                             \
                                    set_global_var(TOWN_REP_VAR,(global_var(TOWN_REP_VAR)+REP_TOWN_KILL_GOOD)); \
                                    debug_msg("Added "+REP_TOWN_KILL_EVIL+" to Town Rep");                      \
                                end

#else
#define inc_evil_critter        if (source_obj == dude_obj) then begin                                          \
                                    set_global_var(GVAR_BAD_MONSTER, (global_var(GVAR_BAD_MONSTER) + 1));       \
                                    if (critter_kill_type(self_obj) == KILL_TYPE_children_kills) then           \
                                        inc_childkiller                                                         \
                                    CHECK_REP_BERSERKER                                                         \
                                    CHECK_REP_CHAMPION                                                          \
                                    inc_general_rep(REP_BONUS_KILLED_EVIL_CRITTER);                             \
                                end
#endif



#endif // REPPOINT_H


/*************************************************************************
 Karma Values for Fan Made Fallout
*************************************************************************/

//City on the Coast
#define REP_HERO_KILLED_BUTCH 			(-20)
#define REP_HERO_KILLED_JEREMIAH 		(-20)



