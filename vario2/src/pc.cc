/*
 * pc.cc
 *
 *  Created on: 7.11.2013
 *      Author: horinek
 */

#include "pc.h"
#include "bui.h"
#include "cfg.h"

extern float temperature;
extern float altitude0;

extern float ram_sea_level_Pa;
extern float ram_kalman_q;
extern float ram_kalman_r;
extern float ram_kalman_p;
extern float raw_pressure;
extern float pressure;
extern float climb;

extern bool meas_new_sample;

Usart usb_uart;
Usart gps_uart;

CreateStdOut(usart_out, usb_uart.Write);


#define PC_IDLE	0
#define PC_LEN	1
#define PC_DATA	2
#define PC_CRC	3

#define PC_START_BYTE	0xAA
#define PC_MAX_LEN		16
#define PC_MAX_TIME		200

#define PC_CRC_KEY		0xD5

uint8_t pc_parser_step = PC_IDLE;
uint8_t pc_data[16];
uint32_t pc_last_byte = 0;
uint8_t pc_index = 0;
uint8_t pc_len = 0;
uint8_t pc_crc;

bool pc_mode = false;

extern Timer meas_timer;
extern void buzzer_set_tone(uint16_t);
extern void buzzer_step();
extern bool buzzer_override;
extern void auto_off_reset();


void pc_init()
{
	SetStdOut(usart_out);

	if (usb_connected)
	{
		GpioSetDirection(USB_UART_TX, OUTPUT);
		GpioWrite(USB_UART_TX, HIGH);

		//start uart
		PR.PRPD = 0b01001101; //usb_uart enabled
		usb_uart.Init(usartD0, 115200ul, 128, 64);
		usb_uart.SetInterruptPriority(LOW);
	}
}

void pc_encode(uint8_t cmd, uint8_t len, uint8_t * data)
{
	uint8_t crc;

	usb_uart.Write(PC_START_BYTE);

	usb_uart.Write(len + 1);
	crc = CalcCRC(0x00, PC_CRC_KEY, len + 1);

	usb_uart.Write(cmd);
	crc = CalcCRC(crc, PC_CRC_KEY, cmd);

	for (uint8_t i = 0; i < len; i++)
	{
		usb_uart.Write(data[i]);
		crc = CalcCRC(crc, PC_CRC_KEY, data[i]);
	}
	usb_uart.Write(crc);
}

#define CMD_INFO		0x00
#define CMD_PING		0x01
#define CMD_GET_VERSION	0x02
#define CMD_GET_VALUE	0x03
#define CMD_SET_VALUE	0x04
#define CMD_RESET		0x05
#define CMD_DEMO		0x06

void pc_get_value()
{
	uint8_t value_id = pc_data[1];
	uint8_t data[16];
	byte2 b2;
	uint8_t index;

	data[0] = value_id;

	switch (value_id)
	{
		case (0x00): //volume
			data[1] = cfg.buzzer_volume;
			pc_encode(CMD_GET_VALUE, 2, data);
		break;

		case (0x01): //auto power off
			b2.uint16 = cfg.auto_poweroff;
			data[1] = b2.uint8[0];
			data[2] = b2.uint8[1];
			pc_encode(CMD_GET_VALUE, 3, data);
		break;

		case (0x02): //active profile
			data[1] = cfg.selected_profile;
			pc_encode(CMD_GET_VALUE, 2, data);
		break;

		case (0x03): //silent start
			data[1] = cfg.supress_startup;
			pc_encode(CMD_GET_VALUE, 2, data);
		break;

		case (0x04): //fluid audio
			data[1] = cfg.fluid_update;
			pc_encode(CMD_GET_VALUE, 2, data);
		break;

		case (0x05): //lift_1
		case (0x06): //lift_2
		case (0x07): //lift_3
		case (0x08): //lift_4
		case (0x09): //lift_5
			index = value_id - 0x05;
			b2.int16 = cfg.lift_steps[index];
			data[1] = b2.uint8[0];
			data[2] = b2.uint8[1];
			pc_encode(CMD_GET_VALUE, 3, data);
		break;

		case (0x0A): //sink_1
		case (0x0B): //sink_2
		case (0x0C): //sink_3
		case (0x0D): //sink_4
		case (0x0E): //sink_5
			index = value_id - 0x0A;
			b2.int16 = cfg.sink_steps[index];
			data[1] = b2.uint8[0];
			data[2] = b2.uint8[1];
			pc_encode(CMD_GET_VALUE, 3, data);
		break;

		case (0x0F): //profile_lift_index
			data[1] = prof.lift_treshold;
			pc_encode(CMD_GET_VALUE, 2, data);
		break;

		case (0x10): //profile_sink_index
			data[1] = prof.sink_treshold;
			pc_encode(CMD_GET_VALUE, 2, data);
		break;

		default: //profile
			if (value_id >= 0x84)
			{
				index = value_id - 0x84;
				if (index < 41) //freq 84 - AC
				{
					b2.int16 = prof.buzzer_freq[index];
					data[1] = b2.uint8[0];
					data[2] = b2.uint8[1];
					pc_encode(CMD_GET_VALUE, 3, data);
					break;
				}
				if (index < 41 * 2) //pause AD - D5
				{
					index -= 41;
					b2.int16 = prof.buzzer_pause[index];
					data[1] = b2.uint8[0];
					data[2] = b2.uint8[1];
					pc_encode(CMD_GET_VALUE, 3, data);
					break;
				}
				if (index < 41 * 3) //length D6 - FE
				{
					index -= 41 * 2;
					b2.int16 = prof.buzzer_length[index];
					data[1] = b2.uint8[0];
					data[2] = b2.uint8[1];
					pc_encode(CMD_GET_VALUE, 3, data);
					break;
				}
			}
	}
}

