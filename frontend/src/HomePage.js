// HomePage.js
import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import './HomePage.css';
import { debounce } from 'lodash'; // Ensure you have lodash installed: npm install lodash

function Homepage() {
    const [contractorName, setContractorName] = useState('');
    const [licenseId, setLicenseId] = useState('');
    const [contractorList, setContractorList] = useState([]);
    const [error, setError] = useState(null);

    const handleNameChange = (event) => {
        setContractorName(event.target.value);
    };

    const handleLicenseIdChange = (event) => {
        setLicenseId(event.target.value);
    };

    const fetchContractors = useCallback(
        debounce(async () => {
            if (!contractorName && !licenseId) {
                setContractorList([]);
                return;
            }

            let apiUrl = 'http://localhost:8003/api/fuzzy-contractor?';
            if (contractorName) {
                apiUrl += `contractor_name=${contractorName}`;
            }
            apiUrl += '&fuzz_ratio=75';

            try {
                const response = await fetch(apiUrl);
                if (!response.ok) {
                    // If the response is not ok, try to parse the JSON
                    let errorMessage = `HTTP error! Status: ${response.status}`;
                    try {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorMessage; // Use detail if available
                    } catch (jsonError) {
                        console.error("Failed to parse error JSON:", jsonError);
                        // Keep original errorMessage if parsing fails
                    }
                    throw new Error(errorMessage);
                }
                const data = await response.json();
                setContractorList(Array.isArray(data) ? data : [data]); // Handle both single object and array responses
                setError(null);
            } catch (err) {
                console.error("Error fetching contractors:", err);
                setError(`Failed to fetch contractors. Please try again. ${err.message}`);
                setContractorList([]);
            }
        }, 300), // 300ms debounce delay
        [contractorName, licenseId]
    );

    const handleSubmit = (event) => {
        event.preventDefault(); // Prevent default form submission
        fetchContractors();
    };

    return (
        <div className="main-container">
            <div className="brand-container">
                <span className="logo-text-bold">Safe</span>
                <span className="text-regular">Contractor</span>
            </div>

            <p className="tagline">Your resource for reliable contractors</p>

            <form className="search-container" onSubmit={handleSubmit}>
                <div className="search-bar-container">
                    <input
                        type="text"
                        placeholder="Name"
                        className="search-input"
                        value={contractorName}
                        onChange={handleNameChange}
                    />
                    <div className="divider"></div>
                    <input
                        type="text"
                        placeholder="License ID (Optional)"
                        className="search-input"
                        value={licenseId}
                        onChange={handleLicenseIdChange}
                    />
                    <div className="divider"></div>
                    <button type="submit" className="search-button">Search</button>
                </div>
            </form>

            {error && <p className="error">{error}</p>}

            {contractorList.length > 0 && (
                <div className="contractor-list">
                    <h3>Contractors:</h3>
                    <ul>
                        {contractorList.map((contractor) => (
                            <li key={contractor.name}>
                                <Link to={`/contractor/${encodeURIComponent(contractor.name)}`}>{contractor.name}</Link>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
}

export default Homepage;