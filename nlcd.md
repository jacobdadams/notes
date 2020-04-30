# Playing with the NLCD

## Alter the colors of the NLCD

1. Create a new text file with the color lookup values for each value in the original NLCD on their own line
   - ie, `11 70 107 159` for NLCD value 11
   - We'll call this `color.txt`
1. Create a vrt using the new color values (https://gdal.org/programs/gdaldem.html#color-relief):
   - `gdaldem color-relief in_nlcd_raster color.txt recolored-nlcd.vrt`
1. If desired, translate the vrt to 3-band rgb tif using the `-expand rgb` switch. This can give you better compression options, allow you do things like blurs and other image operations, and subset a specific area):
   - `gdal_translate -expand rgb recolored-nlcd.vrt recolored-nlcd.tif`
   - Use the `-co compress=lzw` switch to compress using LZW (you could also use jpeg if lossy is OK)
   - Use the `-projwin` switch to subset the NLCD to match your data (this gets tricky- the NLCD is in a nation-wide Albers projection, which can have a significantly different N/S orientation than local projections like UTM)
1. If you've translated it to a 3-band tif, it often loads in ArcGIS with a weird stretch so the colors look wrong. Make sure to change your stretch type to `None` and the Gamma value for each band to `1`. 
