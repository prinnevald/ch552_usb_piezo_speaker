/* SPDX-License-Identifier: MIT */
#ifndef AUDIO_H
#define AUDIO_H
#include <stdint.h>
void audio_init(void);
uint8_t audio_has_space(void);
/* Input is eight packed output bits per byte, MSB first. */
void audio_push(uint8_t packed_bits);
void audio_tick_pdm(void);
#endif
