/* SPDX-License-Identifier: MIT
 * CH552 USB CDC-only packed 64-kHz PDM playback.
 * Firmware receives ONE BYTE PER EIGHT OUTPUT BITS, not PCM!
 * Each byte carries 8 bits, MSB-first; 8000 bytes/s -> 64000 PDM bits/s.
 * Synthesis/modulation runs on the host; this ISR only shifts GPIO P3.0.
 * Output is unipolar into a CURRENT-LIMITED transistor/buzzer driver.
 */
#include <stdint.h>
#include "ch552.h"
#include "audio.h"
#include "audio_settings.h"

#define AUDIO_FIFO_LEN 192u
#define START_THRESHOLD 96u
#define NEXT_INDEX(pos) \
    ((uint8_t)(((pos) == (AUDIO_FIFO_LEN - 1u)) ? 0u : ((pos) + 1u)))

static __xdata uint8_t audio_fifo[AUDIO_FIFO_LEN];
static volatile __data uint8_t audio_head = 0u;
static volatile __data uint8_t audio_tail = 0u;
static volatile __data uint8_t playing = 0u;
/* Only called from Timer2 ISR (after initialization). */
static __data uint8_t pdm_phase = 0u;
static __data uint8_t pdm_shift = 0u;

/* Force legacy PWM off; same proven P3.0 output setup as v7. */
__sfr __at(0x9D) PWM_CTRL;

void audio_init(void)
{
    TR0 = 0;
    ET0 = 0;
    PWM_CTRL = 0u;
    PIN_FUNC &= (uint8_t)~0x04u;
    P3_MOD_OC &= (uint8_t)~0x01u;
    P3_DIR_PU |= 0x01u;
    P3_0 = 0;

    audio_head = 0u;
    audio_tail = 0u;
    playing = 0u;
    pdm_phase = 0u;
    pdm_shift = 0u;
}

uint8_t audio_has_space(void)
{
    return (uint8_t)(NEXT_INDEX(audio_head) != audio_tail);
}

void audio_push(uint8_t packed_bits)
{
    uint8_t next = NEXT_INDEX(audio_head);
    if (next == audio_tail) return;
    audio_fifo[audio_head] = packed_bits;
    audio_head = next;
    if (!playing) {
        uint8_t buffered = (audio_head >= audio_tail)
            ? (uint8_t)(audio_head - audio_tail)
            : (uint8_t)(AUDIO_FIFO_LEN - audio_tail + audio_head);
        if (buffered >= START_THRESHOLD) playing = 1u;
    }
}

/* TIMER2 at exactly 64 kHz, physically verified rate in v7 configuration. */
void audio_tick_pdm(void)
{
    if (pdm_phase == 0u) {
        if (playing && (audio_tail != audio_head)) {
            pdm_shift = audio_fifo[audio_tail];
            audio_tail = NEXT_INDEX(audio_tail);
        } else {
            /* No samples: coil completely OFF, rather than 50% idle PWM. */
            pdm_shift = 0u;
            playing = 0u;
        }
    }
    P3_0 = (pdm_shift & 0x80u) ? 1 : 0;
    pdm_shift <<= 1;
    if (++pdm_phase >= 8u) pdm_phase = 0u;
}
