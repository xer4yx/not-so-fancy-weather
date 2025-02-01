import React from 'react';
import Header from './components/Header';
import WeatherContainer from './components/WeatherContainer';
import './App.css';

function App() {
  return (
    <div className="App">
      <Header />
      <WeatherContainer />
    </div>
  );
}

export default App;
