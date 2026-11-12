#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <naomi/system.h>
#include <naomi/message/message.h>
#include "sram.h"

_Static_assert(SRAM_SIZE == MENU_SRAM_SIZE, "Host SRAM image size must match hardware");

static void *sram_memory(void)
{
    // Match libnaomi's SRAM driver: use the uncached mirror for raw SRAM access.
    return (void *)(UNCACHED_MIRROR + SRAM_BASE);
}

int menu_backup_sram(const config_t *config)
{
    if (!config->sram_save)
    {
        return 0;
    }
    void *snapshot = malloc(MENU_SRAM_SIZE);
    if (!snapshot)
    {
        return -1;
    }
    memcpy(snapshot, sram_memory(), MENU_SRAM_SIZE);
    // message_send copies/queues the payload before returning.
    int result = message_send(MESSAGE_SRAM_READ, snapshot, MENU_SRAM_SIZE);
    free(snapshot);
    return result;
}

int menu_receive(const config_t *config, uint16_t *type, void **data, unsigned int *length)
{
    int result = message_recv(type, data, length);
    if (result != 0 || *type != MESSAGE_SRAM_WRITE)
    {
        return result;
    }
    // A truncated, oversized or disabled restore must never touch battery SRAM.
    if (config->sram_save && *data && *length == MENU_SRAM_SIZE)
    {
        memcpy(sram_memory(), *data, MENU_SRAM_SIZE);
    }
    else
    {
        printf("SRAM restore ignored (enabled=%u, bytes=%u).\n", (unsigned int)config->sram_save, *length);
    }
    free(*data);
    *data = NULL;
    *length = 0;
    *type = 0;
    return -1;
}
