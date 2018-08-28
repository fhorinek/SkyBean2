/*
 * common.cc
 *
 *  Created on: 7.11.2013
 *      Author: horinek
 */

#include "common.h"
#include "bui.h"
#include "cfg.h"

#include <stddef.h>

//kalman filter parameters
//default 0.001, 15.0, 30.0, 0.0
//
//float ram_kalman_q = 0.001;//0.001;
//
//float ram_kalman_r = 6.0;//15.0;
//
//float ram_kalman_p = 30.0;

//Altitude and pressure
float ram_sea_level_Pa = 101325;
float raw_pressure = 0;
float altitude0 = 0;

float temperature = 0;
float pressure = 0;
float climb = 0;

bool meas_new_sample = false;

float ram_climb_noise = 0.1;

//common and system
volatile uint16_t sys_tick_cnt = 0;

uint8_t buzzer_override = true;
uint16_t buzzer_override_tone;

//in ram
profile prof;
configuration cfg;

float ram_sink_begin;
float ram_lift_begin;

uint8_t sleep_now = false;

#include "defaults.h"

#define Check(var, min, max, def)	\
			do { \
				if (var < min || var > max) \
					var = def; \
			} while (0);

void dumpEE(bool show_cfg = false)
{
    union prof_helper
    {
        profile * prof;
        uint8_t * byte;
    };

    union prof_helper phelper;

    phelper.prof = &prof;

    DEBUG("\n\nEE dump\n");
    #define EE_MUL  32
    uint8_t ee_buff[EE_MUL];
    for (uint8_t i = 0; EE_MUL * i < 1024; i++)
    {
        eeprom_busy_wait();
        eeprom_read_block(ee_buff, (const void*) (EE_MUL * i), EE_MUL);
        DEBUG("%04d: ", EE_MUL * i);
        for (uint8_t j = 0; j < EE_MUL; j++)
            DEBUG("%02X ", ee_buff[j]);
        DEBUG("\n");
    }

    if (!show_cfg)
        return;

    DEBUG("\n--- cfg is ---\n");
    DEBUG("buzzer_volume %d\n", cfg.buzzer_volume);
    DEBUG("supress_startup %d\n", cfg.supress_startup);
    DEBUG("auto_poweroff %d\n", cfg.auto_poweroff);
    DEBUG("serial_output %d\n", cfg.serial_output);
    DEBUG("selected_profile %d\n", cfg.selected_profile);

    DEBUG("lift_steps: ");
    for (uint8_t i = 0; i < 5; i++)
        DEBUG("%3d ", cfg.lift_steps[i]);
    DEBUG("\n");

    DEBUG("sink_steps: ");
    for (uint8_t i = 0; i < 5; i++)
        DEBUG("%d ", cfg.sink_steps[i]);
    DEBUG("\n");

    DEBUG("kalman_q %0.4f\n", cfg.kalman_q);
    DEBUG("kalman_r %0.4f\n", cfg.kalman_r);
    DEBUG("kalman_p %0.4f\n", cfg.kalman_p);

    DEBUG("int_interval %d\n", cfg.int_interval);

    for (uint8_t i = 0; i < 3; i++)
    {
        eeprom_busy_wait();
        eeprom_read_block(phelper.prof, &ee.prof[i], sizeof(prof));

        DEBUG("\n--- profile %i ---\n", i);

        DEBUG("name %16s\n", prof.name);

        DEBUG("buzzer_freq:   ");
        for (uint8_t j = 0; j < 41; j++)
            DEBUG("%4d ", prof.buzzer_freq[j]);
        DEBUG("\n");

        DEBUG("buzzer_pause:  ");
        for (uint8_t j = 0; j < 41; j++)
            DEBUG("%4d ", prof.buzzer_pause[j]);
        DEBUG("\n");

        DEBUG("buzzer_length: ");
        for (uint8_t j = 0; j < 41; j++)
            DEBUG("%4d ", prof.buzzer_length[j]);
        DEBUG("\n");

        DEBUG("lift_treshold %d\n", prof.lift_treshold);
        DEBUG("sink_treshold %d\n", prof.sink_treshold);
        DEBUG("enabled %d\n", prof.enabled);
    }
}

