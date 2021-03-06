#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019, 2020 Perspecta Labs Inc.
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, gr_unittest
from gnuradio import blocks
import equalizers_swig as equalizers

import random, numpy
from gnuradio import digital
from gnuradio import channels

class qa_linear_equalizer(gr_unittest.TestCase):

    def unpack_values(self, values_in, bits_per_value, bits_per_symbol):   
        # verify that 8 is divisible by bits_per_symbol 
        m = bits_per_value / bits_per_symbol
        # print(m)
        mask = 2**(bits_per_symbol)-1
            
        if bits_per_value != m*bits_per_symbol:
            print("error - bits per symbols must fit nicely into bits_per_value bit values")
            return []
            
        num_values = len(values_in)
        num_symbols = int(num_values*( m) )
        
        cur_byte = 0
        cur_bit = 0
        out = []
        for i in range(num_symbols):
            s = (values_in[cur_byte] >> (bits_per_value-bits_per_symbol-cur_bit)) & mask
            out.append(s)
            cur_bit += bits_per_symbol
            
            if cur_bit >= bits_per_value:
                cur_bit = 0
                cur_byte += 1
                
        return out

    def map_symbols_to_constellation(self, symbols, cons):
        l = list(map(lambda x: cons.points()[x], symbols))
        return l


    def setUp(self):
        random.seed(987654)
        self.tb = gr.top_block()
        self.num_data = num_data = 10000


        self.sps = sps = 4
        self.eb = eb = 0.35
        self.preamble = preamble = [0x27,0x2F,0x18,0x5D,0x5B,0x2A,0x3F,0x71,0x63,0x3C,0x17,0x0C,0x0A,0x41,0xD6,0x1F,0x4C,0x23,0x65,0x68,0xED,0x1C,0x77,0xA7,0x0E,0x0A,0x9E,0x47,0x82,0xA4,0x57,0x24,]

        self.payload_size = payload_size = 300 # bytes
        self.data = data = [0]*4+[random.getrandbits(8) for i in range(payload_size)]
        self.gain = gain = .001  # LMS gain
        self.corr_thresh = corr_thresh = 3e6
        self.num_taps = num_taps = 16      
        
        

    def tearDown(self):
        self.tb = None


    def transform(self, src_data, gain, const):
        SRC = blocks.vector_source_c(src_data, False)
        EQU = digital.lms_dd_equalizer_cc(4, gain, 1, const.base())
        DST = blocks.vector_sink_c()
        self.tb.connect(SRC, EQU, DST)
        self.tb.run()
        return DST.data()

    def test_001_identity(self):
        # Constant modulus signal so no adjustments
        const = digital.constellation_qpsk()
        src_data = const.points()*1000

        N = 100 # settling time
        expected_data = src_data[N:]
        result = self.transform(src_data, 0.1, const)[N:]

        N = -500
        self.assertComplexTuplesAlmostEqual(expected_data[N:], result[N:], 5)

    def test_qpsk_3tap_lms_training(self):
        # set up fg
        gain = 0.01  # LMS gain
        num_taps = 16
        num_samp = 2000
        num_test = 500
        cons = digital.constellation_qpsk().base()        
        rxmod = digital.generic_mod(cons, False, self.sps, True, self.eb, False, False)
        modulated_sync_word_pre = digital.modulate_vector_bc(rxmod.to_basic_block(),  self.preamble+self.preamble, [1])
        modulated_sync_word = modulated_sync_word_pre[86:(512+86)]  # compensate for the RRC filter delay
        corr_max = numpy.abs(numpy.dot(modulated_sync_word,numpy.conj(modulated_sync_word)))
        corr_calc = self.corr_thresh/(corr_max*corr_max)
        preamble_symbols = self.map_symbols_to_constellation(self.unpack_values(self.preamble, 8, 2), cons)

        alg = equalizers.adaptive_algorithm_lms( cons, gain).base()
        evm = equalizers.meas_evm_cc(cons)
        leq = equalizers.linear_equalizer(num_taps, preamble_symbols,  False, self.sps, alg, 'corr_est')
        correst = digital.corr_est_cc(modulated_sync_word, self.sps, 12, corr_calc, digital.THRESHOLD_ABSOLUTE)
        constmod = digital.generic_mod(
            constellation=cons,
            differential=False,
            samples_per_symbol=4,
            pre_diff_code=True,
            excess_bw=0.35,
            verbose=False,
            log=False)
        chan = channels.channel_model(
            noise_voltage=0.0,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=(1.0 + 1.0j, 0.63-.22j, -.1+.07j),
            noise_seed=0,
            block_tags=False)
        vso = blocks.vector_source_b(self.preamble+self.data, True, 1, [])
        head = blocks.head(gr.sizeof_float*1, num_samp)
        vsi = blocks.vector_sink_f()

        self.tb.connect(vso, constmod, chan, correst, leq, evm, head, vsi)
        self.tb.run()

        # look at the last 1000 samples, should converge quickly, below 5% EVM
        upper_bound = tuple(20.0*numpy.ones((num_test,)))
        lower_bound = tuple(0.0*numpy.zeros((num_test,)))
        output_data = vsi.data()
        output_data = output_data[-num_test:]
        self.assertLess(output_data, upper_bound)
        self.assertGreater(output_data, lower_bound)


if __name__ == '__main__':
    gr_unittest.run(qa_linear_equalizer)
