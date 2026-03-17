#ifndef COMMAND_H
#define COMMAND_H



#define mstr(x)                     message_str(NAME,x)
#define display_mstr(x)             display_msg(mstr(x))

#define LOW_IQ                      (-3)

#define Reply(x)                    gSay_Reply(NAME,x)
#define Reply_Rand(x,y)             Reply(random(x,y))
#define GMessage(x)                 gSay_Message(NAME,x,GOOD_REACTION)
#define NMessage(x)                 gSay_Message(NAME,x,NEUTRAL_REACTION)
#define BMessage(x)                 gSay_Message(NAME,x,BAD_REACTION)

#define GOption(x,y,z)              giQ_Option(z,NAME,x,y,GOOD_REACTION)
#define NOption(x,y,z)              giQ_Option(z,NAME,x,y,NEUTRAL_REACTION)
#define BOption(x,y,z)              giQ_Option(z,NAME,x,y,BAD_REACTION)
#define Option(x,y)                 gSay_Option(NAME,x,y,NEUTRAL_REACTION)


#define critter_is_armed(x)                 (((obj_item_subtype(critter_inven_obj(x,INVEN_TYPE_RIGHT_HAND))) == item_type_weapon) or \
                                             ((obj_item_subtype(critter_inven_obj(x,INVEN_TYPE_LEFT_HAND))) == item_type_weapon))
#define critter_weight(x)                   (100 + ((get_critter_stat(x,STAT_gender) == GENDER_MALE) * 50) + (get_critter_stat(x,STAT_st) * 5) - ((get_critter_stat(x,STAT_ag) + get_critter_stat(x,STAT_en))/3))
#define critter_wearing_armor(x)            (obj_item_subtype(critter_inven_obj(x,INVEN_TYPE_WORN)) == item_type_armor)

#define dude_name                           (obj_name(dude_obj))
#define dude_gender                         (get_critter_stat(dude_obj,STAT_gender))

#define dude_is_male                        (dude_gender == GENDER_MALE)
#define dude_is_female                      (dude_gender == GENDER_FEMALE)
#define dude_is_armed                       critter_is_armed(dude_obj)
#define dude_wearing_armor                  critter_wearing_armor(dude_obj)


/****************************
  The Stink specific defines
 ****************************/

//OBS! REMEMBER TO CHANGE "autodoc_hp_neg1_perk" and "autodoc_hp_neg2_perk" TO THE CORRECT STINK PERKS!

#define dude_has_perm_stink   (global_var(GVAR_STINK_WEAR_OFF) == -1)
#define dude_has_the_stink    (game_time < global_var(GVAR_STINK_WEAR_OFF))

//this is the one that should be used when checking if the dude is stinking:
#define dude_stinks           (dude_has_perm_stink OR dude_has_the_stink)

#define update_the_stink      set_global_var(GVAR_STINK_TOTAL,global_var(GVAR_STINK_TOTAL)+1);                       \
                              if not(has_trait(TRAIT_PERK,dude_obj,PERK_autodoc_hp_neg1_perk)) then begin            \
                                 critter_add_trait(dude_obj,TRAIT_PERK,PERK_autodoc_hp_neg1_perk,1);                 \
                              end                                                                                    \
                              if(global_var(GVAR_STINK_TOTAL) == 20) then begin                                      \
                                 display_msg("You acquired the Permanent Stink!");                                   \
                                 set_global_var(GVAR_STINK_WEAR_OFF,-1);                                             \
                                 critter_rm_trait(dude_obj,TRAIT_PERK,PERK_autodoc_hp_neg1_perk,1);                  \
                                 critter_add_trait(dude_obj,TRAIT_PERK,PERK_autodoc_hp_neg2_perk,1);                 \
                              end

//This one is called to properly add one day's worth of the stink. It is called if the PC finishes a shift at Royce's,
//if the PC sleeps with Royce and possibly in some other situation as well.

