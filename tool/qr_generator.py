"""
QR Code 生成器 - 纯 Python 实现（符合 ISO 18004 标准）
支持 Byte mode，ECC Level M，版本 1-7
"""
import math
from PIL import Image, ImageDraw

# ── GF(256) ────────────────────────────────────────────────────
GF_EXP = [0] * 512
GF_LOG  = [0] * 256
_x = 1
for _i in range(255):
    GF_EXP[_i] = _x
    GF_LOG[_x] = _i
    _x <<= 1
    if _x & 0x100: _x ^= 0x11d
for _i in range(255, 512): GF_EXP[_i] = GF_EXP[_i-255]

def _gf_mul(a, b):
    if a==0 or b==0: return 0
    return GF_EXP[GF_LOG[a]+GF_LOG[b]]

def _rs_poly(n):
    g = [1]
    for i in range(n):
        g2 = [0]*(len(g)+1)
        for j,c in enumerate(g):
            g2[j]   ^= c
            g2[j+1] ^= _gf_mul(c, GF_EXP[i])
        g = g2
    return g

def _rs_encode(data, n_ec):
    gen = _rs_poly(n_ec)
    msg = list(data) + [0]*n_ec
    for i in range(len(data)):
        c = msg[i]
        if c:
            for j,g in enumerate(gen): msg[i+j] ^= _gf_mul(c,g)
    return msg[len(data):]

# ── 版本规格 (ECC Level M) ──────────────────────────────────────
_VER = {
    1:{'sz':21,'dc':16,'ec':10},
    2:{'sz':25,'dc':28,'ec':16},
    3:{'sz':29,'dc':44,'ec':26},
    4:{'sz':33,'dc':64,'ec':18},
    5:{'sz':37,'dc':86,'ec':24},
    6:{'sz':41,'dc':108,'ec':16},
    7:{'sz':45,'dc':124,'ec':18},
}

# ── 格式信息 (ECC Level M, Mask 0-7) ────────────────────────────
# ECC Level M = 00 (in QR spec), format mask = 101010000010010
# 预计算所有 mask 的格式信息（已含掩码异或）
def _calc_format(ecc_level_bits, mask_pattern):
    """ecc_level_bits: L=01,M=00,Q=11,H=10; mask_pattern: 0-7"""
    data = (ecc_level_bits << 3) | mask_pattern
    g = 0b10100110111
    rem = data << 10
    for i in range(4,-1,-1):
        if rem & (1<<(i+10)): rem ^= g<<i
    fmt = ((data<<10) | (rem & 0x3FF)) ^ 0b101010000010010
    return fmt

