// Exercise the actual main_menu with deterministic input/time and no hardware.
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "controls.h"
#include "sram.h"

#define SPEAKER_LEFT 1
#define SPEAKER_RIGHT 2
typedef struct { int width, height; } font_metrics_t;
static controls_t input;
static unsigned int messages, sent_game;
static int expected_reinit;

static int video_width(void) { return 640; }
static int video_height(void) { return 480; }
static unsigned int rgb(int r, int g, int b) { return r + g + b; }
static font_metrics_t font_get_text_metrics(font_t *font, char *text)
{
    (void)font; (void)text;
    return (font_metrics_t){0};
}
static void ta_draw_text(int x, int y, font_t *font, unsigned int color, char *text)
{
    (void)x; (void)y; (void)font; (void)color; (void)text;
}
static void display_sprite(int x, int y, texture_description_t *texture)
{
    (void)x; (void)y; (void)texture;
}
static void audio_play_registered_sound(int sound, int speakers, double volume)
{
    (void)sound; (void)speakers; (void)volume;
}
games_list_t *get_games_list(unsigned int *count)
{
    static games_list_t games[3] = {{.name = "First"}, {.name = "Second"}, {.name = "Third"}};
    *count = 3;
    return games;
}
controls_t get_controls(state_t *state, int reinit)
{
    (void)state;
    assert(reinit == expected_reinit);
    return input;
}
int message_send(uint16_t type, void *data, unsigned int length)
{
    assert(type == MESSAGE_SELECTION && data != NULL && length == 4);
    memcpy(&sent_game, data, 4);
    messages++;
    return 0;
}
int menu_receive(const config_t *config, uint16_t *type, void **data, unsigned int *length)
{
    (void)config; (void)type; (void)data; (void)length;
    return -1;
}

// The inherited renderer passes an unsigned subtraction to abs(). Keep the
// production expression intact while allowing this control-flow host fixture.
#ifdef __clang__
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wabsolute-value"
#endif
#include "native_start_source.c"
#ifdef __clang__
#pragma clang diagnostic pop
#endif

static unsigned int frame(state_t *state, double time, controls_t controls, int reinit)
{
    state->animation_counter = time;
    input = controls;
    expected_reinit = reinit;
    return main_menu(state, reinit);
}

static void begin_hold(state_t *state)
{
    selected_game = -1;
    messages = 0;
    state->test_error_counter = 12.0;
    assert(frame(state, 0.0, (controls_t){0}, 1) == SCREEN_MAIN_MENU);
    assert(selected_game == 1 && state->test_error_counter == 0.0);
    assert(frame(state, 0.0, (controls_t){.start_pressed = 1}, 0) == SCREEN_MAIN_MENU);
    assert(messages == 0);
}

int main(void)
{
    config_t config = {.boot_selection = 1, .disable_sound = 1};
    state_t state = {.config = &config};
    const double release_times[] = {0.125, 0.999999, 1.0, 1.000001, 1.75};
    for (unsigned int i = 0; i < sizeof(release_times) / sizeof(release_times[0]); i++)
    {
        begin_hold(&state);
        // Directional input during a hold cannot change the selected game.
        assert(frame(&state, 0.5 * release_times[i], (controls_t){.down_pressed = 1}, 0) == SCREEN_MAIN_MENU);
        unsigned int screen = frame(&state, release_times[i], (controls_t){.start_released = 1}, 0);
        if (release_times[i] < 1.0)
        {
            assert(screen == SCREEN_MAIN_MENU && messages == 1 && sent_game == 1);
            // Repeated release/press/navigation while awaiting boot cannot resend.
            assert(frame(&state, release_times[i], (controls_t){.start_released = 1, .down_pressed = 1}, 0) == SCREEN_MAIN_MENU);
            assert(frame(&state, release_times[i], (controls_t){.start_pressed = 1}, 0) == SCREEN_MAIN_MENU);
            assert(messages == 1);
        }
        else
        {
            assert(screen == SCREEN_GAME_SETTINGS_LOAD && messages == 0 && selected_game == 1);
        }
    }

    begin_hold(&state);
    assert(frame(&state, 0.999999, (controls_t){0}, 0) == SCREEN_MAIN_MENU);
    assert(frame(&state, 1.0, (controls_t){0}, 0) == SCREEN_GAME_SETTINGS_LOAD);
    assert(messages == 0 && selected_game == 1);

    // Returning to the menu clears the previous hold/lock and permits navigation.
    assert(frame(&state, 2.0, (controls_t){0}, 1) == SCREEN_MAIN_MENU);
    assert(frame(&state, 2.0, (controls_t){.down_pressed = 1}, 0) == SCREEN_MAIN_MENU);
    assert(frame(&state, 2.0, (controls_t){.start_pressed = 1}, 0) == SCREEN_MAIN_MENU);
    assert(frame(&state, 2.25, (controls_t){.start_released = 1}, 0) == SCREEN_MAIN_MENU);
    assert(messages == 1 && sent_game == 2);

    // Reinit also resets the boot-in-progress lock; a stray release cannot launch.
    assert(frame(&state, 3.0, (controls_t){.start_released = 1}, 1) == SCREEN_MAIN_MENU);
    assert(messages == 1);
    assert(frame(&state, 3.0, (controls_t){.start_pressed = 1}, 0) == SCREEN_MAIN_MENU);
    assert(frame(&state, 4.0, (controls_t){.start_released = 1}, 0) == SCREEN_GAME_SETTINGS_LOAD);
    assert(messages == 1 && selected_game == 1);
    puts("PASS: Start release boundary, continuous hold, lock and reinit");
    return 0;
}