#define increase_the_stink    if(dude_has_the_stink) then begin                                                      \
                                 set_global_var(GVAR_STINK_WEAR_OFF,global_var(GVAR_STINK_WEAR_OFF)+ONE_GAME_DAY);   \
                                 update_the_stink                                                                    \
                              end else if not(dude_has_perm_stink) then begin                                        \
                                 set_global_var(GVAR_STINK_WEAR_OFF,game_time+ONE_GAME_DAY);                         \
                                 update_the_stink                                                                    \
                              end

//This is called to properly get rid of the stink. It is called when the PC takes a shower or a bath. It virtually 
//resets all values to make it look as if the PC was never near Royce or his warehouse.
                              
#define remove_the_stink      set_global_var(GVAR_STINK_TOTAL,0);                                                    \
                              set_global_var(GVAR_STINK_WEAR_OFF,0);                                                 \
                              critter_rm_trait(dude_obj,TRAIT_PERK,PERK_autodoc_hp_neg1_perk,1);                     \
                              critter_rm_trait(dude_obj,TRAIT_PERK,PERK_autodoc_hp_neg2_perk,1);

/***********************************
  End of The Stink specific defines
 ***********************************/


#define roll_vs_intimidate(X,Y)     (random(0,1))



/***************************************************************
**************  Begin Original FO Defines   ********************
***************************************************************/

/*********************************************************
 General interaction dealing with the dude
 should he attack people in a community
*********************************************************/
variable global_temp;

#define Get_Rotation_Away_From_Dude(x)      rotation_to_tile(tile_num(dude_obj),tile_num(x))

#define Run_Away_From_Dude_Dir              Get_Rotation_Away_From_Dude(self_obj)
#define run_away_from_dist                  random(3, 10)
#define push_away_from_dist                 random(2, 5)

#define run_away_tile_dir(x)                tile_num_in_direction(tile_num(self_obj), x, run_away_from_dist)
#define Run_Away_From_Dude_Tile             run_away_tile_dir(Run_Away_From_Dude_Dir)

#define Current_Distance_From_Dude          tile_distance_objs(self_obj,dude_obj)

#define Future_Distance_From_Obj(x, y)      tile_num_in_direction(tile_num(x), ((has_trait(TRAIT_OBJECT,x,OBJECT_CUR_ROT) + 3)%6), y)
#define Future_Distance_From_Dude(x)        Future_Distance_From_Obj(dude_obj, x)

#define away_from_tile_type(x, type, dist)  if (anim_busy(self_obj) == false) then begin                                                             \
                                               global_temp := rotation_to_tile(x, self_tile);                                                        \
                                               animate_##type##_to_tile(tile_num_in_direction(self_tile, global_temp, dist));                        \
                                               global_temp := (global_temp + 1) % 6;                                                                 \
                                               while ((anim_busy(self_obj) == false) and (global_temp != rotation_to_tile(x, self_tile))) do begin   \
                                                  debug_msg("flee loop: rot == "+global_temp);                                                       \
                                                  animate_##type##_to_tile(tile_num_in_direction(self_tile, global_temp, dist));                     \
                                                  global_temp := (global_temp + 1) % 6;                                                              \
                                               end                                                                                                   \
                                            end

#define simulate_push(x)                    away_from_tile_type(tile_num_in_direction(self_tile, rotation_to_tile(x, self_tile), 1), move, push_away_from_dist)
#define flee_from_tile(x)                   away_from_tile_type(x, run, run_away_from_dist)
#define Flee_From_Dude                      if ((Current_Distance_From_Dude < 8) or (self_can_see_dude)) then begin  \
                                               flee_from_tile(dude_tile)                                             \
                                            end

#define Flee_From_Dude_Force                if ((Current_Distance_From_Dude < 8) or (self_can_see_dude)) then begin  \
                                                animate_run_to_tile_force(Run_Away_From_Dude_Tile);                  \
                                            end

