// ReliableContractorProfile.js
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faUserCircle } from '@fortawesome/free-solid-svg-icons';
import './ContractorProfile.css';

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

const formatMoney = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

const ReliableContractorProfile = () => {
  const { contractorName } = useParams();
  const [contractorData, setContractorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
  
      try {
        // First try to get data from localStorage
        const storedData = localStorage.getItem('contractorData');
        if (storedData) {
          setContractorData(JSON.parse(storedData));
          localStorage.removeItem('contractorData'); // Clean up after using
          setLoading(false);
          return;
        }
  
        // If no stored data, fetch from API
        const apiUrl = `http://localhost:8003/api/detailed-contractor?contractor_name=${encodeURIComponent(contractorName)}`;
        const response = await fetch(apiUrl);
  
        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }
  
        const data = await response.json();
        setContractorData(data);
      } catch (err) {
        console.error("Error:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
  
    if (contractorName) {
      fetchData();
    }
  }, [contractorName]);

  if (loading) return <div className="contractor-profile-container">Loading contractor data...</div>;
  if (error) return <div className="contractor-profile-container">Error: {error}</div>;
  if (!contractorData) return <div className="contractor-profile-container">Contractor not found.</div>;

  // Check if previous_works exists and has elements
  const latestWork = contractorData.previous_works?.length > 0 ? contractorData.previous_works[0] : null;

  return (
    <div className="contractor-profile-container">
      <div className="header">
        <h1>{contractorName}</h1>
        <FontAwesomeIcon icon={faUserCircle} size="3x" className="profile-icon" />
      </div>

      <div className="info">
        <p><strong>Total Projects:</strong> {contractorData.previous_works?.length || 0}</p>
        {latestWork && (
          <>
            <p><strong>Latest Project Value:</strong> {formatMoney(latestWork.project_amount)}</p>
            <p><strong>Current Status:</strong> {latestWork.project_status.toUpperCase()}</p>
          </>
        )}
      </div>

      <h3>Past Projects</h3>
      <div className="past-projects">
        <table className="projects-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Project Description</th>
              <th>Amount</th>
              <th>Status</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {contractorData.previous_works?.map((project) => (
              <tr key={project.project_id}>
                <td>{project.date_started ? formatDate(project.date_started) : 'N/A'}</td>
                <td>{project.project_description || 'N/A'}</td>
                <td>{project.project_amount ? formatMoney(project.project_amount) : 'N/A'}</td>
                <td style={{
                  color: project.project_status === 'open' ? '#28a745' : '#dc3545',
                  fontWeight: '600'
                }}>
                  {project.project_status?.toUpperCase() || 'N/A'}
                </td>
                <td>
                  <details>
                    <summary>View</summary>
                    <p>{project.project_comments || 'No comments available'}</p>
                  </details>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {contractorData.gpt && (
        <div className="gpt-analysis">
          <h3>AI Analysis</h3>
          <p>{contractorData.gpt}</p>
        </div>
      )}
    </div>
  );
};

export default ReliableContractorProfile;