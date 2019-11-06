#include "eeprom_fix.h"

void eeprom_update_byte_fixed(uint8_t *__p, uint8_t __value)
{
	eeprom_busy_wait();
	uint8_t value = eeprom_read_byte(__p);
	eeprom_busy_wait();

	if (value != __value)
		eeprom_write_block(&__value, (void *)__p, sizeof(uint8_t));
}

void eeprom_update_word_fixed(uint16_t *__p, uint16_t __value)
{
	eeprom_update_block_fixed(&__value, (void *)__p, sizeof(uint16_t));
}

void eeprom_update_block_fixed(void *__src, void *__dst, size_t __n)
{
	for(uint16_t i = 0; i < __n; i++)
	{
		eeprom_update_byte_fixed((uint8_t *)__dst + i, ((uint8_t *)__src)[i]);
	}
}
