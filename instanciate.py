import datetime
from pathlib import Path  # Used for easier handling of auxiliary file's local path

import pyecma376_2  # The base library for Open Packaging Specifications. We will use the OPCCoreProperties class.
from basyx.aas import model
from basyx.aas.adapter import aasx
import basyx.aas.adapter.json
import basyx.aas.adapter.xml
from aas_helper import aas_helper
import requests
import json
import pandas as pd
from api_functions import aas_api_endpoint
import datetime as dt
import copy
import aas_toolchian

aas_toolchian

input = {
    'fahrradType': "www.hackerthon.de/ids/aas/TypeFahrrad",
    'lenker': "https://example.com/ids/AssetAdministrationShell/7487_1553_5310_3896",
    'rahmen': 'www.hackerthon.de/ids/aas/FahrradRahmen',
    'radvorne': 'https://example.com/ids/AssetAdministrationShell/2831_2382_1560_6063',
    'radhinter': 'https://example.com/ids/AssetAdministrationShell/2831_2382_1560_6063',
    'sattel': "https://example.com/ids/AssetAdministrationShell/4506_9976_7663_8793"
}


BOM = {
    "https://example.com/ids/AssetAdministrationShell/7487_1553_5310_3896":"https://markt.aas-suite.de/api",
    "https://example.com/ids/AssetAdministrationShell/4506_9976_7663_8793":"https://markt.aas-suite.de/api",
    "https://example.com/ids/AssetAdministrationShell/2831_2382_1560_6063":"https://markt.aas-suite.de/api"
}



host = 'localhost'

api = aas_api_endpoint()
helper = aas_helper()
### get typeshell


## Download Type Shell

url = api.enpoint + ':' + api.repo_port + "/" + "shells"+ "/" +  api.get_base64_str(input['fahrradType'])
r = json.loads(requests.get(url).text, cls=basyx.aas.adapter.json.AASFromJsonDecoder)
helper.object_store.add(r)

for sm in r.submodel:
    pass
    url = api.enpoint + ':' + api.repo_port + "/" + "submodels"+ "/" +  api.get_base64_str(sm.get_identifier())
    m = json.loads(requests.get(url).text, cls=basyx.aas.adapter.json.AASFromJsonDecoder)
    helper.object_store.add(m)

## Change AAS to Type

aas = helper.object_store.get(input['fahrradType'])

##set instance
aas.asset_information.asset_kind = model.base.AssetKind(1)
aas.id = "www.hackerthon.de/ids/aas/Fahrrad_Instance_001"
aas.asset_information.global_asset_id = "www.hackerthon.de/ids/aas/Fahrrad_Instance_001"
aas.asset_information.id = "www.hackerthon.de/ids/aas/Fahrrad_Instance_001"
aas.display_name['de'] = "Fahrrad_001"
aas.id_short ="FahrradInstance_001"


#===================================================================================


## set instance Submodels
type_submodels = [sm.get_identifier() for sm in aas.submodel]
aas.submodel.clear()
instance_submodels = []
for sm in helper.object_store:
    if type(sm) == model.submodel.Submodel:
        

        type_id = helper.object_store.get(sm.id).id
        submodel = copy.deepcopy(helper.object_store.get(sm.id))
        submodel.id = type_id + "Instance001"
        submodel.update()
        instance_submodels.append(submodel)
        aas.submodel.add(model.ModelReference.from_referable(submodel))
    
    
    pass
pass

[helper.object_store.remove(helper.object_store.get(sm)) for sm in type_submodels if sm in type_submodels]

helper.object_store.update(instance_submodels)

#[aas.submodel.add(model.ModelReference.from_referable(sumo)) for sumo in helper.object_store if type(sumo) == model.Submodel]

## set Serial Number
helper.get_element_by_id_path(aas, 'Nameplate.URIOfTheProduct').value += '_Instance_001'
helper.get_element_by_id_path(aas, 'Nameplate.YearOfConstruction').value = '2024'
helper.get_element_by_id_path(aas, 'Nameplate.DateOfManufacture').value = 'Mrz'
helper.get_element_by_id_path(aas, 'Nameplate.WarrantyUntil').value = str(2024+2)





####################################
### MAKE BOM ######################

# ## Lenker
# url = BOM[input['lenker']] + "/" + "shells"+ "/" +  api.get_base64_str(input['lenker'])
# r = json.loads(requests.get(url).text, cls=basyx.aas.adapter.json.AASFromJsonDecoder)
# helper.get_element_by_id_path(aas, 'BOM.EntryNode.Fahrrad.Lenker').global_asset_id = r.asset_information.global_asset_id


# ## sattel
# url = BOM[input['sattel']] + "/" + "shells"+ "/" +  api.get_base64_str(input['sattel'])
# r = json.loads(requests.get(url).text, cls=basyx.aas.adapter.json.AASFromJsonDecoder)
# helper.get_element_by_id_path(aas, 'BOM.EntryNode.Fahrrad.Sattel').global_asset_id = r.asset_information.global_asset_id

# ## RadVorne
# url = BOM[input['sattel']] + "/" + "shells"+ "/" +  api.get_base64_str(input['radvorne'])
# r = json.loads(requests.get(url).text, cls=basyx.aas.adapter.json.AASFromJsonDecoder)
# helper.get_element_by_id_path(aas, 'BOM.EntryNode.Fahrrad.RadVorne').global_asset_id = r.asset_information.global_asset_id
# ## RadHinten
# url = BOM[input['sattel']] + "/" + "shells"+ "/" +  api.get_base64_str(input['radhinter'])
# r = json.loads(requests.get(url).text, cls=basyx.aas.adapter.json.AASFromJsonDecoder)
# helper.get_element_by_id_path(aas, 'BOM.EntryNode.Fahrrad.RadHinten').global_asset_id = r.asset_information.global_asset_id














api.upload_object_sotre(helper.object_store)
pass

