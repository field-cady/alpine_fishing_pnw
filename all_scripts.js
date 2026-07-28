var mymap = null;
var markerCluster = null;
var markers = [];

// Default icon for Leaflet
var defaultIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [20, 32],
  iconAnchor: [10, 32],
  popupAnchor: [1, -28],
  shadowSize: [32, 32]
});

// Functions for populating the map

var initializeMap = function() {
  // Center on the continental US so all states are visible on load
  mymap = L.map('mapid').setView([39.5, -96.0], 4);
  
  L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
  }).addTo(mymap);
  
  markerCluster = L.markerClusterGroup({
    chunkedLoading: true,
    maxClusterRadius: 50
  });
  mymap.addLayer(markerCluster);
}

var downloadDataAndRender = function(url) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.responseType = 'json';
    xhr.onload = function() {
      if (xhr.status === 200) {
        var data = xhr.response;
        renderData(data);
      } else {
        console.error("Failed to load data from " + url);
      }
    };
    xhr.send();
};

var renderData = function(dat) {
  if (dat["timestamp"]) {
    showTimestamp(dat["timestamp"]);
  }
  addLakesToMap(dat["lakes"]);
  populateSpeciesFilter(dat["lakes"]);
  updateMarkers();
}

// --- Species -> filter category mapping (FRONTEND ONLY; not stored in data) ---
// Display order for the filter checkboxes; "Other" always last.
var SPECIES_CATEGORIES = ["Trout", "Bass", "Panfish", "Catfish", "Walleye & Perch",
  "Crappie", "Pike & Muskie", "Carp & Rough Fish", "Salmon", "Other"];

var speciesCategory = function(name) {
  var n = (name || '').toLowerCase();
  var has = function(keys) {
    for (var i = 0; i < keys.length; i++) { if (n.indexOf(keys[i]) !== -1) return true; }
    return false;
  };
  // Order matters: more specific buckets first.
  if (n.indexOf('crappie') !== -1 || n.indexOf('wcr') !== -1) return 'Crappie';
  if (has(['salmon', 'kokanee', 'chinook', 'coho', 'sockeye', 'chum'])) return 'Salmon';
  if (has(['trout', 'char', 'splake', 'steelhead', 'redband', 'grayling',
           'cutthroat', 'rbt', 'goldbow', 'brownbow', 'cutbow'])) return 'Trout';
  if (has(['catfish', 'bullhead', 'madtom', 'stonecat'])) return 'Catfish';
  if (has(['pike', 'muskellunge', 'musky', 'muskie', 'pickerel'])) return 'Pike & Muskie';
  if (has(['walleye', 'sauger', 'saugeye', 'perch'])) return 'Walleye & Perch';
  if (has(['bass', 'wiper', 'largemouth', 'smallmouth', 'striped', 'stb'])) return 'Bass';
  if (has(['bluegill', 'sunfish', 'pumpkinseed', 'redear', 'warmouth', 'bream',
           'longear', 'shellcracker', 'panfish', 'gsf', 'blg'])) return 'Panfish';
  if (has(['carp', 'buffalo', 'sucker', 'drum', 'bowfin', 'gar', 'burbot', 'whitefish',
           'cisco', 'chub', 'sturgeon', 'paddlefish', 'tench', 'goldfish', 'shad',
           'herring', 'minnow', 'dace', 'sculpin', 'goldeye', 'quillback',
           'shiner', 'smelt', 'stickleback', 'lamprey'])) return 'Carp & Rough Fish';
  return 'Other';
};

// Set of filter categories present at a lake (cached on the lake object).
var lakeCategories = function(lk) {
  if (lk._cats) return lk._cats;
  var set = {};
  var sp = lk.species || [];
  for (var i = 0; i < sp.length; i++) { set[speciesCategory(sp[i])] = true; }
  lk._cats = set;
  return set;
};

var toggleSpeciesMenu = function() {
  var menu = document.getElementById('species_menu');
  if (menu) menu.classList.toggle('open');
};

var updateSpeciesToggleLabel = function() {
  var checked = document.querySelectorAll('#species_menu input[type=checkbox]:checked');
  var label = document.getElementById('species_toggle_label');
  if (label) label.textContent = (checked.length === 0) ? 'Any Species' : (checked.length + ' selected');
};

var populateSpeciesFilter = function(lakes) {
  var counts = {};
  for (var c = 0; c < SPECIES_CATEGORIES.length; c++) { counts[SPECIES_CATEGORIES[c]] = 0; }
  for (var i = 0; i < lakes.length; i++) {
    var cats = lakeCategories(lakes[i]);
    for (var k in cats) { if (counts[k] !== undefined) counts[k]++; }
  }

  var menu = document.getElementById('species_menu');
  if (!menu) return;
  menu.innerHTML = '';
  for (var c2 = 0; c2 < SPECIES_CATEGORIES.length; c2++) {
    var cat = SPECIES_CATEGORIES[c2];
    if (!counts[cat]) continue;   // don't show empty categories
    var row = document.createElement('label');
    row.className = 'dropdown-item';
    row.innerHTML = '<input type="checkbox" value="' + cat + '" onchange="updateMarkers()"> ' +
      '<span>' + cat + '</span><span class="cat-count">' + counts[cat] + '</span>';
    menu.appendChild(row);
  }
}

