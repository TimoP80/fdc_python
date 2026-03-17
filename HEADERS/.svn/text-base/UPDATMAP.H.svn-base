#ifndef UPDATMAP_H
#define UPDATMAP_H

// Lighting Information
#define DAY_LIGHT                       (100)
#define CAVERN_LIGHT                    (50)
#define NIGHT_LIGHT                     (40)
#define INDOOR_LIGHT                    (60)
#define BASEMENT_LIGHT                  (50)

#define Dawn_str                        (message_str(SCRIPT_SUN,get_month*100+get_day))
#define Dusk_str                        (message_str(SCRIPT_SUN,get_month*100+get_day+50))

variable Dawn;
variable Dusk;
variable c := 0;

#define Lighting                        while(c <= 2400) do begin                                                               \
                                           if(Dawn_str == c) then begin                                                         \
                                              Dawn := c;                                                                        \
                                              c := 2500;                                                                        \
                                           end                                                                                  \
                                           c += 1;                                                                              \
                                        end                                                                                     \
                                        c := 0;                                                                                 \
                                        while(c <= 2400) do begin                                                               \
                                           if(Dusk_str == c) then begin                                                         \
                                              Dusk := c;                                                                        \
                                              c := 2500;                                                                        \
                                           end                                                                                  \
                                           c += 1;                                                                              \
                                        end                                                                                     \
                                        if((game_time_hour >= Dawn) AND (game_time_hour < (Dawn + 100))) then begin             \
                                           if(game_time_hour - Dawn > 60) then begin                                            \
                                              set_light_level(NIGHT_LIGHT + game_time_hour - Dawn - 40);                        \
                                           end else begin                                                                       \
                                              set_light_level(NIGHT_LIGHT + game_time_hour - Dawn);                             \
                                           end                                                                                  \
                                        end else if((game_time_hour >= (Dawn + 100)) AND (game_time_hour < Dusk)) then begin    \
                                           set_light_level(DAY_LIGHT);                                                          \
                                        end else if((game_time_hour >= Dusk) AND (game_time_hour < (Dusk + 100))) then begin    \
                                           if(game_time_hour - Dusk > 60) then begin                                            \
                                              set_light_level(DAY_LIGHT - game_time_hour + Dusk + 40);                          \
                                           end else begin                                                                       \
                                              set_light_level(DAY_LIGHT - game_time_hour + Dusk);                               \
                                           end                                                                                  \
                                        end else begin                                                                          \
                                           set_light_level(NIGHT_LIGHT);                                                        \
                                        end

#endif // UPDATMAP_H