#define Follow_Dude(X,Y)                    if (Current_Distance_From_Dude > X) then begin                  \
                                               if (Current_Distance_From_Dude > X*2) then begin             \
                                                  animate_run_to_tile(Future_Distance_From_Dude(Y));        \
                                               end else begin                                               \
                                                  animate_move_to_tile(Future_Distance_From_Dude(Y));       \
                                               end                                                          \
                                            end

#define get_follow_point_dist(the_obj)      ((tile_distance_objs(the_obj, self_obj) / 5) + 1)
#define follow_obj_point(the_range, the_dist, the_obj)                                                            \
                                            if (Current_Distance_From_Dude > the_range) then begin                \
                                                if (Current_Distance_From_Dude > (the_range * 2)) then begin    \
                                                   anim_run_to_point_rate(tile_num_in_direction(tile_num(the_obj), rotation_to_tile(tile_num(the_obj), self_tile), the_dist), get_follow_point_dist(the_obj))   \
                                                end else begin                                                  \
                                                   anim_move_to_point_rate(tile_num_in_direction(tile_num(the_obj), rotation_to_tile(tile_num(the_obj), self_tile), the_dist), get_follow_point_dist(the_obj))  \
                                                end                                                             \
                                            end
#define follow_dude_point(the_range, the_dist)     follow_obj_point(the_range, the_dist, dude_obj)

#define Follow_Dude_Run_Only(X,Y)           if (Current_Distance_From_Dude > X) then begin                  \
                                               animate_run_to_tile(Future_Distance_From_Dude(Y));           \
                                            end

#define Follow_Obj_Run_Only(O,X,Y)          if (tile_distance_objs(self_obj,O) > X) then begin              \
                                               animate_run_to_tile(Future_Distance_From_Obj(O, Y));         \
                                            end
#define Get_In_Obj_Face(the_obj)            if (tile_distance_objs(self_obj, the_obj) > 1) then begin                                                              \
                                               animate_move_to_tile(tile_num_in_direction(tile_num(the_obj), has_trait(TRAIT_OBJECT,the_obj,OBJECT_CUR_ROT), 1));  \
                                            end else if (rotation_to_tile(tile_num(self_obj),tile_num(the_obj)) != self_cur_rot) then begin                        \
                                               if (anim_busy(self_obj) == false) then begin                                                                        \
                                                  Face_Critter(the_obj, self_obj);                                                                                 \
                                               end                                                                                                                 \
                                            end
#define Get_In_Face_Run_Dist(the_obj,dist)  if (tile_distance_objs(self_obj, the_obj) > 1) then begin                                                              \
                                               animate_run_to_tile(tile_num_in_direction(tile_num(the_obj), has_trait(TRAIT_OBJECT,the_obj,OBJECT_CUR_ROT), dist));\
                                            end else if (rotation_to_tile(tile_num(self_obj),tile_num(the_obj)) != self_cur_rot) then begin                        \
                                               if (anim_busy(self_obj) == false) then begin                                                                        \
                                                  Face_Critter(the_obj, self_obj);                                                                                 \
                                               end                                                                                                                 \
                                            end

#define next_and_face_obj(the_obj, the_type, the_rate)                                                                                                                       \
                                             if (tile_distance_objs(self_obj, the_obj) > 1) then begin                                                             \
                                                the_type(tile_num_in_direction(tile_num(the_obj), rotation_to_tile(tile_num(the_obj),tile_num(self_obj)), 1), the_rate);     \
                                             end else if (rotation_to_tile(tile_num(self_obj),tile_num(the_obj)) != self_cur_rot) then begin                       \
                                                if (anim_busy(self_obj) == false) then begin                                                                       \
                                                   Face_Critter(the_obj, self_obj);                                                                                \
                                                end                                                                                                                \
                                             end

