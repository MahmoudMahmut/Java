#!/usr/bin/env python3
# This work is licensed under a Creative Commons CCZero 1.0 Universal License.
# See http://creativecommons.org/publicdomain/zero/1.0/ for more information.
"""
Tutorial for exporting Asset Administration Shells with related objects and auxiliary files to AASX package files, using
the :mod:`~basyx.aas.adapter.aasx` module from the Eclipse BaSyx Python SDK.

.. warning::
    This tutorial is only valid for the current main branch of the Eclipse BaSyx Python SDK. With version 3.0 of
    *Details of the Asset Administration Shell* some specifications of AASX files will change, resulting in changes of
    the :class:`~basyx.aas.adapter.aasx.AASXWriter` interface.
"""
import datetime
from pathlib import Path  # Used for easier handling of auxiliary file's local path

import pyecma376_2  # The base library for Open Packaging Specifications. We will use the OPCCoreProperties class.
from basyx.aas import model
from basyx.aas.adapter import aasx
import basyx.aas.adapter.json
import basyx.aas.adapter.xml
from aas_helper import aas_helper

import json
import pandas as pd
from api_functions import aas_api_endpoint
import datetime as dt


## Hier als Argument den Dateinamen (Ohne Endung) eingeben
## CSV und JSON Files können dann geladen werden


filelist = [ "typeFahrrad"]

api = aas_api_endpoint()
api.clear_repo()

new_aas_helper = aas_helper()



for filename in filelist:

    ### ======<<<<<< Import ID_Short List>>>>>>>>==============
    aas_dataframe = pd.read_csv(filename + '.csv', sep=';', encoding="iso-8859-1", header=0)
    aas_dataframe = aas_dataframe.fillna('')
    nameplate_dict = [list(value) for value in aas_dataframe.values]

    submodel_identifier = {sm[0]:(sm[1], sm[2])  for sm in list(filter(lambda x: x[1] == 'Sm' or x[1] == 'SmRef'  , nameplate_dict))}
    nameplate_dict =                              list(filter(lambda x: x[1] != 'Sm', nameplate_dict))

    ### ======<<<<<< Import AAS-Info >>>>>>>>==============
    with open(filename +'.json') as file:
        aas_info = json.loads(file.read())


    ### ======<<<<<< AAS Erstellen >>>>>>>>==============
    
    new_aas_helper.create_aas_from_id_short_list(aas_info, submodel_identifier, nameplate_dict, )

    ### ======<<<<<< AASX File Schreiben >>>>>>>>==============
    new_aas_helper.write_aas_to_file(aas_info['id'], filename + ".aasx")




api.upload_object_sotre(new_aas_helper.object_store)
####hier müssen Referencen Repariert werden

pass











        




