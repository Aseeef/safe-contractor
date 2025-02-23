// App.js
import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Homepage from './HomePage';
import ReliableContractorProfile from './ReliableContractorProfile';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Homepage />} />
        // Fix in App.js
        <Route path="/contractor/:contractorName" element={<ReliableContractorProfile />} />
      </Routes>
    </Router>
  );
}

export default App;