var addLakesToMap = function(lakes) {
  for (var i=0; i<lakes.length; i++) {
    var lk = lakes[i];
    
    if (lk['lat'] && lk['lon']) {
        var m = L.marker([lk['lat'], lk['lon']], {icon: defaultIcon});
        // Lazy popup: build the HTML only when the marker is actually opened,
        // instead of eagerly for all ~55k markers at load.
        m.bindPopup(function() { return lake2marker_html(lk); });
        
        m.lake = lk;
        lk.marker = m;
        markers.push(m);
    }
  }
}

var lake2marker_html = function(lk) {
  var html = '<div class="popup-custom">';
  
  if (lk['url']) {
      html += '<a target="_blank" href="'+lk['url']+'" class="popup-title">'+lk['name']+'</a>';
  } else {
      html += '<div class="popup-title">'+lk['name']+'</div>';
  }
  
  html += '<div class="popup-row"><span class="popup-label">State</span><span class="popup-value">'+lk['state']+'</span></div>';
  
  if (lk['county']) {
      html += '<div class="popup-row"><span class="popup-label">County</span><span class="popup-value">'+lk['county']+'</span></div>';
  }
  if (lk['elevation']) {
      html += '<div class="popup-row"><span class="popup-label">Elevation</span><span class="popup-value">'+String(Math.round(lk['elevation']))+' ft</span></div>';
  }
  if (lk['area']) {
      html += '<div class="popup-row"><span class="popup-label">Size</span><span class="popup-value">'+String(lk['area'])+'</span></div>';
  }
  if (lk['description']) {
      html += '<div style="margin-top: 8px; font-size: 0.85rem; color: #64748b; line-height: 1.4; border-top: 1px solid #e2e8f0; padding-top: 8px;">'+lk['description']+'</div>';
  }
  
  if (lk['species'] && lk['species'].length > 0) {
    html += '<div class="popup-species">';
    html += '<div class="popup-label" style="margin-bottom: 4px;">Species:</div>';
    for (var i = 0; i < lk['species'].length; i++) {
      html += '<span class="species-tag">' + lk['species'][i] + '</span>';
    }
    html += '</div>';
  }
  
  html += '</div>';
  return html;
}

var getFilterFunction = function() {
  // Name Search
  var search_filter_value = document.getElementById('search_filter') ? document.getElementById('search_filter').value.toLowerCase().trim() : '';
  var text_search_filter = function(lk) {
    if (search_filter_value === '') return true;
    return (lk['name'] && lk['name'].toLowerCase().includes(search_filter_value));
  }
  
  // Species categories (multi-select checkboxes). No boxes checked = show all.
  var checkedBoxes = document.querySelectorAll('#species_menu input[type=checkbox]:checked');
  var checkedCats = [];
  for (var cb = 0; cb < checkedBoxes.length; cb++) { checkedCats.push(checkedBoxes[cb].value); }
  var species_filter;
  if (checkedCats.length === 0) {
    species_filter = function(lk) { return true; }
  } else {
    species_filter = function(lk) {
      var cats = lakeCategories(lk);
      for (var i = 0; i < checkedCats.length; i++) { if (cats[checkedCats[i]]) return true; }
      return false;
    }
  }
  
  // Size
  var size_filter_value = document.getElementById('size_filter') ? document.getElementById('size_filter').value : 'any';
  var size_filter;
  if (size_filter_value === 'any') {
    size_filter = function(el){return true;}
  } else if (size_filter_value === '<5') {
    size_filter = function(el){return el && parseFloat(el) < 5;}
  } else if (size_filter_value === '5-10') {
    size_filter = function(el){if (!el) return false; var val = parseFloat(el); return (5 <= val && val <= 10);}
  } else if (size_filter_value === '>10') {
    size_filter = function(el){return el && 10 < parseFloat(el);}
  }
  
  // Elevation
  var elev_filter_value = document.getElementById('elevation_filter') ? document.getElementById('elevation_filter').value : 'any';
  var elev_filter;
  if (elev_filter_value === 'any') {
    elev_filter = function(el){return true;}
  } else if (elev_filter_value === '<3000') {
    elev_filter = function(el){return el && parseFloat(el) < 3000;}
  } else if (elev_filter_value === '3000-5000') {
    elev_filter = function(el){if (!el) return false; var val = parseFloat(el); return (3000 <= val && val <= 5000);}
  } else if (elev_filter_value === '>5000') {
    elev_filter = function(el){return el && 5000 < parseFloat(el);}
  }

  return function(lk) {
    return text_search_filter(lk) && species_filter(lk) && size_filter(lk.area) && elev_filter(lk.elevation);
  }
}

var updateMarkers = function() {
  updateSpeciesToggleLabel();
  var filter_func = getFilterFunction();
  var validMarkers = [];
  
  for (var i=0; i<markers.length; i++) {
    var m = markers[i];
    var lk = m.lake;
    if (filter_func(lk)) {
      validMarkers.push(m);
    }
  }
  
  markerCluster.clearLayers();
  markerCluster.addLayers(validMarkers);
}

var showTimestamp = function(timestamp) {
  var timestamp_div = document.getElementById("last_update_timestamp");
  if (timestamp_div) {
    timestamp_div.innerHTML = "The data was last updated at: " + timestamp;
  }
}

// Close the species dropdown when clicking outside of it.
document.addEventListener('click', function(e) {
  var dd = document.getElementById('species_dropdown');
  var menu = document.getElementById('species_menu');
  if (dd && menu && !dd.contains(e.target)) menu.classList.remove('open');
});

initializeMap();
downloadDataAndRender("data/all_states.json");