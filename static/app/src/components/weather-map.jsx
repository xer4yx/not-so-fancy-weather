import React, { useState, useEffect, memo, useCallback } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default marker icons in leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// This component handles map view updates
const MapUpdater = memo(({ position }) => {
  const map = useMap();
  
  useEffect(() => {
    if (position) {
      map.setView(position, 10, {
        animate: true,
        duration: 1
      });
    }
  }, [map, position]);
  
  return null;
});

MapUpdater.displayName = 'MapUpdater';

export const WeatherMap = memo(({ weatherData }) => {
  const defaultPosition = [51.505, -0.09]; // Default position (London)
  const [markerPosition, setMarkerPosition] = useState(defaultPosition);
  const [isVisible, setIsVisible] = useState(false);
  
  useEffect(() => {
    if (weatherData && weatherData.city && weatherData.city.coord) {
      const { lat, lon } = weatherData.city.coord;
      setMarkerPosition([lat, lon]);
    }
  }, [weatherData]);

  // Animation for map appearance
  useEffect(() => {
    // Short delay before showing to allow for component mounting
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 50);
    
    return () => clearTimeout(timer);
  }, []);

  const renderMap = useCallback(() => (
    <div 
      className={`transition-opacity duration-500 ease-in-out ${isVisible ? 'opacity-100' : 'opacity-0'}`}
      style={{ height: '100%', width: '100%' }}
    >
      <MapContainer 
        center={defaultPosition} 
        zoom={10} 
        style={{ height: '100%', width: '100%', minHeight: '400px' }}
        className="z-0"
        aria-label={weatherData ? `Map showing ${weatherData.city.name}, ${weatherData.city.country}` : 'Weather map'}
        zoomControl={true}
        attributionControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          className="transition-opacity duration-300"
        />
        <MapUpdater position={markerPosition} />
        {weatherData && weatherData.city && (
          <Marker 
            position={markerPosition}
            eventHandlers={{
              add: (e) => {
                e.target.openPopup();
                setTimeout(() => e.target.closePopup(), 3000);
              }
            }}
          >
            <Popup>
              <div className="font-sans">
                <span className="font-semibold block mb-1">{weatherData.city.name}, {weatherData.city.country}</span>
                <span className="capitalize block">{weatherData.list[0].weather[0].description}</span>
                <span className="block">Temperature: {Math.round(weatherData.list[0].main.temp - 273.15)}°C</span>
              </div>
            </Popup>
          </Marker>
        )}
      </MapContainer>
    </div>
  ), [weatherData, markerPosition, defaultPosition, isVisible]);

  return (
    <div 
      className="h-full w-full mx-auto overflow-hidden shadow-xl border border-gray-200 rounded-lg transition-all duration-300 ease-in-out"
      role="region"
      aria-label="Interactive weather map"
    >
      {renderMap()}
    </div>
  );
});

WeatherMap.displayName = 'WeatherMap'; 