# GDAL Stuff

## Pipelines

Create slope polygons from DEMs in a folder:
`for %f in (new_tiles\*.tif) do (gdal pipeline ! read %f ! slope --unit percent ! reclassify -m "[0,15)=NO_DATA; [15,20)=1; [20,1000)=2; DEFAULT=NO_DATA" ! polygonize -c ! write --format OpenFileGDB --update --config OGR_ORGANIZE_POLYGONS=skip --output-layer %~nf d:\new_hillshade\slope2026_percent.gdb)`

`--config OGR_ORGANIZE_POLYGONS=skip` handles the "Warning 1: organizePolygons() received a polygon with more than 100 parts. The processing may be really slow.
You can skip the processing by setting METHOD=SKIP, or only make it analyze counter-clock wise parts by setting METHOD=ONLY_CCW if you can assume that the outline of holes is counter-clock wise defined" warning.

rescale and resample 30m to 10m:
`gdal raster pipeline ! read 30m_all_turbid-315-15-250-200steps.tif  ! scale --ot byte --dst-min=1 --dst-max=255 ! resize --resolution 10,10 -r cubic ! edit --nodata 0 ! write --co compress=lzw --co bigtiff=yes 30m_skyshade_10m-2.tif`
