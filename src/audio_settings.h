/* SPDX-License-Identifier: MIT */
#ifndef AUDIO_SETTINGS_H
#define AUDIO_SETTINGS_H
/* v8 uses packed PDM: one USB byte is eight PDM ticks at 64 kHz. */
#define PDM_RATE_HZ 64000UL
#define PCM_RATE_HZ 8000UL
#define PDM_TICKS_PER_SAMPLE 8UL
#define PDM_TICKS_PER_MS 64UL
#endif
