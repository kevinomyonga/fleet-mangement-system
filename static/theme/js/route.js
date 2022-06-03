/* ----------------- Start Document ----------------- */
(function($){
"use strict";

$(document).ready(function(){
	var responseJson;
	var tempMarker;
	var markers = [];
	var listItems = [];
	var getListURL = urlDrivers;
	var driverOrdersIframeURL = driverOrdersURL;

	$.get(getListURL, getList);

	function itemToHTML(item, index){
		var ID = item.ID;
		console.log(index);
		var percentComplete = 0;
		var percentHtml = '';
		var rating = item.rating == undefined ? 0 : item.rating;
		if(item.assigned_orders > 0){
			percentHtml =  `
					<div class="freelancer-details-list">
						<div><strong>${item.started_orders}</strong> or <strong>${item.assigned_orders}</strong> orders in progress</div>
					</div>
			`;
			percentComplete = item.started_orders > 0 ? item.started_orders/item.assigned_orders*100 : 0;
		}
		var html =  `
			<div class="freelancer"  onmouseover="showButtonsToRight(this)" onmouseout="hideButtonsToRight(this)">
				<!-- Overview -->
				<div class="freelancer-overview">
					<div class="freelancer-overview-inner">
						<!-- Bookmark Icon -->
						<span class="bookmark-icon"></span>
						
						<!-- Avatar -->
						<div class="freelancer-avatar">
							<a href="#"><img src="${item.thumbnail}"></a>
						</div>

						<!-- Name -->
						<div class="freelancer-name">
							<h4>${item.name}</h4>
							<div class="freelancer-rating">
								<div class="star-rating" data-rating="${rating}"></div>
							</div>
							
						</div>
					</div>
				</div>
				
				<!-- Details -->
				<div class="freelancer-details">
					<div class="freelancer-details-list">
						<div class="progress">
						  <div class="progress-bar" role="progressbar" style="width: ${percentComplete}%" aria-valuenow="${percentComplete}" aria-valuemin="0" aria-valuemax="100"></div>
						</div>
					</div>
					${percentHtml}
					<div class="freelancer-details-list">
						<a href="tel:+${item.phone_number}"><i class="icon-feather-phone"></i>&nbsp;+${item.phone_number}</a>
					</div>


					<div class="buttons-to-right" style="display:none">
						<button class="button gray driver-order-iframe" data-id="${ID}"><i class="icon-feather-list"></i></button>
						<button class="button gray location-hover" data-id="${ID}"><i class="icon-material-outline-my-location"></i></button>
					</div>
				</div>

			</div>
	`;
		return html;
	}

	function getList( data ) {
		var bounds = new google.maps.LatLngBounds();
		responseJson = jQuery.parseJSON(data);
		$('#live-ajax').html("");
		listItems = [];
		markers = [];
		if(responseJson != undefined && responseJson.items != undefined && responseJson.items.length > 0){
			responseJson.items.forEach(function(item, index) {
				var ID = item.ID;
				listItems[ID] = item;
				var html = itemToHTML(item, ID);
				$('#live-ajax').append(html);
				$('.live-available').show();
				$('.no-live-available').hide();
				var i = 0;
				console.log(item.orders);
				for(i = 0; i < item.orders.length; i++){
					var order = item.orders[i];
					orders[order.ID] = order;
					var lat = parseFloat(order.dropoff.location.coords.lat);
					var lng = parseFloat(order.dropoff.location.coords.lng);
					if(isNaN(lng) || isNaN(lng)) continue;
					var latLng = { lat: lat, lng: lng};
					var marker = new google.maps.Marker({position: latLng});
					marker.setTitle(`${order.ID}`);
					marker.setIcon(orderMarkerURL);
					marker.setMap(map);
					markers.push(marker);
					bounds.extend(latLng);
				}
			});
			markerCluster.addMarkers(markers);
			markerCluster.repaint();
			map.fitBounds(bounds);
		} else {
			$('.no-live-available').show();
			$('.live-available').hide();
		}
		$('#live-count').html(`<i class="icon-line-awesome-tasks"></i> ${responseJson.count} drivers`);
	}

	$("#live-ajax").delegate(".location-hover", "click", function(){
		var id = $(this).data("id");
		var driverItem = listItems[id];
		var lat = parseFloat(driverItem.location.lat);
		var lng = parseFloat(driverItem.location.lng);
		if(isNaN(lat) || isNaN(lng)) return;
		
		if(tempMarker != undefined){
			tempMarker.setMap(null);
		}
		var latLng = { lat: lat, lng: lng};
		tempMarker = new google.maps.Marker({position: latLng});
		tempMarker.setIcon(driverMarkerURL);
		tempMarker.setMap(map);
		infowindow.setContent(driverItem.name);
		infowindow.open({anchor: tempMarker,map,shouldFocus: false});
	});

	$("#live-ajax").delegate(".driver-order-iframe", "click", function(){
		var id = $(this).data("id");
		$('#assign-link').attr('href', `${driverOrdersIframeURL}?driver_id=${id}`);
		$('#assign-link').trigger('click');
	});

	
});

})(this.jQuery);

