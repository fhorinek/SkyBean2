/*
 * vario.cc
 *
 *  Created on: 18.10.2013
 *      Author: horinek
 */

#include "vario.h"

#include "filter.h"
#include "bui.h"
#include "buzzer.h"
#include "pc.h"
#include "ms5611.h"
#include "battery.h"
#include "debug.h"
#include "cfg.h"

#define FIRST_SKIP	20

uint8_t skip = 0;
uint8_t usb_connected = false;

MS5611 sensor;

I2c i2c;
Timer meas_timer;

extern float temperature;
extern float raw_pressure;

extern Timer timer_buzzer_tone;
extern Timer timer_buzzer_delay;

extern configuration cfg;

void mark()
{
	GpioSetDirection(LEDR, OUTPUT);
	GpioSetDirection(LEDG, OUTPUT);
	LEDR_OFF
	LEDG_OFF

	while(1)
	{
		LEDR_OFF
		LEDG_ON
		_delay_ms(100);
		LEDR_ON
		LEDG_OFF
		_delay_ms(100);
	}
}

void init_low_power()
{
	PR.PRGEN = 0b10000011;

	PR.PRPA = 0b00000111;
	//stop port B DAC AC
	PR.PRPC = 0b00011100;

	//stop port D TWI USART1 USART0 SPI HIRES TC1 TC0
	PR.PRPD = 0b01011101;

	//NVM EE power reduction mode
	NVM.CTRLB |= 0b00000010;

	//disable digital buffer for bat adc
	PORTA.PIN3CTRL |= 0b00000111;
}

void total_low_power()
{
	PR.PRGEN = 0b10000111;

	//Disable all peripherals
	PR.PRPA = 0b00000111;
	PR.PRPC = 0b01011111;
	PR.PRPD = 0b01011111;

	//LDO SHDN
	GpioSetDirection(B_EN, OUTPUT);
	GpioWrite(B_EN, LOW);

	//Stop timers
	meas_timer.Stop();
	timer_buzzer_tone.Stop();
	timer_buzzer_delay.Stop();

	//other outputs
	GpioSetDirection(BM_PIN, INPUT);

	//leds
	LEDR_OFF;
	LEDG_OFF;

	//NVM EE power reduction mode
	NVM.CTRLB |= 0b00000010;
}


void Setup()
{
	usb_connected = USB_CONNECTED;

	ClockSetSource(x8MHz);

	wdt_init(wdt_1s);

	LoadEEPROM();

	init_low_power();

	EnableInterrupts();

	//port remap
	GpioRemap(&PORTD, gpio_remap_usart);
	GpioRemap(&PORTC, gpio_remap_timerA | gpio_remap_timerB | gpio_remap_timerC | gpio_remap_timerD);

	//configure uart & communicate with the
	pc_init();


	//B_EN enable sensor and I2C pull-up
	GpioSetDirection(B_EN, OUTPUT);
	GpioWrite(B_EN, HIGH);

	//wait to stabilize
	_delay_ms(200);

	i2c.InitMaster(i2cC, 600000ul, 8, 8);

	sys_tick_init();

	battery_init();

	bui_init();

	buzzer_init();

	filter_init();

	sensor.Init(&i2c, MS5611_ADDRESS_CSB_LO);


#ifdef ENABLE_DEBUG_UART
	sensor.CheckID();
#endif

	meas_timer.Init(timerD5, timer_div64); //at 8MHz

	meas_timer.SetTop(125 * 10); // == 10ms
	meas_timer.SetCompare(timer_A, 100); // == 0.64ms


	meas_timer.EnableInterrupts(timer_overflow | timer_compareA);
	meas_timer.Start();

#ifdef ENABLE_DEBUG_TIMING
	GpioSetDirection(DEBUG_PIN, OUTPUT);
#endif
}


//first period
ISR(timerD5_overflow_interrupt)
{
	//Because F*ck you xmega32E5
	meas_timer.ClearOverflowFlag();
	wdt_reset();

#ifdef ENABLE_DEBUG_TIMING
	GpioWrite(DEBUG_PIN, HI);
#endif

	sensor.ReadPressure();
	sensor.StartTemperature();

	sensor.CompensateTemperature();
	sensor.CompensatePressure();

#ifdef ENABLE_DEBUG_TIMING
	GpioWrite(DEBUG_PIN, LO);
#endif
}

//second period
ISR(timerD5_compareA_interrupt)
{
#ifdef ENABLE_DEBUG_TIMING
	GpioWrite(DEBUG_PIN, HI);
#endif

	sensor.ReadTemperature();
	sensor.StartPressure();


	//normal mode
	if (skip > FIRST_SKIP)
	{
		filter_step();
	}
	else
	{
		//skip first
		skip++;
	}

	buzzer_step();

	bui_step();

	battery_step();


#ifdef ENABLE_DEBUG_TIMING
	GpioWrite(DEBUG_PIN, LO);
#endif
}

extern uint8_t sleep_now;

int main()
{
	Setup();

#ifdef ENABLE_DEBUG_UART
	DEBUG("\n\n***starting***\n\n");
	DEBUG("RST.STATUS %02X\n", RST.STATUS);
	if (RST.STATUS & 0b00100000)
		DEBUG("Software\n");
	if (RST.STATUS & 0b00010000)
		DEBUG("PDI\n");
	if (RST.STATUS & 0b00001000)
		DEBUG("WDT\n");
	if (RST.STATUS & 0b00000100)
		DEBUG("BOR\n");
	if (RST.STATUS & 0b00000010)
		DEBUG("External\n");
	if (RST.STATUS & 0b00000001)
		DEBUG("Power On\n");
	RST.STATUS = 0b00111111;

    DEBUG("kalman Q %0.5f\n", cfg.kalman_q);
    DEBUG("kalman R %0.5f\n", cfg.kalman_r);
    DEBUG("kalman P %0.5f\n", cfg.kalman_p);
#endif

	while(1)
	{
		//call sleep command outside the ISR!
		while (sleep_now)
		{

		#ifdef ENABLE_DEBUG_TIMING
			GpioSetDirection(DEBUG_PIN, INPUT);
		#endif


//			DEBUG("\n\n***power down***\n\n");
//			_delay_ms(10);

			total_low_power();

			RtcDisableInterrupts(rtc_overflow);
			wdt_deinit();

			//set waking interrupt
			GpioSetInterrupt(BUTTON_PIN, gpio_interrupt, gpio_falling);

			//sleep
			SystemPowerDown();


//		#ifdef ENABLE_DEBUG_UART
//			//production test: for fast reprogram
//			SystemReset();
//		#endif


//			DEBUG("\n\n***waked up***\n\n");

			//waking up now
			//clear flags
            PORTA.INTFLAGS = 0xFF;
			//clear interrupt
			GpioSetInterrupt(BUTTON_PIN, gpio_clear);

			uint8_t wake_cnt = 0;
			for (uint8_t i = 0; i< 100; i++)
			{
				if (BUTTON_DOWN)
					wake_cnt++;
				else
					break;

				_delay_ms(7); //cca 1sec
			}


//			DEBUG("? %d\n", wake_cnt);

			//if the button was pressed 100 cycles. Restart
			//this is only way to start up the device
			if (wake_cnt == 100)
				SystemReset();
		}

		if (usb_connected != USB_CONNECTED)
			SystemReset();

		if (skip > FIRST_SKIP)
			pc_step();

		//nothing to do lets sleep for a while
		SystemPowerIdle();
	}
}
