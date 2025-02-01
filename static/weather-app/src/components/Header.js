import React from 'react';
import './Header.css'; // Optional: Create a separate CSS file for header styles

const Header = () => {
  return (
    <header className="App-header">
      <nav>
        <h1>NotSoFancyWeather</h1>
        <div className="header-links">
          <a href="http://localhost:8668/docs" target="_blank" rel="noopener noreferrer">API Docs</a>
          <a href="/login">Login</a>
        </div>
      </nav>
    </header>
  );
};

export default Header; 