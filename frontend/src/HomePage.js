// Homepage.js
import React from 'react';
import myBackground from './seaport.jpg';
import './HomePage.css';

function Homepage() {
  return (
    <div className="main-container">
      <div className="brand-container">
        <span className="logo-text-bold">Safe</span>
        <span className="text-regular">Contractor</span>
      </div>

      <p className="tagline">Your resource for reliable contractors</p>

      <div className="search-container">
        <div className="search-bar-container">
          <input
            type="text"
            placeholder="Name"
            className="search-input"
          />
          <div className="divider"></div>
          <input
            type="text"
            placeholder="License ID (Optional)"
            className="search-input"
          />
          <div className="divider"></div>
          <input
            type="text"
            placeholder="Location"
            className="search-input"
          />
          <div className="divider"></div>
          <input
            type="text"
            placeholder="Radius"
            className="search-input"
          />
          <button className="search-button">Search</button>
        </div>
      </div>
    </div>
  );
}

export default Homepage;