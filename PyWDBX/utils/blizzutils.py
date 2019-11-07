from io import BytesIO

class BitsIO:
    def __init__(self, data):
        self.file = BytesIO(data)

        self.curbyte = None
        self.bitsLeft = 0

    def read(self, bits):
        allbytes = b''
        curbyte = 0
        for x in range(bits):
            if x%8 == 0 and x>0:
                allbytes = allbytes+bytes([curbyte])
                curbyte = 0
            curbyte = (curbyte<<1) | self.readbit()

        return allbytes+bytes([curbyte])

    def seek(self, bits):
        off_bytes = bits//8
        off_bits = bits%8

        self.file.seek(off_bytes,0)

        if off_bits > 0:
            self.bitsLeft -= off_bits
        
        if off_bits < 0:
            raise NotImplementedError("Can't seek backwards in BitsIO (yet)")
    
    def readbit(self):
        while self.bitsLeft <= 0:
            self.curbyte = self.file.read(1)[0]
            self.bitsLeft += 8
        
        bit = self.curbyte & (1 << self.bitsLeft-1)
        bit >>= self.bitsLeft-1

        # print(bit)

        self.bitsLeft -= 1

        return bit

def cstr(ar):
    s = b""
    i = 0
    while i < len(ar) and ar[i] != 0:
        s += bytes([ar[i]])
        i += 1
    return s

def var_int(f:object,l:int,le=True):
    return int.from_bytes(f.read(l), byteorder='little' if le else 'big', signed=False)

def jenkins_hash(key:bytes):
    h=0
    for x in key:
        h+=ord(x)
        h=h&0xffffffff
        h+=h<<10
        h=h&0xffffffff
        h^=h>>6
        h=h&0xffffffff
    h+=h<<3
    h=h&0xffffffff
    h^=h>>11
    h=h&0xffffffff
    h+=h<<15
    h=h&0xffffffff
    return h

def rot(x,k):
    return (((x)<<(k)) | ((x)>>(32-(k))))

def mix(a, b, c):
    a &= 0xffffffff; b &= 0xffffffff; c &= 0xffffffff
    a -= c; a &= 0xffffffff; a ^= rot(c,4);  a &= 0xffffffff; c += b; c &= 0xffffffff
    b -= a; b &= 0xffffffff; b ^= rot(a,6);  b &= 0xffffffff; a += c; a &= 0xffffffff
    c -= b; c &= 0xffffffff; c ^= rot(b,8);  c &= 0xffffffff; b += a; b &= 0xffffffff
    a -= c; a &= 0xffffffff; a ^= rot(c,16); a &= 0xffffffff; c += b; c &= 0xffffffff
    b -= a; b &= 0xffffffff; b ^= rot(a,19); b &= 0xffffffff; a += c; a &= 0xffffffff
    c -= b; c &= 0xffffffff; c ^= rot(b,4);  c &= 0xffffffff; b += a; b &= 0xffffffff
    return a, b, c

def final(a, b, c):
    a &= 0xffffffff; b &= 0xffffffff; c &= 0xffffffff
    c ^= b; c &= 0xffffffff; c -= rot(b,14); c &= 0xffffffff
    a ^= c; a &= 0xffffffff; a -= rot(c,11); a &= 0xffffffff
    b ^= a; b &= 0xffffffff; b -= rot(a,25); b &= 0xffffffff
    c ^= b; c &= 0xffffffff; c -= rot(b,16); c &= 0xffffffff
    a ^= c; a &= 0xffffffff; a -= rot(c,4);  a &= 0xffffffff
    b ^= a; b &= 0xffffffff; b -= rot(a,14); b &= 0xffffffff
    c ^= b; c &= 0xffffffff; c -= rot(b,24); c &= 0xffffffff
    return a, b, c

def hashlittle2(data, initval = 0, initval2 = 0):
    length = lenpos = len(data)

    a = b = c = (0xdeadbeef + (length) + initval)

    c += initval2; c &= 0xffffffff

    p = 0  # string offset
    while lenpos > 12:
        a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24)); a &= 0xffffffff
        b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16) + (ord(data[p+7])<<24)); b &= 0xffffffff
        c += (ord(data[p+8]) + (ord(data[p+9])<<8) + (ord(data[p+10])<<16) + (ord(data[p+11])<<24)); c &= 0xffffffff
        a, b, c = mix(a, b, c)
        p += 12
        lenpos -= 12

    if lenpos == 12: c += (ord(data[p+8]) + (ord(data[p+9])<<8) + (ord(data[p+10])<<16) + (ord(data[p+11])<<24)); b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16) + (ord(data[p+7])<<24)); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24));
    if lenpos == 11: c += (ord(data[p+8]) + (ord(data[p+9])<<8) + (ord(data[p+10])<<16)); b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16) + (ord(data[p+7])<<24)); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24));
    if lenpos == 10: c += (ord(data[p+8]) + (ord(data[p+9])<<8)); b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16) + (ord(data[p+7])<<24)); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24));
    if lenpos == 9:  c += (ord(data[p+8])); b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16) + (ord(data[p+7])<<24)); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24));
    if lenpos == 8:  b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16) + (ord(data[p+7])<<24)); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24));
    if lenpos == 7:  b += (ord(data[p+4]) + (ord(data[p+5])<<8) + (ord(data[p+6])<<16)); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24));
    if lenpos == 6:  b += ((ord(data[p+5])<<8) + ord(data[p+4])); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24))
    if lenpos == 5:  b += (ord(data[p+4])); a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24));
    if lenpos == 4:  a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16) + (ord(data[p+3])<<24))
    if lenpos == 3:  a += (ord(data[p+0]) + (ord(data[p+1])<<8) + (ord(data[p+2])<<16))
    if lenpos == 2:  a += (ord(data[p+0]) + (ord(data[p+1])<<8))
    if lenpos == 1:  a += ord(data[p+0])
    a &= 0xffffffff; b &= 0xffffffff; c &= 0xffffffff
    if lenpos == 0: return c, b

    a, b, c = final(a, b, c)

    return c, b

def __hashlittle2_rot(x,k):
    return (x << k) | (x >> (32-k))

def __hashlittle2_mix(a,b,c):
    a -= c;  a ^= __hashlittle2_rot(c, 4);  c += b
    b -= a;  b ^= __hashlittle2_rot(a, 6);  a += c 
    c -= b;  c ^= __hashlittle2_rot(b, 8);  b += a 
    a -= c;  a ^= __hashlittle2_rot(c,16);  c += b 
    b -= a;  b ^= __hashlittle2_rot(a,19);  a += c 
    c -= b;  c ^= __hashlittle2_rot(b, 4);  b += a

    return a,b,c