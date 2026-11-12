#ifndef WIPI_MENU_PROTOCOL_H
#define WIPI_MENU_PROTOCOL_H

#include <stdint.h>
#include <stddef.h>

#define MENU_CONFIG_SIZE 64
#define MENU_SRAM_SIZE 0x8000

#define MESSAGE_SELECTION 0x1000
#define MESSAGE_LOAD_SETTINGS 0x1001
#define MESSAGE_LOAD_SETTINGS_ACK 0x1002
#define MESSAGE_LOAD_SETTINGS_DATA 0x1005
#define MESSAGE_LOAD_PROGRESS 0x1009
#define MESSAGE_UNPACK_PROGRESS 0x100A
#define MESSAGE_SAVE_SETTINGS_DATA 0x1007
#define MESSAGE_SAVE_SETTINGS_ACK 0x1008
#define MESSAGE_SAVE_CONFIG 0x1003
#define MESSAGE_SAVE_CONFIG_ACK 0x1004

#define MESSAGE_SRAM_READ 0x2003
#define MESSAGE_SRAM_WRITE 0x2004

typedef struct __attribute__((__packed__))
{
    char name[128];
    uint8_t serial[4];
    uint32_t id;
} games_list_t;

typedef struct __attribute__((__packed__))
{
    uint32_t game_list_offset;
    uint32_t games_count;
    uint32_t enable_analog;
    uint32_t enable_debug;
    uint32_t boot_selection;
    uint32_t system_region;
    uint32_t use_filenames;
    uint32_t disable_sound;
    uint32_t sram_save;
    uint8_t joy1_hcenter;
    uint8_t joy1_vcenter;
    uint8_t joy2_hcenter;
    uint8_t joy2_vcenter;
    uint8_t joy1_hmin;
    uint8_t joy1_hmax;
    uint8_t joy1_vmin;
    uint8_t joy1_vmax;
    uint8_t joy2_hmin;
    uint8_t joy2_hmax;
    uint8_t joy2_vmin;
    uint8_t joy2_vmax;
    uint32_t fallback_font_offset;
    uint32_t fallback_font_size;
    uint32_t force_players;
    uint8_t reserved[4];
} config_t;


_Static_assert(sizeof(config_t) == MENU_CONFIG_SIZE, "Host configuration must be 64 bytes");
_Static_assert(sizeof(games_list_t) == 136, "Host game records must be 136 bytes");
_Static_assert(offsetof(config_t, sram_save) == 32, "SRAM flag offset");
_Static_assert(offsetof(config_t, joy1_hcenter) == 36, "Calibration offset");
_Static_assert(offsetof(config_t, fallback_font_offset) == 48, "Font offset");
_Static_assert(offsetof(config_t, force_players) == 56, "Player count offset");

#endif