# 掩码函数
_MASKS = [
    lambda r,c: (r+c)%2==0,
    lambda r,c: r%2==0,
    lambda r,c: c%3==0,
    lambda r,c: (r+c)%3==0,
    lambda r,c: (r//2+c//3)%2==0,
    lambda r,c: (r*c)%2+(r*c)%3==0,
    lambda r,c: ((r*c)%2+(r*c)%3)%2==0,
    lambda r,c: ((r+c)%2+(r*c)%3)%2==0,
]

def _penalty(mat, sz):
    """计算惩罚分（选最优掩码）"""
    p = 0
    # Rule 1: 连续5+同色
    for row in mat:
        run=1
        for i in range(1,sz):
            if row[i]==row[i-1]: run+=1
            else:
                if run>=5: p+=run-2
                run=1
        if run>=5: p+=run-2
    for c in range(sz):
        run=1
        for r in range(1,sz):
            if mat[r][c]==mat[r-1][c]: run+=1
            else:
                if run>=5: p+=run-2
                run=1
        if run>=5: p+=run-2
    # Rule 2: 2×2块
    for r in range(sz-1):
        for c in range(sz-1):
            v=mat[r][c]
            if mat[r][c+1]==v and mat[r+1][c]==v and mat[r+1][c+1]==v: p+=3
    # Rule 3: finder-like 1011101 0000 / 0000 1011101
    pat1=[1,0,1,1,1,0,1,0,0,0,0]
    pat2=[0,0,0,0,1,0,1,1,1,0,1]
    for row in mat:
        for i in range(sz-10):
            s=row[i:i+11]
            if list(s)==pat1 or list(s)==pat2: p+=40
    for c in range(sz):
        col=[mat[r][c] for r in range(sz)]
        for i in range(sz-10):
            s=col[i:i+11]
            if s==pat1 or s==pat2: p+=40
    # Rule 4: 比例
    dark=sum(1 for r in mat for v in r if v)
    pct=dark*100//(sz*sz)
    p+=min(abs(pct-50)//5, abs(pct-50+5)//5)*10
    return p

def _make_qr(url):
    data_bytes = url.encode('iso-8859-1')
    n = len(data_bytes)

    # 选版本
    ver = None
    for v,spec in _VER.items():
        needed = math.ceil((4+8+8*n+4)/8)
        if needed <= spec['dc']: ver=v; break
    if ver is None: raise ValueError(f"URL 太长 ({n}字节)")

    spec = _VER[ver]
    sz = spec['sz']

    # 编码数据
    bits = []
    def ab(val,length):
        for i in range(length-1,-1,-1): bits.append((val>>i)&1)
    ab(0b0100,4); ab(n,8)
    for b in data_bytes: ab(b,8)
    ab(0,4)
    while len(bits)%8: bits.append(0)
    pads=[0xEC,0x11]; pi=0
    while len(bits)<spec['dc']*8: ab(pads[pi%2],8); pi+=1
    cw=[]
    for i in range(0,len(bits),8):
        byte=0
        for b in bits[i:i+8]: byte=(byte<<1)|b
        cw.append(byte)

    # RS 纠错
    ec = _rs_encode(cw, spec['ec'])
    all_cw = cw + ec
    all_bits=[]
    for c in all_cw:
        for i in range(7,-1,-1): all_bits.append((c>>i)&1)

    # 构建功能模块标记矩阵
    func = [[False]*sz for _ in range(sz)]

    def set_func(r,c): func[r][c]=True

    def add_finder(tr,tc):
        for dr in range(-1,8):
            for dc in range(-1,8):
                if 0<=tr+dr<sz and 0<=tc+dc<sz: set_func(tr+dr,tc+dc)

    add_finder(0,0); add_finder(0,sz-7); add_finder(sz-7,0)

    for i in range(8,sz-8):
        set_func(6,i); set_func(i,6)

    set_func(4*ver+9,8)  # dark module

    for i in range(9):
        set_func(8,i); set_func(i,8)
    for i in range(sz-8,sz):
        set_func(8,i)
    for i in range(sz-7,sz):
        set_func(i,8)

    # 版本信息 (ver>=7)
    if ver >= 7:
        vi_g = 0b1111100100101
        vi = ver << 12
        for i in range(5,-1,-1):
            if vi & (1<<(i+12)): vi ^= vi_g<<i
        vi = (ver<<12)|vi
        for i in range(18):
            r=(5-i//3); c=(sz-9-i%3); set_func(r,c); set_func(c,r)

    # 对齐图案 (ver>=2)
    _ALIGN = {2:[6,18],3:[6,22],4:[6,26],5:[6,30],6:[6,34],7:[6,22,38]}
    if ver in _ALIGN:
        pos = _ALIGN[ver]
        for ar in pos:
            for ac in pos:
                if not func[ar][ac]:
                    for dr in range(-2,3):
                        for dc in range(-2,3):
                            set_func(ar+dr,ac+dc)

    # 为每种掩码生成候选矩阵
    best_mat = None
    best_penalty = 10**9
    best_mask = 0

    for mask_id in range(8):
        mat = [[False]*sz for _ in range(sz)]

        # 定位图案
        def put_finder(tr,tc):
            for dr in range(7):
                for dc in range(7):
                    v=(dr==0 or dr==6 or dc==0 or dc==6 or (2<=dr<=4 and 2<=dc<=4))
                    mat[tr+dr][tc+dc]=bool(v)
        put_finder(0,0); put_finder(0,sz-7); put_finder(sz-7,0)

        # 分隔符已是False，无需处理
        # 时序
        for i in range(8,sz-8):
            mat[6][i]=bool(i%2==0)
            mat[i][6]=bool(i%2==0)

        # 暗模块
        mat[4*ver+9][8]=True

        # 对齐图案
        if ver in _ALIGN:
            pos=_ALIGN[ver]
            for ar in pos:
                for ac in pos:
                    if not (ar<=6 and ac<=6) and not (ar<=6 and ac>=sz-7) and not (ar>=sz-7 and ac<=6):
                        for dr in range(-2,3):
                            for dc in range(-2,3):
                                in_border=(dr==-2 or dr==2 or dc==-2 or dc==2)
                                mat[ar+dr][ac+dc]=bool(in_border or (dr==0 and dc==0))

        # 版本信息
        if ver >= 7:
            vi_g=0b1111100100101
            vi=ver<<12
            for i in range(5,-1,-1):
                if vi&(1<<(i+12)): vi^=vi_g<<i
            vi=(ver<<12)|vi
            for i in range(18):
                b=bool((vi>>(17-i))&1)
                r=5-i//3; c=sz-11+i%3
                mat[r][c]=b; mat[c][r]=b

        # 数据填充
        bi=0
        mfn=_MASKS[mask_id]
        col=sz-1; going_up=True
        while col>=0:
            if col==6: col-=1
            cols_=[col,col-1]
            rows_=range(sz-1,-1,-1) if going_up else range(sz)
            for r in rows_:
                for c in cols_:
                    if 0<=c<sz and not func[r][c]:
                        bit=all_bits[bi] if bi<len(all_bits) else 0
                        bi+=1
                        mat[r][c]=bool(bit^(1 if mfn(r,c) else 0))
            going_up=not going_up; col-=2

        # 格式信息 (根据 ISO 18004 Figure 19)
        fmt=_calc_format(0b00, mask_id)  # ECC=M=00
        fmt_bits=[(fmt>>(14-i))&1 for i in range(15)]
        # 水平拷贝（行8，左上）: e14..e8 → col=0..5,7,8
        for i in range(6): mat[8][i]=bool(fmt_bits[i])
        mat[8][7]=bool(fmt_bits[6])
        mat[8][8]=bool(fmt_bits[7])
        # 水平拷贝（行8，右上）: e6..e0 → col=sz-8..sz-2
        for i in range(7): mat[8][sz-8+i]=bool(fmt_bits[8+i])
        # 垂直拷贝（列8，左上）: e0..e6 → row=8..0（倒序）
        for i in range(6): mat[5-i][8]=bool(fmt_bits[9+i])
        mat[7][8]=bool(fmt_bits[8])
        # 垂直拷贝（列8，左下）: e14..e7 → row=sz-7..sz-1
        for i in range(7): mat[sz-7+i][8]=bool(fmt_bits[14-i])

        pen=_penalty(mat,sz)
        if pen < best_penalty:
            best_penalty=pen; best_mat=mat; best_mask=mask_id

    return best_mat, sz

def generate_qr_image(url, target_size=557):
    """生成可扫描的 QR 码图片"""
    mat, sz = _make_qr(url)
    quiet = 1   # 减小静默区，让二维码图案视觉上更大，与飞书下载的QR保持一致
    total = sz + 2*quiet
    pixel = max(1, target_size // total)
    actual = total * pixel
    img = Image.new('RGB', (actual, actual), 'white')
    d = ImageDraw.Draw(img)
    for r in range(sz):
        for c in range(sz):
            if mat[r][c]:
                x=(c+quiet)*pixel; y=(r+quiet)*pixel
                d.rectangle([x,y,x+pixel-1,y+pixel-1], fill='black')
    if actual != target_size:
        img = img.resize((target_size, target_size), Image.NEAREST)
    return img

# 兼容旧接口
def generate_qr(url, output_path, size=557):
    img = generate_qr_image(url, target_size=size)
    img.save(output_path)
    return output_path
