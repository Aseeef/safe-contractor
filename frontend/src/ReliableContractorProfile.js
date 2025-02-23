// ReliableContractorProfile.js
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserCircle } from '@fortawesome/free-solid-svg-icons';
import { library } from '@fortawesome/fontawesome-svg-core';
import { faCheckSquare, faSquare } from '@fortawesome/free-regular-svg-icons';
import './ContractorProfile.css';

library.add(faCheckSquare, faSquare);

const ReliableContractorProfile = () => {
  const { contractorName } = useParams(); // Get the contractor name from the URL
  const [contractorData, setContractorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        if (!contractorName) {
          // Handle case where contractorName is initially undefined
          return;
        }

        const apiUrl = `/search-contractor?contractor_name=${contractorName}`;
        const response = await fetch(apiUrl);

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        setContractorData(data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

  }, [contractorName]); // Only run when contractorName changes

  if (loading) {
    return <div className="contractor-profile-container">Loading contractor data...</div>;
  }

  if (error) {
    return <div className="contractor-profile-container">Error: {error}</div>;
  }

  if (!contractorData) {
    return <div className="contractor-profile-container">Contractor not found.</div>;
  }

  return (
    <div className="contractor-profile-container">
      <div className="header">
        <h1>Reliable Contractor</h1>
        <FontAwesomeIcon icon={faUserCircle} size="3x" className="profile-icon" />
      </div>

      <div className="info">
        <p><strong>Name:</strong> {contractorData?.contractor?.name}</p>
        <p><strong>License ID:</strong> {contractorData?.contractor?.license_id}</p>
      </div>

      <h3>Past Projects</h3>
      <div className="past-projects">
        <table className="projects-table">
          <thead>
            <tr>
              <th>Project ID</th>
              <th>Project Description</th>
              <th>Amount</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {contractorData?.previous_works?.map((project) => (
              <tr key={project.project_id}>
                <td>{project.project_id}</td>
                <td>{project.project_description}</td>
                <td>{project.project_amount}</td>
                <td>{project.project_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="address">
        <h3>Address</h3>
        <p>
          {contractorData?.address_details?.street_number} {contractorData?.address_details?.street_name}<br />
          {contractorData?.address_details?.city}, {contractorData?.address_details?.state} {contractorData?.address_details?.zipcode}
        </p>
      </div>
    </div>
  );
};

export default ReliableContractorProfile;