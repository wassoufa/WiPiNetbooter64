#ifndef MEMORY_DIAGNOSTIC_H
#define MEMORY_DIAGNOSTIC_H
#include <stdint.h>

#define MD_SETTLE_FRAMES 120
#define MD_IDLE_US 60000000ULL
#define MD_MAX_RECORDS 96

void md_controls(unsigned int busy);
void md_selection(unsigned int selected);
void md_screen(unsigned int rendered, unsigned int next, int game);
void md_frame(void);
#endif
