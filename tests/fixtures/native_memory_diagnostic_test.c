#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <malloc.h>
#include <naomi/message/packet.h>

static uint32_t now;
static unsigned int allocations, allocated, sends, attempts, timer_stops;
static int fail_send, fail_clock, fail_alloc, bad_heap, no_texture, racing;
static packetlib_stats_t stats;
static char last[256];

static void *probe_malloc(size_t size)
{
    static char probe[4096];
    assert(size == sizeof(probe));
    allocations++;
    if (fail_alloc) { return 0; }
    allocated = 1;
    return probe;
}
static void probe_free(void *p) { if (p) { allocated = 0; } }
struct mallinfo mallinfo(void)
{
    struct mallinfo m = {100000, 1000 + (allocated && !bad_heap ? 4096 : 0), 90000};
    return m;
}
struct mallinfo ta_texture_mallinfo(void)
{
    struct mallinfo m = no_texture ? (struct mallinfo){0, 0, 0} : (struct mallinfo){8000000, 10000, 7990000};
    return m;
}
packetlib_stats_t packetlib_stats(void)
{
    if (racing) { stats.packets_received++; }
    return stats;
}
int timer_start(uint32_t duration) { assert(duration == UINT32_MAX); return fail_clock ? -1 : 1; }
uint32_t timer_elapsed(int clock) { assert(clock == 1); return now; }
void timer_stop(int clock) { assert(clock == 1); timer_stops++; }
int message_send(uint16_t type, void *data, unsigned int length)
{
    assert(type == 0x7FFE && length < sizeof(last));
    attempts++;
    if (fail_send) { return -4; }
    memcpy(last, data, length);
    last[length] = 0;
    sends++;
    fputs(last, stdout);
    return 0;
}

#define malloc probe_malloc
#define free probe_free
#include "memory-diagnostic.c"
#undef malloc
#undef free

static void frames(unsigned int count, unsigned int screen, unsigned int requested, unsigned int input)
{
    while (count--)
    {
        now += 16667;
        md_controls(input);
        md_selection(7);
        md_screen(screen, requested, 7);
        md_frame();
    }
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    fail_send = strcmp(argv[1], "send-failure") == 0;
    fail_clock = strcmp(argv[1], "clock-failure") == 0;
    fail_alloc = strcmp(argv[1], "allocation-failure") == 0;
    bad_heap = strcmp(argv[1], "bad-heap") == 0;
    no_texture = strcmp(argv[1], "no-texture") == 0;
    racing = strcmp(argv[1], "calibration-race") == 0;
    frames(2 * MD_SETTLE_FRAMES, 0, 0, 0);
    if (fail_clock) { assert(attempts == 0 && allocations == 0); return 0; }
    assert(allocations == 1);
    if (racing)
    {
        racing = 0;
        frames(MD_SETTLE_FRAMES, 0, 0, 0);
        assert(sends == 1 && !heap_calibrated && allocations == 1);
        return 0;
    }
    if (fail_send)
    {
        frames(1000, 0, 0, 0);
        assert(attempts == 1 && sends == 0 && timer_stops == 1);
        return 0;
    }
    assert(sends == 1);
    if (fail_alloc || bad_heap || no_texture) { return 0; }
    if (strcmp(argv[1], "overflow") == 0)
    {
        for (unsigned int i = 1; i < MD_MAX_RECORDS + 2; i++)
        {
            unsigned int screen = i % 2 ? 3 : 0;
            frames(MD_SETTLE_FRAMES, screen, screen, 0);
        }
        assert(sends == MD_MAX_RECORDS && stopped && timer_stops == 1);
        return 0;
    }
    if (strcmp(argv[1], "clock-wrap") == 0)
    {
        now = 0;
        md_frame();
        assert(stopped && timer_stops == 1 && sends == 1);
        return 0;
    }
    if (strcmp(argv[1], "save-route") == 0)
    {
        frames(MD_SETTLE_FRAMES, 3, 3, 0);
        assert(sends == 2);
        frames(1, 3, 4, 1);
        frames(MD_SETTLE_FRAMES, 0, 0, 0);
        assert(stopped && timer_stops == 1 && sends == 2);
        return 0;
    }
    frames(MD_SETTLE_FRAMES, 0, 3, 0);
    frames(MD_SETTLE_FRAMES, 3, 3, 1);
    assert(sends == 1);
    stats.send_in_progress = 1;
    frames(MD_SETTLE_FRAMES, 3, 3, 0);
    assert(sends == 1);
    stats.send_in_progress = 0;
    racing = 1;
    frames(MD_SETTLE_FRAMES, 3, 3, 0);
    assert(sends == 1);
    racing = 0;
    frames(MD_SETTLE_FRAMES, 3, 3, 0);
    assert(sends == 2);
    frames(1, 3, 0, 1);
    frames(MD_SETTLE_FRAMES, 0, 0, 0);
    assert(sends == 3 && cycle == 1);
    now += MD_IDLE_US;
    stats.packets_pending_send = 1;
    frames(MD_SETTLE_FRAMES, 0, 0, 0);
    assert(sends == 3);
    stats.packets_pending_send = 0;
    frames(MD_SETTLE_FRAMES, 0, 0, 0);
    assert(sends == 4 && allocations == 1);
    frames(MD_SETTLE_FRAMES, 0, 0, 0);
    assert(sends == 4);
    return 0;
}
