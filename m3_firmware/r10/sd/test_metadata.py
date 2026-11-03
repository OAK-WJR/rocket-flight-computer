"""Real portable C against independent host CRC/field calculations; no card IO."""
import binascii
import ctypes as c
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]))
from m3_firmware.r10.sd import verify
import csv,io,copy,xml.etree.ElementTree as ET


def crc7(data):
    # Polynomial long division, independent of the firmware's bitwise LFSR.
    value=int.from_bytes(data,'big')<<7
    while value.bit_length()>7:
        value^=0x89<<(value.bit_length()-8)
    return value


def field(data,high,low,value):
    n=int.from_bytes(data,'big');mask=((1<<(high-low+1))-1)<<low
    n=(n&~mask)|((value<<low)&mask)
    return n.to_bytes(16,'big')


def packet(data):
    data=bytes(data[:15])+bytes([(crc7(data[:15])<<1)|1])
    return b'\0\xfe'+data+binascii.crc_hqx(data,0).to_bytes(2,'big')


def repacket(data):
    """Recalculate only transport CRC to expose an invalid register CRC/end bit."""
    return data[:18]+binascii.crc_hqx(data[2:18],0).to_bytes(2,'big')


def cid():
    p=bytes(16)
    for high,low,value in ((127,120,0x1b),(119,104,int.from_bytes(b'SD','big')),
                           (103,64,int.from_bytes(b'TEST1','big')),(63,56,0x62),
                           (55,24,0x12345678),(19,8,(26<<4)|11)):
        p=field(p,high,low,value)
    return packet(p)


def csd(structure=1,size=0xffff,read=9,multiplier=3):
    p=field(bytes(16),127,126,structure);p=field(p,83,80,read)
    if structure==0:
        p=field(p,73,62,size);p=field(p,49,47,multiplier)
    else:p=field(p,69,48,size)
    return packet(p)


def ocr(block=True):
    return b'\0'+(0x80ff8000|(int(block)<<30)).to_bytes(4,'big')


class Metadata(c.Structure):
    _fields_=[('capacity',c.c_uint64),('sectors',c.c_uint64),
              ('errors',c.c_uint32*3),('lengths',c.c_uint32*3),('ocr',c.c_uint32),('serial',c.c_uint32),
              ('year',c.c_uint16),('month',c.c_uint8),('mid',c.c_uint8),
              ('major',c.c_uint8),('minor',c.c_uint8),('structure',c.c_uint8),
              ('block',c.c_uint8),('valid',c.c_uint8),('oem',c.c_uint8*2),('product',c.c_uint8*5),
              ('raw_ocr',c.c_uint8*5),('raw_cid',c.c_uint8*20),('raw_csd',c.c_uint8*20)]


