#!/usr/bin/env python3
"""Guarded local R6 port routing. The caller refills and runs native DRC."""
import uuid

import pcbnew

NAMESPACE = uuid.UUID('df7935af-7bcf-408d-a7d5-5bd5c47fa7c2')
MM, mm = pcbnew.FromMM, pcbnew.ToMM

RADIO_REMOVE = {'0d93fbfc-db8c-4e1d-aaab-59ebadcba08b': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (42.63, 33.1),
                                          (42.43, 33.299999),
                                          0.15,
                                          None),
 '1b6ddfac-83d3-4c76-8b3f-26388fc540f8': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'In2.Cu',
                                          (41.33, 38.3),
                                          (41.33, 34.4),
                                          0.15,
                                          None),
 '34d662e3-bcbd-4e40-a4a2-43d1c7576872': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (41.33, 34.5),
                                          (41.375, 34.5),
                                          0.15,
                                          None),
 '44259e6d-7f07-4b08-9a20-fc25fe5e1e09': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (42.43, 33.299999),
                                          (42.43, 33.9),
                                          0.15,
                                          None),
 '4fc958e2-c73e-4386-b475-ceaf461f6e62': ('PCB_TRACK',
                                          'TLM_5V',
                                          'F.Cu',
                                          (41.375, 36.5),
                                          (40.875, 36.5),
                                          0.2,
                                          None),
 '5cb410fc-e6d5-4235-b769-f09ba8072746': ('PCB_TRACK',
                                          'TLM_5V',
                                          'F.Cu',
                                          (40.875, 36.5),
                                          (40.275, 35.9),
                                          0.2,
                                          None),
 '895b80fb-86cd-4c86-9770-a52685e46631': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (42.43, 33.9),
                                          (41.83, 34.5),
                                          0.15,
                                          None),
 '8a625903-5397-48c1-a2f4-e128f14ab237': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (40.33, 37.9),
                                          (40.73, 38.3),
                                          0.15,
                                          None),
 '9d6824d1-a5bd-4529-8637-f81635ed5031': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (40.33, 36.7),
                                          (40.33, 37.9),
                                          0.15,
                                          None),
 'a05f4654-7916-493a-97e3-79da99e16e37': ('PCB_VIA', 'RADIO_TXD', 'F.Cu', (42.63, 33.1), (42.63, 33.1), 0.6, 0.3),
 'd1153acc-663c-42da-b40d-6057e35d02b9': ('PCB_TRACK',
                                          'TLM_5V',
                                          'F.Cu',
                                          (40.275, 35.9),
                                          (40.275, 27.1),
                                          0.2,
                                          None),
 'd90c03ce-425c-49ca-b3c7-010a30d5f030': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (40.73, 38.3),
                                          (41.33, 38.3),
                                          0.15,
                                          None),
 'da493ca1-c883-4a3f-8026-5d66b6946282': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (41.83, 34.5),
                                          (41.33, 34.5),
                                          0.15,
                                          None),
 'dafaaaa6-0253-4030-813b-710d15953899': ('PCB_VIA', 'RADIO_TXD', 'F.Cu', (41.33, 38.3), (41.33, 38.3), 0.6, 0.3),
 'ddcceaa7-a4ac-4c55-a19e-40f49a374c48': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'In2.Cu',
                                          (41.33, 34.4),
                                          (42.63, 33.1),
                                          0.15,
                                          None),
 'e6836564-b490-4fd3-a040-3130bd389375': ('PCB_TRACK',
                                          'RADIO_TXD',
                                          'F.Cu',
                                          (39.63, 36.0),
                                          (40.33, 36.7),
                                          0.15,
                                          None)}
