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
        <Route path="/contractor/" element={<ReliableContractorProfile />} />
      </Routes>
    </Router>
  );
}

export default App;