class ActualC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();root=Path(cls.temp.name)
        harness=root/'harness.c'
        harness.write_text('#include "metadata.c"\n#include <stddef.h>\n'
            'unsigned metadata_size(void){return sizeof(r10_sd_metadata);}\n'
            'unsigned crc16_vector(const uint8_t *p,unsigned n){return crc16(p,n);}\n')
        library=root/'sd.dylib'
        subprocess.run(['/usr/bin/clang','-dynamiclib','-O2','-std=c11','-Wall','-Wextra','-Werror',
                        '-I'+str(HERE),str(harness),'-o',str(library)],check=True,capture_output=True)
        cls.lib=c.CDLL(str(library));u8=c.POINTER(c.c_uint8)
        cls.lib.r10_sd_metadata_decode.argtypes=[u8,c.c_uint,u8,c.c_uint,u8,c.c_uint,c.POINTER(Metadata)]
        cls.lib.r10_sd_metadata_decode.restype=c.c_uint
        cls.lib.r10_sd_metadata_frame.argtypes=[c.c_uint,u8];cls.lib.r10_sd_metadata_frame.restype=c.c_uint
        cls.lib.metadata_size.restype=c.c_uint
        cls.lib.crc16_vector.argtypes=[u8,c.c_uint];cls.lib.crc16_vector.restype=c.c_uint

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def decode(self,op=None,cp=None,sp=None,lengths=None):
        packets=[ocr() if op is None else op,cid() if cp is None else cp,csd() if sp is None else sp]
        counts=[len(x) for x in packets] if lengths is None else lengths
        guards=[];args=[]
        for p,n in zip(packets,counts):
            memory=(c.c_uint8*(len(p)+32))(*([0xa5]*16+list(p)+[0xa5]*16))
            guards.append((memory,bytes(memory)))
            args.extend([c.cast(c.byref(memory,16),c.POINTER(c.c_uint8)),n])
        dest=(c.c_uint8*(c.sizeof(Metadata)+32))(*([0xa5]*(c.sizeof(Metadata)+32)))
        out=Metadata.from_buffer(dest,16)
        code=self.lib.r10_sd_metadata_decode(*args,c.byref(out))
        self.assertEqual(bytes(dest[:16]),b'\xa5'*16);self.assertEqual(bytes(dest[-16:]),b'\xa5'*16)
        for a,b in guards:self.assertEqual(bytes(a),b)
        return code,Metadata.from_buffer_copy(bytes(out))

    def test_native_structure_and_standard_crc16_vector(self):
        self.assertEqual(self.lib.metadata_size(),c.sizeof(Metadata))
        self.assertEqual(self.lib.crc16_vector((c.c_uint8*512)(*([255]*512)),512),0x7fa1)

    def test_known_cmd0_cmd8_crc_and_all_fixed_frames(self):
        opcodes=[0,8,59,55,41,41,58,9,10];arguments=[0,0x1aa,1,0,0,0x40000000,0,0,0]
        for i,(op,arg) in enumerate(zip(opcodes,arguments)):
            out=(c.c_uint8*6)(*([0xa5]*6))
            self.assertEqual(self.lib.r10_sd_metadata_frame(i,out),0)
            expected=bytes([0x40|op])+arg.to_bytes(4,'big')
            self.assertEqual(bytes(out),expected+bytes([(crc7(expected)<<1)|1]))
            if i in (0,1):self.assertEqual(out[5],0x95 if i==0 else 0x87)
        self.assertTrue(set(opcodes).isdisjoint({17,18,24,25,27,28,29,32,33,38,42}))

    def test_unknown_frame_ids_cannot_emit_write_or_erase_commands(self):
        for i in list(range(9,65))+[0xffffffff]:
            out=(c.c_uint8*6)(*([0xa5]*6))
            self.assertEqual(self.lib.r10_sd_metadata_frame(i,out),1)
            self.assertEqual(bytes(out),bytes(6))
        self.assertEqual(self.lib.r10_sd_metadata_frame(0,None),1)

    def test_full_cid_fields_and_nominal_csd_capacity(self):
        code,o=self.decode();self.assertEqual(code,0);self.assertTrue(o.valid)
        self.assertEqual((o.mid,bytes(o.oem),bytes(o.product)),(0x1b,b'SD',b'TEST1'))
        self.assertEqual((o.major,o.minor,o.serial,o.year,o.month),(6,2,0x12345678,2026,11))
        self.assertEqual((o.capacity,o.sectors,o.block,o.structure),(32<<30,1<<26,1,1))

    def test_csd_capacity_extremes_use_64_bit_math(self):
        for size in (0,0xfff,0xffff,0x1fffff,0x3fffff):
            code,o=self.decode(sp=csd(size=size));self.assertEqual(code,0)
            self.assertEqual(o.capacity,(size+1)<<19);self.assertEqual(o.sectors,(size+1)<<10)
        self.assertEqual(o.sectors,1<<32)

    def test_randomized_independent_v1_and_v2_geometry(self):
        rng=random.Random(0x5344)
        for _ in range(500):
            size=rng.randrange(1<<22);code,o=self.decode(sp=csd(size=size))
            self.assertEqual(code,0);self.assertEqual(o.capacity,(size+1)*512*1024)
            size=rng.randrange(4096);mult=rng.randrange(8);read=rng.choice((9,10,11))
            expected=(size+1)*(1<<(mult+2))*(1<<read)
            code,o=self.decode(op=ocr(False),sp=csd(0,size,read,mult))
            self.assertEqual(code,0 if expected<=1<<31 else 12)
            self.assertEqual(o.capacity,expected if not code else 0)

    def test_csd_addressing_disagreement_never_changes_address_mode_silently(self):
        for op,sp in ((ocr(False),csd()),(ocr(),csd(0,1000))):
            code,o=self.decode(op=op,sp=sp);self.assertEqual(code,13)
            self.assertFalse(o.valid);self.assertEqual(o.capacity,0)

    def test_sdsc_bounds_and_reserved_read_lengths(self):
        code,o=self.decode(op=ocr(False),sp=csd(0,4095,10,7))
        self.assertEqual(code,0);self.assertEqual(o.capacity,1<<31)
        for read in list(range(9))+list(range(12,16)):
            code,o=self.decode(op=ocr(False),sp=csd(0,1000,read,1))
            self.assertEqual(code,12);self.assertFalse(o.valid)
        code,o=self.decode(op=ocr(False),sp=csd(0,4095,11,7));self.assertEqual(code,12)

    def test_unsupported_csd_structures_keep_raw_but_never_qualify_spi_capacity(self):
        for version in (2,3):
            raw=csd(version);code,o=self.decode(sp=raw)
            self.assertEqual(code,11);self.assertFalse(o.valid);self.assertEqual(o.capacity,0)
            self.assertEqual(bytes(o.raw_csd),raw);self.assertEqual(o.structure,version)

    def test_every_single_register_packet_bit_error_is_detected(self):
        for which,original in (('cp',cid()),('sp',csd())):
            for bit in range(160):
                value=bytearray(original);value[bit//8]^=1<<(bit%8)
                code,o=self.decode(**{which:bytes(value)})
                self.assertNotEqual(code,0);self.assertFalse(o.valid)

    def test_valid_transport_crc_does_not_hide_invalid_register_crc_or_end_bit(self):
        for which,original in (('cp',cid()),('sp',csd())):
            bad=bytearray(original);bad[7]^=1
            code,o=self.decode(**{which:repacket(bytes(bad))});self.assertEqual(code,7)
            bad=bytearray(original);bad[17]&=0xfe
            code,o=self.decode(**{which:repacket(bytes(bad))});self.assertEqual(code,6)

    def test_bad_cid_bcd_or_date_is_not_reported_as_a_valid_identity(self):
        p=cid()[2:18]
        for hi,lo,value in ((63,56,0xa1),(63,56,0x1f),(11,8,0),(11,8,13)):
            code,o=self.decode(cp=packet(field(p,hi,lo,value)))
            self.assertEqual(code,8);self.assertFalse(o.valid);self.assertEqual(o.serial,0)

    def test_identity_text_is_retained_as_untrusted_bytes(self):
        p=cid()[2:18];p=field(p,119,104,0x0a0d);p=field(p,103,64,int.from_bytes(b'<\0\x80\xff`','big'))
        code,o=self.decode(cp=packet(p));self.assertEqual(code,0)
        self.assertEqual(bytes(o.oem),b'\n\r');self.assertEqual(bytes(o.product),b'<\0\x80\xff`')

    def test_ocr_rejects_idle_not_ready_and_no_nominal_voltage_overlap(self):
        for op,error in ((b'\1'+ocr()[1:],3),(b'\0'+(0x40ff8000).to_bytes(4,'big'),9),
                         (b'\0'+(0xc0000080).to_bytes(4,'big'),10)):
            code,o=self.decode(op=op);self.assertEqual(code,error)
            self.assertEqual(bytes(o.raw_ocr),op);self.assertFalse(o.valid)

    def test_read_error_or_busy_token_is_not_parsed_as_register_data(self):
        for token in (0,1,8,0xfc,0xfd,0xff):
            p=bytearray(cid());p[1]=token;code,o=self.decode(cp=bytes(p))
            self.assertEqual(code,4);self.assertEqual(o.raw_cid[1],token)
        p=bytearray(cid());p[0]=4;code,o=self.decode(cp=bytes(p));self.assertEqual(code,3)

    def test_every_bounded_partial_prefix_is_retained_without_sample_claim(self):
        originals=[ocr(),cid(),csd()]
        for slot,p in enumerate(originals):
            for count in range(len(p)):
                values=originals.copy();values[slot]=p[:count]
                code,o=self.decode(*values);self.assertEqual(code,2);self.assertFalse(o.valid)
                self.assertEqual(o.lengths[slot],count)
                raw=(o.raw_ocr,o.raw_cid,o.raw_csd)[slot]
                self.assertEqual(bytes(raw[:count]),p[:count]);self.assertEqual(bytes(raw[count:]),bytes(len(p)-count))

    def test_excessive_lengths_and_null_inputs_are_checked_before_memory_reads(self):
        for slot,limit in enumerate((5,20,20)):
            counts=[5,20,20];counts[slot]=0xffffffff
            code,o=self.decode(lengths=counts);self.assertEqual(code,1);self.assertFalse(o.valid)
            self.assertEqual(o.lengths[slot],0xffffffff)
        o=Metadata();self.assertEqual(self.lib.r10_sd_metadata_decode(None,5,None,0,None,0,c.byref(o)),1)
        self.assertEqual(list(o.errors),[1,2,2]);self.assertFalse(o.valid)
        self.assertEqual(self.lib.r10_sd_metadata_decode(None,0,None,0,None,0,None),1)

    def test_prior_success_is_cleared_on_partial_next_observation(self):
        arrays=[(c.c_uint8*len(p))(*p) for p in (ocr(),cid(),csd())]
        out=Metadata();self.assertEqual(self.lib.r10_sd_metadata_decode(arrays[0],5,arrays[1],20,arrays[2],20,c.byref(out)),0)
        self.assertTrue(out.valid)
        code=self.lib.r10_sd_metadata_decode(arrays[0],1,arrays[1],3,arrays[2],2,c.byref(out))
        self.assertEqual(code,2);self.assertFalse(out.valid)
        self.assertEqual((out.serial,out.capacity,out.year),(0,0,0))


class SourceBinding(unittest.TestCase):
    def setUp(self):
        self.tree=ET.fromstring((verify.ROOT/verify.NETLIST).read_bytes())
        self.rows=list(csv.DictReader(io.StringIO((verify.ROOT/verify.PIN_TABLE).read_text()),delimiter='\t'))

    def node(self,endpoint):
        ref,pin=endpoint.split('.')
        return next(n for n in self.tree.findall('./nets/net/node') if n.get('ref')==ref and n.get('pin')==pin)

    def test_exact_current_source_and_no_card_detect_or_native_driver_claim(self):
        result=verify.verify();self.assertEqual((result['endpoints'],result['pins']),(30,4))
        self.assertFalse(result['independent_card_detect']);self.assertFalse(result['hardware_tested'])
        self.assertFalse(result['native_adapter_implemented'])
        p=json.loads((HERE/'provenance.json').read_text())
        self.assertFalse(p['image_linked']);self.assertFalse(p['hardware_tested'])

    def test_swapped_data_or_supply_is_rejected(self):
        for endpoint in ('J430.3','J430.4','J430.6','R460.2','C461.1'):
            self.setUp();n=self.node(endpoint);n.set('pin','99')
            with self.assertRaises(ValueError):verify.contract(self.tree,self.rows)

    def test_unreviewed_bus_fanout_is_rejected(self):
        net=self.tree.find("./nets/net[@name='SD_CS']")
        ET.SubElement(net,'node',dict(ref='U1',pin='3',pinfunction='PE4_3'))
        with self.assertRaises(ValueError):verify.contract(self.tree,self.rows)

    def test_part_footprint_and_duplicate_fields_are_rejected(self):
        for mode in ('part','footprint','duplicate'):
            self.setUp();p=self.tree.find("./components/comp[@ref='J430']")
            if mode=='part':p.find('./value').text='different socket'
            elif mode=='footprint':p.find('./footprint').text='different land'
            else:ET.SubElement(p.find('fields'),'field',dict(name='LCSC')).text='C0'
            with self.assertRaises(ValueError):verify.contract(self.tree,self.rows)

    def test_changed_alternate_function_or_reset_detect_contract_is_rejected(self):
        for pin in ('78','79','80','81'):
            rows=copy.deepcopy(self.rows)
            row=next(r for r in rows if r['pin']==pin)
            if pin=='81':row['reset_contract']='has card detect'
            else:row['mode_af']='AF5 SPI1'
            with self.assertRaises(ValueError):verify.contract(self.tree,rows)


if __name__=='__main__':unittest.main()
