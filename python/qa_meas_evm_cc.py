#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019, 2020 Perspecta Labs Inc..
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

class qa_meas_evm_cc(gr_unittest.TestCase):

    def setUp(self):
        random.seed(987654)
        self.tb = gr.top_block()
        self.num_data = num_data = 1000

    def tearDown(self):
        self.tb = None

    def test_qpsk(self):
        # set up fg
        expected_result = tuple(numpy.zeros((self.num_data,)))

        self.cons = cons = digital.constellation_qpsk().base()
        self.data = data = [random.randrange(len(cons.points())) for x in range(self.num_data)]
        self.symbols = symbols = numpy.squeeze([cons.map_to_points_v(i) for i in data])

        evm = equalizers.meas_evm_cc(cons)
        vso = blocks.vector_source_c(symbols, False, 1, [])
        # mc = blocks.multiply_const_cc(3.0+2.0j)
        vsi = blocks.vector_sink_f()

        self.tb.connect(vso, evm, vsi)
        self.tb.run()
        # check data

        output_data = vsi.data()
        self.assertEqual(expected_result, output_data)

    def test_qpsk_nonzeroevm(self):
        # set up fg
        expected_result = tuple(numpy.zeros((self.num_data,)))

        self.cons = cons = digital.constellation_qpsk().base()
        self.data = data = [random.randrange(len(cons.points())) for x in range(self.num_data)]
        self.symbols = symbols = numpy.squeeze([cons.map_to_points_v(i) for i in data])

        evm = equalizers.meas_evm_cc(cons)
        vso = blocks.vector_source_c(symbols, False, 1, [])
        mc = blocks.multiply_const_cc(3.0+2.0j)
        vsi = blocks.vector_sink_f()

        self.tb.connect(vso, mc, evm, vsi)
        self.tb.run()
        # check data

        output_data = vsi.data()
        self.assertNotEqual(expected_result, output_data)

    def test_qpsk_channel(self):
        upper_bound = tuple(50.0*numpy.ones((self.num_data,)))
        lower_bound = tuple(0.0*numpy.zeros((self.num_data,)))

        self.cons = cons = digital.constellation_qpsk().base()
        self.data = data = [random.randrange(len(cons.points())) for x in range(self.num_data)]
        self.symbols = symbols = numpy.squeeze([cons.map_to_points_v(i) for i in data])

        chan = channels.channel_model(
            noise_voltage=0.1,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=[1.0 + 0.0j],
            noise_seed=0,
            block_tags=False)

        evm = equalizers.meas_evm_cc(cons)
        vso = blocks.vector_source_c(symbols, False, 1, [])
        mc = blocks.multiply_const_cc(3.0+2.0j)
        vsi = blocks.vector_sink_f()

        self.tb.connect(vso, chan, evm, vsi)
        self.tb.run()
        # check data

        output_data = vsi.data()
        self.assertLess(output_data, upper_bound)
        self.assertGreater(output_data, lower_bound)

    def test_qam16_channel(self):
        upper_bound = tuple(50.0*numpy.ones((self.num_data,)))
        lower_bound = tuple(0.0*numpy.zeros((self.num_data,)))

        self.cons = cons = digital.constellation_16qam().base()
        self.data = data = [random.randrange(len(cons.points())) for x in range(self.num_data)]
        self.symbols = symbols = numpy.squeeze([cons.map_to_points_v(i) for i in data])

        chan = channels.channel_model(
            noise_voltage=0.1,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=[1.0 + 0.0j],
            noise_seed=0,
            block_tags=False)

        evm = equalizers.meas_evm_cc(cons)
        vso = blocks.vector_source_c(symbols, False, 1, [])
        mc = blocks.multiply_const_cc(3.0+2.0j)
        vsi = blocks.vector_sink_f()

        self.tb.connect(vso, chan, evm, vsi)
        self.tb.run()
        # check data

        output_data = vsi.data()
        self.assertLess(output_data, upper_bound)
        self.assertGreater(output_data, lower_bound)

if __name__ == '__main__':
    gr_unittest.run(qa_meas_evm_cc)