#define point_next_and_face_obj(the_obj, the_type, the_rate)                                                                                                                 \
                                             if (tile_distance_objs(self_obj, the_obj) > 1) then begin                                                             \
                                                the_type(tile_num_in_direction(tile_num(the_obj), rotation_to_tile(tile_num(the_obj),tile_num(self_obj)), 1), the_rate) \
                                             end else if (rotation_to_tile(tile_num(self_obj),tile_num(the_obj)) != self_cur_rot) then begin                       \
                                                if (anim_busy(self_obj) == false) then begin                                                                       \
                                                   Face_Critter(the_obj, self_obj);                                                                                \
                                                end                                                                                                                \
                                             end

#define Get_Next_To_Obj_And_Face_Rate(the_obj, x)     next_and_face_obj(the_obj, animate_move_to_tile, x)
#define Get_Next_To_Obj_And_Face(the_obj)             next_and_face_obj(the_obj, animate_move_to_tile, 1)
#define Run_Next_To_Obj_And_Face_Rate(the_obj, x)     next_and_face_obj(the_obj, animate_run_to_tile, x)
#define Run_Next_To_Obj_And_Face(the_obj)             next_and_face_obj(the_obj, animate_run_to_tile, 1)
#define point_move_next_and_face_Rate(the_obj, x)     point_next_and_face_obj(the_obj, anim_move_to_point, x)
#define point_move_next_and_face(the_obj)             point_next_and_face_obj(the_obj, anim_move_to_point, 1)
#define point_run_next_and_face_Rate(the_obj, x)      point_next_and_face_obj(the_obj, anim_run_to_point, x)
#define point_run_next_and_face(the_obj)              point_next_and_face_obj(the_obj, anim_run_to_point, 1)

// the Z is a variable LOCAL variable that stores the tile where the dude was last time it was told to follow
//    this will keep the animation for the follow clean

#define closest_clear_tile(obj, the_tile, x)       x := the_tile;                                                                   \
                                                   while ((x != tile_num(obj)) and (tile_is_blocked(x, elevation(obj)))) do begin   \
                                                      x := tile_num_in_direction(x, rotation_to_tile(x, tile_num(obj)), 1);         \
                                                   end
// this is like the above but uses to regular variables instead of local vars
// this steps like the old step macro, but it's faster and better
//
variable dest_tile;
variable step_tile;
#define FAIL_STEP_ACTION                           if (tile_get_next_critter(tile_num_in_direction(self_tile, self_cur_rot, 1), self_elevation, 0) != 0) then begin \
                                                      simulate_push(tile_num_in_direction(self_tile, self_cur_rot, 1))                                                                                                 \
                                                   end else step_tile := -10;
//#define FAIL_STEP_ACTION                           step_tile := -5;
#define move_to_point(the_tile, move_type, x)                                                                                                                                    \
                                                   if ((self_tile != the_tile) and (the_tile != 0)) then begin                                                                                  \
                                                      if ((dest_tile == the_tile) and (step_tile < 0)) then begin                                                                               \
                                                         step_tile += 1;                                                                                                                        \
                                                      end else if (anim_busy(self_obj) == false) then begin                                                                                     \
                                                         dest_tile := the_tile;                                                                                                                 \
                                                         step_tile := the_tile;                                                                                                                 \
                                                         animate_##move_type##_to_tile(step_tile);                                                                                              \
                                                         debug_msg("move_to_point: self_tile == "+self_tile);                                                                                   \
                                                         while ((anim_busy(self_obj) == false) and (((tile_distance(self_tile, the_tile)) >= (tile_distance(step_tile, the_tile))))) do begin   \
                                                            step_tile := tile_num_in_direction(step_tile, rotation_to_tile(step_tile, self_tile), (x % tile_distance(step_tile, self_tile)));   \
                                                            debug_msg("move_to_point: step_tile == "+step_tile);                                                                                \
                                                            animate_##move_type##_to_tile(step_tile);                                                                                           \
                                                         end                                                                                                                                    \
                                                         if (anim_busy(self_obj) == false) then begin                                                                                           \
                                                            FAIL_STEP_ACTION                                                                                                                    \
                                                         end                                                                                                                                    \
                                                      end else if ((tile_distance(self_tile, the_tile)) < (tile_distance(dest_tile, the_tile))) then begin                                        \
                                                         reg_anim_clear(self_obj);                                                                                                              \
                                                      end                                                                                                                                       \
                                                   end

