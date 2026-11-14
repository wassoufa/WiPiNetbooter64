#ifndef WIPI_MENU_SRAM_H
#define WIPI_MENU_SRAM_H

#include "protocol.h"

// Called once on menu startup, before any SRAM restore from the host.
int menu_backup_sram(const config_t *config);

// Consume SRAM restoration in any screen; pass other messages to that screen.
// Matches message_recv's success/no-message convention. Owns/frees consumed data.
int menu_receive(const config_t *config, uint16_t *type, void **data, unsigned int *length);

#endif
