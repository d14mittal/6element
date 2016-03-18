'use strict';

(function(global){

    var markersLayer;

   // Add a preview footer under the map when clicking marker
    var onClickMarker = function (e){
        
        var place = e.target.place;
        
        var preview = document.querySelector('#preview');
        if(preview !== null)
            preview.parentNode.removeChild(preview);

        // preview
        preview = document.createElement('nav');
        preview.setAttribute('id', 'preview');
        document.querySelector('#map').parentNode.appendChild(preview);

        // adapt-width
        var adaptWidth = document.createElement('div');
        adaptWidth.classList.add('adapt-width');
        preview.appendChild(adaptWidth);

        // place-header
        var placeHeader = document.createElement('ul');
        placeHeader.classList.add('place-header');
        adaptWidth.appendChild(placeHeader);

        // avatar
        var li = document.createElement('li');
        placeHeader.appendChild(li);
        var avatar = document.createElement('span');
        avatar.classList.add('place-avatar');
        li.appendChild(avatar);
        avatar.style.backgroundColor = place.properties.color;
        avatar.style.height = '40px';
        avatar.style.width = '40px';

        // title
        li = document.createElement('li');
        placeHeader.appendChild(li);
        var title = document.createElement('span');
        title.classList.add('place-title');
        var distance = (place.properties.distance > 1000) ? (place.properties.distance/1000).toFixed(2) + ' Km' : 
                                                  Math.round(place.properties.distance).toString() + ' m';
        li.appendChild(title);
        title.innerHTML = place.properties.name+' - '+distance+'<br/><span class="place-subtitle">'+place.properties.file+'</span>';

        // 2nd ul + icons
        var ul = document.createElement('ul');
        placeHeader.appendChild(ul);
        ul.style.float = 'right';
        ul.style.listStyleType = 'none';
        ul.innerHTML =  '<li><button class="place-infos"><img src="../img/infos.svg"/></button></li>';
        ul.innerHTML += '<li><button class="place-available"><img src="../img/available.svg"/></button></li>';
    }


    global.displayPlaces = function(map, places, filterValues){

        if(markersLayer){
            map.removeLayer(markersLayer);
            markersLayer = undefined;
        }

        var markers = places
        .filter(function(place){
            var relevantFilter = filterValues.find(function(fv){
                return fv.name === place.properties.file;
            });
            
            if(!relevantFilter)
                console.warn('No filter for place', place);
            
            return relevantFilter.checked;
        })
        .map(function(place){
            var isCenter = (place.properties.type === 'centre');
            var options = {
                color: 'black',
                fill: true,
                fillColor: place.properties.color, 
                fillOpacity: 1,
                radius: isCenter ? 10 : 7,
                clickable: true,
                weight: isCenter ? 5 : 3 
            };

            var lat = place.geometry.coordinates.lat || place.geometry.coordinates[1];
            var lon = place.geometry.coordinates.lon || place.geometry.coordinates[0];

            var marker = new L.CircleMarker(new L.LatLng(lat, lon), options);
            marker['place'] = place;
                    marker.on('click', onClickMarker); 

            return marker;
        });

        markersLayer = L.layerGroup(markers);
        map.addLayer(markersLayer);
    };

})(this);