RADIO_ADD = [{'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.275, 27.1], 'c': [40.475, 27.3], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.475, 27.3], 'c': [40.475, 30.6], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.475, 30.6], 'c': [40.5, 30.6], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'via', 'at': [40.5, 30.6], 'width': 0.5, 'drill': 0.3},
 {'net': 'TLM_5V', 'kind': 'via', 'at': [41.33, 38.3], 'width': 0.5, 'drill': 0.3},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'In2.Cu', 'a': [40.5, 30.6], 'c': [41.3, 31.4], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'In2.Cu', 'a': [41.3, 31.4], 'c': [41.3, 38.3], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'In2.Cu', 'a': [41.3, 38.3], 'c': [41.33, 38.3], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [41.33, 38.3], 'c': [40.63, 38.3], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.63, 38.3], 'c': [40.23, 37.9], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.23, 37.9], 'c': [40.23, 37.1], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.23, 37.1], 'c': [40.43, 36.9], 'width': 0.2},
 {'net': 'TLM_5V', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.43, 36.9], 'c': [42.775, 36.9], 'width': 0.2},
 {'net': 'RADIO_M1', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.63, 33], 'c': [40.13, 32.5], 'width': 0.15},
 {'net': 'RADIO_M1', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.13, 32.5], 'c': [41.33, 32.5], 'width': 0.15},
 {'net': 'RADIO_M1', 'kind': 'track', 'layer': 'F.Cu', 'a': [41.33, 32.5], 'c': [41.375, 32.5], 'width': 0.15},
 {'net': 'RADIO_RXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.63, 34.5], 'c': [40.63, 33.5], 'width': 0.15},
 {'net': 'RADIO_RXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.63, 33.5], 'c': [41.33, 33.5], 'width': 0.15},
 {'net': 'RADIO_RXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [41.33, 33.5], 'c': [41.375, 33.5], 'width': 0.15},
 {'net': 'RADIO_TXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.63, 36], 'c': [39.63, 35.8], 'width': 0.15},
 {'net': 'RADIO_TXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.63, 35.8], 'c': [40.93, 34.5], 'width': 0.15},
 {'net': 'RADIO_TXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.93, 34.5], 'c': [41.33, 34.5], 'width': 0.15},
 {'net': 'RADIO_TXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [41.33, 34.5], 'c': [41.375, 34.5], 'width': 0.15},
 {'net': 'RADIO_AUX', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.63, 37.5], 'c': [39.63, 36.9], 'width': 0.15},
 {'net': 'RADIO_AUX', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.63, 36.9], 'c': [40.33, 36.2], 'width': 0.15},
 {'net': 'RADIO_AUX', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.33, 36.2], 'c': [40.33, 36.1], 'width': 0.15},
 {'net': 'RADIO_AUX', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.33, 36.1], 'c': [40.93, 35.5], 'width': 0.15},
 {'net': 'RADIO_AUX', 'kind': 'track', 'layer': 'F.Cu', 'a': [40.93, 35.5], 'c': [41.33, 35.5], 'width': 0.15},
 {'net': 'RADIO_AUX', 'kind': 'track', 'layer': 'F.Cu', 'a': [41.33, 35.5], 'c': [41.375, 35.5], 'width': 0.15}]


POWER_REMOVE = {'72215bf2-0662-4492-a646-cf4b690afbfa': ('PCB_TRACK', '3V3', 'B.Cu', (38.45, 38.75), (38.45, 34.65), 0.25, None),
 '93745301-b176-483a-9387-44fd8be6ac46': ('PCB_TRACK', '3V3', 'B.Cu', (38.45, 34.65), (38.45, 38.75), 0.25, None),
 'c91c1b81-5248-42ba-9836-a761bd4ed66e': ('PCB_TRACK',
                                          '3V3A',
                                          'B.Cu',
                                          (39.8632, 33.7393),
                                          (36.7632, 33.7393),
                                          0.25,
                                          None),
 'ceafa09b-e92c-4d70-a61f-df398833d04b': ('PCB_TRACK',
                                          '3V3A',
                                          'B.Cu',
                                          (40.0632, 33.9393),
                                          (39.8632, 33.7393),
                                          0.25,
                                          None),
 'e311ff28-add3-4149-bf96-d1e9114cdf2d': ('PCB_TRACK',
                                          '3V3A',
                                          'B.Cu',
                                          (36.7632, 33.7393),
                                          (36.3632, 34.1393),
                                          0.25,
                                          None)}
POWER_ADD = [{'net': '3V3', 'kind': 'track', 'layer': 'B.Cu', 'a': (38.45, 34.65), 'c': (39.13, 34.65), 'width': 0.25},
 {'net': '3V3', 'kind': 'track', 'layer': 'B.Cu', 'a': (39.13, 34.65), 'c': (39.13, 38.07), 'width': 0.25},
 {'net': '3V3', 'kind': 'track', 'layer': 'B.Cu', 'a': (39.13, 38.07), 'c': (38.45, 38.75), 'width': 0.25},
 {'net': '3V3A',
  'kind': 'track',
  'layer': 'B.Cu',
  'a': (40.0632, 33.9393),
  'c': (39.2632, 33.1393),
  'width': 0.25},
 {'net': '3V3A',
  'kind': 'track',
  'layer': 'B.Cu',
  'a': (39.2632, 33.1393),
  'c': (37.3632, 33.1393),
  'width': 0.25},
 {'net': '3V3A',
  'kind': 'track',
  'layer': 'B.Cu',
  'a': (37.3632, 33.1393),
  'c': (36.3632, 34.1393),
  'width': 0.25}]
GPS_REMOVE = {'2b6782da-5c99-4a47-bd36-058b8be6c1c1': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (39.57, 44.1),
                                          (39.97, 44.1),
                                          0.15,
                                          None),
 '525aca45-c271-44e5-be5d-47fa05dfaf18': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (38.77, 44.9),
                                          (39.57, 44.1),
                                          0.15,
                                          None),
 '6bf781e3-9f89-4062-9dcc-de960fae5283': ('PCB_TRACK',
                                          'NRST',
                                          'F.Cu',
                                          (37.635, 47.05),
                                          (36.435, 47.05),
                                          0.15,
                                          None),
 '8396ae32-0d56-4069-a5f3-e056efe99518': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (39.97, 44.1),
                                          (40.17, 43.9),
                                          0.15,
                                          None),
 '84ba9b9b-1277-4af8-b947-e261e8df7561': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (37.97, 42.9),
                                          (37.47, 43.4),
                                          0.15,
                                          None),
 'a6132ed8-962d-4e1e-8170-1aea3f027e8e': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (38.77, 45.0),
                                          (38.77, 44.9),
                                          0.15,
                                          None),
 'ad4a1d1a-674c-42cd-b607-944da422655e': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (37.47, 43.4),
                                          (37.45, 43.38),
                                          0.15,
                                          None),
 'c05bce71-ea18-4647-8d34-ee525e37e0bc': ('PCB_TRACK',
                                          'NRST',
                                          'F.Cu',
                                          (45.335, 54.75),
                                          (37.635, 47.05),
                                          0.15,
                                          None),
 'c5fd11a1-7242-424e-94b9-fdea7020bb90': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (37.45, 43.38),
                                          (37.45, 43.35),
                                          0.15,
                                          None),
 'e33b5fef-83dd-4674-b4ad-d9ff7144733d': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (40.17, 43.9),
                                          (40.17, 43.1),
                                          0.15,
                                          None),
 'ebbd506e-c7b9-43f8-9b11-988069658d60': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (40.17, 43.1),
                                          (39.97, 42.9),
                                          0.15,
                                          None),
 'f7b969cc-6541-4cee-a1d8-4d854973f75d': ('PCB_TRACK',
                                          'GPS_RX_MCU',
                                          'F.Cu',
                                          (39.97, 42.9),
                                          (37.97, 42.9),
                                          0.15,
                                          None)}
