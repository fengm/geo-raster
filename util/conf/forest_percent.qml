<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.0.1-Dufour" minimumScale="0" maximumScale="1e+08" hasScaleBasedVisibilityFlag="0">
  <pipe>
    <rasterrenderer opacity="1" alphaBand="-1" classificationMax="100" classificationMinMaxOrigin="User" band="1" classificationMin="0" type="singlebandpseudocolor">
      <rasterTransparency/>
      <rastershader>
        <colorrampshader colorRampType="INTERPOLATED" clip="0">
          <item alpha="255" value="5" label="&lt; 5%" color="#ffffff"/>
          <item alpha="255" value="15" label="5-20%" color="#fffcd9"/>
          <item alpha="255" value="30" label="20-30%" color="#c5ffaa"/>
          <item alpha="255" value="50" label="30-50%" color="#75ecae"/>
          <item alpha="255" value="75" label="50-75%" color="#00c300"/>
          <item alpha="255" value="100" label="> 75%" color="#316300"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0"/>
    <huesaturation colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