#define anim_move_to_point_rate(the_tile, x)       move_to_point(the_tile, move, x)
#define anim_move_to_point(the_tile)               anim_move_to_point_rate(the_tile, 1)
#define anim_run_to_point_rate(the_tile, x)        move_to_point(the_tile, run, x)
#define anim_run_to_point(the_tile)                anim_run_to_point_rate(the_tile, 1)


// map variables that share the same number throught the maps are listed here

#define critter_is_armed(x)                 (((obj_item_subtype(critter_inven_obj(x,INVEN_TYPE_RIGHT_HAND))) == item_type_weapon) or \
                                             ((obj_item_subtype(critter_inven_obj(x,INVEN_TYPE_LEFT_HAND))) == item_type_weapon))
#define critter_weight(x)                   (100 + ((get_critter_stat(x,STAT_gender) == GENDER_MALE) * 50) + (get_critter_stat(x,STAT_st) * 5) - ((get_critter_stat(x,STAT_ag) + get_critter_stat(x,STAT_en))/3))
#define critter_wearing_armor(x)            (obj_item_subtype(critter_inven_obj(x,INVEN_TYPE_WORN)) == item_type_armor)

#define dude_is_stupid                      (dude_iq <= 3)
#define dude_name                           (obj_name(dude_obj))
#define dude_gender                         (get_critter_stat(dude_obj,STAT_gender))
#define dude_strength                       (get_critter_stat(dude_obj,STAT_st))
#define dude_perception                     (get_critter_stat(dude_obj,STAT_pe))
#define dude_endurance                      (get_critter_stat(dude_obj,STAT_en))
#define dude_charisma                       (get_critter_stat(dude_obj,STAT_ch))
#define dude_iq                             (get_critter_stat(dude_obj,STAT_iq))
#define dude_agility                        (get_critter_stat(dude_obj,STAT_ag))
#define dude_luck                           (get_critter_stat(dude_obj,STAT_lu))
#ifndef dude_level
#define dude_level                          (get_pc_stat(PCSTAT_level))
#endif
#define dude_age                            (get_critter_stat(dude_obj,STAT_age))
#define dude_weight                         critter_weight(dude_obj)

#define dude_moron_not_vegetable            (((get_critter_stat(dude_obj,STAT_iq)) > 1) and ((get_critter_stat(dude_obj,STAT_iq)) < 3) )

#define dude_is_male                        (dude_gender == GENDER_MALE)
#define dude_is_female                      (dude_gender == GENDER_FEMALE)
#define dude_is_armed                       critter_is_armed(dude_obj)
#define dude_wearing_armor                  critter_wearing_armor(dude_obj)

#define dude_has_power_armor                (((obj_is_carrying_obj_pid(dude_obj, PID_POWERED_ARMOR)) +            \
                                              (obj_is_carrying_obj_pid(dude_obj, PID_ADVANCED_POWER_ARMOR)) +     \
                                              (obj_is_carrying_obj_pid(dude_obj, PID_ADVANCED_POWER_ARMOR_MK2)) + \
                                              (obj_is_carrying_obj_pid(dude_obj, PID_HARDENED_POWER_ARMOR))) > 0)

#define dude_wielding_knife                 ((obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_RIGHT_HAND)) == PID_KNIFE) or                \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_RIGHT_HAND)) == PID_THROWING_KNIFE) or       \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_RIGHT_HAND)) == PID_RIPPER) or               \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_RIGHT_HAND)) == PID_COMBAT_KNIFE) or         \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_LEFT_HAND)) == PID_KNIFE) or                 \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_LEFT_HAND)) == PID_THROWING_KNIFE) or        \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_LEFT_HAND)) == PID_RIPPER) or                \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_LEFT_HAND)) == PID_COMBAT_KNIFE))

