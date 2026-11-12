// Execute the real wire/SRAM code with message I/O and battery SRAM replaced.
// Other translation units use these wrappers so every SRAM allocation is counted.
#undef malloc
#undef free
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "config.h"
#include "sram.h"

unsigned char test_sram_storage[MENU_SRAM_SIZE + 2] = {0};
static unsigned char sent[MENU_SRAM_SIZE];
static unsigned int sent_length, sends, incoming_length;
static uint16_t sent_type, incoming_type;
static int send_result, pending, incoming_null;
static unsigned int allocations, releases, fail_allocation;
static void *owned_allocation;

void *native_test_malloc(size_t length)
{
    assert(owned_allocation == NULL);
    if (fail_allocation)
    {
        fail_allocation = 0;
        return NULL;
    }
    owned_allocation = malloc(length);
    assert(owned_allocation != NULL);
    allocations++;
    return owned_allocation;
}

void native_test_free(void *data)
{
    if (!data) return;
    assert(data == owned_allocation);
    free(data);
    owned_allocation = NULL;
    releases++;
}

static void assert_no_allocations(void)
{
    assert(owned_allocation == NULL && allocations == releases);
}

int message_send(uint16_t type, void *data, unsigned int length)
{
    assert(length <= sizeof(sent));
    sent_type = type;
    sent_length = length;
    memcpy(sent, data, length);
    sends++;
    return send_result;
}

int message_recv(uint16_t *type, void **data, unsigned int *length)
{
    if (!pending) return -1;
    pending = 0;
    *type = incoming_type;
    *length = incoming_length;
    *data = incoming_null ? NULL : native_test_malloc(incoming_length);
    if (*data) memset(*data, 0x57, incoming_length);
    return 0;
}

static void receive(config_t *config, unsigned int length, int null_data)
{
    uint16_t type = 0;
    void *data = NULL;
    unsigned int size = 0;
    incoming_type = MESSAGE_SRAM_WRITE;
    incoming_length = length;
    incoming_null = null_data;
    pending = 1;
    assert(menu_receive(config, &type, &data, &size) == -1);
    assert(data == NULL && size == 0 && type == 0);
    assert_no_allocations();
}

int main(int argc, char **argv)
{
    assert(argc == 2);
    config_t config = {0};
    if (strcmp(argv[1], "config") == 0)
    {
        assert(fread(&config, 1, sizeof(config), stdin) == MENU_CONFIG_SIZE);
        assert(config.game_list_offset == 64 && config.games_count == 2);
        assert(config.sram_save <= 1);
        assert(config.joy1_hcenter == 128 && config.joy2_hcenter == 126);
        assert(config.fallback_font_offset == 336 && config.fallback_font_size == 4);
        assert(config.force_players == 2);
        assert(menu_save_config(&config) == 0);
        assert(sent_type == MESSAGE_SAVE_CONFIG && sent_length == MENU_CONFIG_SIZE);
        assert(fwrite(sent, 1, sent_length, stdout) == MENU_CONFIG_SIZE);
        return 0;
    }

    for (unsigned int cycle = 0; cycle < 1000; cycle++)
    {
        memset(test_sram_storage, 0xAC, sizeof(test_sram_storage));
        sends = 0;
        config.sram_save = 0;
        send_result = 0;
        assert(menu_backup_sram(&config) == 0 && sends == 0);
        assert_no_allocations();
        config.sram_save = 1;
        assert(menu_backup_sram(&config) == 0 && sends == 1);
        assert(sent_type == MESSAGE_SRAM_READ && sent_length == MENU_SRAM_SIZE);
        assert(memcmp(sent, &test_sram_storage[1], MENU_SRAM_SIZE) == 0);
        assert_no_allocations();
        send_result = -4;
        assert(menu_backup_sram(&config) == -4);
        assert_no_allocations();
        fail_allocation = 1;
        assert(menu_backup_sram(&config) == -1 && sends == 2);
        assert(fail_allocation == 0);
        assert_no_allocations();

        // Disabled and malformed packets leave the entire SRAM and guards intact.
        config.sram_save = 0;
        receive(&config, MENU_SRAM_SIZE, 0);
        config.sram_save = 1;
        receive(&config, MENU_SRAM_SIZE - 1, 0);
        receive(&config, MENU_SRAM_SIZE + 1, 0);
        receive(&config, MENU_SRAM_SIZE, 1);
        for (unsigned int i = 0; i < sizeof(test_sram_storage); i++) assert(test_sram_storage[i] == 0xAC);
        receive(&config, MENU_SRAM_SIZE, 0);
        for (unsigned int i = 1; i <= MENU_SRAM_SIZE; i++) assert(test_sram_storage[i] == 0x57);
        assert(test_sram_storage[0] == 0xAC && test_sram_storage[MENU_SRAM_SIZE + 1] == 0xAC);

        // Non-SRAM messages are still owned by the current screen.
        pending = 1;
        incoming_type = MESSAGE_LOAD_PROGRESS;
        incoming_length = 8;
        incoming_null = 0;
        uint16_t type = 0;
        void *data = NULL;
        unsigned int length = 0;
        assert(menu_receive(&config, &type, &data, &length) == 0);
        assert(type == MESSAGE_LOAD_PROGRESS && length == 8 && data != NULL);
        assert(owned_allocation == data && allocations == releases + 1);
        native_test_free(data);
        assert_no_allocations();
        assert(menu_receive(&config, &type, &data, &length) == -1);
        assert_no_allocations();
    }
    assert(allocations == 7000 && releases == 7000);
    puts("PASS: 1000 SRAM cycles, 7000 allocations released, allocation/send failure and caller ownership");
    return 0;
}
