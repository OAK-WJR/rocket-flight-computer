"""SPI3 microSD, explicitly drawn west escapes and bottom fan-in.

The four SPI lanes leave U1's west pins on F.Cu, drop through one via each and run on B.Cu to the socket's pads; the
USB limiter's output (USB_LIMITED) crosses them on an F.Cu overpass (r10_route_usb).  The socket J430 sits 0.2 mm east of
the previous frame (DX), so every point that meets a pad is relative to it.
"""

def draw(d):
    t,p,v=d.track,d.pad,d.via
    DX=round(p('J430.7')[0]-20.605,4)
    # Each lane leaves its pin west on F.Cu, steps south on a 45 degree segment (the outer lane CS first) and drops through
    # its via; the vias sit on y 38.0 / 39.0 / 39.6 / 40.2 so every other critical centreline passes >= 0.6 mm from each
    # (the In1 void radius is 0.4 mm), then B.Cu runs north and north-east to the socket.
    t('SD_SCK','F',.2,[p('U1.78'),(11.7,38.0)]);v('SD_SCK',(11.7,38.0))
    t('SD_MISO','F',.2,[p('U1.79'),(12.5,38.5),(12.0,39.0),(11.0,39.0)]);v('SD_MISO',(11.0,39.0))
    t('SD_MOSI','F',.2,[p('U1.80'),(13.0,39.0),(12.4,39.6)]);v('SD_MOSI',(12.4,39.6))
    t('SD_CS','F',.2,[p('U1.81'),(13.7,39.5),(13.0,40.2)]);v('SD_CS',(13.0,40.2))
    for at in ((10.3,38.3),(11.7,40.0)):
        v('GND',at)
    # Each lane: a vertical north, a diagonal NE, a horizontal, a vertical north, a second diagonal and a straight entry
    # into the pad from the south.  MISO's second diagonal is offset 0.25 mm from the first (no knee).
    t('SD_MISO','B',.2,[(11.0,39.0),(11.0,35.5),(15.1,31.4),(18.7,31.4),(18.7,27.4),(20.605+DX,27.4-1.905-DX),p('J430.7')])
    t('SD_SCK','B',.2,[(11.7,38.0),(11.7,36.2),(15.8,32.1),(19.4,32.1),(19.4,27.705),(21.505,25.6),(21.505+DX+1.3,25.6),p('J430.5')])
    t('SD_MOSI','B',.2,[(12.4,39.6),(12.4,36.9),(16.5,32.8),(20.1,32.8),(20.1,27.7),(21.6,26.2),(25.005+DX,26.2),p('J430.3')])
    t('SD_CS','B',.2,[(13.0,40.2),(13.0,37.6),(17.1,33.5),(20.8,33.5),(20.8,27.7),(21.5,27.0),(26.105+DX,27.0),p('J430.2')])
    # Pull-up components sit beyond the retaining-body courtyard on B.Cu.
    t('SD_MISO','B',.2,[p('J430.7'),(20.605+DX,22.48+DX),p('R462.1')])
    t('SD_DAT1','B',.2,[p('J430.8'),(19.505+DX,22.0),(16.405+DX,18.9),p('R463.1')])
    t('SD_MOSI','B',.2,[p('J430.3'),(25.005+DX,20.0+DX),(23.375,18.37),p('R461.1')])
    t('SD_CS','B',.2,[p('J430.2'),(26.105+DX,17.67-DX),p('R460.1')])
    # SD_DAT2: a B.Cu stub north from the pad to one via, then a straight F.Cu link to R464, which takes its 3V3 from the
    # socket pin 4's via and carries C461.1's 3V3.  The GND partner via sits within 1.5 mm of the signal via, west of
    # the GPS lanes' band.
    t('SD_DAT2','B',.2,[p('J430.1'),(27.205+DX,22.18)]);v('SD_DAT2',(27.205+DX,22.18))
    t('SD_DAT2','F',.2,[(27.205+DX,22.18),p('R464.1')]);v('GND',(28.2,22.4))
    t('3V3','F',.2,[p('R464.2'),(23.905+DX,23.0)])
    t('3V3','F',.3,[p('C461.1'),(26.605,20.3),p('R464.2')])
    for ref,at in [('R461',(24.5,18.5)),('R462',(13.375,15.8)),('R463',(13.375,20.0))]:
        corners=[(25.025,17.975)] if ref=='R461' else []
        t('3V3','B',.2,[p(ref+'.2'),*corners,at]);v('3V3',at)
    t('3V3','B',.2,[p('R460.2'),(28.625,17.0),(27.725,17.9),(27.4,17.9),(27.4,18.6),(27.0,19.0)]);v('3V3',(27.0,19.0))
    # Opposite-face local bypasses connect to the same 3V3 plane at the socket.
    t('3V3','B',.3,[p('J430.4'),(23.905+DX,23.0)]);v('3V3',(23.905+DX,23.0))
    t('3V3','F',.3,[(23.905+DX,23.0),(23.255,22.35),p('C460.1')])
    t('GND','F',.3,[p('C460.2'),(21.705+DX,22.8)])
    for pin,at in [(6,(21.705+DX,22.8)),(9,(30.875+DX,31.6)),(10,(15.6+DX,30.5)),(11,(18.725+DX,23.3)),(12,(34.0,22.4))]:
        corners=[(16.1+DX,30.0)] if pin==10 else [(30.875+DX,22.4)] if pin==12 else []
        t('GND','B',.3,[p('J430.'+str(pin)),*corners,at]);v('GND',at)
