import os
import json

from typing import Union
from io import BytesIO, IOBase

from PyWDBX.types import get_parser
from PyWDBX.utils.dbx import get_table_from_hash
from PyWDBX.utils.blizzutils import jenkins_hash, hashlittle2

DEFINITION_DIR = os.path.join(os.getcwd(),"definitions")
def get_definition(dbhash, build):
    buildPath = os.path.join(DEFINITION_DIR,str(build)+".json")
    if os.path.exists(buildPath):
        definitions = {}
        with open(buildPath,"r") as d:
            definitions = json.load(d)
            assert definitions['BUILD'] == build, "Invalid build in "+str(build)+".json ("+str(definitions['BUILD'])+")"

        for tbl in definitions['TABLES']:
            defn = definitions['TABLES'][tbl]
            if defn['HASH'] == dbhash:
                return tbl,defn

        raise Exception("Requested DB not supported.")
    else:
        # todo find next build down
        raise Exception("Requested build is not supported.")

class DBCParser:
    def parse(self):
        self.parser(self, self.data)

    def find_parser(self):
        self.signature = self.data.read(4)
        self.data.seek(0)

        self.parser,self.process = get_parser(self.signature)

    def find_name(self):
        self.dbname = get_table_from_hash(self.header['table_hash'])

    def process_defn(self):
        self.dbname, self.defn = get_definition(self.header['table_hash'],self.build)

        self.process(self,self.defn)

    def __init__(self, file:Union[str,bytes,IOBase], build=27075):
        if not isinstance(file,IOBase):
            self.data = BytesIO(self.data)
        else:
            self.data = file

        self.build = build

        self.find_parser()

        # The header format depends on the file type, wdc3 differs from wch for example.
        #  - Refer to each individual types/<type>.py for the struct
        self.header = {}

        # File Data is a file-type based struct to allow for this instance store to keep data about the file on-hand 
        #   rather than parse it over and over. This is effectively useless to the user.
        self._file_data = {}

        # Send the file to the parser we found earlier. Thus populating self._file_data
        self.parse()

        self.table = {} # {cols:[(colname,coltype)...],rows:[[value for each col]...]}
        # Populate self.table with the processor we found earlier, self.table is standardized. 
        self.process_defn()

if __name__ == "__main__":
    dbc = DBCParser(open("pvptalent.db2","rb+"))
    # dbc = DBCParser(open("achievement_category.db2","rb+"))