#define dude_wearing_power_armor            ((obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_POWERED_ARMOR) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_ADVANCED_POWER_ARMOR) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_ADVANCED_POWER_ARMOR_MK2) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_HARDENED_POWER_ARMOR))

#define dude_wearing_leather_armor          ((obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_LEATHER_ARMOR) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_LEATHER_JACKET) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_LEATHER_ARMOR_MK_II) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_CURED_LEATHER_ARMOR))

#define dude_wearing_combat_armor           ((obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_COMBAT_ARMOR) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_BROTHERHOOD_COMBAT_ARMOR) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_COMBAT_ARMOR_MK_II))

#define dude_wearing_metal_armor            ((obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_METAL_ARMOR) or \
                                             (obj_pid(critter_inven_obj(dude_obj,INVEN_TYPE_WORN)) == PID_METAL_ARMOR_MK_II))

#define dude_wearing_vault_suit             COND019(1)
#define dude_has_gambling_skills            ((dude_iq > 3) and (has_skill(dude_obj, SKILL_GAMBLING) >= 25))

#define dude_is_sneaking                    (using_skill(dude_obj,SKILL_SNEAK))
#define dude_is_walking                     (art_anim(obj_art_fid(dude_obj)) == ANIM_walk)
#define dude_is_running                     (art_anim(obj_art_fid(dude_obj)) == ANIM_running)
#define dude_is_poisoned                    (get_poison(dude_obj))
#define dude_is_irradiated                  (get_critter_stat(dude_obj, STAT_current_rad))
#define dude_is_crippled                    ((critter_state(dude_obj) bwand DAM_CRIP_LEG_LEFT)  or \
                                             (critter_state(dude_obj) bwand DAM_CRIP_LEG_RIGHT) or \
                                             (critter_state(dude_obj) bwand DAM_CRIP_ARM_LEFT)  or \
                                             (critter_state(dude_obj) bwand DAM_CRIP_ARM_RIGHT))

#define dude_cur_rot                        (has_trait(TRAIT_OBJECT,dude_obj,OBJECT_CUR_ROT))
#define dude_inv_rot                        ((dude_cur_rot + 3)%6)
#define dude_tile                           (tile_num(dude_obj))
#define dude_elevation                      (elevation(dude_obj))

#define tile_behind_obj(who)                (tile_num_in_direction(tile_num(who),((has_trait(TRAIT_OBJECT,who,OBJECT_CUR_ROT) + 3) % 6), 1))
#define tile_behind_obj_rng(who, rng)       (tile_num_in_direction(tile_num(who),((has_trait(TRAIT_OBJECT,who,OBJECT_CUR_ROT) + 3) % 6), rng))

#define dude_cur_hits                       (get_critter_stat(dude_obj,STAT_current_hp))
#define dude_max_hits                       (get_critter_stat(dude_obj,STAT_max_hp))

#define dude_mental_block                   (has_trait(TRAIT_PERK,dude_obj,PERK_mental_block))
#define dude_presence                       (has_trait(TRAIT_PERK,dude_obj,PERK_presence))
#define dude_awareness                      (has_trait(TRAIT_PERK,dude_obj,PERK_bonus_awareness))
#define dude_fortune_finder                 (has_trait(TRAIT_PERK,dude_obj,PERK_fortune_finder))
#define dude_smooth_talker                  (has_trait(TRAIT_PERK,dude_obj,PERK_smooth_talker))

#define dude_caps                           (item_caps_total(dude_obj))