GPS_ADD = [{'net': 'GPS_RX_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [38.77, 45], 'c': [38.67, 45.1], 'width': 0.15},
 {'net': 'GPS_RX_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [38.67, 45.1], 'c': [38.67, 46.6], 'width': 0.15},
 {'net': 'GPS_RX_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [38.67, 46.6], 'c': [38.65, 46.6], 'width': 0.15},
 {'net': 'GPS_RX_MCU', 'kind': 'via', 'at': [38.65, 46.6], 'width': 0.5, 'drill': 0.3},
 {'net': 'GPS_RX_MCU', 'kind': 'track', 'layer': 'In2.Cu', 'a': [38.65, 46.6], 'c': [38.45, 46.8], 'width': 0.15},
 {'net': 'GPS_RX_MCU', 'kind': 'track', 'layer': 'In2.Cu', 'a': [38.45, 46.8], 'c': [37.45, 46.8], 'width': 0.15},
 {'net': 'GPS_RX_MCU', 'kind': 'track', 'layer': 'In2.Cu', 'a': [37.45, 46.8], 'c': [37.45, 46.85], 'width': 0.15},
 {'net': 'GPS_RXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.63, 43.5], 'c': [39.63, 42.75], 'width': 0.15},
 {'net': 'GPS_RXD', 'kind': 'via', 'at': [39.63, 42.75], 'width': 0.5, 'drill': 0.3},
 {'net': 'GPS_RXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [41.375, 46.0], 'c': [39.575, 47.8], 'width': 0.15},
 {'net': 'GPS_RXD', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.575, 47.8], 'c': [39.6, 48.3], 'width': 0.15},
 {'net': 'GPS_RXD', 'kind': 'via', 'at': [39.6, 48.3], 'width': 0.5, 'drill': 0.3},
 {'net': 'GPS_RXD', 'kind': 'track', 'layer': 'In2.Cu', 'a': [39.63, 42.75], 'c': [40.1, 43.22], 'width': 0.15},
 {'net': 'GPS_RXD', 'kind': 'track', 'layer': 'In2.Cu', 'a': [40.1, 43.22], 'c': [40.1, 47.8], 'width': 0.15},
 {'net': 'GPS_RXD', 'kind': 'track', 'layer': 'In2.Cu', 'a': [40.1, 47.8], 'c': [39.6, 48.3], 'width': 0.15},
 {'net': 'NRST', 'kind': 'via', 'at': [38.5, 49.2], 'width': 0.5, 'drill': 0.3},
 {'net': 'NRST', 'kind': 'track', 'layer': 'In1.Cu', 'a': [36.435, 47.05], 'c': [36.835, 47.05], 'width': 0.15},
 {'net': 'NRST', 'kind': 'track', 'layer': 'In1.Cu', 'a': [36.835, 47.05], 'c': [38.5, 48.715], 'width': 0.15},
 {'net': 'NRST', 'kind': 'track', 'layer': 'In1.Cu', 'a': [38.5, 48.715], 'c': [38.5, 49.2], 'width': 0.15},
 {'net': 'NRST', 'kind': 'track', 'layer': 'F.Cu', 'a': [38.5, 49.2], 'c': [39.785, 49.2], 'width': 0.15},
 {'net': 'NRST', 'kind': 'track', 'layer': 'F.Cu', 'a': [39.785, 49.2], 'c': [45.335, 54.75], 'width': 0.15},
 {'net': 'GND', 'kind': 'track', 'layer': 'F.Cu', 'a': [36.5, 45.65], 'c': [36.5, 46.3], 'width': 0.2},
 {'net': 'GND', 'kind': 'track', 'layer': 'F.Cu', 'a': [36.5, 46.3], 'c': [37.25, 47.05], 'width': 0.2},
 {'net': 'GND', 'kind': 'track', 'layer': 'F.Cu', 'a': [37.25, 47.05], 'c': [37.275, 47.075], 'width': 0.2},
 {'net': 'GND', 'kind': 'track', 'layer': 'F.Cu', 'a': [37.275, 47.075], 'c': [37.275, 48], 'width': 0.2}]

RADIO_MCU_ADD = [{'net': 'RADIO_M1_MCU', 'kind': 'via', 'at': [38.77, 33.75], 'width': 0.5, 'drill': 0.3},
 {'net': 'RADIO_M1_MCU', 'kind': 'via', 'at': [37.1, 36.6], 'width': 0.5, 'drill': 0.3},
 {'net': 'RADIO_M1_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [38.77, 33], 'c': [38.77, 33.75], 'width': 0.15},
 {'net': 'RADIO_M1_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [37.45, 35.65], 'c': [37.1, 36], 'width': 0.15},
 {'net': 'RADIO_M1_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [37.1, 36], 'c': [37.1, 36.6], 'width': 0.15},
 {'net': 'RADIO_M1_MCU',
  'kind': 'track',
  'layer': 'In2.Cu',
  'a': [38.77, 33.75],
  'c': [37.07, 35.45],
  'width': 0.15},
 {'net': 'RADIO_M1_MCU',
  'kind': 'track',
  'layer': 'In2.Cu',
  'a': [37.07, 35.45],
  'c': [37.07, 36.57],
  'width': 0.15},
 {'net': 'RADIO_M1_MCU',
  'kind': 'track',
  'layer': 'In2.Cu',
  'a': [37.07, 36.57],
  'c': [37.1, 36.6],
  'width': 0.15},
 {'net': 'GND', 'kind': 'track', 'layer': 'F.Cu', 'a': [36.5, 35.65], 'c': [36.5, 36.8], 'width': 0.2},
 {'net': 'GND', 'kind': 'track', 'layer': 'F.Cu', 'a': [36.5, 36.8], 'c': [37.275, 37.575], 'width': 0.2},
 {'net': 'GND', 'kind': 'track', 'layer': 'F.Cu', 'a': [37.275, 37.575], 'c': [37.275, 38], 'width': 0.2}]

RADIO_TX_REMOVE = {'05e3b070-9810-4ec2-ba6f-46d11bd94e53': ('PCB_TRACK', '3V3', 'B.Cu', (38.45, 34.65), (38.15, 34.35), 0.25, None),
 '1ee0a10a-48c3-4260-a6f4-5eb197a7ea68': ('PCB_TRACK', '3V3', 'B.Cu', (38.15, 34.35), (37.05, 34.35), 0.25, None),
 '77c573fe-7623-45d9-b903-6b480cb6cae0': ('PCB_VIA', '3V3', 'F.Cu', (37.05, 34.35), (37.05, 34.35), 0.6, 0.3),
 'a5e00384-71b1-54c4-8d7b-9c0e4243e5dd': ('PCB_TRACK', '3V3', 'B.Cu', (38.45, 34.65), (39.13, 34.65), 0.25, None),
 'e034a505-72ee-5732-8530-6239284a74af': ('PCB_TRACK', '3V3', 'B.Cu', (39.13, 34.65), (39.13, 38.07), 0.25, None),
 'f35860f1-8310-4d84-8942-7e2d3a750003': ('PCB_TRACK', '3V3', 'F.Cu', (37.05, 34.35), (36.45, 33.75), 0.25, None)}
RADIO_TX_ADD = [{'net': '3V3', 'kind': 'via', 'at': [36.94, 34.65], 'width': 0.5, 'drill': 0.3},
 {'net': '3V3', 'kind': 'track', 'layer': 'F.Cu', 'a': [36.45, 33.75], 'c': [36.94, 34.24], 'width': 0.25},
 {'net': '3V3', 'kind': 'track', 'layer': 'F.Cu', 'a': [36.94, 34.24], 'c': [36.94, 34.65], 'width': 0.25},
 {'net': '3V3', 'kind': 'track', 'layer': 'B.Cu', 'a': [36.94, 34.65], 'c': [36.94, 35.0], 'width': 0.25},
 {'net': '3V3', 'kind': 'track', 'layer': 'B.Cu', 'a': [36.94, 35.0], 'c': [38.13, 36.19], 'width': 0.25},
 {'net': '3V3', 'kind': 'track', 'layer': 'B.Cu', 'a': [38.13, 36.19], 'c': [39.13, 36.19], 'width': 0.25},
 {'net': '3V3', 'kind': 'track', 'layer': 'B.Cu', 'a': [39.13, 36.19], 'c': [39.13, 38.07], 'width': 0.25},
 {'net': 'RADIO_TX_MCU', 'kind': 'via', 'at': [38.58, 35.25], 'width': 0.5, 'drill': 0.3},
 {'net': 'RADIO_TX_MCU', 'kind': 'via', 'at': [37.52, 34.3], 'width': 0.5, 'drill': 0.3},
 {'net': 'RADIO_TX_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [38.77, 34.5], 'c': [38.58, 34.69], 'width': 0.15},
 {'net': 'RADIO_TX_MCU',
  'kind': 'track',
  'layer': 'F.Cu',
  'a': [38.58, 34.69],
  'c': [38.58, 35.25],
  'width': 0.15},
 {'net': 'RADIO_TX_MCU',
  'kind': 'track',
  'layer': 'F.Cu',
  'a': [37.45, 33.35],
  'c': [37.52, 33.42],
  'width': 0.15},
 {'net': 'RADIO_TX_MCU', 'kind': 'track', 'layer': 'F.Cu', 'a': [37.52, 33.42], 'c': [37.52, 34.3], 'width': 0.15},
 {'net': 'RADIO_TX_MCU', 'kind': 'track', 'layer': 'B.Cu', 'a': [37.52, 34.3], 'c': [38.47, 35.25], 'width': 0.15},
 {'net': 'RADIO_TX_MCU',
  'kind': 'track',
  'layer': 'B.Cu',
  'a': [38.47, 35.25],
  'c': [38.58, 35.25],
  'width': 0.15}]

def point(xy):
    return pcbnew.VECTOR2I(*(MM(v) for v in xy))


def fingerprint(board, item):
    via = item.GetClass() == 'PCB_VIA'
    return (item.GetClass(), item.GetNetname(), board.GetLayerName(item.GetLayer()),
            tuple(round(mm(v), 6) for v in (item.GetStart().x, item.GetStart().y)),
            tuple(round(mm(v), 6) for v in (item.GetEnd().x, item.GetEnd().y)),
            round(mm(item.GetWidth(pcbnew.F_Cu) if via else item.GetWidth()), 6),
            round(mm(item.GetDrillValue()), 6) if via else None)


def item_for(board, group, index, spec):
    if spec['kind'] == 'via':
        item = pcbnew.PCB_VIA(board)
        item.SetViaType(pcbnew.VIATYPE_THROUGH)
        item.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        item.SetPosition(point(spec['at']))
        item.SetDrill(MM(spec['drill']))
    else:
        item = pcbnew.PCB_TRACK(board)
        item.SetLayer(board.GetLayerID(spec['layer']))
        item.SetStart(point(spec['a'])); item.SetEnd(point(spec['c']))
    item.SetNet(board.FindNet(spec['net']))
    item.SetWidth(MM(spec['width'])); item.SetLocked(True)
    item.SetUuid(pcbnew.KIID(str(uuid.uuid5(NAMESPACE, f'{group}:{index}:{spec!r}'))))
    return item


RADIO_RX_ADD = [
    {'net': 'RADIO_RX_MCU', 'kind': 'via', 'at': [38.58, 36.75], 'width': 0.5, 'drill': 0.3},
    {'net': 'RADIO_RX_MCU', 'kind': 'via', 'at': [34, 35.2], 'width': 0.5, 'drill': 0.3},
    {'net': 'RADIO_RX_MCU', 'kind': 'track', 'layer': 'F.Cu',
     'a': [38.77, 36], 'c': [38.58, 36.19], 'width': 0.15},
    {'net': 'RADIO_RX_MCU', 'kind': 'track', 'layer': 'F.Cu',
     'a': [38.58, 36.19], 'c': [38.58, 36.75], 'width': 0.15},
    {'net': 'RADIO_RX_MCU', 'kind': 'track', 'layer': 'F.Cu',
     'a': [35.55, 33.35], 'c': [34, 34.9], 'width': 0.15},
    {'net': 'RADIO_RX_MCU', 'kind': 'track', 'layer': 'F.Cu',
     'a': [34, 34.9], 'c': [34, 35.2], 'width': 0.15},
    {'net': 'RADIO_RX_MCU', 'kind': 'track', 'layer': 'In1.Cu',
     'a': [34, 35.2], 'c': [37.7, 35.55], 'width': 0.15},
    {'net': 'RADIO_RX_MCU', 'kind': 'track', 'layer': 'In1.Cu',
     'a': [37.7, 35.55], 'c': [38.58, 36.75], 'width': 0.15},
]


def repair(board, groups=('radio',)):
    """Apply selected complete groups, or skip connections already closed.

    radio: direct J130 fanout plus the TLM feed detour. power: retain widths
    while freeing MCU-side radio escape space. gps: connect J131.4, move only
    the enclosing GPS_RX_MCU branch, preserve the CAM_5V pour corridor, and
    retain D131 ground with a short In1 NRST corner.
    radio_mcu: pair with power; join R197 to D130 and retain their ground path.
    radio_tx: pair with power; replace its local 3V3 stitch and close R198 to D130.
    radio_rx: after moving R204, close R199 to D130 with the reviewed In1 bridge.
    The caller must refill and validate native DRC after integration.
    """
    definitions = {'radio': (RADIO_REMOVE, RADIO_ADD), 'power': (POWER_REMOVE, POWER_ADD),
                   'gps': (GPS_REMOVE, GPS_ADD), 'radio_mcu': ({}, RADIO_MCU_ADD),
                   'radio_tx': (RADIO_TX_REMOVE, RADIO_TX_ADD), 'radio_rx': ({}, RADIO_RX_ADD)}
    if set(groups) & {'radio_mcu', 'radio_tx'} and 'power' not in groups:
        raise ValueError('radio_mcu and radio_tx require the power group in the same selection')
    if set(groups) - definitions.keys():
        raise ValueError('Unknown port routing group')
    report = {'applied': [], 'skipped': [], 'removed': [], 'added': [],
              'zones_require_refill': False, 'native_drc_required': True}
    pads = {
        'radio': [('R197', '2', 'RADIO_M1', (39.63, 33)), ('R198', '2', 'RADIO_RXD', (39.63, 34.5)),
                  ('R199', '2', 'RADIO_TXD', (39.63, 36)), ('R200', '2', 'RADIO_AUX', (39.63, 37.5)),
                  ('J130', '2', 'RADIO_M1', (41.375, 32.5)), ('J130', '3', 'RADIO_RXD', (41.375, 33.5)),
                  ('J130', '4', 'RADIO_TXD', (41.375, 34.5)), ('J130', '5', 'RADIO_AUX', (41.375, 35.5)),
                  ('J130', '6', 'TLM_5V', (41.375, 36.5))],
        'gps': [('R201', '2', 'GPS_RXD', (39.63, 43.5)), ('R202', '1', 'GPS_RX_MCU', (38.77, 45)),
                ('D131', '4', 'GPS_RX_MCU', (37.45, 43.35)), ('J131', '4', 'GPS_RXD', (41.375, 46)),
                ('D131', '2', 'GND', (36.5, 45.65)), ('C180', '2', 'GND', (37.275, 48))],
        'power': [],
        'radio_rx': [('R199', '1', 'RADIO_RX_MCU', (38.77, 36)),
                     ('D130', '6', 'RADIO_RX_MCU', (35.55, 33.35)),
                     ('R204', '1', 'RADIO_M1_MCU', (38.595944, 39.204056)),
                     ('R204', '2', 'GND', (39.204056, 38.595944))],
        'radio_tx': [('R198', '1', 'RADIO_TX_MCU', (38.77, 34.5)),
                     ('D130', '4', 'RADIO_TX_MCU', (37.45, 33.35)),
                     ('D130', '5', '3V3', (36.5, 33.35))],
        'radio_mcu': [('R197', '1', 'RADIO_M1_MCU', (38.77, 33)),
                      ('D130', '3', 'RADIO_M1_MCU', (37.45, 35.65)),
                      ('D130', '2', 'GND', (36.5, 35.65)), ('C179', '2', 'GND', (37.275, 38))],
    }
    checked = {}
    for group in groups:
        for ref, number, net, xy in pads[group]:
            footprint = board.FindFootprintByReference(ref)
            pad = footprint.FindPadByNumber(number) if footprint else None
            if (not pad or pad.GetNetname() != net or not pad.IsOnLayer(pcbnew.F_Cu)
                    or pad.GetPosition() != point(xy)):
                raise ValueError(f'{ref}.{number}: unexpected R6 port pad/net/position')
            checked[ref, number] = pad
    existing = {item.m_Uuid.AsString(): item for item in board.GetTracks()}
    board.BuildConnectivity()
    connected = board.GetConnectivity()
    def joined(a, c):
        return checked[c].m_Uuid.AsString() in {item.m_Uuid.AsString()
                                              for item in connected.GetConnectedItems(checked[a])}
    pending = []
    for group in dict.fromkeys(groups):
        removals, additions = definitions[group]
        candidates = [item_for(board, group, i, spec) for i, spec in enumerate(additions)]
        own = [item.m_Uuid.AsString() for item in candidates]
        for item in candidates:
            key = item.m_Uuid.AsString()
            if key in existing and fingerprint(board, existing[key]) != fingerprint(board, item):
                raise ValueError(f'{key}: changed generated port route')
        # The TX stitch replaces two generated power segments. Recognize only
        # its complete guarded geometry; partial or changed upgrades still fail.
        if group == 'power':
            upgrade = [item_for(board, 'radio_tx', i, spec) for i, spec in enumerate(RADIO_TX_ADD)]
            upgraded = all(item.m_Uuid.AsString() in existing and
                           fingerprint(board, existing[item.m_Uuid.AsString()]) == fingerprint(board, item)
                           for item in upgrade)
            retained = all((key not in existing if key in RADIO_TX_REMOVE else
                            key in existing and fingerprint(board, existing[key]) == fingerprint(board, item))
                           for key, item in zip(own, candidates))
            if upgraded and retained and not any(key in existing for key in removals | RADIO_TX_REMOVE):
                report['skipped'].append('power: complete radio_tx upgrade already applied')
                continue
        present = [key for key in own if key in existing]
        if present:
            if len(present) != len(own) or any(key in existing for key in removals):
                raise ValueError('Partial generated port routing; refusing mixed old/new geometry')
            report['skipped'].append(f'{group}: already applied')
            continue
        if ((group == 'radio' and all(joined((ref, '2'), ('J130', pin))
                for ref, pin in (('R197', '2'), ('R198', '3'), ('R200', '5')))) or
                (group == 'gps' and joined(('R201', '2'), ('J131', '4'))) or
                (group == 'radio_mcu' and joined(('R197', '1'), ('D130', '3'))) or
                (group == 'radio_tx' and joined(('R198', '1'), ('D130', '4'))) or
                (group == 'radio_rx' and joined(('R199', '1'), ('D130', '6')))):
            report['skipped'].append(f'{group}: requested connections already closed')
            continue
        for key, expected in removals.items():
            if key not in existing or fingerprint(board, existing[key]) != expected:
                raise ValueError(f'{key}: original local route changed; refusing stale repair')
        pending.append((group, [(key, existing[key]) for key in removals], candidates))
        # Validate later groups against the preceding planned geometry.
        for key in removals:
            del existing[key]
        for item in candidates:
            existing[item.m_Uuid.AsString()] = item
    # All selected groups are checked before any mutation.
    for group, removals, candidates in pending:
        for key, item in removals:
            board.Delete(item); report['removed'].append(key)
        for item in candidates:
            board.Add(item); report['added'].append(item.m_Uuid.AsString())
        report['applied'].append(group)
    if pending:
        board.BuildConnectivity()
        report['zones_require_refill'] = True
    return report


PULLDOWN_ADD = [{'net': 'RADIO_M1_MCU', 'kind': 'via', 'at': [38, 39.8], 'width': 0.5, 'drill': 0.3},
 {'net': 'RADIO_M1_MCU',
  'kind': 'track',
  'layer': 'F.Cu',
  'a': [38.595944, 39.204056],
  'c': [38, 39.8],
  'width': 0.15},
 {'net': 'RADIO_M1_MCU', 'kind': 'track', 'layer': 'In2.Cu', 'a': [37.1, 36.6], 'c': [37.1, 38.3], 'width': 0.15},
 {'net': 'RADIO_M1_MCU', 'kind': 'track', 'layer': 'In2.Cu', 'a': [37.1, 38.3], 'c': [38.0, 39.2], 'width': 0.15},
 {'net': 'RADIO_M1_MCU', 'kind': 'track', 'layer': 'In2.Cu', 'a': [38.0, 39.2], 'c': [38.0, 39.8], 'width': 0.15}]


def repair_pulldown(board):
    """Move unrouted R204 into the radio block and join its existing M1 component."""
    board.BuildConnectivity()
    footprint = board.FindFootprintByReference('R204')
    if not footprint:
        raise ValueError('R204 is missing')
    signal, ground = (footprint.FindPadByNumber(n) for n in ('1', '2'))
    if (not signal or not ground or signal.GetNetname() != 'RADIO_M1_MCU'
            or ground.GetNetname() != 'GND' or not footprint.IsOnLayer(pcbnew.F_Cu)):
        raise ValueError('R204 pad/net/layer changed')
    old_position, new_position = point((34, 35.5)), point((38.9, 38.9))
    old = footprint.GetPosition() == old_position and abs(footprint.GetOrientationDegrees() - 90) < 1e-6
    new = footprint.GetPosition() == new_position and abs(footprint.GetOrientationDegrees() - 45) < 1e-6
    if not (old or new):
        raise ValueError('R204 position/orientation changed')
    existing = {item.m_Uuid.AsString(): item for item in board.GetTracks()}
    candidates = [item_for(board, 'radio_pulldown', i, spec) for i, spec in enumerate(PULLDOWN_ADD)]
    own = [item.m_Uuid.AsString() for item in candidates]
    for item in candidates:
        key = item.m_Uuid.AsString()
        if key in existing and fingerprint(board, existing[key]) != fingerprint(board, item):
            raise ValueError('Changed generated R204 route')
    present = [key for key in own if key in existing]
    report = {'applied': False, 'added': [], 'zones_require_refill': False, 'native_drc_required': True}
    if new and len(present) == len(own):
        report['skipped'] = 'already applied'
        return report
    if present or new:
        raise ValueError('Partial R204 placement/routing; refusing mixed geometry')
    if signal.GetPosition() != point((34, 35.93)) or ground.GetPosition() != point((34, 35.07)):
        raise ValueError('R204 original pad geometry changed')
    target = board.FindFootprintByReference('D130').FindPadByNumber('3')
    if target.m_Uuid.AsString() in {x.m_Uuid.AsString() for x in board.GetConnectivity().GetConnectedItems(signal)}:
        report['skipped'] = 'pulldown already connected'
        return report
    anchor_spec = next(spec for spec in RADIO_MCU_ADD if spec['kind'] == 'via' and spec['at'] == [37.1, 36.6])
    anchor_index = RADIO_MCU_ADD.index(anchor_spec)
    anchor = item_for(board, 'radio_mcu', anchor_index, anchor_spec)
    key = anchor.m_Uuid.AsString()
    if key not in existing or fingerprint(board, existing[key]) != fingerprint(board, anchor):
        raise ValueError('Reviewed M1 anchor is missing or changed')
    for pad in (signal, ground):
        shape = pad.GetEffectiveShape(pcbnew.F_Cu)
        if any(t.IsOnLayer(pcbnew.F_Cu) and shape.Collide(t.GetEffectiveShape(pcbnew.F_Cu), 0)
               for t in board.GetTracks()):
            raise ValueError('R204 has attached copper; refusing to tear a routed lead')
    silk_footprints = [board.FindFootprintByReference(ref) for ref in ('R204', 'R200', 'C179')]
    if not all(silk_footprints):
        raise ValueError('A reference for final silkscreen is missing')
    # No mutation until placement, anchor and all generated copper pass the guards.
    footprint.SetPosition(new_position)
    footprint.SetOrientationDegrees(45)
    for item in silk_footprints:
        item.Reference().SetVisible(False)
    for item in candidates:
        board.Add(item)
        report['added'].append(item.m_Uuid.AsString())
    board.BuildConnectivity()
    report.update(applied=True, zones_require_refill=True, position_mm=(38.9, 38.9),
                  orientation_degrees=45, references_for_final_silk=['R204', 'R200', 'C179'])
    return report
