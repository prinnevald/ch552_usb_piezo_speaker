/* SPDX-License-Identifier: MIT
 * Timer2 clock Fsys/12 = 2 MHz at a 24 MHz CPU clock.
 * Fixed to 64 kHz: 31,31,31,32 counts (2 MHz / 31.25).
 * USB carries packed PDM bits (8 bits per byte, 8000 bytes/s).
 * No PCM conversion occurs in this interrupt.
 */
#include <stdint.h>
#include "ch552.h"
#include "config.h"
#include "tick.h"
#include "audio.h"
#include "audio_settings.h"

#if FREQ_SYS != 24000000UL
#error "PDM Timer2 configuration requires FREQ_SYS=24000000"
#endif

volatile uint32_t tick_ms = 0u;
static __data uint8_t ticks_in_ms = 0u;
static __data uint8_t reload_phase = 0u;

void tick_init(void)
{
    T2CON = 0x00u;
    T2MOD = 0x00u;          /* auto-reload, timer input Fsys/12 */
    RCAP2H = 0xFFu;
#if PDM_RATE_HZ == 32000UL
    RCAP2L = 0xC1u;        /* initial: 63 ticks */
#elif PDM_RATE_HZ == 48000UL
    RCAP2L = 0xD6u;        /* initial: 42 ticks */
#else
    RCAP2L = 0xE1u;        /* initial: 31 ticks */
#endif
    TH2 = RCAP2H;
    TL2 = RCAP2L;
    ticks_in_ms = 0u;
    reload_phase = 0u;
    TF2 = 0;
    ET2 = 1;
    TR2 = 1;
}

void tick_isr(void) __interrupt(INT_NO_TMR2)
{
    TF2 = 0;
    /* Timer2 has already loaded the current period from RCAP2.
     * Set RCAP2 for the NEXT overflow.
     */
#if PDM_RATE_HZ == 32000UL
    reload_phase ^= 1u;
    RCAP2L = reload_phase ? 0xC2u : 0xC1u;   /* 62,63 */
#elif PDM_RATE_HZ == 48000UL
    if (++reload_phase >= 3u) reload_phase = 0u;
    RCAP2L = (reload_phase == 2u) ? 0xD7u : 0xD6u;  /* 42,41,42 */
#else
    if (++reload_phase >= 4u) reload_phase = 0u;
    RCAP2L = (reload_phase == 3u) ? 0xE0u : 0xE1u;  /* 31,31,32,31 */
#endif

    audio_tick_pdm();

    if (++ticks_in_ms >= (uint8_t)PDM_TICKS_PER_MS) {
        ticks_in_ms = 0u;
        ++tick_ms;
    }
}

uint32_t tick_now(void)
{
    uint32_t value;
    uint8_t was_enabled = EA;
    EA = 0;
    value = tick_ms;
    EA = was_enabled;
    return value;
}

uint16_t tick_now16(void)
{
    uint16_t value;
    uint8_t was_enabled = EA;
    EA = 0;
    value = (uint16_t)tick_ms;
    EA = was_enabled;
    return value;
}
