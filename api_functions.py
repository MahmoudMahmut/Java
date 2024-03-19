import json 
import requests
import base64
import basyx.aas.adapter.json


class aas_api_endpoint():
     
    def __init__(self, addres = 'http://localhost', content_repository = '8081'):
         self.enpoint = addres
         self.repo_port = content_repository 
         


    def get_base64_str(self, input_string):
            b = base64.b64encode(bytes(input_string, 'utf-8')) # bytes
            base64_str = b.decode('utf-8') # convert bytes to string
            return base64_str


    def clear_repo(self, shells = True, submodels = True):
        urls = []
        if shells == True:
            urls.append( self.enpoint + ':' + self.repo_port + "/" + "shells")
        if submodels == True:
            urls.append(self.enpoint + ':' + self.repo_port + "/" + "submodels")
        
        for url in urls:
            r = json.loads(requests.get(url).text)['result']
            id_list = list(map(lambda x: x['id'], r))
            for id in id_list:
                print("Clearing: " , requests.delete(url + "/" +  self.get_base64_str(id)))
    
    def upload_shell(self, identifier, object_store):
        
        shell = object_store.get(identifier)
        aashell_json_string = json.dumps(shell, cls=basyx.aas.adapter.json.AASToJsonEncoder)

        result = requests.post( self.enpoint + ':' + self.repo_port + "/" + "shells" , 
                                data = aashell_json_string, 
                                headers = {"Content-Type": "application/json"})
        
        print(identifier, result)
        
        for submodel in [s.get_identifier() for s in shell.submodel]:
            pass
            sm = self.object_store.get(submodel)
            sm_json_string = json.dumps(sm, cls=basyx.aas.adapter.json.AASToJsonEncoder)

            result = requests.post(  self.enpoint + ':' + self.repo_port + "/" + "submodels", 
                                    data = sm_json_string, 
                                    headers = {"Content-Type": "application/json"})
            
            print(submodel, result)

    def upload_object_sotre(self, object_store):
         

        aas_list = list(filter(lambda x :type(x) == basyx.aas.model.AssetAdministrationShell, object_store ))
        submodel_list = list(filter(lambda x :type(x) == basyx.aas.model.Submodel, object_store ))

        for aas in aas_list:
            

            aashell_json_string = json.dumps(aas, cls=basyx.aas.adapter.json.AASToJsonEncoder)
            result = requests.post( self.enpoint + ':' + self.repo_port + "/" + "shells" , 
                                    data = aashell_json_string, 
                                    headers = {"Content-Type": "application/json"})
    
            print(aas.id, result)
            
        for submodel in submodel_list:
            
            sm_json_string = json.dumps(submodel, cls=basyx.aas.adapter.json.AASToJsonEncoder)

            result = requests.post(  self.enpoint + ':' + self.repo_port + "/" + "submodels", 
                                    data = sm_json_string, 
                                    headers = {"Content-Type": "application/json"})
            
            print(submodel.id, result)

