import datetime
from pathlib import Path  # Used for easier handling of auxiliary file's local path

import pyecma376_2  # The base library for Open Packaging Specifications. We will use the OPCCoreProperties class.
from basyx.aas import model
from basyx.aas.adapter import aasx
import basyx.aas.adapter.json
import basyx.aas.adapter.xml
import requests
import json
import base64



class aas_helper():

    unresolved_references = []
    

    def __init__(self):
        self.object_store : model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
        self.file_store = aasx.DictSupplementaryFileContainer()

    def get_base64_str(self, input_string):
        b = base64.b64encode(bytes(input_string, 'utf-8')) # bytes
        base64_str = b.decode('utf-8') # convert bytes to string
        return base64_str
    
    def upload_shell(self, identifier):
        pass
        host = 'http://localhost'

        shell = self.object_store.get(identifier)
        aashell_json_string = json.dumps(shell, cls=basyx.aas.adapter.json.AASToJsonEncoder)

        result = requests.post(  host + ':8081/shells' , 
                                data = aashell_json_string, 
                                headers = {"Content-Type": "application/json"})
        
        print(identifier, result)
        
        for submodel in [s.get_identifier() for s in shell.submodel]:
            pass
            sm = self.object_store.get(submodel)
            sm_json_string = json.dumps(sm, cls=basyx.aas.adapter.json.AASToJsonEncoder)

            result = requests.post(  host + ':8081/submodels', 
                                    data = sm_json_string, 
                                    headers = {"Content-Type": "application/json"})
            
            print(submodel, result)
        
        
        
            



        


    
    def create_aas_from_id_short_list(self, aas_info:dict, 
                                  sub_model_identifier:dict, 
                                  submodel_element_id_sort_list:list,                                  
                                  explicit_smc_declaration = None)-> model.DictObjectStore:
        
        kind={"Type": model.AssetKind.TYPE,
              "Instance": model.AssetKind.INSTANCE}

        asset_information = model.AssetInformation(
        asset_kind=kind[aas_info["assetInformation"]["assetKind"]],
        global_asset_id=aas_info["assetInformation"]["globalAssetId"]
        )
    
        aas = model.AssetAdministrationShell(
            id_=aas_info['id'],  # set identifier
            asset_information = asset_information,
            id_short= aas_info['idShort'], 
            display_name=  model.MultiLanguageNameType({ l['language']: l['text'] for l in aas_info['displayName']})
        )
        submodels = {}
        for entry in list(dict.fromkeys([p[0].split('.')[0] for p in submodel_element_id_sort_list])):
            pass
            submodel_id_short = entry

            ## Submodel Reference??
            if sub_model_identifier[submodel_id_short][0] == 'SmRef':
                
                model.ExternalReference([model.Key(model.KeyTypes(2000), value=sub_model_identifier[submodel_id_short][1])])
                continue

            ## Submodel erzeugen, wenn noch nicht vorhanden.
            if submodel_id_short not in submodels: 
                submodel_ = model.Submodel(
                id_=sub_model_identifier[submodel_id_short][1],
                id_short=submodel_id_short
                )
                submodels.update({submodel_id_short: submodel_})
            else:
                pass
            
            submodel_element_info = list(filter(lambda x: x[0].split('.')[0] == submodel_id_short, submodel_element_id_sort_list))
            submodel_ = self.create_submodel_from_id_short_list(submodel_, submodel_element_info, explicit_smc_declaration = explicit_smc_declaration)
            aas.submodel.add(model.ModelReference.from_referable(submodel_))
            if submodel_.id not in [sm.id for sm in self.object_store]:
                self.object_store.add(submodel_)
            else:
                pass
        self.create_model_references(aas, submodel_element_id_sort_list)
        self.object_store.add(aas)
        self.handle_unresolved_references()
        return self.object_store
        
    def create_submodel_from_id_short_list(self, submodel_, submodel_element_info, explicit_smc_declaration = None):
        
        ## Reduce to keys in Submodel
        submodel_key_info = list(map(lambda x: [x[0].split('.')[1:], x[1], x[2], {"id_short_path": x[0], "submodel_id": submodel_.id}], submodel_element_info))

        ###################### Checking for Implicit SMC definition #######################################
        if explicit_smc_declaration == None:
            keys = list(map(lambda x: x[0][0], submodel_key_info))
            potential_smc = [k for k in list(dict.fromkeys(keys)) if keys.count(k) >1]
            id_short_endpoints = list(map(lambda x: x[0].split('.')[-1], submodel_element_info))
            
            
            if True in [smc in id_short_endpoints for smc in potential_smc]:
                explicit_smc_declaration = True
            else:
                explicit_smc_declaration = False

        ## Creating Collectinos for Subsets        
        keys = list(map(lambda x: x[0][0], submodel_key_info)) 
        smcs = list(dict.fromkeys([v for v in keys if keys.count(v)>1]))
        smc_explicit = [s[0][0] for s in submodel_key_info if s[1] == 'Smc']
        smcs = list(dict.fromkeys(smcs + smc_explicit))
        collections = {}    
        for subset in smcs:
            collections.update({subset: [element for element in submodel_key_info if element[0][0] == subset]})
            ## Insert Explicit Info
            index = [x[0][0] for x in submodel_key_info].index(subset)
            if explicit_smc_declaration == True:
                info = submodel_key_info[index]
            elif explicit_smc_declaration == False:
                info = [[subset], 'Smc', '']
            submodel_key_info = list(filter(lambda x : x[0][0] != subset, submodel_key_info))
            submodel_key_info.insert(index, info)
            
        for el in submodel_key_info:
            
            if el[1] == "Prop":
                print(submodel_.id_short + " -> writing Property", el)
                submodel_.submodel_element.add(self.makeProperty(el))

            elif el[1] == 'Ref':
                referenceElement_ = self.makeReferenceElement(el) 
                submodel_.submodel_element.add(referenceElement_)
            elif el[1] == "mRef":
                referenceElement_ = model.ReferenceElement(el[0][0], value=el[2])
                submodel_.submodel_element.add(referenceElement_)

            elif el[1] == 'Smc':
                submodel_element_collection = self.create_collection_from_id_short_list(el[0][0], collections[el[0][0]], explicit_smc_declaration = explicit_smc_declaration)
                submodel_.submodel_element.add(submodel_element_collection)
            elif el[1] == 'Sml':
                pass
                submodel_element_collection = self.create_collection_from_id_short_list(el[0][0], collections[el[0][0]], explicit_smc_declaration = explicit_smc_declaration)
                submodel_.submodel_element.add(submodel_element_collection)
            elif el[1] == 'Ent':
                pass
                submodel_element_collection = self.create_collection_from_id_short_list(el[0][0], collections[el[0][0]], explicit_smc_declaration = explicit_smc_declaration)
                submodel_.submodel_element.add(submodel_element_collection)

        return submodel_


    def create_collection_from_id_short_list(self, id_short_sme, submodel_element_info, explicit_smc_declaration = None):
        property_list = []
        ## Reduce to keys in Submodel
        collection_key_info = list(map(lambda x: [x[0][1:], x[1], x[2], x[3] ], submodel_element_info))

        if collection_key_info[0][1]=='Smc' or collection_key_info[0][1]=='Sml' or collection_key_info[0][1]=='Ent': ## SML oder SMC Speichern??
            sme = collection_key_info.pop(0)
        else:
            sme = [[], 'Smc', None]

        ## Creating Collectinos for Subsets        
        keys = list(map(lambda x: x[0][0], collection_key_info)) 
        smcs = list(dict.fromkeys([v for v in keys if keys.count(v)>1]))
        smc_explicit = [s[0][0] for s in collection_key_info if s[1] == 'Smc']
        smcs = list(dict.fromkeys(smcs + smc_explicit))
        collections = {}    
        for subset in smcs:
            collections.update({subset: [element for element in collection_key_info if element[0][0] == subset]})
            ## Insert Explicit Info
            index = [x[0][0] for x in collection_key_info].index(subset)
            if collection_key_info[index][0][0] == subset and len(collection_key_info[index][0]) == 1 : ##muss weg
                info = collection_key_info[index]
            else: ##muss weg
                info = [[subset], 'Smc', '']
            collection_key_info = list(filter(lambda x : x[0][0] != subset, collection_key_info))
            collection_key_info.insert(index, info)
            
        ###################################################################################################
       

        for el in collection_key_info:
    
            if el[1] == "Prop":
                print(id_short_sme + " -> writing Property", el)
                property_list.append(self.makeProperty(el))

            elif el[1] == 'Ref':
                referenceElement_ = self.makeReferenceElement(el) 
                property_list.append(referenceElement_)

            elif el[1] == "mRef":
                referenceElement_ = model.ReferenceElement(el[0][0], value=el[2])
                property_list.append(referenceElement_)
            
            elif el[1] == "Ent":
                if el[0][0] in collections.keys():
                    entity_ = self.create_collection_from_id_short_list(el[0][0], collections[el[0][0]], explicit_smc_declaration = explicit_smc_declaration)
                else:
                    entity_ = self.makeEnitity(el)
                property_list.append(entity_)

            elif el[1] == 'Smc':
           
                submodel_element_collection = self.create_collection_from_id_short_list(el[0][0], collections[el[0][0]], explicit_smc_declaration = explicit_smc_declaration)
                property_list.append(submodel_element_collection)

       
        if sme[1] == 'Smc':
            collection = model.SubmodelElementCollection(
                id_short=id_short_sme,
                value=property_list
            )
        elif sme[1] == 'Sml': ## Listen sind noch nicht implementiert
            collection = model.SubmodelElementList(
                id_short=id_short_sme,
                value=property_list
            )
        elif sme[1] == 'Ent': ## Listen sind noch nicht implementiert
            collection = model.Entity(
                id_short_sme,
                model.EntityType(1),
                global_asset_id= submodel_element_info[0][2],
                statement=property_list
            )

        return collection
    

    def write_aas_to_file(self, aas_id_to_write:str, path:str):
        with aasx.AASXWriter(path) as writer:
    
            writer.write_aas(aas_ids=[aas_id_to_write],
                            object_store=self.object_store,
                            file_store= self.file_store)
            return True
    

    def get_element_by_id_path(self, id_obj, idPath:str):
        pass
        if type(id_obj) == model.AssetAdministrationShell:
            id_short_keys = idPath.split('.')
            ## Find Submodel in self.ObjectStore
            ref_sm = list(filter(lambda x: x.id_short == id_short_keys[0], [sm.resolve(self.object_store) for sm in id_obj.submodel]))[0]

            if len(id_short_keys) == 1 and '.'.join(id_short_keys) == ref_sm.id_short:
                return ref_sm
        elif type(id_obj) == model.Submodel:
            id_short_keys = idPath.split('.')
            ref_sm = id_obj


        index = 1
        while True:
            cur_id = id_short_keys[index]
            cur_el = list(filter(lambda x: x.id_short == id_short_keys[index], iter(ref_sm)))[0]
            #If cur_el = None => return False
            index += 1
            if '.'.join(id_short_keys) == '.'.join(id_short_keys[:index]):
                return cur_el
            ref_sm = cur_el
    
    def create_model_references(self, shell, id_short_list):
        pass
        ## suche mRefs
        mRef_list = list(filter(lambda x: x[1] == 'mRef', id_short_list))

        for ref in mRef_list:
            try:

                referred_element = self.get_element_by_id_path(shell, ref[2])
                refering_element = self.get_element_by_id_path(shell, ref[0])

                refering_element.value =  model.ModelReference.from_referable(referred_element)
                print(refering_element)
            except:
                print('Fehler')
            pass

    def handle_unresolved_references(self):
        for i in reversed(range(len(self.unresolved_references))):
            ref = self.unresolved_references[i]
            obj = self.object_store.get(ref[3]["submodel_id"])
            if obj != None:
                element = self.get_element_by_id_path(obj, ref[3]['id_short_path'])
                dest = self.object_store.get(ref[2])
                if dest != None:
                    element.value = model.ModelReference.from_referable(dest)
                    self.unresolved_references.pop(i)

    def makeReferenceElement(self, el:list) -> model.ReferenceElement:
        
        try:
            r = model.ModelReference.from_referable(self.object_store.get(el[2]))
        except:
            if not el[2] == "":
            
                r = model.ExternalReference([model.Key(model.KeyTypes(2000), el[2])])
                self.unresolved_references.append(el)
            else:
                r =  model.ExternalReference([model.Key(model.KeyTypes(2000), 'EmptyReference')])
            print("External Reference konnte nicht erstellt werden", el)
            
        return model.ReferenceElement(el[0][0], value=r)
            
    def makeProperty(self, el:list)-> model.Property:
        ## Check for unallowed Characters in ID short   
        property_ = model.Property(
        id_short= el[0][0],  # Identifying string of the element within the Submodel namespace
        value_type=model.datatypes.String,  # Data type of the value
        value=el[2],  # Value of the Property   
        )
        return property_
    
    def makeEnitity(self, el:list) -> model.Entity:
        pass
        ent = model.Entity(el[0][0], model.EntityType(1), global_asset_id=el[2], statement=[])
        return ent

    def importSubmodelFromAAS(self, file, sm_id=None):
        pass
        with aasx.AASXReader(file) as reader:
            meta_data = reader.get_thumbnail()
            reader.read_into(   self.object_store, 
                                self.file_store)
        
        pass
        sm_list = list(filter(lambda x: type(x) == model.submodel.Submodel, self.object_store))
        if sm_id == None or len(sm_list) == 1:
            sm = sm_list[0]
        else:
            sm_list = list(filter(lambda x: x.id == sm_id, sm_list))
            if sm_list == []:
                return None
            else:
                sm = sm_list[0]
        return sm

    def exportSubmodelToList(self, Element):
        pass
        
        for el in Element:


            id_short_list = [] ## [id_short_path, Prop, Value]





        ## Find Submodel in self.ObjectStore
        # ref_sm = list(filter(lambda x: x.id_short == id_short_keys[0], [sm.resolve(self.object_store) for sm in aas.submodel]))[0]

        # if len(id_short_keys) == 1 and '.'.join(id_short_keys) == ref_sm.id_short:
        #     return ref_sm


        # index = 1
        # while True:
        #     cur_id = id_short_keys[index]
        #     cur_el = list(filter(lambda x: x.id_short == id_short_keys[index], iter(ref_sm)))[0]
        #     #If cur_el = None => return False
        #     index += 1
        #     if '.'.join(id_short_keys) == '.'.join(id_short_keys[:index]):
        #         return cur_el
        #     ref_sm = cur_el
        
        
        