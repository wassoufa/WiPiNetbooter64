/* Dedicated BIOS-only reader. No address/length is accepted from the host. */
#include <stdint.h>
#include <stdlib.h>
#include <naomi/system.h>
#include <naomi/message/message.h>
#define READY 0x2100
#define READ 0x2101
#define DATA 0x2102
#define DONE 0x2103
#define CHUNK 4096
_Static_assert(BIOS_SIZE == 0x200000, "unexpected BIOS size");
static void run(void)
{
    message_init();
    if (message_send(READY, NULL, 0) != 0) { while (1) {} }
    unsigned int next = 0;
    while (next < 2 * (BIOS_SIZE / CHUNK))
    {
        uint16_t type = 0;
        uint8_t *data = NULL;
        unsigned int length = 0;
        if (message_recv(&type, (void **)&data, &length) != 0) { continue; }
        /* Sequential chunk index spans two separate complete physical reads. */
        uint32_t index = 0;
        if (length == 4 && data) {
            index = data[0] | (data[1] << 8) | (data[2] << 16) | ((uint32_t)data[3] << 24);
        }
        int valid = type == READ && length == 4 && index == next;
        free(data);
        if (!valid) { continue; }
        uint8_t reply[CHUNK + 4];
        for (unsigned int i = 0; i < 4; i++) { reply[i] = index >> (8 * i); }
        volatile const uint8_t *bios = (volatile const uint8_t *)(UNCACHED_MIRROR | BIOS_BASE);
        unsigned int offset = (index % (BIOS_SIZE / CHUNK)) * CHUNK;
        for (unsigned int i = 0; i < CHUNK; i++) { reply[4 + i] = bios[offset + i]; }
        if (message_send(DATA, reply, sizeof(reply)) != 0) { while (1) {} }
        next++;
    }
    message_send(DONE, NULL, 0);
    while (1) {}
}
void main(void) { run(); }
void test(void) { while (1) {} }
