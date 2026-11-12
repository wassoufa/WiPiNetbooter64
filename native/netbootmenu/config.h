#ifndef __CONFIG_H
#define __CONFIG_H

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <naomi/eeprom.h>
#include <naomi/video.h>
#include <naomi/ta.h>

#include "protocol.h"

typedef struct
{
    int scroll;
    int check;
    int change;
} sounds_t;

typedef struct
{
    eeprom_t *settings;
    config_t *config;
    double fps;
    double animation_counter;
    double test_error_counter;
    font_t *font_18pt;
    font_t *font_12pt;
    texture_description_t *sprite_up;
    texture_description_t *sprite_down;
    texture_description_t *sprite_cursor;
    sounds_t sounds;
} state_t;

config_t *get_config();
int menu_save_config(config_t *config);
games_list_t *get_games_list(unsigned int *count);
uint8_t *get_fallback_font(unsigned int *size);

#ifdef __cplusplus
}
#endif

#endif
