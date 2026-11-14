/* Included only in the isolated B4 diagnostic build. */
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <naomi/ta.h>
#include <naomi/timer.h>
#include <naomi/message/message.h>
#include <naomi/message/packet.h>
#include "memory-diagnostic.h"

static unsigned int busy, rendered, next, quiet, sequence, cycle, stopped;
static unsigned int observed = ~0U, pending, settings_seen;
static int game;
static unsigned int main_game;
static unsigned int calibration_done, heap_calibrated;
static uint64_t guest_us, last_sample_us;
static int clock_handle = -1;

void md_controls(unsigned int value)
{
    busy |= value;
}

void md_screen(unsigned int current, unsigned int requested, int selected)
{
    rendered = current;
    next = requested;
    game = current == 0 ? (int)main_game : selected;
}

void md_selection(unsigned int selected) { main_game = selected; }

static unsigned int valid(struct mallinfo m)
{
    return m.arena > 0 && (uint64_t)m.uordblks <= (uint64_t)m.arena &&
        (uint64_t)m.fordblks <= (uint64_t)m.arena &&
        (uint64_t)m.uordblks + (uint64_t)m.fordblks <= (uint64_t)m.arena;
}

void md_frame(void)
{
    if (stopped) { busy = 0; return; }
    if (clock_handle < 0)
    {
        clock_handle = timer_start(UINT32_MAX);
        if (clock_handle < 0) { stopped = 1; busy = 0; return; }
    }
    uint32_t elapsed_us = timer_elapsed(clock_handle);
    if (elapsed_us == UINT32_MAX || elapsed_us < guest_us)
    {
        stopped = 1;
        timer_stop(clock_handle);
        busy = 0;
        return;
    }
    guest_us = elapsed_us;

    if (rendered == 3 && next != 3)
    {
        if (next == 0) { settings_seen = 1; }
        else { stopped = 1; timer_stop(clock_handle); busy = 0; return; }
    }

    /* Screen IDs are the existing screens.c constants: main=0, settings=3. */
    if (rendered != observed)
    {
        if (rendered == 3) { pending = 2; }
        else if (rendered == 0)
        {
            pending = settings_seen ? 3 : 1;
            if (settings_seen) { cycle++; settings_seen = 0; }
        }
        else { pending = 0; }
        observed = rendered;
        quiet = 0;
    }

    if (busy || rendered != next || (rendered != 0 && rendered != 3))
    {
        quiet = 0;
        busy = 0;
        return;
    }
    busy = 0;
    packetlib_stats_t packets = packetlib_stats();
    if (packets.packets_pending_send || packets.packets_pending_receive ||
        packets.send_in_progress || packets.receive_in_progress)
    {
        quiet = 0;
        return;
    }
    if (quiet < MD_SETTLE_FRAMES) { quiet++; }
    if (quiet < MD_SETTLE_FRAMES) { return; }
    if (!pending && (rendered != 0 || guest_us - last_sample_us < MD_IDLE_US)) { return; }

    if (!calibration_done)
    {
        calibration_done = 1;
        struct mallinfo before = mallinfo();
        void *probe = malloc(4096);
        unsigned int allocated = probe != 0;
        struct mallinfo during = mallinfo();
        free(probe);
        struct mallinfo after = mallinfo();
        packetlib_stats_t end = packetlib_stats();
        heap_calibrated = allocated && valid(before) && valid(during) && valid(after) &&
            (uint64_t)during.uordblks >= (uint64_t)before.uordblks + 4096 &&
            after.uordblks == before.uordblks && memcmp(&packets, &end, sizeof(packets)) == 0;
        /* Observer allocation may retain arena space; settle again, never retry. */
        quiet = 0;
        return;
    }

    /* Snapshot first. Formatting and the queued stdout packet allocate afterward. */
    struct mallinfo heap = mallinfo();
    struct mallinfo texture = ta_texture_mallinfo();
    packetlib_stats_t after = packetlib_stats();
    if (memcmp(&packets, &after, sizeof(packets)) != 0) { quiet = 0; return; }
    unsigned int event = pending ? pending : 4;
    if (sequence == MD_MAX_RECORDS - 1) { event = 5; stopped = 1; }
    char line[256];
    int length = snprintf(line, sizeof(line),
        "B4M1,%u,%u,%u,%u,%d,%llu,%u,%llu,%llu,%llu,%u,%llu,%llu,%llu\n",
        ++sequence, cycle, event, rendered, game, (unsigned long long)guest_us,
        heap_calibrated && valid(heap), (unsigned long long)heap.arena, (unsigned long long)heap.uordblks, (unsigned long long)heap.fordblks,
        valid(texture), (unsigned long long)texture.arena, (unsigned long long)texture.uordblks, (unsigned long long)texture.fordblks);
    /* One stdout-protocol packet, checked directly: printf masks send failures. */
    if (length < 0 || (unsigned int)length >= sizeof(line) ||
        message_send(0x7FFE, line, (unsigned int)length) != 0)
    {
        stopped = 1;
    }
    pending = 0;
    last_sample_us = guest_us;
    quiet = 0;
    if (stopped) { timer_stop(clock_handle); }
}
