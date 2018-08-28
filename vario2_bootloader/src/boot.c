#include <avr/io.h>
#include <stdlib.h>

#include "sp_driver.h"
#include "clock.h"
#include "common.h"
#include "usart.h"

#include "adc.h"


void switch_to_app()
{
	void (*reset_vect)( void ) = 0x000000;

	//move int to back to 0x0
	CCPIOWrite(&PMIC.CTRL, 0);

	clock_deinit();
	usart_deinit();
	adc_deinit();

	LEDR_OFF;
	LEDG_OFF;

	PORTA.DIRCLR = 0b00000011;

	//jump to first 128
	EIND = 0x0;
	//jump to 0x0
	reset_vect();
}

void debug(uint8_t cnt)
{
	uint8_t j;
	_delay_ms(500);
	for (j = 0; j < cnt; j++)
	{
		LEDR_OFF;
		LEDG_OFF;
		_delay_ms(500);
		LEDR_ON;
		LEDG_ON;
		_delay_ms(200);
	}
}

void flash_erase()
{
	uint32_t adr;

	for (adr = 0; adr < APP_SECTION_SIZE; adr += APP_SECTION_PAGE_SIZE)
	{
		// wait for SPM instruction to complete
		SP_WaitForSPM();
		// erase page
		SP_EraseApplicationPage(adr);
	}
}

int main()
{
	//move int to boot
	CCPIOWrite(&PMIC.CTRL, PMIC_IVSEL_bm);

	PORTA.DIRSET = 0b00000011;
	LEDR_OFF;
	LEDG_OFF;

	//clock_init();
	//osc_init();

	uint32_t adr;

	int16_t adrh;
	int16_t adrm;
	int16_t adrl;

	int16_t sizeh;
	int16_t sizel;
	uint16_t size;

	uint16_t i;

	//enable int
	PMIC.CTRL |= PMIC_LOLVLEX_bm;
	sei();

	int16_t cmd;

	uint8_t done = 1;

	//wait loop
	uint8_t wait_done = 1;
	uint16_t wait_counter = 0;
	uint8_t wait_seq = 0;

	_delay_ms(10);
	if (USB_CONNECTED)
	{
		wait_done = 0;
		usart_init();
		usart_putchar('b');
	}

	LEDR_ON;
	LEDG_ON;

	while (!wait_done)
	{
		//printf("wc %d\n", wait_counter);
//		usart_putchar('b');

		_delay_ms(1);
		wait_counter++;

		if (usart_rx_len > 0)
		{
			cmd = usart_getchar();

			switch (wait_seq)
			{
			case(0):
				if (cmd == 'e')
					wait_seq++;
			break;
			case(1):
				if (cmd == 'b')
					wait_seq++;
			break;
			case(2):
				if (cmd == 'l')
				{
					wait_done = 1;
					done = 0;

					usart_putchar('b');
					usart_putchar('o');
					usart_putchar('o');
					usart_putchar('t');
					usart_putchar('l');
					usart_putchar('o');
					usart_putchar('a');
					usart_putchar('d');
					usart_putchar('e');
					usart_putchar('r');

					usart_putchar((VERSION & 0xFF00) >> 8);
					usart_putchar(VERSION & 0x00FF);

					while(usart_tx_len);
				}
			break;
			}
		}

		if (wait_counter > WAIT_TIME)
		{
			wait_done = 1;
		}
	}

	LEDR_OFF;
	LEDG_OFF;

	uint8_t error = false;

	while (!done)
	{
		cmd = usart_getchar();

		if (cmd == 0xF0)
			continue;

		switch(cmd)
		{
		case('h')://hello
			usart_putchar('h');
		break;

		case('e')://erase app
			LEDR_ON;

			flash_erase();

			usart_putchar('d');

			LEDR_OFF;
		break;

		case('r')://read flash
			LEDG_ON;
			LEDR_ON;


			//start address
			adrl = usart_getchar();
			if (adrl == -1)
			{
				error = 1;
				break;
			}

			adrm = usart_getchar();
			if (adrm == -1)
			{
				error = 1;
				break;
			}

			adrh = usart_getchar();
			if (adrh == -1)
			{
				error = 1;
				break;
			}

			adr = ((uint32_t) adrh << 16) | ((uint16_t) adrm << 8) | (adrl);

			//block size
			sizel = usart_getchar();
			if (sizel == -1)
			{
				error = 1;
				break;
			}

			sizeh = usart_getchar();
			if (sizeh == -1)
			{
				error = 1;
				break;
			}

			size = (sizeh << 8) | sizel;

			for (i=0; i<size; i++)
			{
				SP_WaitForSPM();
				//read byte
				uint8_t byte = SP_ReadByte(adr + i);
				usart_putchar(byte);
			}

			LEDR_OFF;
			LEDG_OFF;
		break;

		case('p')://upload block
			LEDG_ON;

			//start address
			adrl = usart_getchar();
			if (adrl == -1)
			{
				error = 1;
				break;
			}

			adrm = usart_getchar();
			if (adrm == -1)
			{
				error = 1;
				break;
			}

			adrh = usart_getchar();
			if (adrh == -1)
			{
				error = 1;
				break;
			}

			adr = ((uint32_t) adrh << 16) | ((uint16_t) adrm << 8) | (adrl);

			//block size
			sizel = usart_getchar();
			if (sizel == -1)
			{
				error = 1;
				break;
			}

			sizeh = usart_getchar();
			if (sizeh == -1)
			{
				error = 1;
				break;
			}

			size = (sizeh << 8) | sizel;

			SP_EraseFlashBuffer();

			for (i = 0; i < size; i++)
			{
				int16_t datal = usart_getchar();
				if (datal == -1)
				{
					error = 1;
					break;
				}

				int16_t datah = usart_getchar();
				if (datah == -1)
				{
					error = 1;
					break;
				}

				SP_WaitForSPM();
				SP_LoadFlashWord(adr + i * 2, datah << 8 | datal);
			}

			SP_WaitForSPM();
			SP_WriteApplicationPage(adr);

			usart_putchar('d');
			LEDG_OFF;
		break;

		case('b')://boot
			_delay_ms(1);
			while(usart_tx_len);
			done = 1;
		break;

		case(0x0D)://\n
		case(0x0A)://\r
		case(-1)://idle
		break;

		default:
			usart_putchar('?');
			usart_putchar(cmd);
		}

		if (error)
		{
			//timeout error, erase
			usart_putchar('!');
			flash_erase();
			usart_putchar('d');
			_delay_ms(1);
			while(usart_tx_len);
			done = 1;
		}

	}

	//diable int
	cli();

    //wait until work is done
	SP_WaitForSPM();
	//lock SPM
	//SP_LockSPM();

	switch_to_app();

	return 0;
}