#define dude_has_car                        (global_var(GVAR_PLAYER_GOT_CAR))
#define dude_is_pornstar                    dude_has_porn_star_rep
#define dude_is_high                        drug_influence(dude_obj)
#define dude_found_geck                     global_var(GVAR_VAULT13_FOUND_GECK)


#define dude_stat_win(X,Y)                  ((do_check(dude_obj,X,Y)) > (do_check(self_obj,X,0)))
#define dude_stat_lose(X,Y)                 ((do_check(dude_obj,X,Y)) < (do_check(self_obj,X,0)))
#define dude_stat_tie(X,Y)                  ((do_check(dude_obj,X,Y)) == (do_check(self_obj,X,0)))
#define dude_can_see_self                   obj_can_see_obj(dude_obj,self_obj)

#define dude_item(x)                        obj_carrying_pid_obj(dude_obj, x)
#define dude_item_count(x)                  obj_is_carrying_obj_pid(dude_obj, x)

#define dude_is_addict                      (has_trait(TRAIT_TRAIT, dude_obj, TRAIT_drug_addict))

// spouse related
#define spouse_none                       (0)
#define spouse_female                     (1)
#define spouse_male                       (2)
#define dude_spouse_is_male               (global_var(GVAR_PLAYER_MARRIED) == spouse_male)
#define dude_spouse_is_female             (global_var(GVAR_PLAYER_MARRIED) == spouse_female)
#define dude_is_married                   (global_var(GVAR_PLAYER_MARRIED) != spouse_none)
#define set_dude_married                  if ((dude_is_married == false) and (dude_was_married == false)) then begin    \
                                             if (NAME == SCRIPT_MCDAVIN) then begin                                     \
                                                set_global_var(GVAR_PLAYER_MARRIED, spouse_male);                       \
                                             end else if (NAME == SCRIPT_MCMIRIA) then begin                                                             \
                                                set_global_var(GVAR_PLAYER_MARRIED, spouse_female);                     \
                                             end                                                                        \
                                          end                                                                           \
                                          debug_msg("set_dude_married")
#define dude_spouse_was_male              (global_var(GVAR_PLAYER_WAS_MARRIED) == spouse_male)
#define dude_spouse_was_female            (global_var(GVAR_PLAYER_WAS_MARRIED) == spouse_female)
#define dude_was_married                  (global_var(GVAR_PLAYER_WAS_MARRIED) != 0)
#define set_dude_was_married              if (dude_is_married == false) then begin                                      \
                                             set_global_var(GVAR_PLAYER_WAS_MARRIED, global_var(GVAR_PLAYER_MARRIED));  \
                                             set_global_var(GVAR_PLAYER_MARRIED, spouse_none);                          \
                                          end                                                                           \
                                          debug_msg("set_dude_was_married")

/***************************************************************
****************  Dialogue Information   ***********************
***************************************************************/
#define floater(x)              float_msg(self_obj, message_str(NAME,x), FLOAT_COLOR_NORMAL)
#define floater_rand(x,y)       floater(random(x,y))


/*
FLOAT_MSG_BLACK
FLOAT_MSG_PURPLE
FLOAT_MSG_NEAR_WHITE
FLOAT_MSG_BLUE
*/
#define FLOAT_COLOR_NORMAL          FLOAT_MSG_YELLOW
#define FLOAT_COLOR_SICK            FLOAT_MSG_GREEN
#define FLOAT_COLOR_BAD             FLOAT_MSG_RED
#define FLOAT_COLOR_GOOD            FLOAT_MSG_WHITE
#define FLOAT_COLOR_SFX             FLOAT_MSG_LIGHT_GREY
#define FLOAT_COLOR_SAD             FLOAT_MSG_GREY
#define FLOAT_COLOR_AFRAID          FLOAT_MSG_LIGHT_RED
#define FLOAT_COLOR_PAIN            FLOAT_MSG_LIGHT_GREY
#define FLOAT_COLOR_HIGH            FLOAT_MSG_PURPLE
#define FLOAT_COLOR_WHISPER         FLOAT_MSG_GREY


