# takes XML from https://github.com/WowDevTools/WDBXEditor and converts to PyWDBX JSON format

import xml.etree.ElementTree as ET
import json

from PyWDBX.utils.dbx import get_hash_from_table

cv = "27075"

e = ET.parse(cv+".xml")
r = e.getroot()

jsdefs = {"BUILD":int(cv),"TABLES":{}}
for d in r:
    if d.attrib['Build'] != cv:
        raise Exception(d+" is build "+d.attrib['Build']+" not "+cv)

    tableName = d.attrib["Name"].upper()
    tableHash = get_hash_from_table(tableName)
    tableCols = []
    hasIndex = False
    for col in d:
        ctype = col.attrib['Type'].lower()
        coltype = "str" if ctype == "string" else ctype
        
        isIndex = bool(col.attrib['IsIndex']) if 'IsIndex' in col.attrib else False

        assert not (isIndex and hasIndex), "Duplicate Index in table "+tableName

        hasIndex = hasIndex or isIndex
        arrayLen = int(col.attrib['ArraySize']) if 'ArraySize' in col.attrib else 1

        assert arrayLen >= 1, "Invalid arraylen "+str(arrayLen)+" in "+tableName

        for x in col.attrib:
            assert x in ['IsIndex','ArraySize','Type','Name'], "Unsupported XML argument "+x

        clen = 0        
        colObj = {"TYPE":coltype}

        colObj['INDEX'] = isIndex

        if coltype in ['int','short','byte','long']:
            colObj['TYPE'] = "int"
            colObj['SIZE'] = ['byte','short',None,'int',None,None,None,'long'].index(coltype)+1

        assert colObj['TYPE'] in ['int','str','float'], "Unsupported type "+coltype+" in "+tableName

        if arrayLen > 1:
            colObj = {"TYPE":"list","LENGTH":arrayLen,"OBJ":colObj}

        colObj['NAME']=col.attrib['Name']

        tableCols.append(colObj)
    if not hasIndex:
        raise Exception("Table "+tableName+" has no index.")
    jsdefs['TABLES'][tableName] = {"HASH":tableHash,"STRUCT":tableCols}

json.dump(jsdefs,open("definitions/"+cv+".json","w+"),indent=4,separators=(",",": "))