void resetEEPROM()
{
    #define EE_PAGE_SIZE            32

    DEBUG("resetEEPROM\n\n");
    for (uint16_t i = 0; i < DEFAULT_CFG_LENGTH; i += EE_PAGE_SIZE)
    {
        uint8_t buff[EE_PAGE_SIZE];
        uint8_t size = min(DEFAULT_CFG_LENGTH - i, EE_PAGE_SIZE);
        void * progmem_adr = (void *) ((uint16_t) (&default_cfg) + i);
        void * eeprom_adr = (void *) ((uint16_t) (&ee) + i);

        memcpy_P(buff, progmem_adr, size);
        eeprom_busy_wait();
        eeprom_write_block(buff, eeprom_adr, size);

        wdt_reset();
    }

    eeprom_busy_wait();
    SystemReset();
}

void LoadEEPROM()
{
    eeprom_busy_wait();

    eeprom_read_block(&cfg, &ee.cfg, sizeof(cfg));

    if (cfg.buzzer_volume == 0xFF)
        resetEEPROM();

    Check(cfg.buzzer_volume, 1, 4, 4);
    Check(cfg.supress_startup, 0, 1, 0);
    Check(cfg.auto_poweroff, 0, 3600, 60 * 5);
    Check(cfg.serial_output, 0, 10, 0);
    Check(cfg.selected_profile, 0, 2, 0);
    for (uint8_t i = 0; i < 5; i++)
    {
        Check(cfg.lift_steps[i], -1500, 1500, i * 10);
        Check(cfg.sink_steps[i], -1500, 1500, i * -50);
    }
    Check(cfg.kalman_q, 0, 10, 0.001);
    Check(cfg.kalman_r, 0, 10, 6.0);
    Check(cfg.kalman_p, 0, 100, 30.0);
    Check(cfg.int_interval, 12, 50, 25);

    eeprom_read_block(&prof, &ee.prof[cfg.selected_profile], sizeof(prof));
    for (uint8_t i = 0; i < 41; i++)
    {
        //todo: fallback table
        Check(prof.buzzer_freq[i], 0, 2000, 100);
        Check(prof.buzzer_pause[i], 0, 2000, 100);
        Check(prof.buzzer_length[i], 0, 2000, 100);
    }
    Check(prof.lift_treshold, 0, 5, 1);
    Check(prof.sink_treshold, 0, 5, 1);

    Check(prof.enabled, 0, 1, 1);

    LiftSinkRefresh();

    //NVM EE power reduction mode
    NVM.CTRLB |= 0b00000010;

}
void StoreVolume()
{
    eeprom_busy_wait();
    eeprom_update_byte(&ee.cfg.buzzer_volume, cfg.buzzer_volume);

    //NVM EE power reduction mode
    NVM.CTRLB |= 0b00000010;
}

void StoreLift()
{
    eeprom_busy_wait();
    eeprom_update_byte(&ee.prof[cfg.selected_profile].lift_treshold, prof.lift_treshold);

    //NVM EE power reduction mode
    NVM.CTRLB |= 0b00000010;
}

void StoreSink()
{
    eeprom_busy_wait();
    eeprom_update_byte(&ee.prof[cfg.selected_profile].sink_treshold, prof.sink_treshold);

    //NVM EE power reduction mode
    NVM.CTRLB |= 0b00000010;
}

void LoadProfile()
{
    eeprom_busy_wait();
    eeprom_update_byte(&ee.cfg.selected_profile, cfg.selected_profile);

    eeprom_read_block(&prof, &ee.prof[cfg.selected_profile], sizeof(prof));
    for (uint8_t i = 0; i < 41; i++)
    {
        //todo: fallback table
        Check(prof.buzzer_freq[i], 0, 2000, 100);
        Check(prof.buzzer_pause[i], 0, 2000, 100);
        Check(prof.buzzer_length[i], 0, 2000, 100);
    }
    Check(prof.lift_treshold, 0, 5, 1);
    Check(prof.sink_treshold, 0, 5, 1);

    Check(prof.enabled, 0, 1, 1);
}

ISR(rtc_overflow_interrupt)
{
    sys_tick_cnt += 1;
}

//1ms system timer for crude timing (button, battery measurement, etc...)
void sys_tick_init()
{
    RtcInit(rtc_1000Hz_ulp, rtc_div1);
    RtcEnableInterrupts(rtc_overflow);
}

uint32_t sys_tick_get()
{
    uint16_t act = RtcGetValue();

    return ((uint32_t) sys_tick_cnt << 16) | act;
}

