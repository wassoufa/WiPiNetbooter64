#include <stdint.h>
int message_send(uint16_t type, void *data, unsigned int length);
int message_recv(uint16_t *type, void **data, unsigned int *length);
