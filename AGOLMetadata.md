# Understanding AGOL and Feature Service Metadata

The location of metadata in AGOL isn't immediately obvious, and I've not been able to find any good, single-page documentation on it. It becomes easier to follow when you understand all the different pieces at play. First, we'll discuss the AGOL and Hosted Feature Service (HFS) architecture. Then we'll dive into the two or three metadatas, their sources, where they're located, and how they can be updated.

## AGOL Architecture

### Splitting hairs

While it's easy to mash them together, an AGOL item and a Hosted Feature Service (HFS) are really two separate things.

An HFS is a RESTful service hosted in Esri's cloud that provides access to individual geographic features. Contrast this with a Feature Service hosted in a stand-alone ArcGIS Server. A feature service has one or more layers, identified by a layer id in the service URL (`https://<server_name>/arcgis/rest/services/<service_name>/FeatureServer/0`, `/1`, etc).

AGOL is basically a giant card catalog (anyone remember those?) for finding Esri-cloud-based GIS items. AGOL items are just a reference or pointer to some cloud-based resource along with some additional data about the resource—summary, description, tags, terms of use, etc. The resources can include individual files, like CSVs or GDBs; web applications, like web maps or Web AppBuilder apps; and REST services, like feature services or map image services. There are probably other resource types that I'm forgetting.

### Publishing an HFS

To understand what happens when you publish an HFS, it's helpful to follow the python code. See the `define_service()` function in `AGOL_item_updates.py` in this repository. This (I think) mirrors what's happening behind the scenes when you use the UI to share a web layer.

First, we programmatically open the Pro project and select the map we want to work with.

Next, we make sure we've only got the layers we want to share. In the example code, we remove any existing layers and tables to ensure a blank map, and then add our desired layer.

Now that our map is prepared, we create a draft service definition _from the map object_, not the layer. This defines what kind of server it will end up on, what kind of service we want, and what it will be called. We then stage the draft service definition into an actual service definition.

This is where AGOL comes into play. We upload our service definition to our AGOL organization, where it is just a file being stored in their servers. By calling the `.publish()` function on the service definition AGOL item, we tell their servers to create a new feature service on their servers using the information in the service definition.

As part of the publishing process, AGOL creates a new item that points to our new Hosted Feature Service. This item allows others to easily find it in AGOL and for us to share information about it.

So, in the end, we have three distinct things:
1. The HFS itself.
1. The individual layers within the HFS.
1. The AGOL item referring to the HFS.

(We also have a service definition file hosted in Esri's cloud and it's associated AGOL item, but these aren't germane to the metadata discussion)

## The Two/Three Different Metadatas

Now that we understand the relationships between an AGOl item and an HFS, it's easier to understand a fundamental principle of AGOL metadata: **each of our three distinct items has (or can have) it's own metadata**. Each metadata is stored in a separate location (in XML?) and is accessible from it's own URL/UI element.

### Hosted Feature Service Metadata

(**NOTE: This may be the same metadata as the AGOL Item**, just accessed in a different place)

The HFS metadata allows a publisher to specify information about the collection of layers in that feature service.

> **Access:** `https://<server_name>/arcgis/rest/services/<service_name>/FeatureServer/info/metadata`
>
> **Source:** The metadata set for the map in ArcGIS Pro. This is why it's important to remember that when we publish a feature service, we do it from a map. If the map doesn't have any metadata set, it *may* grab some basic information from one (or more; I haven't tested a multi-layer service) of the layers, including the spatial reference, fields and types, and the source feature class name. It does not appear to pull any descriptions, summaries, etc from the layer.
>
> **Updating:** I've not verified my theory on this, but I believe this metadata can only be updated by overwriting the service with a map that has the new metadata set in it's properties. **OR**, it is updated when you update the AGOL Item's metadata using the AGOL metadata editor.

### Individual Layers within an HFS

Each layer in a hosted feature service also has it's own metadata. This allows us to pull the information specific to the source dataset.

> **Access:** `https://<server_name>/arcgis/rest/services/<service_name>/FeatureServer/<layer_id_number>/metadata`
>
> **Source:** The metadata set for the layer's source feature class in a GDB or SDE.
>
> **Updating:** The layer's source can only be updated programmatically by updating the source feature class' metadata in the GDB/SDE and then overwriting the service with the new information (in python, overwriting the service definition with new data and then calling `.publish(overwrite=True)` on the service definition item). The layer's metadata can be edited with the UI metadata editor in ArcGIS online.

### AGOL Item

Any(?) AGOL item can have metadata associated with it. The summary, description, etc displayed on the item's page are stored in this metadata. This metadata is also used for the information displayed in Hub/OpenData and is checked for organization names to build the Source list.

> **Access:** The metadata UI button (you may first need to [enable metadata](https://doc.arcgis.com/en/hub/get-started/frequently-asked-questions.htm#GUID-9843B713-46D2-4938-A961-EC0CD81AE410) for your AGOL organization). Certain elements, like the description and summary, can also be accessed programmatically with the ArcGIS API for Python (`item.description`).
>
> **Source:** If uploaded via a script, it appears the AGOL item's metadata pulls the same few things from the source data as the service metadata (it may actaully be the same metadata as the feature service's metadata). If uploaded from the ArcGIS Pro UI, it also appears to pull in the summary, description, and tags from the source dataset (except where overwritten in the tool UI).
>
> **Updating:** There are three ways to update an AGOL item's metadata:
> 1. The few fields exposed as properties of the item's object in the ArcGIS API for Python can be set using the `item.update(item_properties={'property': 'value'})` ([docs](https://developers.arcgis.com/python/api-reference/arcgis.gis.toc.html#arcgis.gis.Item.update)).
> 1. The item's entire metadata can be overwritten by setting the item object's `.metadata` parameter to either a path to a metadata xml file or to the xml data as a string. The source metadata needs to be in the ArcGIS metadata format. Depending on the age and "crustiness" of the source metadata, it may be neccesary to upgrade the metadata. It may also be necessary to use the `exact copy of.xslt` template included with ArcMap (`C:\Program Files (x86)\ArcGIS\Desktop10.7\Metadata\Stylesheets\gpTools\exact copy of.xslt`) when exporting the metadata to xml.
> 1. The "Metadata" UI button on the item's webpage opens a metadata editor, which can be used to manually update any of the metadata fields.