void pc_set_value()
{
	uint8_t value_id = pc_data[1];
	byte2 b2;
	uint8_t index;


	switch (value_id)
	{
		case (0x00): //volume
			cfg.buzzer_volume = pc_data[2];
			eeprom_busy_wait();
			eeprom_update_byte_fixed(&ee.cfg.buzzer_volume, cfg.buzzer_volume);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		case (0x01): //auto power off
			b2.uint8[0] = pc_data[2];
			b2.uint8[1] = pc_data[3];
			cfg.auto_poweroff = b2.uint16;
			eeprom_busy_wait();
			eeprom_update_word_fixed(&ee.cfg.auto_poweroff, cfg.auto_poweroff);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		case (0x02): //active profile
			cfg.selected_profile = pc_data[2];
			DEBUG("active: %d", cfg.selected_profile);
			eeprom_busy_wait();
			eeprom_update_byte_fixed(&ee.cfg.selected_profile, cfg.selected_profile);
			LoadProfile();
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		case (0x03): //silent start
			cfg.supress_startup = pc_data[2];
			eeprom_busy_wait();
			eeprom_update_byte_fixed((uint8_t *)&ee.cfg.supress_startup, cfg.supress_startup);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		case (0x04): //fluid audio
			cfg.fluid_update = pc_data[2];
			eeprom_busy_wait();
			eeprom_update_byte_fixed((uint8_t *)&ee.cfg.fluid_update, cfg.fluid_update);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		case (0x05): //lift_1
		case (0x06): //lift_2
		case (0x07): //lift_3
		case (0x08): //lift_4
		case (0x09): //lift_5
			index = value_id - 0x05;
			b2.uint8[0] = pc_data[2];
			b2.uint8[1] = pc_data[3];
			cfg.lift_steps[index] = b2.int16;
			eeprom_busy_wait();
			eeprom_update_word_fixed((uint16_t *)&ee.cfg.lift_steps[index], cfg.lift_steps[index]);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		case (0x0A): //sink_1
		case (0x0B): //sink_2
		case (0x0C): //sink_3
		case (0x0D): //sink_4
		case (0x0E): //sink_5
			index = value_id - 0x0A;
			b2.uint8[0] = pc_data[2];
			b2.uint8[1] = pc_data[3];
			cfg.sink_steps[index] = b2.int16;
			eeprom_busy_wait();
			eeprom_update_word_fixed((uint16_t *)&ee.cfg.sink_steps[index], cfg.sink_steps[index]);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;


		case (0x0F): //profile_lift_index
			prof.lift_treshold = pc_data[2];
			eeprom_busy_wait();
			eeprom_update_byte_fixed(&ee.prof[cfg.selected_profile].lift_treshold, prof.lift_treshold);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		case (0x10): //profile_sink_index
			prof.sink_treshold = pc_data[2];
			eeprom_busy_wait();
			eeprom_update_byte_fixed(&ee.prof[cfg.selected_profile].sink_treshold, prof.sink_treshold);
			pc_encode(CMD_SET_VALUE, 0, NULL);
		break;

		default: //profile
			if (value_id >= 0x84)
			{
				index = value_id - 0x84;
				if (index < 41) //freq 84 - AC
				{
					b2.uint8[0] = pc_data[2];
					b2.uint8[1] = pc_data[3];
					prof.buzzer_freq[index] = b2.int16;
					eeprom_busy_wait();
					eeprom_update_word_fixed((uint16_t *)&ee.prof[cfg.selected_profile].buzzer_freq[index], prof.buzzer_freq[index]);
					pc_encode(CMD_SET_VALUE, 0, NULL);
					break;
				}
				if (index < 41 * 2) //pause AD - D5
				{
					index -= 41;
					b2.uint8[0] = pc_data[2];
					b2.uint8[1] = pc_data[3];
					prof.buzzer_pause[index] = b2.int16;
					eeprom_busy_wait();
					eeprom_update_word_fixed((uint16_t *)&ee.prof[cfg.selected_profile].buzzer_pause[index], prof.buzzer_pause[index]);
					pc_encode(CMD_SET_VALUE, 0, NULL);
					break;
				}
				if (index < 41 * 3) //length D6 - FE
				{
					index -= 41 * 2;
					b2.uint8[0] = pc_data[2];
					b2.uint8[1] = pc_data[3];
					prof.buzzer_length[index] = b2.int16;
					eeprom_busy_wait();
					eeprom_update_word_fixed((uint16_t *)&ee.prof[cfg.selected_profile].buzzer_length[index], prof.buzzer_length[index]);
					pc_encode(CMD_SET_VALUE, 0, NULL);
					break;
				}
			}
	}
}


