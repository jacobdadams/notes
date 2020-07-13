# Turn the visibility of any sub-group layers off

```python
project = arcpy.mp.ArcGISProject("CURRENT")
cur_map = project.activeMap
for l in cur_map.listLayers():
    if l.isGroupLayer:
        for l2 in l.listLayers():
            l2.visible = False
```
