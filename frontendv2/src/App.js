import React from 'react';
import myBackground from './seaport.jpg'; 

const mainContainerStyle = {
  position: 'relative',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  height: '100vh',
  // Combine the overlay and the background image
  backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.15)), url(${myBackground})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  backgroundRepeat: 'no-repeat',
};


// SafeContractor logo container 
const brandContainerStyle = {
  position: 'absolute',
  top: '20px',
  left: '20px',
  width: '310px',
  height: '80px',
  display: 'flex',
  alignItems: 'center',
};

const LogoTextBoldStyle = {
  color: 'hsl(123, 89%, 40%)',
  fontFamily: 'Inter, sans-serif',
  fontSize: '36px',
  fontStyle: 'normal',
  fontWeight: 700,
  lineHeight: 'normal',
};

const textRegularStyle = {
  color: '#FFF',
  fontFamily: 'Inter, sans-serif',
  fontSize: '36px',
  fontStyle: 'normal',
  fontWeight: 400,
  lineHeight: 'normal',
};

// Tagline
const taglineStyle = {
  fontFamily: 'Inter, sans-serif',
  fontSize: '36px', 
  fontStyle: 'normal',
  color: '#FFF',
  fontWeight: 900,
  lineHeight: 'normal',
  textAlign: 'center',
  marginBottom: '10px', 
};

const searchBarContainerStyle = {
  display: 'flex',
  alignItems: 'center',
  backgroundColor: '#fff',
  border: '1px solid #ccc',
  borderRadius: '50px', 
  padding: '5px 10px',
};

// Shared style for each input field
const searchInputStyle = {
  border: 'none',
  outline: 'none',
  padding: '10px',
  fontSize: '16px',
  fontFamily: 'Inter, sans-serif',
  flex: 1, // expand to fill available space
};

// A thin vertical line between inputs
const verticalDividerStyle = {
  height: '30px',
  width: '1px',
  backgroundColor: '#ccc',
  margin: '0 10px',
};

// The Search button (on the right side)
const searchButtonStyle = {
  padding: '10px 20px',
  border: 'none',
  borderRadius: '40px',
  backgroundColor: '#088B0E',
  color: '#fff',
  fontSize: '16px',
  fontFamily: 'Inter, sans-serif',
  cursor: 'pointer',
};

function App() {
  return (
    
    <div style={mainContainerStyle}>
      {/* Logo at the top left */}


      <div style={brandContainerStyle}>
        <span style={LogoTextBoldStyle}>Safe</span>
        <span style={textRegularStyle}>Contractor</span>
      </div>

      {/* Tagline */}
      <p style={taglineStyle}>Your resource for reliable contractors</p>

      {/* Search bar with three inputs + Search button */}
      <div style={searchBarContainerStyle}>
        <input
          type="text"
          placeholder="Name"
          style={searchInputStyle}
        />
        <div style={verticalDividerStyle}></div>
        <input
          type="text"
          placeholder="License ID (Optional)"
          style={searchInputStyle}
        />
        
        <div style={verticalDividerStyle}></div>
        <input
          type="text"
          placeholder="Location"
          style={searchInputStyle}
        />

        <div style={verticalDividerStyle}></div>
        <input
          type="text"
          placeholder="Radius"
          style={searchInputStyle}
        />

        <button style={searchButtonStyle}>Search</button> 
      </div>
    </div>
  );
}

export default App;