/*********************************************************
 General information dealing with a critter script
*********************************************************/
#define self_attack_dude                    if (critter_is_fleeing(self_obj)) then begin        \
                                               if (anim_busy(self_obj) == false) then begin     \
                                                  Flee_From_Dude                                \
                                               end                                              \
                                            end else attack(dude_obj)

#define self_name                           (obj_name(self_obj))
#define self_gender                         (get_critter_stat(self_obj,STAT_gender))
#define self_strength                       (get_critter_stat(self_obj,STAT_st))
#define self_perception                     (get_critter_stat(self_obj,STAT_pe))
#define self_endurance                      (get_critter_stat(self_obj,STAT_en))
#define self_charisma                       (get_critter_stat(self_obj,STAT_ch))
#define self_iq                             (get_critter_stat(self_obj,STAT_iq))
#define self_agility                        (get_critter_stat(self_obj,STAT_ag))
#define self_luck                           (get_critter_stat(self_obj,STAT_lu))

#define self_is_male                        (self_gender == GENDER_MALE)
#define self_is_female                      (self_gender == GENDER_FEMALE)
#define self_is_armed                       critter_is_armed(self_obj)
#define self_wearing_armor                  critter_wearing_armor(self_obj)

#define self_carrying_laser_pistol          ((obj_pid(critter_inven_obj(self_obj,INVEN_TYPE_LEFT_HAND)) == PID_LASER_PISTOL) or \
                                             (obj_pid(critter_inven_obj(self_obj,INVEN_TYPE_RIGHT_HAND)) == PID_LASER_PISTOL))

#define self_is_sneaking                    (using_skill(self_obj,SKILL_SNEAK))
#define self_is_walking                     (art_anim(obj_art_fid(self_obj)) == ANIM_walk)
#define self_is_running                     (art_anim(obj_art_fid(self_obj)) == ANIM_running)
#define self_is_poisoned                    (get_poison(self_obj))

#define self_cur_rot                        (has_trait(TRAIT_OBJECT,self_obj,OBJECT_CUR_ROT))
#define self_inv_rot                        ((self_cur_rot + 3)%6)
#define self_tile                           (tile_num(self_obj))
#define self_elevation                      (elevation(self_obj))

#define self_pid                            (obj_pid(self_obj))
#define self_team                           has_trait(TRAIT_OBJECT,self_obj,OBJECT_TEAM_NUM)
#define self_ai                             has_trait(TRAIT_OBJECT,self_obj,OBJECT_AI_PACKET)
#define self_visible                        obj_is_visible_flag(self_obj)

#define self_cur_hits                       (get_critter_stat(self_obj,STAT_current_hp))
#define self_max_hits                       (get_critter_stat(self_obj,STAT_max_hp))

#define self_mental_block                   (has_trait(TRAIT_PERK,self_obj,PERK_mental_block))
#define self_presence                       (has_trait(TRAIT_PERK,self_obj,PERK_presence))
#define self_awareness                      (has_trait(TRAIT_PERK,self_obj,PERK_bonus_awareness))
#define self_fortune_finder                 (has_trait(TRAIT_PERK,self_obj,PERK_fortune_finder))

#define self_caps                           (item_caps_total(self_obj))
#define self_fid                            (obj_art_fid(self_obj))

#define skill_success(x,y,z)                (is_success(roll_vs_skill(x,y,z)))
#define stat_success(x,y,z)                 (is_success(do_check(x,y,z)))

#define self_can_see_dude                   obj_can_see_obj(self_obj,dude_obj)
#define self_distance_from_dude             tile_distance(self_tile, dude_tile)
#define self_is_high                        drug_influence(self_obj)

#define self_item(x)                        obj_carrying_pid_obj(self_obj, x)
#define self_item_count(x)                  obj_is_carrying_obj_pid(self_obj, x)



#endif // COMMAND_H