(function () {
  function getHistoricName(feature) {
    return (
      feature?.properties?.area_name ||
      feature?.properties?.name ||
      feature?.properties?.historic_district ||
      feature?.properties?.district_name ||
      'Historic District'
    );
  }

  function getPopupHtml(feature) {
    const props = feature?.properties || {};
    const rows = [];
    rows.push(`<div style="font-weight:600;margin-bottom:4px;">${getHistoricName(feature)}</div>`);
    if (props.borough) rows.push(`<div><strong>Borough:</strong> ${props.borough}</div>`);
    if (props.cb_name) rows.push(`<div><strong>Community Board:</strong> ${props.cb_name}</div>`);
    if (props.cb_num) rows.push(`<div><strong>Community Board:</strong> ${props.cb_num}</div>`);
    return `<div style="line-height:1.35;">${rows.join('')}</div>`;
  }

  function ensureOverlayControl(map) {
    if (map._historicDistrictsOverlayControl) return map._historicDistrictsOverlayControl;
    if (map.layerControl && typeof map.layerControl.addOverlay === 'function') {
      map._historicDistrictsOverlayControl = map.layerControl;
      return map.layerControl;
    }
    if (window.layerControl && typeof window.layerControl.addOverlay === 'function') {
      map._historicDistrictsOverlayControl = window.layerControl;
      return window.layerControl;
    }
    const control = L.control.layers(null, null, { collapsed: false, position: 'topright' }).addTo(map);
    map._historicDistrictsOverlayControl = control;
    return control;
  }

  window.loadHistoricDistrictsLayer = async function loadHistoricDistrictsLayer(options) {
    const {
      map,
      geojsonUrl,
      layerLabel = 'Historic Districts',
      addToMap = true,
      fitBounds = false
    } = options || {};

    if (!map) throw new Error('loadHistoricDistrictsLayer: map is required');
    if (!geojsonUrl) throw new Error('loadHistoricDistrictsLayer: geojsonUrl is required');

    if (!map.getPane('historicDistrictsPane')) {
      map.createPane('historicDistrictsPane');
      map.getPane('historicDistrictsPane').style.zIndex = 430;
    }

    const response = await fetch(geojsonUrl, { cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Historic districts GeoJSON failed to load: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    const layer = L.geoJSON(data, {
      pane: 'historicDistrictsPane',
      style: function () {
        return {
          color: '#6b3f1d',
          weight: 2,
          opacity: 0.95,
          fillColor: '#a66a2c',
          fillOpacity: 0.18
        };
      },
      onEachFeature: function (feature, layer) {
        layer.bindPopup(getPopupHtml(feature));
      }
    });

    const control = ensureOverlayControl(map);
    control.addOverlay(layer, layerLabel);

    if (addToMap) {
      layer.addTo(map);
    }

    if (fitBounds && layer.getBounds && layer.getBounds().isValid()) {
      map.fitBounds(layer.getBounds(), { padding: [20, 20] });
    }

    return layer;
  };
})();
