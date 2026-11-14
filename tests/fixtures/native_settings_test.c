// The generated include contains the real screens.c parser and settings caller.
// Rendering and message transport are stubs; no Naomi hardware is accessed.
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "controls.h"
#include "sram.h"

static void *owned[64];
static unsigned int allocations, releases;

static void *settings_test_malloc(size_t size)
{
    void *data = malloc(size);
    assert(data != NULL);
    for (unsigned int i = 0; i < 64; i++)
    {
        if (owned[i] == NULL)
        {
            owned[i] = data;
            allocations++;
            return data;
        }
    }
    abort();
}

static void settings_test_free(void *data)
{
    if (data == NULL) return;
    for (unsigned int i = 0; i < 64; i++)
    {
        if (owned[i] == data)
        {
            owned[i] = NULL;
            releases++;
            free(data);
            return;
        }
    }
    // Detect double frees and attempts to free memory owned by somebody else.
    abort();
}

typedef struct { int width; } font_metrics_t;
static font_metrics_t font_get_text_metrics(font_t *font, char *text)
{
    (void)font; (void)text;
    return (font_metrics_t){0};
}
static int video_width(void) { return 640; }
static unsigned int rgb(int r, int g, int b) { return r + g + b; }
static void ta_draw_text(int x, int y, font_t *font, unsigned int color, char *text)
{
    (void)x; (void)y; (void)font; (void)color; (void)text;
}
controls_t get_controls(state_t *state, int reinit)
{
    (void)state; (void)reinit;
    return (controls_t){0};
}
int message_send(uint16_t type, void *data, unsigned int length)
{
    assert(type == MESSAGE_LOAD_SETTINGS && data != NULL && length == 4);
    return 0;
}

static uint8_t packet[512];
static unsigned int packet_length;
static int receive_result;
int menu_receive(const config_t *config, uint16_t *type, void **data, unsigned int *length)
{
    (void)config;
    if (receive_result != 0) return receive_result;
    *type = MESSAGE_LOAD_SETTINGS_DATA;
    *length = packet_length;
    *data = settings_test_malloc(packet_length);
    memcpy(*data, packet, packet_length);
    return 0;
}

#define malloc settings_test_malloc
#define free settings_test_free
#include "native_settings_source.c"
#undef malloc
#undef free

static void assert_no_allocations(void)
{
    assert(allocations == releases);
    for (unsigned int i = 0; i < 64; i++) assert(owned[i] == NULL);
}

static void put_u32(uint32_t value)
{
    memcpy(packet + packet_length, &value, sizeof(value));
    packet_length += sizeof(value);
}

static void put_setting(char name)
{
    packet[packet_length++] = 1;
    packet[packet_length++] = name;
    put_u32(1);                       // One selectable value, with a label.
    put_u32(42);
    packet[packet_length++] = 1;
    packet[packet_length++] = 'v';
    put_u32(42);                      // Current value.
    put_u32(0);                       // Conditional read-only setting.
    put_u32(0);                       // Not negated.
    put_u32(2);                       // Two nested dependency values.
    put_u32(42);
    put_u32(43);
}

int main(void)
{
    (void)expecting_boot;
    put_u32(7);
    packet[packet_length++] = 1;       // One patch.
    packet[packet_length++] = 1;
    packet[packet_length++] = 1;
    packet[packet_length++] = 'p';
    packet[packet_length++] = 1;       // Force settings enabled.
    packet[packet_length++] = 2;
    put_setting('S');
    put_setting('T');
    unsigned int system_end = packet_length;
    packet[packet_length++] = 2;
    put_setting('G');
    put_setting('H');
    unsigned int complete_length = packet_length;

    game_options_t *options = parse_game_options(packet, complete_length);
    assert(options != NULL && options->selected_game == 7);
    assert(options->patch_count == 1 && options->patches[0].enabled == 1);
    assert(options->system_settings_count == 2 && options->game_settings_count == 2);
    assert(options->system_settings[0].values[0].value == 42);
    assert(options->game_settings[1].read_only.values[1] == 43);
    free_game_options(options);
    assert_no_allocations();

    // Every prefix fails, including a missing game count after complete system
    // settings and a failed later setting after earlier nested allocations.
    for (unsigned int length = 0; length < complete_length; length++)
    {
        assert(parse_game_options(packet, length) == NULL);
        assert_no_allocations();
    }

    selected_game = 7;
    state_t state = {0};
    packet_length = system_end;
    assert(game_settings_load(&state, 1) == SCREEN_COMM_ERROR);
    assert(game_options == NULL);
    assert_no_allocations();

    packet_length = complete_length;
    uint32_t wrong_game = 8;
    memcpy(packet, &wrong_game, 4);
    assert(game_settings_load(&state, 1) == SCREEN_COMM_ERROR);
    assert(game_options == NULL);
    assert_no_allocations();

    uint32_t right_game = 7;
    memcpy(packet, &right_game, 4);
    assert(game_settings_load(&state, 1) == SCREEN_GAME_SETTINGS);
    assert(game_options != NULL && allocations > releases);
    free_game_options(game_options);
    game_options = NULL;
    assert_no_allocations();

    // No ACK arrived, but a complete response is available after the timeout.
    // The caller must keep the settings screen's ownership of that response.
    receive_result = -1;
    assert(game_settings_load(&state, 1) == SCREEN_GAME_SETTINGS_LOAD);
    state.animation_counter = MAX_WAIT_FOR_COMMS + 1.0;
    receive_result = 0;
    assert(game_settings_load(&state, 0) == SCREEN_GAME_SETTINGS);
    assert(game_options != NULL && allocations > releases);
    free_game_options(game_options);
    game_options = NULL;
    assert_no_allocations();

    // A missing response still times out and owns no settings allocations.
    receive_result = -1;
    state.animation_counter = 0.0;
    assert(game_settings_load(&state, 1) == SCREEN_GAME_SETTINGS_LOAD);
    state.animation_counter = MAX_WAIT_FOR_COMMS + 1.0;
    assert(game_settings_load(&state, 0) == SCREEN_COMM_ERROR);
    assert(game_options == NULL);
    assert_no_allocations();
    printf("PASS: %u settings prefixes cleaned up; caller failure, mismatch and success ownership; late response without ACK\n", complete_length);
    return 0;
}