void pc_parse_data()
{
	uint8_t cmd = pc_data[0];
	byte2 b2;
	uint8_t data[16];

//	DEBUG("cmd %02X\n", cmd);

	if (!pc_mode && cmd != CMD_INFO)
		return;

	wdt_reset();
	led_task();

	switch (cmd)
	{
		case(CMD_INFO): //Info AA 01 00 AB
			pc_mode = true;
			meas_timer.Stop();
			buzzer_set_tone(0);
			buzzer_override = false;
			led_mode = LED_MODE_G_ON;
			strcpy_P((char *)data, PSTR("bean2"));
			pc_encode(CMD_INFO, 6, data);
		break;

		case(CMD_PING): //Ping
			led_mode = LED_MODE_G_ON;
			pc_encode(CMD_PING, 0, NULL);
			auto_off_reset();
		break;

		case(CMD_GET_VALUE): //GetValue
			led_mode = LED_MODE_G;
			pc_get_value();
		break;

		case(CMD_SET_VALUE): //SetValue
			led_mode = LED_MODE_G;
			pc_set_value();
		break;

		case(CMD_RESET): //reset EEPROM AA 01 05 FB
			resetEEPROM();
		break;

		case(CMD_DEMO):
			led_mode = LED_MODE_G;
			if (pc_data[1] == 0xFF and pc_data[2] == 0x7F)
			{
				buzzer_set_tone(0);
			}
			else
			{
				b2.uint8[0] = pc_data[1];
				b2.uint8[1] = pc_data[2];

				climb = b2.int16 / 100.0;
				buzzer_override = false;
				buzzer_step();
			}
			pc_encode(CMD_DEMO, 0, NULL);
		break;


		case(0xFE): //reset to bootloader AA 01 FE FE
			SystemReset();
		break;

	}
}

void pc_decode(uint8_t c)
{
	if (sys_tick_get() - pc_last_byte > PC_MAX_TIME)
		pc_parser_step = PC_IDLE;

	DEBUG("c %02X %u\n", c, pc_parser_step);

	pc_last_byte = sys_tick_get();
	switch (pc_parser_step)
	{
		case(PC_IDLE):
			if (c == PC_START_BYTE)
				pc_parser_step = PC_LEN;
		break;

		case(PC_LEN):
			if (c > PC_MAX_LEN || c == 0)
			{
				pc_parser_step = PC_IDLE;
				break;
			}
			pc_parser_step = PC_DATA;
			pc_len = c;
			pc_index = 0;
			pc_crc = CalcCRC(0x00, PC_CRC_KEY, pc_len);
		break;

		case(PC_DATA):
			pc_crc = CalcCRC(pc_crc, PC_CRC_KEY, c);
			pc_data[pc_index] = c;

			pc_index++;
			if (pc_len == pc_index)
				pc_parser_step = PC_CRC;
		break;

		case(PC_CRC):
			if (pc_crc == c)
				pc_parse_data();
			else
				DEBUG("pc_crc %02X\n", pc_crc);

			pc_parser_step = PC_IDLE;
		break;
	}
}

uint8_t nmea_checksum(char *s)
{
	uint8_t c = 0;

    while(*s)
        c ^= *s++;

    return c;
}

uint32_t uart_next_step	= 0;
#define UART_PERIOD		50

void pc_step()
{
	if (usb_connected)
	{
		while (!usb_uart.isRxBufferEmpty())
			pc_decode(usb_uart.Read());

		if (uart_next_step < sys_tick_get() && !pc_mode)
		{
			char tmp[83];

//			printf_P(PSTR("%0.0f,%0.0f,%0.4f,%0.2f\n"), pressure, raw_pressure, climb, temperature);

			sprintf_P(tmp, PSTR("LK8EX1,%0.0f,99999,%0.0f,%0.0f,999,"), pressure, (climb * 100.0), temperature);
            printf_P(PSTR("$%s*%02X\r\n"), tmp, nmea_checksum(tmp));
//			sprintf_P(tmp, PSTR("POV,R,%0.2f,TE,%0.2f,T,%0.2f"), pressure, climb, temperature / 10.0);
//			printf_P(PSTR("$%s*%02X\r\n"), tmp, nmea_checksum(tmp));

			uart_next_step = sys_tick_get() + UART_PERIOD;
		}
	}
}
