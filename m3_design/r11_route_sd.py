"""R11 family `sd` (stage C1b, D-R11-44): the microSD bus, U1's SPI3 balls (B8 MISO, B9 SCK, C8 MOSI, D8 CS) to the
pull-up column R460-R464 and J430, and the two data lines DAT1 / DAT2 from their pull-ups to J430. Explicit tables only
(D-R11-07), frozen in r11_escape.py; the escapes are pinned in r11_fanout.tsv (stageC1b.md)."""

NETS = ('SD_SCK', 'SD_MISO', 'SD_CS', 'SD_DAT1', 'SD_DAT2', 'SD_MOSI')   # SD_MOSI: three vias since D-R11-63; its via
# (29.80, 17.05) keeps the gate lane's critical_via_no_gnd allowlist entry (D-R11-61)


def draw(d):
    import r11_escape
    r11_escape.draw(d, 'sd')
