import struct

from io import BytesIO

from PyWDBX.utils.blizzutils import var_int, BitsIO, cstr

class CompressionType:
    NONE = 0
    IMMEDIATE = 1
    SPARSE = 2
    PALLET = 3
    PALLETARRAY = 4
    SIGNEDIMMEDIATE = 5

def _parse_wdb3_section_header(f):
    shdr = {}
    shdr['tact_key_hash'] = f.read(8)
    shdr['file_offset'] = var_int(f,4)
    shdr['record_count'] = var_int(f,4)
    shdr['string_table_size'] = var_int(f,4)
    shdr['offset_records_end'] = var_int(f,4)
    shdr['id_list_size'] = var_int(f,4)
    shdr['relationship_data_size'] = var_int(f,4)
    shdr['offset_map_id_count'] = var_int(f,4)
    shdr['copy_table_count'] = var_int(f,4)

    return shdr

def _parse_wdb3_header(f):
    hdr = {}
    hdr['magic'] = f.read(4)
    hdr['record_count'] = var_int(f,4)
    hdr['field_count'] = var_int(f,4)
    hdr['record_size'] = var_int(f,4)
    hdr['string_table_size'] = var_int(f,4)
    hdr['table_hash'] = var_int(f,4)
    hdr['layout_hash'] = f.read(4)
    hdr['min_id'] = var_int(f,4)
    hdr['max_id'] = var_int(f,4)
    hdr['locale'] = var_int(f,4)
    hdr['flags'] = var_int(f,2)
    hdr['id_index'] = var_int(f,2)
    hdr['total_field_count'] = var_int(f,4)
    hdr['bitpacked_data_offset'] = var_int(f,4)
    hdr['lookup_column_count'] = var_int(f,4)
    hdr['field_storage_info_size'] = var_int(f,4)
    hdr['common_data_size'] = var_int(f,4)
    hdr['pallet_data_size'] = var_int(f,4)
    hdr['section_count'] = var_int(f,4)

    return hdr

def _parse_wdb3_field_storage_info(f):
    fsi = {}
    fsi['field_offset_bits'] = var_int(f,2)
    fsi['field_size_bits'] = var_int(f,2)
    fsi['additional_data_size'] = var_int(f,4)

    fsi['comp'] = var_int(f,4)

    fsi['var1'],fsi['var2'],fsi['var3'] = var_int(f,4),var_int(f,4),var_int(f,4)

    print(fsi)

    return fsi

