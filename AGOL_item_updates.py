import getpass

from pathlib import Path

import arcgis
import arcpy


def define_service(project_path, map_name, layer_name, fc_path_str, item_name, temp_dir_path):

    #: Reference a Pro project so that we can get a map and share it
    print('getting Pro project and map...')
    proj = arcpy.mp.ArcGISProject(str(project_path))

    #: Select the right map from the project
    for m in proj.listMaps():
        if m.name == map_name:
            agol_map = m
    del m

    #: Remove any other layers to create a single-layer hosted feature service
    print('clearing existing layers...')
    for l in agol_map.listLayers():
        agol_map.removeLayer(l)
    for t in agol_map.listTables():
        agol_map.removeTable(t)

    #: Add the desired data as a layer and give it the desired name
    print('adding layer...')
    layer = agol_map.addDataFromPath(fc_path_str)
    # print(layer)
    layer.name = layer_name

    #: Save the project so that the changes stick.
    proj.save()

    #: Create paths for the service definition draft and service definition files
    draft_path = Path(temp_dir_path, f'{item_name}.sddraft')
    service_definition_path = Path(temp_dir_path, f'{item_name}.sd')

    #: Delete draft and definition if existing
    for file_path in (draft_path, service_definition_path):
        if file_path.exists():  #: This check can be replaced in 3.8 with missing_ok=True
            print(f'deleting existing {file_path}...')
            file_path.unlink()

    #: Create the service definition draft and stage it to create a service definition file
    print('draft and stage...')
    sharing_draft = agol_map.getWebLayerSharingDraft('HOSTING_SERVER', 'FEATURE', item_name, [layer])
    sharing_draft.exportToSDDraft(str(draft_path))
    arcpy.server.StageService(str(draft_path), str(service_definition_path))

    #: Return the path to the service definition file
    return service_definition_path

def publish(org, service_definition_path):
    print('uploading...')
    source_item = org.content.add({}, data=str(service_definition_path))
    print('publishing...')
    item = source_item.publish()

    return item

def overwrite(org, service_definition_path, item_id, sd_id):
    # item = org.content.get(item_id)
    sd_item = org.content.get(sd_id)
    print('updating...')
    sd_item.update(data=str(service_definition_path))
    print('publishing...')
    sd_item.publish(overwrite=True)

portal = 'https://www.arcgis.com'
user = ''

fc_path_str = r''

#: id of the hosted feature service's AGOL item
item_id = ''
#: id of the service definition AGOL item for the feature service.
sd_id = ''

item_name = 'md_test'
layer_name = 'md_test'
map_name = 'Map'
temp_dir_path = Path(r'')  #: Place to store the .sd and .sddraft files
new_item = False  #: True to publish new item, False to overwrite existing data

project_path = Path(r'')

print('Getting AGOL organization object...')
jake = arcgis.gis.GIS(portal, user, getpass.getpass())

print(f'Staging {fc_path_str}...')
service_definition_path = define_service(project_path, map_name, layer_name, fc_path_str, item_name, temp_dir_path)

#: publish if it doesn't exist yet
if new_item:
    publish(jake, service_definition_path)

#: otherwise, update using the item_id and sd_id above
else:
    overwrite(jake, service_definition_path, item_id, sd_id)