def _parse_wdb3_section(h,sh,fs,fi,f):
    f.seek(sh['file_offset'])
    if sh['tact_key_hash'] != b"\0\0\0\0\0\0\0\0": # if it has a key, fuck me.
        return None

    recs = None
    strdata = None

    if h['flags']&1==0:
        # normal records
        full_recs = [f.read(h['record_size']) for r in range(sh['record_count'])]
        strdata = f.read(sh['string_table_size'])
        recs = []
        for rec in full_recs:
            recbits = BytesIO(rec)
            real_rec = []
            for fx in range(len(fi)):
                fis = fi[fx]
                fss = fs[fx]
                if fis['comp'] == CompressionType.SPARSE:
                    real_rec.append(fis["var1"])
                elif fis['comp'] in [CompressionType.IMMEDIATE,CompressionType.SIGNEDIMMEDIATE]:
                    recbits.seek(fis['field_offset_bits']//8)
                    b = recbits.read((fis['field_size_bits'] + (fis['field_offset_bits'] & 7) + 7)//8)
                    b = int.from_bytes(b,byteorder="little") >> (fis['field_offset_bits'] & 7)
                    b = b & ((1 << fis['field_size_bits'] ) - 1)
                    real_rec.append(b)
                elif fis['comp'] == CompressionType.NONE:
                    real_rec.append(recbits.read(fis['field_size_bits']//8))
                else:
                    raise NotImplementedError("aaaaaaa "+str(fis['comp']))
            recs.append(real_rec)
    else:
        raise Exception("unsupported!!! :()")

    ids = [var_int(f,4) for r in range(sh['id_list_size']//4)]

    ctes = [{"dupe_row":var_int(f,4),"orig_row":var_int(f,4)} for x in range(sh['copy_table_count'])]

    osmes = [{"offset":var_int(f,4),"size":var_int(f,2)} for x in range(sh['offset_map_id_count'])]

    relmap = {}
    relmap['entrymap'] = {}
    if sh['relationship_data_size'] > 0:
        relmap['num_entries'] = var_int(f,4)
        relmap['min_id'] = var_int(f,4) 
        relmap['max_id'] = var_int(f,4) 
        for x in range(relmap['num_entries']):
            ent = {"foreign_id":var_int(f,4),"record_index":var_int(f,4)}
            if ent['record_index'] in relmap['entrymap']:
                raise Exception("Relmap with 2 foreignid per ind")
            else:
                relmap['entrymap'][ent['record_index']] = ent['foreign_id']

    return recs,strdata,ids,ctes,osmes,relmap

def parse_wdc3(parser,f):
    parser.header = _parse_wdb3_header(f)

    section_hdrs = []
    for si in range(parser.header['section_count']):
        section_hdrs.append(_parse_wdb3_section_header(f))

    field_structs = []
    for fi in range(parser.header['total_field_count']):
        fstruct = {"size":var_int(f,2),"offset":var_int(f,2)}
        field_structs.append(fstruct)

    field_infos = []
    for fi in range(parser.header['field_storage_info_size']//(24)):
        field_infos.append(_parse_wdb3_field_storage_info(f))

    pallet_data = f.read(parser.header['pallet_data_size'])
    common_data = f.read(parser.header['common_data_size'])

    print(parser.header)
    print(section_hdrs[0])
    print(section_hdrs)

    sections = []
    for sh in section_hdrs:
        sections.append(_parse_wdb3_section(parser.header,sh,field_structs,field_infos,f))
        
    # print(sections[0][0])

    parser._file_data = (section_hdrs,field_structs,field_infos,pallet_data,common_data,sections)

    # print(parser._file_data[5][5])

def process_wdc3(parser,defn):
    data = {}
    data_pos = {}

    relations = {}

    for s_i in range(len(parser._file_data[0])):
        s_h = parser._file_data[0][s_i]
        s = parser._file_data[5][s_i]
        if s is None:
            continue
        if s_h['id_list_size'] > 0: # specifically for sections that have an id_list_size.
            for x in range(s_h['record_count']):
                data_pos[s[2][x]] = (s,(x - s_h['record_count']) * parser.header['record_size'])
                data[s[2][x]] = s[0][x]
                if x in s[5]['entrymap']:
                    relations[s[2][x]] = s[5]['entrymap'][x]
        else:
            idcol = parser.header['id_index']
            for x in range(len(s[0])):
                data_pos[s[0][x][idcol]] = (s,(x - s_h['record_count']) * parser.header['record_size'])
                data[s[0][x][idcol]] = s[0][x][:idcol]+s[0][x][idcol+1:]
                if x in s[5]['entrymap']:
                    relations[s[0][x][idcol]] = s[5]['entrymap'][x]

    assert len(data[min(data)]) == len(defn['STRUCT'])-1, "Invalid Definition size ( "+str(len(data[min(data)]))+" == "+str(len(defn['STRUCT'])-1)+" )"

    if parser.header['common_data_size']>0:
        sparse_cols = []
        sparse_offset = 0
        for xi in range(len(parser._file_data[2])):
            if parser._file_data[2][xi]['comp'] == CompressionType.SPARSE:
                sparse_cols.append((xi, sparse_offset, parser._file_data[2][xi]))
                sparse_offset += parser._file_data[2][xi]['additional_data_size']
        
        common_dat = BytesIO(parser._file_data[4])
        for scol in sparse_cols:
            common_dat.seek(scol[1],0)
            for _ in range(scol[2]['additional_data_size']//8):
                r,v = var_int(common_dat,4),var_int(common_dat,4)
                data[r][scol[0]-1]=v

        # common_dat = BytesIO(parser._file_data[4])
        # l = 0
        # while l < parser.header['common_data_size']:
        #     r,v = var_int(common_dat,4),var_int(common_dat,4)
        #     print(l,r,v)
        #     data[r][i]=v
        #     l += 8

        # print(i,sparse_col)

    index_mapping = {} # maps index of row in data to index of row in rows. -1 = ID of data, -2 = relation

    row_len = sum(s['LENGTH'] if s['TYPE'] == 'list' else 1 for s in defn['STRUCT'])+(1 if len(relations)>0 else 0)

    cols = [None]*row_len

    data_index = 0
    cur_index  = 0
    for col in defn['STRUCT']:
        if col['TYPE'] == "int" and col['INDEX']:
            cols[cur_index]=("int","ID")
            index_mapping[cur_index]=-1
        else:
            cols[cur_index]=(col['TYPE'],col['NAME'])
            if col['TYPE'] == 'list':
                col_t = col["OBJ"]
                for x in range(col['LENGTH']):
                    cols[cur_index]=(col['TYPE'],col['NAME'])
                    index_mapping[cur_index]=data_index
                    data_index+=1
                    cur_index+=1
            else:
                index_mapping[cur_index]=data_index
                data_index+=1
        cur_index+=1
    
    # assert ('RELATION' in defn) == (len(relations)>0), f"Mismatch for Relations between Defn & Reality. ({'' if 'RELATION' in defn else 'not '}in defn && {len(relations)} in reality)"

    if len(relations)>0:
        cols[cur_index] = defn['RELATION'] if 'RELATION' in defn else ("int","RELATION")
        index_mapping[cur_index] = -2
        cur_index += 1

    rows = []
    col_renamed = False
    for r in data:
        rd = data[r]
        cur_row = [None]*row_len

        last_ry = None
        last_item = None

        for y in index_mapping:
            ry = index_mapping[y]

            if cols[y][0] == 'list':
                same_obj = last_item[0] == cols[y][0] if last_item is not None else False
                if last_item is not None and same_obj:
                    rv = rd[last_ry-1][ry-last_ry]
                    if not col_renamed:
                        cols[y] = (cols[y][0],cols[y][1]+f"[{ry-last_ry:d}]")

                if last_item is None or not same_obj:
                    last_ry = ry
                    rv = rd[ry][0]
                    if not col_renamed:
                        cols[y] = (cols[y][0],cols[y][1]+f"[{ry-last_ry:d}]")
                last_item = cols[y]
            else:
                rv = rd[ry] if ry>=0 else (r if ry==-1 else relations[r])

            if cols[y][0] == 'str':
                sec,ofs = data_pos[r]
                rv = int.from_bytes(rv,byteorder="little") + ofs
                rv = cstr(sec[1][rv:])

            cur_row[y] = rv
        
        col_renamed = True
        rows.append(cur_row)

    col_width = max(max(len(str(c)) for c in r) for r in rows)
    col_width = max(col_width,max(len(c[1]) for c in cols if c is not None))
    # print(col_width) 

    # return

    for c in cols:
        if c is None:
            continue
        print(f" {c[1]:>{col_width}}|",end="")     
    print()

    prnt_cnt = 0
    for r in rows:
        for c in r:
            print(f" {str(c):>{col_width}}|",end="")     
        prnt_cnt += 1
        if prnt_cnt > 100:
            break
        print()
    print()